from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from kreo_control.device.keyboard import KreoKeyboard
from kreo_control.lighting.matrix import load_swarm75_led_map
from kreo_control.profiles.models import (
    KeyboardProfile,
    ProfileCreateRequest,
    ProfileLightingData,
    ProfileUpdateRequest,
)


def get_default_store_path() -> Path:
    """Return persistent profiles JSON path under backend data directory."""
    path = Path(__file__).resolve().parents[3] / "data" / "profiles.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def build_default_profiles() -> list[KeyboardProfile]:
    """Generate curated default profiles for first-time startup."""
    now = datetime.now(timezone.utc).isoformat()
    led_map = load_swarm75_led_map()

    # 1. Default Factory Profile
    p_default = KeyboardProfile(
        id="default-factory",
        name="Default (Rainbow Wave)",
        description="Factory spectrum rainbow wave across all keys",
        is_active=True,
        created_at=now,
        updated_at=now,
        lighting=ProfileLightingData(
            mode_id=3,
            mode_name="Rainbow",
            brightness=3,
            speed=2,
            direction=0,
            color="#FF0000",
            is_custom_per_key=False,
            keys={},
        ),
    )

    # 2. Cyberpunk Neon (Per-Key)
    cyber_keys: dict[str, str] = {}
    modifier_keys = {
        "esc", "tab", "caps", "left_shift", "right_shift", "left_ctrl",
        "left_win", "left_alt", "space", "right_alt", "fn", "right_ctrl",
        "enter", "backspace", "del", "page_up", "page_down", "end", "up", "down", "left", "right"
    }
    for k in led_map:
        u = k.ui_key.toLowerCase() if hasattr(k.ui_key, "toLowerCase") else k.ui_key.lower()
        if u in modifier_keys:
            cyber_keys[u] = "#FF007F"  # Hot pink
        elif u in {"w", "a", "s", "d"}:
            cyber_keys[u] = "#FFE600"  # Cyber gold
        else:
            cyber_keys[u] = "#00E5FF"  # Aqua cyan

    p_cyberpunk = KeyboardProfile(
        id="preset-cyberpunk",
        name="Cyberpunk 2077",
        description="Cyan alphas, hot pink modifiers, and neon gold WASD keys",
        is_active=False,
        created_at=now,
        updated_at=now,
        lighting=ProfileLightingData(
            mode_id=277,
            mode_name="Custom (Per-Key)",
            brightness=4,
            speed=0,
            direction=0,
            color="#00E5FF",
            is_custom_per_key=True,
            keys=cyber_keys,
        ),
    )

    # 3. Toxic Matrix (FPS Gamer)
    matrix_keys: dict[str, str] = {}
    gamer_keys = {"w", "a", "s", "d", "up", "down", "left", "right", "space"}
    for k in led_map:
        u = k.ui_key.lower()
        if u in gamer_keys:
            matrix_keys[u] = "#00FF66"  # Electric Green
        else:
            matrix_keys[u] = "#061A0C"  # Dark forest stealth

    p_matrix = KeyboardProfile(
        id="preset-matrix",
        name="Toxic Matrix (FPS)",
        description="High-contrast neon green gaming clusters with blackout base",
        is_active=False,
        created_at=now,
        updated_at=now,
        lighting=ProfileLightingData(
            mode_id=277,
            mode_name="Custom (Per-Key)",
            brightness=4,
            speed=0,
            direction=0,
            color="#00FF66",
            is_custom_per_key=True,
            keys=matrix_keys,
        ),
    )

    # 4. Oceanic Deep Blue (Static)
    p_oceanic = KeyboardProfile(
        id="preset-oceanic",
        name="Oceanic Calm",
        description="Subtle static deep sapphire glow for evening focus",
        is_active=False,
        created_at=now,
        updated_at=now,
        lighting=ProfileLightingData(
            mode_id=1,
            mode_name="Static",
            brightness=2,
            speed=0,
            direction=0,
            color="#0077B6",
            is_custom_per_key=False,
            keys={},
        ),
    )

    return [p_default, p_cyberpunk, p_matrix, p_oceanic]


