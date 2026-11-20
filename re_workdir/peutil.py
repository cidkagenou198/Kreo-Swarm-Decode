"""Minimal PE helpers for static extraction from OemDrv.exe.

VA -> file offset uses the section table only (image base 0x400000).
"""
import struct
import sys

PATH = r"D:\Reverse-Any\re_workdir\target\OemDrv.exe"


class PE:
    def __init__(self, path=PATH):
        self.data = open(path, "rb").read()
        d = self.data
        e_lfanew = struct.unpack_from("<I", d, 0x3C)[0]
        assert d[e_lfanew:e_lfanew + 4] == b"PE\0\0"
        coff = e_lfanew + 4
        nsec = struct.unpack_from("<H", d, coff + 2)[0]
        optsz = struct.unpack_from("<H", d, coff + 16)[0]
        opt = coff + 20
        self.image_base = struct.unpack_from("<I", d, opt + 28)[0]
        sec = opt + optsz
        self.sections = []
        for i in range(nsec):
            o = sec + i * 40
            name = d[o:o + 8].rstrip(b"\0").decode("latin1")
            vsize, va, rsize, rptr = struct.unpack_from("<IIII", d, o + 8)
            self.sections.append((name, va, vsize, rptr, rsize))

    def off(self, va):
        rva = va - self.image_base
        for name, sva, vsize, rptr, rsize in self.sections:
            if sva <= rva < sva + max(vsize, rsize):
                return rptr + (rva - sva)
        raise KeyError(hex(va))

    def read(self, va, n):
        o = self.off(va)
        return self.data[o:o + n]

    def u16(self, va):
        return struct.unpack("<H", self.read(va, 2))[0]

    def u32(self, va):
        return struct.unpack("<I", self.read(va, 4))[0]


if __name__ == "__main__":
    pe = PE()
    print("image base", hex(pe.image_base))
    for s in pe.sections:
        print(s)
    va = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x64b700
    n = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x40
    b = pe.read(va, n)
    for i in range(0, len(b), 16):
        print(f"{va + i:08x}  " + " ".join(f"{x:02x}" for x in b[i:i + 16]))
