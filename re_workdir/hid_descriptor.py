"""Read the HID report descriptor of a device path (read-only) and decode IDs."""
from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes as w

import hid

GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
INVALID_HANDLE_VALUE = w.HANDLE(-1).value
IOCTL_HID_GET_REPORT_DESCRIPTOR = 0x000B0003


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.CreateFileW.restype = w.HANDLE
kernel32.CreateFileW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, w.LPVOID, w.DWORD, w.DWORD, w.HANDLE]
kernel32.DeviceIoControl.argtypes = [
    w.HANDLE, w.DWORD, w.LPVOID, w.DWORD, w.LPVOID, w.DWORD,
    ctypes.POINTER(w.DWORD), w.LPVOID,
]
kernel32.DeviceIoControl.restype = w.BOOL


def descriptor(path: str) -> bytes:
    h = kernel32.CreateFileW(
        path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, None, OPEN_EXISTING, 0, None
    )
    if h == INVALID_HANDLE_VALUE:
        raise OSError(ctypes.get_last_error(), "CreateFileW failed")
    try:
        buf = ctypes.create_string_buffer(8192)
        returned = w.DWORD(0)
        ok = kernel32.DeviceIoControl(
            h, IOCTL_HID_GET_REPORT_DESCRIPTOR, None, 0,
            buf, len(buf), ctypes.byref(returned), None,
        )
        if not ok:
            raise OSError(ctypes.get_last_error(), "DeviceIoControl failed")
        return buf.raw[: returned.value]
    finally:
        kernel32.CloseHandle(h)


SHORT = {-4: 0, -3: 1, -2: 2, -1: 3}
# item prefix -> (size index, type, tag)


def decode(desc: bytes) -> None:
    i = 0
    rid = 0
    report_size = 0
    report_count = 0
    usage_page = 0
    usages: list[int] = []
    print(f"descriptor length {len(desc)}")
    while i < len(desc):
        prefix = desc[i]
        size = prefix & 0x03
        size = 4 if size == 3 else size
        itype = (prefix >> 2) & 0x03
        tag = (prefix >> 4) & 0x0F
        data = desc[i + 1 : i + 1 + size]
        val = int.from_bytes(data, "little") if data else 0

        if itype == 1:  # global
            if tag == 0:
                usage_page = val
            elif tag == 7:
                report_size = val
            elif tag == 8:
                rid = val
            elif tag == 9:
                report_count = val
        elif itype == 2:  # local
            if tag == 0:
                usages.append(val)
        elif itype == 0:  # main
            kind = {8: "input", 9: "output", 11: "feature"}.get(tag)
            if kind:
                nbytes = (report_size * report_count + 7) // 8
                print(
                    f"  rid={rid:#04x} {kind:8s} bits={report_size} count={report_count} "
                    f"bytes={nbytes} page={usage_page:#06x} usages={[hex(u) for u in usages[:4]]}"
                )
            usages = []
        i += 1 + size


def main() -> None:
    vid = int(sys.argv[1], 16)
    pid = int(sys.argv[2], 16)
    want_page = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0xFF00
    seen = set()
    for d in hid.enumerate(vid, pid):
        if d["usage_page"] != want_page:
            continue
        p = d["path"].decode()
        if p in seen:
            continue
        seen.add(p)
        print(f"\n== {p}")
        try:
            desc = descriptor(p)
        except OSError as exc:
            print(f"  descriptor error: {exc}")
            continue
        print(desc.hex(" "))
        decode(desc)


if __name__ == "__main__":
    main()
