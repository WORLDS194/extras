#!/usr/bin/env python3
"""fast duplicate file finder using size buckets + sha256."""

import argparse
import collections
import hashlib
import os


def file_hash(path: str, chunk: int = 65536) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while data := f.read(chunk):
            h.update(data)
    return h.hexdigest()


def find_dupes(root: str, min_size: int) -> list[list[str]]:
    by_size: dict[int, list[str]] = collections.defaultdict(list)
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                if os.path.islink(path):
                    continue
                sz = os.path.getsize(path)
                if sz >= min_size:
                    by_size[sz].append(path)
            except OSError:
                pass

    by_hash: dict[str, list[str]] = collections.defaultdict(list)
    for sz, paths in by_size.items():
        if len(paths) < 2:
            continue
        for p in paths:
            try:
                by_hash[f"{sz}:{file_hash(p)}"].append(p)
            except OSError:
                pass

    return [paths for paths in by_hash.values() if len(paths) > 1]


def main() -> None:
    p = argparse.ArgumentParser(description="find duplicate files in a directory")
    p.add_argument("dir", nargs="?", default=".", help="directory to scan")
    p.add_argument("--min-bytes", type=int, default=1, help="ignore files smaller than this")
    args = p.parse_args()

    groups = find_dupes(os.path.abspath(args.dir), args.min_bytes)
    if not groups:
        print("no duplicate files found")
        return

    wasted = 0
    for i, g in enumerate(groups, 1):
        sz = os.path.getsize(g[0])
        wasted += sz * (len(g) - 1)
        print(f"group {i} ({sz:,} bytes each):")
        for path in g:
            print(f"  {path}")
    print(f"\n{len(groups)} duplicate group(s), {wasted / (1024 * 1024):.2f} mb reclaimable")


if __name__ == "__main__":
    main()
