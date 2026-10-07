# Class handling in FF1 (Dawn of Souls, USA)

Phase 1 deliverable: every place the game depends on the class ID or on there being
12 classes, i.e. everything phase 2 must patch to support classes 12–15.

Addresses are GBA bus addresses (ROM offset + `0x08000000`). Function addresses are
entry points as decompiled by Ghidra (`python tools/ghidra.py decomp out.c <addr>`).

## How this list was built
1. `tools/scan_div6.py`: every call to the library divide/modulo helpers with divisor 6,
   which is how the game turns a class ID into a mask bit (`(c%6) + (c/6)*8`) or into a
   base class (`c%6`).
2. Every code reference to a per-class table (names, base stats, growth, accuracy, magic
   resist, spell-learn masks); see `tools/class_sites.py`.
3. A decompile of all 1,523 functions in `0x08000000–0x08080000` (the FF1 code range),
   grepped for reads of the class byte (`+0x0D` of the `0x48`-byte character struct).
   Battle code has no separate class field; it reads the party struct directly.

## Character struct (`0x48` bytes, party at `0x020026CC`)
| Off | Field | Off | Field |
|---|---|---|---|
| `00–0B` | name (6 Shift-JIS chars) | `1C` | spell-level cap |
| `0D` | **class** | `1D–21` | STR, AGI, INT, STA, LCK |
| `0E` | level − 1 | `22/24/26` | accuracy, evade, magic def (u16) |
| `10` | EXP (u32) | `28` | weapon slot |
| `14/16` | HP cur/max | `29–2C` | armor slots (body `2B`) |
| `18/1A` | MP cur/max | `2D–44` | learned spells, 8 levels × 3 |

## A. Class → mask bit (equip / spell-learn permissions)
The u16 masks use bit `(c%6) + (c/6)*8`, so classes 12–15 would land on bits 16+.
Phase 2 replaces every site with a call to one `ClassMaskBit(class)` function that maps
12–15 to bits 6, 7, 14, 15.

| Function | What |
|---|---|
| `080315E0` | field equip menu: can-equip checks (2 sites) |
| `080319C8` | field equip menu: class grid of who can equip (loops 12 slots, 2×6 layout) |
| `08034A3C` | equip check with class passed in |
| `08044974` | shop: can this character equip the item |
| `080454E4` | spell shop: can purchaser learn this spell |
| `080456A4` | class usability for given spell |
| `0806CBD4` | **battle** equip menu: inline `switch` class → bit (cases 0–11) |
| `0807329C` | unused "equip bit for class" jump table (dead code; free to reuse) |

## B. Class → base class (`class % 6`)
| Function | What |
|---|---|
| `0806A190` | level-up gain per stat: growth row = `levelup[(c%6)*99 + lv-2]` |
| `0806A324`, `0806A36C` | level-up helpers, same `% 6` row lookup |

## C. Per-class tables (all need 16 entries, relocated to free space)
| Table | ROM | Size | Read by |
|---|---|---|---|
| Class names ×3 | ptrs `1DA938`, `1E0980`, `1E1490` | 12 ptrs each | menus (`033560`, `03782C`, `03848C`, `038918`, `045F9C`), party creation (`04DC30`, `04DD60`) |
| Base stats | `1E1354` | 6 × 16 B | new-game init `04E580` (only base classes need entries) |
| Level-up growth | `223ADC` | 6 × 99 B | `06A190`, `06A324` → becomes 16 × 99 |
| Level accuracy | `226FD6` | 12 B | root level-up `072358` |
| Level magic resist | `226FE2` | 12 B | root level-up `072358` |
| **Promotion** | `21609A` | `06 07 08 09 0A 0B` | class change `05E654` |
| Field sprite ID | `21608E` | 12 B (`95 97 … A0`) | class change `05E654` |
| Class graphics (3 ptrs each, 12 B/class) | via RAM ptr `0200035C` | 12 × 12 B | `01FB58`, `01FF8C`, `0292F8`, `0319C8`, `039348`, `039908`, `073554` |

## D. Hardcoded class rules (become table lookups or explicit new cases)
| Function | Rule | Classes |
|---|---|---|
| `0801591C` total attack | unarmed: Monk formula / Master formula; armed: +1 for Monk, BlM, Master, BlW | 2, 8 / 2, 5, 8, 11 |
| `080159B4` total defense | unarmored bonuses per empty slot | Monk 2, Master 8 |
| `08071EC8`, `0807672C` battle stats | unarmed: hit count from STA, attack ×2 | Monk 2, Master 8 |
| `0806A190` level-up | no MP gain | 0, 1, 2, 8 |
| `0806A190` level-up | growth stat #7: +3 / +4 / +1 | War+Knight / Thf+Ninja / others |
| `08038918`, `08039588` status | max spell level: 0/3/4/6/7/8 | per class (`switch`) |
| `0804B2F4` party creation | default party classes 0, 1, 4, 5; loops `< 0xC` | — |

## E. Class change (Bahamut)
`0805E654` loops over the 4 characters: `class = promo[class]` (table `21609A`), then
sets the leader's field sprite from table `21608E`. No `+6` arithmetic.
Branching plan: per-character flag (set by the yes/no prompt) → use an alternate promo
table (`War→12, Thf→13, Mnk→14, RdM→15`).

## Still to map (early phase 2)
- ROM source of the class graphics table behind `0200035C`; battle sprites, portraits,
  and field sprites for the new classes (palette-swap placeholders).
- What growth stat #7 is (the +3/+4/+1 values suggest hit% rather than spell level).
- The Bahamut event script that calls `0805E654`, and the yes/no dialog command, for phase 3.
- Party creation menu layout (`04B2F4`, `04DC30`, `04DD60`) to confirm it stays 6 choices.
- Runtime check of all of the above in mGBA (party address, struct offsets).
