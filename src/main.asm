; FF1 Dawn of Souls (USA) - branching classes hack
; Assembled by tools/build.py after the Python data patches are applied.
; ROMFILE is passed on the command line (-strequ ROMFILE <path>).

.gba
.thumb
.open ROMFILE, 0x08000000

; ---------------------------------------------------------------------------
; Free space: 0x08EE0760 - 0x08FFFFFF is 0xFF padding (~1.1 MiB).
;   0x08EE0800 - 0x08EE0FFF  new code (this file and its includes)
;   0x08EE1000 - ...         tables built by data/*.py (romlib.FREE_DATA)
; Hooks overwrite vanilla code in place; new code goes in the code area.
; ---------------------------------------------------------------------------
.definelabel FreeSpace,        0x08EE0800
.definelabel FreeSpaceCodeEnd, 0x08EE1000

.include "src/classes16.asm"   ; phase 2: 16-class engine

.close
