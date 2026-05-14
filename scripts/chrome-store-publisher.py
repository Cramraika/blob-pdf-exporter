#!/usr/bin/env python3
"""
chrome-store-publisher.py — Chrome Web Store API CLI.

Mirrors the pattern of `~/AndroidStudioProjects/pulseboard/scripts/google-play-publisher.py`
(Google Play Publisher API) but targets the Chrome Web Store Items API:
https://developer.chrome.com/docs/webstore/using-api

Auth: OAuth2 refresh-token flow. One-time browser dance produces a long-lived
refresh_token that survives indefinitely (until revoked). Subsequent calls
exchange the refresh_token for short-lived access_tokens — fully headless.

Required env vars (or pass as CLI args):
    CHROME_OAUTH_CLIENT_ID
    CHROME_OAUTH_CLIENT_SECRET
    CHROME_OAUTH_REFRESH_TOKEN
    CHROME_EXTENSION_ID         (item ID assigned by CWS on first manual upload)

Subcommands:
    auth-bootstrap    Interactive: open browser → operator approves → capture
                      refresh_token. Run once locally, NOT in CI.
    status            GET /items/{id} — return uploadState + draftStatus.
    upload            PUT zip → /upload/chromewebstore/v1.1/items/{id}.
    publish           POST /items/{id}/publish?publishTarget=...

Common usage:
    # One-time (operator-local; opens browser):
    python3 scripts/chrome-store-publisher.py auth-bootstrap

    # In CI / repeat (headless):
    python3 scripts/chrome-store-publisher.py status
    python3 scripts/chrome-store-publisher.py upload --zip dist/ext.zip
    python3 scripts/chrome-store-publisher.py publish --target default
    python3 scripts/chrome-store-publisher.py publish --target trustedTesters

References:
    https://developer.chrome.com/docs/webstore/using-api
    https://developers.google.com/identity/protocols/oauth2/native-app
"""
from __future__ import annotations

import argparse
import http.server
import json
import os
import socketserver
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

OAUTH_AUTHZ_URL = "https://accounts.google.com/o/oauth2/auth"
OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
CWS_API_BASE = "https://www.googleapis.com/chromewebstore/v1.1"
CWS_UPLOAD_BASE = "https://www.googleapis.com/upload/chromewebstore/v1.1"
SCOPE = "https://www.googleapis.com/auth/chromewebstore"
REDIRECT_HOST = "127.0.0.1"
REDIRECT_PORT = 8765
REDIRECT_PATH = "/oauth/callback"


class CredentialError(RuntimeError):
    """Raised when required OAuth credentials are missing."""


def _read_env(name: str, required: bool = True) -> str | None:
    val = os.environ.get(name)
    if not val and required:
        raise CredentialError(
            f"Missing env var {name}. See docs/store/SETUP.md for one-time setup."
        )
    return val


def _http_request(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    timeout: int = 60,
) -> tuple[int, dict[str, str], bytes]:
    """Plain stdlib HTTP wrapper to avoid the requests dependency."""
    req = urllib.request.Request(url, data=data, method=method)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        body = b""
        try:
            body = e.read()
        except Exception:
            pass
        return e.code, dict(e.headers or {}), body


def exchange_refresh_for_access(
    client_id: str, client_secret: str, refresh_token: str
) -> str:
    """POST /token grant_type=refresh_token. Returns access_token."""
    body = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    ).encode("utf-8")
    status, _, payload = _http_request(
        OAUTH_TOKEN_URL,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=body,
    )
    if status != 200:
        raise CredentialError(
            f"Token exchange failed (HTTP {status}): {payload.decode('utf-8', 'replace')}"
        )
    return json.loads(payload)["access_token"]


def _bearer(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}", "x-goog-api-version": "2"}


