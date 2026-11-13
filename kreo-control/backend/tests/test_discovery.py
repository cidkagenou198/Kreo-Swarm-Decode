from __future__ import annotations

import pytest
from kreo_control.device.discovery import enumerate_kreo_devices, get_active_device
from kreo_control.device.models import ConnectionType


def test_discovery_live():
    devices = enumerate_kreo_devices()
    assert isinstance(devices, list)
    # If the user has their keyboard/receiver connected, verify attributes
    if devices:
        dev = devices[0]
        assert dev.vendor_id in (0x258A, 0x3554)
        assert dev.product_id in (0x010C, 0xFA09)
        assert dev.connection_type in (ConnectionType.WIRED, ConnectionType.WIRELESS)


def test_get_active_device():
    dev = get_active_device()
    # If connected, active device should be resolved
    if dev is not None:
        assert dev.vendor_id in (0x258A, 0x3554)
        assert len(dev.path) > 0

