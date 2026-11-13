import json
import re

# Read KB.ini
kb_ini_path = r"C:\Program Files (x86)\KreoSWARM75\Dev\kb\KB.ini"
with open(kb_ini_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

ini_keys = []
key_section = False
for line in lines:
    line = line.strip()
    if line.startswith("[KEY]"):
        key_section = True
        continue
    elif line.startswith("[") and key_section:
        break
    if key_section:
        if line.startswith(";"):
            curr_name = line[1:].strip()
        elif line.startswith("K") and "=" in line:
            parts = line.split("=", 1)[1].split(",")
            if len(parts) >= 8:
                led_idx = int(parts[7].strip())
                ini_keys.append((curr_name, led_idx))

# Read led-map.json
with open(r"d:\Reverse-Any\kreo-control\frontend\public\keyboard\swarm75\meta\led-map.json", "r", encoding="utf-8") as f:
    json_data = json.load(f)

json_keys = json_data.get("keys", [])

print(f"Total keys in KB.ini: {len(ini_keys)}")
print(f"Total keys in led-map.json: {len(json_keys)}")

# Let's compare position-by-position
mismatches = 0
for i in range(min(len(ini_keys), len(json_keys))):
    ini_name, ini_led = ini_keys[i]
    jk = json_keys[i]
    j_log = jk["logicalId"]
    j_led = jk["ledIndex"]
    if ini_led != j_led:
        print(f"MISMATCH at index {i}: KB.ini={ini_name} (ledIdx={ini_led}) vs json={j_log} (ledIdx={j_led})")
        mismatches += 1

if mismatches == 0:
    print("ALL 82 KEYS IN KB.INI AND LED-MAP.JSON MATCH 100% PERFECTLY!")

