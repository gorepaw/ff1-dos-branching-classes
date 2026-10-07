"""Quick Thumb disassembly: python tools/disasm.py <rom_offset_hex> [length_hex] [arm]"""
import sys
import capstone
from romlib import find_base_rom, GBA_ROM

d = find_base_rom().read_bytes()
start = int(sys.argv[1], 16) & 0xFFFFFF
length = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x80
mode = capstone.CS_MODE_ARM if "arm" in sys.argv[3:] else capstone.CS_MODE_THUMB
md = capstone.Cs(capstone.CS_ARCH_ARM, mode)
md.skipdata = True
for i in md.disasm(d[start:start + length], GBA_ROM + start):
    extra = ""
    if i.mnemonic == "ldr" and "pc" in i.op_str:  # resolve literal pool
        imm = int(i.op_str.split("#")[1].rstrip("]"), 16)
        lit = ((i.address + 4) & ~3) + imm
        extra = f"   ; ={int.from_bytes(d[lit - GBA_ROM:lit - GBA_ROM + 4], 'little'):#010x}"
    print(f"{i.address:08X}  {i.bytes.hex():8s}  {i.mnemonic} {i.op_str}{extra}")
