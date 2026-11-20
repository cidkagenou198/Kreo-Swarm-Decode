"""Read-only wired probe across the G5KB command space (Get* only)."""
from __future__ import annotations

import sys
import time

import hid

sys.path.insert(0, r"D:\Reverse-Any\kreo-control\backend\src")
sys.path.insert(0, r"D:\Reverse-Any\re_workdir")
from dump_caps_any import get_caps  # noqa: E402
from kreo_control.device.protocol import (  # noqa: E402
    G5KB_CHUNK_SIZE,
    G5KB_FEATURE_REPORT_SIZE,
    G5KB_REPORT_ID_FW_18,
    build_feature_frame,
    parse_feature_frame,
)

VID, PID = 0x258A, 0x010C
REPORT_ID = G5KB_REPORT_ID_FW_18


def feature_path(want: int) -> str:
    for d in hid.enumerate(VID, PID):
        if d["usage_page"] != 0xFF00 or d["usage"] != 1:
            continue
        p = d["path"].decode()
        caps = get_caps(p)
        if caps and caps.FeatureReportByteLength == want:
            return p
    raise SystemExit("no 520-byte feature collection")


def read_cmd(dev: hid.device, cmd: int, expected: int, param: int = 0) -> bytes:
    total = max(1, (expected + G5KB_CHUNK_SIZE - 1) // G5KB_CHUNK_SIZE)
    out = bytearray()
    for index in range(total):
        want = min(G5KB_CHUNK_SIZE, expected - len(out))
        req = build_feature_frame(
            cmd, b"", param=param, index=index, total=total,
            length=want, report_id=REPORT_ID,
        )
        dev.send_feature_report(req)
        time.sleep(0.02)
        raw = dev.get_feature_report(REPORT_ID, G5KB_FEATURE_REPORT_SIZE)
        reply = parse_feature_frame(REPORT_ID, bytes(raw))
        print(
            f"  cmd={cmd:#04x} idx={index}: raw={len(raw)} declared={len(reply)} "
            f"header={bytes(raw)[:8].hex(' ')}"
        )
        if len(reply) < want:
            print(f"    short reply ({len(reply)} < {want})")
        out += reply[:want]
        time.sleep(0.02)
    return bytes(out)


def main() -> None:
    dev = hid.device()
    dev.open_path(feature_path(G5KB_FEATURE_REPORT_SIZE).encode())
    try:
        for layer in (0, 1):
            data = read_cmd(dev, 0x83, 504, param=layer)
            nz = [
                (i // 4, data[i : i + 4].hex(), int.from_bytes(data[i : i + 4], "big"))
                for i in range(0, len(data) - 3, 4)
                if data[i : i + 4] != b"\x00\x00\x00\x00"
            ]
            print(f"  layer {layer}: {len(data)} bytes, {len(nz)} nonzero")
            print("  first:", [(p, hex(v)) for p, _, v in nz[:6]])

        g = read_cmd(dev, 0x86, 378)
        print(f"  game: {len(g)} bytes, plane max={[max(g[i*126:(i+1)*126]) for i in range(3)]}")

        t = read_cmd(dev, 0x8A, 512)
        print(f"  rgb-tab: {len(t)} bytes, %21={len(t) % 21}, tail={t[-8:].hex(' ')}")

        p = read_cmd(dev, 0x82, 6)
        print(f"  password: {len(p)} bytes")
    finally:
        dev.close()


if __name__ == "__main__":
    main()
