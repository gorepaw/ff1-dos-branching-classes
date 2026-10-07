"""Run patched ROM routines in a CPU emulator and compare against vanilla.

    python tests/test_classes16.py      (build first: python tools/build.py)
"""
import struct
import sys
from pathlib import Path

from unicorn import UC_ARCH_ARM, UC_HOOK_INTR, UC_MODE_THUMB, Uc
from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1,
                               UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from romlib import find_base_rom  # noqa: E402

STOP = 0x02000100  # return address; emulation stops when execution reaches it


class Cpu:
    def __init__(self, rom):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.uc.mem_map(0x02000000, 0x40000)   # EWRAM
        self.uc.mem_map(0x03000000, 0x8000)    # IWRAM
        self.uc.mem_map(0x08000000, len(rom))
        self.uc.mem_write(0x08000000, bytes(rom))
        self.uc.hook_add(UC_HOOK_INTR, self._bios)

    def _bios(self, uc, intno, _):
        # Only BIOS Div (svc 6) is needed: r0 = r0 / r1, r1 = r0 % r1, r3 = |quotient|
        pc = uc.reg_read(UC_ARM_REG_PC)
        svc = uc.mem_read(pc - 2, 1)[0]
        if svc != 6:
            raise RuntimeError(f"unhandled svc {svc:#x} at {pc:#x}")
        n, d = uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)
        uc.reg_write(UC_ARM_REG_R0, n // d)
        uc.reg_write(UC_ARM_REG_R1, n % d)
        uc.reg_write(UC_ARM_REG_R3, n // d)

    def call(self, addr, *args):
        regs = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2]
        for r, v in zip(regs, args):
            self.uc.reg_write(r, v)
        self.uc.reg_write(UC_ARM_REG_SP, 0x03007F00)
        self.uc.reg_write(UC_ARM_REG_LR, STOP | 1)
        self.uc.emu_start(addr | 1, STOP, count=100000)
        return self.uc.reg_read(UC_ARM_REG_R0)


def symbols():
    syms = {}
    for line in (ROOT / "build" / "ff1dos_classes.sym").read_text().splitlines():
        parts = line.split()
        if len(parts) == 2 and not parts[1].startswith("."):
            syms[parts[1].lower()] = int(parts[0], 16)
    return syms


EXPECTED_BIT = [0, 1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13, 6, 7, 14, 15]
BASE = [0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5, 0, 1, 2, 3]

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)


def main():
    vanilla = Cpu(find_base_rom().read_bytes())
    hacked = Cpu((ROOT / "build" / "ff1dos_classes.gba").read_bytes())
    s = symbols()

    for c in range(16):
        lo, hi = hacked.call(s["classbitlo"], c, 6), hacked.call(s["classbithi"], c, 6)
        check(lo + hi * 8 == EXPECTED_BIT[c], f"ClassBitLo/Hi({c}) -> bit {lo + hi * 8}")
        check(hacked.call(s["classmaskword"], c) == 1 << EXPECTED_BIT[c], f"ClassMaskWord({c})")
        check(hacked.call(s["classbase"], c) == BASE[c], f"ClassBase({c})")
        check(hacked.call(s["classself"], c) == c, f"ClassSelf({c})")

    # 0x080456A4: can class r1 use spell r2 (bit test on the spell-learn mask table)
    for spell in range(1, 65):
        for c in range(12):
            v, h = vanilla.call(0x080456A4, 0, c, spell), hacked.call(0x080456A4, 0, c, spell)
            check(v == h, f"spell usability spell={spell} class={c}: vanilla {v} hacked {h}")
        for c in range(12, 16):
            mask = struct.unpack_from("<H", find_base_rom().read_bytes(), 0x1A20C0 + spell * 2)[0]
            want = mask >> EXPECTED_BIT[c] & 1
            check(hacked.call(0x080456A4, 0, c, spell) == want, f"spell usability spell={spell} class={c}")

    # 0x0806A324: growth bit for (class, level, stat). New layout gives every class its own
    # row; rows start as copies of the base class, so results must match vanilla's c % 6.
    for c in range(16):
        for level in (2, 10, 50, 99):
            for stat in range(8):
                v = vanilla.call(0x0806A324, BASE[c], level, stat)
                h = hacked.call(0x0806A324, c, level, stat)
                check(v == h, f"growth class={c} lv={level} stat={stat}: vanilla {v} hacked {h}")

    if failures:
        print(f"FAIL: {len(failures)} checks")
        for f in failures[:30]:
            print("  ", f)
        sys.exit(1)
    print("all checks passed")


if __name__ == "__main__":
    main()
