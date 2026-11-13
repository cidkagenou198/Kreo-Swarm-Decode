from __future__ import annotations

import hid
from kreo_control.device.models import ConnectionType, DeviceDescriptor, SupportedDevice

SUPPORTED_TARGETS: tuple[SupportedDevice, ...] = (
    SupportedDevice(
        vendor_id=0x258A,
        product_id=0x010C,
        usage_page=0xFF00,
        usage=0x01,
        product_name="Kreo Swarm 75 (Wired)",
        connection_type=ConnectionType.WIRED,
    ),
    SupportedDevice(
        vendor_id=0x3554,
        product_id=0xFA09,
        usage_page=0xFF02,
        usage=0x02,
        product_name="Kreo Swarm 75 (Wireless 2.4G)",
        connection_type=ConnectionType.WIRELESS,
    ),
)


def enumerate_kreo_devices() -> list[DeviceDescriptor]:
    """Scan all connected HID devices and filter for supported Kreo Swarm 75 interfaces."""
    raw_devices = hid.enumerate()
    found: list[DeviceDescriptor] = []

    for d in raw_devices:
        vid = int(d.get("vendor_id", 0))
        pid = int(d.get("product_id", 0))
        up = int(d.get("usage_page", 0))
        u = int(d.get("usage", 0))

        for target in SUPPORTED_TARGETS:
            if (
                vid == target.vendor_id
                and pid == target.product_id
                and up == target.usage_page
                and u == target.usage
            ):
                raw_path = d.get("path")
                path_str = raw_path.decode("utf-8") if isinstance(raw_path, bytes) else str(raw_path)
                
                # For wired 0x258A:0x010C on Windows, multiple HID collections match (Col03, Col05, Col06).
                # Only Col06 has the 520-byte feature report interface.
                if target.connection_type == ConnectionType.WIRED:
                    path_lower = path_str.lower()
                    if "col" in path_lower and "col06" not in path_lower:
                        continue

                found.append(
                    DeviceDescriptor(
                        vendor_id=vid,
                        product_id=pid,
                        usage_page=up,
                        usage=u,
                        interface_number=int(d.get("interface_number", -1)),
                        path=path_str,
                        product_name=target.product_name,
                        product_string=d.get("product_string"),
                        serial_number=d.get("serial_number_string"),
                        connection_type=target.connection_type,
                    )
                )

    return found


def get_active_device() -> DeviceDescriptor | None:
    """Find the best active Kreo keyboard interface. Prefers Wired over Wireless."""
    devices = enumerate_kreo_devices()
    if not devices:
        return None

    # Prefer wired if connected
    for dev in devices:
        if dev.connection_type == ConnectionType.WIRED:
            return dev

    return devices[0]
