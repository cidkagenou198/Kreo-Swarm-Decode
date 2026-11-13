# Kreo Swarm 75 Communication Protocol Specification

**Status**: Verified with Live Hardware  
**Target Hardware**: Kreo Swarm 75 Wireless Mechanical Keyboard  
**Controller Architecture**: SinoWealth SH68F90 / BY-Tech (BYCOMBO4 / IC2481)  

---

## 1. Hardware Identification & Interfaces

The keyboard presents different USB identifiers and descriptors based on its physical connection:

| Parameter | Wired USB Mode | 2.4 GHz Wireless Dongle |
| :--- | :--- | :--- |
| **Vendor ID (VID)** | `0x258A` (SinoWealth / BY-Tech) | `0x3554` |
| **Product ID (PID)** | `0x010C` | `0xFA09` |
| **Product String** | `KreoSWARM75` | `2.4G Wireless Receiver` |
| **Configuration Interface** | Interface `0` (or `1`) | Interface `1` |
| **Usage Page** | `0xFF00` (Vendor-Defined) | `0xFF02` (Vendor-Defined) |
| **Usage** | `0x0001` | `0x0002` |

> [!NOTE]
> Standard Bluetooth Low Energy (BLE) HID descriptors do not expose vendor configuration feature reports. Protocol configuration is supported exclusively via Wired USB and the 2.4 GHz RF Dongle.

---

## 2. Transport Mechanisms

### A. Wired USB Transport (`send_feature_report` / `get_feature_report`)
* **Write Transport**: `send_feature_report`
  * **Report ID**: `0x05`
  * **Buffer Length**: Fixed **520 bytes** (`0x0208`).
  * **Format**: `[0x05, Command (1-7 B), Payload (N B), 0x00 ... (zero-padded to 520 B)]`
* **Read Transport**: `get_feature_report`
  * **Report ID**: `0x06`
  * **Response Format**: `[0x06, Status/Header (8 B), Payload Data (N B)]`

### B. 2.4 GHz Wireless Dongle Transport (`write` / `read`)
* **Packet Size**: Fixed **19 bytes** (`0x13`).
* **Chunk Payload Size**: **14 bytes** per packet.
* **Checksum Algorithm**:
  $$\text{Checksum} = (0\text{x}13 + \sum_{i=1}^{18} \text{Byte}_i) \pmod{256}$$

#### Wireless Query Frame:
```
[0x13, Command_ID, 0x00, 0x00, 0x00, 0x00, 0x00, ... (zero-padded to 19 bytes)]
```

#### Wireless Multi-Packet Stream (Device -> Host):
Each chunk received from `device.read(64)` has:
```
Byte 0:       0x13 (Report ID)
Byte 1:       Command Response Code (matches query command)
Byte 2:       Total Chunks Count (e.g., 0x0A = 10 chunks for 128-byte profile)
Byte 3:       Chunk Index (0-based)
Byte 4:       Valid Payload Length in Chunk (typically 14 bytes)
Bytes 5..18:  Data Payload (14 bytes)
Byte 19:      Checksum Byte
```

---

## 3. Command Definitions

| Command Name | Wired Code / Prefix | Wireless Query Cmd | Wireless Write Cmd | Payload Size |
| :--- | :--- | :---: | :---: | :---: |
| **Read Profile** | `\x84\x00\x00\x01\x00\x80` | `68` (`0x44`) | — | 128 bytes |
| **Write Profile** | `\x04\x00\x00\x01\x00\x80\x00` | — | `4` (`0x04`) | 128 bytes |
| **Read Light Table** | `\x8a\x00\x00\x01\x00\xe3\x01` | `73` (`0x49`) | — | 480 bytes |
| **Write Light Table**| `\x0a\x00\x00\x00\x00\x00\x02` | — | `9` (`0x09`) | 480 bytes |
| **Prepare Custom RGB**| `\x86\x00\x00\x01\x00\x7a\x01` | `66` (`0x42`) | — | 378 bytes |
| **Write Custom RGB** | `\x06\x00\x00\x01\x00\x7a\x01` | — | `2` (`0x02`) | 378 bytes |
| **Read Keymap (Base)**| `\x83\x00\x00\x01\x00\xf8\x01` | `65` (`0x41`) | — | 504 bytes |
| **Write Keymap (Base)**| `\x03\x00\x00\x01\x00\xf8\x01` | — | `1` (`0x01`) | 504 bytes |
| **Read Macros** | `\x85\x00\x00\x01\x00\x00\x02` | — | — | 512 bytes |
| **Write Macros** | `\x05\x00\x00\x01\x00\x00\x02` | — | — | 512 bytes |

