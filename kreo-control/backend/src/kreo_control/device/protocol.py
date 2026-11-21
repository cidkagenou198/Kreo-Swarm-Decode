from __future__ import annotations

import struct
import time
from collections.abc import Mapping, Sequence
from typing import NamedTuple
from kreo_control.device.transport import HidTransport, KreoProtocolError, KreoTimeoutError
from kreo_control.lighting.constants import (
    CUSTOM_FRAME_SIZE,
    LIGHTING_MODES,
    LIGHT_TABLE_SIZE,
    MAX_PROFILE_SIZE,
    LOGICAL_TO_HW_EFFECT,
    HW_EFFECT_TO_LOGICAL,
    TOTAL_MATRIX_KEYS,
)
from kreo_control.lighting.matrix import hex_to_rgb, rgb_to_hex
from kreo_control.lighting.models import LightingState, RGBColor

# Wired Constants
WIRED_WRITE_REPORT_ID = 0x06
WIRED_READ_REPORT_ID = 0x06
WIRED_FEATURE_REPORT_SIZE = 520

PROFILE_READ_CMD = b"\x84\x00\x00\x01\x00\x80"
PROFILE_WRITE_CMD = b"\x04\x00\x00\x01\x00\x80\x00"
LIGHT_TABLE_READ_CMD = b"\x8a\x00\x00\x01\x00\xe3\x01"
LIGHT_TABLE_WRITE_CMD = b"\x0a\x00\x00\x00\x00\x00\x02"
CUSTOM_LIGHT_PREPARE_CMD = b"\x86\x00\x00\x01\x00\x00\x02"
CUSTOM_LIGHT_WRITE_CMD = b"\x06\x00\x00\x01\x00\x00\x02"

# Wireless Constants
WIRELESS_REPORT_ID = 0x13
WIRELESS_REPORT_SIZE = 19
WIRELESS_CHUNK_SIZE = 14
WIRELESS_PADDING_SIZE = 512

WIRELESS_CMD_PROFILE_READ = 68
WIRELESS_CMD_PROFILE_WRITE = 4
WIRELESS_CMD_MATRIX_READ = 0x41
WIRELESS_CMD_MATRIX_WRITE = 0x01
WIRELESS_CMD_LIGHT_TABLE_READ = 73
WIRELESS_CMD_LIGHT_TABLE_WRITE = 9
WIRELESS_CMD_CUSTOM_LIGHT_READ = 66
WIRELESS_CMD_CUSTOM_LIGHT_WRITE = 2

CUSTOM_MODE_ID = 277
STATIC_MODE_ID = 1
SNOW_MODE_ID = 19

# Wired (CDevG5KB) feature-report constants, decoded from FUN_0048c600.
G5KB_REPORT_ID_FW_18 = 0x06
G5KB_REPORT_ID_OTHER = 0x09
G5KB_FEATURE_REPORT_SIZE = 0x208
G5KB_CHUNK_SIZE = 512
G5KB_CHUNK_DELAY = 0.020
G5KB_RETRY_DELAY = 0.046
G5KB_MAX_ATTEMPTS = 3

# Wired command IDs (CDevG5KB vtable slots +0x4c..+0x80).
G5KB_CMD_SET_MATRIX = 0x03
G5KB_CMD_GET_MATRIX = 0x83
G5KB_CMD_SET_PROFILE = 0x04
G5KB_CMD_GET_PROFILE = 0x84
G5KB_CMD_SET_MACRO = 0x05
G5KB_CMD_GET_MACRO = 0x85
G5KB_CMD_SET_GAME = 0x06
G5KB_CMD_GET_GAME = 0x86
G5KB_CMD_SET_LED_TABLE = 0x0A
G5KB_CMD_GET_LED_TABLE = 0x8A
G5KB_CMD_SET_SCREEN_PARAM = 0x0B
G5KB_CMD_RESET = 0x11
G5KB_CMD_GET_PASSWORD = 0x82

# Payload layout constants.
KEYMAP_RECORD_SIZE = 4
MATRIX_LAYER_POSITIONS = TOTAL_MATRIX_KEYS  # live GetMatrix returns 126 * 4 = 504 bytes
MATRIX_LAYER_CAPACITY = 0x80  # vendor cfg+0x2ff4 default (pre-device-probe figure)
RGB_TAB_ENTRY_SIZE = 21  # 7 RGB triples per key
RGB_TAB_ZONES = 7
RGB_TAB_PAD_SIZE = 0x200
RGB_TAB_CRC_TAIL = b"\x5A\xA5"

# Live evidence (2026-11-18): both transports return a 23-entry table
# (23 * 21 = 483 bytes) followed by a 7-byte trailer whose first 6 bytes are
# KB.ini's `Psd`. The vendor's own read constant requests 483 bytes
# (`LIGHT_TABLE_READ_CMD` ends in `e3 01`). `LIGHT_TABLE_SIZE` (480) in the
# lighting constants is 3 bytes short; see protocol_spec.md "Open items".
RGB_TAB_ENTRY_COUNT = 23
RGB_TAB_TABLE_BYTES = RGB_TAB_ENTRY_COUNT * RGB_TAB_ENTRY_SIZE  # 483
RGB_TAB_PSD_TRAILER_SIZE = 7
RGB_TAB_TOTAL_BYTES = RGB_TAB_TABLE_BYTES + RGB_TAB_PSD_TRAILER_SIZE  # 490
RGB_TAB_DEFAULT_PSD_TRAILER = bytes([0x03, 0x00, 0x00, 0x00, 0x01, 0xBE, 0x01])

# Action pages observed in a live layer read.
KEYMAP_PAGE_KEYBOARD = 0x00
KEYMAP_PAGE_CONSUMER = 0x02
KEYMAP_PAGE_VENDOR_07 = 0x07
KEYMAP_PAGE_VENDOR_08 = 0x08


