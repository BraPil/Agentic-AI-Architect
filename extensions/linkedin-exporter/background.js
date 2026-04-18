"use strict";
// Background service worker — minimal; downloads are handled directly in popup.js
// Keeps the extension alive when needed.
chrome.runtime.onInstalled.addListener(() => {
  console.log("[AAA LinkedIn Exporter] Installed.");
});
