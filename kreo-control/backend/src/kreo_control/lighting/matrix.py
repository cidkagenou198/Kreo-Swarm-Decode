from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kreo_control.lighting.constants import CUSTOM_FRAME_SIZE, TOTAL_MATRIX_KEYS
from kreo_control.lighting.models import RGBColor


@dataclass(frozen=True)
class LedKeyInfo:
    logical_id: str
    ui_key: str
    label: str
    svg_id: str
    led_index: int
    protocol_pos: int
    row: int
    col: int


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """Convert '#RRGGBB' or 'RRGGBB' to (r, g, b) integers."""
    clean = hex_str.lstrip("#")
    if len(clean) != 6:
        raise ValueError(f"Invalid hex color string: {hex_str!r}")
    return (
        int(clean[0:2], 16),
        int(clean[2:4], 16),
        int(clean[4:6], 16),
    )


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert (r, g, b) integers to '#RRGGBB'."""
    return f"#{r & 0xFF:02x}{g & 0xFF:02x}{b & 0xFF:02x}"


def normalize_hex(color_str: str) -> str:
    clean = color_str.lstrip("#").lower()
    if len(clean) != 6:
        raise ValueError(f"Invalid hex color: {color_str}")
    return f"#{clean}"


_CACHED_LED_MAP: list[LedKeyInfo] | None = None


def find_led_map_json_path() -> Path:
    """Find the path to led-map.json across project directories."""
    candidates = [
        # In frontend public folder
        Path(__file__).resolve().parents[4] / "frontend" / "public" / "keyboard" / "swarm75" / "meta" / "led-map.json",
        # In ref clone
        Path(__file__).resolve().parents[5] / "ref-kreo-macos" / "kreo_website_dump" / "kontrol.kreo-tech.com" / "assets" / "keyboard" / "swarm75" / "meta" / "led-map.json",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"led-map.json not found in candidate paths: {[str(c) for c in candidates]}")


def map_logical_id_to_ui(logical_id: str) -> tuple[str, str]:
    """Map firmware logical key name (e.g. ESC, LCTRL, F1) to UI key and display label."""
    upper = logical_id.upper()
    if upper.startswith("F") and upper[1:].isdigit():
        return upper.lower(), upper
    if len(upper) == 1 and upper.isalpha():
        return upper.lower(), upper
    if len(upper) == 1 and upper.isdigit():
        return upper, upper

    special_mapping: dict[str, tuple[str, str]] = {
        "ESC": ("esc", "Esc"),
        "PRINTSCREEN": ("print_screen", "PrtSc"),
        "PAUSE": ("pause", "Pause"),
        "SCROLLLOCK": ("scroll_lock", "ScrLk"),
        "DELETE": ("del", "Del"),
        "PAGEUP": ("page_up", "PgUp"),
        "PAGEDOWN": ("page_down", "PgDn"),
        "HOME": ("home", "Home"),
        "END": ("end", "End"),
        "INSERT": ("ins", "Ins"),
        "GRAVE": ("`", "`"),
        "MINUS": ("-", "-"),
        "EQUAL": ("=", "="),
        "BACKSPACE": ("backspace", "Backspace"),
        "TAB": ("tab", "Tab"),
        "LBRACKET": ("[", "["),
        "RBRACKET": ("]", "]"),
        "BACKSLASH": ("\\", "\\"),
        "CAPSLOCK": ("caps", "Caps"),
        "SEMICOLON": (";", ";"),
        "QUOTE": ("'", "'"),
        "ENTER": ("enter", "Enter"),
        "LSHIFT": ("left_shift", "Shift"),
        "COMMA": (",", ","),
        "DOT": (".", "."),
        "SLASH": ("/", "/"),
        "RSHIFT": ("right_shift", "Shift"),
        "LCTRL": ("left_ctrl", "Ctrl"),
        "LGUI": ("left_win", "Win"),
        "LALT": ("left_alt", "Alt"),
        "SPACE": ("space", "Space"),
        "RALT": ("right_alt", "Alt"),
        "FN": ("fn", "Fn"),
        "RCTRL": ("right_ctrl", "Ctrl"),
        "UP": ("up", "▲"),
        "DOWN": ("down", "▼"),
        "LEFT": ("left", "◄"),
        "RIGHT": ("right", "►"),
        "KNOB": ("knob", "Knob"),
    }
    return special_mapping.get(upper, (upper.lower(), upper))


def load_swarm75_led_map() -> list[LedKeyInfo]:
    """Load and cache the 82-key LED mapping table for Swarm 75."""
    global _CACHED_LED_MAP
    if _CACHED_LED_MAP is not None:
        return _CACHED_LED_MAP

    path = find_led_map_json_path()
    raw_data = json.loads(path.read_text(encoding="utf-8"))
    keys: list[LedKeyInfo] = []

    for item in raw_data.get("keys", []):
        logical_id = str(item.get("logicalId", ""))
        svg_id = str(item.get("svgId", ""))
        led_index = int(item.get("ledIndex", 0))
        protocol_pos = int(item.get("protocolPos", 0))
        grid = item.get("grid", {})
        row = int(grid.get("row", 0))
        col = int(grid.get("col", 0))

        ui_key, label = map_logical_id_to_ui(logical_id)
        keys.append(
            LedKeyInfo(
                logical_id=logical_id,
                ui_key=ui_key,
                label=label,
                svg_id=svg_id,
                led_index=led_index,
                protocol_pos=protocol_pos,
                row=row,
                col=col,
            )
        )

    _CACHED_LED_MAP = keys
    return keys


def parse_planar_custom_light_color(frame: bytes, led_index: int) -> str:
    """Parse color '#RRGGBB' from 378-byte planar custom frame (126 R, 126 G, 126 B)."""
    if led_index < 0 or led_index >= TOTAL_MATRIX_KEYS:
        return "#000000"
    if len(frame) < CUSTOM_FRAME_SIZE:
        return "#000000"
    return rgb_to_hex(
        frame[led_index],
        frame[TOTAL_MATRIX_KEYS + led_index],
        frame[TOTAL_MATRIX_KEYS * 2 + led_index],
    )


def parse_receiver_custom_light_color(frame: bytes, led_index: int) -> str:
    """Parse color '#RRGGBB' from custom frame (planar layout on both USB and RF)."""
    return parse_planar_custom_light_color(frame, led_index)


def update_receiver_frame_color(
    frame: bytes | bytearray,
    led_index: int,
    rgb: tuple[int, int, int],
) -> bytes:
    """Update a single LED's RGB in planar frame (126 R, 126 G, 126 B)."""
    if led_index < 0 or led_index >= TOTAL_MATRIX_KEYS:
        raise ValueError(f"LED index {led_index} is out of bounds (0..{TOTAL_MATRIX_KEYS-1})")
    if len(frame) < CUSTOM_FRAME_SIZE:
        frame = bytearray(frame) + bytearray([0] * (CUSTOM_FRAME_SIZE - len(frame)))
    updated = bytearray(frame)
    updated[led_index] = rgb[0]
    updated[TOTAL_MATRIX_KEYS + led_index] = rgb[1]
    updated[TOTAL_MATRIX_KEYS * 2 + led_index] = rgb[2]
    return bytes(updated)


