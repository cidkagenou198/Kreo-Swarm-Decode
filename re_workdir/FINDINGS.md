# KreoSWARM75 reverse-engineering findings

## Status
- Inventory started; static analysis only. No vendor binary or firmware was modified.

## Architecture

### Confirmed

- Shortcut: `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\KreoSWARM75\KreoSWARM75.lnk`
  resolves to `C:\Program Files (x86)\KreoSWARM75\OemDrv.exe` with no arguments.
- `OemDrv.exe` is a 32-bit x86 PE, 2,640,896 bytes, SHA-256
  `ab0a2492c3538c247d4e6dfde1613cad5df78852490a41880a31fe47558b7117`.
  REA Evidence: `ev_172a175502bf44c5c1b3f280ef66341ee30d73ee81d6b9eb2d4e588c1faa551f`.
- REA managed-artifact inspection reports PE machine `0x014c`, PE32, five sections,
  and no CLI data directory (`cli-directory-absent`), so this is not a .NET/CIL
  executable. Evidence above.
- The install tree contains native-style resources and configuration:
  `Cfg.ini`, `Dev\kb\KB.ini`, `Dev\kb\{Cartoon,ET}\*.txt`, `Text\{en,sc}\text.xml`,
  `skins\*.png`, `InitSetup.dll`, and `uninstall.dll`. No `app.asar`, JavaScript
  bundle, Electron runtime, Qt deployment tree, or Tauri resources were found in
  the recursively enumerated install tree.
- `Dev\kb\KB.ini` identifies the target and layout statically:
  `VID=0x258a`, `PID=0x010C`, wireless `VID=0x3554`, `PID=0xfa09`,
  `SleepTime=180`, `ShowDebounce=0x04000101`, `DefLedIndex=10`,
  and 82 visible keyboard entries (`K1` through `K83`, including the non-physical
  `Mute` entry). It also contains `FN1` entries and `LedOpt1` through `LedOpt20`.
- The supplied installer copy is an Inno Setup executable, SHA-256
  `8107cd3b45a6c7adac4332976ed42629d99ba157936a626015cf7287e9e2c71d`;
  all three Downloads copies have that same hash. Its compressed payload was not
  extracted because no Inno unpacker is present in this workspace. This does not
  block analysis of the installed `OemDrv.exe`.
- `InitSetup.dll` imports only `SHLWAPI.dll` and `KERNEL32.dll`; it has no HID,
  SetupAPI, firmware, OTA, or ISP string/import match. `uninstall.dll` imports
  only `MSVCR90.dll` and `KERNEL32.dll`. This makes both unlikely to be the
  main device transport component. Evidence: their PE import directories.

### Hypothesis

- The GUI is a native C/C++ Windows application, probably using a framework such
  as MFC or a vendor UI library. This is inferred from the native PE plus external
  INI/XML/bitmap resources; the exact framework remains to be confirmed from
  imports and RTTI.

### Not yet established

- Exact HID backend and all command-building functions.
- Whether `InitSetup.dll` participates in device I/O or is installer-only.

## Transport and session

### Confirmed

- `OemDrv.exe` imports `SetupDiGetClassDevsW`, `SetupDiEnumDeviceInterfaces`,
  `SetupDiGetDeviceInterfaceDetailW`, `CreateFileW`, `ReadFile`, `WriteFile`,
  `HidD_GetHidGuid`, `HidD_GetAttributes`, `HidD_GetPreparsedData`,
  `HidP_GetCaps`, `HidD_SetFeature`, and `HidD_GetFeature`. The import address
  table (IAT) contains `HidD_SetFeature` at VA `0x005D11FC`,
  `HidD_GetFeature` at `0x005D1200`, `WriteFile` at `0x005D1220`, and
  `ReadFile` at `0x005D1238`. Source: `OemDrv.exe`, PE import directory,
  file offset `0x236EA2` (`HID.DLL`) and IAT thunk region file offset `0x1B9D16`.
- Direct calls to `ReadFile` and `WriteFile` occur in the device-code region.
  In particular, code at RVA `0x87D4B` initializes a 20-byte read buffer with
  `0x13` at stack-buffer offset `+8`, then calls `ReadFile` via IAT
  `0x005D1238` with byte count `0x14` (20). This confirms the native app uses
  Win32 overlapped/file-handle I/O for at least its RF report path.
  Evidence: `OemDrv.exe` file offset `0x8714B`, bytes
  `6A 14 ... C6 44 24 30 13 FF 15 38 12 5D 00`.
- Code at RVA `0x87348` constructs a buffer with byte zero `0x13`, calculates
  a sum over 20-byte groups, and calls internal helpers. It is consistent with
  the supplied wireless framing/checksum description, but static analysis has
  not yet resolved all argument meanings. Evidence: `OemDrv.exe` file offset
  `0x86748`; the header store is `C6 44 24 30 13`; the loop advances by four
  (`83 C1 04`) up to `0x14` (`83 F9 14`).

### Correction: two transports, feature reports ARE used

An earlier revision of this document claimed `HidD_SetFeature`/`HidD_GetFeature`
had no callers. **That is false.** Direct calls exist in `FUN_0048c880`
(`CDevG5KB::GetMatrix`):

```
0048c9d2  CALL 0x005ba914      ; HidD_SetFeature
0048ca07  CALL 0x005ba91a      ; HidD_GetFeature
```

