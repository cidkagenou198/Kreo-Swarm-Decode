import struct, sys
from peutil import PE

pe = PE()
d = pe.data

def va_of(off):
    for name, sva, vsize, rptr, rsize in pe.sections:
        if rptr <= off < rptr + rsize:
            return pe.image_base + sva + (off - rptr)
    return None

def find_wide(s):
    pat = s.encode("utf-16-le")
    out = []
    i = d.find(pat)
    while i != -1:
        out.append((i, va_of(i)))
        i = d.find(pat, i + 1)
    return out

for s in sys.argv[1:]:
    for off, va in find_wide(s):
        print(f"{s!r}: file {off:#x} va {va and hex(va)}")
