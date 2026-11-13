from __future__ import annotations

import pytest
from kreo_control.device.protocol import (
    calculate_wireless_checksum,
    find_second_255_index,
    parse_effect_indices,
    parse_mode_id,
    parse_profile,
    build_profile_write,
)


def test_calculate_wireless_checksum():
    body = bytes([0x44, 0x0A, 0x00, 0x0E, 0x00, 0x03, 0x03, 0x02, 0x00, 0x00, 0x04, 0x04, 0x07, 0x00, 0x0B, 0x20, 0x01, 0x00])
    chk = calculate_wireless_checksum(body)
    assert chk == 0xB2


def test_parse_profile():
    raw = bytearray([0] * 128)
    raw[0] = 0x00
    raw[1] = 0x03  # Rainbow
    raw[2] = 0x03  # Brightness 3
    raw[3] = 0x02  # Speed 2
    raw[4] = 0x00  # Dir 0
    raw[5] = 0x00  # Custom RGB flag
    raw[6] = 255   # R
    raw[7] = 128   # G
    raw[8] = 0     # B

    state = parse_profile(bytes(raw))
    assert state.mode_id == 3
    assert state.mode_name == "Rainbow"
    assert state.brightness == 3
    assert state.speed == 2
    assert state.direction == 0
    assert state.color.upper() == "#FF8000"


def test_build_profile_write_and_indices():
    raw = bytearray([0] * 128)
    raw[30] = 0xFF
    raw[31] = 0xFF  # Second 255 marker at 30, marker_index = 32

    marker = find_second_255_index(raw)
    assert marker == 32

    # Mode 1 (Static): brightness_index = 32, speed_index = 33
    b_idx, s_idx = parse_effect_indices(raw, 1)
    assert b_idx == 32
    assert s_idx == 33

    updated = build_profile_write(
        bytes(raw),
        mode_id=1,
        brightness_level=4,
        speed=3,
        effect_type=1,
    )
    assert updated[9] == 0
    assert updated[10] == 1
    assert updated[32] == 4
    assert (updated[33] >> 4) == 3
