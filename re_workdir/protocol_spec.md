# KreoSWARM75 protocol specification

Target: `C:\Program Files (x86)\KreoSWARM75\OemDrv.exe`
SHA-256 `ab0a2492c3538c247d4e6dfde1613cad5df78852490a41880a31fe47558b7117`
Image base `0x400000`. All addresses are virtual addresses.

## Evidence scope and status legend

- **CONFIRMED** = read directly from decompiled/disassembled vendor code.
- **HYPOTHESIS** = inferred from code shape or `KB.ini`; not yet validated on a
  device.
- **OPEN** = requires a USBPcap capture or report-descriptor dump.

No device write was performed during this investigation, and no firmware or
vendor binary was modified. Firmware update paths are deliberately not
documented here (see the DANGEROUS note at the end).

## Transport selection

The app implements **two independent transports** in two classes. A
`CDev3632` object is the outer driver and constructs a `CDevG5KB` object
(model `0x916`) through vtable slot `+0x1c` (`FUN_0048bb40`).

| Transport | Win32 API | Frame | Vendor class | Status |
|---|---|---|---|---|
| Interrupt OUT/IN | `WriteFile` / `ReadFile` | 20 bytes, report ID `0x13` | `CDev3632` | CONFIRMED |
| HID Feature | `HidD_SetFeature` / `HidD_GetFeature` | 520 bytes (`0x208`) | `CDevG5KB` | CONFIRMED |

Evidence for feature reports: `CALL 0x005ba914` (`HidD_SetFeature`) at
`0x0048c9d2` and `CALL 0x005ba91a` (`HidD_GetFeature`) at `0x0048ca07`, both in
`FUN_0048c880`.

Both devices are enumerated by usage page, not by literal VID/PID:

| Match | Meaning | Status |
|---|---|---|
| `usagePage=0xFF00, usage=1` | wired control collection | CONFIRMED |
| `usagePage=0xFF02, usage=2` | wireless dongle collection | CONFIRMED |

`nFw` (device info `+0x14`) must be `0x18` or `0x1a`. VID/PID come from
`KB.ini` at runtime (`VID=0x258a PID=0x010C`, `VID_Wireless=0x3554
PID_Wireless=0xfa09`) and are not literals in the binary.

**Verified on hardware (2026-11-18):** `3554:FA09` ("2.4G Wireless Receiver")
exposes collection `0xFF02/2` with input=20, output=20, **feature=0**, which
matches the enumerate check `entry[-3]==0x14, entry[-2]==0x14, entry[-4]==0x13`
and confirms the `0x13` interrupt transport. The dongle also exposes a separate
`0xFF04/2` collection with an 8-byte feature report (dongle-side control, not
the keyboard protocol). The `0x208` feature transport therefore belongs to the
wired `258A:010C` device.

## Transport A — wireless interrupt framing (report ID `0x13`)

### Wire format (CONFIRMED)

Every frame is exactly 20 bytes:

| offset | field | value |
|---:|---|---|
| 0 | report ID | `0x13` |
| 1 | command | see table |
| 2 | total chunk count | `ceil(len/14)`, `0x01` for queries |
| 3 | chunk index | 0-based |
| 4 | flag / length | low nibble = payload length (`0`..`0x0E`); **high nibble is a caller-supplied flag** |
| 5..18 | payload | 14 bytes, zero padded |
| 19 | checksum | `(0x13 + sum(bytes[1..18])) & 0xFF` |

Response frames use the same layout, but byte 1 is `cmd | 0x80`; bit 7 of
byte 1 indicates a CRC/transport error. ACK is read for all commands **except**
`cmd & 0x80` or `cmd == 0x06` (`FUN_00487260`).

Command dispatch: `AccessData(cmd, byte4_hi_nibble, buf, len, retry_log,
delay)`.

### Wireless command table (CONFIRMED)

| cmd | name | args |
|---:|---|---|
| `0x01` | SetMatrix | `(layer, buf, len)`; high nibble = layer |
| `0x41` | GetMatrix | `(layer, buf, len)` |
| `0x02` | SetGame (planar RGB) | `(index, buf, len)`; high nibble = index |
| `0x42` | GetGame | `(index, buf, len)` |
| `0x03` | SetMacro / WriteMacroData | pages of `0x200`, high nibble = page index, `Sleep(100)` between pages |
| `0x43` | GetMacro | `(0, buf, len)` |
| `0x04` | SetLED (128-byte profile) | `(0, buf, len)` |
| `0x44` | GetLED | `(0, buf, 0x80)` |
| `0x09` | SetLedRgbTab (21 B/key) | `(0, buf, len)` |
| `0x49` | GetLedRgbTab | `(0, buf, len)` |
| `0x0A` | SetOnBoard | `(0, &byte, 1)` |
| `0x4A` | GetOnBoard | `(0, buf, 1)` |
| `0x0B` | SetScreenParam | `(0, buf, len)` |
| `0x06` | ResetDevice | `(0, &byte, 1)`; no ACK |
| `0x07` | Online | writes result to `this+0x238`, `-1` on failure |

