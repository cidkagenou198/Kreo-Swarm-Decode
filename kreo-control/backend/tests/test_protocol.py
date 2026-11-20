from __future__ import annotations

import pytest
from kreo_control.device.protocol import (
    calculate_wireless_checksum,
    find_second_255_index,
    parse_effect_indices,
    parse_mode_id,
    parse_profile,
    build_profile_write,
    build_wireless_frame,
    build_wireless_packets,
    build_feature_frame,
    parse_feature_frame,
    g5kb_report_id,
    build_keymap_layer,
    build_macro_block,
    build_rgb_table,
    decode_keymap_layer,
    decode_keymap_record,
    pack_base_key,
    pack_keyboard_action,
    split_rgb_table,
    G5KB_FEATURE_REPORT_SIZE,
    G5KB_REPORT_ID_FW_18,
    G5KB_REPORT_ID_OTHER,
    WIRELESS_CHUNK_SIZE,
    WIRELESS_REPORT_ID,
)
from kreo_control.lighting.constants import (
    HW_EFFECT_TO_LOGICAL,
    LOGICAL_TO_HW_EFFECT,
    VENDOR_EFFECT_CAPABILITIES,
)


def test_calculate_wireless_checksum():
    body = bytes([0x44, 0x0A, 0x00, 0x0E, 0x00, 0x03, 0x03, 0x02, 0x00, 0x00, 0x04, 0x04, 0x07, 0x00, 0x0B, 0x20, 0x01, 0x00])
    chk = calculate_wireless_checksum(body)
    assert chk == 0xB2


def test_parse_profile():
    raw = bytearray([0] * 128)
    raw[0] = 0x00
    raw[1] = 0x02  # Rainbow hardware effect ID (KB.ini LedOpt3)
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


def test_vendor_effect_id_table_from_kb_ini():
    """Regression vectors from the official `Dev/kb/KB.ini` LedOpt rows."""
    assert LOGICAL_TO_HW_EFFECT == {
        0: 0, 1: 1, 2: 3, 3: 2, 4: 19, 5: 15, 6: 13, 7: 20,
        8: 16, 9: 18, 10: 5, 11: 7, 12: 17, 13: 12, 14: 8,
        15: 28, 16: 30, 17: 14, 18: 29, 19: 21, 277: 21,
    }
    assert HW_EFFECT_TO_LOGICAL[3] == 2
    assert HW_EFFECT_TO_LOGICAL[30] == 16
    assert VENDOR_EFFECT_CAPABILITIES[1] == (0, 1, 0, 1, 1)
    assert VENDOR_EFFECT_CAPABILITIES[15] == (1, 1, 0, 0, 0)


# ---------------------------------------------------------
# Frame builders (decoded from OemDrv.exe)
# ---------------------------------------------------------


def test_build_wireless_frame_layout_and_checksum():
    payload = bytes(range(1, 1 + WIRELESS_CHUNK_SIZE))
    frame = build_wireless_frame(0x01, index=0, total=1, payload=payload, flag=2)

    assert len(frame) == 20
    assert frame[0] == WIRELESS_REPORT_ID
    assert frame[1] == 0x01
    assert frame[2] == 0x01  # total
    assert frame[3] == 0x00  # index
    # high nibble = flag (layer 2), low nibble = payload length (14)
    assert frame[4] == (2 << 4) | WIRELESS_CHUNK_SIZE
    assert frame[5:19] == payload
    assert frame[19] == calculate_wireless_checksum(frame[1:19])


def test_build_wireless_frame_short_chunk_is_zero_padded():
    frame = build_wireless_frame(0x41, index=0, total=1, payload=b"\xaa\xbb")
    assert frame[4] == 2
    assert frame[5:7] == b"\xaa\xbb"
    assert frame[7:19] == b"\x00" * 12


def test_build_wireless_packets_chunks_and_pads():
    payload = bytes([0xC3] * 128)
    frames = build_wireless_packets(0x04, payload)
    assert len(frames) == 10  # ceil(128 / 14)
    assert all(len(f) == 20 for f in frames)
    assert [f[3] for f in frames] == list(range(10))
    assert all(f[2] == 10 for f in frames)
    assert frames[0][4] == WIRELESS_CHUNK_SIZE
    # last chunk holds 128 - 9*14 = 2 bytes
    assert frames[-1][4] == 2


def test_build_wireless_packets_pad_to_512():
    frames = build_wireless_packets(0x09, b"\x00\x01", pad_to=512)
    assert len(frames) == 37  # ceil(512 / 14)
    assert frames[0][4] == WIRELESS_CHUNK_SIZE


