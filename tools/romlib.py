"""Shared helpers for reading/writing the FF1&2 Dawn of Souls (USA) ROM."""
import hashlib
import struct
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BASE_SHA1 = "6472695d69661490f78245e2982e1e676c080be7"
BASE_SIZE = 0x1000000
GBA_ROM = 0x08000000

# Known FF1 offsets (ROM file offsets). See FINDINGS.md.
CLASS_NAME_PTRS = (0x1DA938, 0x1E0980, 0x1E1490)  # 12 pointers each
WEAPON_TABLE, WEAPON_COUNT, WEAPON_SIZE = 0x19F33C, 65, 28
ARMOR_TABLE, ARMOR_COUNT, ARMOR_SIZE = 0x19FA58, 71, 28
SPELL_TABLE, SPELL_COUNT, SPELL_SIZE = 0x1A1980, 116, 16
SPELL_LEARN_TABLE = 0x1A20C0  # u16 class mask per spell
BASE_STATS_TABLE, BASE_STATS_SIZE = 0x1E1354, 16  # 6 entries
LEVELUP_TABLE = 0x223ADC  # 6 classes x 99 levels, 1 byte each
WEAPON_NAMES = 0x19A65A
SPELL_NAMES = 0x1A021D
FREE_SPACE = 0xEE0760  # 0xFF-filled to end of ROM

CLASSES = ["Warrior", "Thief", "Monk", "Red Mage", "White Mage", "Black Mage",
           "Knight", "Ninja", "Master", "Red Wizard", "White Wizard", "Black Wizard"]


def find_base_rom():
    """Return the path of a clean USA ROM in the repo root, verified by SHA1."""
    for p in sorted(ROOT.glob("*.gba")):
        if p.stat().st_size == BASE_SIZE and sha1(p.read_bytes()) == BASE_SHA1:
            return p
    raise SystemExit(
        "No clean ROM found. Put 'Final Fantasy I & II - Dawn of Souls (USA).gba' "
        f"(SHA1 {BASE_SHA1}) in {ROOT}")


def sha1(data):
    return hashlib.sha1(data).hexdigest()


def class_bit(class_id):
    """Bit index used by the game's u16 class masks (vanilla: (id/6)*8 + id%6)."""
    if class_id < 12:
        return (class_id // 6) * 8 + class_id % 6
    return (6, 7, 14, 15)[class_id - 12]  # planned mapping for new classes 12-15


def u16(d, o):
    return struct.unpack_from("<H", d, o)[0]


def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def read_str(d, o):
    """Read a null-terminated Shift-JIS string; returns (text, next_offset)."""
    end = d.index(b"\0", o)
    return unicodedata.normalize("NFKC", d[o:end].decode("cp932", "replace")), end + 1


def read_strs(d, o, n):
    out = []
    for _ in range(n):
        s, o = read_str(d, o)
        out.append(s)
    return out


def encode_str(text):
    """Encode ASCII text as full-width Shift-JIS, null-terminated (game's text format)."""
    fw = "".join("　" if c == " " else chr(ord(c) + 0xFEE0) if "!" <= c <= "~" else c
                 for c in text)
    return fw.encode("cp932") + b"\0"
