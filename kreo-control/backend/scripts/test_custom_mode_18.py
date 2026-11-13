import time
from kreo_control.device.keyboard import KreoKeyboard
from kreo_control.device.protocol import (
    read_profile_wireless,
    write_profile_wireless,
    write_custom_light_wireless,
)
from kreo_control.lighting.matrix import (
    load_swarm75_led_map,
    build_planar_custom_frame,
)

def test():
    kb = KreoKeyboard.auto_connect()
    t, dev = kb._ensure_connected()
    print("Testing Custom Mode 18 / 29 on hardware:", dev.connection_type)
    
    # Read current profile
    p = bytearray(read_profile_wireless(t))
    print("Original Profile bytes 0..16:", list(p[:16]))
    
    # Set to Gaoshou / Custom Mode:
    # In KB.ini: GaoshouIndex=18, LedOpt18=18,29,...
    p[1] = 18         # Active mode index: 18 (Gaoshou)
    p[2] = 4          # Max brightness (4)
    p[3] = 2          # Speed
    p[4] = 1          # Custom Mode flag = 1!
    p[5] = 29         # Hardware effect code = 29 (0x1D)!
    p[6] = 0
    p[9] = 0
    p[10] = 18        # Mode ID 18
    p[20] = 0xFF
    p[21] = 0xFF
    
    # Brightness slot for mode 18: index = 32 + (18 * 2) - 2 = 66
    slot_idx = 32 + (18 * 2) - 2
    if slot_idx + 1 < len(p):
        p[slot_idx] = 4
        p[slot_idx + 1] = 0x20
        
    print("Writing updated profile with Mode 18, Byte4=1, Byte5=29...")
    write_profile_wireless(t, bytes(p))
    time.sleep(0.1)
    
    # Build planar custom frame:
    # WASD in bright RED, Space in bright BLUE, ESC in bright GREEN
    edits = {
        "w": "#FF0000",
        "a": "#FF0000",
        "s": "#FF0000",
        "d": "#FF0000",
        "esc": "#00FF00",
        "space": "#0000FF",
    }
    
    # Fill background with a visible soft cyan (#002233) so the user can see all keys are working!
    bg = bytearray(378)
    led_map = load_swarm75_led_map()
    for entry in led_map:
        idx = entry.led_index
        bg[idx] = 0       # Red
        bg[126 + idx] = 40 # Green
        bg[252 + idx] = 80 # Blue
        
    frame = build_planar_custom_frame(edits, bytes(bg))
    print("Sending planar custom frame...")
    write_custom_light_wireless(t, frame)
    print("Custom frame written! Check keyboard lights now!")

if __name__ == "__main__":
    test()

