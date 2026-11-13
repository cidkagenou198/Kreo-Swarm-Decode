import time
from kreo_control.device.keyboard import KreoKeyboard
from kreo_control.device.protocol import (
    write_custom_light_wireless,
    write_profile_wireless,
    build_profile_write,
    CUSTOM_MODE_ID,
)
from kreo_control.lighting.matrix import load_swarm75_led_map

def test():
    kb = KreoKeyboard.auto_connect()
    transport, dev = kb._ensure_connected()
    print("Keyboard connected:", dev.connection_type)
    
    # Switch to mode 277 (custom mode)
    profile = kb._cached_profile or bytes([0] * 128)
    up = build_profile_write(profile, mode_id=CUSTOM_MODE_ID, brightness_level=4, speed=0, effect_type=1)
    write_profile_wireless(transport, up)
    time.sleep(0.1)
    
    led_map = load_swarm75_led_map()
    map_by_key = {k.ui_key.lower(): k for k in led_map}
    w_entry = map_by_key['w']
    print(f"W key: led_index={w_entry.led_index}") # Should be 14
    
    # TEST 1: PLANAR FRAME
    # 378 bytes: [126 bytes Red, 126 bytes Green, 126 bytes Blue]
    # Let's turn ONLY 'W' to PURE GREEN (0, 255, 0)
    print("\n--- TEST 1: Writing 'W' as GREEN in PLANAR format ---")
    planar = bytearray(378)
    # Red channel: index 14 = 0
    # Green channel: index 126 + 14 = 255
    planar[126 + w_entry.led_index] = 255
    # Blue channel: index 252 + 14 = 0
    write_custom_light_wireless(transport, bytes(planar))
    print("Written planar frame! Green channel at byte 140.")
    time.sleep(3)
    
    # TEST 2: PLANAR FRAME with WASD in RED
    print("\n--- TEST 2: Writing WASD as RED in PLANAR format ---")
    planar2 = bytearray(378)
    for k_name in ['w', 'a', 's', 'd']:
        idx = map_by_key[k_name].led_index
        planar2[idx] = 255 # Red
    write_custom_light_wireless(transport, bytes(planar2))
    print("Written planar WASD in RED.")
    time.sleep(3)

if __name__ == "__main__":
    test()

