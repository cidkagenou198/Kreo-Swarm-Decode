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

# Hardware effect IDs from the vendor application's `Dev/kb/KB.ini` `LedOpt1`
# through `LedOpt18` rows. The logical UI order is not the MCU effect order.
# Custom mode intentionally remains 21: the vendor INI's `LedOpt19=21,0,...`
# is incompatible with the observed profile custom flag / effect convention and
# must not overwrite the established protocol behavior here.
CUSTOM_HW_MODE = 21
CUSTOM_LOGICAL_MODE = 277

LOGICAL_TO_HW_EFFECT: dict[int, int] = {
    0: 0,
    1: 1,
    2: 3,
    3: 2,
    4: 19,
    5: 15,
    6: 13,
    7: 20,
    8: 16,
    9: 18,
    10: 5,
    11: 7,
    12: 17,
    13: 12,
    14: 8,
    15: 28,
    16: 30,
    17: 14,
    18: 29,
    19: CUSTOM_HW_MODE,
    CUSTOM_LOGICAL_MODE: CUSTOM_HW_MODE,
}

HW_EFFECT_TO_LOGICAL: dict[int, int] = {
    hw: logical
    for logical, hw in LOGICAL_TO_HW_EFFECT.items()
    if logical != 19
}

# The vendor UI capability flags following each `LedOpt` mapping:
# (speed, brightness/light, direction, random/rainbow, color).
VENDOR_EFFECT_CAPABILITIES: dict[int, tuple[int, int, int, int, int]] = {
    1: (0, 1, 0, 1, 1),
    2: (1, 1, 0, 1, 1),
    3: (1, 1, 0, 0, 0),
    4: (1, 1, 0, 1, 1),
    5: (1, 1, 0, 1, 1),
    6: (1, 1, 0, 1, 1),
    7: (1, 1, 0, 1, 1),
    8: (1, 1, 0, 1, 1),
    9: (1, 1, 0, 1, 1),
    10: (1, 1, 0, 1, 1),
    11: (1, 1, 0, 1, 1),
    12: (1, 1, 0, 1, 1),
    13: (1, 1, 0, 1, 1),
    14: (1, 1, 0, 1, 1),
    15: (1, 1, 0, 0, 0),
    16: (1, 1, 0, 0, 0),
    17: (1, 1, 0, 0, 0),
    18: (1, 1, 0, 1, 1),
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
