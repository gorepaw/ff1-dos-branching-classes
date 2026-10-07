"""Find Thumb `ldr rX, [pc, #imm]` instructions that load a given literal-pool slot.
python tools/litrefs.py <literal_rom_offset_hex> [...]"""
import struct
import sys
from romlib import find_base_rom

d = find_base_rom().read_bytes()
for arg in sys.argv[1:]:
    lit = int(arg, 16)
    found = []
    for a in range(max(0, lit - 1024), lit, 2):
        w = struct.unpack_from("<H", d, a)[0]
        if w >> 11 == 0b01001 and ((a + 4) & ~3) + (w & 0xFF) * 4 == lit:
            found.append(f"{a:#x} (r{(w >> 8) & 7})")
    print(f"{lit:#x}: {', '.join(found) or 'none'}")
