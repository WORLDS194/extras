#!/usr/bin/env python3
"""stdlib-only authenticated stream cipher packer (sha256 keystream + hmac)."""

import argparse
import getpass
import hashlib
import hmac
import os
import sys

MAGIC = b"CPACK1"


def keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < length:
        out.extend(hashlib.sha256(key + nonce + counter.to_bytes(8, "big")).digest())
        counter += 1
    return bytes(out[:length])


def derive_keys(password: str, salt: bytes) -> tuple[bytes, bytes]:
    master = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000, dklen=64)
    return master[:32], master[32:]


def encrypt_bytes(data: bytes, password: str) -> bytes:
    salt = os.urandom(16)
    nonce = os.urandom(16)
    enc_key, mac_key = derive_keys(password, salt)
    ks = keystream(enc_key, nonce, len(data))
    ct = bytes(a ^ b for a, b in zip(data, ks))
    tag = hmac.new(mac_key, MAGIC + salt + nonce + ct, hashlib.sha256).digest()
    return MAGIC + salt + nonce + tag + ct


def decrypt_bytes(blob: bytes, password: str) -> bytes:
    if len(blob) < 70 or not blob.startswith(MAGIC):
        raise ValueError("invalid file header")
    salt = blob[6:22]
    nonce = blob[22:38]
    tag = blob[38:70]
    ct = blob[70:]
    enc_key, mac_key = derive_keys(password, salt)
    expected = hmac.new(mac_key, MAGIC + salt + nonce + ct, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected):
        raise ValueError("wrong password or corrupted data")
    ks = keystream(enc_key, nonce, len(ct))
    return bytes(a ^ b for a, b in zip(ct, ks))


def main() -> None:
    p = argparse.ArgumentParser(description="encrypt or decrypt files with password (stdlib only)")
    p.add_argument("mode", choices=["enc", "dec"], help="encrypt or decrypt")
    p.add_argument("input", help="input file path")
    p.add_argument("-o", "--output", help="output file path")
    p.add_argument("-k", "--key", help="password (prompts if omitted)")
    args = p.parse_args()

    pw = args.key if args.key is not None else getpass.getpass("password: ")
    with open(args.input, "rb") as f:
        raw = f.read()

    try:
        res = encrypt_bytes(raw, pw) if args.mode == "enc" else decrypt_bytes(raw, pw)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    out_path = args.output or (args.input + ".cpack" if args.mode == "enc" else args.input.removesuffix(".cpack") + ".dec")
    with open(out_path, "wb") as f:
        f.write(res)
    print(f"wrote {out_path} ({len(res)} bytes)")


if __name__ == "__main__":
    main()
