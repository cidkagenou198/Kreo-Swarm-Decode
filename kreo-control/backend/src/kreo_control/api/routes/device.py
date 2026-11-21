from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from kreo_control.device.discovery import get_active_device
from kreo_control.device.keyboard import KreoKeyboard
from kreo_control.device.models import DeviceDescriptor
from kreo_control.device.transport import KreoTransportError
from kreo_control.lighting.models import LightingState

router = APIRouter(prefix="/api/device", tags=["device"])

# Global singleton keyboard instance for API session
_keyboard_instance: KreoKeyboard | None = None


def get_keyboard() -> KreoKeyboard:
    global _keyboard_instance
    if _keyboard_instance is None:
        _keyboard_instance = KreoKeyboard()
    return _keyboard_instance


class DeviceStatusResponse(BaseModel):
    connected: bool
    device: DeviceDescriptor | None = None


class DeviceDiagnostics(BaseModel):
    connected: bool
    connection_type: str | None = None
    vendor_id: int | None = None
    product_id: int | None = None
    usage_page: int | None = None
    usage: int | None = None
    firmware_id: int = 24
    report_id: int = 6
    matrix_slots: int = 126
    physical_keys: int = 82
    planar_frame_bytes: int = 378
    light_table_bytes: int = 490
    keymap_layer_bytes: int = 504


@router.get("/status", response_model=DeviceStatusResponse)
def get_status() -> DeviceStatusResponse:
    """Check if a Kreo Swarm 75 is currently connected."""
    dev = get_active_device()
    if dev is None:
        return DeviceStatusResponse(connected=False, device=None)
    return DeviceStatusResponse(connected=True, device=dev)


@router.get("/diagnostics", response_model=DeviceDiagnostics)
def get_diagnostics() -> DeviceDiagnostics:
    """Return hardware parameters, active transport, and protocol constants."""
    dev = get_active_device()
    if dev is None:
        return DeviceDiagnostics(connected=False)
    return DeviceDiagnostics(
        connected=True,
        connection_type=dev.connection_type,
        vendor_id=dev.vendor_id,
        product_id=dev.product_id,
        usage_page=dev.usage_page,
        usage=dev.usage,
        firmware_id=24,
        report_id=0x13 if dev.connection_type == "wireless" else 0x06,
        matrix_slots=126,
        physical_keys=82,
        planar_frame_bytes=378,
        light_table_bytes=490,
        keymap_layer_bytes=504,
    )


@router.get("/profile", response_model=LightingState)
def get_profile() -> LightingState:
    """Read the active hardware lighting profile non-destructively."""
    kb = get_keyboard()
    try:
        return kb.get_lighting_state()
    except KreoTransportError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/reconnect", response_model=DeviceStatusResponse)
def reconnect() -> DeviceStatusResponse:
    """Force re-enumeration and reconnect to the device."""
    global _keyboard_instance
    if _keyboard_instance is not None:
        _keyboard_instance.disconnect()
        _keyboard_instance = None
    return get_status()