The vendor application therefore uses two distinct transports:

| Transport | Win32 API | Report | Used by |
|---|---|---|---|
| Interrupt OUT/IN | `WriteFile`/`ReadFile` | 20-byte report, ID `0x13` | `CDev3632` family (wireless dongle) |
| HID Feature | `HidD_SetFeature`/`HidD_GetFeature` | 520-byte frame, report ID `0x06` | `CDevG5KB` family (wired) |

Both transports were verified on hardware on 2026-11-18:

- `3554:FA09` exposes `0xFF02/2` with in=20/out=20/feature=0 ⇒ the `0x13`
  interrupt path answered all `Get*` queries.
- `258A:010C` exposes `0xFF00/1` with `FeatureReportByteLength = 520`; report
  ID `0x06` is accepted and `0x09` is rejected.

### Hypothesis

- The app discovers HID interfaces with SetupAPI, opens the selected interface
  with `CreateFileW`, and uses `ReadFile`/`WriteFile` for the dongle and
  `HidD_*Feature` for the wired device.

### Not yet established

- `CreateFileW` access flags, handshake/unlock sequence, and exact timing.

## Class structure and vtables

### Confirmed

Ghidra had no vtable symbols; the tables were located by scanning `.rdata` for
method pointers.

**`CDev3632` vtable base `0x0060F4B4`** (RTTI pointer at `0x60F4B0`)

| slot | target | meaning |
|---|---|---|
| +0x00 | `FUN_00486fd0` | destructor path |
| +0x04 | `FUN_00487200` | `FindHIDDevice` / open |
| +0x18 | `FUN_004871c0` | on-device-opened |
| +0x1c | `FUN_0048bb40` | **constructs `CDevG5KB` object (model `0x916`)** |
| +0x2c | `FUN_00487c60` | `Online` (cmd `0x07`) |
| +0x34 | `FUN_004883b0` | `ApplySetting` (delegates to `FUN_0048ec30`) |
| +0x4c | `FUN_00487be0` | `SetScreenParam` (cmd `0x0B`) |
| +0x50 | `FUN_00487880` | `SetMatrix` (cmd `0x01`) |
| +0x54 | `FUN_004878c0` | `GetMatrix` (cmd `0x41`) |
| +0x58 | `FUN_00487990` | `SetMacro` (cmd `0x03`) |
| +0x5c | `FUN_004879d0` | `GetMacro` (cmd `0x43`) |
| +0x60 | `FUN_004879f0` | `SetLED` (cmd `0x04`) |
| +0x64 | `FUN_00487a40` | `GetLED` (cmd `0x44`) |
| +0x68 | `FUN_00487b20` | `SetGame` (cmd `0x02`) |
| +0x6c | `FUN_00487b60` | `GetGame` (cmd `0x42`) |
| +0x70 | `FUN_00487b80` | `SetLedRgbTab` (cmd `0x09`) |
| +0x74 | `FUN_00487bc0` | `GetLedRgbTab` (cmd `0x49`) |
| +0x78 | `FUN_00487a70` | `SetOnBoard` (cmd `0x0A`) |
| +0x7c | `FUN_00487ac0` | `GetOnBoard` (cmd `0x4A`) |
| +0x80 | `FUN_00487c20` | `ResetDevice` (cmd `0x06`) |
| +0x88 | `FUN_00486b90` | enter/leave critical section |
| +0x8c | `FUN_00486bb0` | error check (non-zero aborts) |

Evidence: `dumpvt.py` scan of `.rdata`; `out_decomp_wrappers.txt`;
`out_decomp_3632apply.txt`.

**`CDevG5KB` vtable base `0x0061186C`** (RTTI `0x61DE78` at `0x611868`), same
slot numbering, overrides:

| slot | target | meaning |
|---|---|---|
| +0x04 | `FUN_0048c250` | `FindHIDDevice` (model `0x916`) |
| +0x0c | `FUN_0048c160` | create worker thread/events |
| +0x10 | `FUN_0048c1f0` | tear down thread/events |
| +0x18 | `FUN_00490110` | close handle |
| +0x24 | `FUN_0048c5a0` | `GetVersionNumber` (logs `FW Version=0x%x`) |
| +0x2c | `FUN_00486b20` | **stub returning 1** ⇒ wired device always "online" |
| +0x34 | `FUN_0048ec30` | `ApplySetting` |
| +0x4c | `FUN_0048d620` | `SetScreenParam` (cmd `0x0B`) |
| +0x50 | `FUN_0048c840` | `SetMatrix` (cmd `0x03`) |
| +0x54 | `FUN_0048c880` | `GetMatrix` (cmd `0x83`) |
| +0x58 | `FUN_0048ca90` | `SetMacro` (cmd `0x05`) |
| +0x5c | `FUN_0048cae0` | `GetMacro` (cmd `0x85`) |
| +0x60 | `FUN_0048cce0` | `SetLED` (cmd `0x04`) |
| +0x64 | `FUN_0048cd30` | `GetLED` (cmd `0x84`) |
| +0x68 | `FUN_0048cf30` | `SetGame` (cmd `0x06`) |
| +0x6c | `FUN_0048cf90` | `GetGame` (cmd `0x86`) |
| +0x70 | `FUN_0048d380` | `SetLedRgbTab` (cmd `0x0A`) |
| +0x74 | `FUN_0048d3d0` | `GetLedRgbTab` (cmd `0x8A`) |
| +0x78/+0x7c | `FUN_00486b00` | `SetOnBoard`/`GetOnBoard` **stubbed** |
| +0x80 | `FUN_0048d5d0` | `ResetDevice` (cmd `0x11`) |
| +0x8c | `FUN_0048be30` | |
| +0x90 | `FUN_0048d890` | `keyinfo_to_hardware_code` (keymap encoder) |
| +0x94 | `FUN_0048d860` | macro serialize wrapper |

