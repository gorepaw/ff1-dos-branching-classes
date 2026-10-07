"""List every call to the library divide/modulo helpers with a constant divisor of 6
(the game's class -> mask-bit and class -> base-class math)."""
import struct
from romlib import find_base_rom

d = find_base_rom().read_bytes()
HELPERS = {0x08000F05: "div", 0x08000F0D: "mod", 0x08000F19: "div", 0x08000F2D: "mod"}
TRAMPOLINES = range(0x0818C24C, 0x0818C270, 4)  # bx r0..r8 veneers


def bl_target(a):
    hi, lo = struct.unpack_from("<HH", d, a)
    if hi >> 11 != 0b11110 or lo >> 11 != 0b11111:
        return None
    off = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
    if off & 0x400000:
        off -= 0x800000
    return 0x08000000 + a + 4 + off


sites = []
for a in range(0, 0x200000, 2):
    if struct.unpack_from("<H", d, a)[0] != 0x2106:  # movs r1, #6
        continue
    for b in (a + 2, a + 4):
        t = bl_target(b)
        if t in TRAMPOLINES:
            # find the helper address loaded into the veneer's register just before
            reg = (t - 0x0818C24C) // 4
            kind = "?"
            for c in range(a - 2, a - 16, -2):
                w = struct.unpack_from("<H", d, c)[0]
                if w >> 11 == 0b01001 and (w >> 8) & 7 == reg:
                    lit = ((c + 4) & ~3) + (w & 0xFF) * 4
                    kind = HELPERS.get(struct.unpack_from("<I", d, lit)[0], "other")
                    break
            sites.append((a, kind))
            break

for a, kind in sites:
    print(f"{0x08000000 + a:08X}  {kind}")
print(len(sites), "sites")