def calculate_wireless_checksum(body: bytes) -> int:
    """Calculate the 8-bit additive checksum for a 20-byte wireless packet."""
    return (WIRELESS_REPORT_ID + sum(body)) & 0xFF


def find_second_255_index(profile: bytes | bytearray) -> int:
    """Locate the 0xFF, 0xFF table marker inside the 128-byte profile."""
    for index in range(len(profile) - 1):
        if profile[index] == 0xFF and profile[index + 1] == 0xFF:
            return index + 2
    raise KreoProtocolError("Lighting brightness table marker (0xFF, 0xFF) not found in profile")


def parse_mode_id(profile: bytes) -> int:
    """Extract logical mode ID from profile buffer using golden truth hardware effect table."""
    if len(profile) < 11:
        raise KreoProtocolError(f"Profile too small to parse mode: {len(profile)} bytes")
    custom_flag = profile[9]
    hw_effect = profile[10]

    # Custom per-key mode is flagged by profile[9] == 1 or effect ID 21
    if custom_flag == 1 or hw_effect == 21 or (len(profile) > 1 and profile[1] == 21):
        return CUSTOM_MODE_ID

    # Look up hardware effect ID in reverse mapping to return the correct logical mode ID
    if hw_effect != 0 and hw_effect in HW_EFFECT_TO_LOGICAL:
        return HW_EFFECT_TO_LOGICAL[hw_effect]
    if len(profile) > 1 and profile[1] != 0 and profile[1] in HW_EFFECT_TO_LOGICAL:
        return HW_EFFECT_TO_LOGICAL[profile[1]]
    if hw_effect in HW_EFFECT_TO_LOGICAL:
        return HW_EFFECT_TO_LOGICAL[hw_effect]
    return profile[1] if len(profile) > 1 else hw_effect


def parse_effect_indices(profile: bytes | bytearray, mode_id: int) -> tuple[int, int]:
    """Calculate the brightness and speed byte offsets for a given mode ID."""
    marker_index = find_second_255_index(profile)
    brightness_index = marker_index + (mode_id * 2) - 2
    speed_index = brightness_index + 1
    if speed_index >= len(profile):
        raise KreoProtocolError(
            f"Mode {mode_id} index ({speed_index}) falls outside profile bounds ({len(profile)})"
        )
    return brightness_index, speed_index


def parse_effect_speed(profile: bytes, mode_id: int) -> int:
    """Extract 0-4 animation speed for a given mode ID."""
    if mode_id in {CUSTOM_MODE_ID, 0, SNOW_MODE_ID}:
        return 0
    _, speed_index = parse_effect_indices(profile, mode_id)
    raw = (profile[speed_index] >> 4) & 0x0F
    return min(4, max(0, raw))


def parse_effect_brightness(profile: bytes, mode_id: int) -> int:
    """Extract 0-4 brightness level for a given mode ID."""
    if mode_id in {CUSTOM_MODE_ID, 0, SNOW_MODE_ID}:
        # In custom mode, brightness defaults to static mode brightness
        mode_id = STATIC_MODE_ID
    brightness_index, _ = parse_effect_indices(profile, mode_id)
    return min(4, max(0, profile[brightness_index]))


def build_profile_write(
    profile: bytes,
    *,
    mode_id: int,
    brightness_level: int,
    speed: int,
    direction: int = 0,
    effect_type: int = 1,
) -> bytes:
    """
    Construct a validated 128-byte profile with updated mode, brightness, speed, and direction.
    Uses golden truth SinoWealth hardware effect IDs from Dev/kb/KB.ini.
    """
    updated = bytearray(profile)

    if mode_id in (CUSTOM_MODE_ID, 21):
        effective_brightness = min(4, max(1, brightness_level))
        updated[1] = 21
        updated[2] = effective_brightness & 0xFF
        updated[3] = 0
        updated[4] = direction & 0x01
        updated[5] = 0
        updated[9] = 1
        updated[10] = 21
    else:
        hw_effect = LOGICAL_TO_HW_EFFECT.get(mode_id, mode_id)
        updated[1] = hw_effect & 0xFF
        updated[2] = brightness_level & 0xFF
        updated[3] = speed & 0xFF
        updated[4] = direction & 0x01
        updated[5] = 0 if effect_type == 0 else 1
        updated[9] = 0
        updated[10] = hw_effect & 0xFF

    # Markers
    if len(updated) > 57:
        updated[56] = 0xFF
        updated[57] = 0xFF
    if len(updated) >= 128:
        updated[126] = 0x5A
        updated[127] = 0xA5

    # Update mode brightness & speed table (mode_id 1..18 maps to slots 0..17)
    if mode_id not in {CUSTOM_MODE_ID, 0, SNOW_MODE_ID, 21} and 1 <= mode_id <= 18:
        try:
            b_idx, s_idx = parse_effect_indices(updated, mode_id)
            updated[b_idx] = brightness_level & 0xFF
            updated[s_idx] = ((speed & 0x0F) << 4) | (0 if effect_type == 1 else 7)
        except KreoProtocolError:
            pass

    return bytes(updated)


def update_light_table_color(
    light_table: bytes,
    mode_id: int,
    rgb: tuple[int, int, int],
) -> bytes:
    """Update 3-byte RGB group color for a specific mode in the 480-byte light table."""
    offset = mode_id * 21
    if offset + 2 >= len(light_table):
        raise KreoProtocolError(f"Light table offset {offset} out of bounds ({len(light_table)})")
    updated = bytearray(light_table)
    updated[offset] = rgb[0]
    updated[offset + 1] = rgb[1]
    updated[offset + 2] = rgb[2]
    return bytes(updated)


