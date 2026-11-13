"""API routes for Screen Ambience Real-Time Screen Synchronization."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from kreo_control.ambience.controller import AmbienceController
from kreo_control.ambience.models import AmbienceConfig, AmbienceStatusResponse
from kreo_control.profiles.store import ProfilesStore

router = APIRouter(prefix="/api/ambience", tags=["Screen Ambience"])
controller = AmbienceController.get_shared_instance()
store = ProfilesStore()


@router.get("/status", response_model=AmbienceStatusResponse)
def get_ambience_status() -> AmbienceStatusResponse:
    """Get current screen ambience streaming status and statistics."""
    return controller.get_status()


@router.post("/start", response_model=AmbienceStatusResponse)
def start_ambience(config: AmbienceConfig | None = None) -> AmbienceStatusResponse:
    """Start real-time screen ambience streaming to the keyboard."""
    try:
        controller.start(config)
        return controller.get_status()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to start ambience sync: {exc}")


@router.post("/stop", response_model=AmbienceStatusResponse)
def stop_ambience(restore_profile: bool = True) -> AmbienceStatusResponse:
    """Stop real-time screen ambience streaming and optionally restore the active profile."""
    try:
        controller.stop()
        if restore_profile:
            active = store.get_active()
            if active is not None:
                store.activate(active.id, controller.keyboard)
        return controller.get_status()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to stop ambience sync: {exc}")


@router.post("/config", response_model=AmbienceConfig)
def update_ambience_config(config: AmbienceConfig) -> AmbienceConfig:
    """Update ambient capture parameters in real time."""
    return controller.update_config(config)


@router.get("/colors")
def get_live_ambient_colors() -> dict[str, Any]:
    """Retrieve current frame colors for live UI preview canvas."""
    return {
        "running": controller.is_running,
        "dominant_color": controller.sampler.dominant_color_hex,
        "colors": controller.get_latest_colors(),
    }


class AmbienceStreamFrameRequest(BaseModel):
    colors: dict[str, str] = Field(..., description="Mapping of ui_key to #RRGGBB hex color")


@router.post("/stream-frame")
def stream_ambience_frame(request: AmbienceStreamFrameRequest) -> dict[str, Any]:
    """High-speed streaming endpoint for client-side screen sampler frames."""
    try:
        controller.keyboard.connect()
        controller.keyboard.set_per_key_lighting(request.colors)
        return {"status": "ok", "keys_updated": len(request.colors)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to stream frame to keyboard: {exc}")

