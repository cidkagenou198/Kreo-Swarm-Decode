"""Pydantic models and configuration schemas for Screen Ambience Synchronization."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class AmbienceMode(str, Enum):
    SPATIAL = "spatial"      # 2D coordinate-mapped spatial screen zones to keyboard matrix
    AVERAGE = "average"      # Full screen average/dominant color across all keys
    CENTER = "center"        # Center crosshair / gaming action zone focus


class AmbienceConfig(BaseModel):
    mode: AmbienceMode = Field(default=AmbienceMode.SPATIAL, description="Sampling layout mode")
    fps: int = Field(default=15, ge=5, le=30, description="Target update rate in FPS (recommended 10-20 for wireless)")
    smoothness: float = Field(default=0.45, ge=0.0, le=0.95, description="Exponential moving average smoothing factor")
    saturation_boost: float = Field(default=1.3, ge=1.0, le=2.5, description="RGB saturation enhancement multiplier")
    brightness_multiplier: float = Field(default=1.0, ge=0.1, le=1.0, description="Global brightness attenuation")


class AmbienceStatusResponse(BaseModel):
    running: bool
    config: AmbienceConfig
    current_fps: float = 0.0
    dominant_color: str = "#000000"
    last_error: str | None = None

