# FF1 Dawn of Souls (USA) — Hacking Findings

ROM: `Final Fantasy I & II - Dawn of Souls (USA).gba`
- Header `FF1&2DAWNOFS` / `BFFE`, 16 MiB
- CRC32 `1B39CDAB`, MD5 `5D29999685413C4D2BEC10D3160F6EE6` (the MD5 exline's editor and the Approaching Chaos randomizer expect)
- SHA1 `6472695D69661490F78245E2982E1E676C080BE7`

All offsets are ROM file offsets (add `0x08000000` for GBA bus addresses).

## Text
- Shift-JIS full-width (decode with Python `cp932` + NFKC), null-terminated. Not compressed.
- Class names: `0x1DA85C`; pointer tables (12 entries each) at `0x1DA938`, `0x1E0980`, `0x1E1490`.
  - Code refs to `0x1DA938`: 0x32400, 0x32444, 0x324E8, 0x325B4, 0x33818, 0x37A84, 0x38830, 0x38A54
  - Code refs to `0x1E0980`: 0x469EC–0x46D70 (12 refs)
  - Code refs to `0x1E1490`: 0x4DCE0, 0x4DD54, 0x4DE88
- Weapon/armor/item/spell names + descriptions: see the [Data Crystal ROM map](https://datacrystal.tcrf.net/wiki/Final_Fantasy_I_%26_II:_Dawn_of_Souls/ROM_map).

## Class system (key for adding classes)
- Class IDs 0–11: Warrior, Thief, Monk, RdM, WhM, BlM, Knight, Ninja, Master, RdW, WhW, BlW.
- **Equip / spell-learn permission = u16 bitmask**: bits 0–5 = base classes, bits 8–13 = promoted
  (verified: Nunchaku `0x0604` = Monk|Ninja|Master). **Free bits: 6, 7, 14, 15** → room for
  2 new base classes + 2 promotions without changing data formats.
  - Weapons `0x19F33C` (65 × 28 B, mask at +2), Armor `0x19FA58` (71 × 28 B, mask at +2),
    Spell-learn table `0x1A20C0` (u16 per spell).
- Base stats `0x1E1354`: 6 × 16 B (hp u16, mp u16, spell_level, str, agi, int, sta, lck, acc, eva, mdef, init_weapon, init_armor, 0).
  Only 6 entries → promoted classes inherit; table abuts the class-name strings (must relocate to expand).
- Level-up growth `0x223ADC`: 594 entries = 6 classes × 99 levels, 1 bitfield byte each
  (hp mp str agi int sta lck spell_level). Also must relocate to add classes.
- Per-class level accuracy `0x226FD6` (12 B), magic resist `0x226FE2` (12 B).
- Hardcoded class checks exist, e.g. `0x06A264` (Warrior/Thief/Monk/Master don't gain MP).
  Expect more `cmp rX, #12`-style bounds and class switch tables in menu/battle code.
- Equip menu draws class list as 2 rows × 6 (code ~0x32480).

## Spells
- Spell data `0x1A1980`: 116 × 16 B (usage, targeting, power u16, element u16, type, anim, acc, level, mp u16, price u32).
- Table layouts cross-checked against the [Approaching Chaos](https://github.com/abyssonym/approaching_chaos) randomizer's `tables/`.

## Free space
- `0xEE0760`–`0xFFFFFF` (~1.1 MiB of 0xFF). ROM can be expanded to 32 MiB (use BPS, not IPS, past 16 MiB).

## Existing scene
- **FFI DoS Editor** (exline, RHDN utility #1291, v2.7d 2022): main data editor; needs our exact MD5.
- **Mod of Balance** (Ludmeister, RHDN #853): 12 classes selectable from start — closest prior art.
- **Vancian Magic System** + **Remix** (Kea, RHDN #3459): ASM-heavy, source included.
- **Maeson** (RHDN #6244), **Hard Mode** (#1978), **Solo Assist** (Rabite, #5253), **Improved Equip Stat Viewing** (#5685).
- **Approaching Chaos** randomizer (abyssonym, github.com/abyssonym/approaching_chaos): `tables/` has struct definitions for most FF1 tables.
- Docs: [Data Crystal wiki](https://datacrystal.tcrf.net/wiki/Final_Fantasy_I_%26_II:_Dawn_of_Souls), [Ludwig's hacking notes](https://www.jeffludwig.com/finalfantasy/hacking-notes.php).
- No prior hack found that adds a 13th+ class.

## RAM
- Party: `0x020026CC`, 4 characters × `0x48` bytes; field layout in [docs/class_handling.md](docs/class_handling.md). Inventory `0x020027EC`, gil `0x02002AB4`.

## Class handling
See [docs/class_handling.md](docs/class_handling.md) for every class-dependent site.

## Toolchain
- `tools/setup.py`: armips 0.11.0, Flips v198; `--ghidra` adds JDK 21, Ghidra 12.0.2, gba-ghidra-loader.
- mGBA 0.10.5 (debugger, Lua scripting) for testing; Python + capstone for quick disassembly.
