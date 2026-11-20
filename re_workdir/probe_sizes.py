"""Read-only probe with length-aware assembly and one retry per command."""
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


def attempt(dev, cmd: int, flag: int, wait: float) -> tuple[int | None, dict[int, tuple[int, bytes]]]:
    dev.write(build_wireless_frame(cmd, 0, 1, b"", flag=flag))
    chunks: dict[int, tuple[int, bytes]] = {}
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
        chunks[f[2]] = (f[3] & 0x0F, f[4:18])
        if len(chunks) >= total:
            break
    return total, chunks


def read(dev, cmd: int, flag: int = 0, wait: float = 3.0) -> bytes:
    for _ in range(2):
        total, chunks = attempt(dev, cmd, flag, wait)
        if total is not None and len(chunks) >= total:
            break
    if total is None:
        print(f"cmd {cmd:#04x}: no reply")
        return b""
    missing = [i for i in range(total) if i not in chunks]
    print(f"cmd {cmd:#04x}: total={total} received={len(chunks)} missing={missing}")
    data = b""
    for i in range(total):
        if i not in chunks:
            continue
        length, chunk = chunks[i]
        data += chunk[: (length if length else 14)]
    print(f"  declared bytes={len(data)}")
    return data


def main() -> None:
    dev = hid.device()
    dev.open_path(path().encode())
    try:
        g = read(dev, 0x42)
        if g:
            print("  len:", len(g), "planes:", [max(g[i * 126 : (i + 1) * 126]) for i in range(3)])
        t = read(dev, 0x49)
        if t:
            print("  len %21:", len(t) % 21, "entries:", len(t) / 21)
            print("  first 21:", t[:21].hex(" "))
            print("  last 6  :", t[-6:].hex(" "))
            print("  has 5A A5 anywhere:", t.find(b"\x5a\xa5"))
    finally:
        dev.close()


if __name__ == "__main__":
    main()
