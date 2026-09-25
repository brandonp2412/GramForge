#!/usr/bin/env python3
"""Normalize FeurStagram's runtime defaults to GramForge's ads-only profile."""
from __future__ import annotations
import re
import sys
from pathlib import Path

def die(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")

def find_one(root: Path, suffix: str) -> Path:
    matches = list(root.glob(f"**/{suffix}"))
    if len(matches) != 1:
        die(f"expected one {suffix}, found {len(matches)}")
    return matches[0]

def method_span(text: str, name: str) -> tuple[int, int]:
    match = re.search(rf"(?ms)^\.method[^\n]*\s{name}\([^\n]*\n.*?^\.end method\s*$", text)
    if not match:
        die(f"method {name} not found")
    return match.span()

def set_boolean_default(text: str, method: str, old: int, new: int) -> str:
    start, end = method_span(text, method)
    body = text[start:end]
    pattern = rf"const/4 (v\d+), 0x{old:x}(?=\s+invoke-static \{{[^}}]+\}}, Lcom/feurstagram/extension/Config;->getBlocked)"
    updated, count = re.subn(pattern, rf"const/4 \1, 0x{new:x}", body, count=1)
    if count != 1:
        die(f"{method}: expected one default {old}, found {count}")
    return text[:start] + updated + text[end:]

def replace_method(text: str, name: str, body: str) -> str:
    start, end = method_span(text, name)
    return text[:start] + body.rstrip() + "\n" + text[end:]

def patch_config(path: Path) -> None:
    text = path.read_text()
    for method in (
        "isFeedBlocked", "isExploreBlocked", "isReelsBlocked",
        "isFriendsLaneBlocked", "isInstantsBlocked", "isNotesBlocked",
        "isSuggestedBlocked", "arePopupsHidden", "isForceSdr",
        "isAutoUpdateEnabled",
    ):
        text = set_boolean_default(text, method, 1, 0)
    text = set_boolean_default(text, "isReelsTabShown", 0, 1)
    text = set_boolean_default(text, "isOnboardingDone", 0, 1)
    text = replace_method(text, "navDefault", """.method public static navDefault(Ljava/lang/String;)Z
    .locals 1

    const/4 v0, 0x1

    return v0
.end method""")
    for method, expected in (
        ("isAdsBlocked", 1),
        ("isStoriesBlocked", 0),
        ("isNotificationsButtonBlocked", 0),
    ):
        start, end = method_span(text, method)
        body = text[start:end]
        if not re.search(
            rf"const/4 v\d+, 0x{expected:x}(?=\s+invoke-static \{{[^}}]+\}}, Lcom/feurstagram/extension/Config;->getBlocked)",
            body,
        ):
            die(f"{method}: upstream default no longer matches expected {expected}")
    path.write_text(text)

def patch_reels_nav_default(path: Path) -> None:
    text = path.read_text()
    start, end = method_span(text, "installAll")
    body = text[start:end]
    pattern = r'(?s)(const-string v\d+, "nav_show_reels"(?:(?!nav_show_).){0,500}?const/4 v\d+, )0x0'
    updated, count = re.subn(pattern, r"\g<1>0x1", body, count=1)
    if count != 1:
        die("Hiders.installAll: could not make the Reels tab visible by default")
    path.write_text(text[:start] + updated + text[end:])

def replace_with_run_callback(path: Path, method: str) -> None:
    text = path.read_text()
    start, end = method_span(text, method)
    header = text[start:text.find("\n", start)]
    replacement = f"""{header}
    .locals 0

    invoke-interface {{p1}}, Ljava/lang/Runnable;->run()V

    return-void
.end method"""
    path.write_text(text[:start] + replacement + "\n" + text[end:])

def replace_with_return(path: Path, method: str) -> None:
    text = path.read_text()
    start, end = method_span(text, method)
    header = text[start:text.find("\n", start)]
    replacement = f"""{header}
    .locals 0

    return-void
.end method"""
    path.write_text(text[:start] + replacement + "\n" + text[end:])

def main() -> None:
    if len(sys.argv) != 2:
        die("usage: patch-feurstagram-profile.py <apktool-decoded-dir>")
    root = Path(sys.argv[1])
    if not root.is_dir():
        die(f"decoded directory not found: {root}")
    patch_config(find_one(root, "com/feurstagram/extension/Config.smali"))
    patch_reels_nav_default(find_one(root, "com/feurstagram/extension/Hiders.smali"))
    replace_with_run_callback(find_one(root, "com/feurstagram/extension/FollowPrompt.smali"), "maybeShow")
    replace_with_return(find_one(root, "com/feurstagram/extension/UpdateChecker.smali"), "checkWhatsNew")
    print("FeurStagram profile normalized: ads on; other Feur blocks/prompts/updater off; nav visible")

if __name__ == "__main__":
    main()
