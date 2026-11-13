from __future__ import annotations

from fastapi import APIRouter, HTTPException
from kreo_control.device.keyboard import KreoKeyboard
from kreo_control.lighting.constants import LIGHTING_MODES, MODE_NAME_TO_ID
from kreo_control.lighting.matrix import load_swarm75_led_map
from kreo_control.lighting.models import (
    BatchKeyApplyRequest,
    GlobalLightingRequest,
    KeyLedInfo,
    LightingState,
    PerKeyApplyRequest,
)

router = APIRouter(prefix="/api/lighting", tags=["Lighting"])

KEY_GROUPS: dict[str, list[str]] = {
    "wasd": ["w", "a", "s", "d"],
    "qwer": ["q", "w", "e", "r"],
    "arrows": ["up", "down", "left", "right"],
    "numbers": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "="],
    "functions": [f"f{i}" for i in range(1, 13)],
    "modifiers": [
        "esc",
        "tab",
        "caps",
        "left_shift",
        "right_shift",
        "left_ctrl",
        "left_win",
        "left_alt",
        "space",
        "right_alt",
        "fn",
        "right_ctrl",
        "enter",
        "backspace",
    ],
}


@router.get("/modes")
def get_supported_modes() -> list[dict[str, Any]]:
    """Return list of all supported lighting presets."""
    return [
        {"id": mode_id, "name": name, "key": name.lower().replace(" ", "_")}
        for mode_id, name in LIGHTING_MODES.items()
    ]


@router.get("/state", response_model=LightingState)
def get_lighting_state() -> LightingState:
    """Get active global lighting state."""
    try:
        kb = KreoKeyboard.auto_connect()
        return kb.get_lighting_state()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read lighting state: {exc}")


@router.post("/state", response_model=LightingState)
def set_lighting_state(request: GlobalLightingRequest) -> LightingState:
    """Set global lighting preset, brightness, speed, direction, and optional color."""
    try:
        kb = KreoKeyboard.auto_connect()
        return kb.set_global_lighting(
            mode=request.mode,
            brightness=request.brightness,
            speed=request.speed,
            direction=request.direction,
            color=request.color,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to set lighting state: {exc}")


@router.get("/per-key", response_model=list[KeyLedInfo])
def get_per_key_lighting() -> list[KeyLedInfo]:
    """Get current color for all 82 keys."""
    try:
        kb = KreoKeyboard.auto_connect()
        return kb.get_per_key_lighting()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read per-key lighting: {exc}")


@router.post("/per-key", response_model=list[KeyLedInfo])
def set_per_key_lighting(request: PerKeyApplyRequest) -> list[KeyLedInfo]:
    """Set custom RGB colors for specified keys and switch keyboard to custom mode."""
    try:
        kb = KreoKeyboard.auto_connect()
        return kb.set_per_key_lighting(request.edits)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to apply per-key colors: {exc}")


@router.post("/per-key/batch", response_model=list[KeyLedInfo])
def apply_batch_key_lighting(request: BatchKeyApplyRequest) -> list[KeyLedInfo]:
    """Set color for a predefined group of keys ('all', 'wasd', 'arrows', 'numbers', etc.)."""
    try:
        kb = KreoKeyboard.auto_connect()
        group_lower = request.group.lower()

        if group_lower == "all":
            all_keys = [k.ui_key for k in load_swarm75_led_map()]
            edits = {k: request.color for k in all_keys}
        elif group_lower in KEY_GROUPS:
            edits = {k: request.color for k in KEY_GROUPS[group_lower]}
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown key group '{request.group}'. Valid groups: all, wasd, qwer, arrows, numbers, functions, modifiers",
            )

        return kb.set_per_key_lighting(edits)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to apply batch lighting: {exc}")

