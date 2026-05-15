# Blob PDF Exporter

A Chrome extension that combines `blob:`-URL images on the current page into a single PDF, in document order.

Useful for document viewers that render pages as in-memory blob images instead of offering a direct download.

## Links

- **Source code:** [github.com/Cramraika/blob-pdf-exporter](https://github.com/Cramraika/blob-pdf-exporter)
- **Privacy policy:** [PRIVACY](PRIVACY)
- **Releases:** [github.com/Cramraika/blob-pdf-exporter/releases](https://github.com/Cramraika/blob-pdf-exporter/releases)
- **Report an issue:** [github.com/Cramraika/blob-pdf-exporter/issues](https://github.com/Cramraika/blob-pdf-exporter/issues)
- **Sponsor:** [github.com/sponsors/Cramraika](https://github.com/sponsors/Cramraika)

## What it does

1. Open a page where document pages render as `blob:` images.
2. Scroll through every page so the viewer loads each blob into the DOM.
3. Click the Blob PDF Exporter toolbar icon → **Export to PDF**.
4. The PDF saves to your downloads folder.

No network calls, no telemetry, no tracking. `activeTab` + `scripting` permissions only. MIT-licensed.

---

Built by [Chinmay Ramraika](https://chinmayramraika.in) / Vagary Labs.