## Transport B — HID feature reports (wired)

### Feature frame (CONFIRMED)

A fixed **520-byte** buffer, always written whole:

| offset | width | field |
|---:|---:|---|
| 0 | 1 | report ID: `0x09` if `nFw != 0x18`, else `0x06` |
| 1 | 1 | command |
| 2 | 1 | parameter (layer / index, else `0`) |
| 3 | 1 | reserved, `0` |
| 4 | 1 | total chunk count |
| 5 | 1 | chunk index |
| 6 | 2 | payload length, LE16 |
| 8 | 512 | payload, zero padded |

Report ID derivation in asm is `(((nFw != 0x18) - 1) & 0xFD) + 9`. With
`KB.ini Fw=24` (`0x18`) the report ID is **`0x06`**.

**Verified on hardware (2026-11-18)** with `258A:010C` "Kreo Swarm":
the `0xFF00/1` control collection (Col06) reports
`FeatureReportByteLength = 520`, so `0x208` is the descriptor's real maximum.
Report ID `0x06` is accepted and `0x09` is rejected.

**Read commands carry the requested byte count in `[6..7]`.** The vendor
computes `_Size = min(0x200, length)` for reads too, with an empty payload.
Sending `len = 0` produces an 8-byte header-only ACK
(`06 84 00 00 01 00 00 00`). Live example: request
`06 84 00 00 01 00 80 00` → reply with the same header plus 128 payload bytes.
This is what `build_feature_frame(..., length=N)` in `protocol.py` encodes.

Chunking: 512-byte chunks. Per chunk: `Sleep(20 ms)` → `HidD_SetFeature(h, buf,
520)`; up to 3 attempts, `70 ms` apart; then `Sleep(20 ms)` →
`HidD_GetFeature(h, buf, 520)` for read-after-write operations. Response payload
is `buf[8 : 8+len]`.

### Live wired read results (CONFIRMED, 2026-11-18)

| Query | cmd | Result |
|---|---:|---|
| `GetLED` | `0x84` | 128 bytes, `FF FF` at 56/57, `5A A5` at 126/127 |
| `GetMatrix` | `0x83` | 504 bytes, byte-identical to the wireless read |
| `GetGame` | `0x86` | 378 bytes (3 × 126) |
| `GetLedRgbTab` | `0x8A` | 512 declared: 483-byte table + 7-byte trailer, zeros, `5A A5` at 506/507, `00 10 00 00` |
| `GetPassword` | `0x82` | 6 bytes `00 10 00 00 00 00` |

These were also reproduced through the driver: `read_profile_wired` (128 B),
`read_keymap_wired(0/1)` (504 B, 85/34 assigned, decoded per the action-code
layout) and `read_light_table_wired` (480 B — truncated by the known
`LIGHT_TABLE_SIZE` bug).

**Only one transport answers at a time.** With the USB cable attached,
wireless queries (`read_profile_wireless`) time out even though the dongle is
still enumerated. This validates the existing "prefer wired" selection in
`discovery.get_active_device()`: never poll the wireless transport while a
wired collection is present.

### Wired command table (CONFIRMED)

| cmd | name | args |
|---:|---|---|
| `0x03` | SetMatrix | `(layer, buf, len)` |
| `0x83` | GetMatrix | `(layer, buf, len)` |
| `0x04` | SetLED (128-byte profile) | `(buf, len)` |
| `0x84` | GetLED | `(buf, len)` |
| `0x05` | SetMacro | `(buf, len)` |
| `0x85` | GetMacro | `(buf, len)` |
| `0x06` | SetGame (planar RGB) | `(index, buf, len)` |
| `0x86` | GetGame | `(index, buf, len)` |
| `0x0A` | SetLedRgbTab (21 B/key) | `(buf, len)` |
| `0x8A` | GetLedRgbTab | `(buf, len)` |
| `0x0B` | SetScreenParam | `(buf, len)` |
| `0x11` | ResetDevice | — |
| `0x82` | GetPassword (6 bytes) | param `0x01`, total `1` |

**The two command spaces are not interchangeable.** Wired uses `0x03/0x83` for
matrix, wireless uses `0x01/0x41`.

## Payload layouts

### Key map (4 bytes per position) — CONFIRMED ON HARDWARE

A live `GetMatrix` read returns **504 bytes = 126 positions × 4** (36 chunks ×
14). Each record is a **32-bit action code stored big-endian**:

```
record = pack(">I", action)
action = page << 24 | value                      # pack_keyboard_action
base   = modifier_mask << 16 | hid_usage         # pack_base_key (page 0)
```

Live vectors:

| pos | key | wire bytes | decoded |
|---:|---|---|---|
| 0 | Esc | `00 00 00 29` | page 0, HID usage `0x29` |
| 1 | `` ` `` | `00 00 00 35` | usage `0x35` |
| 2 | Tab | `00 00 00 2B` | usage `0x2B` |
| 4 | LShift | `00 02 00 00` | modifier `0x02` |
| 5 | LCtrl | `00 01 00 00` | modifier `0x01` |
| 8 | Q | `00 00 00 14` | usage `0x14` |
| 11 | LWin | `00 08 00 00` | modifier `0x08` |
| 12 | F1 | `00 00 00 3A` | usage `0x3A` |
| 90 | Mute | `02 00 00 E2` | page `0x02`, consumer `0x00E2` |

Layer 1 records are byte-identical to the `KB.ini` `[FN1]` 32-bit fields:
Esc `07 00 00 04`, `` ` `` `08 07 00 00`, F1 `02 00 01 94`. Pages observed:
`0x00`, `0x02`, `0x07`, `0x08`. Layers 2 and 3 read back all zero.

An earlier static reading claimed `24-bit hwCode LE + macro-slot byte3`; the
live data disproves it. Macro binding encoding is still OPEN.

### Macro block — CONFIRMED

```
uint16 entries[n][2]   ; (offset, size), little endian
byte   data[]          ; concatenated macro blobs
```

Offsets include the `n*4` header bias, so they are absolute from block start.
Wireless sends the block in `0x200`-byte pages, `100 ms` apart.

The earlier claim that keymap byte 3 selects a macro slot is **disproved** by
the live layer read (records are big-endian 32-bit action codes). How a macro
binding is encoded in that action code is still OPEN.

### LED profile (128 bytes) — CONFIRMED carrier, partial field map

Carried by `0x04`/`0x44` (wireless) and `0x04`/`0x84` (wired). Builder
`FUN_0048e880`:

| offset | content | status |
|---:|---|---|
| `+0x03` | cfg byte when `cfg+0x2d3c != 0` | HYPOTHESIS |
| `+0x09` | `cfg+0x2f1c == profile index` (active profile) | CONFIRMED |
| `+0x0a` | `cfg+0x3032[profile*0x28]` | CONFIRMED offset |
| `+0x0b` | `cfg+0x2fee + param+0x2440` (group base / brightness) | CONFIRMED offset |
| `+0x12..0x15` | side LED mode/light/speed/color when `nFw != 0x1a` | HYPOTHESIS |
| `+0x1a` | wheel mode | HYPOTHESIS |
| `+0x32..0x35` | side LED alt layout when `nFw == 0x1a` | HYPOTHESIS |
| `+0x38/+0x39` | `0xFF, 0xFF` table marker | CONFIRMED |
| `+0x3b..` | per-group brightness/speed, 2 bytes/group | CONFIRMED |

Per-group entries: `[g*2+0x3a] = brightness`, `[g*2+0x3b] = (speed & 0x0F) |
(other << 4)`.

The established 128-byte profile layout used by `kreo_control` (mode at byte 1,
brightness byte 2, speed byte 3, direction byte 4, colour-mode byte 5,
colour bytes 6..8, custom flag byte 9, hardware effect byte 10, `FF FF` at
56/57, `5A A5` at 126/127) remains consistent with the table marker at
`+0x38/+0x39` and the `+0x3b` group table.

Live comparison of the two transports shows the payload is identical **except
byte 14**: `00` on wired, `01` on wireless. Treat byte 14 as a transport/link
flag and preserve it on read-modify-write.

### Per-key RGB table (21 bytes/key) — CONFIRMED

From `FUN_0048ec30` (G5KB) / `FUN_0048a060` (916KB):

```
entry = 7 RGB triples (7 zones per key) = 21 bytes
size  = (count + 1) * 21
if cfg+0x2ff5 (KB.ini CRC=1):
    pad to 0x200, set [0x1FE]=0x5A, [0x1FF]=0xA5
```

Records are packed with stride `0x15` by `FUN_00407a60(buf, size, 0x15, 3)`.

**Live read (2026-11-18):** `GetLedRgbTab` (`0x49`) returned 490 bytes =
**483-byte table (23 × 21) + 7-byte trailer** `03 00 00 00 01 BE 01`; the first
6 trailer bytes equal `KB.ini Psd=3,0,0,0,1,BE`. No `5A A5` and no 0x200 pad on
the wireless read path, so the CRC packing applies to the wired write path.
The driver's `LIGHT_TABLE_SIZE = 480` disagrees with 483 and is OPEN.

