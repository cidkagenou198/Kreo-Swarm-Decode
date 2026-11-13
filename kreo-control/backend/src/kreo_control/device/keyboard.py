from __future__ import annotations

import threading
import time
from typing import Any

from kreo_control.device.discovery import get_active_device
from kreo_control.device.models import ConnectionType, DeviceDescriptor
from kreo_control.device.protocol import (
    CUSTOM_MODE_ID,
    STATIC_MODE_ID,
    build_profile_write,
    parse_mode_id,
    parse_profile_to_state,
    read_custom_light_wired,
    read_custom_light_wireless,
    read_light_table_wired,
    read_light_table_wireless,
    read_profile_wired,
    read_profile_wireless,
    update_light_table_color,
    write_custom_light_wired,
    write_custom_light_wireless,
    write_light_table_wired,
    write_light_table_wireless,
    write_profile_wired,
    write_profile_wireless,
)
from kreo_control.device.transport import HidTransport, KreoDeviceNotFoundError, KreoProtocolError
from kreo_control.lighting.constants import CUSTOM_FRAME_SIZE, LIGHTING_MODES, MODE_NAME_TO_ID
from kreo_control.lighting.matrix import (
    build_planar_custom_frame,
    load_swarm75_led_map,
    parse_planar_custom_light_color,
    rgb_to_hex,
)
from kreo_control.lighting.models import KeyLedInfo, LightingState