Constructor `FUN_0048bb40` sets `vftable = CDevG5KB::vftable` and
`model = 0x916`. Constructor is only reachable through `CDev3632` slot `+0x1c`
(no direct `CALL`), so `CDev3632` is the outer/primary class and constructs
`CDevG5KB` as the wired sub-device.

## Command tables

### CDev3632 (0x13 / 20-byte interrupt transport)

Argument semantics proven by disassembly of `FUN_00487260` / `FUN_0048c840`:
`AccessData(cmd, byte4_hi_nibble, buf, len, retry_log, delay)`.

| cmd | function | virtual | args |
|---|---|---|---|
| `0x01` | `FUN_00487880` SetMatrix | +0x50 | `(layer, buf, len)`; nibble = layer |
| `0x41` | `FUN_004878c0` GetMatrix | +0x54 | `(layer, buf, len)` |
| `0x02` | `FUN_00487b20` SetGame | +0x68 | `(index, buf, len)`; nibble = index |
| `0x42` | `FUN_00487b60` GetGame | +0x6c | `(index, buf, len)` |
| `0x03` | `FUN_004878f0` WriteMacroData / `FUN_00487990` SetMacro | +0x58 | pages of `0x200`, nibble = page index, `Sleep(100)` between pages |
| `0x43` | `FUN_004879d0` GetMacro | +0x5c | `(0, buf, len)` |
| `0x04` | `FUN_004879f0` SetLED | +0x60 | 128-byte LED profile |
| `0x44` | `FUN_00487a40` GetLED | +0x64 | `(0, buf, 0x80)` |
| `0x09` | `FUN_00487b80` SetLedRgbTab | +0x70 | 21-byte/key table |
| `0x49` | `FUN_00487bc0` GetLedRgbTab | +0x74 | `(0, buf, len)` |
| `0x0A` | `FUN_00487a70` SetOnBoard | +0x78 | `(0, &byte, 1)` |
| `0x4A` | `FUN_00487ac0` GetOnBoard | +0x7c | `(0, buf, 1)` |
| `0x0B` | `FUN_00487be0` SetScreenParam | +0x4c | `(0, buf, len)` |
| `0x06` | `FUN_00487c20` ResetDevice | +0x80 | `(0, &byte, 1)`; **no ACK read** |
| `0x07` | `FUN_00487c60` Online | +0x2c | result to `this+0x238`, `-1` on failure |

ACK rule confirmed in `FUN_00487260`: `if (cmd & 0x80 || cmd == 6) skip ACK`.

Response frame (`FUN_00487fa0` / `FUN_004875c0`): byte0 report `0x13`,
byte1 `cmd|0x80` (bit7 = CRC error), byte2 total chunks `& 0x7F`, byte3 chunk
index, byte4 low nibble = payload length (≤`0x0E`), bytes 5.. data,
byte 19 checksum = sum of all 20 bytes.

### CDevG5KB (HID Feature transport)

Helper `FUN_0048c600` (write) builds a **0x208 (520)-byte** buffer that is always
sent whole:

```
off 0     report ID          = 0x09 if nFw != 0x18, else 0x06
off 1     command
off 2     parameter          (layer / index, else 0)
off 3     0
off 4     total chunk count
off 5     chunk index
off 6..7  payload length, LE16
off 8..   payload (max 512 bytes)
```

The report-ID expression is `(((nFw != 0x18) - 1) & 0xFD) + 9` ⇒ `0x09` for
`nFw != 0x18`, `0x06` for `nFw == 0x18`. `KB.ini` has `Fw=24` (`0x18`), so this
unit uses report ID **`0x06`**.

**Live confirmation (2026-11-18):** on `258A:010C` the `0xFF00/1` control
collection reports `FeatureReportByteLength = 520`, report ID `0x06` is accepted
(`SetFeature` 520 bytes, `GetFeature` returns data) and `0x09` is rejected
(`SetFeature` -1 / `GetFeature` read error). So both the frame size `0x208` and
report ID `0x06` are confirmed, not just predicted.

Per chunk: `Sleep(0x14)` → `HidD_SetFeature(h, buf, 0x208)`; up to 3 attempts
with `0x46` ms between failures; then `Sleep(0x14)` → `HidD_GetFeature` for
read-after-write operations. Response payload is copied from `buf[8..]`.

For **read** commands the vendor still fills bytes 6..7 with the requested byte
count (`_Size = min(0x200, length)`), with an empty payload. Sending `len=0`
returns only an 8-byte header. Live example: `06 84 00 00 01 00 80 00` →
`06 84 00 00 01 00 80 00` + 128 bytes.

| cmd | method | args |
|---|---|---|
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
| `0x82` | GetPassword (6 bytes) | param byte2 = 1, total = 1 |

**Command numbering differs from `CDev3632`** — do not reuse `0x01`/`0x41` on
the feature transport. Evidence: `out_decomp_g5kb.txt`, `out_decomp_g5kb2.txt`.