def parse_profile_to_state(
    profile: bytes,
    light_table: bytes | None = None,
) -> LightingState:
    """Convert raw profile buffer and optional light table into high-level LightingState."""
    mode_id = parse_mode_id(profile)
    is_custom = mode_id == CUSTOM_MODE_ID

    if is_custom:
        brightness = min(4, max(1, profile[2])) if len(profile) > 2 and profile[2] != 0 else 4
        speed = 0
    else:
        try:
            brightness = min(4, max(0, parse_effect_brightness(profile, mode_id)))
            speed = min(4, max(0, parse_effect_speed(profile, mode_id)))
        except KreoProtocolError:
            brightness = min(4, max(0, profile[2])) if len(profile) > 2 else 3
            speed = min(4, max(0, profile[3])) if len(profile) > 3 else 2

    hex_color = "#FF0000"
    if light_table and len(light_table) >= 480:
        offset = STATIC_MODE_ID * 21
        hex_color = rgb_to_hex(light_table[offset], light_table[offset + 1], light_table[offset + 2])
    elif len(profile) >= 9:
        hex_color = rgb_to_hex(profile[6], profile[7], profile[8])

    mode_name = "Custom (Per-Key)" if is_custom else LIGHTING_MODES.get(mode_id, f"Mode {mode_id}")

    return LightingState(
        mode_id=mode_id,
        mode_name=mode_name,
        brightness=brightness,
        speed=speed,
        direction=profile[4] if len(profile) > 4 else 0,
        color_mode=profile[5] if len(profile) > 5 else 0,
        color=hex_color,
        is_custom_per_key=is_custom,
    )


# Alias for backwards compatibility
parse_profile = parse_profile_to_state


# ---------------------------------------------------------
# Frame builders (decoded from the vendor binary)
# ---------------------------------------------------------


def build_wireless_frame(
    command: int,
    index: int,
    total: int,
    payload: bytes = b"",
    *,
    flag: int = 0,
    length: int | None = None,
) -> bytes:
    """Build one 20-byte `0x13` wireless frame.

    Layout (confirmed in `FUN_00487260` / `FUN_00487fa0`):

    ``[0]=0x13, [1]=cmd, [2]=total, [3]=index, [4]=(flag<<4)|len,``
    ``[5..18]=payload, [19]=checksum``.

    The high nibble of byte 4 is a caller-supplied flag (layer for
    ``SetMatrix``, group index for ``SetGame``, page for macro writes), *not* a
    last-chunk marker.
    """
    if not 0 <= command <= 0xFF:
        raise KreoProtocolError(f"Wireless command out of range: {command}")
    if not 0 <= index <= 0xFF:
        raise KreoProtocolError(f"Wireless chunk index out of range: {index}")
    if not 0 <= total <= 0xFF:
        raise KreoProtocolError(f"Wireless chunk total out of range: {total}")
    if not 0 <= flag <= 0x0F:
        raise KreoProtocolError(f"Wireless flag nibble out of range: {flag}")

    if length is None:
        length = len(payload)
    if not 0 <= length <= WIRELESS_CHUNK_SIZE:
        raise KreoProtocolError(f"Wireless chunk length out of range: {length}")

    chunk = bytes(payload[:WIRELESS_CHUNK_SIZE])
    chunk += b"\x00" * (WIRELESS_CHUNK_SIZE - len(chunk))

    byte4 = ((flag & 0x0F) << 4) | (length & 0x0F)
    body = bytes([command & 0xFF, total & 0xFF, index & 0xFF, byte4]) + chunk
    return bytes([WIRELESS_REPORT_ID]) + body + bytes([calculate_wireless_checksum(body)])


