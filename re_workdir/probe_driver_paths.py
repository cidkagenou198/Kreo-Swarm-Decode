"""Read-only validation of kreo_control's new read paths on real hardware.

Uses only Get* commands. No Set* / write report is ever sent.
"""
from __future__ import annotations

import sys

import hid

sys.path.insert(0, r"D:\Reverse-Any\kreo-control\backend\src")
sys.path.insert(0, r"D:\Reverse-Any\re_workdir")

from dump_caps_any import get_caps  # noqa: E402
from kreo_control.device import protocol as p  # noqa: E402
from kreo_control.device.transport import HidTransport  # noqa: E402


def wired_path() -> str:
    for d in hid.enumerate(0x258A, 0x010C):
        if d["usage_page"] == 0xFF00 and d["usage"] == 1:
            pth = d["path"].decode()
            caps = get_caps(pth)
            if caps and caps.FeatureReportByteLength == 520:
                return pth
    raise SystemExit("wired 520-byte feature collection not found")


def wireless_path() -> str:
    for d in hid.enumerate(0x3554, 0xFA09):
        if d["usage_page"] == 0xFF02 and d["usage"] == 2:
            return d["path"].decode()
    raise SystemExit("dongle 0xFF02/2 collection not found")


def describe(layer: bytes, name: str) -> None:
    actions = p.decode_keymap_layer(layer)
    used = [a for a in actions if a.kind != "empty"]
    print(f"  {name}: {len(layer)} bytes, {len(used)} assigned")
    for a in used[:6]:
        print(
            f"    pos {a.position:3d} page {a.page:#04x} value {a.value:#08x} "
            f"kind {a.kind} usage {a.hid_usage if a.hid_usage is None else hex(a.hid_usage)} "
            f"mod {a.modifier_mask}"
        )


def main() -> None:
    print("== wired 258A:010C ==")
    with HidTransport(wired_path()) as t:
        prof = p.read_profile_wired(t)
        print(f"  profile: {len(prof)} bytes, tail {prof[-2:].hex(' ')}")
        for layer in (0, 1):
            describe(p.read_keymap_wired(t, layer), f"layer {layer}")
        table = p.read_light_table_wired(t)
        entries, trailer = p.split_rgb_table(table) if len(table) >= 490 else ([], b"")
        print(f"  light table: {len(table)} bytes, entries={len(entries)}, trailer={trailer.hex(' ')}")

    print("== wireless 3554:FA09 ==")
    with HidTransport(wireless_path()) as t:
        prof = p.read_profile_wireless(t)
        print(f"  profile: {len(prof)} bytes, tail {prof[-2:].hex(' ')}")
        for layer in (0, 1):
            describe(p.read_keymap_wireless(t, layer), f"layer {layer}")
        table = p.read_light_table_wireless(t)
        entries, trailer = p.split_rgb_table(table) if len(table) >= 490 else ([], b"")
        print(f"  light table: {len(table)} bytes, entries={len(entries)}, trailer={trailer.hex(' ')}")


if __name__ == "__main__":
    main()
