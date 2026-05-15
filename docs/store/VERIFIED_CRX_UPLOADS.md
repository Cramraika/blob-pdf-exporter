# Verified CRX Uploads — setup

[Verified CRX Uploads](https://developer.chrome.com/blog/verified-uploads-cws) is a Chrome Web Store opt-in (May 2025+) that requires every future package update to be a CRX3 signed with an RSA private key you control. Uploads not signed by the registered key are rejected — a supply-chain guard even if your CWS account is compromised.

This repo is wired for it. The keypair is generated, the signer is built, CI is ready. **One operator action remains: paste the public key + opt in on the dashboard.**

## What's already done (this session)

- RSA-2048 keypair generated via `openssl genpkey`.
- Private key stored:
  - locally at `~/.config/cws-crx/privatekey.pem` (chmod 600, outside any repo)
  - as GitHub Actions secret `CHROME_CRX_PRIVATE_KEY_B64` (base64)
- `scripts/pack-crx.py` — pure-Python CRX3 signer (no Chrome binary needed).
- `scripts/chrome-store-publisher.py` — `upload` accepts `.crx` with the
  `X-Goog-Upload-Protocol: raw` headers CWS requires for verified uploads.
- `Makefile` — `make crx`, `make upload-crx`, `make ship-trusted/ship-public`
  (now CRX-based).
- `.github/workflows/store-release.yml` — signs + uploads CRX when the
  two-gate switch is on.
- Repo variable `CRX_OPTED_IN` = `false` (the safety gate).

## The public key — paste THIS in the dashboard

```
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAimMj0uDhnE3cLDKICPsw
chcSzyq/TBJh9mjRkEW/PqILvHGbHeRse2crruMT+4goPAd7sYdtqLmv3OOBOP8T
TZ+1b+yDxyoJkXyXW4qOu1sjNz7S3KFTfaxTkgZMeFRrFJ3Cv2hvTjcNihWvTclQ
TLSY2EODnVWp56acKv2xbkdmUbxHiBSoKvaUdsnj11f/g8E0K8+w4+S6FlHwGVvj
IsvSnx5Y7HgS9wYevG1hufNgsE3A5yyr//JtKCHatVKkjZZeD3EQUH6uPoZSUjPx
A+Rmlx2g4vJ+aZrvSAtNqRc7oSST5qbmzXr3pSY2kWp1h+3XtePC/AyPaha2xjX2
MQIDAQAB
-----END PUBLIC KEY-----
```

SHA-256 of the public key (DER): `aa4397b45d90a20404754ced21e9a6eb2b186f5fcfe2442403941206e4acb2df`

You can re-derive this any time:
```bash
openssl rsa -in ~/.config/cws-crx/privatekey.pem -pubout
```

## Operator steps (one-time, ~2 min)

### 1. Opt in on the dashboard

1. Open the dashboard → your item → **Package** tab.
2. Find the **Verified CRX Uploads** section → **Opt In**.
3. Paste the public key block above into the "Public key" field.
4. Confirm.

### 2. Flip the CI gate

```bash
cd ~/Documents/Github/blob-pdf-exporter
gh variable set CRX_OPTED_IN --body true
```

That's it. From now on:
- `git tag vX.Y.Z && git push --tags` → CI signs a CRX with the private key + uploads it.
- `make ship-public` locally does the same.

## Risk acknowledgment

⚠️ **If you lose `~/.config/cws-crx/privatekey.pem` AND the `CHROME_CRX_PRIVATE_KEY_B64` GitHub secret, you cannot update this extension** — you'd have to contact Chrome Web Store support to opt back out (up to ~1 week turnaround).

Mitigations in place:
- Two independent copies: local file + GitHub secret.
- Recommended: also back up `~/.config/cws-crx/privatekey.pem` to your password manager or an encrypted backup.

```bash
# Verify the local key is intact at any time:
openssl rsa -in ~/.config/cws-crx/privatekey.pem -check -noout
```

## How the CRX signing works (technical)

`scripts/pack-crx.py` builds a CRX3 container:

```
"Cr24"  +  uint32(3)  +  uint32(header_len)  +  CrxFileHeader  +  zip_payload
```

The `CrxFileHeader` protobuf carries an `AsymmetricKeyProof` (public key + RSA-SHA256 signature) and a `SignedData` (crx_id = first 16 bytes of SHA256(public key)). The signature covers:

```
"CRX3 SignedData\x00" + uint32_LE(len(signed_header)) + signed_header + zip_bytes
```

CWS verifies this signature against the registered public key, then **repackages with its own distribution key** — so the public store extension ID (`nkaleipmbbceglfkjkjognhkfimjogol`-class) is unchanged. The verified-upload key is purely an upload-time gate.

## Reverting

To opt back out: contact Chrome Web Store support (there's no self-serve opt-out). Then:
```bash
gh variable set CRX_OPTED_IN --body false
```
and CI reverts to ZIP uploads.

## References

- [Verified uploads in the Chrome Web Store](https://developer.chrome.com/blog/verified-uploads-cws)
- [Protect package updates](https://developer.chrome.com/docs/webstore/update#protect-package-updates)
- CRX3 format: [chromium crx_file component](https://chromium.googlesource.com/chromium/src/+/main/components/crx_file/)
