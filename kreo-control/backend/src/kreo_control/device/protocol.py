from __future__ import annotations

import time
from kreo_control.device.transport import HidTransport, KreoProtocolError, KreoTimeoutError
from kreo_control.lighting.constants import (
    CUSTOM_FRAME_SIZE,
    LIGHTING_MODES,
    LIGHT_TABLE_SIZE,
    MAX_PROFILE_SIZE,
    LOGICAL_TO_HW_EFFECT,
    HW_EFFECT_TO_LOGICAL,
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
WIRELESS_CMD_LIGHT_TABLE_READ = 73
WIRELESS_CMD_LIGHT_TABLE_WRITE = 9
WIRELESS_CMD_CUSTOM_LIGHT_READ = 66
WIRELESS_CMD_CUSTOM_LIGHT_WRITE = 2

CUSTOM_MODE_ID = 277
STATIC_MODE_ID = 1
SNOW_MODE_ID = 19


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
    effect_type: int = 1,
) -> bytes:
    """
    Construct a validated 128-byte profile with updated mode, brightness, and speed.
    Uses golden truth SinoWealth hardware effect IDs from Dev/kb/KB.ini.
    """
    updated = bytearray(profile)

    if mode_id in (CUSTOM_MODE_ID, 21):
        effective_brightness = min(4, max(1, brightness_level))
        updated[1] = 21
        updated[2] = effective_brightness & 0xFF
        updated[3] = 0
        updated[9] = 1
        updated[10] = 21
    else:
        hw_effect = LOGICAL_TO_HW_EFFECT.get(mode_id, mode_id)
        updated[1] = hw_effect & 0xFF
        updated[2] = brightness_level & 0xFF
        updated[3] = speed & 0xFF
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
    """Read 480-byte light table over wired USB feature reports."""
    padding = [0] * (WIRED_FEATURE_REPORT_SIZE - 1 - len(LIGHT_TABLE_READ_CMD))
    payload = bytes([WIRED_WRITE_REPORT_ID, *LIGHT_TABLE_READ_CMD, *padding])
    transport.send_feature_report(payload)

    response = transport.get_feature_report(WIRED_READ_REPORT_ID, WIRED_FEATURE_REPORT_SIZE)
    if len(response) < 8 + LIGHT_TABLE_SIZE:
        raise KreoProtocolError(f"Incomplete wired light table response: {len(response)} bytes")

    return response[8 : 8 + LIGHT_TABLE_SIZE]


def write_light_table_wired(transport: HidTransport, light_table: bytes) -> None:
    """Write 480-byte light table over wired USB feature reports."""
    if len(light_table) != LIGHT_TABLE_SIZE:
        raise KreoProtocolError(f"Light table requires {LIGHT_TABLE_SIZE} bytes, got {len(light_table)}")
    command = LIGHT_TABLE_WRITE_CMD + light_table
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
) -> bytes:
    """Send a query with proper 20-byte framing and assemble multi-packet response chunks from wireless receiver."""
    # Drain stale unread packets if any
    for _ in range(50):
        stale = transport.read(64, timeout_ms=5)
        if len(stale) == 0:
            break

    body = bytes([query_cmd, 1] + [0] * 16)
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
        packets[chunk_idx] = payload[4:-1]

    assembled = b"".join(packets.get(i, b"\x00" * WIRELESS_CHUNK_SIZE) for i in range(total_packets))
    return assembled[:expected_bytes]


def _write_wireless_chunked(
    transport: HidTransport,
    command: int,
    payload: bytes,
    *,
    chunk_delay: float = 0.005,
) -> None:
    """Send payload in 14-byte chunks with 20-byte framing and verified ACK handshake to 2.4 GHz wireless receiver."""
    total_chunks = max(1, (len(payload) + WIRELESS_CHUNK_SIZE - 1) // WIRELESS_CHUNK_SIZE)

    for index in range(total_chunks):
        start = index * WIRELESS_CHUNK_SIZE
        chunk = payload[start : start + WIRELESS_CHUNK_SIZE]
        padded_chunk = bytes([*chunk, *([0] * (WIRELESS_CHUNK_SIZE - len(chunk)))])

        length_byte = len(chunk)
        if index == total_chunks - 1 and len(chunk) == WIRELESS_CHUNK_SIZE:
            length_byte = 2

        body = bytes([command, total_chunks & 0xFF, index & 0xFF, length_byte, *padded_chunk])
        checksum = calculate_wireless_checksum(body)
        packet = bytes([WIRELESS_REPORT_ID, *body, checksum])

        for attempt in range(3):
            bytes_written = transport.write(packet)
            if bytes_written <= 0:
                time.sleep(0.005)
                continue

            # Read ACK packet from wireless receiver
            ack = transport.read(64, timeout_ms=150)
            if len(ack) > 1 and ack[0] == WIRELESS_REPORT_ID and ack[1] == command:
                break
            time.sleep(0.005)

        if chunk_delay > 0:
            time.sleep(chunk_delay)


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
    """Read 480-byte light table from 2.4 GHz RF dongle."""
    return _read_wireless_stream(
        transport=transport,
        query_cmd=WIRELESS_CMD_LIGHT_TABLE_READ,
        expected_response_cmd=WIRELESS_CMD_LIGHT_TABLE_READ,
        expected_bytes=LIGHT_TABLE_SIZE,
    )


def write_light_table_wireless(transport: HidTransport, light_table: bytes) -> None:
    """Write 480-byte light table (padded to 512 bytes) to 2.4 GHz RF dongle."""
    if len(light_table) != LIGHT_TABLE_SIZE:
        raise KreoProtocolError(f"Light table requires {LIGHT_TABLE_SIZE} bytes, got {len(light_table)}")
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