def build_wireless_packets(
    command: int,
    payload: bytes,
    *,
    flag: int = 0,
    total: int | None = None,
    chunk_size: int = WIRELESS_CHUNK_SIZE,
    pad_to: int | None = None,
) -> list[bytes]:
    """Split `payload` into 20-byte `0x13` frames.

    `total` overrides the advertised chunk count (the vendor sends a fixed
    logical count, e.g. macro page count). `pad_to` zero-extends the payload to
    a fixed device-side length before chunking.
    """
    if pad_to is not None:
        if len(payload) > pad_to:
            raise KreoProtocolError(f"Payload ({len(payload)}) exceeds pad_to ({pad_to})")
        payload = bytes(payload) + bytes(pad_to - len(payload))

    actual = max(1, (len(payload) + chunk_size - 1) // chunk_size)
    advertised = actual if total is None else total
    frames: list[bytes] = []
    for index in range(actual):
        start = index * chunk_size
        chunk = payload[start : start + chunk_size]
        frames.append(
            build_wireless_frame(
                command,
                index,
                advertised,
                chunk,
                flag=flag,
                length=len(chunk),
            )
        )
    return frames


def g5kb_report_id(nfw: int) -> int:
    """Report ID the wired device expects: 0x06 for Fw==0x18 else 0x09."""
    return G5KB_REPORT_ID_FW_18 if (nfw & 0xFF) == 0x18 else G5KB_REPORT_ID_OTHER


def build_feature_frame(
    command: int,
    payload: bytes = b"",
    *,
    param: int = 0,
    index: int = 0,
    total: int = 1,
    length: int | None = None,
    report_id: int = G5KB_REPORT_ID_FW_18,
    report_size: int = G5KB_FEATURE_REPORT_SIZE,
) -> bytes:
    """Build one fixed-size HID feature frame for the wired transport.

    Layout confirmed in `FUN_0048c600`:

    ``[0]=report id, [1]=cmd, [2]=param, [3]=0, [4]=total, [5]=index,``
    ``[6..7]=len LE16, [8..]=payload``.

    For read commands the vendor sets `[6..7]` to the *requested* byte count
    while leaving the payload empty; pass `length` for that case.
    """
    if not 0 <= command <= 0xFF:
        raise KreoProtocolError(f"Feature command out of range: {command}")
    if not 0 <= report_id <= 0xFF:
        raise KreoProtocolError(f"Feature report ID out of range: {report_id}")
    if report_size < 8:
        raise KreoProtocolError(f"Feature report size too small: {report_size}")
    capacity = report_size - 8
    if len(payload) > capacity:
        raise KreoProtocolError(f"Feature payload ({len(payload)}) exceeds capacity ({capacity})")
    if length is None:
        length = len(payload)
    if not 0 <= length <= 0xFFFF:
        raise KreoProtocolError(f"Feature length out of range: {length}")
    if not 0 <= index <= 0xFF or not 0 <= total <= 0xFF:
        raise KreoProtocolError("Feature chunk index/total out of range")

    frame = bytearray(report_size)
    frame[0] = report_id & 0xFF
    frame[1] = command & 0xFF
    frame[2] = param & 0xFF
    frame[3] = 0
    frame[4] = total & 0xFF
    frame[5] = index & 0xFF
    frame[6:8] = struct.pack("<H", length)
    frame[8 : 8 + len(payload)] = payload
    return bytes(frame)


def parse_feature_frame(report_id: int, frame: bytes) -> bytes:
    """Extract the payload from a 520-byte feature buffer.

    The vendor buffer keeps the report ID at byte 0 (hidapi-style), so the
    header is `[0]=report id, [1]=cmd, [2]=param, [4]=total, [5]=index,
    [6..7]=len LE16` and the payload starts at byte 8.
    """
    data = bytes(frame)
    if len(data) < 8:
        raise KreoProtocolError(f"Feature response too short: {len(frame)} bytes")
    if data[0] != (report_id & 0xFF):
        raise KreoProtocolError(
            f"Unexpected feature report ID {data[0]:#04x}, expected {report_id & 0xFF:#04x}"
        )
    length = struct.unpack_from("<H", data, 6)[0]
    if 8 + length > len(data):
        raise KreoProtocolError(
            f"Feature response length {length} exceeds buffer ({len(data) - 8} payload bytes)"
        )
    return data[8 : 8 + length]


def pack_keyboard_action(page: int, value: int) -> int:
    """Pack a 32-bit keymap action: `page << 24 | value`.

    The on-wire record is this value stored big-endian. Confirmed against a
    live `GetMatrix` read: base keys use page `0x00`, FN1 uses `0x02/0x07/0x08`
    and the values equal the `KB.ini` `[FN1]` 32-bit fields byte-for-byte.
    """
    if not 0 <= page <= 0xFF:
        raise KreoProtocolError(f"Action page out of range: {page}")
    if not 0 <= value <= 0xFFFFFF:
        raise KreoProtocolError(f"Action value out of range: {value:#x}")
    return ((page & 0xFF) << 24) | (value & 0xFFFFFF)


def pack_base_key(hid_usage: int, modifier_mask: int = 0) -> int:
    """Pack a base-layer key: page 0, `modifier_mask << 16 | hid_usage`.

    Observed: Esc `0x00000029`, Q `0x00000014`, LShift `0x00020000`,
    LCtrl `0x00010000`, LWin `0x00080000`.
    """
    if not 0 <= hid_usage <= 0xFF:
        raise KreoProtocolError(f"HID usage out of range: {hid_usage}")
    if not 0 <= modifier_mask <= 0xFF:
        raise KreoProtocolError(f"Modifier mask out of range: {modifier_mask}")
    return ((modifier_mask & 0xFF) << 16) | (hid_usage & 0xFF)


def encode_keyboard_action(hid_usage: int, modifier_mask: int = 0) -> int:
    """Encode a standard page-0 keyboard usage + modifier into a 32-bit action code."""
    return pack_keyboard_action(KEYMAP_PAGE_KEYBOARD, pack_base_key(hid_usage, modifier_mask))


def encode_consumer_action(consumer_usage: int) -> int:
    """Encode a page-2 consumer key (e.g. media keys) into a 32-bit action code."""
    return pack_keyboard_action(KEYMAP_PAGE_CONSUMER, consumer_usage & 0xFFFF)


def build_keymap_layer(
    assignments: Mapping[int, int] | Sequence[int],
    *,
    matrix_len: int = MATRIX_LAYER_POSITIONS,
    fill: int = 0,
    base_layer: bytes | None = None,
) -> bytes:
    """Build one keymap layer: 4-byte big-endian action codes, 126 positions (504 bytes).

    If ``base_layer`` is supplied (e.g. read from hardware), unassigned positions
    retain their existing hardware action code rather than being overwritten with
    ``fill``. This protects the 13 unpopulated hardware matrix slots from being wiped.
    """
    if matrix_len < 0:
        raise KreoProtocolError(f"matrix_len must be non-negative, got {matrix_len}")

    if base_layer is not None:
        needed = matrix_len * KEYMAP_RECORD_SIZE
        if len(base_layer) < needed:
            raise KreoProtocolError(f"base_layer too short: {len(base_layer)} < {needed}")
        records = [
            int.from_bytes(base_layer[i * 4 : i * 4 + 4], "big")
            for i in range(matrix_len)
        ]
    else:
        records = [fill & 0xFFFFFFFF] * matrix_len

    if isinstance(assignments, Mapping):
        items = assignments.items()
    else:
        items = enumerate(assignments)

    for position, value in items:
        if not 0 <= position < matrix_len:
            raise KreoProtocolError(f"Keymap position {position} outside 0..{matrix_len - 1}")
        if not 0 <= value <= 0xFFFFFFFF:
            raise KreoProtocolError(f"Action code out of range: {value:#x}")
        records[position] = value

    return b"".join(struct.pack(">I", record) for record in records)


class KeyAction(NamedTuple):
    """One decoded 32-bit keymap action (live-confirmed layout)."""

    position: int
    page: int
    value: int
    kind: str  # empty | keyboard | modifier | keyboard+modifier | consumer | vendor

    @property
    def hid_usage(self) -> int | None:
        """HID usage for page-0 keys, else ``None``."""
        return (self.value & 0xFF) if self.page == KEYMAP_PAGE_KEYBOARD else None

    @property
    def modifier_mask(self) -> int | None:
        """Modifier bitmask for page-0 keys, else ``None``."""
        return ((self.value >> 16) & 0xFF) if self.page == KEYMAP_PAGE_KEYBOARD else None


def decode_keymap_record(record: int, position: int = 0) -> KeyAction:
    """Decode one big-endian 32-bit action code into a :class:`KeyAction`.

    Live vectors: Esc `0x00000029`, LShift `0x00020000`, Mute `0x020000E2`,
    FN1 Esc `0x07000004`, FN1 ```` `0x08070000``.
    """
    if not 0 <= record <= 0xFFFFFFFF:
        raise KreoProtocolError(f"Action code out of range: {record:#x}")

    page = (record >> 24) & 0xFF
    value = record & 0xFFFFFF

    if record == 0:
        kind = "empty"
    elif page == KEYMAP_PAGE_KEYBOARD:
        modifier = (value >> 16) & 0xFF
        usage = value & 0xFF
        if usage == 0 and modifier:
            kind = "modifier"
        elif modifier:
            kind = "keyboard+modifier"
        else:
            kind = "keyboard"
    elif page == KEYMAP_PAGE_CONSUMER:
        kind = "consumer"
    else:
        kind = "vendor"

    return KeyAction(position=position, page=page, value=value, kind=kind)


def decode_keymap_layer(
    payload: bytes,
    *,
    positions: int = MATRIX_LAYER_POSITIONS,
) -> list[KeyAction]:
    """Decode a full `GetMatrix` layer (504 bytes = 126 x 4, big-endian)."""
    expected = positions * KEYMAP_RECORD_SIZE
    if len(payload) < expected:
        raise KreoProtocolError(f"Keymap layer too short: {len(payload)} < {expected}")
    return [
        decode_keymap_record(
            int.from_bytes(payload[i * 4 : i * 4 + 4], "big"), position=i
        )
        for i in range(positions)
    ]


def build_macro_block(macros: Sequence[bytes]) -> bytes:
    """Build a macro block: `(offset, size)` LE16 table followed by the blobs.

    Offsets include the `n * 4` byte header bias, so they are absolute from the
    start of the block (confirmed in `FUN_0048e340`).
    """
    header_size = len(macros) * 4
    if header_size > 0xFFFF:
        raise KreoProtocolError("Too many macros for a 16-bit header")

    table = bytearray()
    offset = header_size
    for blob in macros:
        size = len(blob)
        if offset > 0xFFFF or size > 0xFFFF:
            raise KreoProtocolError("Macro block exceeds 16-bit offset/size space")
        table += struct.pack("<HH", offset, size)
        offset += size

    return bytes(table) + b"".join(bytes(m) for m in macros)


def build_rgb_table(
    entries: Sequence[Sequence[tuple[int, int, int]]],
    *,
    crc: bool = True,
    pad_size: int = RGB_TAB_PAD_SIZE,
) -> bytes:
    """Build the 21-byte-per-key RGB table used by `SetLedRgbTab`.

    Each entry is 7 RGB triples (7 zones per key). When `crc` is set the table
    is zero-padded to `pad_size` and terminated with `5A A5` at the last two
    bytes, matching `cfg+0x2ff5` / `KB.ini CRC=1` (confirmed in
    `FUN_0048ec30`).
    """
    out = bytearray()
    for entry in entries:
        if len(entry) != RGB_TAB_ZONES:
            raise KreoProtocolError(
                f"RGB table entry needs {RGB_TAB_ZONES} colours, got {len(entry)}"
            )
        for rgb in entry:
            if len(rgb) != 3:
                raise KreoProtocolError(f"RGB triple must have 3 components, got {rgb!r}")
            out += bytes(
                (int(rgb[0]) & 0xFF, int(rgb[1]) & 0xFF, int(rgb[2]) & 0xFF)
            )

    if not crc:
        return bytes(out)

    if len(out) > pad_size - len(RGB_TAB_CRC_TAIL):
        raise KreoProtocolError(f"RGB table ({len(out)}) does not fit in {pad_size} bytes")
    out += bytes(pad_size - len(out) - len(RGB_TAB_CRC_TAIL))
    out += RGB_TAB_CRC_TAIL
    return bytes(out)


def split_rgb_table(
    raw: bytes,
    *,
    entry_count: int = RGB_TAB_ENTRY_COUNT,
) -> tuple[list[bytes], bytes]:
    """Split a `GetLedRgbTab` reply into 21-byte entries plus its Psd trailer.

    Live replies are `entry_count * 21` bytes (483) followed by a 7-byte trailer
    whose first 6 bytes equal `KB.ini`'s `Psd`. The wired path additionally pads
    with zeros, `5A A5` and `00 10 00 00`; that padding is ignored here.
    """
    expected = entry_count * RGB_TAB_ENTRY_SIZE
    needed = expected + RGB_TAB_PSD_TRAILER_SIZE
    if len(raw) < needed:
        raise KreoProtocolError(f"RGB table reply too short: {len(raw)} < {needed}")
    entries = [
        raw[index * RGB_TAB_ENTRY_SIZE : (index + 1) * RGB_TAB_ENTRY_SIZE]
        for index in range(entry_count)
    ]
    return entries, raw[expected:needed]


# ---------------------------------------------------------
# Wired HID Transmissions (Feature Reports)
# ---------------------------------------------------------


def read_profile_wired(transport: HidTransport) -> bytes:
    """Read 128-byte profile over wired USB feature reports."""
    padding = [0] * (WIRED_FEATURE_REPORT_SIZE - 1 - len(PROFILE_READ_CMD))
    payload = bytes([WIRED_WRITE_REPORT_ID, *PROFILE_READ_CMD, *padding])
    transport.send_feature_report(payload)

    response = transport.get_feature_report(WIRED_READ_REPORT_ID, WIRED_FEATURE_REPORT_SIZE)
    if len(response) < 8 + MAX_PROFILE_SIZE:
        raise KreoProtocolError(f"Incomplete wired profile response: {len(response)} bytes")

    return response[8 : 8 + MAX_PROFILE_SIZE]


def write_profile_wired(transport: HidTransport, profile: bytes) -> None:
    """Write 128-byte profile over wired USB feature reports."""
    if len(profile) != MAX_PROFILE_SIZE:
        raise KreoProtocolError(f"Profile write requires {MAX_PROFILE_SIZE} bytes, got {len(profile)}")
    command = PROFILE_WRITE_CMD + profile
    padding = [0] * (WIRED_FEATURE_REPORT_SIZE - 1 - len(command))
    payload = bytes([WIRED_WRITE_REPORT_ID, *command, *padding])
    transport.send_feature_report(payload)


def read_light_table_wired(transport: HidTransport) -> bytes:
    """Read RGB palette table over wired USB feature reports (483 or 490 bytes)."""
    padding = [0] * (WIRED_FEATURE_REPORT_SIZE - 1 - len(LIGHT_TABLE_READ_CMD))
    payload = bytes([WIRED_WRITE_REPORT_ID, *LIGHT_TABLE_READ_CMD, *padding])
    transport.send_feature_report(payload)

    response = transport.get_feature_report(WIRED_READ_REPORT_ID, WIRED_FEATURE_REPORT_SIZE)
    if len(response) < 8 + LIGHT_TABLE_SIZE:
        raise KreoProtocolError(f"Incomplete wired light table response: {len(response)} bytes")

    avail = len(response) - 8
    read_len = min(avail, RGB_TAB_TOTAL_BYTES)
    return response[8 : 8 + read_len]


def write_light_table_wired(transport: HidTransport, light_table: bytes) -> None:
    """Write RGB palette table over wired USB feature reports."""
    if len(light_table) not in (LIGHT_TABLE_SIZE, RGB_TAB_TABLE_BYTES, RGB_TAB_TOTAL_BYTES):
        raise KreoProtocolError(
            f"Light table requires {LIGHT_TABLE_SIZE}, {RGB_TAB_TABLE_BYTES}, or {RGB_TAB_TOTAL_BYTES} bytes, got {len(light_table)}"
        )
    table_payload = light_table
    if len(table_payload) == RGB_TAB_TABLE_BYTES:
        table_payload = table_payload + RGB_TAB_DEFAULT_PSD_TRAILER
    elif len(table_payload) == LIGHT_TABLE_SIZE:
        table_payload = table_payload + bytes([0] * 3) + RGB_TAB_DEFAULT_PSD_TRAILER

    command = LIGHT_TABLE_WRITE_CMD + table_payload
    padding = [0] * (WIRED_FEATURE_REPORT_SIZE - 1 - len(command))
    payload = bytes([WIRED_WRITE_REPORT_ID, *command, *padding])
    transport.send_feature_report(payload)


def read_custom_light_wired(transport: HidTransport) -> bytes:
    """Read 378-byte planar custom light frame over wired USB."""
    padding = [0] * (WIRED_FEATURE_REPORT_SIZE - 1 - len(CUSTOM_LIGHT_PREPARE_CMD))
    payload = bytes([WIRED_WRITE_REPORT_ID, *CUSTOM_LIGHT_PREPARE_CMD, *padding])
    transport.send_feature_report(payload)

    response = transport.get_feature_report(WIRED_READ_REPORT_ID, WIRED_FEATURE_REPORT_SIZE)
    if len(response) < 8 + CUSTOM_FRAME_SIZE:
        raise KreoProtocolError(f"Incomplete wired custom light response: {len(response)} bytes")

    return response[8 : 8 + CUSTOM_FRAME_SIZE]


def write_custom_light_wired(transport: HidTransport, planar_frame: bytes) -> None:
    """Write 378-byte planar custom light frame (padded to 512 bytes) over wired USB."""
    if len(planar_frame) != CUSTOM_FRAME_SIZE:
        raise KreoProtocolError(f"Planar frame requires {CUSTOM_FRAME_SIZE} bytes, got {len(planar_frame)}")

    # Pad planar frame to 512 bytes payload
    payload_512 = planar_frame + bytes([0] * (512 - len(planar_frame)))
    command = CUSTOM_LIGHT_WRITE_CMD + payload_512
    padding = [0] * (WIRED_FEATURE_REPORT_SIZE - 1 - len(command))
    payload = bytes([WIRED_WRITE_REPORT_ID, *command, *padding])
    transport.send_feature_report(payload)


# ---------------------------------------------------------
# Wireless 2.4 GHz Chunk Transmissions
# ---------------------------------------------------------


def _read_wireless_stream(
    transport: HidTransport,
    query_cmd: int,
    expected_response_cmd: int,
    expected_bytes: int,
    *,
    flag: int = 0,
) -> bytes:
    """Send a query with proper 20-byte framing and assemble multi-packet response chunks from wireless receiver.

    `flag` is the caller-supplied high nibble of byte 4 (layer / group / page),
    the same value `AccessData` takes as its second argument.
    """
    # Drain stale unread packets if any
    for _ in range(50):
        stale = transport.read(64, timeout_ms=5)
        if len(stale) == 0:
            break

    body = bytes([query_cmd, 1, 0, (flag & 0x0F) << 4]) + bytes(14)
    chk = calculate_wireless_checksum(body)
    query = bytes([WIRELESS_REPORT_ID, *body, chk])
    transport.write(query)

    packets: dict[int, bytes] = {}
    total_packets: int | None = None
    start_time = time.monotonic()
    last_packet_time = time.monotonic()

    while total_packets is None or len(packets) < total_packets:
        if total_packets is None and (time.monotonic() - start_time > 1.2):
            raise KreoTimeoutError(
                f"Keyboard did not respond to command {query_cmd} within 1.2s (device may be idle/asleep)"
            )

        if time.monotonic() - last_packet_time > 1.2 or time.monotonic() - start_time > 3.0:
            if total_packets is not None and len(packets) > 0:
                assembled = b"".join(packets.get(i, b"\x00" * WIRELESS_CHUNK_SIZE) for i in range(total_packets))
                return assembled[:expected_bytes]
            raise KreoTimeoutError(
                f"Timed out reading command {query_cmd} chunks (received {len(packets)} of {total_packets})"
            )

        packet = transport.read(64, timeout_ms=100)
        if len(packet) == 0:
            continue

        last_packet_time = time.monotonic()
        payload = packet[1:] if packet[0] == WIRELESS_REPORT_ID else packet

        if len(payload) < 5 or payload[0] != expected_response_cmd:
            continue

        total_packets = payload[1]
        chunk_idx = payload[2]
        declared = payload[3] & 0x0F
        # Live frames carry the real chunk length in the low nibble, including a
        # short final chunk (e.g. 2 bytes for the 128-byte profile).
        packets[chunk_idx] = payload[4 : 4 + (declared or WIRELESS_CHUNK_SIZE)]

    assembled = b"".join(packets.get(i, b"\x00" * WIRELESS_CHUNK_SIZE) for i in range(total_packets))
    return assembled[:expected_bytes]


def _write_wireless_chunked(
    transport: HidTransport,
    command: int,
    payload: bytes,
    *,
    flag: int = 0,
    total: int | None = None,
    chunk_delay: float = 0.015,
) -> None:
    """Send `payload` in 14-byte chunks using the 20-byte `0x13` framing.

    `flag` is the caller-supplied high nibble of byte 4 (layer / group / page),
    matching `AccessData(cmd, nibble, buf, len, ...)`.
    """
    for packet in build_wireless_packets(command, payload, flag=flag, total=total):
        transport.write(packet)
        if chunk_delay > 0:
            time.sleep(chunk_delay)


def write_g5kb_chunked(
    transport: HidTransport,
    command: int,
    payload: bytes,
    *,
    param: int = 0,
    report_id: int = G5KB_REPORT_ID_FW_18,
    chunk_size: int = G5KB_CHUNK_SIZE,
    chunk_delay: float = G5KB_CHUNK_DELAY,
) -> None:
    """Write a payload over HID feature reports in 512-byte chunks.

    Mirrors `FUN_0048c600`: one fixed 520-byte frame per chunk, `Sleep(20 ms)`
    before each transfer.
    """
    if chunk_size <= 0 or chunk_size > G5KB_FEATURE_REPORT_SIZE - 8:
        raise KreoProtocolError(f"Invalid feature chunk size: {chunk_size}")

    total = max(1, (len(payload) + chunk_size - 1) // chunk_size)
    for index in range(total):
        start = index * chunk_size
        chunk = payload[start : start + chunk_size]
        frame = build_feature_frame(
            command,
            chunk,
            param=param,
            index=index,
            total=total,
            report_id=report_id,
        )
        if chunk_delay > 0:
            time.sleep(chunk_delay)
        transport.send_feature_report(frame)


def read_g5kb(
    transport: HidTransport,
    command: int,
    *,
    expected_bytes: int,
    param: int = 0,
    report_id: int = G5KB_REPORT_ID_FW_18,
    chunk_delay: float = G5KB_CHUNK_DELAY,
    poll_retries: int = 3,
    poll_delay: float = G5KB_RETRY_DELAY,
) -> bytes:
    """Run a wired read command and assemble its chunked feature-reply payload.

    Each chunk is a `SetFeature` request followed by a `GetFeature` reply with
    the same command/index header.
    """
    total = max(1, (expected_bytes + G5KB_CHUNK_SIZE - 1) // G5KB_CHUNK_SIZE)
    assembled = bytearray()

    for index in range(total):
        want = min(G5KB_CHUNK_SIZE, expected_bytes - len(assembled))
        request = build_feature_frame(
            command,
            b"",
            param=param,
            index=index,
            total=total,
            length=want,
            report_id=report_id,
        )
        if chunk_delay > 0:
            time.sleep(chunk_delay)
        transport.send_feature_report(request)

        reply: bytes | None = None
        for _ in range(poll_retries):
            if chunk_delay > 0:
                time.sleep(chunk_delay)
            raw = transport.get_feature_report(report_id, G5KB_FEATURE_REPORT_SIZE)
            candidate = parse_feature_frame(report_id, raw)
            if candidate:
                reply = candidate
                break
            if poll_delay > 0:
                time.sleep(poll_delay)

        if reply is None:
            raise KreoTimeoutError(
                f"No feature reply for command {command:#04x} chunk {index}"
            )
        assembled += reply[:want]

    if len(assembled) < expected_bytes:
        raise KreoProtocolError(
            f"Short feature reply for command {command:#04x}: "
            f"{len(assembled)} of {expected_bytes} bytes"
        )
    return bytes(assembled[:expected_bytes])


def read_keymap_wired(transport: HidTransport, layer: int = 0) -> bytes:
    """Read one 504-byte keymap layer over the wired feature transport (`0x83`)."""
    return read_g5kb(
        transport,
        G5KB_CMD_GET_MATRIX,
        expected_bytes=MATRIX_LAYER_POSITIONS * KEYMAP_RECORD_SIZE,
        param=layer & 0xFF,
    )


def read_keymap_wireless(transport: HidTransport, layer: int = 0) -> bytes:
    """Read one 504-byte keymap layer from the 2.4 GHz dongle (`0x41`)."""
    return _read_wireless_stream(
        transport,
        WIRELESS_CMD_MATRIX_READ,
        WIRELESS_CMD_MATRIX_READ,
        MATRIX_LAYER_POSITIONS * KEYMAP_RECORD_SIZE,
        flag=layer,
    )


def write_keymap_wired(transport: HidTransport, layer_bytes: bytes, layer: int = 0) -> None:
    """Write one 504-byte keymap layer over the wired feature transport (`0x03`)."""
    expected = MATRIX_LAYER_POSITIONS * KEYMAP_RECORD_SIZE
    if len(layer_bytes) != expected:
        raise KreoProtocolError(f"Keymap layer requires {expected} bytes, got {len(layer_bytes)}")
    write_g5kb_chunked(
        transport,
        G5KB_CMD_SET_MATRIX,
        layer_bytes,
        param=layer & 0xFF,
    )


def write_keymap_wireless(transport: HidTransport, layer_bytes: bytes, layer: int = 0) -> None:
    """Write one 504-byte keymap layer to the 2.4 GHz dongle (`0x01`)."""
    expected = MATRIX_LAYER_POSITIONS * KEYMAP_RECORD_SIZE
    if len(layer_bytes) != expected:
        raise KreoProtocolError(f"Keymap layer requires {expected} bytes, got {len(layer_bytes)}")
    _write_wireless_chunked(
        transport=transport,
        command=WIRELESS_CMD_MATRIX_WRITE,
        payload=layer_bytes,
        flag=layer,
    )


def read_profile_wireless(transport: HidTransport) -> bytes:
    """Read 128-byte profile from 2.4 GHz RF dongle."""
    return _read_wireless_stream(
        transport=transport,
        query_cmd=WIRELESS_CMD_PROFILE_READ,
        expected_response_cmd=WIRELESS_CMD_PROFILE_READ,
        expected_bytes=MAX_PROFILE_SIZE,
    )


def write_profile_wireless(transport: HidTransport, profile: bytes) -> None:
    """Write 128-byte profile to 2.4 GHz RF dongle."""
    if len(profile) != MAX_PROFILE_SIZE:
        raise KreoProtocolError(f"Wireless profile write requires {MAX_PROFILE_SIZE} bytes, got {len(profile)}")
    _write_wireless_chunked(
        transport=transport,
        command=WIRELESS_CMD_PROFILE_WRITE,
        payload=profile,
    )


def read_light_table_wireless(transport: HidTransport) -> bytes:
    """Read RGB palette table from 2.4 GHz RF dongle."""
    return _read_wireless_stream(
        transport=transport,
        query_cmd=WIRELESS_CMD_LIGHT_TABLE_READ,
        expected_response_cmd=WIRELESS_CMD_LIGHT_TABLE_READ,
        expected_bytes=RGB_TAB_TOTAL_BYTES,
    )


def write_light_table_wireless(transport: HidTransport, light_table: bytes) -> None:
    """Write RGB palette table (padded to 512 bytes) to 2.4 GHz RF dongle."""
    if len(light_table) not in (LIGHT_TABLE_SIZE, RGB_TAB_TABLE_BYTES, RGB_TAB_TOTAL_BYTES):
        raise KreoProtocolError(
            f"Light table requires {LIGHT_TABLE_SIZE}, {RGB_TAB_TABLE_BYTES}, or {RGB_TAB_TOTAL_BYTES} bytes, got {len(light_table)}"
        )
    padded = bytes([*light_table, *([0] * (WIRELESS_PADDING_SIZE - len(light_table)))])
    _write_wireless_chunked(
        transport=transport,
        command=WIRELESS_CMD_LIGHT_TABLE_WRITE,
        payload=padded,
    )


def read_custom_light_wireless(transport: HidTransport) -> bytes:
    """Read 378-byte interleaved custom light frame from 2.4 GHz RF dongle."""
    return _read_wireless_stream(
        transport=transport,
        query_cmd=WIRELESS_CMD_CUSTOM_LIGHT_READ,
        expected_response_cmd=WIRELESS_CMD_CUSTOM_LIGHT_READ,
        expected_bytes=CUSTOM_FRAME_SIZE,
    )


def write_custom_light_wireless(
    transport: HidTransport,
    interleaved_frame: bytes,
    *,
    wake_first: bool = False,
) -> None:
    """
    Write 378-byte planar custom light frame (padded to 512 bytes) to 2.4 GHz RF dongle.
    Only sends wakeup read query when wake_first=True to maximize streaming framerate.
    """
    if len(interleaved_frame) != CUSTOM_FRAME_SIZE:
        raise KreoProtocolError(
            f"Interleaved frame requires {CUSTOM_FRAME_SIZE} bytes, got {len(interleaved_frame)}"
        )

    # Wakeup query only if explicitly requested
    if wake_first:
        try:
            query = bytes([WIRELESS_REPORT_ID, WIRELESS_CMD_CUSTOM_LIGHT_READ] + [0] * 17)
            transport.write(query)
            _ = transport.read(64, timeout_ms=50)
            time.sleep(0.02)
        except Exception:
            pass

    padded = bytes([*interleaved_frame, *([0] * (WIRELESS_PADDING_SIZE - len(interleaved_frame)))])
    _write_wireless_chunked(
        transport=transport,
        command=WIRELESS_CMD_CUSTOM_LIGHT_WRITE,
        payload=padded,
    )
