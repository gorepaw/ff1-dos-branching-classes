"""Download the Windows toolchain into tools/bin/ (git-ignored).

    python tools/setup.py            # armips + Flips (needed to build)
    python tools/setup.py --ghidra   # also JDK 21 + Ghidra 12.0.2 + GBA loader (for RE work)
"""
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

BIN = Path(__file__).resolve().parent / "bin"
DL = BIN / "dl"

BUILD_TOOLS = {
    "armips": ("https://github.com/Kingcom/armips/releases/download/v0.11.0/"
               "armips-v0.11.0-windows-x86.7z", "armips.7z"),
    "flips": ("https://github.com/Sir-Walrus/Flips/releases/download/v198/flips-windows.zip",
              "flips.zip"),
}
RE_TOOLS = {
    "jdk21": ("https://github.com/adoptium/temurin21-binaries/releases/download/"
              "jdk-21.0.9%2B10/OpenJDK21U-jdk_x64_windows_hotspot_21.0.9_10.zip", "jdk21.zip"),
    "ghidra": ("https://github.com/NationalSecurityAgency/ghidra/releases/download/"
               "Ghidra_12.0.2_build/ghidra_12.0.2_PUBLIC_20260129.zip", "ghidra.zip"),
    "gbaloader": ("https://github.com/pudii/gba-ghidra-loader/releases/download/1.1.0/"
                  "ghidra_12.0.2_PUBLIC_20260209_gba-ghidra-loader.zip", "gbaloader.zip"),
}


def fetch(url, name):
    dest = DL / name
    if not dest.exists():
        print(f"downloading {name} ...")
        DL.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url) as r, open(dest, "wb") as f:
            shutil.copyfileobj(r, f)
    return dest


def extract(archive, target):
    if target.exists():
        return
    print(f"extracting {archive.name} -> {target.name}/")
    if archive.suffix == ".7z":
        target.mkdir(parents=True)
        subprocess.run(["tar", "-xf", str(archive), "-C", str(target)], check=True)
    else:
        with zipfile.ZipFile(archive) as z:
            z.extractall(target)


def main():
    tools = dict(BUILD_TOOLS)
    if "--ghidra" in sys.argv:
        tools.update(RE_TOOLS)
    for name, (url, fname) in tools.items():
        if name == "gbaloader":
            # Extensions unzipped into Ghidra/Extensions are installed automatically
            ghidra = next((BIN / "ghidra").glob("ghidra_*"))
            ext = ghidra / "Ghidra" / "Extensions"
            if not (ext / "gba-ghidra-loader").exists():
                with zipfile.ZipFile(fetch(url, fname)) as z:
                    z.extractall(ext)
            continue
        extract(fetch(url, fname), BIN / name)
    print("done:", ", ".join(tools))


if __name__ == "__main__":
    main()
