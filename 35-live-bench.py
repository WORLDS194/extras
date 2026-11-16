#!/usr/bin/env python3
"""quick pure-python cpu, hash, and disk micro-benchmark."""

import argparse
import hashlib
import os
import tempfile
import time


def bench_primes(limit: int = 120_000) -> float:
    t0 = time.perf_counter()
    sieve = bytearray([1]) * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for i in range(2, int(limit ** 0.5) + 1):
        if sieve[i]:
            sieve[i * i : limit + 1 : i] = b"\x00" * len(range(i * i, limit + 1, i))
    return time.perf_counter() - t0


def bench_sha256(mb: int = 128) -> float:
    block = os.urandom(1024 * 1024)
    t0 = time.perf_counter()
    h = hashlib.sha256()
    for _ in range(mb):
        h.update(block)
    _ = h.digest()
    dt = time.perf_counter() - t0
    return mb / dt


def bench_disk(mb: int = 64) -> tuple[float, float]:
    data = os.urandom(1024 * 1024)
    with tempfile.NamedTemporaryFile(delete=True) as f:
        t0 = time.perf_counter()
        for _ in range(mb):
            f.write(data)
        f.flush()
        os.fsync(f.fileno())
        w_speed = mb / (time.perf_counter() - t0)

        f.seek(0)
        t1 = time.perf_counter()
        while f.read(1024 * 1024):
            pass
        r_speed = mb / (time.perf_counter() - t1)
    return w_speed, r_speed


def main() -> None:
    p = argparse.ArgumentParser(description="pure-python cpu, sha256, and disk benchmark")
    p.add_argument("--mb", type=int, default=64, help="megabytes for hash and disk tests")
    args = p.parse_args()

    print(f"running on {os.cpu_count()} logical cores...")
    sieve_dt = bench_primes()
    hash_mbps = bench_sha256(args.mb)
    w_mbps, r_mbps = bench_disk(args.mb)

    print(f"  sieve (120k primes): {sieve_dt * 1000:.2f} ms")
    print(f"  sha256 throughput:   {hash_mbps:.1f} mb/s")
    print(f"  disk write (fsync):  {w_mbps:.1f} mb/s")
    print(f"  disk read (cached):  {r_mbps:.1f} mb/s")


if __name__ == "__main__":
    main()
