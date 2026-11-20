import struct, sys
from peutil import PE

pe = PE()
d = pe.data

def find(pat, label):
    n = 0
    i = d.find(pat)
    while i != -1 and n < 40:
        va = None
        for name, sva, vsize, rptr, rsize in pe.sections:
            if rptr <= i < rptr + rsize:
                va = pe.image_base + sva + (i - rptr)
                sec = name
                break
        print(f"{label}: file 0x{i:x} va {hex(va) if va else '?'} {sec if va else ''}")
        n += 1
        i = d.find(pat, i + 1)
    print(f"-- {label}: {n} hits\n")

# VID 0x258a, PID 0x010c adjacent dwords
find(struct.pack("<II", 0x258a, 0x010c), "258a:010c")
find(struct.pack("<II", 0x3554, 0xfa09), "3554:fa09")
find(struct.pack("<II", 0x0c, 0x0001) + struct.pack("<II", 0x258a, 0x010c), "usage0c/1 + 258a:010c")
