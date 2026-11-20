import struct, sys, bisect
from peutil import PE

pe = PE()
d = pe.data

# load function table: entry, size, name
funcs = []
for line in open(r"D:\Reverse-Any\re_workdir\out_functions.txt", encoding="utf-8", errors="replace"):
    p = line.rstrip("\n").split("\t")
    if len(p) == 3:
        funcs.append((int(p[0], 16), int(p[1]), p[2]))
funcs.sort()
starts = [f[0] for f in funcs]

def resolve(va):
    i = bisect.bisect_right(starts, va) - 1
    if i >= 0 and starts[i] <= va < starts[i] + max(funcs[i][1], 1):
        return funcs[i][2] + ("+%#x" % (va - starts[i]) if va != starts[i] else "")
    return "?"

def dump(start, end):
    print(f"--- {hex(start)} .. {hex(end)} ---")
    for va in range(start, end, 4):
        v = pe.u32(va)
        mark = ""
        if v in (0x487880, 0x4878c0, 0x487990, 0x4879d0, 0x4879f0, 0x487a40, 0x487a70,
                 0x487ac0, 0x487b20, 0x487b60, 0x487b80, 0x487bc0, 0x487be0, 0x487c20, 0x487c60):
            mark = "  <== 3632 method"
        print(f"{hex(va)}  slot+{va - 0x60f4b4:#05x}  {hex(v):>10s}  {resolve(v)}{mark}")

if __name__ == "__main__":
    dump(int(sys.argv[1], 16), int(sys.argv[2], 16))
