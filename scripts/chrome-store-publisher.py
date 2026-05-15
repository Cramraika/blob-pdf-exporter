#!/usr/bin/env python3
"""
chrome-store-publisher.py — Chrome Web Store API CLI.

Mirrors `~/AndroidStudioProjects/pulseboard/scripts/google-play-publisher.py`
(Google Play Publisher API) but targets the Chrome Web Store Items API v1.1:
https://developer.chrome.com/docs/webstore/using-api

Auth (two supported modes, in priority order):

  1. **Service Account + publisherEmail (default; pulseboard-compatible).**
     Reads SA private key JSON, mints a JWT-bearer assertion, exchanges
     for a Bearer token, attaches `publisherEmail=<dev account>` to every
     request. The SA must be registered as a member of the publisher's
     CWS account (Chrome Web Store dashboard → Account → Add member).

  2. **OAuth refresh-token (fallback / non-Workspace dev accounts).**
     Uses CHROME_OAUTH_CLIENT_ID + CHROME_OAUTH_CLIENT_SECRET +
     CHROME_OAUTH_REFRESH_TOKEN. Triggered when CHROME_SA_JSON env var
     is unset OR --auth oauth flag is passed. Use `auth-bootstrap`
     subcommand to capture the refresh_token via a one-time browser dance.

Required env vars (SA mode — default):
    CHROME_SA_JSON              Path to SA JSON (default: ~/.config/google-play/sa.json)
    CHROME_PUBLISHER_EMAIL      Publisher account email (e.g. chinu.ramraika@gmail.com)
    CHROME_EXTENSION_ID         Item ID (assigned on first POST /items)

Required env vars (OAuth mode):
    CHROME_OAUTH_CLIENT_ID
    CHROME_OAUTH_CLIENT_SECRET
    CHROME_OAUTH_REFRESH_TOKEN
    CHROME_EXTENSION_ID

Subcommands:
    auth-bootstrap    OAuth-only: capture refresh_token via local browser dance.
    insert            POST /items — creates NEW item; CWS assigns extension ID.
                      Use this for a fresh extension that doesn't have an ID yet.
    upload            PUT zip → /upload/...items/{id} (updates existing item).
    status            GET /items/{id} — return uploadState + draftStatus.
    publish           POST /items/{id}/publish?publishTarget=...

Common usage:
    # Create the item the first time (assigns extension ID):
    python3 scripts/chrome-store-publisher.py insert --zip dist/ext.zip

    # Update existing item:
    python3 scripts/chrome-store-publisher.py upload --zip dist/ext.zip

    # State check:
    python3 scripts/chrome-store-publisher.py status

    # Publish:
    python3 scripts/chrome-store-publisher.py publish --target trustedTesters
    python3 scripts/chrome-store-publisher.py publish --target default

References:
    https://developer.chrome.com/docs/webstore/using-api
    https://developer.chrome.com/docs/webstore/group-publishers
"""
from __future__ import annotations

import argparse
import base64
import http.server
import json
import os
import socketserver
import sys
import threading
import time
import urllib.error
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

DEFAULT_SA_PATH = Path(
    os.environ.get("CHROME_SA_JSON")
    or os.environ.get("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON")
    or (Path.home() / ".config" / "google-play" / "sa.json")
).expanduser()


class CredentialError(RuntimeError):
    """Raised when required credentials are missing."""


def _http(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    timeout: int = 120,
) -> tuple[int, dict[str, str], bytes]:
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


# ---------------------------------------------------------------------------
# Auth — SA-mode (default; leverages pulseboard's existing SA + GCP project)
# ---------------------------------------------------------------------------


def _b64url(b: bytes) -> bytes:
    return base64.urlsafe_b64encode(b).rstrip(b"=")


