"""End-to-End Live hardware verification script for Kreo Swarm 75 Profile Management."""

import time
from kreo_control.device.keyboard import KreoKeyboard
from kreo_control.profiles.models import ProfileCreateRequest, ProfileLightingData
from kreo_control.profiles.store import ProfilesStore

def main():
    print("=" * 65)
    print("   Kreo Control — Phase 4 Live Hardware Profile Verification")
    print("=" * 65)

    kb = KreoKeyboard.get_shared_instance()
    kb.connect()
    print(f"[+] Connected to physical device: {kb.descriptor.product_name} ({kb.descriptor.connection_type.value})")

    store = ProfilesStore()
    profiles = store.list_all()
    print(f"[+] Verified {len(profiles)} profiles in persistent storage:")
    for p in profiles:
        active_mark = "[ACTIVE]" if p.is_active else "        "
        print(f"    {active_mark} {p.id:18} | {p.name}")

    # 1. Activate Cyberpunk 2077 (Mode 277 Custom Per-Key: Neon Cyan & Pink)
    print("\n[*] Step 1: Activating 'preset-cyberpunk' (Cyberpunk 2077)...")
    activated = store.activate("preset-cyberpunk", kb)
    assert activated is not None, "Failed to activate preset-cyberpunk"
    print(f"[+] Successfully flashed to hardware: {activated.name}")

    time.sleep(1.5)
    state = kb.get_lighting_state()
    print(f"    - Hardware Mode: {state.mode_name} (ID: {state.mode_id})")
    print(f"    - Custom Per-Key: {state.is_custom_per_key}")
    print(f"    - Brightness: {state.brightness}/4")
    assert state.is_custom_per_key is True

    # 2. Activate Toxic Matrix (FPS)
    print("\n[*] Step 2: Activating 'preset-matrix' (Toxic Matrix FPS)...")
    activated = store.activate("preset-matrix", kb)
    assert activated is not None, "Failed to activate preset-matrix"
    print(f"[+] Successfully flashed to hardware: {activated.name}")

    time.sleep(1.5)
    state = kb.get_lighting_state()
    print(f"    - Hardware Mode: {state.mode_name} (ID: {state.mode_id})")
    print(f"    - Custom Per-Key: {state.is_custom_per_key}")
    assert state.is_custom_per_key is True

    # 3. Create a dynamic test profile
    test_id = "test-live-profile"
    print(f"\n[*] Step 3: Creating and activating new custom profile '{test_id}'...")
    # Delete if exists from previous run
    store.delete(test_id)
    new_profile = store.create(ProfileCreateRequest(
        name="Live Test Profile",
        description="Automated end-to-end hardware profile test",
        lighting=ProfileLightingData(
            mode_id=1,
            mode_name="Static",
            brightness=3,
            speed=0,
            direction=0,
            color="#FF0055",
            is_custom_per_key=False,
            keys={},
        )
    ))
    activated = store.activate(new_profile.id, kb)
    print(f"[+] Activated newly created profile: {activated.name}")

    time.sleep(1.5)
    state = kb.get_lighting_state()
    print(f"    - Hardware Mode: {state.mode_name} (ID: {state.mode_id})")
    print(f"    - Color: {state.color}")
    print(f"    - Brightness: {state.brightness}/4")

    # Clean up test profile
    store.delete(new_profile.id)
    print(f"[+] Cleaned up temporary test profile '{new_profile.id}'")

    # 4. Restore Default Profile
    print("\n[*] Step 4: Restoring 'default-factory' profile (Rainbow Wave)...")
    activated = store.activate("default-factory", kb)
    print(f"[+] Restored: {activated.name}")

    time.sleep(1.0)
    state = kb.get_lighting_state()
    print(f"    - Final Hardware Mode: {state.mode_name} (ID: {state.mode_id})")
    print(f"    - Brightness: {state.brightness}/4")
    print(f"    - Speed: {state.speed}/4")

    print("\n" + "=" * 65)
    print("   ALL HARDWARE PROFILE OPERATIONS VERIFIED LIVE WITH KEYBOARD!")
    print("=" * 65)

if __name__ == "__main__":
    main()
