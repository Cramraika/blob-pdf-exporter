# Screenshot specification — Chrome Web Store listing

Required: 1-5 screenshots. Recommended: 3-5 for higher install-rate. Resolution: **1280×800** (preferred) OR **640×400**.

## Screenshot 1 — popup UI (REQUIRED)

**What to capture:**
- Extension popup open, anchored from toolbar icon
- A document viewer visible in the background (e.g., a public-domain book viewer)
- Popup shows "Blob PDF Exporter" title + "Export to PDF" button + "Ready." status

**Capture flow:**
1. Open `https://archive.org/details/<some-public-domain-book>` (or any viewer using blob: images)
2. Click toolbar icon to open popup
3. Capture window (Cmd-Shift-4 on macOS, Win+Shift+S on Windows)
4. Resize/letterbox to 1280×800

## Screenshot 2 — export in progress (RECOMMENDED)

**What to capture:**
- Overlay visible: "Exporting PDF" + progress bar at ~50% + "Page N of M"
- Background shows the document viewer

**Capture flow:**
1. Open a document viewer with 10+ visible blob: images
2. Click Export to PDF
3. Capture mid-progress (timer or screenshot tool with delay)

## Screenshot 3 — finished PDF preview (RECOMMENDED)

**What to capture:**
- The exported PDF open in Chrome / Preview / Acrobat
- 2-3 pages visible (thumbnail strip + main page)
- Filename in the title bar shows the auto-derived name

**Capture flow:**
1. Run an export
2. Open the resulting PDF
3. Screenshot the viewer at 1280×800

## Screenshot 4 — privacy-first messaging (OPTIONAL)

**What to capture:**
- Custom marketing tile: dark-mode background, financial-green primary, copy:
  - "No network calls"
  - "No telemetry"
  - "activeTab only — never <all_urls>"
- Tools: Figma or Canva mock

**Or skip** if running with 3 screenshots is enough.

## Screenshot 5 — chrome://extensions developer mode (OPTIONAL)

**What to capture:**
- chrome://extensions page with Blob PDF Exporter card visible
- Helps users who want to verify the extension is the unpacked one they cloned

## Tools

- macOS: Cmd-Shift-4 (selection), or `screencapture -W` (window)
- Cross-platform: ShareX (Windows), Flameshot (Linux)
- Resize: Preview (macOS), GIMP, online cropper at 1280×800

## File naming

Save to `chrome-store-assets/screenshots/`:
- `01-popup.png`
- `02-progress.png`
- `03-finished-pdf.png`
- `04-privacy.png` (optional)
- `05-devmode.png` (optional)

These files are gitignored by default (large PNGs). If you want to track them, remove the pattern from `.gitignore` or add an explicit allowlist.

## Constraints

- **Do NOT include any user PII / private documents in screenshots.** Use public-domain or sample-document viewers.
- **Do NOT include any third-party trademarks** in foreground unless you own them. Background browser UI is fine.
- **Real-content fidelity** — screenshots should reflect what users will actually see; mocked UI not allowed by Google.
