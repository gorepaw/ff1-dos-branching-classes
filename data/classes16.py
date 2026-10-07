"""Phase 2: expand every per-class table from 12 to 16 classes and repoint its users.

New classes 12-15 (see romlib.NEW_CLASSES) start as copies of an existing promoted
class (graphics, field sprite, accuracy/magic-resist growth) and of their base class
(stat growth), so they behave like that class until phase 5 gives them real data.
The class -> mask-bit code lives in src/classes16.asm.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from romlib import (CLASS_NAME_PTRS, LEVELUP_TABLE, NEW_CLASSES, FreeSpace, encode_str,
                    repoint, u32)

N_OLD = 12
GROWTH_ROW = 99

# Code literal-pool slots (and one RAM-init block entry) that point at each table.
NAME_SITES = {
    0x1DA938: [0x32400, 0x32444, 0x324E8, 0x325B4, 0x33818, 0x37A84, 0x38830, 0x38A54],
    0x1E0980: [0x469EC, 0x46A34, 0x46A84, 0x46AD4, 0x46B14, 0x46B34, 0x46B68, 0x46BB4,
               0x46C04, 0x46C54, 0x46CA4, 0x46D70],
    0x1E1490: [0x4DCE0, 0x4DD54, 0x4DE88],
}
LEVELUP_SITES = [0x6A208, 0x6A368]
ACC_TABLE, ACC_SITES = 0x226FD6, [0x72550]
MRES_TABLE, MRES_SITES = 0x226FE2, [0x72554]
FIELD_SPRITE_TABLE = 0x21608E
FIELD_SPRITE_SITES = [0x572DC, 0x5A058, 0x5CF94, 0x5E764, 0x60008]
GFX_TABLE, GFX_ENTRY = 0x2230FC, 12
# 0xEDF174 is in the pointer block copied to EWRAM 0x02000010 at boot (RAM 0x0200035C)
GFX_SITES = [0x1FD48, 0x20044, 0x293D0, 0x733D0, 0x737F4, 0xEDF174]


def expand(rom, table, entry, extra):
    """Copy a 12-entry table and append one entry per new class, copied from `extra`."""
    old = bytes(rom[table:table + N_OLD * entry])
    return old + b"".join(old[c * entry:(c + 1) * entry] for c in extra)


def apply(rom):
    space = FreeSpace(rom)
    templates = [t for _, _, t in NEW_CLASSES]

    # Class names: the three vanilla pointer tables hold identical strings, so all
    # their users share one 16-entry table.
    ptrs = [u32(rom, CLASS_NAME_PTRS[0] + 4 * c) for c in range(N_OLD)]
    for name, _, _ in NEW_CLASSES:
        ptrs.append(0x08000000 + space.alloc(encode_str(name), align=1))
    names = space.alloc(b"".join(p.to_bytes(4, "little") for p in ptrs))
    for old, sites in NAME_SITES.items():
        repoint(rom, sites, old, names)

    # Stat growth: vanilla indexes rows by class % 6 (6 rows). Now one row per class;
    # promoted and new classes start as copies of their base class's row.
    base_of = list(range(6)) * 2 + [b for _, b, _ in NEW_CLASSES]
    rows = [bytes(rom[LEVELUP_TABLE + b * GROWTH_ROW:LEVELUP_TABLE + (b + 1) * GROWTH_ROW])
            for b in base_of]
    repoint(rom, LEVELUP_SITES, LEVELUP_TABLE, space.alloc(b"".join(rows)))

    # Per-class accuracy / magic resist gained per level, field sprite IDs, graphics.
    repoint(rom, ACC_SITES, ACC_TABLE, space.alloc(expand(rom, ACC_TABLE, 1, templates)))
    repoint(rom, MRES_SITES, MRES_TABLE, space.alloc(expand(rom, MRES_TABLE, 1, templates)))
    repoint(rom, FIELD_SPRITE_SITES, FIELD_SPRITE_TABLE,
            space.alloc(expand(rom, FIELD_SPRITE_TABLE, 1, templates)))
    repoint(rom, GFX_SITES, GFX_TABLE, space.alloc(expand(rom, GFX_TABLE, GFX_ENTRY, templates)))