## Payload layouts

### Key map (`SetMatrix`): 4 bytes per position — CORRECTED BY LIVE READ

A live `GetMatrix` (cmd `0x41`) read on 2026-11-18 returned **504 bytes =
126 positions × 4**, and the bytes are a **32-bit action code stored
big-endian** (page byte first). This overrides the earlier static-pass reading
of "24-bit `hwCode` little-endian + macro-slot byte"; byte 3 is not a macro id.

```
record = pack(">I", action)
action = page << 24 | value            (pack_keyboard_action)
base   = 0x00 << 24 | modifier << 16 | hid_usage   (pack_base_key)
```

Live vectors (see `device_probe_2026-11-18.txt`):

| position | key | wire bytes | action |
|---:|---|---|---|
| 0 | Esc | `00 00 00 29` | page 0, HID usage `0x29` |
| 1 | `` ` `` | `00 00 00 35` | usage `0x35` |
| 2 | Tab | `00 00 00 2B` | usage `0x2B` |
| 4 | LShift | `00 02 00 00` | modifier mask `0x02` |
| 5 | LCtrl | `00 01 00 00` | modifier mask `0x01` |
| 8 | Q | `00 00 00 14` | usage `0x14` |
| 11 | LWin | `00 08 00 00` | modifier mask `0x08` |
| 12 | F1 | `00 00 00 3A` | usage `0x3A` |
| 90 | Mute | `02 00 00 E2` | page `0x02`, consumer `0x00E2` |

Layer 1 (FN1) records are **byte-identical to the `KB.ini` `[FN1]` 32-bit
fields**: Esc `07 00 00 04` (`0x07000004`), `` ` `` `08 07 00 00`
(`0x08070000`), F1 `02 00 01 94` (`0x02000194`), F2 `02 00 02 23`,
F3 `02 00 01 92`. Pages seen: `0x00`, `0x02`, `0x07`, `0x08`. Layers 2 and 3
read back all zero.

Layer sizes: 36 chunks × 14 = 504 bytes per layer, all chunks full length.
`MatrixLen` in `KB.ini` is absent, and the device reports 126 positions — this
matches `TOTAL_MATRIX_KEYS = 126`, not the 128 implied by the `cfg+0x2ff4`
default `0x80`.


### Macro block (`SetMacro`)

```
uint16 entries[n][2]   ; (offset, size) pairs, little endian
byte   data[]          ; concatenated macro blobs
```

Offsets are pre-biased by the `n*4` header size, so they are absolute from the
block start. `CDev3632` sends the block via `WriteMacroData` in `0x200`-byte
pages with `100` ms sleeps.

Note: the earlier claim that keymap byte 3 selects a macro slot is **wrong**
(disproved by the live layer read). How a macro binding is encoded in the
32-bit action code is still OPEN.

### LED profile (`SetLED`/`GetLED`): 128 bytes

Carried by `0x04`/`0x44` (3632) and `0x04`/`0x84` (G5KB); built by
`FUN_0048e880`. Observed fields:

```
+0x03  cfg byte at param_2+0x3340 when cfg+0x2d3c != 0
+0x09  bool: cfg+0x2f1c == profile byte (active profile match)
+0x0a  cfg+0x3032[profile*0x28]
+0x0b  cfg+0x2fee + param+0x2440
+0x12..0x15 side LED (mode/light/speed/color) when nFw != 0x1a
+0x16  cfg+0x3338 low byte
+0x17  cfg+0x3342 == 0
+0x18  cfg+0x2dfc[param+0x333e*4] low byte
+0x1a  wheel mode
+0x32..0x35 side LED alt layout when nFw == 0x1a
+0x38/0x39 = 0xFF,0xFF
+0x3b.. per-group table, 2 bytes/group (stride 0x24 in the settings array):
       [g*2+0x3a] = brightness (cfg+0x2e70[...])
       [g*2+0x3b] = (speed & 0x0F) | (cfg+0x2e50[...] << 4)
```

**Live confirmation (2026-11-18):** `GetLED` (cmd `0x44`) returned 10 chunks
with the last chunk length `2` ⇒ exactly 128 bytes, `FF FF` at offsets 56/57,
a 2-byte group table from 58 (`04 37` = brightness 4, upper nibble 3,
`07 47`, `07 44`, ...), and `5A A5` at 126/127. See
`device_probe_2026-11-18.txt`.

### Per-key RGB table (`SetLedRgbTab`): 21 bytes per entry

From `FUN_0048ec30` (G5KB) / `FUN_0048a060` (916KB):

```
for each entry g: 7 RGB triples = 21 bytes (7 zones/key)
  entry[0..2]   = colour #1
  ...
  entry[18..20] = colour #7
size = (count + 1) * 21
if cfg+0x2ff5 (INI CRC=1): pad to 0x200, set [0x1FE]=0x5A, [0x1FF]=0xA5
```

`FUN_00407a60(buf, size, 0x15, 3)` sorts/packs records with stride `0x15`.

**Live confirmation (2026-11-18):** `GetLedRgbTab` (cmd `0x49`) returned
490 bytes = **483-byte table (23 entries × 21)** + a **7-byte trailer**
`03 00 00 00 01 BE 01`. The first 6 trailer bytes equal `KB.ini`
`Psd=3,0,0,0,1,BE`. Entries are 7-colour palettes
(`ff0000 00ff00 0000ff ffff00 ff00ff 00ffff ffffff`). There is **no `5A A5`**
and no 0x200 padding on the wireless read path, so the CRC padding is specific
to the wired feature write path. The driver's `LIGHT_TABLE_SIZE = 480` does not
match the observed 483 and must be reconciled before any table write.


