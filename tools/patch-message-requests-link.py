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
PRIMARY_CLASS = ".class public final LX/0RDL;"
PRIMARY_METHOD_RE = re.compile(
    r"(?ms)^\.method public final A01\(Lcom/instagram/common/session/UserSession;"
    r"LX/06Zx;LX/0Jnp;IZZZ\)LX/05Ku;\n.*?^\.end method$"
)
PRIMARY_REQUEST_MODE = "    sget-object v6, LX/01tK;->A00:LX/01tK;"
PRIMARY_CONSTRUCTOR = (
    "    invoke-direct/range {v21 .. v31}, LX/0X7V;-><init>"
    "(LX/0RDO;LX/06Zx;Ljava/lang/Integer;Ljava/lang/Integer;"
    "Ljava/lang/Integer;Ljava/lang/Integer;Ljava/util/Set;ZZZ)V"
)
PRIMARY_ADD = (
    "    invoke-virtual {v7, v1}, "
    "Ljava/util/AbstractCollection;->add(Ljava/lang/Object;)Z"
)
PRIMARY_SKIP = """    iget-object v2, v4, Landroid/util/Pair;->second:Ljava/lang/Object;

    sget-object v3, LX/01tK;->A00:LX/01tK;

    invoke-static {v2, v3}, LX/00d6;->areEqual(Ljava/lang/Object;Ljava/lang/Object;)Z

    move-result v2

    if-nez v2, :goto_4

"""


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


def transform_primary(source: str) -> str:
    """Omit Requests from the live folder list built by A07 -> 0RDL.A01."""
    if PRIMARY_CLASS not in source:
        raise PatchMismatch("primary Direct inbox navigation class changed")
    matches = list(PRIMARY_METHOD_RE.finditer(source))
    if len(matches) != 1:
        raise PatchMismatch(f"expected one primary inbox builder, found {len(matches)}")
    method = matches[0].group()
    for marker in (PRIMARY_REQUEST_MODE, PRIMARY_CONSTRUCTOR, PRIMARY_ADD):
        if method.count(marker) != 1:
            raise PatchMismatch(f"primary Requests fingerprint missing/duplicated: {marker}")
    mode = method.index(PRIMARY_REQUEST_MODE)
    constructor = method.index(PRIMARY_CONSTRUCTOR)
    addition = method.index(PRIMARY_ADD)
    if not (mode < constructor < addition < method.index("    goto/16 :goto_4", addition)):
        raise PatchMismatch("primary Requests navigation insertion changed")
    updated = method.replace(PRIMARY_ADD, PRIMARY_SKIP + PRIMARY_ADD, 1)
    return source[:matches[0].start()] + updated + source[matches[0].end():]


def patch(root: Path, *, check: bool = False) -> Path:
    if not root.is_dir():
        raise PatchMismatch(f"decoded APK missing: {root}")
    legacy_paths = list(root.rglob("05PM.smali"))
    primary_paths = list(root.rglob("0RDL.smali"))
    if len(legacy_paths) != 1 or len(primary_paths) != 1:
        raise PatchMismatch(
            "expected exactly one of each Direct inbox navigation builder; "
            f"found {len(legacy_paths)} legacy and {len(primary_paths)} primary"
        )
    # Validate both paths before writing either one, so an upstream mismatch
    # cannot leave the decoded APK half-patched.
    legacy_path, primary_path = legacy_paths[0], primary_paths[0]
    legacy_updated = transform(legacy_path.read_text())
    primary_updated = transform_primary(primary_path.read_text())
    if not check:
        legacy_path.write_text(legacy_updated)
        primary_path.write_text(primary_updated)
    return primary_path


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