def build_planar_custom_frame(
    edits: dict[str, str],
    base_frame: bytes | None = None,
) -> bytes:
    """
    Build 378-byte planar frame for both Wired USB and Wireless 2.4 GHz RF.
    Format: [126 Red, 126 Green, 126 Blue].
    Keys in edits can be ui_key, logicalId, or svgId.
    """
    red = [0] * TOTAL_MATRIX_KEYS
    green = [0] * TOTAL_MATRIX_KEYS
    blue = [0] * TOTAL_MATRIX_KEYS

    if base_frame and len(base_frame) == CUSTOM_FRAME_SIZE:
        red = list(base_frame[0:TOTAL_MATRIX_KEYS])
        green = list(base_frame[TOTAL_MATRIX_KEYS : TOTAL_MATRIX_KEYS * 2])
        blue = list(base_frame[TOTAL_MATRIX_KEYS * 2 : TOTAL_MATRIX_KEYS * 3])

    led_map = load_swarm75_led_map()
    key_by_ui = {entry.ui_key.lower(): entry for entry in led_map}
    key_by_logical = {entry.logical_id.upper(): entry for entry in led_map}
    key_by_svg = {entry.svg_id: entry for entry in led_map}

    for key_id, hex_color in edits.items():
        entry = (
            key_by_ui.get(key_id.lower())
            or key_by_logical.get(key_id.upper())
            or key_by_svg.get(key_id)
        )
        if entry is None:
            continue

        r, g, b = hex_to_rgb(hex_color)
        idx = entry.led_index
        if 0 <= idx < TOTAL_MATRIX_KEYS:
            red[idx] = r
            green[idx] = g
            blue[idx] = b

    return bytes([*red, *green, *blue])


def build_receiver_custom_frame(
    edits: dict[str, str],
    base_frame: bytes | None = None,
) -> bytes:
    """
    Build 378-byte custom frame for 2.4 GHz wireless receiver.
    Uses the verified hardware-identical planar layout [126 R, 126 G, 126 B].
    """
    return build_planar_custom_frame(edits, base_frame)


def pad_receiver_payload(payload: bytes, padded_size: int = 512) -> bytes:
    """Zero-pad a wireless frame payload to padded_size (typically 512 bytes)."""
    if len(payload) > padded_size:
        raise ValueError(f"Payload ({len(payload)} bytes) exceeds target padded size ({padded_size})")
    return bytes([*payload, *([0] * (padded_size - len(payload)))])
