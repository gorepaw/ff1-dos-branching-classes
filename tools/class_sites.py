"""Collect function entry points that touch class data, for batch decompiling.
Writes ghidra/class_funcs.txt (one address per line, with the reason)."""
import re
import struct
import subprocess
import sys

from romlib import ROOT, find_base_rom, CLASS_NAME_PTRS, BASE_STATS_TABLE, LEVELUP_TABLE, SPELL_LEARN_TABLE

d = find_base_rom().read_bytes()
TABLES = {"class_names": CLASS_NAME_PTRS, "base_stats": [BASE_STATS_TABLE], "levelup": [LEVELUP_TABLE],
          "lvl_acc": [0x226FD6], "lvl_mres": [0x226FE2], "spell_learn": [SPELL_LEARN_TABLE]}


def func_start(a):
    """Walk back to the nearest `push {..., lr}`."""
    for b in range(a & ~1, max(0, a - 0x2000), -2):
        if d[b + 1] == 0xB5:
            return b
    return None


reasons = {}
out = subprocess.run([sys.executable, str(ROOT / "tools" / "scan_div6.py")], capture_output=True,
                     text=True, check=True).stdout
for line in out.splitlines():
    m = re.match(r"([0-9A-F]{8})\s+(\S+)", line)
    if m:
        a = int(m.group(1), 16) - 0x08000000
        s = func_start(a)
        if s is not None:
            reasons.setdefault(s, set()).add("div6")

for name, tables in TABLES.items():
    for t in tables:
        for m in re.finditer(re.escape(struct.pack("<I", 0x08000000 + t)), d):
            s = func_start(m.start())  # literal pool sits after its function
            if s is not None:
                reasons.setdefault(s, set()).add(name)

path = ROOT / "ghidra" / "class_funcs.txt"
with open(path, "w") as f:
    for s in sorted(reasons):
        f.write(f"{0x08000000 + s:08X}  # {','.join(sorted(reasons[s]))}\n")
print(f"{len(reasons)} functions -> {path}")
