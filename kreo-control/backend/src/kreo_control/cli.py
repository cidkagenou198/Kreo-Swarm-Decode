from __future__ import annotations

import sys
from kreo_control.device.discovery import enumerate_kreo_devices, get_active_device
from kreo_control.device.keyboard import KreoKeyboard
from kreo_control.device.transport import KreoTransportError


def main() -> None:
    print("\n=======================================================")
    print("   Kreo Control — Hardware Detection & Protocol Probe")
    print("=======================================================\n")

    print("[*] Scanning for connected Kreo Swarm 75 devices...")
    devices = enumerate_kreo_devices()

    if not devices:
        print("[!] No supported Kreo Swarm 75 devices found.")
        print("    Please ensure the keyboard is connected via USB cable or 2.4 GHz RF dongle.")
        sys.exit(1)

    print(f"[+] Found {len(devices)} matching interface(s):")
    for idx, dev in enumerate(devices, 1):
        print(f"    [{idx}] {dev.product_name} | {dev.connection_type.value.upper()} | VID: 0x{dev.vendor_id:04X} PID: 0x{dev.product_id:04X} | Page: 0x{dev.usage_page:04X} Usage: 0x{dev.usage:04X}")

    active = get_active_device()
    assert active is not None
    print(f"\n[*] Active Device Selected: {active.product_name} ({active.connection_type.value})")

    print("[*] Connecting to device and querying active hardware profile...")
    kb = KreoKeyboard(active)
    try:
        state = kb.get_lighting_state()
        print("\n[+] SUCCESS! Read active hardware state:")
        print(f"    - Lighting Mode:    {state.mode_name} (ID: {state.mode_id})")
        print(f"    - Brightness:       Level {state.brightness} / 4")
        print(f"    - Speed:            Level {state.speed} / 4")
        print(f"    - Direction:        {'Clockwise / L-to-R' if state.direction == 0 else 'Counter-Clockwise / R-to-L'}")
        print(f"    - Color Mode:       {'Rainbow Spectrum / Dynamic' if state.color_mode == 1 else 'Single Custom Color'}")
        print(f"    - Current RGB:      {state.color}")
        print("\n[+] Hardware verification passed safely and non-destructively.\n")
    except KreoTransportError as exc:
        print(f"[!] Protocol communication error: {exc}")
        sys.exit(2)
    finally:
        kb.disconnect()


if __name__ == "__main__":
    main()

