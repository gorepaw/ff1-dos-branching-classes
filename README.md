# FF1 Dawn of Souls: Branching Classes

A ROM hack of the FF1 half of *Final Fantasy I & II: Dawn of Souls* (GBA, USA) that adds
four alternate class promotions at Bahamut, offered to Warrior, Thief, Monk and Red Mage:

| Base | Standard promotion | Alternate promotion |
|---|---|---|
| Warrior | Knight | **Dark Knight** |
| Thief | Ninja (reworked: pure physical) | **Ranger** (monster hunter) |
| Monk | Master | **Druid** |
| Red Mage | Red Wizard | **Spellblade** |

It also adds an optional "begin at Bahamut" quick start, per-class stat growth, and a
balance pass. See [PLAN.md](PLAN.md) for the design and roadmap and [FINDINGS.md](FINDINGS.md)
for ROM research notes.

**Status:** early development. Nothing playable yet.

## Building

You need Windows, Python 3.10+, and your own dump of the game. This repo contains no ROM
data.

1. Put `Final Fantasy I & II - Dawn of Souls (USA).gba` in the repo root
   (SHA1 `6472695d69661490f78245e2982e1e676c080be7`, any filename works).
2. `python tools/setup.py` downloads armips and Flips into `tools/bin/`.
3. `python tools/build.py` writes `build/ff1dos_classes.gba` and `build/ff1dos_classes.bps`.

For reverse-engineering work, `python tools/setup.py --ghidra` also fetches JDK 21, Ghidra
12.0.2 and the [GBA loader](https://github.com/pudii/gba-ghidra-loader); start it with
`tools\ghidra.bat`. `lua/devtools.lua` holds helper functions for mGBA's scripting console.

## Layout

```
src/     armips assembly (src/main.asm is the entry point)
data/    Python data patches, each exposing apply(rom)
tools/   build, setup, and ROM helper scripts
lua/     mGBA scripting helpers
```

## Credits

Research built on work by the Dawn of Souls hacking community:
[Data Crystal](https://datacrystal.tcrf.net/wiki/Final_Fantasy_I_%26_II:_Dawn_of_Souls),
[Jeff Ludwig (Ludmeister)](https://www.jeffludwig.com/finalfantasy/hacking-notes.php),
Kea, exline (FFI DoS Editor), and abyssonym
([Approaching Chaos](https://github.com/abyssonym/approaching_chaos)).
