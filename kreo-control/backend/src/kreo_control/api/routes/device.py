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


@router.get("/status", response_model=DeviceStatusResponse)
def get_status() -> DeviceStatusResponse:
    """Check if a Kreo Swarm 75 is currently connected."""
    dev = get_active_device()
    if dev is None:
        return DeviceStatusResponse(connected=False, device=None)
    return DeviceStatusResponse(connected=True, device=dev)


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

