#!/usr/bin/env python3
"""colorized hex dump and binary pattern inspector (stdlib only)."""

import argparse
import os
import sys


def hexdump(path: str, offset: int, length: int, width: int = 16) -> None:
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        f.seek(offset)
        data = f.read(length if length > 0 else size - offset)

    for i in range(0, len(data), width):
        chunk = data[i : i + width]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        print(f"{offset + i:08x}  {hex_part:<{width * 3 - 1}}  |{ascii_part}|")


def find_pattern(path: str, pattern: bytes) -> None:
    with open(path, "rb") as f:
        data = f.read()
    idx = 0
    hits = []
    while True:
        pos = data.find(pattern, idx)
        if pos == -1:
            break
        hits.append(pos)
        idx = pos + 1
    if not hits:
        print("no matches")
    else:
        for h in hits[:50]:
            print(f"match at 0x{h:08x} ({h})")
        if len(hits) > 50:
            print(f"...and {len(hits) - 50} more")


def main() -> None:
    p = argparse.ArgumentParser(description="hex dump and binary pattern finder")
    p.add_argument("file", help="binary file to inspect")
    p.add_argument("-o", "--offset", type=lambda x: int(x, 0), default=0, help="start offset (dec or 0xhex)")
    p.add_argument("-n", "--bytes", type=int, default=256, help="bytes to display (0 = all)")
    p.add_argument("-f", "--find", help="ascii string to search for")
    p.add_argument("-x", "--find-hex", help="hex bytes to search for, e.g. 55aa")
    args = p.parse_args()

    if not os.path.isfile(args.file):
        print(f"file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    if args.find:
        find_pattern(args.file, args.find.encode("utf-8"))
    elif args.find_hex:
        find_pattern(args.file, bytes.fromhex(args.find_hex.replace(" ", "")))
    else:
        hexdump(args.file, args.offset, args.bytes)


if __name__ == "__main__":
    main()
