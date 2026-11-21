#!/usr/bin/env python3
"""Normalize FeurStagram's runtime defaults to GramForge's ads-only profile."""
from __future__ import annotations
import os
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

def patch_surface_defaults(text: str) -> str:
    """Adapt FeurStagram 456's map-backed surface defaults without disabling ads.

    Its surface blockers now call effective(key), which delegates to a table
    instead of using per-method getBlocked(key, default) calls. Verify every
    upstream entry before altering only non-ad defaults.
    """
    start, end = method_span(text, "<clinit>")
    original = text[start:end]
    expected = [
        ("block_feed", "3"),
        ("block_explore", "3"),
        ("block_reels", "3"),
        ("block_friends_lane", "3"),
        ("block_stories", "6"),
        ("block_instants", "3"),
        ("block_notes", "3"),
        ("block_suggested", "3"),
        ("block_ads", "3"),
        ("block_comments", "6"),
        ("block_notifications", "6"),
        ("block_threads", "3"),
    ]
    pattern = (
        r'const-string v2, "(block_[a-z_]+)"'
        r'(?:(?!const-string v2,).)*?'
        r'filled-new-array \{v2, v([36])\}, \[Ljava/lang/String;'
    )
    entries = re.findall(pattern, original, flags=re.S)
    if entries != expected:
        die(f"SURFACE_DEFAULTS changed: expected {expected!r}, found {entries!r}")
    if (
        original.count(".locals 8") != 1
        or re.search(r"\bv8\b", original)
        or original.count("SURFACE_DEFAULTS:Ljava/util/Map;") != 2
        or not re.search(r"const/16 v0, 0xc\b", original)
        or "storedBlocked(Ljava/lang/String;)Z" not in text
        or "effective(Ljava/lang/String;)Z" not in text
    ):
        die("SURFACE_DEFAULTS structure or register allocation changed")
    body = original
    for key, default_register in expected:
        if default_register != "3" or key == "block_ads":
            continue
        marker = f'const-string v2, "{key}"'
        pos = body.index(marker)
        next_pos = body.find("const-string v2,", pos + len(marker))
        if next_pos < 0:
            next_pos = len(body)
        chunk = body[pos:next_pos]
        old = "filled-new-array {v2, v3}, [Ljava/lang/String;"
        if chunk.count(old) != 1:
            die(f"SURFACE_DEFAULTS: {key} constructor unexpectedly changed")
        body = body[:pos] + chunk.replace(
            old, "filled-new-array {v2, v8}, [Ljava/lang/String;", 1
        ) + body[next_pos:]
    body = body.replace(
        ".locals 8", '.locals 9\n    const-string v8, "false"', 1
    )
    if body.count("filled-new-array {v2, v8}, [Ljava/lang/String;") != 8:
        die("SURFACE_DEFAULTS: non-ad default count changed")
    return text[:start] + body + text[end:]


def replace_method(text: str, name: str, body: str) -> str:
    start, end = method_span(text, name)
    return text[:start] + body.rstrip() + "\n" + text[end:]

def patch_config(path: Path) -> None:
    text = path.read_text()
    surface_methods = {
        "isFeedBlocked": "block_feed",
        "isExploreBlocked": "block_explore",
        "isReelsBlocked": "block_reels",
        "isFriendsLaneBlocked": "block_friends_lane",
        "isInstantsBlocked": "block_instants",
        "isNotesBlocked": "block_notes",
        "isSuggestedBlocked": "block_suggested",
    }
    if "SURFACE_DEFAULTS:Ljava/util/Map;" in text:
        for method, key in surface_methods.items():
            start, end = method_span(text, method)
            body = text[start:end]
            if (
                f'const-string v0, "{key}"' not in body
                or body.count("->effective(Ljava/lang/String;)Z") != 1
                or "->getBlocked(Ljava/lang/String;Z)Z" in body
            ):
                die(f"{method}: map-backed surface getter changed")
        text = patch_surface_defaults(text)
    else:
        for method in surface_methods:
            text = set_boolean_default(text, method, 1, 0)
    for method in ("arePopupsHidden", "isForceSdr", "isAutoUpdateEnabled"):
        text = set_boolean_default(text, method, 1, 0)
    text = set_boolean_default(text, "isReelsTabShown", 0, 1)
    text = set_boolean_default(text, "isOnboardingDone", 0, 1)
    if os.environ.get("HIDE_HOME") == "true":
        text = replace_method(text, "isHomeTabShown", """.method public static isHomeTabShown()Z
    .locals 1

    const/4 v0, 0x0

    return v0
.end method""")
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
        if "SURFACE_DEFAULTS:Ljava/util/Map;" in text:
            key = {
                "isAdsBlocked": "block_ads",
                "isStoriesBlocked": "block_stories",
                "isNotificationsButtonBlocked": "block_notifications",
            }[method]
            if (
                f'const-string v0, "{key}"' not in body
                or body.count("->effective(Ljava/lang/String;)Z") != 1
            ):
                die(f"{method}: map-backed default no longer matches expected {expected}")
        elif not re.search(
            rf"const/4 v\d+, 0x{expected:x}(?=\s+invoke-static \{{[^}}]+\}}, Lcom/feurstagram/extension/Config;->getBlocked)",
            body,
        ):
            die(f"{method}: upstream default no longer matches expected {expected}")
    path.write_text(text)

def patch_reels_nav_default(path: Path) -> None:
    text = path.read_text()
    start, end = method_span(text, "installAll")
    body = text[start:end]
    if os.environ.get("HIDE_HOME") == "true" and "Lcom/feurstagram/extension/Hiders$HomeTabHider;" not in body:
        die("Hiders.installAll: HomeTabHider is not installed")
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

def patch_manifest_for_apktool(path: Path) -> None:
    """Remove the explicit default-false API 37 flag unsupported by bundled aapt2.

    Apktool 3.0.3's aapt2 cannot link the upstream manifest containing this
    newer framework attribute. Removing its false value retains the default
    behavior while permitting the existing resource-preserving rebuild.
    """
    text = path.read_text()
    marker = ' android:allowCrossUidActivitySwitchFromBelow="false"'
    if text.count(marker) != 1:
        die(f"AndroidManifest.xml: expected one explicit false API 37 attribute, found {text.count(marker)}")
    path.write_text(text.replace(marker, "", 1))


def main() -> None:
    if len(sys.argv) != 2:
        die("usage: patch-feurstagram-profile.py <apktool-decoded-dir>")
    root = Path(sys.argv[1])
    if not root.is_dir():
        die(f"decoded directory not found: {root}")
    patch_manifest_for_apktool(root / "AndroidManifest.xml")
    patch_config(find_one(root, "com/feurstagram/extension/Config.smali"))
    patch_reels_nav_default(find_one(root, "com/feurstagram/extension/Hiders.smali"))
    replace_with_run_callback(find_one(root, "com/feurstagram/extension/FollowPrompt.smali"), "maybeShow")
    replace_with_return(find_one(root, "com/feurstagram/extension/UpdateChecker.smali"), "checkWhatsNew")
    print(f"FeurStagram profile normalized: ads on; other Feur blocks/prompts/updater off; Home hidden={os.environ.get('HIDE_HOME') == 'true'}")

if __name__ == "__main__":
    main()
