from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from kreo_control.device.keyboard import KreoKeyboard
from kreo_control.profiles.models import (
    KeyboardProfile,
    ProfileCreateRequest,
    ProfileLightingData,
    ProfilesListResponse,
    ProfileUpdateRequest,
)
from kreo_control.profiles.store import ProfilesStore

router = APIRouter(prefix="/api/profiles", tags=["Profiles"])
store = ProfilesStore()


@router.get("", response_model=ProfilesListResponse)
def list_profiles() -> ProfilesListResponse:
    """List all saved profiles and indicate the active one."""
    profiles = store.list_all()
    active = store.get_active()
    return ProfilesListResponse(
        active_profile_id=active.id if active else None,
        profiles=profiles,
    )


@router.post("", response_model=KeyboardProfile)
def create_profile(request: ProfileCreateRequest) -> KeyboardProfile:
    """Create a new profile. If copy_active is true, captures current keyboard lighting."""
    current_lighting: ProfileLightingData | None = None
    if request.copy_active:
        try:
            kb = KreoKeyboard.auto_connect()
            state = kb.get_lighting_state()
            keys_info = kb.get_per_key_lighting()
            keys_map = {k.ui_key.lower(): k.color for k in keys_info}
            current_lighting = ProfileLightingData(
                mode_id=state.mode_id,
                mode_name=state.mode_name,
                brightness=state.brightness,
                speed=state.speed,
                direction=state.direction,
                color=state.color,
                is_custom_per_key=state.is_custom_per_key,
                keys=keys_map if state.is_custom_per_key else {},
            )
        except Exception:
            current_lighting = None

    return store.create(request, current_lighting=current_lighting)


@router.get("/{profile_id}", response_model=KeyboardProfile)
def get_profile(profile_id: str) -> KeyboardProfile:
    """Retrieve details for a specific profile."""
    profile = store.get(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/{profile_id}", response_model=KeyboardProfile)
def update_profile(profile_id: str, request: ProfileUpdateRequest) -> KeyboardProfile:
    """Update name, description, or lighting configuration for a profile."""
    updated = store.update(profile_id, request)
    if updated is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return updated


@router.delete("/{profile_id}")
def delete_profile(profile_id: str) -> dict[str, str]:
    """Delete a profile (cannot delete the last remaining profile)."""
    success = store.delete(profile_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot delete this profile or profile not found")
    return {"status": "deleted", "id": profile_id}


@router.post("/{profile_id}/activate", response_model=KeyboardProfile)
def activate_profile(profile_id: str) -> KeyboardProfile:
    """Activate a profile and push its lighting settings to physical hardware."""
    try:
        kb = KreoKeyboard.auto_connect()
        activated = store.activate(profile_id, kb)
        if activated is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        return activated
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to activate profile on hardware: {exc}")


@router.post("/{profile_id}/duplicate", response_model=KeyboardProfile)
def duplicate_profile(profile_id: str) -> KeyboardProfile:
    """Duplicate an existing profile."""
    cloned = store.duplicate(profile_id)
    if cloned is None:
        raise HTTPException(status_code=404, detail="Source profile not found")
    return cloned


@router.get("/{profile_id}/export")
def export_profile(profile_id: str) -> JSONResponse:
    """Export profile as downloadable JSON."""
    data = store.export_profile(profile_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    headers = {"Content-Disposition": f"attachment; filename={profile_id}.kreo.json"}
    return JSONResponse(content=data, headers=headers)


@router.post("/import", response_model=KeyboardProfile)
def import_profile(data: dict[str, Any]) -> KeyboardProfile:
    """Import a profile from JSON payload."""
    try:
        return store.import_profile(data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid profile payload: {exc}")

