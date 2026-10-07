"""Run the local Ghidra with the local JDK 21 (run `python tools/setup.py --ghidra` first).

    python tools/ghidra.py                 # GUI
    python tools/ghidra.py import          # import ROM into ghidra/ff1dos (no auto-analysis;
                                           # full analysis takes hours and mistakes data for code)
    python tools/ghidra.py script X.java [args]   # run tools/ghidra_scripts/X.java on the project
    python tools/ghidra.py decomp out.c addr...   # decompile functions at addresses (or @listfile)

Environment variables whose names aren't plain identifiers are dropped, because
Ghidra's launcher crashes on them.
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from romlib import ROOT, find_base_rom

BIN = ROOT / "tools" / "bin"
PROJECT_DIR = ROOT / "ghidra"
PROJECT = "ff1dos"


def env():
    e = {k: v for k, v in os.environ.items() if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_()]*", k)}
    jdk = next((BIN / "jdk21").glob("jdk-*"))
    e["JAVA_HOME"] = str(jdk)
    e["PATH"] = str(jdk / "bin") + os.pathsep + e.get("PATH", "")
    return e


def ghidra_dir():
    return next((BIN / "ghidra").glob("ghidra_*"))


def headless(*args):
    cmd = [str(ghidra_dir() / "support" / "analyzeHeadless.bat"), str(PROJECT_DIR), PROJECT, *args]
    return subprocess.run(cmd, env=env()).returncode


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "gui"
    PROJECT_DIR.mkdir(exist_ok=True)
    if mode == "gui":
        subprocess.Popen([str(ghidra_dir() / "ghidraRun.bat")], env=env())
    elif mode == "import":
        # Ghidra's .bat launcher can't handle '&' in paths, so import a plainly named copy
        rom = PROJECT_DIR / "ff1dos.gba"
        shutil.copy(find_base_rom(), rom)
        sys.exit(headless("-import", str(rom), "-loader", "GBALoader", "-overwrite", "-noanalysis"))
    elif mode in ("script", "decomp"):
        script = sys.argv[2:] if mode == "script" else ["DecompileAt.java", *sys.argv[2:]]
        script = [str(Path(a).resolve()) if a.endswith(".c") else a for a in script]
        sys.exit(headless("-process", "ff1dos.gba", "-noanalysis",
                          "-scriptPath", str(ROOT / "tools" / "ghidra_scripts"),
                          "-postScript", *script))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
