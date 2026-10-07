"""Find Thumb `bl` instructions targeting the given addresses.
python tools/blrefs.py <target_hex> [...]   (ROM offsets or 0x08... addresses)"""
import struct
import sys
from romlib import find_base_rom

d = find_base_rom().read_bytes()
targets = {int(a, 16) & 0xFFFFFE for a in sys.argv[1:]}
hits = {t: [] for t in targets}
for a in range(0, 0x400000, 2):
    hi, lo = struct.unpack_from("<HH", d, a)
    if hi >> 11 == 0b11110 and lo >> 11 == 0b11111:
        off = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
        if off & 0x400000:
            off -= 0x800000
        t = (a + 4 + off) & 0xFFFFFE
        if t in hits:
            hits[t].append(a)
for t, h in hits.items():
    print(f"{t:#x}: {', '.join(hex(x) for x in h) or 'none'}")