---

## 4. 128-Byte Profile Memory Layout

When reading or writing the active Profile (`PROFILE_READ` / `PROFILE_WRITE`):

| Byte Offset | Parameter | Value Range / Description |
| :---: | :--- | :--- |
| **`0`** | Profile Slot Index | `0x00` (Default Profile 1) |
| **`1`** | Lighting Mode ID | `0` (Off), `1` (Static), `2` (Breathing), `3` (Rainbow), ..., `19` / `277` (Custom) |
| **`2`** | Global Brightness | `0` to `4` (5 discrete brightness levels) |
| **`3`** | Global Speed | `0` to `4` (5 discrete speed levels) |
| **`4`** | Direction | `0` = Left-to-Right / Clockwise, `1` = Right-to-Left / CCW |
| **`5`** | Color Mode Flag | `0` = Custom RGB, `1` = Rainbow Spectrum / Dynamic Multi-color |
| **`6`** | Red Component | `0` to `255` |
| **`7`** | Green Component | `0` to `255` |
| **`8`** | Blue Component | `0` to `255` |
| **`9 .. 127`**| Device Configuration | Sleep timeout, debounce filter, reporting intervals |

---

## 5. Per-Key Addressable Lighting Frame (Planar vs Interleaved)

The custom per-key lighting frame contains 378 bytes ($126 \text{ LEDs} \times 3 \text{ channels}$), but is structured differently depending on the connection mode:

### A. Wired USB Transport (Planar Layout):
$$\text{Frame}_{\text{wired}} = [\text{Red Plane (126 B)}] + [\text{Green Plane (126 B)}] + [\text{Blue Plane (126 B)}]$$
* **Red intensity**: `Frame[k]`
* **Green intensity**: `Frame[126 + k]`
* **Blue intensity**: `Frame[252 + k]`

### B. 2.4 GHz Wireless RF Transport (Interleaved RGB):
$$\text{Frame}_{\text{wireless}} = [R_0, G_0, B_0, R_1, G_1, B_1, \dots, R_{125}, G_{125}, B_{125}]$$
* **Offset for LED index $k$**: `offset = k * 3`
* **Red**: `Frame[offset]`
* **Green**: `Frame[offset + 1]`
* **Blue**: `Frame[offset + 2]`
* **Transmission**: Zero-padded to 512 bytes, transmitted across 37 chunks of 14 bytes each via Command `2` (`WIRELESS_CMD_CUSTOM_LIGHT_WRITE`). Before writing, a wakeup read query `66` (`WIRELESS_CMD_CUSTOM_LIGHT_READ`) is sent.

### Key Logical Coordinates to LED Index Map (82-Key ANSI):

The Swarm 75 uses a 16-column $\times$ 6-row hardware switch matrix:
$$\text{Matrix Index} = (\text{Column} \times 6) + \text{Row}$$

