import json
from kreo_control.lighting.matrix import load_swarm75_led_map, map_logical_id_to_ui

led_map = load_swarm75_led_map()
print(f"Total entries in backend led_map: {len(led_map)}")

# Let's inspect frontend SWARM75_SVG_PATHS
with open(r"d:\Reverse-Any\kreo-control\frontend\src\lib\svgPaths.ts", "r", encoding="utf-8") as f:
    svg_code = f.read()

import re
svg_ids = re.findall(r'"(key_[A-Za-z0-9_]+)":', svg_code)
print(f"Total keys in frontend svgPaths.ts: {len(svg_ids)}")

# Check if every backend svg_id is in frontend svgPaths.ts
backend_svg_ids = {e.svg_id for e in led_map}
frontend_svg_ids = set(svg_ids)

missing_in_frontend = backend_svg_ids - frontend_svg_ids
missing_in_backend = frontend_svg_ids - backend_svg_ids

print(f"Missing in frontend: {missing_in_frontend}")
print(f"Missing in backend: {missing_in_backend}")

for e in led_map[:10]:
    print(f"logical={e.logical_id:<12} -> ui_key={e.ui_key:<12} label={e.label:<8} svg_id={e.svg_id:<15} ledIdx={e.led_index}")