### Planar per-key RGB frame (`SetGame`): 378 bytes = 3 × 126

`FUN_0048ec30` builds three planes of `0x7E` (126) bytes:

```
plane R: buf[0x00 .. 0x7D]
plane G: buf[0x7E .. 0xFB]
plane B: buf[0xFC .. 0x179]
```

Per-key index = `cfg+0xc + 0x10*i`, written only when `index < MatrixLen`.
Top nibble = group index. Sent once per colour group (`cfg+0x2fec`, default 5)
with `Sleep(100)` between groups.

**Live confirmation (2026-11-18):** `GetGame` (cmd `0x42`) returned exactly
**378 bytes = 27 chunks × 14**, all zero (no per-key custom colours stored at
the time of the probe). This confirms the 3 × 126 planar frame size on
hardware and the driver's `CUSTOM_FRAME_SIZE`.

### 916KB-only commands (unresolved, different product)

`FUN_0048a060` calls `FUN_00488d80(0xBC)` / `FUN_00488d80(0xC0)`
("SetLedMatrix(0x%X)", 0x200-byte frame) and `FUN_004891d0(macroId)`
("SetMacroData(%x)", ids `0xDC/0xE0/0xE4/0xE8`, 0x400 bytes). Also
`FUN_00488e40` "SetKeyMatrix", `FUN_00488bf0` "SetProfile",
`FUN_00488c90` "Cfg(Load-Global)/Cfg(Load-Pro1)". Out of scope for the Swarm 75
(G5KB) spec.

## INI → cfg configuration map (from `FUN_00410b90`)

cfg block = `0x34D0` bytes at `*(this+0x20)`.

| INI key | cfg offset | default | meaning |
|---|---|---|---|
| `Fw` | +0x14 | 0 | firmware/feature version (24 = `0x18`) |
| `MatrixLen` | +0x2ff4 | `0x80` | positions per layer |
| `CRC` | +0x2ff5 | 1 | append `5A A5` to the 0x200 LED table |
| `LayerMask` | +0x2d50 | 0 | layers not writable |
| `DefLedIndex` | +0x2f1b | 0 | default effect |
| `LedMask` | +0x2d40 | 0 | effect bitmask |
| `ChannelMask` | +0x2d48 | 0 | |
| `GaoshouIndex` | +0x2f1c | -1 | active profile |
| `GaoshouGroupNum` | +0x2fec | 5 | colour groups |
| `StartGp` | +0x2fee | `0x20` | group base |
| `RGBIndex` | +0x2ff8..+0x2ffa | 2,1,0 | R,G,B byte order |
| `GameRGBIndex` | +0x2ffb..+0x2ffd | 2,1,0 | |
| `IC2481` | +0x2d89 | 0 | 5 s vs 2 s response timeout |
| `SleepTime` | +0x2d94 | `0x78` | |

Relevant `KB.ini`: `Fw=24`, `MatrixLen` absent (→128), `CRC=1`,
`GaoshouGroupNum=1`, `GaoshouIndex=18`, `Psd=3,0,0,0,1,BE`,
`VID=0x258a PID=0x010C`, `VID_Wireless=0x3554 PID_Wireless=0xfa09`.
`Psd` is 6 bytes parsed by `FUN_004611f0` and compared at device open
(`Psd unmatch: ...`).

## Device enumeration

`CDevG5KB::FindHIDDevice` (`FUN_0048c250`) walks a table starting at
`0x0064B918`, stride `0x22C`, guard `> 0x6525AF`. Each entry holds a wide device
path at `entry-0x86` (0x208 bytes), `Psd` bytes at `entry-0x04..-0x01`, then
`[0]=usagePage [1]=usage [2]=VID [3]=PID` and flags near `+0x228`.

Match logic (re-read with the live caps as ground truth):

- `nFw == 0x18`:
  - wired: `usagePage=0xFF00`, `usage=1`, `entry[-1] == 0x208` (report buffer)
  - wireless: `usagePage=0xFF02`, `usage=2`, `entry[-3] == 0x14` (input len),
    `entry[-2] == 0x14` (output len), `entry[-4] == 0x13` (report ID)
  - consumer: `usagePage=0x000C`, `usage=1`, `entry[-3] == 3` (input len)
- `nFw == 0x1a`: wireless/feature variant (`0xFF02/2`, `entry[-1]==0x208`,
  `entry[-3]==8`); the decompiled branch is incomplete, do not rely on it.

**Verified on hardware (2026-11-18):** the attached `3554:FA09` dongle exposes
`0xFF02/2` with **in=20, out=20, feature=0**, i.e. the interrupt `0x13`
transport, and also a separate `0xFF04/2` collection with an 8-byte feature
report (dongle-side control, not the keyboard protocol). Therefore the
`0x208` feature transport belongs to the **wired** `258A:010C` device. On
success `this+0x0c = hFile`, the table entry's `+0x228` flag is set, and
`Sleep(30)` precedes the version query.

The table is in BSS and filled at runtime from `KB.ini`, so **no raw VID/PID
literals exist in the binary** (verified: the byte pair `8a 25 0c 01` does not
occur).

