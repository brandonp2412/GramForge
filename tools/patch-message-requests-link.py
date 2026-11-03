#!/usr/bin/env python3
"""Hide Requests navigation entry in Instagram's Direct inbox (454).

Drops only the inbox_requests menu item while retaining its folder and data.
Fail closed when Instagram's Smali structure changes.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


class PatchMismatch(Exception):
    pass


METHOD_RE = re.compile(r"(?ms)^\.method public final A06\(\)V\n.*?^\.end method$")
REQUEST_TITLE = "    const v7, 0x7f133e2b"
REQUEST_MODE = "    sget-object v14, LX/01tK;->A00:LX/01tK;"
REQUEST_CONSTRUCTOR = (
    "    invoke-direct/range {v12 .. v22}, LX/0X7V;-><init>"
    "(LX/0RDO;LX/06Zx;Ljava/lang/Integer;Ljava/lang/Integer;"
    "Ljava/lang/Integer;Ljava/lang/Integer;Ljava/util/Set;ZZZ)V"
)
REQUEST_ADD = (
    "    invoke-virtual {v0, v12}, "
    "Ljava/util/AbstractCollection;->add(Ljava/lang/Object;)Z\n"
)
LIST_COMMIT = "    new-instance v5, LX/05Ku;"


def transform(source: str) -> str:
    if ".class public final LX/05PM;" not in source:
        raise PatchMismatch("Direct inbox navigation class changed")
    matches = list(METHOD_RE.finditer(source))
    if len(matches) != 1:
        raise PatchMismatch(f"expected one inbox navigation builder, found {len(matches)}")
    method = matches[0].group()
    for marker in (REQUEST_TITLE, REQUEST_MODE, REQUEST_CONSTRUCTOR, LIST_COMMIT):
        if method.count(marker) != 1:
            raise PatchMismatch(f"Requests navigation fingerprint missing/duplicated: {marker}")
    title = method.index(REQUEST_TITLE)
    mode = method.index(REQUEST_MODE)
    constructor = method.index(REQUEST_CONSTRUCTOR)
    list_commit = method.index(LIST_COMMIT)
    additions = [m.start() for m in re.finditer(re.escape(REQUEST_ADD), method)]
    if len(additions) != 1 or not (title < mode < constructor < additions[0] < list_commit):
        raise PatchMismatch("Requests navigation insertion changed")
    updated = method.replace(REQUEST_ADD, "", 1)
    return source[:matches[0].start()] + updated + source[matches[0].end():]


def patch(root: Path, *, check: bool = False) -> Path:
    if not root.is_dir():
        raise PatchMismatch(f"decoded APK missing: {root}")
    paths = list(root.rglob("05PM.smali"))
    if len(paths) != 1:
        raise PatchMismatch(f"expected one Direct inbox navigation class, found {len(paths)}")
    path = paths[0]
    updated = transform(path.read_text())
    if not check:
        path.write_text(updated)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded_apk", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        patch(args.decoded_apk, check=args.check)
    except PatchMismatch as exc:
        parser.exit(1, f"ERROR: Message Requests link patch incompatible: {exc}\n")
    print("GramForge Message Requests link " + ("verified" if args.check else "hidden"))
