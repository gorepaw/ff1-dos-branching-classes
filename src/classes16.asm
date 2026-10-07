; Phase 2: 16-class engine - class ID -> permission mask bit, and per-class growth rows.
;
; Vanilla turns a class ID into its u16 mask bit with library calls:
;     bit = (class % 6) + (class / 6) * 8         ; 0-5 -> bits 0-5, 6-11 -> bits 8-13
; Each site loads the mod/div helper's address from its own literal-pool slot, so
; repointing those slots to ClassBitLo/ClassBitHi changes the mapping without touching
; the sites. Classes 12-15 map to the free bits 6, 7, 14, 15:
;     12 Dark Knight -> 6   13 Ranger -> 7   14 Druid -> 14   15 Spellblade -> 15
; The tables themselves are expanded by data/classes16.py.

; Overwrite a 32-bit word after checking it still holds the vanilla value.
.macro patchword,addr,expected,value
    .if readu32(ROMFILE, addr - 0x08000000) != expected
        .error "patchword: unexpected value at " + tohex(addr)
    .endif
    .org addr
    .word value
.endmacro

; Overwrite code after checking the halfword at addr.
.macro checkhalf,addr,expected
    .if readu16(ROMFILE, addr - 0x08000000) != expected
        .error "checkhalf: unexpected code at " + tohex(addr)
    .endif
.endmacro

.definelabel LibMod6Lit, 0x08000F2D   ; library remainder routine (Thumb)
.definelabel LibDiv6Lit, 0x08000F19   ; library divide routine (Thumb)
.definelabel LibModAlt,  0x08000F0D   ; second remainder entry used by the spell code
.definelabel LibDivAlt,  0x08000F05
.definelabel VeneerBxR1, 0x0818C250   ; "bx r1" trampoline

; ---------------------------------------------------------------------------
; New code (free space)
; ---------------------------------------------------------------------------
.org FreeSpace
.area FreeSpaceCodeEnd - FreeSpace

.align 4
; r0 = class -> r0 = low part of mask bit (vanilla: class % 6). Uses r0, r1 only.
ClassBitLo:
    cmp     r0, 6
    blo     @@done
    cmp     r0, 12
    bhs     @@new
    sub     r0, 6
@@done:
    bx      lr
@@new:
    mov     r1, 1
    and     r0, r1
    add     r0, 6
    bx      lr

; r0 = class -> r0 = high part of mask bit (vanilla: class / 6). Uses r0 only.
ClassBitHi:
    cmp     r0, 6
    blo     @@zero
    cmp     r0, 12
    bhs     @@new
    mov     r0, 1
    bx      lr
@@zero:
    mov     r0, 0
    bx      lr
@@new:
    sub     r0, 12
    lsr     r0, r0, 1
    bx      lr

; r0 = class -> r0 = class. Replaces "class % 6" where a per-class row is wanted.
ClassSelf:
    bx      lr

; r0 = class -> r0 = base class (0-5). Vanilla: class % 6.
ClassBase:
    cmp     r0, 6
    blo     @@done
    cmp     r0, 12
    bhs     @@new
    sub     r0, 6
    bx      lr
@@new:
    sub     r0, 12
@@done:
    bx      lr

; r0 = class -> r0 = 1 << mask bit. Uses r0, r1 only.
ClassMaskWord:
    cmp     r0, 6
    blo     @@shift
    cmp     r0, 12
    bhs     @@new
    add     r0, 2               ; 6-11 -> bits 8-13
    b       @@shift
@@new:
    sub     r0, 12              ; 0-3
    cmp     r0, 2
    blo     @@low
    add     r0, 6               ; 2,3 -> 8,9
@@low:
    add     r0, 6               ; -> 6,7,14,15
@@shift:
    mov     r1, 1
    lsl     r1, r0
    mov     r0, r1
    bx      lr

.endarea

; ---------------------------------------------------------------------------
; Class -> mask bit sites: repoint each site's mod/div helper literal.
; (Each slot is loaded by exactly one instruction; checked in phase 1.)
; ---------------------------------------------------------------------------
.macro maskbit_site,modlit,divlit,modval,divval
    patchword modlit, modval, ClassBitLo|1
    patchword divlit, divval, ClassBitHi|1
.endmacro

maskbit_site 0x080316D0, 0x080316D4, LibMod6Lit, LibDiv6Lit   ; field equip menu
maskbit_site 0x080317E8, 0x080317EC, LibMod6Lit, LibDiv6Lit   ; field equip menu
maskbit_site 0x080323F8, 0x080323FC, LibMod6Lit, LibDiv6Lit   ; equip menu class grid
maskbit_site 0x080324DC, 0x080324E0, LibMod6Lit, LibDiv6Lit   ; equip menu class grid
maskbit_site 0x08034AC4, 0x08034AC8, LibMod6Lit, LibDiv6Lit   ; equip check
maskbit_site 0x080449E8, 0x080449EC, LibMod6Lit, LibDiv6Lit   ; shop: can equip
maskbit_site 0x0804562C, 0x08045630, LibModAlt, LibDivAlt     ; spell shop: can learn
maskbit_site 0x080456DC, 0x080456E0, LibModAlt, LibDivAlt     ; spell usability

; Battle equip menu (0x0806CBD4): replace the inline 12-case switch
;     cmp r0,#11 / bhi default / jump table
; with  r0 = ClassMaskWord(r0)  then continue at the switch's join point.
checkhalf 0x0806CBFE, 0x280B    ; cmp r0, #0xB
.org 0x0806CBFE
    ldr     r1, =ClassMaskWord|1
    bl      VeneerBxR1
    b       0x0806CC82
    .pool

; ---------------------------------------------------------------------------
; Growth rows: one row per class instead of class % 6 (table built in Python).
; ---------------------------------------------------------------------------
; 0x0806A190 (level-up stat gain): "movs r1,#6 ; bl mod" -> nops, leaving r0 = class.
; The mod helper there is also used for a random roll, so its literal stays.
checkhalf 0x0806A1B8, 0x2106    ; movs r1, #6
.org 0x0806A1B8
    nop
    nop
    nop

patchword 0x0806A364, LibMod6Lit, ClassSelf|1   ; growth-bit helper (0x0806A324)
patchword 0x0806A384, LibMod6Lit, ClassBase|1   ; base-class helper (0x0806A36C)
