#!/usr/bin/env python3
"""fast multithreaded tcp port scanner (stdlib only)."""

import argparse
import concurrent.futures
import socket
import sys
import time


def scan_port(host: str, port: int, timeout: float) -> tuple[int, str] | None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        if s.connect_ex((host, port)) == 0:
            try:
                svc = socket.getservbyport(port, "tcp")
            except OSError:
                svc = "unknown"
            return port, svc
    return None


def parse_ports(spec: str) -> list[int]:
    ports: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            ports.update(range(int(a), int(b) + 1))
        elif part:
            ports.add(int(part))
    return sorted(p for p in ports if 1 <= p <= 65535)


def main() -> None:
    p = argparse.ArgumentParser(description="fast multithreaded tcp port scanner")
    p.add_argument("host", nargs="?", default="127.0.0.1", help="target host (default: 127.0.0.1)")
    p.add_argument("-p", "--ports", default="1-1024", help="ports or ranges, e.g. 22,80,443,8000-8100")
    p.add_argument("-t", "--timeout", type=float, default=0.35, help="socket timeout in seconds")
    p.add_argument("-w", "--workers", type=int, default=120, help="thread count")
    args = p.parse_args()

    try:
        ip = socket.gethostbyname(args.host)
    except socket.gaierror as e:
        print(f"could not resolve {args.host}: {e}", file=sys.stderr)
        sys.exit(1)

    ports = parse_ports(args.ports)
    t0 = time.perf_counter()
    open_ports: list[tuple[int, str]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for res in ex.map(lambda pt: scan_port(ip, pt, args.timeout), ports):
            if res is not None:
                open_ports.append(res)

    dt = time.perf_counter() - t0
    print(f"scanned {len(ports)} ports on {args.host} ({ip}) in {dt:.2f}s")
    if not open_ports:
        print("no open ports found")
    else:
        for port, svc in sorted(open_ports):
            print(f"  {port:<6} open  ({svc})")


if __name__ == "__main__":
    main()
