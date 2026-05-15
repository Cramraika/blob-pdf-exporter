#!/usr/bin/env python3
"""
pack-crx.py — pure-Python CRX3 packer/signer for Chrome Web Store verified uploads.

Chrome Web Store "Verified CRX Uploads" (opt-in, May 2025+) requires every
package update to be a CRX3 file signed with a registered RSA private key.
This script builds that CRX3 from a plain extension ZIP.

CRX3 wire format:
    "Cr24"               magic                       (4 bytes)
    version = 3          uint32 little-endian         (4 bytes)
    header_length        uint32 little-endian         (4 bytes)
    header               CrxFileHeader protobuf       (header_length bytes)
    payload              the extension ZIP bytes      (rest)

CrxFileHeader (protobuf, field numbers):
    field 2  (repeated AsymmetricKeyProof)  sha256_with_rsa
    field 10000 (bytes)                     signed_header_data  (a SignedData msg)

AsymmetricKeyProof:
    field 1 (bytes)  public_key   — DER SubjectPublicKeyInfo
    field 2 (bytes)  signature    — RSA PKCS#1 v1.5 over the signed payload

SignedData:
    field 1 (bytes)  crx_id       — first 16 bytes of SHA256(public_key DER)

Signature is RSA-SHA256 over:
    b"CRX3 SignedData\\x00"
    + uint32_LE(len(signed_header_data))
    + signed_header_data
    + zip_bytes

Refs:
    https://developer.chrome.com/docs/webstore/update#protect-package-updates
    https://chromium.googlesource.com/chromium/src/+/main/components/crx_file/

No third-party deps beyond `cryptography` (already required by the publisher).

Usage:
    python3 scripts/pack-crx.py --zip dist/blob-pdf-exporter-v0.1.3.zip \\
        --key ~/.config/cws-crx/privatekey.pem \\
        --out dist/blob-pdf-exporter-v0.1.3.crx
"""
from __future__ import annotations

import argparse
import hashlib
import struct
import sys
from pathlib import Path


def _varint(n: int) -> bytes:
    """Encode an int as a protobuf base-128 varint."""
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def _tag(field_number: int, wire_type: int) -> bytes:
    return _varint((field_number << 3) | wire_type)


def _len_delimited(field_number: int, value: bytes) -> bytes:
    """Encode a length-delimited (wire type 2) protobuf field."""
    return _tag(field_number, 2) + _varint(len(value)) + value


def build_crx3(zip_bytes: bytes, private_key_pem: bytes) -> bytes:
    """Return signed CRX3 bytes for the given ZIP payload + RSA private key."""
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding, rsa
    except ImportError as e:  # pragma: no cover
        raise SystemExit(
            f"Missing dependency {e.name}; install with `pip install cryptography`."
        ) from e

    key = serialization.load_pem_private_key(private_key_pem, password=None)
    if not isinstance(key, rsa.RSAPrivateKey):
        raise SystemExit("Private key must be RSA (Chrome Web Store requirement).")

    pub = key.public_key()
    pub_der = pub.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # crx_id = first 16 bytes of SHA256(public key DER)
    crx_id = hashlib.sha256(pub_der).digest()[:16]

    # SignedData message: field 1 = crx_id
    signed_header_data = _len_delimited(1, crx_id)

    # Signature is over a fixed-prefix framing.
    to_sign = (
        b"CRX3 SignedData\x00"
        + struct.pack("<I", len(signed_header_data))
        + signed_header_data
        + zip_bytes
    )
    signature = key.sign(to_sign, padding.PKCS1v15(), hashes.SHA256())

    # AsymmetricKeyProof: field 1 = public_key, field 2 = signature
    proof = _len_delimited(1, pub_der) + _len_delimited(2, signature)

    # CrxFileHeader: field 2 = sha256_with_rsa proof, field 10000 = signed_header_data
    header = _len_delimited(2, proof) + _len_delimited(10000, signed_header_data)

    # Assemble the CRX3 container.
    return (
        b"Cr24"
        + struct.pack("<I", 3)
        + struct.pack("<I", len(header))
        + header
        + zip_bytes
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--zip", required=True, help="Path to the extension ZIP.")
    p.add_argument(
        "--key",
        default=str(Path.home() / ".config" / "cws-crx" / "privatekey.pem"),
        help="Path to the RSA private key PEM "
        "(default: ~/.config/cws-crx/privatekey.pem).",
    )
    p.add_argument(
        "--out",
        help="Output CRX path (default: same as --zip but with .crx extension).",
    )
    args = p.parse_args()

    zip_path = Path(args.zip).resolve()
    if not zip_path.is_file():
        print(f"zip not found: {zip_path}", file=sys.stderr)
        return 2

    key_path = Path(args.key).expanduser()
    if not key_path.is_file():
        print(
            f"private key not found: {key_path}\n"
            f"Generate with: openssl genpkey -algorithm RSA "
            f"-pkeyopt rsa_keygen_bits:2048 -out {key_path}",
            file=sys.stderr,
        )
        return 2

    out_path = (
        Path(args.out).resolve()
        if args.out
        else zip_path.with_suffix(".crx")
    )

    crx = build_crx3(zip_path.read_bytes(), key_path.read_bytes())
    out_path.write_bytes(crx)

    print(f"wrote {out_path} ({len(crx)} bytes)")
    print("  magic: Cr24  version: 3")
    print(f"  sha256: {hashlib.sha256(crx).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
