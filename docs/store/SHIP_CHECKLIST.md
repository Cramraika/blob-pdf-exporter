# Ship Checklist — first publish to Chrome Web Store

**TL;DR.** All script-side work is done. CWS API uploads via Service Account (`vagarylife@vagarylife.iam.gserviceaccount.com`, leveraged from pulseboard) succeed. The extension exists at item ID **`nkaleipmbbceglfkjkjognhkfimjepjc`** in draft state. To submit for review, fill in 10 listing fields in the developer dashboard once. Every release thereafter is `git tag && git push --tags`.

The 10 fields are Google-mandated dashboard-only (no API endpoint to set them). Copy-paste content for each is below.

---

## Quick links

- **Devconsole item:** https://chrome.google.com/webstore/devconsole/edit/nkaleipmbbceglfkjkjognhkfimjepjc
- **Privacy policy URL:** https://cramraika.github.io/blob-pdf-exporter/PRIVACY
- **Source listing copy:** [`chrome-store-assets/store-listing.md`](../../chrome-store-assets/store-listing.md)
- **Screenshots:** [`chrome-store-assets/screenshots/`](../../chrome-store-assets/screenshots/) — 3 PNGs at 1280×800 ready to upload

---

## Step-by-step (the 1% manual work)

Open: https://chrome.google.com/webstore/devconsole/edit/nkaleipmbbceglfkjkjognhkfimjepjc

### Tab: Store listing → Description

**Name** (already from manifest):

```
Blob PDF Exporter
```

**Summary** (≤132 chars):

```
Combine blob: images on the current page into a single PDF. Useful for document viewers that render pages as blob URLs.
```

**Detailed description** (≤16,000 chars; needs ≥25 to satisfy the validator):

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

v0.1.x — Initial releases.

BUILT BY

Chinmay Ramraika / Vagary Labs.
```

**Category**: `Productivity`

**Language**: `English (United States)`

---

### Tab: Store listing → Graphic assets

- **Store icon (128×128 PNG)**: upload `icons/icon-128.png` from this repo (already at `/Users/chinmayramraika/Documents/Github/blob-pdf-exporter/icons/icon-128.png`).
- **Screenshots (1280×800 PNG, 1-5)**: upload all three from `chrome-store-assets/screenshots/`:
  - `01-popup-idle.png` — popup UI in idle state
  - `02-export-in-progress.png` — export overlay mid-progress
  - `03-export-success.png` — completion state
- **Promotional images** (optional): skip for first publish; can add later.

---

### Tab: Privacy practices

Click "Add" / "Edit" for each subsection:

**Single purpose justification** (paste verbatim):

```
Single purpose: Combine blob: image URLs on the active web page into a downloadable PDF.

Permissions required:
- activeTab: Read images from the currently-focused tab the user explicitly clicks the extension on. No background tabs accessed.
- scripting: Inject the exporter and bundled jsPDF library into the active tab when the user clicks "Export to PDF". Required because the exporter must run in the page's main world to access blob:-URL canvas data.

No host_permissions are requested. No <all_urls>. The extension never runs without an explicit user action on the active tab.
```

**Permission justifications:**

| Permission | Justification (paste in each field) |
|---|---|
| `activeTab` | `Read blob:-URL images from the currently-focused tab when the user explicitly clicks the extension. No background tab access. Permission is scoped to the single tab and gone when the user navigates away.` |
| `scripting` | `Inject the bundled jsPDF library and exporter logic into the active tab via chrome.scripting.executeScript when the user clicks "Export to PDF". Required because exporter must access blob:-URL canvas data in the page's main world. No persistent content script.` |

**Remote code use justification:**

```
This extension does not use remote code. jsPDF 2.5.1 is bundled at vendor/jspdf.umd.min.js (verified by Chrome Web Store automated review tooling on upload). No CDN load, no eval() of remote scripts, no dynamic import from network sources.
```

**Data usage disclosures** (check / select on the form):

- ✅ I certify that my data usage complies with the Developer Program Policies.
- ❌ Personally identifiable information — `No`
- ❌ Health information — `No`
- ❌ Financial/payment info — `No`
- ❌ Authentication information — `No`
- ❌ Personal communications — `No`
- ❌ Location — `No`
- ❌ Web history — `No`
- ❌ User activity — `No`
- ❌ Website content — `No` (we read images from the active tab solely to build the PDF locally; nothing is transmitted off-device)

**Data handling:**

- Sold to third parties — `No`
- Used or transferred for purposes unrelated to the item's core function — `No`
- Used or transferred to determine creditworthiness or for lending purposes — `No`

**Privacy policy URL:**

```
https://cramraika.github.io/blob-pdf-exporter/PRIVACY
```

---

### Tab: Account / Settings

**Publisher contact email**:

```
mail@chinmayramraika.in
```

Click **Verify email** — Chrome Web Store sends a confirmation email. Click the link in the email to verify.

(Or use any email you control. The verified contact appears publicly on the listing page.)

---

## Final submit

After all 10 fields above are filled in, click **Submit for review** at the top of the page. Review typically takes 1-3 business days for first submission.

While reviewing, you can keep iterating on code + tagging new versions; CI uploads them as drafts. They queue behind the in-review one.

---

## Verification

Once submitted, run from your laptop:

```bash
cd ~/Documents/Github/blob-pdf-exporter
export CHROME_PUBLISHER_EMAIL='chinu.ramraika@gmail.com'
export CHROME_EXTENSION_ID='nkaleipmbbceglfkjkjognhkfimjepjc'
make status                # GET /items/{id} — show item state
```

You should see `uploadState: SUCCESS` + `crxVersion` matching your latest tag.

---

## Future releases

Once the first review passes:

```bash
make bump-patch              # 0.1.1 → 0.1.2
git add manifest.json && git commit -m "chore: bump to v0.1.2" && git push
make tag                     # → CI auto-uploads as draft
gh workflow run store-release.yml -f publish_target=default
```

Or skip CI and ship from laptop:

```bash
make ship-public             # pack + upload + publish to public
```

That's the 99% loop.

---

## What about C12 / SETUP.md's 7-step setup?

Now mostly obsolete. The SETUP.md described the OAuth path which assumed creating a new OAuth client. We took the SA path instead by leveraging pulseboard's existing service account + `vagarylife` GCP project. Specifically:

| SETUP.md step | Replaced by |
|---|---|
| 1. Create OAuth client (Google Cloud Console) | Skipped — used existing SA from pulseboard |
| 2. Capture refresh_token | Skipped — SA mints tokens via JWT-bearer |
| 3. Manual first upload (get extension ID) | DONE in this session via `POST /items?publisherEmail=...` (HTTP 200 → ID `nkaleipmbbceglfkjkjognhkfimjepjc`) |
| 4. Add 4 GitHub secrets | DONE: `CHROME_SA_JSON_B64`, `CHROME_PUBLISHER_EMAIL`, `CHROME_EXTENSION_ID` |
| 5. Smoke-test | DONE — `make status` returns 200 |
| 6. Test CI workflow | Will be verified on next tag push |
| 7. Publish | Blocked only by the 10 fields in this checklist |

Keep `SETUP.md` for the OAuth fallback path (e.g., if you ever want to publish from a CWS dev account NOT registered with this SA). For the current `chinu.ramraika@gmail.com` dev account, SA mode is sufficient and is the path CI uses.