## Live device verification (2026-11-18)

Read-only `Get*` probes only; no `Set*` command was ever sent. Raw frames are in
`device_probe_2026-11-18.txt`.

### Wireless `3554:FA09` ("2.4G Wireless Receiver") — CONFIRMED

| Collection | In | Out | Feature | Meaning |
|---|---:|---:|---:|---|
| `0xFF02 / 0x02` | 20 | 20 | 0 | keyboard control ⇒ interrupt `0x13` |
| `0xFF04 / 0x02` | 0 | 0 | 8 | dongle-side control, not keyboard protocol |

`GetLED` 128 B (`FF FF` at 56/57, `5A A5` at 126/127), `GetMatrix` 504 B
(126 × 4), `GetGame` 378 B (3 × 126), `GetLedRgbTab` 483 B table + 7-byte
`Psd` trailer.

### Wired `258A:010C` ("Kreo Swarm", BY Tech) — CONFIRMED

| Collection | In | Out | Feature | Meaning |
|---|---:|---:|---:|---|
| `0xFF00/1` Col03 | 4 | 0 | 0 | keyboard input |
| `0xFF00/1` Col05 | 0 | 0 | 6 | 6-byte feature (password) |
| `0xFF00/1` Col06 | 8 | 0 | **520** | main control/feature collection |

- `FeatureReportByteLength = 520` — the `0x208` frame size is the descriptor's
  real maximum, not merely the app's buffer.
- Report ID `0x06` accepted (`SetFeature` 520 B, `GetFeature` returns data);
  `0x09` rejected (`SetFeature` -1, `GetFeature` read error). Matches the
  `nFw == 0x18` branch.
- **Read requests must carry the requested byte count in bytes 6..7.** With
  `len=0` the device replies with an 8-byte header only. `06 84 00 00 01 00 80
  00` ⇒ header + 128 payload bytes.
- `GetMatrix` `0x83` returns 504 B and is **byte-identical to the wireless
  read** (layer 0: 85 nonzero, layer 1: 34 nonzero) — the big-endian 32-bit
  action-code format holds on both transports.
- `GetGame` `0x86` returns 378 B.
- `GetLedRgbTab` `0x8A` (512 requested) returns the same 483-byte table and
  7-byte `Psd` trailer, then 16 zero bytes, `5A A5` at 506/507 and
  `00 10 00 00` at 508..511 — i.e. the `CRC=1` 0x200 padding is present on the
  wired path.
- `GetPassword` `0x82` returns 6 bytes `00 10 00 00 00 00`.

### Wired vs wireless `GetLED` payload: one byte differs

The 128-byte profile is identical on both transports **except byte 14**, which
is `00` when wired and `01` when wireless. Every other byte, including `FF FF`
at 56/57 and `5A A5` at 126/127, matches. Byte 14 is therefore most likely a
link/transport (or dongle-attached) flag rather than a user setting; it should
be preserved on read-modify-write instead of hardcoded.

### `LIGHT_TABLE_SIZE = 480` is inconsistent with the device

Both transports return a 483-byte table (23 × 21) followed by a 7-byte
trailer whose first 6 bytes equal `KB.ini Psd=3,0,0,0,1,BE`. The vendor's own
read constant requests `0x01E3` = **483** bytes. `LIGHT_TABLE_SIZE = 480` in
the driver is therefore 3 bytes short and must be corrected (and the trailer
appended) before any table write.

Confirmed in the driver itself: `read_light_table_wired()` returns only 480
bytes from the live 512-byte device reply, so the last palette's final 3 bytes
are dropped. `protocol.split_rgb_table()` now parses the correct 483 + trailer
form, but the IO functions still use `LIGHT_TABLE_SIZE`.

### Driver read paths validated live (wired, 2026-11-18)

`re_workdir/probe_driver_paths.py` drives the real `kreo_control` code
(read-only). On `258A:010C`:

- `read_profile_wired()` → 128 bytes, tail `5A A5`.
- `read_keymap_wired(0)` → 504 bytes, 85 assigned; `read_keymap_wired(1)` →
  504 bytes, 34 assigned. `decode_keymap_layer()` maps pos 0/1/2/3 to keyboard
  usages `0x29/0x35/0x2B/0x39`, pos 4/5 to modifiers `0x02/0x01`, FN1 pos 0 to
  page `0x07` value `4` and pos 12 to page `0x02` value `0x0194`.
- `read_light_table_wired()` → 480 bytes (truncated, see above).

**Only one transport answers at a time.** With the USB cable attached,
`read_profile_wireless()` times out waiting for the dongle, even though
`3554:FA09` is still enumerated. This confirms the driver's existing
"prefer wired" selection in `discovery.get_active_device()` is required: do not
poll the wireless transport while a wired collection is present.


## Lighting modes

### Confirmed

`Dev\kb\KB.ini` is the vendor's explicit logical-to-hardware effect table.
The seven fields are annotated in the file as `hw effect speed light direct
random color`; the first numeric field is the UI/logical mode. Therefore the
remaining fields are recorded verbatim below rather than over-interpreted.

