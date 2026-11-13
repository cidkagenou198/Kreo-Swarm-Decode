from __future__ import annotations

LIGHTING_MODES: dict[int, str] = {
    0: "Off",
    1: "Static",
    2: "Breathing",
    3: "Rainbow",
    4: "Flash Away",
    5: "Raindrops",
    6: "Rainbow Wheel",
    7: "Ripples Shining",
    8: "Stars Twinkle",
    9: "Shadow Disappear",
    10: "Retro Snake",
    11: "Neon Stream",
    12: "Reaction",
    13: "Sine Wave",
    14: "Retinue Scanning",
    15: "Rotating Windmill",
    16: "Colorful Waterfall",
    17: "Blossoming",
    18: "Rotating Storm",
    19: "Custom (Self-Define)",
    277: "Custom (Per-Key)",
}

# Golden Truth: Hardware Mode IDs in SinoWealth SH68F90 MCU firmware
# Verified against text.xml, KB.ini, and live hardware readback
CUSTOM_HW_MODE = 21
CUSTOM_LOGICAL_MODE = 277

LOGICAL_TO_HW_EFFECT: dict[int, int] = {
    mode: (CUSTOM_HW_MODE if mode in (19, CUSTOM_LOGICAL_MODE) else mode)
    for mode in LIGHTING_MODES
}

HW_EFFECT_TO_LOGICAL: dict[int, int] = {
    hw: (CUSTOM_LOGICAL_MODE if hw == CUSTOM_HW_MODE else hw)
    for hw in LOGICAL_TO_HW_EFFECT.values()
}

MODE_NAME_TO_ID: dict[str, int] = {
    name.lower().replace(" ", "_"): mode_id
    for mode_id, name in LIGHTING_MODES.items()
}

MAX_BRIGHTNESS_LEVEL = 4
MAX_SPEED_LEVEL = 4
MAX_PROFILE_SIZE = 128
LIGHT_TABLE_SIZE = 480
CUSTOM_FRAME_SIZE = 378  # 126 LEDs * 3 channels
TOTAL_MATRIX_KEYS = 126
PHYSICAL_KEYS_SWARM75 = 82

