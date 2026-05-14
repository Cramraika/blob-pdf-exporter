# Automation Envelope — Chrome Web Store

Honest scope of what can and cannot be automated for publishing this extension to the Chrome Web Store. Refer here whenever the question "can this be fully automatic?" comes up.

Companion to pulseboard's `docs/play/AUTOMATION_ENVELOPE.md` (Google Play). Same shape; different store.

## Short version

- **First-time per-extension setup** (Google Cloud OAuth client + first manual upload to register the item ID + accept Web Store terms + listing form): **~15-30 min browser, once forever per extension.**
- **Every subsequent release** (zip pack, upload, optional publish-to-trusted-testers or publish-public): **0 browser** when GitHub Actions secrets are set. Triggered by `git tag v0.X.Y && git push --tags`.
- Operator manual review/rollback at the Chrome Web Store devconsole is always optional and always browser.

## 99/1 rule

If you accept the one-time browser tax, the remaining 99% is `git tag` and walking away.

---

## What's fully automated (API-driven, headless)

Once OAuth secrets + extension ID are configured:

### Release lifecycle
- `make pack` — deterministic zip from manifest + src/ + vendor/ + icons/ + LICENSE + README.
- `make upload` — PUT zip via Chrome Web Store API.
- `make publish-trusted` — flip draft → trustedTesters (private test cohort).
- `make publish-public` — flip draft → public (production rollout).
- `make ship-trusted` / `make ship-public` — composed (pack + upload + publish).
- `make status` — GET current item state (uploadState + status array).
- `make tag` — version-tag → CI auto-uploads.

### CI workflow (`.github/workflows/store-release.yml`)
- Triggers on tag push `v*` OR `workflow_dispatch`.
- Verifies tag version matches `manifest.json` version (pre-flight).
- Packs zip.
- Uploads to Chrome Web Store.
- Optionally publishes if `workflow_dispatch` was invoked with `publish_target` ≠ `skip`.
- Attaches zip as a release asset on GitHub.

### Hosted privacy policy
- `https://cramraika.github.io/blob-pdf-exporter/PRIVACY` — served by GitHub Pages from `/docs` on `main`. The URL the Web Store listing references.

---

## What's browser-only, per Google's deliberate design

Verified against Chrome Web Store Items API v1.1 documentation.

### Per-extension one-time setup
1. **Google Cloud OAuth client creation** — at https://console.cloud.google.com/apis/credentials. Project + OAuth consent screen + "Desktop app" credential. **Browser. One-time.**
2. **First manual zip upload** — at https://chrome.google.com/webstore/devconsole. Required to register the extension item ID + accept Chrome Web Store terms + provide initial listing details. **Browser. One-time.**
3. **Accept Web Store policy + privacy practices form** — radio-button-style declarations on the same dashboard. **Browser. One-time per extension. Per policy update may re-fire.**
4. **Set privacy-policy URL + listing copy + screenshots** — these CAN be edited via API (`commit` flow), but the first declaration of them is part of the manual upload step.
5. **Pay $5 Developer registration** — one-time per Google account, NOT per extension. **Browser. One-time forever.**

### Ongoing (rare)
- **Responding to policy violations / appeals** — browser only.
- **Reading reviews / responding to user feedback** — browser only.
- **Pulling install stats / crash reports** — browser-only as of API v1.1 (no stats endpoint).

---

## What we've codified to keep the 99%

| Codified | Where | Purpose |
|---|---|---|
| Reproducible zip pack | `make pack` | Zip is byte-identical across machines (no node_modules, no DS_Store, no docs/) |
| Pre-flight version check | `.github/workflows/store-release.yml` step "Pre-flight" | Tag and manifest.json version MUST match before upload |
| Idempotent publisher CLI | `scripts/chrome-store-publisher.py` | Stateless; each invocation re-exchanges refresh→access; no session caching |
| Doctor target | `make doctor` | One command surfaces missing creds before you waste a CI minute |
| Conservative publish default | CI input `publish_target: skip` (default) | Tag push uploads but does NOT auto-publish; operator picks the moment to flip public |

---

## Risk-aware defaults

- **Tag push uploads but does NOT auto-publish to production.** That requires explicit `workflow_dispatch` with `publish_target=default`.
- **`make publish-public` carries the warning emoji** in `make help` because it ships to end users immediately.
- **`make tag` refuses to overwrite an existing tag** — bumps must go through `bump-patch` / `bump-minor` first.

These are policy choices, not API limitations. Edit `Makefile` + workflow if you want a more aggressive default.

---

## What it would take to remove the 1% browser tax

Google's design forbids it. The OAuth-client creation, terms acceptance, content-rating form, and first item-ID assignment all require interactive consent. Workarounds attempted by others (headless Chromium + scripted form-fill) violate Google Cloud terms and risk account suspension. **We don't pursue them.**

The 1% is the floor.

---

## Cross-references

- `SETUP.md` — step-by-step for the one-time setup.
- `RELEASE_RUNBOOK.md` — what a release looks like end-to-end.
- `~/AndroidStudioProjects/pulseboard/docs/play/AUTOMATION_ENVELOPE.md` — sibling document for the Play Store path.
