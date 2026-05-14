# Privacy Policy — Blob PDF Exporter

**Last updated:** R7-deep+ session, 2026-05-14.

## Summary

Blob PDF Exporter does not collect, transmit, store, or share any user data.

## What we don't do

- ❌ No analytics (no Google Analytics, no Mixpanel, no PostHog, no Plausible)
- ❌ No error reporting (no Sentry, no Glitchtip, no Rollbar)
- ❌ No usage tracking
- ❌ No advertising identifiers
- ❌ No remote scripts loaded at runtime (jsPDF is bundled)
- ❌ No external HTTP requests
- ❌ No background data collection
- ❌ No personal information requested

## What we do

The extension runs entirely locally in your browser:

1. When you click **Export to PDF**, the extension reads `<img>` elements with `blob:` URLs from the active tab.
2. Each image is drawn to a canvas inside your browser.
3. The canvas data is encoded as PDF pages using the bundled jsPDF library.
4. The resulting PDF is saved to your downloads folder via the browser's standard download mechanism.

All processing happens in your browser. Nothing is transmitted to any server. The maintainer cannot see what documents you export.

## Permissions

- **`activeTab`** — grants temporary access to the currently-focused tab when you explicitly click the extension's toolbar icon. Access ends when you switch tabs or close the popup. No access to background tabs.
- **`scripting`** — allows the extension to inject the bundled jsPDF library and the exporter logic into the active tab when you click "Export to PDF". Required because the exporter must run in the page's main world to access `blob:`-URL canvas data.

No `host_permissions`, no `<all_urls>`, no broad-access patterns.

## Third-party libraries

- **jsPDF 2.5.1** ([github.com/parallax/jsPDF](https://github.com/parallax/jsPDF)) — MIT license. Bundled in `vendor/jspdf.umd.min.js`. Runs entirely client-side.

## Data retention

We retain no data because we collect no data.

## Children's privacy

The extension does not knowingly collect any data from anyone, including children under 13. There is no account creation, no login, no profile.

## International users

The extension functions identically regardless of user location. No geographic targeting, no region-specific data handling, because no data is handled.

## Open source

The full source code is publicly available at [github.com/Cramraika/blob-pdf-exporter](https://github.com/Cramraika/blob-pdf-exporter). You can verify these privacy claims by auditing the code yourself. Every network-call API (`fetch`, `XMLHttpRequest`, `navigator.sendBeacon`) is absent from the codebase by design.

## Changes to this policy

If the extension ever begins collecting data (e.g., optional opt-in error reporting for debugging), this document will be updated and the change announced in the repo's release notes. Users will be required to opt in; collection will never be enabled by default.

## Contact

Questions, concerns, or audits welcome via GitHub Issues: [github.com/Cramraika/blob-pdf-exporter/issues](https://github.com/Cramraika/blob-pdf-exporter/issues)

Maintained by Chinmay Ramraika / Vagary Labs.
