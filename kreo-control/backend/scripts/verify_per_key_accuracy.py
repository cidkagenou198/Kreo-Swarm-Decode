import time
from kreo_control.device.keyboard import KreoKeyboard
from kreo_control.device.protocol import (
    write_custom_light_wireless,
    read_custom_light_wireless,
    write_profile_wireless,
    build_profile_write,
    CUSTOM_MODE_ID,
)
from kreo_control.lighting.matrix import (
    load_swarm75_led_map,
    build_planar_custom_frame,
    rgb_to_hex,
)

def verify():
    kb = KreoKeyboard.auto_connect()
    transport, dev = kb._ensure_connected()
    print("Connected to:", dev.product_name, f"({dev.connection_type})")
    
    # 1. Switch to custom mode 277
    profile = kb._cached_profile or bytes([0] * 128)
    up = build_profile_write(profile, mode_id=CUSTOM_MODE_ID, brightness_level=4, speed=0, effect_type=1)
    write_profile_wireless(transport, up)
    time.sleep(0.05)
    
    # 2. Build planar frame with specific colors:
    # ESC: Pure RED (#FF0000)
    # W: Pure GREEN (#00FF00)
    # SPACE: Pure BLUE (#0000FF)
    # ENTER: YELLOW (#FFFF00)
    edits = {
        "esc": "#FF0000",
        "w": "#00FF00",
        "space": "#0000FF",
        "enter": "#FFFF00",
    }
    
    # Base frame is all black (0)
    black_base = bytes([0] * 378)
    planar_frame = build_planar_custom_frame(edits, black_base)
    
    print("\nWriting PLANAR custom frame to hardware...")
    write_custom_light_wireless(transport, planar_frame)
    print("Hardware write completed!")
    time.sleep(0.15)
    
    # 3. Read back frame from hardware to verify exact memory state
    print("\nReading back custom frame from hardware...")
    readback = read_custom_light_wireless(transport)
    assert len(readback) == 378, f"Unexpected length {len(readback)}"
    
    led_map = load_swarm75_led_map()
    map_by_key = {k.ui_key.lower(): k for k in led_map}
    
    for key_name, expected_hex in edits.items():
        entry = map_by_key[key_name]
        idx = entry.led_index
        r = readback[idx]
        g = readback[126 + idx]
        b = readback[252 + idx]
        read_hex = rgb_to_hex(r, g, b)
        print(f"Key '{key_name.upper():<6}' (ledIdx={idx:<2}): Expected={expected_hex} | Read={read_hex}")
        assert read_hex.lower() == expected_hex.lower(), f"Mismatch on {key_name}: expected {expected_hex}, got {read_hex}"
        
    print("\n>>> ALL VERIFIED ACCURATE 100%! Physical keyboard hardware matches perfectly! <<<")

if __name__ == "__main__":
    verify()

