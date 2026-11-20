"""Read-only probe: GetGame (0x42) and GetLedRgbTab (0x49)."""
from __future__ import annotations

import sys
import time

import hid

sys.path.insert(0, r"D:\Reverse-Any\kreo-control\backend\src")
from kreo_control.device.protocol import WIRELESS_REPORT_ID, build_wireless_frame  # noqa: E402

VENDOR, PRODUCT = 0x3554, 0xFA09
USAGE_PAGE, USAGE = 0xFF02, 0x0002


def path() -> str:
    for d in hid.enumerate(VENDOR, PRODUCT):
        if d.get("usage_page") == USAGE_PAGE and d.get("usage") == USAGE:
            return d["path"].decode()
    raise SystemExit("not found")


def read(dev, cmd: int, flag: int, wait: float = 2.0) -> bytes:
    dev.write(build_wireless_frame(cmd, 0, 1, b"", flag=flag))
    chunks: dict[int, bytes] = {}
    total = None
    start = time.monotonic()
    while time.monotonic() - start < wait:
        raw = dev.read(64, 100)
        if not raw:
            continue
        f = bytes(raw)
        if f[0] == WIRELESS_REPORT_ID:
            f = f[1:]
        if len(f) < 19 or f[0] not in (cmd, cmd | 0x80):
            continue
        total = f[1]
        chunks[f[2]] = f[4:18]
        if len(chunks) >= total:
            break
    if total is None:
        print(f"cmd {cmd:#04x} flag {flag}: no reply")
        return b""
    data = b"".join(chunks[i] for i in sorted(chunks))
    print(f"cmd {cmd:#04x} flag {flag}: total={total} bytes={len(data)}")
    return data


def main() -> None:
    dev = hid.device()
    dev.open_path(path().encode())
    try:
        for flag in (0,):
            g = read(dev, 0x42, flag)
            if g:
                print("  game[0:32]:", g[:32].hex(" "))
                print("  game[-16:]:", g[-16:].hex(" "))
                print("  plane max R/G/B:", max(g[0:126]), max(g[126:252]), max(g[252:378]))
                print("  beyond 378 all zero:", all(b == 0 for b in g[378:]))
        t = read(dev, 0x49, 0)
        if t:
            print("  rgb-tab[0:42]:", t[:42].hex(" "))
            print("  rgb-tab[-8:]:", t[-8:].hex(" "))
            print("  last-2 == 5A A5:", t[-2:] == b"\x5a\xa5")
    finally:
        dev.close()


if __name__ == "__main__":
    main()
