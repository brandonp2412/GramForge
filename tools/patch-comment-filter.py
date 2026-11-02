#!/usr/bin/env python3
"""Hide Instagram comment rows containing "your page", case-insensitively.

Targets the Compose CommentRow that renders regular comments and replies.
Matches the actual comment body, never the author, caption or surrounding UI.
Refuses to patch a changed renderer rather than silently shipping unfiltered.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


class PatchMismatch(Exception):
    pass


MARKER = "com.instagram.comments.mvvm.view.compose.CommentRow (CommentRow.kt:"
METHOD_HEADER = (
    ".method public static final "
    "A00(LX/1BaO;LX/05n4;LX/0Il1;LX/0Hxu;LX/0iom;LX/0Hes;IIZZZZZ)V"
)
MODEL_FIELD = "LX/0Il1;->A0O:Ljava/lang/String;"
ANCHOR = (
    "    invoke-static {v5, v10}, LX/00d6;->A0V(Ljava/lang/Object;I)V\n\n"
    "    const/4 v14, 0x1"
)
METHOD_RE = re.compile(r"(?ms)^\.method [^\n]+\n.*?^\.end method")
HOOK = """    # gramforge: suppress matching comment rows before Compose opens a group.
    iget-object v0, v5, LX/0Il1;->A0O:Ljava/lang/String;

    if-eqz v0, :gramforge_comment_visible

    sget-object v1, Ljava/util/Locale;->ROOT:Ljava/util/Locale;

    invoke-virtual {v0, v1}, Ljava/lang/String;->toLowerCase(Ljava/util/Locale;)Ljava/lang/String;

    move-result-object v0

    const-string v1, "your page"

    invoke-virtual {v0, v1}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v0

    if-eqz v0, :gramforge_comment_visible

    return-void

    :gramforge_comment_visible

"""


def locate_row(root: Path) -> Path:
    search = subprocess.run(
        ["rg", "--no-ignore", "-l", "-F", MARKER, "--glob", "*.smali", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )
    if search.returncode not in (0, 1):
        raise PatchMismatch(f"comment renderer search failed: {search.stderr.strip()}")
    matches = [Path(line) for line in search.stdout.splitlines()]
    if len(matches) != 1:
        raise PatchMismatch(f"expected one Compose CommentRow, found {len(matches)}")
    return matches[0]


def patch(root: Path, *, check: bool = False) -> list[str]:
    if not root.is_dir():
        raise PatchMismatch(f"decoded APK directory not found: {root}")
    path = locate_row(root)
    source = path.read_text()
    matches = [match for match in METHOD_RE.finditer(source) if MARKER in match.group()]
    if len(matches) != 1:
        raise PatchMismatch(f"expected one Compose CommentRow method, found {len(matches)}")
    method = matches[0].group()
    if not method.startswith(METHOD_HEADER + "\n"):
        raise PatchMismatch("CommentRow signature changed")
    if "gramforge_comment_visible" in source:
        raise PatchMismatch("comment filter already applied")
    if (
        ".locals 59" not in method
        or method.count(ANCHOR) != 1
        or method.count(MODEL_FIELD) != 1
        or "invoke-interface {v0, v1}, LX/1BaO;->Hg2(I)V" not in method
    ):
        raise PatchMismatch("CommentRow body or model text field changed")

    updated = method.replace(ANCHOR, ANCHOR.replace("    const/4 v14, 0x1", HOOK + "    const/4 v14, 0x1"), 1)
    if not check:
        path.write_text(source.replace(method, updated, 1))
    return ['comment text containing "your page" (case-insensitive)']


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded_apk", type=Path)
    parser.add_argument("--check", action="store_true", help="validate without modifying smali")
    args = parser.parse_args()
    try:
        labels = patch(args.decoded_apk, check=args.check)
    except PatchMismatch as exc:
        parser.exit(1, f"ERROR: Instagram comment filter incompatible: {exc}\n")
    print("GramForge comment filter " + ("verified" if args.check else "patched") + ": " + ", ".join(labels))


if __name__ == "__main__":
    main()
