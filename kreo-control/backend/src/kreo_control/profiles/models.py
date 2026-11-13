from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field


class ProfileLightingData(BaseModel):
    mode_id: int = 3
    mode_name: str = "Rainbow"
    brightness: int = Field(ge=0, le=4, default=3)
    speed: int = Field(ge=0, le=4, default=2)
    direction: int = Field(ge=0, le=1, default=0)
    color: str = "#FF0000"
    is_custom_per_key: bool = False
    keys: dict[str, str] = Field(default_factory=dict)


class KeyboardProfile(BaseModel):
    id: str
    name: str
    description: str = ""
    is_active: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    lighting: ProfileLightingData


class ProfileCreateRequest(BaseModel):
    name: str
    description: str = ""
    copy_active: bool = True
    lighting: ProfileLightingData | None = None


class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    lighting: ProfileLightingData | None = None


class ProfilesListResponse(BaseModel):
    active_profile_id: str | None
    profiles: list[KeyboardProfile]

