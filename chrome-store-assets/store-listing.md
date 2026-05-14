# Chrome Web Store listing — Blob PDF Exporter

Copy-paste-ready listing content for the Chrome Web Store Developer Dashboard.

## Pre-publish checklist (operator action items)

1. **Google Developer account** — $5 one-time registration fee at https://chrome.google.com/webstore/devconsole. Use Cramraika personal Google account (or a dedicated Vagary Labs Google account if separate identity preferred).
2. **Privacy policy URL** — required for any extension. Options:
   - (a) Embed in this repo: `docs/PRIVACY.md` + GitHub Pages → `https://cramraika.github.io/blob-pdf-exporter/PRIVACY.html` (need to enable GitHub Pages on the repo).
   - (b) Point to a section of README: `https://github.com/Cramraika/blob-pdf-exporter#privacy` (simpler; review whether Google accepts a README anchor).
3. **Screenshots** — minimum 1, max 5. Required resolution **1280×800** or **640×400**. Capture: (a) popup UI on a real document-viewer page, (b) export overlay mid-progress, (c) downloaded PDF preview. See `screenshots-spec.md` (sibling file).
4. **Promotional images (optional)**:
   - Small tile **440×280** — appears in store search.
   - Marquee **1400×560** — appears on featured pages (only if Google features it).
5. **Pack the extension** — CI workflow produces `blob-pdf-exporter-<sha>.zip` as an artifact. Or pack locally: `zip -r blob-pdf-exporter.zip manifest.json src/ vendor/ icons/ LICENSE README.md`.
6. **Submit for review** — typical review window 1–3 business days for first submission.

## Listing fields

### Name
```
Blob PDF Exporter
```
*(≤45 chars — currently 19)*

### Summary
```
Combine blob: images on the current page into a single PDF. Useful for document viewers that render pages as blob URLs.
```
*(≤132 chars — currently 121)*

### Category
```
Productivity
```

### Language
```
English (United States)
```

### Detailed description
*(≤16,000 chars — current ~1,500)*

```
Blob PDF Exporter combines blob:-URL images on the current page into a single PDF file, in document order.

Some document viewers (book readers, slide-deck embeds, scanned-document apps, certain PDF readers) intentionally avoid serving direct file downloads — they render each page as a blob: URL in an <img> tag, then revoke the URL when you navigate away. This extension lets you reconstruct the document for offline use, accessibility tooling, or archival.

HOW IT WORKS

1. Open a page where document pages render as blob: images.
2. Scroll through every page so the viewer loads each blob into the DOM.
   (Most viewers lazy-load — if a page isn't visited, its image isn't in the DOM, so it won't appear in the PDF.)
3. Click the Blob PDF Exporter toolbar icon.
4. Click "Export to PDF".
5. PDF saves to your downloads folder.

WHAT GETS EXPORTED

- Every unique blob: image found in <img> elements on the active tab.
- Sorted by visual position (top-to-bottom, left-to-right) so the PDF page order matches the document.
- Each PDF page is sized to its source image's natural dimensions — no resizing.
- Quality: JPEG at 0.92 for opaque images; PNG (lossless) for transparent.
- Filename derived from og:title / <h1> / <title> / URL slug.

PRIVACY

- No network calls. jsPDF is bundled, not loaded from a CDN.
- No telemetry. No analytics, no error reporting, no usage tracking.
- Permissions: activeTab (runs only on the tab you click from) + scripting (injects the exporter into that tab).
- No host_permissions. No <all_urls>. No background data collection.

LIMITATIONS

- Cross-origin images that taint the canvas are skipped silently (browser security — this extension cannot work around CORS).
- Pages that don't render content as <img src="blob:..."> won't produce output. This is a tool for the specific document-viewer-with-blob-images pattern, not a general "save webpage as PDF" tool.
- For arbitrary page-to-PDF conversion, use Chrome's built-in Print → Save as PDF.

INTENDED USE

For documents you have legitimate access to. Respect copyright; don't use this to circumvent paywalls or redistribute paid content.

OPEN SOURCE

MIT-licensed. Source: https://github.com/Cramraika/blob-pdf-exporter

If this saves you time, consider sponsoring the maintainer:
https://github.com/sponsors/Cramraika

CHANGELOG

v0.1.0 — Initial release.

BUILT BY

Chinmay Ramraika / Vagary Labs.
```

### Single purpose justification
*(required for any extension; explain why permissions are needed)*

```
Single purpose: Combine blob: image URLs on the active web page into a downloadable PDF.

Permissions required:
- activeTab: Read images from the currently-focused tab the user explicitly clicks the extension on. No background tabs accessed.
- scripting: Inject the exporter and bundled jsPDF library into the active tab when the user clicks "Export to PDF". Required because the exporter must run in the page's main world to access blob:-URL canvas data.

No host_permissions are requested. No <all_urls>. The extension never runs without an explicit user action on the active tab.
```

### Privacy practices (Chrome Web Store form)
- ✅ Personally identifiable information? **No**
- ✅ Health information? **No**
- ✅ Financial / payment information? **No**
- ✅ Authentication information? **No**
- ✅ Personal communications? **No**
- ✅ Location? **No**
- ✅ Web history? **No**
- ✅ User activity? **No**
- ✅ Website content? **No** (we read images from the active tab solely to build the PDF locally; nothing is transmitted off-device)

Use of remote code: **None.** jsPDF is bundled.

Data collected: **None.**

Data transmitted off-device: **None.**

## Future versions

When updating, bump `manifest.json` `version` semver, repack zip, upload, submit for review. Chrome Web Store auto-pushes the update to existing installs after approval (review window typically 1-3 days for established extensions).

## See also

- `screenshots-spec.md` — what each screenshot should show
- Privacy policy (TBD path) — must be hosted at a publicly resolvable URL