def test_g5kb_report_id_follows_firmware_version():
    assert g5kb_report_id(0x18) == G5KB_REPORT_ID_FW_18 == 0x06
    assert g5kb_report_id(0x1A) == G5KB_REPORT_ID_OTHER == 0x09
    assert g5kb_report_id(0x00) == 0x09


def test_build_feature_frame_layout():
    payload = bytes([0x11] * 128)
    frame = build_feature_frame(0x04, payload, param=0, index=0, total=1, report_id=0x06)

    assert len(frame) == G5KB_FEATURE_REPORT_SIZE
    assert frame[0] == 0x06
    assert frame[1] == 0x04
    assert frame[2] == 0x00
    assert frame[3] == 0x00
    assert frame[4] == 0x01
    assert frame[5] == 0x00
    assert frame[6:8] == b"\x80\x00"  # 128 LE16
    assert frame[8:136] == payload
    assert frame[136:] == b"\x00" * (G5KB_FEATURE_REPORT_SIZE - 136)


def test_build_feature_frame_chunk_header():
    frame = build_feature_frame(0x03, b"\x00" * 512, param=1, index=2, total=3)
    assert frame[2] == 1
    assert frame[4] == 3
    assert frame[5] == 2
    assert frame[6:8] == b"\x00\x02"  # 512 LE16


def test_build_feature_frame_read_advertises_requested_length():
    # Live wired GetLED request: header 06 84 00 00 01 00 80 00.
    frame = build_feature_frame(0x84, b"", length=128, report_id=0x06)
    assert frame[:8] == b"\x06\x84\x00\x00\x01\x00\x80\x00"
    assert frame[8:] == b"\x00" * (G5KB_FEATURE_REPORT_SIZE - 8)


def test_parse_feature_frame_roundtrip():
    payload = bytes(range(1, 65))
    frame = build_feature_frame(0x84, payload, index=0, total=1)
    assert parse_feature_frame(0x06, frame) == payload


def test_pack_base_key_matches_live_layer0_records():
    # Live GetMatrix layer 0 vectors (2026-11-18).
    assert pack_base_key(0x29) == 0x00000029  # Esc
    assert pack_base_key(0x14) == 0x00000014  # Q
    assert pack_base_key(0x3A) == 0x0000003A  # F1
    assert pack_base_key(0x00, 0x02) == 0x00020000  # LShift
    assert pack_base_key(0x00, 0x01) == 0x00010000  # LCtrl
    assert pack_base_key(0x00, 0x08) == 0x00080000  # LWin


def test_pack_keyboard_action_matches_live_fn1_records():
    # Live GetMatrix layer 1 vectors; identical to KB.ini [FN1] values.
    assert pack_keyboard_action(0x07, 0x000004) == 0x07000004
    assert pack_keyboard_action(0x08, 0x070000) == 0x08070000
    assert pack_keyboard_action(0x02, 0x000194) == 0x02000194
    assert pack_keyboard_action(0x02, 0x000223) == 0x02000223


def test_build_keymap_layer_is_big_endian_with_126_records():
    layer = build_keymap_layer(
        {
            0: pack_base_key(0x29),
            4: pack_base_key(0x00, 0x02),
            12: pack_keyboard_action(0x02, 0x000194),
        }
    )
    assert len(layer) == 126 * 4 == 504
    assert layer[0:4] == b"\x00\x00\x00\x29"
    assert layer[16:20] == b"\x00\x02\x00\x00"
    assert layer[48:52] == b"\x02\x00\x01\x94"
    assert layer[4:8] == b"\x00\x00\x00\x00"


def test_build_keymap_layer_sequence_and_bounds():
    layer = build_keymap_layer([0x00000029, 0x00000035], matrix_len=4, fill=0)
    assert layer == b"\x00\x00\x00\x29" b"\x00\x00\x00\x35" b"\x00\x00\x00\x00" b"\x00\x00\x00\x00"
    with pytest.raises(Exception):
        build_keymap_layer({4: 1}, matrix_len=4)


def test_decode_keymap_record_matches_live_vectors():
    assert decode_keymap_record(0x00000029) == (0, 0x00, 0x29, "keyboard")
    assert decode_keymap_record(0x00020000) == (0, 0x00, 0x020000, "modifier")
    assert decode_keymap_record(0x00090005) == (0, 0x00, 0x090005, "keyboard+modifier")
    assert decode_keymap_record(0x020000E2) == (0, 0x02, 0x00E2, "consumer")
    assert decode_keymap_record(0x07000004) == (0, 0x07, 0x000004, "vendor")
    assert decode_keymap_record(0x08070000) == (0, 0x08, 0x070000, "vendor")
    assert decode_keymap_record(0x00000000) == (0, 0x00, 0x00, "empty")


