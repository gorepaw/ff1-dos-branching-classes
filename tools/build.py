"""Build the hacked ROM and BPS patch.

    python tools/build.py

Steps: clean ROM -> data patches (data/*.py, each exposing apply(rom)) ->
armips (src/main.asm) -> build/ff1dos_classes.gba + build/ff1dos_classes.bps
"""
import importlib.util
import subprocess
import sys

from romlib import ROOT, find_base_rom, sha1

BIN = ROOT / "tools" / "bin"
BUILD = ROOT / "build"
OUT_ROM = BUILD / "ff1dos_classes.gba"
OUT_BPS = BUILD / "ff1dos_classes.bps"


def run_data_patches(rom):
    for path in sorted((ROOT / "data").glob("*.py")):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        print(f"data: {path.name}")
        mod.apply(rom)


def main():
    for exe in ("armips/armips.exe", "flips/flips.exe"):
        if not (BIN / exe).exists():
            sys.exit(f"missing tools/bin/{exe} - run: python tools/setup.py")

    base = find_base_rom()
    rom = bytearray(base.read_bytes())
    run_data_patches(rom)

    BUILD.mkdir(exist_ok=True)
    OUT_ROM.write_bytes(rom)

    rel_rom = OUT_ROM.relative_to(ROOT).as_posix()
    subprocess.run([str(BIN / "armips/armips.exe"), "src/main.asm", "-strequ", "ROMFILE", rel_rom],
                   cwd=ROOT, check=True)

    OUT_BPS.unlink(missing_ok=True)
    subprocess.run([str(BIN / "flips/flips.exe"), "--create", "--bps-delta",
                    str(base), str(OUT_ROM), str(OUT_BPS)], check=True, stdout=subprocess.DEVNULL)

    out = OUT_ROM.read_bytes()
    changed = sum(a != b for a, b in zip(out, base.read_bytes())) + abs(len(out) - base.stat().st_size)
    print(f"built {OUT_ROM.relative_to(ROOT)}  sha1 {sha1(out)}  ({changed} bytes differ from base)")
    print(f"patch {OUT_BPS.relative_to(ROOT)}  ({OUT_BPS.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