### Planar per-key RGB frame (378 bytes) — CONFIRMED

Three planes of 126 bytes:

```
R: [0x000 .. 0x07D]
G: [0x07E .. 0x0FB]
B: [0x0FC .. 0x179]
```

Key index = `cfg+0xc + 0x10*i`; writes are bounds-checked against
`MatrixLen`. The high nibble of the index carries the colour-group number.
Sent once per group (`GaoshouGroupNum`, default 5), `100 ms` apart. This matches
the existing `CUSTOM_FRAME_SIZE = 378` / `TOTAL_MATRIX_KEYS = 126` driver code.

**Live read (2026-11-18):** `GetGame` (`0x42`) returned exactly 378 bytes
(27 chunks × 14), confirming the 3 × 126 frame size on hardware.

## Configuration (`KB.ini` → cfg)

| INI key | cfg offset | default | meaning |
|---|---|---|---|
| `Fw` | `+0x14` | 0 | firmware / feature version |
| `MatrixLen` | `+0x2ff4` | `0x80` | positions per layer |
| `CRC` | `+0x2ff5` | 1 | append `5A A5` to the 0x200 LED table |
| `LayerMask` | `+0x2d50` | 0 | layers not writable |
| `GaoshouIndex` | `+0x2f1c` | -1 | active profile |
| `GaoshouGroupNum` | `+0x2fec` | 5 | colour groups |
| `StartGp` | `+0x2fee` | `0x20` | group base |
| `RGBIndex` | `+0x2ff8..0x2ffa` | 2,1,0 | R,G,B byte order |
| `IC2481` | `+0x2d89` | 0 | 5 s vs 2 s response timeout |
| `SleepTime` | `+0x2d94` | `0x78` | |

## Existing driver mapping

| Driver function | Wireless | Wired |
|---|---|---|
| `read_profile_*` | `0x44` | `0x84` |
| `write_profile_*` | `0x04` | `0x04` |
| `read_light_table_*` | `0x49` | `0x8A` |
| `write_light_table_*` | `0x09` | `0x0A` |
| `read_custom_light_*` | `0x42` | `0x86` |
| `write_custom_light_*` | `0x02` | `0x06` |
| `read_keymap_*` (new, read-only) | `0x41` | `0x83` |

Note the asymmetry: on the wireless transport "custom light" uses `0x02`
(SetGame) and its read `0x42`, whereas the driver currently names the constant
`WIRELESS_CMD_CUSTOM_LIGHT_WRITE = 2` — that matches. The `0x13` frame's byte 4
high nibble carries the caller's layer/group/page; `protocol.py` now exposes it
as the `flag` argument of `build_wireless_frame` / `build_wireless_packets`.

## Open items

Resolved on 2026-11-18 by read-only probing of both attached units
(`3554:FA09` wireless and `258A:010C` wired):

- ~~Which PID binds to which transport.~~ `3554:FA09` = `0xFF02/2`, in/out 20,
  feature 0 ⇒ interrupt `0x13`. `258A:010C` = `0xFF00/1`, feature 520 ⇒ HID
  Feature transport. Both confirmed live.
- ~~Real HID feature descriptor length / accepted report ID.~~ 520 bytes and
  report ID `0x06` (verified accepted; `0x09` rejected).
- ~~Matrix payload is 128 positions.~~ Live read = 504 bytes = 126 positions.
- ~~Planar frame size.~~ Live read = 378 bytes.
- ~~Profile layout.~~ Live read = 128 bytes, `FF FF` at 56/57, `5A A5` at
  126/127. Only byte 14 differs between transports (`00` wired, `01` wireless).
- ~~Byte-4 high-nibble semantics.~~ Caller-supplied layer/group/page nibble.
- ~~Read length field.~~ Must advertise the requested byte count; `0` yields a
  header-only ACK.

Still open:

1. Macro binding encoding inside the 32-bit keymap action code.
2. Safe-write rules for the 13 unpopulated matrix positions and `LayerMask`.
3. Reconcile `LIGHT_TABLE_SIZE = 480` with the observed 483-byte table plus
   7-byte `Psd` trailer (the vendor's read constant is `0x01E3` = 483).
4. Semantics of the 7th trailer byte (`0x01`) and of `GetPassword`
   `00 10 00 00 00 00`.
5. Whether byte 14 of the LED profile is a transport flag or a user setting.

## DANGEROUS / not documented

The UI and `Cfg.ini` contain firmware-update references. No update command,
payload, or execution path is documented or implemented here. Do not implement
OTA/ISP flashing.