class KreoKeyboard:
    """Unified hardware controller interface for the Kreo Swarm 75 keyboard."""

    _instance: KreoKeyboard | None = None
    _lock = threading.RLock()

    def __init__(self, descriptor: DeviceDescriptor | None = None) -> None:
        self.descriptor: DeviceDescriptor | None = descriptor
        self._transport: HidTransport | None = None
        self._cached_profile: bytes | None = None
        self._cached_table: bytes | None = None
        self._cached_custom_frame: bytes | None = None
        self._current_mode_id: int | None = None

    @classmethod
    def get_shared_instance(cls) -> KreoKeyboard:
        """Get or initialize singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def auto_connect(cls) -> KreoKeyboard:
        """Find the active keyboard and initialize connection."""
        inst = cls.get_shared_instance()
        inst.connect()
        return inst

    def connect(self) -> None:
        """Open HID transport."""
        with self._lock:
            if self.descriptor is None or (self._transport and not self._transport.is_open):
                self.descriptor = get_active_device()
                if self.descriptor is None:
                    raise KreoDeviceNotFoundError("No supported Kreo Swarm 75 device found.")

            if self._transport is None or not self._transport.is_open:
                self._transport = HidTransport(self.descriptor.path)
                self._transport.open()

    def disconnect(self) -> None:
        """Close HID transport."""
        with self._lock:
            if self._transport is not None:
                self._transport.close()
                self._transport = None

    @property
    def is_connected(self) -> bool:
        return self._transport is not None and self._transport.is_open

    def _ensure_connected(self) -> tuple[HidTransport, DeviceDescriptor]:
        if not self.is_connected or self._transport is None or self.descriptor is None:
            self.connect()
        assert self._transport is not None
        assert self.descriptor is not None
        return self._transport, self.descriptor

    def get_lighting_state(self) -> LightingState:
        """Read active hardware profile and light table with fallback to cached state."""
        with self._lock:
            try:
                transport, dev = self._ensure_connected()
                if dev.connection_type == ConnectionType.WIRED:
                    profile = read_profile_wired(transport)
                    try:
                        table = read_light_table_wired(transport)
                    except Exception:
                        table = self._cached_table
                else:
                    profile = read_profile_wireless(transport)
                    try:
                        table = read_light_table_wireless(transport)
                    except Exception:
                        table = self._cached_table

                self._cached_profile = profile
                self._cached_table = table
                state = parse_profile_to_state(profile, table)
                self._current_mode_id = state.mode_id
                return state
            except Exception:
                # If wireless keyboard is sleeping or query timed out, use last known cache
                if self._cached_profile is not None:
                    return parse_profile_to_state(self._cached_profile, self._cached_table)
                # Default baseline
                return LightingState(
                    mode_id=3,
                    mode_name="Rainbow",
                    brightness=3,
                    speed=2,
                    direction=0,
                    color_mode=1,
                    color="#00E5FF",
                    is_custom_per_key=False,
                )

    def set_global_lighting(
        self,
        *,
        mode: str | int,
        brightness: int = 3,
        speed: int = 2,
        color: str | None = None,
    ) -> LightingState:
        """Apply a hardware lighting mode, brightness, speed, and optional color."""
        # Resolve mode ID
        if isinstance(mode, int):
            mode_id = mode
        else:
            clean_mode = mode.lower().strip().replace("-", "_").replace(" ", "_")
            mode_id = MODE_NAME_TO_ID.get(clean_mode, 1)

        with self._lock:
            transport, dev = self._ensure_connected()

            # Read current profile if not cached
            if self._cached_profile is None:
                try:
                    if dev.connection_type == ConnectionType.WIRED:
                        self._cached_profile = read_profile_wired(transport)
                    else:
                        self._cached_profile = read_profile_wireless(transport)
                except Exception:
                    self._cached_profile = bytes([0x00] * 128)

            current_profile = self._cached_profile

            # Build updated profile
            updated_profile = build_profile_write(
                current_profile,
                mode_id=mode_id,
                brightness_level=min(4, max(0, brightness)),
                speed=min(4, max(0, speed)),
                effect_type=1 if color is not None else 0,
            )

            # Write profile
            if dev.connection_type == ConnectionType.WIRED:
                write_profile_wired(transport, updated_profile)
                if color and mode_id == STATIC_MODE_ID:
                    try:
                        table = read_light_table_wired(transport)
                        updated_table = update_light_table_color(table, STATIC_MODE_ID, hex_to_rgb(color))
                        write_light_table_wired(transport, updated_table)
                        self._cached_table = updated_table
                    except Exception:
                        self._cached_profile = bytes([0x00] * 128)
            else:
                write_profile_wireless(transport, updated_profile)
                if color and mode_id == STATIC_MODE_ID:
                    try:
                        table = read_light_table_wireless(transport)
                        updated_table = update_light_table_color(table, STATIC_MODE_ID, hex_to_rgb(color))
                        write_light_table_wireless(transport, updated_table)
                        self._cached_table = updated_table
                    except Exception:
                        self._cached_profile = bytes([0x00] * 128)

            time.sleep(0.02)
            self._cached_profile = updated_profile
            self._current_mode_id = mode_id
            return parse_profile_to_state(updated_profile, self._cached_table)

    def get_per_key_lighting(self) -> list[KeyLedInfo]:
        """Get RGB colors for all 82 keys."""
        led_map = load_swarm75_led_map()

        with self._lock:
            transport, dev = self._ensure_connected()

            # Try to read custom frame from hardware
            frame = self._cached_custom_frame
            try:
                if dev.connection_type == ConnectionType.WIRED:
                    frame = read_custom_light_wired(transport)
                else:
                    frame = read_custom_light_wireless(transport)
                self._cached_custom_frame = frame
            except Exception:
                pass

        keys: list[KeyLedInfo] = []
        for entry in led_map:
            color = "#273240"
            if frame is not None and len(frame) == CUSTOM_FRAME_SIZE:
                color = parse_planar_custom_light_color(frame, entry.led_index)

            keys.append(
                KeyLedInfo(
                    logical_id=entry.logical_id,
                    ui_key=entry.ui_key,
                    label=entry.label,
                    svg_id=entry.svg_id,
                    led_index=entry.led_index,
                    row=entry.row,
                    col=entry.col,
                    color=color,
                )
            )

        return keys

    def set_per_key_lighting(self, edits: dict[str, str]) -> list[KeyLedInfo]:
        """Apply custom colors to keys and activate Custom Per-Key mode (277)."""
        with self._lock:
            transport, dev = self._ensure_connected()

            # 1. Switch to custom mode 277 if not already active
            if self._cached_profile is None:
                try:
                    if dev.connection_type == ConnectionType.WIRED:
                        self._cached_profile = read_profile_wired(transport)
                    else:
                        self._cached_profile = read_profile_wireless(transport)
                except Exception:
                    self._cached_profile = bytes([0x00] * 128)

            current_mode = parse_mode_id(self._cached_profile) if self._cached_profile else None
            current_brightness = (
                self._cached_profile[2]
                if self._cached_profile and len(self._cached_profile) > 2
                else 0
            )
            if (
                current_mode != CUSTOM_MODE_ID
                or self._current_mode_id != CUSTOM_MODE_ID
                or current_brightness < 1
            ):
                updated_profile = build_profile_write(
                    self._cached_profile or bytes([0x00] * 128),
                    mode_id=CUSTOM_MODE_ID,
                    brightness_level=4,
                    speed=0,
                    effect_type=1,
                )
                if dev.connection_type == ConnectionType.WIRED:
                    write_profile_wired(transport, updated_profile)
                else:
                    write_profile_wireless(transport, updated_profile)
                self._cached_profile = updated_profile
                time.sleep(0.04)

            self._current_mode_id = CUSTOM_MODE_ID

            # 2. Build and write custom light frame (planar format for both wired and wireless)
            base_frame = self._cached_custom_frame
            new_frame = build_planar_custom_frame(edits, base_frame)
            if dev.connection_type == ConnectionType.WIRED:
                write_custom_light_wired(transport, new_frame)
            else:
                write_custom_light_wireless(transport, new_frame)

            self._cached_custom_frame = new_frame

            # 3. Construct updated key list directly from frame in memory
            led_map = load_swarm75_led_map()
            keys: list[KeyLedInfo] = []
            for entry in led_map:
                u = entry.ui_key.lower()
                if u in edits:
                    color = edits[u]
                elif new_frame and len(new_frame) == CUSTOM_FRAME_SIZE:
                    color = parse_planar_custom_light_color(new_frame, entry.led_index)
                else:
                    color = "#273240"

                keys.append(
                    KeyLedInfo(
                        logical_id=entry.logical_id,
                        ui_key=entry.ui_key,
                        label=entry.label,
                        svg_id=entry.svg_id,
                        led_index=entry.led_index,
                        row=entry.row,
                        col=entry.col,
                        color=color,
                    )
                )

            return keys
