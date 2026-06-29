"use strict";

// Background service worker.
//
// Single-page exports are handled in popup.js. This worker adds BATCH MODE:
// given a list of profile handles/URLs, it drives the active tab through each
// person's /recent-activity/all/ page in your logged-in session — navigate →
// settle → inject → scroll+scrape → download JSON → next.
//
// This is the realistic "automation": it runs in YOUR authenticated browser, so
// it respects LinkedIn auth. It is NOT headless/server-side (LinkedIn auth-walls
// anonymous access and bans datacenter scraping). Polite delays are built in;
// don't crank the pace — aggressive automated scraping risks your account.

const CONTENT_VERSION = "23";
const SETTLE_MS = 3500;             // wait after a page reports "complete"
const BETWEEN_PROFILES_MS = 4000;   // politeness gap between profiles

chrome.runtime.onInstalled.addListener(() => {
  console.log("[AAA LinkedIn Exporter] Installed.");
});

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.action === "batchStart") {
    runBatch(msg.handles || [], msg.opts || {})
      .then(summary => sendResponse({ ok: true, summary }))
      .catch(err => sendResponse({ ok: false, error: String(err) }));
    return true; // keep the channel open for the async response
  }
});

// Normalize "alliekmiller", "in/alliekmiller", or a full URL → recent-activity URL.
function toRecentActivityUrl(handle) {
  const h = (handle || "").trim();
  if (!h) return null;
  if (h.startsWith("http")) {
    const base = h.replace(/\/+$/, "").replace(/\/recent-activity.*$/, "");
    return base + "/recent-activity/all/";
  }
  const slug = h.replace(/^in\//, "").replace(/^\/+|\/+$/g, "");
  return `https://www.linkedin.com/in/${slug}/recent-activity/all/`;
}

function slugFromHandle(handle) {
  const h = (handle || "").trim().replace(/^https?:\/\/[^/]+/, "").replace(/[^a-zA-Z0-9]/g, "_");
  return h.replace(/_+/g, "_").replace(/^_|_$/g, "").slice(0, 40) || "profile";
}

function waitForComplete(tabId, timeoutMs = 30000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      chrome.tabs.onUpdated.removeListener(listener);
      reject(new Error("page load timeout"));
    }, timeoutMs);
    function listener(updatedId, info) {
      if (updatedId === tabId && info.status === "complete") {
        clearTimeout(timer);
        chrome.tabs.onUpdated.removeListener(listener);
        resolve();
      }
    }
    chrome.tabs.onUpdated.addListener(listener);
  });
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function ensureContentScript(tabId) {
  try {
    const pong = await chrome.tabs.sendMessage(tabId, { action: "ping" });
    if (pong?.version === CONTENT_VERSION) return;
  } catch (_) { /* not injected yet */ }
  await chrome.scripting.executeScript({ target: { tabId }, files: ["content.js"] });
  await sleep(500);
}

async function setProgress(p) {
  await chrome.storage.local.set({ batchProgress: p });
}

async function runBatch(handles, opts) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) throw new Error("no active tab");

  const maxScrolls = opts.maxScrolls || 15;
  const maxAgeMonths = opts.maxAgeMonths || 0;   // 0 = no cutoff; e.g. 2 = last 2 months
  const maxPosts = opts.maxPosts || 0;
  const results = [];

  for (let i = 0; i < handles.length; i++) {
    const handle = handles[i];
    const url = toRecentActivityUrl(handle);
    if (!url) continue;
    const slug = slugFromHandle(handle);

    await setProgress({ i: i + 1, n: handles.length, handle, stage: "navigating", done: false, results });

    try {
      await chrome.tabs.update(tab.id, { url });
      await waitForComplete(tab.id);
      await sleep(SETTLE_MS);
      await ensureContentScript(tab.id);

      await setProgress({ i: i + 1, n: handles.length, handle, stage: "scraping", done: false, results });
      const res = await chrome.tabs.sendMessage(tab.id, {
        action: "scroll_then_scrape",
        maxScrolls, delay: 1500, expandAll: true,
        maxPosts, maxAgeMonths,
        requireVersion: CONTENT_VERSION,
      });

      const count = res?.count || 0;
      if (res?.ok && count > 0) {
        const payload = JSON.stringify(res, null, 2);
        const blobUrl = "data:application/json;charset=utf-8," + encodeURIComponent(payload);
        const ts = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
        await chrome.downloads.download({
          url: blobUrl,
          filename: `linkedin_export_${slug}_${ts}.json`,
          saveAs: false,
        });
      }
      results.push({ handle, count, ok: !!res?.ok });
    } catch (err) {
      results.push({ handle, count: 0, ok: false, error: String(err) });
    }

    if (i < handles.length - 1) await sleep(BETWEEN_PROFILES_MS);
  }

  await setProgress({ i: handles.length, n: handles.length, stage: "done", done: true, results });
  return results;
}
