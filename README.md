# Blob PDF Exporter

Chrome extension that scans the current page for `blob:`-URL images and combines them into a single PDF, in document order.

Useful for document viewers that render PDF pages as in-memory blob images (no download button) — book readers, slide viewers, scanned-document apps.

[![GitHub Sponsors](https://img.shields.io/github/sponsors/Cramraika?label=Sponsor&logo=GitHub)](https://github.com/sponsors/Cramraika) [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## What it does

1. You click the toolbar icon → popup shows "Export to PDF".
2. The extension scans the active tab for `<img>` elements with `blob:` URLs.
3. Each image is drawn to a canvas, encoded (JPEG for opaque, PNG for transparent), and added as a PDF page sized to the image's natural dimensions.
4. The PDF saves with a filename derived from the page's `og:title` / `<h1>` / `<title>` / URL slug.

No data leaves your browser. The extension only runs on the tab you explicitly click it from (`activeTab` permission).

## Install

### From Chrome Web Store

Coming soon — pending Chrome Web Store review.

### From source (developer mode)

1. Clone or download this repo.
2. Open `chrome://extensions/`.
3. Toggle **Developer mode** on (top right).
4. Click **Load unpacked** → select this repo's folder.
5. The Blob PDF Exporter icon appears in your toolbar.

### From a packaged zip

Download `blob-pdf-exporter-vX.Y.Z.zip` from the [Releases page](https://github.com/Cramraika/blob-pdf-exporter/releases), unzip, then Load unpacked the extracted folder per above.

## Usage

1. Open a page where document pages render as `blob:` images (e.g., a document viewer).
2. Scroll through every page so the viewer loads each blob URL into the DOM. *(Most viewers lazy-load — if a page isn't visited, its image isn't in the DOM, so it won't appear in the PDF.)*
3. Click the Blob PDF Exporter toolbar icon.
4. Click **Export to PDF**.
5. PDF saves to your downloads folder.

## Behaviour & limits

- **Image order** is determined by visual position (top-to-bottom, left-to-right by DOM bounding-rect).
- **Image quality**: JPEG at quality 0.92 for opaque images; PNG (lossless) for any image with transparency.
- **Page size**: each PDF page is sized to its source image's natural dimensions (no resize, no resampling).
- **Cross-origin**: cross-origin images that taint the canvas are skipped silently (browser security — extension cannot work around this).
- **Memory**: pages are processed one at a time; canvases are released after each page. Large documents (100+ pages) work but may briefly spike memory.

## Why this exists

Document viewers (some PDF readers, slide-deck embeds, scanned-doc apps) intentionally avoid serving direct file downloads — they render each page as a `blob:` URL in an `<img>` tag, then revoke the URL when you navigate away. This extension lets you reconstruct the document for offline use, accessibility tooling, or archival.

**Intended use:** documents you have legitimate access to. Respect copyright; don't use this to circumvent paywalls or distribute paid content.

## Privacy

- **No network calls.** The extension does not contact any server. jsPDF is bundled, not loaded from a CDN.
- **No telemetry.** No analytics, no error reporting, no usage tracking.
- **Permissions:** `activeTab` (runs only on the tab you click from) + `scripting` (injects the exporter into that tab). No `host_permissions`, no `<all_urls>`.

## Tech

- **MV3** Chrome extension (no remote scripts, no `eval`).
- **jsPDF 2.5.1** bundled locally (`vendor/jspdf.umd.min.js`, MIT-licensed).
- **Popup-triggered injection** via `chrome.scripting.executeScript({ world: "MAIN" })` — runs exporter in page's main world to access `blob:` URL resources via canvas.

## Development

```bash
git clone https://github.com/Cramraika/blob-pdf-exporter
cd blob-pdf-exporter
# Load unpacked in chrome://extensions/ → Developer mode → Load unpacked
make help              # see all release commands
make lint              # validate manifest.json + JS syntax
make pack              # produce dist/blob-pdf-exporter-vX.Y.Z.zip
```

No build step. Pure vanilla JS + HTML. Edits in `src/` and `vendor/` apply on extension reload.

### Release automation

This repo ships with full Chrome Web Store auto-deploy:

- **`make tag`** — bumps version + tags + pushes → CI auto-uploads to Web Store.
- **`gh workflow run store-release.yml -f publish_target=default`** — promotes the uploaded draft to public.
- See [`docs/store/RELEASE_RUNBOOK.md`](docs/store/RELEASE_RUNBOOK.md) for the full release flow.
- See [`docs/store/SETUP.md`](docs/store/SETUP.md) for one-time OAuth setup (~30 min, then forever-automatic).
- See [`docs/store/AUTOMATION_ENVELOPE.md`](docs/store/AUTOMATION_ENVELOPE.md) for the honest scope of what's API-driven vs browser-only.

Pattern mirrors [Pulseboard](https://github.com/Cramraika/pulseboard)'s Google Play auto-deploy (`docs/play/`).

### CI

Two GitHub Actions workflows:

- **`.github/workflows/ci.yml`** runs on every push/PR: validates manifest, JS syntax, vendor + icons presence, packs zip artifact.
- **`.github/workflows/store-release.yml`** runs on tag push (`v*`) or workflow_dispatch: pre-flight version check, pack, upload to Chrome Web Store, optionally publish, attach zip to GitHub Release.

## Sponsor

Built and maintained by [Chinmay Ramraika](https://chinmayramraika.in) / [Vagary Labs](https://github.com/Cramraika).

If this extension saves you time, [become a sponsor](https://github.com/sponsors/Cramraika) — sponsor revenue funds OSS time on this and other tools (`bulk`, `tldv_downloader`, `pulseboard`).

## License

MIT — see [LICENSE](LICENSE).

## Cross-references

- [Pulseboard](https://github.com/Cramraika/pulseboard) — Android network monitor (OSS sibling)
- [bulk](https://github.com/Cramraika/bulk) — bulk webhook trigger CLI (OSS sibling)
- [tldv_downloader](https://github.com/Cramraika/tldv_downloader) — tldv meeting downloader (OSS sibling)