| Key | Col | Row | LED Index | Key | Col | Row | LED Index | Key | Col | Row | LED Index |
| :--- | :---: | :---: | :---: | :--- | :---: | :---: | :---: | :--- | :---: | :---: | :---: |
| **Esc** | 0 | 0 | **0** | **Q** | 1 | 2 | **8** | **F6** | 7 | 0 | **42** |
| **\`** | 0 | 1 | **1** | **A** | 1 | 3 | **9** | **7** | 7 | 1 | **43** |
| **Tab** | 0 | 2 | **2** | **Z** | 1 | 4 | **10** | **U** | 7 | 2 | **44** |
| **Caps** | 0 | 3 | **3** | **LWin**| 1 | 5 | **11** | **J** | 7 | 3 | **45** |
| **LShift**| 0 | 4 | **4** | **F1** | 2 | 0 | **12** | **M** | 7 | 4 | **46** |
| **LCtrl** | 0 | 5 | **5** | **2** | 2 | 1 | **13** | **F7** | 8 | 0 | **48** |
| **1** | 1 | 1 | **7** | **W** | 2 | 2 | **14** | **8** | 8 | 1 | **49** |
| **Space** | 5 | 5 | **35** | **Enter**| 13 | 3 | **81** | **Knob** | 15 | 0 | **90** |
| **Bksp** | 13 | 1 | **79** | **Del** | 15 | 1 | **91** | **Up** | 14 | 4 | **88** |
| **RShift**| 13 | 4 | **82** | **PgUp**| 15 | 2 | **92** | **Down**| 14 | 5 | **89** |
| **Left** | 13 | 5 | **83** | **PgDn**| 15 | 3 | **93** | **Right**| 15 | 5 | **95** |

---

## 6. Safety & Timing Envelope

1. **Inter-Packet Pacing**:
   * Minimum pause between consecutive feature reports: **`30 ms` to `50 ms`**.
   * Pause after query before reading wireless response: **`100 ms` to `200 ms`**.
2. **Read Deadline**:
   * Multi-chunk wireless sequences (10 packets) require a timeout window of at least **`1.5 seconds`** with rolling packet reset.
3. **Fail-Closed Write Safety**:
   * Never issue write operations with unverified lengths.
   * Profile write **must** be exactly 128 bytes.
   * Light table write **must** be exactly 480 bytes.
   * Custom light frame **must** be exactly 378 bytes.



---

## 7. Profile Architecture & Management (Phase 4)

Because the keyboard MCU stores only the single active profile buffer in flash/SRAM without multiple onboard hardware profile banks, multi-profile support is managed app-side with persistent JSON storage:
* **Storage Path**: `backend/data/profiles.json`
* **Profile Schema**:
  ```json
  {
    "id": "preset-matrix",
    "name": "Toxic Matrix (FPS)",
    "description": "High-contrast neon green gaming clusters with blackout base",
    "is_active": true,
    "lighting": {
      "mode_id": 277,
      "mode_name": "Custom (Per-Key)",
      "brightness": 4,
      "speed": 0,
      "direction": 0,
      "color": "#00FF66",
      "is_custom_per_key": true,
      "keys": { "w": "#00FF66", "a": "#00FF66", "s": "#00FF66", "d": "#00FF66" }
    }
  }
  ```
* **Activation Flow**:
  1. Profile is selected in UI or API (`POST /api/profiles/{id}/activate`).
  2. If custom per-key: uploads the 378-byte RGB matrix to Mode 277.
  3. If global preset: builds 128-byte profile and flashes parameters to the keyboard.

---

## 8. Screen Ambience & Virtual Display Mapper (Phase 5)

Phase 5 introduces real-time spatial screen sampling with an interactive virtual display layout:
1. **Virtual Display Mapping**:
   * Screen resolution normalized to coordinates $[0.0, 1.0] \times [0.0, 1.0]$.
   * Configurable insets: $[x_{\text{inset}}, y_{\text{inset}}]$.
   * Normalized key position:
     $$x_{\text{mapped}} = x_{\text{inset}} + (1 - 2 x_{\text{inset}}) \cdot \frac{\text{col}}{15.5}$$
     $$y_{\text{mapped}} = y_{\text{inset}} + (1 - 2 y_{\text{inset}}) \cdot \frac{\text{row}}{5.0}$$
2. **Keyboard Layer on Display**:
   * All 82 ANSI keys are rendered as an interactive overlay directly on top of the virtual display layout.
   * Each key displays its label, a reticle box showing the exact pixel sampling region, and the live averaged RGB color.
   * Real-time HUD shows key inspection: pixel coordinates, sample radius, and averaged color.
3. **Pixel Averaging & Color Post-Processing**:
   * Pixels sampled in a radius $R$ box around $(x_{\text{pixel}}, y_{\text{pixel}})$.
   * RGB values averaged: $(\bar{R}, \bar{G}, \bar{B})$.
   * Saturation boosted via HSV conversion: $S_{\text{new}} = \min(1.0, S \times \text{boost})$.
   * Exponential Moving Average (EMA) smoothing prevents flicker:
     $$C_t = C_{t-1} \cdot (1 - \alpha) + C_{\text{sample}} \cdot \alpha$$
4. **Physical Keyboard Streaming**:
   * Averaged key colors are streamed to the physical keyboard via `/api/ambience/stream-frame` at ~12-14 FPS over 2.4 GHz RF dongle.
