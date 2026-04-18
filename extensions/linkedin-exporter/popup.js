"use strict";

const CONTENT_VERSION = "8";

let exportData = null;

const $ = id => document.getElementById(id);

function setStatus(msg, type = "") {
  const el = $("status");
  el.textContent = msg;
  el.className = "status" + (type ? " " + type : "");
}

function setButtons(enabled) {
  ["btnScroll", "btnScrape", "btnScrollScrape"].forEach(id => {
    $(id).disabled = !enabled;
  });
}

function storeExport(data) {
  exportData = data;
  const count = data.posts?.length || 0;
  $("countBadge").textContent = count;
  $("btnDownload").disabled = count === 0;
  $("btnCopy").disabled = count === 0;
  chrome.storage.local.set({ lastExport: data });
}

// Auto-download log as a .txt file on every scrape run.
// This way the log is never lost when the popup closes.
function downloadLog(lines, label = "scrape") {
  if (!lines?.length) return;
  const ts = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const text = `AAA LinkedIn Exporter — ${label} log\n${ts}\n\n` + lines.join("\n");
  const blob = new Blob([text], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  chrome.downloads.download({
    url,
    filename: `aaa_scrape_log_${ts}.txt`,
    saveAs: false,
  });
}

function showLog(lines) {
  const panel = $("logPanel");
  const body = $("logBody");
  if (!lines?.length) { panel.style.display = "none"; return; }
  body.textContent = lines.join("\n");
  panel.style.display = "block";
  $("logDetails").open = true;  // always open so user sees it
}

function handleScrapeResult(res, label) {
  setButtons(true);
  const log = res?.log || [];
  showLog(log);
  downloadLog(log, label);   // auto-save every run
  if (chrome.runtime.lastError || !res?.ok) {
    setStatus((label + " failed: ") + (chrome.runtime.lastError?.message || res?.error || "unknown"), "err");
    return;
  }
  storeExport(res);
  setStatus(`${label}: ${res.count} post(s) scraped.`, res.count > 0 ? "ok" : "err");
}

// ---------------------------------------------------------------------------
// Get active tab and check it's LinkedIn
// ---------------------------------------------------------------------------

async function getLinkedInTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function init() {
  const tab = await getLinkedInTab();
  $("pageUrl").textContent = tab?.url || "unknown";

  if (!tab?.url?.includes("linkedin.com")) {
    $("notLinkedIn").style.display = "block";
    setButtons(false);
    setStatus("Not on LinkedIn.", "err");
    return;
  }

  // Ping content script; reinject if missing or wrong version.
  // Note: injecting doesn't evict old scripts — we use requireVersion in
  // messages so only the matching version responds.
  let needsInject = false;
  try {
    const pong = await chrome.tabs.sendMessage(tab.id, { action: "ping" });
    if (pong?.version !== CONTENT_VERSION) needsInject = true;
  } catch (_) {
    needsInject = true;
  }
  if (needsInject) {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"],
    });
  }

  setStatus("Ready. " + (tab.url.includes("reactions") ? "Reactions page detected." : ""), "ok");
}

// ---------------------------------------------------------------------------
// Actions — every message includes requireVersion so stale scripts are silent
// ---------------------------------------------------------------------------

$("btnScroll").addEventListener("click", async () => {
  const tab = await getLinkedInTab();
  const maxScrolls = parseInt($("scrollCount").value) || 15;
  setStatus("Scrolling to load posts…", "info");
  setButtons(false);

  chrome.tabs.sendMessage(tab.id,
    { action: "scroll", maxScrolls, delay: 1500, requireVersion: CONTENT_VERSION },
    res => {
      setButtons(true);
      if (chrome.runtime.lastError || !res?.ok) {
        setStatus("Scroll failed: " + (chrome.runtime.lastError?.message || res?.error || "unknown"), "err");
      } else {
        setStatus("Scroll complete. Now click Scrape.", "ok");
      }
    });
});

$("btnScrape").addEventListener("click", async () => {
  const tab = await getLinkedInTab();
  setStatus("Scraping posts…", "info");
  setButtons(false);

  chrome.tabs.sendMessage(tab.id,
    { action: "scrape", expandAll: $("expandReadMore").checked, requireVersion: CONTENT_VERSION },
    res => handleScrapeResult(res, "Scrape"));
});

$("btnScrollScrape").addEventListener("click", async () => {
  const tab = await getLinkedInTab();
  const maxScrolls = parseInt($("scrollCount").value) || 15;
  setStatus("Scrolling + scraping…", "info");
  setButtons(false);

  const maxPosts = parseInt($("maxPosts").value) || 0;
  chrome.tabs.sendMessage(tab.id,
    { action: "scroll_then_scrape", maxScrolls, delay: 1500,
      expandAll: $("expandReadMore").checked,
      maxPosts,
      requireVersion: CONTENT_VERSION },
    res => handleScrapeResult(res, "Scroll+Scrape"));
});

// ---------------------------------------------------------------------------
// Download / Copy export
// ---------------------------------------------------------------------------

$("btnDownload").addEventListener("click", async () => {
  if (!exportData) return;

  const json = JSON.stringify(exportData, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const ts = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const pageSlug = (exportData.page_url || "linkedin")
    .replace(/https?:\/\/[^/]+/, "")
    .replace(/[^a-zA-Z0-9]/g, "_")
    .slice(0, 40);

  chrome.downloads.download({
    url,
    filename: `linkedin_export_${pageSlug}_${ts}.json`,
    saveAs: false,
  }, downloadId => {
    if (chrome.runtime.lastError) {
      setStatus("Download error: " + chrome.runtime.lastError.message, "err");
    } else {
      setStatus(`Downloaded! (${exportData.posts?.length} posts, ID ${downloadId})`, "ok");
    }
  });
});

$("btnCopy").addEventListener("click", async () => {
  if (!exportData) return;
  await navigator.clipboard.writeText(JSON.stringify(exportData, null, 2));
  setStatus("Copied to clipboard.", "ok");
});

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

init().catch(err => setStatus("Init error: " + err.message, "err"));