def test_decode_keymap_record_properties():
    action = decode_keymap_record(0x0002001D, position=4)
    assert action.position == 4
    assert action.hid_usage == 0x1D  # Z
    assert action.modifier_mask == 0x02
    consumer = decode_keymap_record(0x020000E2)
    assert consumer.hid_usage is None
    assert consumer.modifier_mask is None


def test_decode_keymap_layer_round_trips_build_keymap_layer():
    assignments = {
        0: pack_base_key(0x29),
        4: pack_base_key(0x00, 0x02),
        12: pack_keyboard_action(0x02, 0x000194),
        90: pack_keyboard_action(0x02, 0x00E2),
    }
    actions = decode_keymap_layer(build_keymap_layer(assignments))
    assert len(actions) == 126
    assert actions[0].kind == "keyboard" and actions[0].hid_usage == 0x29
    assert actions[4].kind == "modifier" and actions[4].modifier_mask == 0x02
    assert actions[12].kind == "consumer" and actions[12].value == 0x000194
    assert actions[90].kind == "consumer" and actions[90].value == 0x00E2
    assert sum(1 for a in actions if a.kind != "empty") == 4
    with pytest.raises(Exception):
        decode_keymap_layer(b"\x00" * 500)


def test_read_keymap_wireless_requests_layer_and_assembles_chunks():
    import kreo_control.device.protocol as protocol

    payload = build_keymap_layer(
        {0: pack_base_key(0x29), 90: pack_keyboard_action(0x02, 0x00E2)}
    )
    frames = protocol.build_wireless_packets(0x41, payload, flag=1)

    class FakeWireless:
        """Drains silently, then replays the canned reply frames."""

        def __init__(self, replies):
            self.replies = list(replies)
            self.written: list[bytes] = []
            self._sent = False

        def write(self, data):
            self.written.append(bytes(data))
            self._sent = True
            return len(data)

        def read(self, length=64, timeout_ms=200):
            if not self._sent:
                return b""
            return self.replies.pop(0) if self.replies else b""

    fake = FakeWireless(frames)
    assert protocol.read_keymap_wireless(fake, 1) == payload

    request = fake.written[0]
    assert request[0] == 0x13
    assert request[1:5] == bytes([0x41, 1, 0, 0x10])  # cmd, total, idx, flag=1
    assert request[19] == protocol.calculate_wireless_checksum(request[1:19])


def test_build_macro_block_offsets_include_header():
    macros = [b"\xaa\xbb", b"\xcc\xdd\xee"]
    block = build_macro_block(macros)
    # 2 entries -> 8-byte header
    assert block[0:8] == b"\x08\x00\x02\x00\x0a\x00\x03\x00"
    assert block[8:] == b"\xaa\xbb\xcc\xdd\xee"


def test_build_rgb_table_crc_pad_and_tail():
    entry = [(i, i, i) for i in range(7)]
    table = build_rgb_table([entry], crc=True)
    assert len(table) == 0x200
    assert table[0:21] == bytes([v for rgb in entry for v in rgb])
    assert table[0x1FE:0x200] == b"\x5A\xA5"


def test_build_rgb_table_without_crc_targets_512_payload():
    entries = [[(0, 0, 0)] * 7 for _ in range(23)]
    table = build_rgb_table(entries, crc=False)
    assert len(table) == 23 * 21 == 483  # fits the 512-byte feature payload


def test_split_rgb_table_matches_live_wireless_reply():
    # Live GetLedRgbTab (0x49): 483-byte table + 7-byte Psd trailer.
    first_entry = bytes.fromhex(
        "ff0000" "00ff00" "0000ff" "ffff00" "ff00ff" "00ffff" "ffffff"
    )
    raw = first_entry + bytes(483 - 21) + bytes.fromhex("0300000001be01")
    entries, trailer = split_rgb_table(raw)
    assert len(entries) == 23
    assert entries[0] == first_entry
    assert trailer == bytes.fromhex("0300000001be01")


def test_split_rgb_table_ignores_wired_padding():
    # Live wired GetLedRgbTab (0x8A): table + trailer, zeros, 5A A5, 00 10 00 00.
    raw = bytes(483) + bytes.fromhex("0300000001be01") + bytes(16) + b"\x5A\xA5\x00\x10\x00\x00"
    assert len(raw) == 512
    entries, trailer = split_rgb_table(raw)
    assert len(entries) == 23
    assert trailer == bytes.fromhex("0300000001be01")
