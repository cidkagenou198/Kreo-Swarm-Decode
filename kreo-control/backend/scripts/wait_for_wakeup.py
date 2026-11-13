import time
from kreo_control.device.keyboard import KreoKeyboard
from kreo_control.device.protocol import (
    read_profile_wireless,
    write_profile_wireless,
    build_profile_write,
)

def wait_for_wakeup():
    print("Connecting to dongle...")
    kb = KreoKeyboard.auto_connect()
    t, dev = kb._ensure_connected()
    
    print("\nWaiting for keyboard to wake up from RF sleep (press any key on your keyboard)...")
    for attempt in range(1, 20):
        try:
            p = read_profile_wireless(t)
            print(f"\n>>> KEYBOARD AWAKE & CONNECTED! (attempt {attempt}) <<<")
            
            # Immediately restore standard Rainbow Wave mode (Mode 3, Brightness 4, Speed 2)
            up = build_profile_write(p, mode_id=3, brightness_level=4, speed=2, effect_type=1)
            write_profile_wireless(t, up)
            print(">>> Restored active Rainbow effect on hardware! <<<")
            return True
        except Exception as e:
            print(f"Attempt {attempt}: keyboard asleep... waiting for keypress")
            time.sleep(1.0)
            
    print("Could not wake up keyboard. Please toggle physical switch on bottom.")
    return False

if __name__ == "__main__":
    wait_for_wakeup()

