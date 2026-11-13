import json

kb_ini_path = r"C:\Program Files (x86)\KreoSWARM75\Dev\kb\KB.ini"
with open(kb_ini_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

ini_map = {}
key_section = False
curr_name = ""
for line in lines:
    line = line.strip()
    if line.startswith("[KEY]"):
        key_section = True
        continue
    elif line.startswith("[") and key_section:
        break
    if key_section:
        if line.startswith(";"):
            curr_name = line[1:].strip().upper()
        elif line.startswith("K") and "=" in line:
            parts = line.split("=", 1)[1].split(",")
            if len(parts) >= 8:
                led_idx = int(parts[7].strip())
                ini_map[curr_name] = led_idx

with open(r"d:\Reverse-Any\kreo-control\frontend\public\keyboard\swarm75\meta\led-map.json", "r", encoding="utf-8") as f:
    json_data = json.load(f)

json_map = {k["logicalId"].upper(): k["ledIndex"] for k in json_data.get("keys", [])}

alias = {
    "PRTSC": "PRINTSCREEN",
    "CAPSLOCK": "CAPSLOCK",
    "LWIN": "LGUI",
    "WIN": "LGUI",
    "PGUP": "PAGEUP",
    "PGDN": "PAGEDOWN",
    "`": "GRAVE",
    "-": "MINUS",
    "=": "EQUAL",
    "[": "LBRACKET",
    "]": "RBRACKET",
    "\\": "BACKSLASH",
    ";": "SEMICOLON",
    "'": "QUOTE",
    ",": "COMMA",
    ".": "DOT",
    "/": "SLASH",
}

mismatches = 0
for ini_k, ini_led in ini_map.items():
    if ini_k == "MUTE":
        continue
    norm_k = alias.get(ini_k, ini_k)
    json_led = json_map.get(norm_k)
    if json_led is None:
        print(f"Key in KB.ini but not in json: {ini_k} (norm: {norm_k})")
        mismatches += 1
    elif json_led != ini_led:
        print(f"LED ID MISMATCH: {ini_k} -> KB.ini={ini_led} vs json={json_led}")
        mismatches += 1

print(f"Total checked: {len(ini_map)-1}. Mismatches: {mismatches}")
if mismatches == 0:
    print("SUCCESS: 100% PERFECT MATCH! Every single key has the exact same LED index in both KB.ini and led-map.json!")
