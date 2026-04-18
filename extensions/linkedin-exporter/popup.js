"use strict";

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

  // Persist in extension storage for background download
  chrome.storage.local.set({ lastExport: data });
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

  // Ping content script to confirm it's loaded
  try {
    await chrome.tabs.sendMessage(tab.id, { action: "ping" });
  } catch (_) {
    // Content script may not be injected yet — inject it
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"],
    });
  }

  setStatus("Ready. " + (tab.url.includes("reactions") ? "Reactions page detected." : ""), "ok");
}

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

$("btnScroll").addEventListener("click", async () => {
  const tab = await getLinkedInTab();
  const maxScrolls = parseInt($("scrollCount").value) || 15;
  setStatus("Scrolling to load posts…", "info");
  setButtons(false);

  chrome.tabs.sendMessage(tab.id, { action: "scroll", maxScrolls, delay: 1500 }, res => {
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
  const expandReadMore = $("expandReadMore").checked;
  setStatus("Scraping posts…", "info");
  setButtons(false);

  chrome.tabs.sendMessage(tab.id, { action: "scrape", expandAll: expandReadMore }, res => {
    setButtons(true);
    if (chrome.runtime.lastError || !res?.ok) {
      setStatus("Scrape failed: " + (chrome.runtime.lastError?.message || res?.error || "unknown"), "err");
      return;
    }
    storeExport(res);
    setStatus(`Scraped ${res.count} post(s).`, "ok");
  });
});

$("btnScrollScrape").addEventListener("click", async () => {
  const tab = await getLinkedInTab();
  const maxScrolls = parseInt($("scrollCount").value) || 15;
  const expandReadMore = $("expandReadMore").checked;
  setStatus("Scrolling to load all posts…", "info");
  setButtons(false);

  chrome.tabs.sendMessage(tab.id,
    { action: "scroll_then_scrape", maxScrolls, delay: 1500, expandAll: expandReadMore },
    res => {
      setButtons(true);
      if (chrome.runtime.lastError || !res?.ok) {
        setStatus("Failed: " + (chrome.runtime.lastError?.message || res?.error || "unknown"), "err");
        return;
      }
      storeExport(res);
      setStatus(`Done! ${res.count} post(s) scraped.`, "ok");
    }
  );
});

// ---------------------------------------------------------------------------
// Download / Copy
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