| Logical mode | Hardware ID | Vendor UI name | `speed,light,direct,random,color` |
|---:|---:|---|---|
| 1 | 1 | Fixed_on | `0,1,0,1,1` |
| 2 | 3 | Respire | `1,1,0,1,1` |
| 3 | 2 | Rainbow | `1,1,0,0,0` |
| 4 | 19 | Flash_away | `1,1,0,1,1` |
| 5 | 15 | Raindrops | `1,1,0,1,1` |
| 6 | 13 | Rainbow_wheel | `1,1,0,1,1` |
| 7 | 20 | Ripples_shining | `1,1,0,1,1` |
| 8 | 16 | Stars_twinkle | `1,1,0,1,1` |
| 9 | 18 | Shadow_disappear | `1,1,0,1,1` |
| 10 | 5 | Retro_snake | `1,1,0,1,1` |
| 11 | 7 | Neon_stream | `1,1,0,1,1` |
| 12 | 17 | Reaction | `1,1,0,1,1` |
| 13 | 12 | Sine_wave | `1,1,0,1,1` |
| 14 | 8 | Retinue scanning | `1,1,0,1,1` |
| 15 | 28 | Rotating windmill | `1,1,0,0,0` |
| 16 | 30 | Colorful waterfall | `1,1,0,0,0` |
| 17 | 14 | Blossoming | `1,1,0,0,0` |
| 18 | 29 | Rotating storm | `1,1,0,1,1` |
| 21 | 0 | Self-define | `0,0,0,0,0` |
| 0 | 0 | OFF | `0,0,0,0,0` |

Evidence: `C:\Program Files (x86)\KreoSWARM75\Dev\kb\KB.ini`,
lines `LedOpt1`–`LedOpt20`; UI labels are `Text\en\text.xml`,
elements `tc_kb_led1`–`tc_kb_led20`.

## Keymap and layers

### Confirmed

- `KB.ini` has base layout entries `K1`–`K83`, a populated `FN1` layer, and
  empty `FN2` and `Tap` sections. The UI explicitly exposes Default, FN1,
  FN2, and Tap layers (`Text\en\text.xml`, `tc_kb5`–`tc_kb10`).
- A base key definition contains display bounds, Windows virtual-key data, and
  a final protocol-position-like value. Example: `K1`/Esc ends
  `0x02,0x1B,0x00,0`; `K2`/F1 ends `0x02,0x70,0x00,12`.
  This establishes UI metadata and an ordered key position, but does *not*
  prove the on-wire keymap record format.
- FN1 records use three values. Example: F1 is
  `0x09,0x01,0x02000194`; Esc is `0x09,0x01,0x07000004`.
  The field meanings and byte order on-device remain unresolved.

### Full base-layer table (CONFIRMED, `KB.ini` `[KEY]`)

Every `K<n>` record has the shape `x1,y1,x2,y2, type, code, 0x00, position`.
`type=0x02` with `code` equal to a Windows virtual-key code (Esc `0x1B`,
F1 `0x70`, `A` `0x41`, LShift `0xA0`, LWin `0x5B`, FN `0xFA`, Mute `0x8F`).
The trailing `position` value is a dense 0..95 index that is *not* the same as
the key number `n` (e.g. `K2`/F1 = 12, `K30`/Tab = 2, `K74`/LWin = 11,
`K76`/Space = 35, `K82`/RCtrl = 65, `K83`/Mute = 90).

Full decoded set (key, VK, position):
Esc `0x1B`/0, F1 `0x70`/12, F2 `0x71`/18, F3 `0x72`/24, F4 `0x73`/30,
F5 `0x74`/36, F6 `0x75`/42, F7 `0x76`/48, F8 `0x77`/54, F9 `0x78`/60,
F10 `0x79`/66, F11 `0x7A`/72, F12 `0x7B`/78, PrtSc `0x2C`/84,
`` ` `` `0xC0`/1, 1..0 `0x31..0x30`/7,13,19,25,31,37,43,49,55,61,
`-` `0xBD`/67, `=` `0xBB`/73, Backspace `0x08`/79, Delete `0x2E`/91,
Tab `0x09`/2, Q `0x51`/8, W `0x57`/14, E `0x45`/20, R `0x52`/26,
T `0x54`/32, Y `0x59`/38, U `0x55`/44, I `0x49`/50, O `0x4F`/56,
P `0x50`/62, `[` `0xDB`/68, `]` `0xDD`/74, `\` `0xDC`/80, PgUp `0x21`/92,
CapsLock `0x14`/3, A `0x41`/9, S `0x53`/15, D `0x44`/21, F `0x46`/27,
G `0x47`/33, H `0x48`/39, J `0x4A`/45, K `0x4B`/51, L `0x4C`/57,
`;` `0xBA`/63, `'` `0xDE`/69, Enter `0x0D`/81, PgDn `0x22`/93,
LShift `0xA0`/4, Z `0x5A`/10, X `0x58`/16, C `0x43`/22, V `0x56`/28,
B `0x42`/34, N `0x4E`/40, M `0x4D`/46, `,` `0xBC`/52, `.` `0xBE`/58,
`/` `0xBF`/64, RShift `0xA1`/82, Up `0x26`/88, End `0x23`/94,
LCtrl `0xA2`/5, LWin `0x5B`/11, LAlt `0xA4`/17, Space `0x20`/35,
RAlt `0xA5`/53, FN `0xFA`/59, Left `0x25`/83, Down `0x28`/89,
Right `0x27`/95, RCtrl `0xA3`/65, Mute `0x8F`/90.

