"""Read-only HID capability dump for any VID/PID. No reports are written."""
from __future__ import annotations

import ctypes
import struct
import sys
from ctypes import wintypes as w

import hid as hidapi

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
INVALID_HANDLE_VALUE = w.HANDLE(-1).value
HIDP_STATUS_SUCCESS = 0x00110000


class HIDP_CAPS(ctypes.Structure):
    _fields_ = [
        ("Usage", w.USHORT),
        ("UsagePage", w.USHORT),
        ("InputReportByteLength", w.USHORT),
        ("OutputReportByteLength", w.USHORT),
        ("FeatureReportByteLength", w.USHORT),
        ("Reserved", w.USHORT * 17),
        ("NumberLinkCollectionNodes", w.USHORT),
        ("NumberInputButtonCaps", w.USHORT),
        ("NumberInputValueCaps", w.USHORT),
        ("NumberInputDataIndices", w.USHORT),
        ("NumberOutputButtonCaps", w.USHORT),
        ("NumberOutputValueCaps", w.USHORT),
        ("NumberOutputDataIndices", w.USHORT),
        ("NumberFeatureButtonCaps", w.USHORT),
        ("NumberFeatureValueCaps", w.USHORT),
        ("NumberFeatureDataIndices", w.USHORT),
    ]


hidlib = ctypes.WinDLL("hid.dll")
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.CreateFileW.restype = w.HANDLE
kernel32.CreateFileW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, w.LPVOID, w.DWORD, w.DWORD, w.HANDLE]
hidlib.HidD_GetPreparsedData.argtypes = [w.HANDLE, ctypes.POINTER(ctypes.c_void_p)]
hidlib.HidD_GetPreparsedData.restype = w.BOOL
hidlib.HidD_FreePreparsedData.argtypes = [ctypes.c_void_p]
hidlib.HidP_GetCaps.argtypes = [ctypes.c_void_p, ctypes.POINTER(HIDP_CAPS)]
hidlib.HidP_GetCaps.restype = ctypes.c_long


def get_caps(path: str) -> HIDP_CAPS | None:
    h = kernel32.CreateFileW(
        path, GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE,
        None, OPEN_EXISTING, 0, None,
    )
    if h == INVALID_HANDLE_VALUE:
        return None
    preparsed = ctypes.c_void_p()
    if not hidlib.HidD_GetPreparsedData(h, ctypes.byref(preparsed)):
        kernel32.CloseHandle(h)
        return None
    try:
        caps = HIDP_CAPS()
        if hidlib.HidP_GetCaps(preparsed, ctypes.byref(caps)) != HIDP_STATUS_SUCCESS:
            return None
        return caps
    finally:
        hidlib.HidD_FreePreparsedData(preparsed)
        kernel32.CloseHandle(h)


def get_descriptor(path: str) -> bytes:
    """HidD_GetReportDescriptor is not exported; use IOCTL_HID_GET_REPORT_DESCRIPTOR."""
    h = kernel32.CreateFileW(
        path, 0, FILE_SHARE_READ | FILE_SHARE_WRITE, None, OPEN_EXISTING, 0, None,
    )
    if h == INVALID_HANDLE_VALUE:
        return b""
    try:
        IOCTL_HID_GET_REPORT_DESCRIPTOR = 0x000B0000
        buf = ctypes.create_string_buffer(4096)
        returned = w.DWORD(0)
        ok = kernel32.DeviceIoControl(
            h, IOCTL_HID_GET_REPORT_DESCRIPTOR, None, 0,
            buf, len(buf), ctypes.byref(returned), None,
        )
        if not ok:
            return b""
        return buf.raw[: returned.value]
    finally:
        kernel32.CloseHandle(h)


def decode_report_ids(desc: bytes) -> list[tuple[int, int]]:
    """Very small parser: report ID -> (kind, report size in bytes)."""
    out: list[tuple[int, int]] = []
    rid = None
    size_bits = 0
    count = 0
    size_items: dict[int, int] = {}
    kind = None
    kind_names = {0x80: "input", 0x90: "output", 0xB0: "feature"}
    i = 0
    while i < len(desc):
        b = desc[i]
        if b == 0x85:  # Report ID
            rid = desc[i + 1]
            i += 2
            continue
        if b in (0x81, 0x91, 0xB1):
            if size_bits and count:
                size_items[rid or 0] = size_items.get(rid or 0, 0) + (size_bits * count + 7) // 8
            i += 2 if (b & 0x03) != 0x03 else 3
            continue
        if b in (0x75, 0x95, 0x15, 0x25, 0x05, 0x09, 0x19, 0x29, 0x07, 0x17, 0x27, 0x05, 0x0B, 0x0A, 0x0C):
            # only care about report size/count here
            if b == 0x75:
                size_bits = desc[i + 1]
                i += 2
                continue
            if b == 0x95:
                count = desc[i + 1]
                i += 2
                continue
        i += 1
    return sorted(size_items.items())


def main() -> None:
    vid = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x258A
    pid = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x010C
    fallback = None
    for d in hidapi.enumerate(vid, pid):
        p = d["path"].decode()
        caps = get_caps(p)
        print(f"\npath={p}")
        print(
            f"  interface={d['interface_number']} usagePage={d['usage_page']:#06x} "
            f"usage={d['usage']:#06x}"
        )
        if caps:
            print(
                f"  in={caps.InputReportByteLength} out={caps.OutputReportByteLength} "
                f"feature={caps.FeatureReportByteLength} "
                f"featVal={caps.NumberFeatureValueCaps} outVal={caps.NumberOutputValueCaps}"
            )
        else:
            print("  caps unavailable (open denied)")
        if d["usage_page"] == 0xFF00 and d["usage"] == 1:
            desc = get_descriptor(p)
            print(f"  report descriptor ({len(desc)} bytes): {desc.hex(' ')}")
            fallback = fallback or desc
    if fallback:
        print("\nparsed report sizes (id -> bytes):", decode_report_ids(fallback))


if __name__ == "__main__":
    main()