def cmd_auth_bootstrap(args: argparse.Namespace) -> int:
    """One-time interactive OAuth dance.

    Opens browser → operator approves → local 127.0.0.1 server catches the
    redirect → exchanges authorization_code for refresh_token → prints it.

    Operator copy-pastes the refresh_token into GitHub Actions secrets
    (CHROME_OAUTH_REFRESH_TOKEN) and locally to ~/.config/cws/refresh_token
    if they want to run from this machine too.
    """
    client_id = args.client_id or _read_env("CHROME_OAUTH_CLIENT_ID")
    client_secret = args.client_secret or _read_env("CHROME_OAUTH_CLIENT_SECRET")
    assert client_id and client_secret

    redirect_uri = f"http://{REDIRECT_HOST}:{REDIRECT_PORT}{REDIRECT_PATH}"
    state = os.urandom(16).hex()
    authz_url = (
        f"{OAUTH_AUTHZ_URL}?"
        + urllib.parse.urlencode(
            {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": SCOPE,
                "access_type": "offline",
                "prompt": "consent",
                "state": state,
            }
        )
    )

    received: dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != REDIRECT_PATH:
                self.send_response(404)
                self.end_headers()
                return
            qs = dict(urllib.parse.parse_qsl(parsed.query))
            received.update(qs)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            ok = "code" in qs and qs.get("state") == state
            self.wfile.write(
                (
                    "<h2>Chrome Web Store auth — "
                    + ("OK, close this tab." if ok else "FAILED, check terminal.")
                    + "</h2>"
                ).encode("utf-8")
            )

        def log_message(self, *_: Any) -> None:
            pass

    with socketserver.TCPServer((REDIRECT_HOST, REDIRECT_PORT), Handler) as srv:
        srv.timeout = 300
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        print(f"Opening browser: {authz_url}")
        print(
            f"If the browser doesn't open, paste the URL above. "
            f"Listening on {redirect_uri} for ~5 minutes."
        )
        webbrowser.open(authz_url)

        deadline = time.time() + 300
        while time.time() < deadline and "code" not in received:
            time.sleep(1)
        srv.shutdown()

    if "code" not in received:
        print("Timed out waiting for OAuth callback.", file=sys.stderr)
        return 2
    if received.get("state") != state:
        print("State mismatch — possible CSRF; aborting.", file=sys.stderr)
        return 3

    body = urllib.parse.urlencode(
        {
            "code": received["code"],
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
    ).encode("utf-8")
    status, _, payload = _http_request(
        OAUTH_TOKEN_URL,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=body,
    )
    if status != 200:
        print(
            f"Token exchange failed (HTTP {status}): "
            f"{payload.decode('utf-8', 'replace')}",
            file=sys.stderr,
        )
        return 4

    data = json.loads(payload)
    rt = data.get("refresh_token")
    if not rt:
        print(
            "No refresh_token in response. Most common cause: prior consent "
            "is still cached. Revoke at https://myaccount.google.com/permissions "
            "then re-run.",
            file=sys.stderr,
        )
        print(json.dumps(data, indent=2), file=sys.stderr)
        return 5

    print("")
    print("=" * 60)
    print("CHROME_OAUTH_REFRESH_TOKEN:")
    print(rt)
    print("=" * 60)
    print("")
    print("Save as GitHub Actions secret CHROME_OAUTH_REFRESH_TOKEN")
    print("AND (optional) locally to ~/.config/cws/refresh_token")
    return 0


def get_access_token(args: argparse.Namespace) -> str:
    client_id = args.client_id or _read_env("CHROME_OAUTH_CLIENT_ID")
    client_secret = args.client_secret or _read_env("CHROME_OAUTH_CLIENT_SECRET")
    refresh_token = args.refresh_token or _read_env("CHROME_OAUTH_REFRESH_TOKEN")
    assert client_id and client_secret and refresh_token
    return exchange_refresh_for_access(client_id, client_secret, refresh_token)


def cmd_status(args: argparse.Namespace) -> int:
    """GET /items/{id} — print uploadState + status array."""
    item_id = args.item_id or _read_env("CHROME_EXTENSION_ID")
    assert item_id
    access = get_access_token(args)
    url = f"{CWS_API_BASE}/items/{item_id}?projection=DRAFT"
    status, _, payload = _http_request(url, headers=_bearer(access))
    print(f"HTTP {status}")
    try:
        print(json.dumps(json.loads(payload), indent=2))
    except Exception:
        print(payload.decode("utf-8", "replace"))
    return 0 if status == 200 else 1


def cmd_upload(args: argparse.Namespace) -> int:
    """PUT zip → /upload/...items/{id}."""
    item_id = args.item_id or _read_env("CHROME_EXTENSION_ID")
    assert item_id
    zip_path = Path(args.zip).resolve()
    if not zip_path.is_file():
        print(f"zip not found: {zip_path}", file=sys.stderr)
        return 2

    access = get_access_token(args)
    url = f"{CWS_UPLOAD_BASE}/items/{item_id}"
    with zip_path.open("rb") as f:
        body = f.read()
    headers = {
        **_bearer(access),
        "Content-Type": "application/zip",
        "Content-Length": str(len(body)),
    }
    status, _, payload = _http_request(url, method="PUT", headers=headers, data=body)
    print(f"HTTP {status}  ({len(body)} bytes uploaded)")
    try:
        decoded = json.loads(payload)
        print(json.dumps(decoded, indent=2))
        upload_state = decoded.get("uploadState")
        if upload_state and upload_state.upper() == "FAILURE":
            print("Upload state FAILURE — see itemError list above.", file=sys.stderr)
            return 1
    except Exception:
        print(payload.decode("utf-8", "replace"))
    return 0 if status == 200 else 1


def cmd_publish(args: argparse.Namespace) -> int:
    """POST /items/{id}/publish?publishTarget=default|trustedTesters."""
    item_id = args.item_id or _read_env("CHROME_EXTENSION_ID")
    assert item_id
    target = args.target
    if target not in ("default", "trustedTesters"):
        print(f"--target must be default|trustedTesters; got {target}", file=sys.stderr)
        return 2

    access = get_access_token(args)
    url = (
        f"{CWS_API_BASE}/items/{item_id}/publish"
        f"?publishTarget={target}"
    )
    headers = {**_bearer(access), "Content-Length": "0"}
    status, _, payload = _http_request(url, method="POST", headers=headers, data=b"")
    print(f"HTTP {status}  target={target}")
    try:
        print(json.dumps(json.loads(payload), indent=2))
    except Exception:
        print(payload.decode("utf-8", "replace"))
    return 0 if status == 200 else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--client-id", help="Override CHROME_OAUTH_CLIENT_ID env var.")
    p.add_argument(
        "--client-secret", help="Override CHROME_OAUTH_CLIENT_SECRET env var."
    )
    p.add_argument(
        "--refresh-token", help="Override CHROME_OAUTH_REFRESH_TOKEN env var."
    )
    p.add_argument("--item-id", help="Override CHROME_EXTENSION_ID env var.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("auth-bootstrap", help="One-time interactive OAuth dance.")
    sub.add_parser("status", help="GET item state.")

    up = sub.add_parser("upload", help="PUT zip to existing item.")
    up.add_argument("--zip", required=True, help="Path to packed extension .zip")

    pub = sub.add_parser("publish", help="Publish item.")
    pub.add_argument(
        "--target",
        default="default",
        help="default (public) | trustedTesters (test cohort).",
    )

    return p


def main() -> int:
    args = build_parser().parse_args()
    try:
        match args.cmd:
            case "auth-bootstrap":
                return cmd_auth_bootstrap(args)
            case "status":
                return cmd_status(args)
            case "upload":
                return cmd_upload(args)
            case "publish":
                return cmd_publish(args)
            case _:
                print(f"Unknown subcommand: {args.cmd}", file=sys.stderr)
                return 2
    except CredentialError as e:
        print(f"Credential error: {e}", file=sys.stderr)
        return 10


if __name__ == "__main__":
    sys.exit(main())
