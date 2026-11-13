from __future__ import annotations

import pytest
from kreo_control.lighting.matrix import (
    build_planar_custom_frame,
    build_receiver_custom_frame,
    hex_to_rgb,
    load_swarm75_led_map,
    map_logical_id_to_ui,
    parse_receiver_custom_light_color,
    rgb_to_hex,
)


def test_color_conversions():
    assert hex_to_rgb("#FF00AA") == (255, 0, 170)
    assert hex_to_rgb("00FF00") == (0, 255, 0)
    assert rgb_to_hex(255, 0, 170) == "#ff00aa"


def test_logical_id_mapping():
    assert map_logical_id_to_ui("ESC") == ("esc", "Esc")
    assert map_logical_id_to_ui("SPACE") == ("space", "Space")
    assert map_logical_id_to_ui("W") == ("w", "W")
    assert map_logical_id_to_ui("F5") == ("f5", "F5")


def test_load_swarm75_led_map():
    keys = load_swarm75_led_map()
    assert len(keys) == 82
    ui_keys = {k.ui_key for k in keys}
    assert "esc" in ui_keys
    assert "w" in ui_keys
    assert "a" in ui_keys
    assert "s" in ui_keys
    assert "d" in ui_keys
    assert "space" in ui_keys
    assert "enter" in ui_keys


def test_build_receiver_custom_frame():
    edits = {"esc": "#ff0000", "w": "#00ff00", "space": "#0000ff"}
    frame = build_receiver_custom_frame(edits)
    assert len(frame) == 378

    # ESC ledIndex is 0 -> Planar format: R at [0], G at [126], B at [252]
    assert frame[0] == 255
    assert frame[126] == 0
    assert frame[252] == 0
    assert parse_receiver_custom_light_color(frame, 0) == "#ff0000"

    # W ledIndex is 14 -> G at [126 + 14 = 140]
    assert frame[14] == 0
    assert frame[140] == 255
    assert frame[266] == 0
    assert parse_receiver_custom_light_color(frame, 14) == "#00ff00"


def test_build_planar_custom_frame():
    edits = {"esc": "#ff0000"}
    frame = build_planar_custom_frame(edits)
    assert len(frame) == 378

    # Planar: Red channel is first 126 bytes
    assert frame[0] == 255
    assert frame[126] == 0
    assert frame[252] == 0

