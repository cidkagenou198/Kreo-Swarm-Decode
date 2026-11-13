import time
from kreo_control.device.keyboard import KreoKeyboard
from kreo_control.lighting.matrix import (
    load_swarm75_led_map,
    build_receiver_custom_frame,
    hex_to_rgb,
)
from kreo_control.lighting.constants import CUSTOM_FRAME_SIZE

def test():
    kb = KreoKeyboard.auto_connect()
    print(f"Connected to: {kb.descriptor}")
    
    # Let's test ESC key
    # In led-map.json: ESC has ledIndex=0, pos=0
    print("Testing ESC in RED...")
    kb.set_per_key_lighting({"esc": "#FF0000"})
    time.sleep(2)
    
    print("Testing ESC in GREEN...")
    kb.set_per_key_lighting({"esc": "#00FF00"})
    time.sleep(2)
    
    print("Testing ESC in BLUE...")
    kb.set_per_key_lighting({"esc": "#0000FF"})
    time.sleep(2)

if __name__ == "__main__":
    test()

