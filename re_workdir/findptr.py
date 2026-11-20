import struct, sys
from peutil import PE

pe = PE()
d = pe.data

targets = [int(x, 16) for x in sys.argv[1:]] or [0x48c250, 0x48ec30, 0x48a060]

for i in range(0, len(d) - 4, 4):
    v = struct.unpack_from("<I", d, i)[0]
    if v in targets:
        for name, sva, vsize, rptr, rsize in pe.sections:
            if rptr <= i < rptr + rsize:
                va = pe.image_base + sva + (i - rptr)
                print(f"{hex(v)} -> {hex(va)} ({name})")
                break
