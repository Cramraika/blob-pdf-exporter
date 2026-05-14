# One-time Setup — Chrome Web Store auto-deploy

Do this ONCE per extension. After it's done, releases are `git tag v0.X.Y && git push --tags` forever.

Total time: ~15-30 min of interactive browser work, then 4 GitHub secrets to paste. The publisher script + workflow + Makefile handle everything else.

---

## Prerequisites

- [ ] Google account with Chrome Web Store developer registration (one-time $5; you said you already have this)
- [ ] GitHub repo with the extension code (`Cramraika/blob-pdf-exporter` — already set up)
- [ ] Python 3.11+ locally (for `auth-bootstrap`)
- [ ] `gh` CLI authenticated as the repo owner (for setting GitHub secrets)

---

## Step 1 — Create the OAuth client (Google Cloud Console)

The Chrome Web Store API uses Google OAuth2. You need a "Desktop app" OAuth client (NOT a Service Account — service accounts can't act on extensions you own).

1. Open https://console.cloud.google.com/
2. Create a new project (or pick existing): **vagary-labs** or similar.
3. Enable the Chrome Web Store API:
   - https://console.cloud.google.com/apis/library
   - Search "Chrome Web Store API" → Enable.
4. Configure OAuth consent screen:
   - APIs & Services → OAuth consent screen.
   - User Type: **External** (Internal is Google Workspace only).
   - App name: "blob-pdf-exporter publisher" (or any name; only you see it).
   - Support email: your address.
   - Add scope: `https://www.googleapis.com/auth/chromewebstore`
   - Add test user: your own Google account email (the one that owns the Web Store dev account).
   - **Don't submit for verification** — staying in "Testing" mode is fine for personal-use OAuth clients. Refresh tokens may expire every 7 days in Testing mode; publish the app to "In production" if you want indefinite refresh tokens (no review needed for internal-scope apps).
5. Create credentials:
   - APIs & Services → Credentials → Create Credentials → OAuth client ID.
   - Application type: **Desktop app**.
   - Name: "chrome-store-publisher".
   - Click Create. Copy the Client ID + Client Secret.

You now have:
- `CHROME_OAUTH_CLIENT_ID` (looks like `123456789-abc.apps.googleusercontent.com`)
- `CHROME_OAUTH_CLIENT_SECRET` (looks like `GOCSPX-...`)

---

## Step 2 — Capture the refresh_token (local browser dance, ~1 min)

```bash
cd ~/Documents/Github/blob-pdf-exporter

export CHROME_OAUTH_CLIENT_ID='<from step 1>'
export CHROME_OAUTH_CLIENT_SECRET='<from step 1>'

make auth-bootstrap
```

What happens:
1. The script opens `https://accounts.google.com/o/oauth2/auth?...` in your default browser.
2. You sign in with the Google account that owns the Web Store dev registration.
3. You consent to the `chromewebstore` scope.
4. Google redirects to `http://127.0.0.1:8765/oauth/callback?code=...` — the script catches this on a local server.
5. The script exchanges the `code` for a `refresh_token` and prints it.

The refresh_token is long-lived. Copy it; that's `CHROME_OAUTH_REFRESH_TOKEN`.

**If `auth-bootstrap` says "no refresh_token in response":** Google has cached your prior consent. Revoke at https://myaccount.google.com/permissions ("Apps & sites you've granted access to" → find your "blob-pdf-exporter publisher" → remove access). Re-run `make auth-bootstrap`.

---

## Step 3 — Manual first upload (one-time browser, ~10 min)

Chrome Web Store assigns the extension ID on the first manual upload. You can't pre-create an ID via API.

1. Open https://chrome.google.com/webstore/devconsole
2. Click "**+ New item**".
3. Upload `dist/blob-pdf-exporter-v0.1.0.zip` (run `make pack` to produce it).
4. Web Store extracts manifest, assigns the extension ID, shows the listing form.
5. Copy the extension ID from the URL or the dashboard. Format: 32-char lowercase alphanumeric. That's `CHROME_EXTENSION_ID`.
6. Fill in the listing form (use the copy from `chrome-store-assets/store-listing.md`):
   - **Description (≤16,000 chars)**: paste from `store-listing.md` § Detailed description.
   - **Category**: Productivity.
   - **Language**: English (United States).
   - **Screenshots**: upload 3-5 PNG/JPEG, 1280×800 or 640×400. See `chrome-store-assets/screenshots-spec.md`.
   - **Promotional images**: optional 440×280 small tile + 1400×560 marquee.
   - **Privacy policy URL**: `https://cramraika.github.io/blob-pdf-exporter/PRIVACY`
   - **Single-purpose justification**: paste from `store-listing.md` § Single purpose justification.
   - **Data practices**: declare "no data collected, no remote scripts" per `store-listing.md` § Privacy practices.
7. Save as Draft. You can submit for review now OR after CI is wired (recommended: wire CI first, then submit for review on the next version).

---

## Step 4 — Add 4 secrets to the GitHub repo

```bash
cd ~/Documents/Github/blob-pdf-exporter

gh secret set CHROME_OAUTH_CLIENT_ID --body '<from step 1>'
gh secret set CHROME_OAUTH_CLIENT_SECRET --body '<from step 1>'
gh secret set CHROME_OAUTH_REFRESH_TOKEN --body '<from step 2>'
gh secret set CHROME_EXTENSION_ID --body '<from step 3>'
```

Verify:

```bash
gh secret list
# expect 4 entries: CHROME_OAUTH_CLIENT_ID, CHROME_OAUTH_CLIENT_SECRET,
#                  CHROME_OAUTH_REFRESH_TOKEN, CHROME_EXTENSION_ID
```

---

## Step 5 — Smoke-test the publisher

Locally first (faster feedback than CI):

```bash
export CHROME_OAUTH_REFRESH_TOKEN='<from step 2>'
export CHROME_EXTENSION_ID='<from step 3>'

make doctor          # confirms all 4 env vars set
make status          # GET /items/{id} → uploadState + status array
```

If `make status` returns HTTP 200 with a JSON blob containing `id`, `kind`, `crxVersion`, etc.: you're wired.

If it returns 401: refresh_token is bad or scope is wrong. Re-run `make auth-bootstrap`.

If it returns 404: extension ID typo or you're authenticated as a different Google account from the one that owns the extension.

---

## Step 6 — Test the CI workflow

```bash
# Bump the version (since v0.1.0 is taken)
make bump-patch              # 0.1.0 → 0.1.1
git add manifest.json
git commit -m "chore: bump to v0.1.1"
git push

make tag                     # tags v0.1.1, pushes tag
```

GitHub Actions `store-release.yml` fires. Steps:
1. Pre-flight verifies tag matches manifest.
2. Packs zip.
3. Status (GET current item state).
4. Upload (PUT zip).
5. Publish — SKIPPED because tag push uses default `publish_target=skip`. Upload alone uploads as a draft; you decide when to publish.
6. Attaches zip to GitHub Release v0.1.1.

Watch the run: `gh run watch`.

---

## Step 7 — Publish from CI (when ready)

Production:

```bash
gh workflow run store-release.yml -f publish_target=default
```

Trusted testers (private cohort) first:

```bash
gh workflow run store-release.yml -f publish_target=trustedTesters
```

OR locally from your laptop with secrets in env:

```bash
make publish-trusted   # to test cohort
make publish-public    # ⚠️ to all users
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `auth-bootstrap` says "no refresh_token" | Prior consent cached | Revoke at https://myaccount.google.com/permissions, re-run |
| HTTP 401 on upload/status | refresh_token expired (Testing mode → 7 day max) | Re-run `auth-bootstrap`; consider moving OAuth app to "In production" |
| HTTP 403 on upload | Wrong Google account owns the OAuth client vs the extension | Both must be the same Google account |
| HTTP 404 on status | Wrong CHROME_EXTENSION_ID | Verify in Web Store devconsole URL |
| `uploadState: FAILURE` on upload | zip schema invalid OR version not greater than current | Run `make lint` locally; check version was bumped |
| Pre-flight fails: "tag != manifest" | You tagged without bumping manifest.json | `git tag -d v0.X.Y; git push origin :v0.X.Y; make bump-patch; commit; make tag` |
| `make tag` says tag exists | You tried to re-tag | Bump version first |

---

## What this setup buys you

After this 30 min, you can:
- `git tag v0.X.Y && git push --tags` — uploads to Web Store as a draft.
- `gh workflow run store-release.yml -f publish_target=default` — publishes to public.
- `make publish-trusted` — push to a test cohort.
- `make status` — quick state check.

You will never again open chrome://chrome.google.com/webstore/devconsole except to:
- Read user reviews.
- Respond to policy violations.
- Watch install statistics.

Everything else: API.
