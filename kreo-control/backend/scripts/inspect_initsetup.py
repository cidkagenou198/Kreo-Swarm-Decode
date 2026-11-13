import struct

with open(r'C:\Program Files (x86)\KreoSWARM75\InitSetup.dll', 'rb') as f:
    d = f.read()

pe_offset = struct.unpack('<I', d[0x3C:0x40])[0]
export_rva = struct.unpack('<I', d[pe_offset + 0x78 : pe_offset + 0x7C])[0]
num_sections = struct.unpack('<H', d[pe_offset + 6 : pe_offset + 8])[0]
opt_hdr_size = struct.unpack('<H', d[pe_offset + 0x14 : pe_offset + 0x16])[0]
sec_table = pe_offset + 0x18 + opt_hdr_size

def rva_to_fo(rva):
    for i in range(num_sections):
        sec = d[sec_table + i*40 : sec_table + (i+1)*40]
        vsize, va, rsize, roffset = struct.unpack('<IIII', sec[8:24])
        if va <= rva < va + vsize:
            return roffset + (rva - va)
    return None

exp_fo = rva_to_fo(export_rva)
num_names = struct.unpack('<I', d[exp_fo + 0x18 : exp_fo + 0x1C])[0]
names_rva = struct.unpack('<I', d[exp_fo + 0x20 : exp_fo + 0x24])[0]
names_fo = rva_to_fo(names_rva)

for i in range(num_names):
    name_rva = struct.unpack('<I', d[names_fo + i*4 : names_fo + (i+1)*4])[0]
    nfo = rva_to_fo(name_rva)
    end = d.find(b'\x00', nfo)
    print(f'Export {i}: {d[nfo:end].decode("ascii", errors="ignore")}')

