#!/usr/bin/env python3
"""Rewrite an APK ZIP with consistent local/central-directory metadata."""
from __future__ import annotations
import sys
import zipfile
from pathlib import Path

def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: normalize-apk.py <input.apk> <output.apk>")
    source, target = map(Path, sys.argv[1:])
    if source.resolve() == target.resolve():
        raise SystemExit("input and output must differ")
    seen: set[str] = set()
    with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(target, "w", allowZip64=True) as zout:
        for info in zin.infolist():
            if info.filename in seen:
                raise SystemExit(f"duplicate ZIP entry: {info.filename}")
            seen.add(info.filename)
            data = zin.read(info.filename)
            clean = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            clean.compress_type = info.compress_type
            clean.comment = info.comment
            clean.internal_attr = info.internal_attr
            clean.external_attr = info.external_attr
            clean.create_system = info.create_system
            zout.writestr(clean, data, compress_type=info.compress_type)

if __name__ == "__main__":
    main()
