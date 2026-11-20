"""Read-only wireless probe: GetMatrix (cmd 0x41) for one layer.

Never sends a Set* command.
"""
from __future__ import annotations

import sys
import time

import hid

sys.path.insert(0, r"D:\Reverse-Any\kreo-control\backend\src")
from kreo_control.device.protocol import WIRELESS_REPORT_ID, build_wireless_frame  # noqa: E402

VENDOR, PRODUCT = 0x3554, 0xFA09
VENDOR_USAGE_PAGE, VENDOR_USAGE = 0xFF02, 0x0002


def find_vendor_path() -> str:
    for d in hid.enumerate(VENDOR, PRODUCT):
        if d.get("usage_page") == VENDOR_USAGE_PAGE and d.get("usage") == VENDOR_USAGE:
            return d["path"].decode()
    raise SystemExit("vendor 0xFF02/2 collection not found")


def read_cmd(dev: hid.device, cmd: int, layer: int, expected: int, timeout: float = 2.0) -> bytes:
    query = build_wireless_frame(cmd, 0, 1, b"", flag=layer)
    dev.write(query)

    packets: dict[int, tuple[bytes, int]] = {}
    total = None
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        raw = dev.read(64, 100)
        if not raw:
            if total is None and time.monotonic() - start > timeout - 0.5:
                break
            continue
        frame = bytes(raw)
        if frame[0] == WIRELESS_REPORT_ID:
            frame = frame[1:]
        if len(frame) < 5:
            continue
        if frame[0] not in (cmd, cmd | 0x80):
            print(f"  (skip cmd {frame[0]:#04x})")
            continue
        total = frame[1]
        idx = frame[2]
        length = frame[3] & 0x0F
        packets[idx] = (frame[4 : 4 + length], length)
        if total is not None and len(packets) >= total:
            break

    if total is None:
        raise SystemExit("no reply")
    data = b"".join(packets[i][0] for i in sorted(packets))
    print(f"cmd={cmd:#04x} layer={layer} chunks={total} assembled={len(data)}")
    return data[:expected]


def main() -> None:
    path = find_vendor_path()
    dev = hid.device()
    dev.open_path(path.encode())
    try:
        for layer in (0, 1):
            data = read_cmd(dev, 0x41, layer, 512)
            print(f"layer {layer} first 64 bytes: {data[:64].hex(' ')}")
            nonzero = [(i // 4, int.from_bytes(data[i : i + 4], 'little')) for i in range(0, len(data), 4)
                       if data[i : i + 4] != b'\x00\x00\x00\x00']
            print(f"layer {layer} assigned positions: {len(nonzero)}")
            print("  sample:", [(p, hex(v)) for p, v in nonzero[:12]])
            print("  tail  :", data[-16:].hex(' '))
    finally:
        dev.close()


if __name__ == "__main__":
    main()
