# Kreo Control — next 5 features, ranked by value / risk

Evidence base: `FINDINGS.md`, `protocol_spec.md`, `device_probe_2026-11-18.txt`.
No write command has been exercised on hardware yet; every "write" item below
needs one authorized capture before it can be called CONFIRMED.

| # | Feature | Value | Risk | Status |
|---:|---|---|---|---|
| 1 | Keymap read + remap (layers 0–3) | Highest: core remapping | Low (read) / Medium (write) | Read DONE and live-validated; write not started |
| 2 | Light-table truncation fix (480 → 483 + trailer) | High: corrects a live bug | Low (read) / Medium (write) | Read path diagnosed; fix pending |
| 3 | Effect profile write parity | High: all lighting modes | Medium | Field map partial |
| 4 | Macro write | High: headline feature | High | Block known, binding unknown |
| 5 | Device status / settings surface | Medium | Low (0x82 read) / Unknown (0x0B write) | 0x82 verified read-only |

## 1. Keymap read + remap — highest value, safest increment

**Read side is done** (this session):

- `protocol.read_keymap_wired(transport, layer)` → `0x83`
- `protocol.read_keymap_wireless(transport, layer)` → `0x41`
- `protocol.decode_keymap_record()` / `decode_keymap_layer()` →
  `KeyAction(position, page, value, kind)` with `hid_usage` / `modifier_mask`
  helpers.

Live-validated on `258A:010C`: layer 0 = 85 assigned, layer 1 = 34 assigned,
FN1 pos 12 = page `0x02` value `0x0194` (identical to `KB.ini`).

**Write side** (`0x03` wired / `0x01` wireless, payload
`build_keymap_layer(...)` = 504 bytes big-endian) needs:

1. A capture/verification of one vendor remap, to confirm the layer goes in the
   frame's `param` byte (wireless: byte-4 high nibble) and not in the payload.
2. A rule for the 13 unpopulated matrix positions (`KB.ini` dense 0..95 has
   gaps): preserve the read-back record instead of writing 0.
3. `LayerMask` check (cfg+0x2d50) so firmware-protected layers are skipped.

**Mitigation:** read-back and diff after each single-key write; keep a
pre-write layer dump so the operation is reversible.

## 2. Light-table truncation — real bug in the current driver

Live device returns **483 bytes (23 × 21) + 7-byte `Psd` trailer**, and the
vendor's own read constant requests 483 (`e3 01`). The driver still uses
`LIGHT_TABLE_SIZE = 480`, and `probe_driver_paths.py` shows
`read_light_table_wired()` returning only 480 of the live 512-byte reply.

Planned sequence:

1. Read-side fix only (low risk): return 483 or the full 512-byte buffer and
   parse with the new `split_rgb_table()`. No write is involved.
2. Then one authorized table write, captured and read back, to settle:
   - is the 7-byte trailer required in the write payload?
   - why does the stored buffer show `5A A5` at 506/507 while the static
     builder (`FUN_0048ec30`) puts it at `0x1FE/0x1FF` (510/511)?
   - what are the trailing `00 10 00 00` bytes?

Do not change the write path before those three questions are answered.

## 3. Effect profile write parity

The 128-byte profile carrier is confirmed on both transports
(`0x04`, `FF FF` at 56/57, `5A A5` at 126/127). Byte 14 differs by transport
(`00` wired / `01` wireless) and must be preserved, not hardcoded.

Remaining field work is HYPOTHESIS and needs one capture per group:

- `+0x03` (`cfg+0x2d3c != 0`)
- `+0x12..0x15` side-LED mode/light/speed/colour (`nFw != 0x1a`)
- `+0x32..0x35` side-LED alt layout (`nFw == 0x1a`)
- `+0x1a` wheel mode

**Mitigation:** read-modify-write only, never a whole-blob write built from
defaults.

## 4. Macro write — highest risk, do last

Known: block format `(offset, size)` LE16 header + concatenated blobs
(`build_macro_block`), wired cmd `0x05`, wireless `0x03` in `0x200` pages with
100 ms gaps.

Blocked: **how a macro binding is encoded in the 32-bit keymap action code.**
The old "byte 3 = macro id − 1" theory is disproved by the live layer read.
Without that, a macro can be stored but never triggered.

Preconditions: #1 shipped, plus a capture of the vendor saving and binding one
macro. Do not ship a write path that leaves an unreachable macro blob.

## 5. Device status / settings surface

Cheap, low-risk reads already proven:

- `GetPassword 0x82` → 6 bytes `00 10 00 00 00 00` (read-only probe). Meaning
  unknown; do not display as a value without interpretation.
- `GetOnBoard 0x4A` (wireless) / `0x0A` set — onboard-profile slot, not probed.
- `SetScreenParam 0x0B` — write only, semantics unknown; skip until captured.

Suggested first step: expose a read-only "device info" panel (transport,
report ID, firmware `nFw`, matrix positions, table size) so users can verify
which mode the driver picked. This is pure information and carries no write
risk.

## Explicitly out of scope

- Firmware update / OTA / ISP: DANGEROUS, not documented as an implementation.
- 916KB-only commands (`0xBC/0xC0` SetLedMatrix, `0xDC/0xE0/0xE4/0xE8` macro
  slots): different product.
