# Release Runbook — Chrome Web Store

What a release looks like end-to-end, once `SETUP.md` is done.

## The common case (~30 seconds of human time)

```bash
# 1. Bump version in manifest.json
make bump-patch                          # 0.1.0 → 0.1.1

# 2. Commit the bump
git add manifest.json
git commit -m "chore: bump to v0.1.1"
git push

# 3. Tag → CI auto-uploads
make tag                                 # tags v0.1.1, pushes tag

# 4. Watch CI (optional)
gh run watch
```

CI does:
- Pre-flight: tag version == manifest.json version.
- Packs deterministic zip.
- Uploads to Chrome Web Store API (draft state).
- Attaches zip to a new GitHub Release.

**Status: uploaded as draft.** Not visible to users yet.

## Publishing the draft

Tag push uploads but deliberately does NOT auto-publish (risk-aware default — see `AUTOMATION_ENVELOPE.md` § risk-aware defaults).

### Option A — Trusted testers first (recommended)

```bash
gh workflow run store-release.yml -f publish_target=trustedTesters
# or locally:
make publish-trusted
```

Trusted testers receive the new version within minutes. Public users still see the old version.

After testing:

```bash
gh workflow run store-release.yml -f publish_target=default
# or locally:
make publish-public
```

### Option B — Straight to public

```bash
gh workflow run store-release.yml -f publish_target=default
# or locally:
make publish-public                       # ⚠️ Reaches end users
```

Web Store review typically:
- **First-ever submission**: 1-3 business days.
- **Subsequent updates**: 1-24 hours.
- **Major changes (permissions, metadata)**: 1-3 business days.

You can keep tagging new versions during review; they queue.

## Patch / minor / major bumps

```bash
make bump-patch    # 0.1.0 → 0.1.1 (bugfix)
make bump-minor    # 0.1.5 → 0.2.0 (new feature)
# Major bumps: edit manifest.json by hand (rare; reserve for breaking UX changes)
```

After bumping always:
```bash
git add manifest.json
git commit -m "chore: bump to vX.Y.Z"
git push
make tag
```

## Rolling back

Chrome Web Store does NOT support straight rollbacks (older version replaces newer). The workaround:

1. Check out the previous good version's source:
   ```bash
   git checkout v0.1.5         # the known-good tag
   ```
2. Bump beyond the bad version:
   ```bash
   make bump-patch             # gives you v0.1.5 → v0.1.6
   ```
   But the bad version was v0.1.6 — bump again:
   ```bash
   make bump-patch             # → v0.1.7
   ```
3. Commit on a hotfix branch, tag, push:
   ```bash
   git checkout -b hotfix-rollback
   git add manifest.json
   git commit -m "chore: rollback bad v0.1.6 — content of v0.1.5"
   make tag                    # v0.1.7
   ```
4. CI uploads v0.1.7 — which is byte-identical to v0.1.5 minus the version bump. Users update from v0.1.6 → v0.1.7 → effectively rolled back.

## Halting a rollout mid-flight

Chrome Web Store doesn't support staged rollout fractions like Google Play. Every publish is 100% to the selected audience. If a bad publish hits production:

1. Don't wait — immediately publish a hotfix (see rollback above).
2. Optionally: in the devconsole, manually "Reject" the draft. This stops further propagation but does NOT recall already-installed copies.

## Observability

```bash
make status                              # current item state from API
```

Returns JSON with:
- `id` — extension ID
- `uploadState` — SUCCESS | IN_PROGRESS | FAILURE | NOT_FOUND
- `status` — array of state codes; "OK" means uploaded cleanly
- `crxVersion` — version Web Store thinks is current
- `itemError` — list of upload errors (when uploadState = FAILURE)

For install statistics, reviews, crash reports: open https://chrome.google.com/webstore/devconsole — these aren't exposed via API as of v1.1.

## Sponsor-revenue tracking integration

After each meaningful release (especially public publishes), the new install volume + any sponsor activity flow into:

```
vagary-earnings/data/current-sponsors.yaml      ← github-sponsors-sync.py
vagary-earnings/data/monthly/YYYY-MM.yaml       ← monthly-aggregator.py
vagary-earnings/docs/hustles/chrome-extensions/blob-pdf-exporter.md  ← manual update on milestones
```

The hustle entry's `revenue_to_date_usd` is the per-hustle ground truth; the monthly snapshots are the aggregator's roll-up.

## Cross-references

- `AUTOMATION_ENVELOPE.md` — what's API vs browser.
- `SETUP.md` — one-time setup.
- `~/Documents/Github/blob-pdf-exporter/.github/workflows/store-release.yml` — CI workflow.
- `~/Documents/Github/blob-pdf-exporter/Makefile` — local commands.
- `~/Documents/Github/vagary-earnings/docs/hustles/chrome-extensions/blob-pdf-exporter.md` — hustle tracker entry.
