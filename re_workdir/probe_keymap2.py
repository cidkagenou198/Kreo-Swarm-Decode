"""Read-only: GetMatrix (0x41) full layer, always consuming 14 data bytes/chunk."""
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


def read_layer(dev: hid.device, layer: int) -> bytes:
    dev.write(build_wireless_frame(0x41, 0, 1, b"", flag=layer))
    chunks: dict[int, bytes] = {}
    total = None
    start = time.monotonic()
    while time.monotonic() - start < 2.5:
        raw = dev.read(64, 100)
        if not raw:
            continue
        f = bytes(raw)
        if f[0] == WIRELESS_REPORT_ID:
            f = f[1:]
        if len(f) < 19 or f[0] not in (0x41, 0xC1):
            continue
        total = f[1]
        chunks[f[2]] = f[4:18]  # always 14
        if len(chunks) >= total:
            break
    if total is None:
        raise SystemExit("no reply")
    print(f"layer {layer}: total={total} chunks, bytes={total * 14}")
    return b"".join(chunks[i] for i in sorted(chunks))[: total * 14]


def main() -> None:
    dev = hid.device()
    dev.open_path(path().encode())
    try:
        for layer in (0, 1, 2, 3):
            data = read_layer(dev, layer)
            pos = [
                (i // 4, data[i : i + 4].hex(), int.from_bytes(data[i : i + 4], "big"))
                for i in range(0, len(data) - 3, 4)
            ]
            nonzero = [p for p in pos if p[2] != 0]
            print(f"  nonzero records: {len(nonzero)} / {len(pos)}")
            if layer == 0:
                print("  first 8:", [(p, hex(v)) for p, _, v in nonzero[:8]])
                print("  last 6 :", [(p, hex(v)) for p, _, v in nonzero[-6:]])
                print("  raw 480..504:", data[480:504].hex(" "))
            if layer == 1:
                print("  fn1 non-zero:", [(p, hex(v)) for p, _, v in nonzero[:10]])
            if layer >= 2:
                print("  all-zero:", all(v == 0 for _, _, v in pos))
    finally:
        dev.close()


if __name__ == "__main__":
    main()
