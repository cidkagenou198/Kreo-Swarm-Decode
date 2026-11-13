import time
from kreo_control.device.keyboard import KreoKeyboard
from kreo_control.lighting.matrix import (
    load_swarm75_led_map,
    build_receiver_custom_frame,
)

def run():
    kb = KreoKeyboard.auto_connect()
    print("Testing single key lights on keyboard.")
    
    led_map = load_swarm75_led_map()
    map_by_key = {k.ui_key.lower(): k for k in led_map}
    
    test_keys = ["esc", "1", "q", "w", "a", "s", "d", "space", "enter"]
    
    for key_name in test_keys:
        k = map_by_key.get(key_name)
        if not k:
            print(f"Key {key_name} not found in map!")
            continue
        print(f"\n--- Lighting key: '{key_name}' (ledIndex={k.led_index}, pos={getattr(k, 'protocol_pos', 'N/A')}) in RED ---")
        
        # Blackout all, then light this one key in RED (#FF0000)
        # Note: we create a zeroed frame of 378 bytes
        frame = bytearray(378)
        offset = k.led_index * 3
        frame[offset] = 255
        frame[offset + 1] = 0
        frame[offset + 2] = 0
        
        # Write via keyboard
        kb.set_per_key_lighting({key_name: "#FF0000"})
        print(f"Applied {key_name} at offset {offset}. Check your keyboard!")
        time.sleep(1)

if __name__ == "__main__":
    run()

