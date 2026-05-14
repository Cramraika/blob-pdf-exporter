// popup.js — entry point. Injects vendor/jspdf + content.js into the active
// tab via chrome.scripting.executeScript when the user clicks Export.
//
// Why this shape: MV3 forbids remote-loading scripts into the page. We bundle
// jsPDF and run our exporter as a discrete injection rather than a
// long-running content script — keeps permissions minimal (activeTab only).

const runBtn = document.getElementById("run");
const statusEl = document.getElementById("status");

function setStatus(text, level) {
  statusEl.textContent = text;
  statusEl.classList.remove("error", "success");
  if (level === "error") statusEl.classList.add("error");
  if (level === "success") statusEl.classList.add("success");
}

runBtn.addEventListener("click", async () => {
  runBtn.disabled = true;
  setStatus("Scanning page for blob: images…");

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) {
      setStatus("No active tab.", "error");
      runBtn.disabled = false;
      return;
    }
    if (tab.url?.startsWith("chrome://") || tab.url?.startsWith("chrome-extension://")) {
      setStatus("Cannot run on this page (chrome:// or extension page).", "error");
      runBtn.disabled = false;
      return;
    }

    // Inject jsPDF first (sets window.jspdf), then the exporter.
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["vendor/jspdf.umd.min.js"],
      world: "MAIN",
    });

    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["src/content.js"],
      world: "MAIN",
    });

    const result = results?.[0]?.result;
    if (result?.success) {
      setStatus(`Exported ${result.added} of ${result.found} blob images.`, "success");
    } else if (result?.message) {
      setStatus(result.message, "error");
    } else {
      setStatus("Export completed.", "success");
    }
  } catch (e) {
    console.error("[blob-pdf-exporter] popup error:", e);
    setStatus(`Failed: ${e.message}`, "error");
  } finally {
    runBtn.disabled = false;
  }
});
