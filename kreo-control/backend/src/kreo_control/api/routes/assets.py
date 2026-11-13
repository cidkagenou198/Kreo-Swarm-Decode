from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from kreo_control.lighting.matrix import load_swarm75_led_map

router = APIRouter(prefix="/api/keyboard-assets", tags=["Keyboard Assets"])


class KeyboardAssetKey(BaseModel):
    logical_id: str
    svg_id: str
    ui_key: str
    label: str
    protocol_pos: int
    led_index: int
    row: int
    col: int


class KeyboardAssetResponse(BaseModel):
    asset_name: str
    base_image_url: str
    letters_image_url: str
    interactive_svg_url: str
    total_keys: int
    keys: list[KeyboardAssetKey]


def get_public_dir() -> Path:
    candidates = [
        Path(__file__).resolve().parents[4] / "frontend" / "public",
        Path(__file__).resolve().parents[5] / "frontend" / "public",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


@router.get("/{asset_name}", response_model=KeyboardAssetResponse)
def get_keyboard_asset(asset_name: str) -> KeyboardAssetResponse:
    """Return asset manifest and key definitions for the specified keyboard model."""
    clean_name = asset_name.lower().replace("-", "").replace("_", "")
    if clean_name not in {"swarm75", "kreoswarm75"}:
        raise HTTPException(status_code=404, detail=f"Keyboard asset '{asset_name}' not found.")

    public_dir = get_public_dir()
    asset_root = public_dir / "keyboard" / "swarm75"
    if not asset_root.exists():
        raise HTTPException(status_code=500, detail="Keyboard assets directory not found.")

    led_keys = load_swarm75_led_map()
    keys = [
        KeyboardAssetKey(
            logical_id=k.logical_id,
            svg_id=k.svg_id,
            ui_key=k.ui_key,
            label=k.label,
            protocol_pos=k.protocol_pos,
            led_index=k.led_index,
            row=k.row,
            col=k.col,
        )
        for k in led_keys
    ]

    return KeyboardAssetResponse(
        asset_name="swarm75",
        base_image_url="/keyboard/swarm75/base/default.webp",
        letters_image_url="/keyboard/swarm75/letters/default.webp",
        interactive_svg_url="/keyboard/swarm75/overlay/interactive.svg",
        total_keys=len(keys),
        keys=keys,
    )

