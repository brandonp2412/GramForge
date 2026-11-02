#!/usr/bin/env python3
"""Remove Reels Save/Repost buttons and their companion count rows.

The obfuscated names move between Instagram versions, so identify the four
Reels-only factories by render markers and their action-rail call sites. Refuse
to modify an APK unless every factory feeds a null-skipping Litho list builder.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


class PatchMismatch(Exception):
    pass


MARKERS = {
    "ufi": "ClipsUfiComponent_maybeCreateSaveButtonComponent",
    "save": "ClipsSaveButtonComponent_render",
    "repost": "ClipsAnimatedRepostButtonComponent_render",
    "repost_child": "ClipsRepostButtonComponent_render",
    "save_count": "ClipsUfiComponent_maybeCreateSaveCountComponent",
}

METHOD_RE = re.compile(r"(?ms)^\.method [^\n]+\n.*?^\.end method\s*$")
CLASS_RE = re.compile(r"(?m)^\.class [^\n]*? (L[^;]+;)$")


def locate_markers(root: Path) -> dict[str, tuple[Path, str, str]]:
    cmd = ["rg", "-l", "-F"]
    for marker in MARKERS.values():
        cmd.extend(["-e", marker])
    cmd.extend(["--glob", "*.smali", str(root)])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise PatchMismatch("ripgrep is required to identify Reels components") from exc
    if result.returncode not in (0, 1):
        raise PatchMismatch(f"smali search failed: {result.stderr.strip()}")
    found: dict[str, list[tuple[Path, str, str]]] = {key: [] for key in MARKERS}
    for line in result.stdout.splitlines():
        path = Path(line)
        source = path.read_text()
        class_match = CLASS_RE.search(source)
        if class_match is None:
            raise PatchMismatch(f"missing class descriptor in {path}")
        for key, marker in MARKERS.items():
            if marker in source:
                found[key].append((path, source, class_match.group(1)))
    for key, matches in found.items():
        if len(matches) != 1:
            raise PatchMismatch(
                f"expected exactly one {key} component marker, found {len(matches)}"
            )
    return {key: matches[0] for key, matches in found.items()}


def factory(source: str, component: str, marker: str | None) -> tuple[str, str, str]:
    candidates = []
    for block in METHOD_RE.finditer(source):
        header = block.group().splitlines()[0]
        if not header.endswith(f"){component}") or " final " not in header:
            continue
        if marker is not None and marker not in block.group():
            continue
        if not re.search(rf"(?m)^\s*new-instance v\d+, {re.escape(component)}$", block.group()):
            continue
        signature = re.search(r"([^\s(]+)(\([^)]*\)L[^;]+;)$", header)
        if signature:
            candidates.append((block, signature.group(1), signature.group(2)))
    if len(candidates) != 1:
        raise PatchMismatch(
            f"expected one Reels factory for {component}, found {len(candidates)}"
        )
    block, name, signature = candidates[0]
    return block.group(), name, signature


def factory_by_marker(
    source: str, marker: str, result_type: str
) -> tuple[str, str, str]:
    candidates = []
    for match in METHOD_RE.finditer(source):
        block = match.group()
        header = block.splitlines()[0]
        if marker not in block or not header.endswith(f"){result_type}"):
            continue
        signature = re.search(r"([^\s(]+)(\([^)]*\)L[^;]+;)$", header)
        if signature:
            candidates.append((block, signature.group(1), signature.group(2)))
    if len(candidates) != 1:
        raise PatchMismatch(f"expected one factory containing {marker}, found {len(candidates)}")
    return candidates[0]


def repost_count_factory(
    source: str, owner: str, repost_name: str, repost_signature: str
) -> tuple[str, str, str]:
    # The numeric Repost label is a separate Litho child appended directly
    # after the Repost button in the Reels action rail on eligible media.
    invocation = re.escape(f"{owner}->{repost_name}{repost_signature}")
    matches = re.finditer(
        r"invoke-direct(?:/range)? \{[^\n]+\}, " + invocation
        + r"\s+move-result-object v\d+"
        + r"\s+invoke-virtual \{v\d+, v\d+\}, L[^;]+;->[^\s(]+\(LX/05x0;\)V",
        source,
    )
    candidates = set()
    for match in matches:
        following = source[match.end():match.end() + 650]
        candidate = re.search(
            r"invoke-direct(?:/range)? \{[^\n]+\}, "
            + re.escape(owner)
            + r"->(?P<name>[^\s(]+)(?P<signature>\([^)]*\)LX/00Ax;)",
            following,
        )
        if candidate:
            candidates.add((candidate["name"], candidate["signature"]))

    verified = []
    for name, signature in candidates:
        blocks = [
            match.group() for match in METHOD_RE.finditer(source)
            if match.group().splitlines()[0].endswith(f"{name}{signature}")
        ]
        if len(blocks) == 1 and "->DMp()" in blocks[0] and '"ufi_count"' in blocks[0]:
            verified.append((blocks[0], name, signature))
    if len(verified) != 1:
        raise PatchMismatch(
            f"expected one companion Repost count factory, found {len(verified)}"
        )
    return verified[0]


def verified_append_calls(
    source: str, owner: str, name: str, signature: str
) -> tuple[str, str]:
    invocation = re.escape(f"{owner}->{name}{signature}")
    all_calls = len(re.findall(r"invoke-direct(?:/range)? [^\n]+ " + invocation, source))
    pattern = re.compile(
        r"invoke-direct(?:/range)? \{[^\n]+\}, "
        + invocation
        + r"\s+move-result-object (?P<value>v\d+)"
        + r"\s+invoke-virtual \{v\d+, (?P=value)\}, "
        + r"(?P<builder>L[^;]+;)->(?P<append>[^\s(]+)\(LX/05x0;\)V"
    )
    calls = list(pattern.finditer(source))
    if not calls or len(calls) != all_calls:
        raise PatchMismatch(
            f"{name}: {len(calls)}/{all_calls} call sites append directly to a Litho builder"
        )
    builders = {(call["builder"], call["append"]) for call in calls}
    if len(builders) != 1:
        raise PatchMismatch(f"{name}: multiple or inconsistent Reels list builders")
    return builders.pop()


def verify_null_skipping_builder(root: Path, owner: str, append: str) -> None:
    paths = list(root.glob(f"smali*/{owner[1:-1]}.smali"))
    if len(paths) != 1:
        raise PatchMismatch(f"cannot uniquely find Litho builder {owner}")
    source = paths[0].read_text()
    blocks = [
        match.group() for match in METHOD_RE.finditer(source)
        if match.group().splitlines()[0].endswith(f"{append}(LX/05x0;)V")
    ]
    if len(blocks) != 1:
        raise PatchMismatch(f"cannot uniquely identify {owner}->{append}")
    body = blocks[0]
    guard = re.search(r"if-eqz p1, :(?P<label>\w+)", body)
    if guard is None or "Ljava/util/List;->add(Ljava/lang/Object;)Z" not in body:
        raise PatchMismatch("Reels component builder no longer safely skips null")
    if not re.search(
        rf":{re.escape(guard['label'])}\s+return-void", body
    ):
        raise PatchMismatch("Reels component builder null branch changed")


def patch(root: Path, *, check: bool = False) -> list[str]:
    if not root.is_dir():
        raise PatchMismatch(f"decoded APK directory not found: {root}")
    marked = locate_markers(root)
    ufi_path, ufi_source, ufi_owner = marked["ufi"]
    if marked["save"][2] == marked["repost"][2]:
        raise PatchMismatch("Reels Save and Repost unexpectedly share a component class")
    # Confirm the animated Repost renderer actually embeds the Reels Repost child.
    repost_path, repost_source, repost_component = marked["repost"]
    if f"new-instance " not in repost_source or marked["repost_child"][2] not in repost_source:
        raise PatchMismatch(f"{repost_path}: animated Reels Repost child no longer present")

    save_button = factory(ufi_source, marked["save"][2], MARKERS["ufi"])
    repost_button = factory(ufi_source, repost_component, None)
    save_count = factory_by_marker(
        ufi_source, MARKERS["save_count"], "LX/00Ax;"
    )
    repost_count = repost_count_factory(
        ufi_source, ufi_owner, repost_button[1], repost_button[2]
    )
    targets = [
        ("Save", *save_button),
        ("Repost", *repost_button),
        ("Save count", *save_count),
        ("Repost count", *repost_count),
    ]
    replacements: list[tuple[str, str, str]] = []
    builders: set[tuple[str, str]] = set()
    for label, old, name, signature in targets:
        builders.add(verified_append_calls(ufi_source, ufi_owner, name, signature))
        header = old.splitlines()[0]
        replacement = (
            f"{header}\n    .locals 1\n\n"
            "    const/4 v0, 0x0\n\n"
            "    return-object v0\n.end method"
        )
        replacements.append((label, old, replacement))
    if len(builders) != 1:
        raise PatchMismatch("Reels buttons and count rows no longer share one action builder")
    verify_null_skipping_builder(root, *next(iter(builders)))
    if not check:
        updated = ufi_source
        for _, old, replacement in replacements:
            if updated.count(old) != 1:
                raise PatchMismatch("ambiguous Reels factory replacement")
            updated = updated.replace(old, replacement, 1)
        ufi_path.write_text(updated)
    return [label for label, _, _ in replacements]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded_apk", type=Path)
    parser.add_argument("--check", action="store_true", help="validate without changing smali")
    args = parser.parse_args()
    try:
        targets = patch(args.decoded_apk, check=args.check)
    except PatchMismatch as exc:
        parser.exit(1, f"ERROR: Reels action patch incompatible with this Instagram build: {exc}\n")
    print(f"GramForge Reels actions {'verified' if args.check else 'patched'}: {', '.join(targets)}")


if __name__ == "__main__":
    main()
