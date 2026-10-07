# FF1 Dawn of Souls — Branching Classes Hack: Plan

Base: vanilla FF1 Dawn of Souls (USA, MD5 `5d29999685413c4d2bec10d3160f6ee6`). FF2 untouched.
Technical background: see [FINDINGS.md](FINDINGS.md).

## Design

### Roster (16 classes: 6 base, 6 original promotions, 4 new alternates)
Party creation stays at the original 6. At Bahamut, Warrior/Thief/Monk/Red Mage get a yes/no
prompt offering their alternate path; White/Black Mage promote normally.

| Base | Standard promotion | Alternate promotion (new) |
|---|---|---|
| Warrior | **Knight**: tank, white magic ≤ L3, holy swords (Excalibur, Ragnarok) | **Dark Knight**: dark/status black magic (Dark, Fear, Slow, Hold, Scourge, late Death/Break), Dark Claymore, Deathbringer, Braveheart, axes |
| Thief | **Ninja** (reworked): no magic and no MP; Ninja-only katanas (Kikuichimonji, Asura, Kotetsu + Sasuke's, Murasame), top AGI/crit | **Ranger**: monster hunter; signature bane weapons (Wyrmkiller, Werebuster, Ogrekiller, Coral Sword, …), high accuracy/crit, utility spells (Sleep, Slow, Blind, Poisona, Exit). **Bows added in a later phase.** |
| Monk | **Master**: unchanged | **Druid**: Monk-like body, **weaker Monk-style unarmed bonus**, staves/hammers; lightning line, Blizzard/Blizzara, Quake, Sleep/Sleepra/Slow/Hold, Nul-wards, Protect/Protera, Poisona, Cure/Cura |
| Red Mage | **Red Wizard**: generalist caster, wider and higher spell list, loses top-tier swords | **Spellblade**: best swords of the mage line; Temper, Haste, Saber, Focus, Blink, elemental lines up to -ara tier |
| White Mage | White Wizard | — |
| Black Mage | Black Wizard | — |

Overlap rules: Knight = defense + white; Dark Knight = offense + status/death black;
Spellblade = swords + buffs + elemental; Red Wizard = breadth of casting; Druid = elemental
control + wards; Ranger = physical precision + bows + utility; Ninja = pure physical speed.

### Other features
- **Bahamut quick start**: after party creation, a yes/no "Begin at Bahamut?" (it reuses the
  Bahamut yes/no dialog code). Yes = jump to just before the class change with preset
  level, gear, gil, items, story flags, and the airship. Still pick from the original 6.
- **Own stat growth** for every promoted class (level-up table grows from 6 to 16 classes).
- **Common-sense balance pass** on vanilla (scope to be listed later).
- **Vancian magic, eventually**: built on or ported from Kea's Vancian hack (source is
  public; ask Kea for permission and credit them). Until then, keep all per-class magic
  data table-driven and 16 entries wide so the port is a data change, not a redesign.

## Technical approach (decided so far)
- Class IDs 12–15 = Dark Knight, Ranger, Druid, Spellblade (order TBD). Patch the
  ID→bitmask function (`bit = (id/6)*8 + id%6`) so 12–15 map to free bits 6, 7, 14, 15.
- Relocate and expand class tables into free space at `0xEE0760+`: names (3 pointer tables),
  level-up growth (16×99), level accuracy and magic resist (16 each), plus any others found.
- New-class graphics start as palette swaps of existing classes; custom art comes later.
- Every change is built by a reproducible script and distributed as a **BPS** patch.

## Phases

### Phase 0 — Setup ✅
- `tools/setup.py` fetches armips, Flips, and (with `--ghidra`) JDK 21 + Ghidra 12.0.2 +
  gba-ghidra-loader into `tools/bin/` (git-ignored).
- Layout: `src/` (armips .asm), `data/` (Python data patches), `tools/`, `lua/`,
  `build/` (output ROM + .bps; git-ignored). `python tools/build.py` → clean ROM + data +
  asm → patched ROM + BPS. Verified: the empty build reproduces the base ROM exactly.
- `lua/devtools.lua`: party dump, byte poke, set gil, RAM snapshot/diff.
  Class/level/item setters come once phase 1 maps the character struct.
- The repo never contains ROM data or third-party files; extracted data is generated
  locally from the user's ROM.

### Phase 1 — Map class handling ✅ (see [docs/class_handling.md](docs/class_handling.md))
Find and document every place that depends on class ID or class count:
the bitmask function(s) and every caller, the 12-entry tables, the hardcoded class checks
(MP gain `0x06A264`, Monk/Master unarmed, Ninja/Master armor/evade quirks, etc.),
the class change event and its `+6` logic, sprite/portrait/map-graphic lookups per class,
menu layouts (2×6 class grid), and the save-data class byte.
Deliverable: `docs/class_handling.md`, a checklist of every site to patch.
Result: promotion is a lookup table (`0x21609A`), not `+6`; no central class→bit
function, so ~8 mapping sites get rewired to one new `ClassMaskBit()`.

### Phase 2 — 16-class engine (implemented; in-game check pending)
Expand and relocate the tables; patch the bitmask mapping and all class-bound code;
placeholder names and palette-swap graphics for 12–15.
Done: `data/classes16.py` (16-entry name, growth, accuracy, magic-resist, field-sprite and
graphics tables) + `src/classes16.asm` (ClassBitLo/Hi via literal repoints, battle equip
switch → ClassMaskWord, growth rows per class). `tests/test_classes16.py` runs the patched
routines in a CPU emulator against vanilla. New classes currently look and grow like
their template (DK=Knight art/Warrior growth, etc.); custom palettes come with phase 5/7.
**Milestone:** poke a character to class 12–15 with Lua → status, equip, magic menu,
battle, level-up, and save/load all work.

### Phase 3 — Bahamut branching
A yes/no prompt per eligible character during the class change event; Yes → alternate ID.

### Phase 4 — Bahamut quick start
Capture the target state by diffing save data: a real save just before Bahamut vs. a
fresh save gives the flags, inventory and position. New-game code applies the preset
after party creation when the player picks Yes.

### Phase 5 — Class content
- Spell-learn masks, equipment permissions, growth curves, MP rules for all 16 classes.
- Ninja rework (remove black magic, add to the no-MP list, katana exclusivity).
- Druid's reduced unarmed formula.
- Ranger as monster hunter: bane-weapon access, accuracy/crit, and **extra damage when a
  bane weapon hits its monster family** (ASM patch in the physical damage routine).

### Phase 6 — Balance pass
### Phase 7 — Custom graphics for the new classes
### Phase 8 — Bows for Ranger
New weapon type with its own icon glyph, new weapon entries (expand weapon table, names,
descriptions, hit-effect list, item ID bounds), battle attack graphics, shop/chest
placement. Fallback if expansion is too invasive: repurpose redundant swords.
### Phase 9 — Vancian magic

## Open decisions
- Quick-start preset: party level, gear per class, gil, which optional content is pre-cleared.
- Ranger's bane bonus size (e.g. ×1.5 on top of the normal bane effect).
- (Phase 8) Which classes besides Ranger can use bows; how many bows and where found.
- Whether Knight keeps white magic (keeps it distinct from Dark Knight).
- Exact balance-pass scope.