def get_sa_access_token() -> str:
    """Mint a chromewebstore-scoped access token from the service account JSON.

    Auth path: pulseboard-compatible. SA must be added as a member of the
    publisher's CWS account (operator-action; one-time browser step at
    https://chrome.google.com/webstore/devconsole → Account → Add member).
    """
    if not DEFAULT_SA_PATH.is_file():
        raise CredentialError(
            f"CHROME_SA_JSON not found at {DEFAULT_SA_PATH}. "
            f"Set CHROME_SA_JSON env or place sa.json there. "
            f"See docs/store/SETUP.md."
        )
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError as e:
        raise CredentialError(
            f"Missing dependency: {e.name}. Install with `pip install cryptography`."
        ) from e

    sa = json.loads(DEFAULT_SA_PATH.read_text())
    header = _b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    now = int(time.time())
    claim = {
        "iss": sa["client_email"],
        "scope": SCOPE,
        "aud": OAUTH_TOKEN_URL,
        "exp": now + 3600,
        "iat": now,
    }
    payload = _b64url(json.dumps(claim).encode())
    signing_input = header + b"." + payload
    key = serialization.load_pem_private_key(sa["private_key"].encode(), password=None)
    sig = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    jwt = signing_input + b"." + _b64url(sig)

    body = urllib.parse.urlencode(
        {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt.decode(),
        }
    ).encode()
    status, _, payload_bytes = _http(
        OAUTH_TOKEN_URL,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=body,
    )
    if status != 200:
        raise CredentialError(
            f"SA token exchange failed (HTTP {status}): "
            f"{payload_bytes.decode('utf-8', 'replace')}"
        )
    return json.loads(payload_bytes)["access_token"]


# ---------------------------------------------------------------------------
# Auth — OAuth refresh-token mode (fallback; pre-existing)
# ---------------------------------------------------------------------------


def get_oauth_access_token(args: argparse.Namespace) -> str:
    client_id = args.client_id or os.environ.get("CHROME_OAUTH_CLIENT_ID")
    client_secret = args.client_secret or os.environ.get("CHROME_OAUTH_CLIENT_SECRET")
    refresh_token = args.refresh_token or os.environ.get("CHROME_OAUTH_REFRESH_TOKEN")
    if not (client_id and client_secret and refresh_token):
        raise CredentialError(
            "OAuth mode requires CHROME_OAUTH_CLIENT_ID + CHROME_OAUTH_CLIENT_SECRET + "
            "CHROME_OAUTH_REFRESH_TOKEN. See docs/store/SETUP.md for one-time setup."
        )
    body = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    ).encode()
    status, _, payload = _http(
        OAUTH_TOKEN_URL,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=body,
    )
    if status != 200:
        raise CredentialError(
            f"OAuth token exchange failed (HTTP {status}): "
            f"{payload.decode('utf-8', 'replace')}"
        )
    return json.loads(payload)["access_token"]


def get_access_token(args: argparse.Namespace) -> str:
    """Pick SA or OAuth based on what's available; --auth flag forces."""
    mode = args.auth
    if mode == "oauth":
        return get_oauth_access_token(args)
    if mode == "sa":
        return get_sa_access_token()
    if DEFAULT_SA_PATH.is_file():
        return get_sa_access_token()
    return get_oauth_access_token(args)


def _bearer(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}", "x-goog-api-version": "2"}


def _publisher_query(args: argparse.Namespace) -> str:
    email = args.publisher_email or os.environ.get("CHROME_PUBLISHER_EMAIL")
    if not email:
        return ""
    return "publisherEmail=" + urllib.parse.quote(email)


