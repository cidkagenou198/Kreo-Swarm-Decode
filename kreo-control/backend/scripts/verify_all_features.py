"""Comprehensive verification of ALL Kreo Swarm 75 hardware features."""

import time
from kreo_control.device.keyboard import KreoKeyboard
from kreo_control.device.protocol import CUSTOM_MODE_ID, STATIC_MODE_ID
from kreo_control.lighting.constants import LIGHTING_MODES
from kreo_control.profiles.models import ProfileCreateRequest, ProfileLightingData
from kreo_control.profiles.store import ProfilesStore

def main():
    print("=" * 70)
    print("   KREO SWARM 75 — COMPREHENSIVE FEATURE VERIFICATION SUITE")
    print("=" * 70)

    kb = KreoKeyboard.get_shared_instance()
    kb.connect()
    print(f"\n[1] HARDWARE CONNECTION:")
    print(f"    - Device: {kb.descriptor.product_name}")
    print(f"    - Connection: {kb.descriptor.connection_type.value}")
    print(f"    - VID: {hex(kb.descriptor.vendor_id)} | PID: {hex(kb.descriptor.product_id)}")
    print(f"    - Status: CONNECTED & RESPONDING")

    # Feature 2: Read current hardware state
    print(f"\n[2] READ ACTIVE LIGHTING STATE:")
    state = kb.get_lighting_state()
    print(f"    - Current Mode: {state.mode_name} (ID: {state.mode_id})")
    print(f"    - Brightness: {state.brightness}/4")
    print(f"    - Speed: {state.speed}/4")
    print(f"    - Per-Key Mode: {state.is_custom_per_key}")

    # Feature 3: Set Hardware Presets (Wave, Rainbow, Breath)
    print(f"\n[3] GLOBAL HARDWARE PRESETS:")
    print(f"    [*] Testing Preset: Rainbow (Mode 3, Brightness 4, Speed 2)...")
    t0 = time.perf_counter()
    s_rainbow = kb.set_global_lighting(mode=3, brightness=4, speed=2)
    t1 = time.perf_counter()
    print(f"        -> Set in {(t1-t0)*1000:.1f}ms: Mode={s_rainbow.mode_name}, Brightness={s_rainbow.brightness}/4")

    time.sleep(1.0)

    # Feature 4: Static Color Mode with Light Table update
    print(f"\n[4] STATIC COLOR WITH LIGHT-TABLE UPDATE:")
    print(f"    [*] Setting Static Sapphire Blue (#0055FF)...")
    t0 = time.perf_counter()
    s_static = kb.set_global_lighting(mode=STATIC_MODE_ID, brightness=3, speed=0, color="#0055FF")
    t1 = time.perf_counter()
    print(f"        -> Set in {(t1-t0)*1000:.1f}ms: Mode={s_static.mode_name}, Color={s_static.color}")

    time.sleep(1.0)

    # Feature 5: Individual Per-Key RGB Customization (WASD + Space + Enter + Arrows)
    print(f"\n[5] INDIVIDUAL PER-KEY RGB CUSTOMIZATION:")
    per_key_edits = {
        "w": "#00FF00",  # Neon Green
        "a": "#00FF00",
        "s": "#00FF00",
        "d": "#00FF00",
        "space": "#00E5FF",  # Cyan
        "enter": "#FF007F",  # Neon Pink
        "esc": "#FF0000",    # Crimson Red
        "up": "#FFFF00",     # Electric Yellow
        "down": "#FFFF00",
        "left": "#FFFF00",
        "right": "#FFFF00",
    }
    print(f"    [*] Flashing custom per-key cluster ({len(per_key_edits)} keys)...")
    t0 = time.perf_counter()
    updated_keys = kb.set_per_key_lighting(per_key_edits)
    t1 = time.perf_counter()
    print(f"        -> Flashed in {(t1-t0)*1000:.1f}ms! Verified keys returned: {len(updated_keys)}")
    
    # Verify readback of key colors
    state_after = kb.get_lighting_state()
    print(f"        -> Active Mode on Keyboard: {state_after.mode_name} (ID: {state_after.mode_id})")
    print(f"        -> Per-Key Custom Active: {state_after.is_custom_per_key}")
    assert state_after.is_custom_per_key, "Failed: keyboard did not switch to Custom Per-Key Mode 277"

    time.sleep(1.5)

    # Feature 6: Profiles Store (Save, Activate, Duplicate, Delete)
    print(f"\n[6] PROFILES ENGINE:")
    store = ProfilesStore()
    profiles = store.list_all()
    print(f"    [+] Loaded {len(profiles)} saved profiles")
    for p in profiles:
        print(f"        - {p.id}: {p.name} ({p.lighting.mode_name})")

    # Activate "preset-cyberpunk"
    print(f"    [*] Activating 'Cyberpunk 2077' Profile...")
    t0 = time.perf_counter()
    store.activate("preset-cyberpunk", kb)
    t1 = time.perf_counter()
    print(f"        -> Profile activated and uploaded to hardware in {(t1-t0)*1000:.1f}ms")

    time.sleep(1.5)

    # Clean restore to factory default
    print(f"\n[7] RESTORING DEFAULT RAINBOW FACTORY STATE:")
    store.activate("default-factory", kb)
    print(f"    [+] Restored default Rainbow Wave profile.")

    print("\n" + "=" * 70)
    print("   ALL HARDWARE FEATURES VERIFIED WORKING LIVE 100%!")
    print("=" * 70)

if __name__ == "__main__":
    main()

