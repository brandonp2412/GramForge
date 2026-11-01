#!/usr/bin/env python3
"""Apply Rotta's launcher artwork to Apktool-decoded Instagram resources."""
from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

DENSITIES = ("mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi")
VARIANTS = ("icon", "foreground", "background")
ADAPTIVE = '''<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@mipmap/ig_launcher_background"/>
    <foreground android:drawable="@mipmap/ig_launcher_foreground"/>
</adaptive-icon>
'''


def artwork(assets: Path) -> list[tuple[Path, str, str]]:
    files = [(assets / f"{density}-{variant}.png", density, variant)
             for density in DENSITIES for variant in VARIANTS]
    for path, _, _ in files:
        if not path.is_file() or not path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            raise SystemExit(f"Invalid Rotta launcher image: {path}")
    return files


def fingerprint(assets: Path) -> str:
    digest = hashlib.sha256()
    for path, _, _ in artwork(assets):
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def patch(decoded: Path, assets: Path) -> None:
    xml = decoded / "res/mipmap-anydpi/icon.xml"
    if not xml.is_file():
        raise SystemExit(f"Instagram adaptive launcher resource missing: {xml}")
    original = xml.read_text()
    if "ig_launcher_background" not in original or "ig_launcher_foreground" not in original:
        raise SystemExit("Instagram adaptive launcher references changed")
    files = artwork(assets)
    destinations = []
    for source, density, variant in files:
        name = "icon" if variant == "icon" else f"ig_launcher_{variant}"
        dest = decoded / f"res/mipmap-{density}/{name}.png"
        if not dest.is_file():
            raise SystemExit(f"Instagram launcher resource missing: {dest}")
        destinations.append((source, dest))
    for source, dest in destinations:
        shutil.copyfile(source, dest)
    xml.write_text(ADAPTIVE)
    print(f"Rotta launcher applied to all densities ({fingerprint(assets)})")


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--fingerprint":
        print(fingerprint(Path(sys.argv[2])))
        return
    if len(sys.argv) != 3:
        raise SystemExit("usage: patch-launcher-icon.py [--fingerprint <assets> | <decoded> <assets>]")
    patch(Path(sys.argv[1]), Path(sys.argv[2]))


if __name__ == "__main__":
    main()
