// background.js — minimal MV3 service worker.
//
// Currently no background logic needed (popup-triggered injection is enough).
// Kept as a module-stub so future features (context-menu, omnibox, hotkey)
// have a place to land without manifest changes.

self.addEventListener("install", () => {
  // No-op; reserved for future cache pre-warm if jspdf bundle grows.
});

chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === "install") {
    chrome.tabs.create({
      url: "https://github.com/Cramraika/blob-pdf-exporter#usage",
    });
  }
});