def _join_query(*parts: str) -> str:
    parts = tuple(p for p in parts if p)
    return ("?" + "&".join(parts)) if parts else ""


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def cmd_auth_bootstrap(args: argparse.Namespace) -> int:
    """One-time interactive OAuth dance — captures refresh_token.

    Required ONLY for OAuth mode (when SA path isn't applicable).
    """
    client_id = args.client_id or os.environ.get("CHROME_OAUTH_CLIENT_ID")
    client_secret = args.client_secret or os.environ.get("CHROME_OAUTH_CLIENT_SECRET")
    if not (client_id and client_secret):
        print(
            "auth-bootstrap requires CHROME_OAUTH_CLIENT_ID + CHROME_OAUTH_CLIENT_SECRET.\n"
            "Create an OAuth Desktop client at https://console.cloud.google.com/apis/credentials.",
            file=sys.stderr,
        )
        return 2

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
            msg = "OK, close this tab." if ok else "FAILED, check terminal."
            self.wfile.write(f"<h2>Chrome Web Store auth — {msg}</h2>".encode())

        def log_message(self, *_: Any) -> None:
            pass

    with socketserver.TCPServer((REDIRECT_HOST, REDIRECT_PORT), Handler) as srv:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        print(f"Opening browser: {authz_url}")
        print(f"Listening on {redirect_uri} for ~5 min.")
        webbrowser.open(authz_url)
        deadline = time.time() + 300
        while time.time() < deadline and "code" not in received:
            time.sleep(1)
        srv.shutdown()

    if "code" not in received:
        print("Timed out waiting for OAuth callback.", file=sys.stderr)
        return 2
    if received.get("state") != state:
        print("State mismatch — aborting.", file=sys.stderr)
        return 3

    body = urllib.parse.urlencode(
        {
            "code": received["code"],
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
    ).encode()
    status, _, payload = _http(
        OAUTH_TOKEN_URL,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=body,
    )
    if status != 200:
        print(
            f"Token exchange failed (HTTP {status}): {payload.decode('utf-8', 'replace')}",
            file=sys.stderr,
        )
        return 4

    data = json.loads(payload)
    rt = data.get("refresh_token")
    if not rt:
        print(
            "No refresh_token. Revoke at https://myaccount.google.com/permissions "
            "and re-run.",
            file=sys.stderr,
        )
        return 5
    print("\n" + "=" * 60)
    print("CHROME_OAUTH_REFRESH_TOKEN:")
    print(rt)
    print("=" * 60)
    return 0


def cmd_insert(args: argparse.Namespace) -> int:
    """POST /items — creates a new CWS item. CWS assigns extension ID.

    Useful for first-time uploads. publisherEmail required when using SA mode.
    Prints the new extension ID — save it as CHROME_EXTENSION_ID for future
    uploads.
    """
    zip_path = Path(args.zip).resolve()
    if not zip_path.is_file():
        print(f"zip not found: {zip_path}", file=sys.stderr)
        return 2
    access = get_access_token(args)
    body = zip_path.read_bytes()
    url = f"{CWS_UPLOAD_BASE}/items{_join_query(_publisher_query(args))}"
    headers = {
        **_bearer(access),
        "Content-Type": "application/zip",
        "Content-Length": str(len(body)),
    }
    status, _, payload = _http(url, method="POST", headers=headers, data=body)
    print(f"HTTP {status}  ({len(body)} bytes)")
    try:
        decoded = json.loads(payload)
        print(json.dumps(decoded, indent=2))
        item_id = decoded.get("id")
        if item_id:
            print(f"\nExtension ID assigned: {item_id}")
            print("Save as CHROME_EXTENSION_ID env / GitHub secret.")
    except Exception:
        print(payload.decode("utf-8", "replace"))
    return 0 if status == 200 else 1


def cmd_upload(args: argparse.Namespace) -> int:
    """PUT package → /upload/items/{id}. Item must already exist (use insert first).

    Accepts either a .zip (CWS-managed signing) or a .crx (verified CRX uploads).
    A .crx must be signed with the RSA key registered on the dashboard's
    Verified CRX Uploads section, else CWS rejects it.
    """
    item_id = args.item_id or os.environ.get("CHROME_EXTENSION_ID")
    if not item_id:
        raise CredentialError(
            "CHROME_EXTENSION_ID not set. Run `insert` first to create the item."
        )
    pkg_path = Path(args.zip).resolve()
    if not pkg_path.is_file():
        print(f"package not found: {pkg_path}", file=sys.stderr)
        return 2
    is_crx = pkg_path.suffix.lower() == ".crx"
    access = get_access_token(args)
    body = pkg_path.read_bytes()
    url = f"{CWS_UPLOAD_BASE}/items/{item_id}{_join_query(_publisher_query(args))}"
    headers = {
        **_bearer(access),
        "Content-Length": str(len(body)),
    }
    if is_crx:
        # Verified CRX upload — per CWS docs the raw-upload headers are required.
        headers["Content-Type"] = "application/x-chrome-extension"
        headers["X-Goog-Upload-Protocol"] = "raw"
        headers["X-Goog-Upload-File-Name"] = pkg_path.name
    else:
        headers["Content-Type"] = "application/zip"
    status, _, payload = _http(url, method="PUT", headers=headers, data=body)
    print(f"HTTP {status}  ({len(body)} bytes uploaded, {'CRX' if is_crx else 'ZIP'})")
    try:
        decoded = json.loads(payload)
        print(json.dumps(decoded, indent=2))
        if decoded.get("uploadState", "").upper() == "FAILURE":
            print("Upload FAILURE — see itemError above.", file=sys.stderr)
            return 1
    except Exception:
        print(payload.decode("utf-8", "replace"))
    return 0 if status == 200 else 1


def cmd_status(args: argparse.Namespace) -> int:
    """GET /items/{id}?projection=DRAFT."""
    item_id = args.item_id or os.environ.get("CHROME_EXTENSION_ID")
    if not item_id:
        raise CredentialError("CHROME_EXTENSION_ID not set.")
    access = get_access_token(args)
    qs = _join_query("projection=DRAFT", _publisher_query(args))
    url = f"{CWS_API_BASE}/items/{item_id}{qs}"
    status, _, payload = _http(url, headers=_bearer(access))
    print(f"HTTP {status}")
    try:
        print(json.dumps(json.loads(payload), indent=2))
    except Exception:
        print(payload.decode("utf-8", "replace"))
    return 0 if status == 200 else 1


def cmd_publish(args: argparse.Namespace) -> int:
    """POST /items/{id}/publish?publishTarget=default|trustedTesters."""
    item_id = args.item_id or os.environ.get("CHROME_EXTENSION_ID")
    if not item_id:
        raise CredentialError("CHROME_EXTENSION_ID not set.")
    target = args.target
    if target not in ("default", "trustedTesters"):
        print("--target must be default|trustedTesters", file=sys.stderr)
        return 2
    access = get_access_token(args)
    qs = _join_query(f"publishTarget={target}", _publisher_query(args))
    url = f"{CWS_API_BASE}/items/{item_id}/publish{qs}"
    headers = {**_bearer(access), "Content-Length": "0"}
    status, _, payload = _http(url, method="POST", headers=headers, data=b"")
    print(f"HTTP {status}  target={target}")
    try:
        print(json.dumps(json.loads(payload), indent=2))
    except Exception:
        print(payload.decode("utf-8", "replace"))
    return 0 if status == 200 else 1


# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--auth",
        choices=["auto", "sa", "oauth"],
        default="auto",
        help="auth mode (auto picks SA if sa.json exists, else OAuth)",
    )
    p.add_argument("--client-id", help="override CHROME_OAUTH_CLIENT_ID (oauth mode)")
    p.add_argument(
        "--client-secret", help="override CHROME_OAUTH_CLIENT_SECRET (oauth mode)"
    )
    p.add_argument(
        "--refresh-token", help="override CHROME_OAUTH_REFRESH_TOKEN (oauth mode)"
    )
    p.add_argument(
        "--publisher-email",
        help="override CHROME_PUBLISHER_EMAIL (SA mode — owner of the CWS dev account)",
    )
    p.add_argument("--item-id", help="override CHROME_EXTENSION_ID")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("auth-bootstrap", help="One-time interactive OAuth dance.")

    ins = sub.add_parser("insert", help="POST /items — create a NEW item (assigns ID).")
    ins.add_argument("--zip", required=True)

    up = sub.add_parser("upload", help="PUT zip — update existing item.")
    up.add_argument("--zip", required=True)

    sub.add_parser("status", help="GET item state.")

    pub = sub.add_parser("publish", help="Publish item.")
    pub.add_argument(
        "--target", default="default", help="default | trustedTesters"
    )

    return p


def main() -> int:
    args = build_parser().parse_args()
    try:
        match args.cmd:
            case "auth-bootstrap":
                return cmd_auth_bootstrap(args)
            case "insert":
                return cmd_insert(args)
            case "upload":
                return cmd_upload(args)
            case "status":
                return cmd_status(args)
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
