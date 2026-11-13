from __future__ import annotations

from pydantic import BaseModel, Field


class RGBColor(BaseModel):
    r: int = Field(ge=0, le=255, default=255)
    g: int = Field(ge=0, le=255, default=255)
    b: int = Field(ge=0, le=255, default=255)

    def to_hex(self) -> str:
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"

    @classmethod
    def from_hex(cls, hex_str: str) -> RGBColor:
        clean = hex_str.lstrip("#")
        if len(clean) != 6:
            raise ValueError(f"Invalid hex color: {hex_str}")
        return cls(
            r=int(clean[0:2], 16),
            g=int(clean[2:4], 16),
            b=int(clean[4:6], 16),
        )


class LightingState(BaseModel):
    mode_id: int
    mode_name: str
    brightness: int = Field(ge=0, le=10, default=3)
    speed: int = Field(ge=0, le=10, default=2)
    direction: int = Field(ge=0, le=10, default=0)
    color_mode: int = 0  # 0: static/custom RGB, 1: rainbow/dynamic
    color: str = "#FF0000"
    is_custom_per_key: bool = False


class KeyLedInfo(BaseModel):
    logical_id: str
    ui_key: str
    label: str
    svg_id: str
    led_index: int
    row: int = 0
    col: int = 0
    color: str = "#273240"


class GlobalLightingRequest(BaseModel):
    mode: str | int
    brightness: int = Field(ge=0, le=4, default=3)
    speed: int = Field(ge=0, le=4, default=2)
    color: str | None = None


class PerKeyApplyRequest(BaseModel):
    edits: dict[str, str]  # { "esc": "#FF0000", "w": "#00FF00" }


class BatchKeyApplyRequest(BaseModel):
    group: str  # "all", "wasd", "qwer", "arrows", "numbers", "functions"
    color: str  # "#FF0000"
