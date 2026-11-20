"""Read-only wired probe: GetLED (cmd 0x84) over HID feature reports.

Tries report IDs 0x06 and 0x09. Sends only Get commands.
"""
from __future__ import annotations

import sys
import time

import hid

sys.path.insert(0, r"D:\Reverse-Any\kreo-control\backend\src")
sys.path.insert(0, r"D:\Reverse-Any\re_workdir")
from dump_caps_any import get_caps  # noqa: E402
from kreo_control.device.protocol import (  # noqa: E402
    G5KB_FEATURE_REPORT_SIZE,
    build_feature_frame,
)

VID, PID = 0x258A, 0x010C
USAGE_PAGE, USAGE = 0xFF00, 0x0001


def feature_path(want: int) -> str:
    for d in hid.enumerate(VID, PID):
        if d["usage_page"] != USAGE_PAGE or d["usage"] != USAGE:
            continue
        p = d["path"].decode()
        caps = get_caps(p)
        if caps and caps.FeatureReportByteLength == want:
            return p
    raise SystemExit(f"no 0xFF00/1 collection with feature={want}")


def try_read(dev: hid.device, report_id: int, cmd: int, expected: int) -> bytes | None:
    request = build_feature_frame(cmd, b"", length=expected, report_id=report_id)
    try:
        n = dev.send_feature_report(request)
    except Exception as exc:
        print(f"  report id {report_id:#04x}: SetFeature failed: {exc}")
        return None
    print(f"  report id {report_id:#04x}: SetFeature wrote {n} bytes")

    for attempt in range(3):
        try:
            raw = dev.get_feature_report(report_id, G5KB_FEATURE_REPORT_SIZE)
        except Exception as exc:
            print(f"    GetFeature attempt {attempt + 1} failed: {exc}")
            time.sleep(0.05)
            continue
        if not raw:
            print(f"    GetFeature attempt {attempt + 1}: empty")
            time.sleep(0.05)
            continue
        data = bytes(raw)
        print(f"    reply [{len(data)}]: {data[:24].hex(' ')} ... {data[-4:].hex(' ')}")
        rid, rcmd = data[0], data[1]
        length = int.from_bytes(data[6:8], "little") if len(data) >= 8 else -1
        print(f"    rid={rid:#04x} cmd={rcmd:#04x} total={data[4]} idx={data[5]} len={length}")
        if rcmd in (cmd, cmd | 0x80) and 0 < length <= G5KB_FEATURE_REPORT_SIZE - 8:
            return data[8 : 8 + min(length, expected)]
        time.sleep(0.05)
    return None


def main() -> None:
    path = feature_path(G5KB_FEATURE_REPORT_SIZE)
    print(f"feature path={path}")

    dev = hid.device()
    dev.open_path(path.encode())
    try:
        for report_id in (0x06, 0x09):
            payload = try_read(dev, report_id, 0x84, 128)
            if payload:
                print(f"  RESULT rid={report_id:#04x}: {len(payload)} bytes")
                print(f"  profile[0:32]={payload[:32].hex(' ')}")
                print(f"  marker[54:64]={payload[54:64].hex(' ')}")
                print(f"  tail[124:128]={payload[124:128].hex(' ')}")
                return
            print(f"  rid={report_id:#04x}: no valid reply")
        print("no report ID produced a valid reply")
    finally:
        dev.close()


if __name__ == "__main__":
    main()