class ProfilesStore:
    """Manages persistent profiles and physical hardware profile synchronization."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or get_default_store_path()
        self._profiles: list[KeyboardProfile] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._profiles = build_default_profiles()
            self._save()
            return

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._profiles = [KeyboardProfile.model_validate(item) for item in raw]
            if not self._profiles:
                self._profiles = build_default_profiles()
                self._save()
        except Exception:
            self._profiles = build_default_profiles()
            self._save()

    def _save(self) -> None:
        raw = [p.model_dump() for p in self._profiles]
        self.path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    def list_all(self) -> list[KeyboardProfile]:
        return list(self._profiles)

    def get(self, profile_id: str) -> KeyboardProfile | None:
        for p in self._profiles:
            if p.id == profile_id:
                return p
        return None

    def get_active(self) -> KeyboardProfile | None:
        for p in self._profiles:
            if p.is_active:
                return p
        return self._profiles[0] if self._profiles else None

    def create(
        self,
        request: ProfileCreateRequest,
        current_lighting: ProfileLightingData | None = None,
    ) -> KeyboardProfile:
        now = datetime.now(timezone.utc).isoformat()
        lighting = request.lighting or current_lighting or ProfileLightingData()

        new_profile = KeyboardProfile(
            id=f"profile-{uuid4().hex[:8]}",
            name=request.name.strip(),
            description=request.description.strip(),
            is_active=False,
            created_at=now,
            updated_at=now,
            lighting=lighting,
        )
        self._profiles.append(new_profile)
        self._save()
        return new_profile

    def update(self, profile_id: str, request: ProfileUpdateRequest) -> KeyboardProfile | None:
        profile = self.get(profile_id)
        if profile is None:
            return None

        if request.name is not None:
            profile.name = request.name.strip()
        if request.description is not None:
            profile.description = request.description.strip()
        if request.lighting is not None:
            profile.lighting = request.lighting

        profile.updated_at = datetime.now(timezone.utc).isoformat()
        self._save()
        return profile

    def delete(self, profile_id: str) -> bool:
        if len(self._profiles) <= 1:
            # Cannot delete the only remaining profile
            return False

        target = self.get(profile_id)
        if target is None:
            return False

        was_active = target.is_active
        self._profiles = [p for p in self._profiles if p.id != profile_id]

        if was_active and self._profiles:
            self._profiles[0].is_active = True

        self._save()
        return True

    def duplicate(self, profile_id: str) -> KeyboardProfile | None:
        source = self.get(profile_id)
        if source is None:
            return None

        now = datetime.now(timezone.utc).isoformat()
        cloned = KeyboardProfile(
            id=f"profile-{uuid4().hex[:8]}",
            name=f"{source.name} (Copy)",
            description=source.description,
            is_active=False,
            created_at=now,
            updated_at=now,
            lighting=ProfileLightingData.model_validate(source.lighting.model_dump()),
        )
        self._profiles.append(cloned)
        self._save()
        return cloned

    def activate(self, profile_id: str, keyboard: KreoKeyboard) -> KeyboardProfile | None:
        """Set profile active and upload its complete lighting state to the physical keyboard."""
        target = self.get(profile_id)
        if target is None:
            return None

        for p in self._profiles:
            p.is_active = (p.id == profile_id)

        target.updated_at = datetime.now(timezone.utc).isoformat()
        self._save()

        # Apply to hardware
        lighting = target.lighting
        if lighting.is_custom_per_key and lighting.keys:
            keyboard.set_per_key_lighting(lighting.keys)
        else:
            keyboard.set_global_lighting(
                mode=lighting.mode_id,
                brightness=lighting.brightness,
                speed=lighting.speed,
                color=lighting.color,
            )

        return target

    def export_profile(self, profile_id: str) -> dict | None:
        profile = self.get(profile_id)
        if profile is None:
            return None
        return profile.model_dump()

    def import_profile(self, data: dict) -> KeyboardProfile:
        now = datetime.now(timezone.utc).isoformat()
        lighting_data = data.get("lighting", {})

        imported = KeyboardProfile(
            id=f"profile-{uuid4().hex[:8]}",
            name=f"{data.get('name', 'Imported Profile')}".strip(),
            description=data.get("description", "Imported from file").strip(),
            is_active=False,
            created_at=now,
            updated_at=now,
            lighting=ProfileLightingData.model_validate(lighting_data),
        )
        self._profiles.append(imported)
        self._save()
        return imported

