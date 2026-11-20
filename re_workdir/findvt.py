import struct
from peutil import PE

pe = PE()
d = pe.data

def va_range():
    for name, sva, vsize, rptr, rsize in pe.sections:
        base = pe.image_base + sva
        yield name, base, rptr, max(vsize, rsize)

targets = {
    0x487880: "SetMatrix3632",
    0x4878c0: "GetMatrix3632",
    0x4878f0: "WriteMacroData3632",
    0x487990: "SetMacro3632",
    0x4879d0: "GetMacro3632",
    0x4879f0: "SetLED3632",
    0x487a40: "GetLED3632",
    0x487a70: "SetOnBoard3632",
    0x487ac0: "GetOnBoard3632",
    0x487b20: "SetGame3632",
    0x487b60: "GetGame3632",
    0x487b80: "SetLedRgbTab3632",
    0x487bc0: "GetLedRgbTab3632",
    0x487be0: "SetScreenParam3632",
    0x487c20: "ResetDevice3632",
    0x487c60: "Online3632",
}

hits = {}
for i in range(0, len(d) - 4, 4):
    v = struct.unpack_from("<I", d, i)[0]
    if v in targets:
        hits.setdefault(v, []).append(i)

for name, base, rptr, size in va_range():
    for v, offs in hits.items():
        for o in offs:
            if rptr <= o < rptr + size:
                print(f"{targets[v]:20s} {hex(v)} -> VA {hex(base + (o - rptr))} ({name})")
