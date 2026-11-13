import json
from pathlib import Path

path = Path("d:/Reverse-Any/kreo-control/frontend/public/keyboard/swarm75/meta/led-map.json")
data = json.loads(path.read_text(encoding="utf-8"))
keys = data.get("keys", [])

print(f"Total keys: {len(keys)}")
for i, k in enumerate(keys):
    row = k.get("grid", {}).get("row")
    col = k.get("grid", {}).get("col")
    print(f"{i:02d}: logical={k['logicalId']:<12} svg={k['svgId']:<15} ledIdx={k['ledIndex']:<3} pos={k['pos']:<3} pPos={k['protocolPos']:<3} arrIdx={k.get('arrayIndex', -1):<3} r={row} c={col}")

