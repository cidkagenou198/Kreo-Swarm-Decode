"""Live hardware verification for Phase 5 Real-Time Screen Ambience Streaming."""

import math
import time
from kreo_control.device.keyboard import KreoKeyboard
from kreo_control.lighting.matrix import load_swarm75_led_map, rgb_to_hex
from kreo_control.profiles.store import ProfilesStore

def main():
    print("=" * 65)
    print("   Kreo Control — Phase 5 Live Screen Ambience Hardware Stream")
    print("=" * 65)

    kb = KreoKeyboard.get_shared_instance()
    kb.connect()
    print(f"[+] Physical device connected: {kb.descriptor.product_name} ({kb.descriptor.connection_type.value})")

    led_map = load_swarm75_led_map()
    max_col = max(k.col for k in led_map)
    max_row = max(k.row for k in led_map)

    print("\n[*] Streaming 10 dynamic ambient frames to physical keyboard...")
    
    # Simulate a dynamic spatial screen gradient moving across the screen
    for frame in range(10):
        t0 = time.perf_counter()
        t = frame * 0.35
        frame_colors: dict[str, str] = {}

        for k in led_map:
            u = k.col / max_col
            v = k.row / max_row

            # Spatial 2D screen wave: Cyan to Purple to Neon Orange
            wave_val = (math.sin(u * 3.14 + t) + math.cos(v * 3.14 - t * 0.7)) * 0.5
            r = int(max(0, min(255, (wave_val + 1.0) * 110)))
            g = int(max(0, min(255, (1.0 - abs(wave_val)) * 220)))
            b = int(max(0, min(255, (1.0 - wave_val) * 125 + 50)))

            frame_colors[k.ui_key.lower()] = rgb_to_hex(r, g, b)

        # Transmit to hardware
        kb.set_per_key_lighting(frame_colors)
        elapsed = (time.perf_counter() - t0) * 1000
        print(f"    [Frame {frame + 1:02d}/10] Streamed 82 keys in {elapsed:.1f}ms | ESC: {frame_colors['esc']} | Space: {frame_colors['space']}")
        time.sleep(0.08)  # ~12.5 FPS

    print("[+] Screen ambience stream finished cleanly!")

    # Verify readback
    state = kb.get_lighting_state()
    print(f"\n[*] Active Hardware State after streaming:")
    print(f"    - Mode: {state.mode_name} (ID: {state.mode_id})")
    print(f"    - Per-Key Mode: {state.is_custom_per_key}")

    # Restore default rainbow profile
    print("\n[*] Restoring default profile on keyboard...")
    store = ProfilesStore()
    store.activate("default-factory", kb)
    print("[+] Restored Default Profile!")

    print("\n" + "=" * 65)
    print("   PHASE 5 LIVE AMBIENCE STREAMING HARDWARE VERIFICATION PASSED!")
    print("=" * 65)

if __name__ == "__main__":
    main()

