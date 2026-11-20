"""Read-only probe of the Kreo 2.4G dongle (3554:FA09, 0xFF02/2).

Sends only a GetLED (cmd 0x44) query; never a write/set command.
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


def main() -> None:
    path = find_vendor_path()
    print(f"path={path}")

    dev = hid.device()
    dev.open_path(path.encode())

    try:
        query = build_wireless_frame(0x44, 0, 1, b"")
        print("query  :", query.hex(" "))
        written = dev.write(query)
        print("wrote  :", written)

        packets: dict[int, bytes] = {}
        total = None
        start = time.monotonic()
        last = start
        while time.monotonic() - start < 2.0:
            raw = dev.read(64, 100)
            if not raw:
                if total is None and time.monotonic() - start > 1.5:
                    break
                continue
            frame = bytes(raw).rstrip(b"\x00") if raw[0] != WIRELESS_REPORT_ID else bytes(raw)
            if frame and frame[0] == WIRELESS_REPORT_ID:
                frame = frame[1:]
            if len(frame) < 5:
                continue
            print("reply  :", bytes(raw).hex(" "))
            total = frame[1]
            idx = frame[2]
            packets[idx] = frame[4:18]
            last = time.monotonic()
            if total is not None and len(packets) >= total:
                break

        if total is None:
            print("RESULT : no reply within 1.5 s (device may be asleep)")
            return

        assembled = b"".join(packets.get(i, b"\x00" * 14) for i in range(total))
        print(f"RESULT : cmd=0x{frame[0]:02x} total_chunks={total} got={len(assembled)} bytes")
        print("payload:", assembled[:128].hex(" "))
    finally:
        dev.close()


if __name__ == "__main__":
    main()
