; FF1 Dawn of Souls (USA) - branching classes hack
; Assembled by tools/build.py after the Python data patches are applied.
; ROMFILE is passed on the command line (-strequ ROMFILE <path>).

.gba
.thumb
.open ROMFILE, 0x08000000

; ---------------------------------------------------------------------------
; Free space: 0x08EE0760 - 0x08FFFFFF is 0xFF padding (~1.1 MiB).
; Hooks overwrite vanilla code in place; new code and relocated tables go in
; free space. Each feature gets its own file and its own fixed slice of free
; space, so the layout doesn't shift when one feature grows.
; ---------------------------------------------------------------------------
.definelabel FreeSpace,    0x08EE0800
.definelabel FreeSpaceEnd, 0x09000000

; .include "src/classes16.asm"   ; phase 2

.close