The position field is a candidate for the firmware key-number used by the
keymap write; it must be confirmed against a capture or the builder function.
Position 0..95 is 96 slots for 82 physical keys, i.e. the firmware address space
is larger than the populated key set.

### FN1 layer encoding (CONFIRMED table, HYPOTHESIS field meaning)

FN1 rows have three fields: `0x09, 0x01, <32-bit value>`. Examples:
Esc `0x07000004`, PrtSc `0x08000000`, `` ` `` `0x08070000`,
PgDn `0x00000048`, End `0x0000004A`, Up `0x08030100`, Down `0x08030200`,
Left `0x08040200`, Right `0x08040100`, and media keys
F1 `0x02000194`, F2 `0x02000223`, F3 `0x02000192`, F10 `0x020000E2`,
F11 `0x020000EA`, F12 `0x020000E9`.

Pattern: values beginning `0x02` carry a 16-bit consumer-page usage in the low
half (`0x0194` browser, `0x0192` calculator, `0x018A` email, `0x00CD`
play/pause, `0x00B5`/`0x00B6` next/prev track, `0x00E2` mute, `0x00E9`/`0x00EA`
volume up/down). Values beginning `0x07`/`0x08` use keyboard/vendor page
encodings. This byte layout is HYPOTHESIS pending the keymap builder function.

`0x09` is therefore likely "special function" and `0x01` a subtype; the 32-bit
value is the action. Media icons shipped in `ins\fun55x55\media_*.png` match
this consumer-usage set one-to-one.

### Key-name vocabulary (CONFIRMED, `Dev\kb\Cartoon\*` / `Dev\kb\ET\*`)

The preview-animation files list physical key names in layout rows and also
carry a per-key `:r,g,b` color override syntax. They confirm the physical key
set and rows but contain no LED indices. One unnamed key `k45` appears in
`wheel_unit.txt` and `stream_h.txt`, which is not in the `KB.ini` `[KEY]` table.

## Macros and settings

### Confirmed

- The UI resource supports macro recording/editing, start/holding/end timing,
  delay, mouse X/Y movement, and three repeat modes (count, until released,
  until any key pressed). Evidence: `Text\en\text.xml`,
  `tc_macro_msg1`–`tc_macro_msg25`.
- The UI exposes firmware version, battery, sleep, reset, debounce, and polling
  rate. Evidence: `Text\en\text.xml`, `tc_msg3`, `tc_msg5`, `tc_msg49`,
  `tc_msg50`, `tc_msg54`, `tc_ms6`, and `tc_ms13`.
- `KB.ini` configures default `SleepTime=180` and exposes
  `ShowDebounce=0x04000101`.

### DANGEROUS / not analyzed

- The UI has firmware-update text and `Cfg.ini` contains update-related flags
  (`UpdateByLocal=0` and commented `UpdateDir`). Evidence:
  `Text\en\text.xml`, `tc_update1` and `tc_update6`; `Cfg.ini`.
  No update command, payload, or execution path has been decoded or exercised.

## Open questions / required capture

1. Use USBPcap/Wireshark and capture one action per trace after idle:
   set one lighting effect, remap one base-layer key, bind one macro, alter
   polling/debounce/sleep, query firmware/battery, and factory reset *only if
   you explicitly accept that risk*. Filter USB device IDs `258A:010C` or
   `3554:FA09`; retain interrupt/feature OUT and IN URBs plus timestamps.
2. For each action, capture an immediately preceding no-op/read baseline and
   compare byte ranges. This will distinguish the command byte, payload, and
   response without guessing from UI strings.
3. Do not capture or invoke firmware update. If an updater binary is later
   isolated, document it statically as DANGEROUS only.

### Specific facts still blocked on runtime evidence

Resolved on 2026-11-18 by read-only probing of the attached units
(`device_probe_2026-11-18.txt`):

- ~~Which transport each PID uses.~~ `3554:FA09` = `0xFF02/2`, in=20/out=20/
  feature=0 ⇒ interrupt `0x13`; `258A:010C` = `0xFF00/1` with feature 520 ⇒
  HID Feature transport. Both verified live.
- ~~Dongle forwards `0x13` unchanged.~~ Confirmed: requests and replies are
  20-byte `0x13` frames with byte-19 checksum.
- ~~Matrix payload length.~~ Live `GetMatrix` returns 504 bytes = 126
  positions × 4 on both transports, not 128.
- ~~Planar frame size.~~ Live `GetGame` returns exactly 378 bytes (3 × 126) on
  both transports.
- ~~Profile layout.~~ Live `GetLED` returns 128 bytes with `FF FF` at 56/57
  and `5A A5` at 126/127 on both transports; only byte 14 differs.
- ~~Wired feature descriptor length / report ID.~~ Descriptor is 520 bytes and
  report ID `0x06` is accepted, `0x09` rejected.
- ~~Read request length field.~~ Must be the requested byte count; `0` yields a
  header-only ACK.

Still open:

1. Macro binding encoding inside the 32-bit keymap action code.
2. Whether writes are safe for all layers given `LayerMask` and the
   `FP`/`matrixIndex` gaps (13 unused positions).
3. Meaning of the 7th trailer byte after `Psd` (`0x01`) and of `GetPassword`
   `00 10 00 00 00 00` — read-only observations, semantics unknown.
4. `LIGHT_TABLE_SIZE` fix: 480 → 483 plus the `Psd` trailer (see the live
   verification section).
