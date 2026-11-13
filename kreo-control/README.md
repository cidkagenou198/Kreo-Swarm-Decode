# Kreo Control

Independent desktop application and hardware communication engine for the **Kreo Swarm 75** mechanical keyboard.

---

## Architecture Overview

```
kreo-control/
├── backend/                        # Python 3.11+ / FastAPI / hidapi / mss / pillow
│   ├── src/kreo_control/
│   │   ├── ambience/               # Screen capture & spatial pixel averaging engine
│   │   ├── api/                    # REST API routes (/api/lighting, /profiles, /ambience)
│   │   ├── device/                 # Transport, Discovery, Chunked Protocol framing
│   │   ├── lighting/               # RGB models, 126-key dual matrix builder (ANSI 82)
│   │   └── profiles/               # Persistent JSON profile store & hardware flasher
│   ├── scripts/                    # Live hardware verification test scripts
│   └── tests/                      # Pytest hardware and protocol tests (24 passing)
│
├── frontend/                       # React 18 / TypeScript / Tailwind CSS / Vite
│   ├── public/keyboard/swarm75/    # Vector SVG overlays and key metadata
│   └── src/
│       ├── components/
│       │   ├── DisplayMapperPanel.tsx  # Virtual Display Layout & Keyboard Screen Overlay
│       │   ├── ProfileModal.tsx        # Profile switcher & management drawer
│       │   ├── SvgKeyboardSurface.tsx  # Photorealistic SVG keyboard canvas
│       │   ├── KeyboardLayout.tsx      # Tactical mechanical grid layout
│       │   ├── BoardActionsBar.tsx     # Undo/Redo & quick pattern generators
│       │   ├── ColorPickerPanel.tsx    # Precision RGB hex palette picker
│       │   └── EffectsPanel.tsx        # Hardware preset effects simulator
│       └── lib/                        # Math effects & screen sampling utilities
│
├── start-app.bat                   # One-click Windows desktop launcher
├── start-app.ps1                   # PowerShell concurrent runner
└── docs/
    └── PROTOCOL.md                 # Living verified hardware specification
```

---

## Development Phases & Status

* **Phase 1: Protocol Verification & Discovery** — COMPLETE (Verified live over 2.4 GHz RF `0x3554:0xFA09`).
* **Phase 2: Dual Matrix Composition & Chunked Framing** — COMPLETE (378-byte RGB matrix across 37 chunks).
* **Phase 3: Interactive Visual Editor & Effects Engine** — COMPLETE (SVG surface + tactical grid, staged edits, undo/redo).
* **Phase 4: Profile Management & Desktop Integration** — COMPLETE (Persistent JSON profiles, instant hardware activation, import/export, `start-app.bat`).
* **Phase 5: Screen Ambience & Real-Time Screen Sync** — COMPLETE (Virtual Display Layout, Keyboard Layer screen overlay, real-time pixel averaging, and physical Kreo Swarm 75 sync).

---

## Quick Start

### Option A: One-Click Desktop Launcher
Simply double-click `start-app.bat` or run:
```powershell
.\start-app.ps1
```
This automatically boots the FastAPI backend (port 8000), Vite frontend (port 5173), and launches your browser.

### Option B: Manual Startup

#### 1. Hardware Probe Diagnostics:
```powershell
cd backend
uv run kreo-probe
```

#### 2. Start Backend API Server:
```powershell
cd backend
uv run uvicorn kreo_control.api.app:app --port 8000
```

#### 3. Start Frontend UI:
```powershell
cd frontend
npm run dev
```

#### 4. Run Test Suite:
```powershell
cd backend
uv run pytest
```
