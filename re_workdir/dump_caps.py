"""Read-only HID capability dump for the Kreo dongle.

Uses CreateFileW + HidD_GetPreparsedData + HidP_GetCaps. No report is written.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes as w

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


hid = ctypes.WinDLL("hid.dll")
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

kernel32.CreateFileW.restype = w.HANDLE
kernel32.CreateFileW.argtypes = [
    w.LPCWSTR, w.DWORD, w.DWORD, w.LPVOID, w.DWORD, w.DWORD, w.HANDLE,
]
hid.HidD_GetPreparsedData.argtypes = [w.HANDLE, ctypes.POINTER(ctypes.c_void_p)]
hid.HidD_GetPreparsedData.restype = w.BOOL
hid.HidD_FreePreparsedData.argtypes = [ctypes.c_void_p]
hid.HidD_FreePreparsedData.restype = w.BOOL
hid.HidP_GetCaps.argtypes = [ctypes.c_void_p, ctypes.POINTER(HIDP_CAPS)]
hid.HidP_GetCaps.restype = ctypes.c_long


def dump(path: str) -> None:
    h = kernel32.CreateFileW(
        path,
        GENERIC_READ | GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        None,
        OPEN_EXISTING,
        0,
        None,
    )
    if h == INVALID_HANDLE_VALUE:
        print(f"  open failed (err {ctypes.get_last_error()})")
        return

    preparsed = ctypes.c_void_p()
    ok = hid.HidD_GetPreparsedData(h, ctypes.byref(preparsed))
    if not ok:
        print(f"  HidD_GetPreparsedData failed (err {ctypes.get_last_error()})")
        kernel32.CloseHandle(h)
        return

    try:
        caps = HIDP_CAPS()
        status = hid.HidP_GetCaps(preparsed, ctypes.byref(caps))
        if status != HIDP_STATUS_SUCCESS:
            print(f"  HidP_GetCaps failed status={status:#x}")
            return
        print(
            f"  usagePage={caps.UsagePage:#06x} usage={caps.Usage:#06x} "
            f"in={caps.InputReportByteLength} out={caps.OutputReportByteLength} "
            f"feature={caps.FeatureReportByteLength} "
            f"featValCaps={caps.NumberFeatureValueCaps} featBtnCaps={caps.NumberFeatureButtonCaps} "
            f"outValCaps={caps.NumberOutputValueCaps}"
        )
    finally:
        hid.HidD_FreePreparsedData(preparsed)
        kernel32.CloseHandle(h)


def main() -> None:
    import hid as hidapi

    print("== 3554:FA09 collections ==")
    for d in hidapi.enumerate(0x3554, 0xFA09):
        print(f"\npath={d['path'].decode(errors='replace')}")
        print(
            f"  interface={d['interface_number']} usagePage={d['usage_page']:#06x} "
            f"usage={d['usage']:#06x} product={d['product_string']!r}"
        )
        dump(d["path"].decode())


if __name__ == "__main__":
    main()
