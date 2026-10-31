#!/usr/bin/env python3
"""Validate GramForge's Home-tab defaults in FeurStagram smali."""
from __future__ import annotations

import os
import runpy
import tempfile
import unittest
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
profile = runpy.run_path(str(repo / "tools/patch-feurstagram-profile.py"))


def blocked_method(name: str, default: int) -> str:
    return f""".method public static {name}()Z
    .locals 2
    const-string v0, "test"
    const/4 v1, 0x{default:x}
    invoke-static {{v0, v1}}, Lcom/feurstagram/extension/Config;->getBlocked(Ljava/lang/String;Z)Z
    move-result v0
    return v0
.end method
"""


def fake_config() -> str:
    defaults = {
        **dict.fromkeys((
            "isFeedBlocked", "isExploreBlocked", "isReelsBlocked",
            "isFriendsLaneBlocked", "isInstantsBlocked", "isNotesBlocked",
            "isSuggestedBlocked", "arePopupsHidden", "isForceSdr",
            "isAutoUpdateEnabled", "isAdsBlocked",
        ), 1),
        "isReelsTabShown": 0,
        "isOnboardingDone": 0,
        "isStoriesBlocked": 0,
        "isNotificationsButtonBlocked": 0,
        "isHomeTabShown": 1,
        "navDefault": 1,
    }
    return "\n".join(blocked_method(name, default) for name, default in defaults.items())


def method_body(text: str, name: str) -> str:
    start, end = profile["method_span"](text, name)
    return text[start:end]


class HomeTabTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = Path(self.tmp.name) / "Config.smali"
        self.hiders = Path(self.tmp.name) / "Hiders.smali"
        self.original_hide_home = os.environ.get("HIDE_HOME")
        self.addCleanup(self.restore_environment)
        self.config.write_text(fake_config())

    def restore_environment(self) -> None:
        if self.original_hide_home is None:
            os.environ.pop("HIDE_HOME", None)
        else:
            os.environ["HIDE_HOME"] = self.original_hide_home

    def test_hide_home_forces_false_even_if_saved_preference_exists(self) -> None:
        os.environ["HIDE_HOME"] = "true"
        profile["patch_config"](self.config)
        patched = method_body(self.config.read_text(), "isHomeTabShown")
        self.assertIn("const/4 v0, 0x0", patched)
        self.assertNotIn("getBlocked", patched)

    def test_show_home_preserves_existing_behavior(self) -> None:
        os.environ["HIDE_HOME"] = "false"
        profile["patch_config"](self.config)
        patched = method_body(self.config.read_text(), "isHomeTabShown")
        self.assertIn("getBlocked", patched)

    def test_home_hider_must_be_installed(self) -> None:
        os.environ["HIDE_HOME"] = "true"
        self.hiders.write_text(""".method public static installAll(Landroid/view/ViewGroup;)V
    .locals 3
    const-string v0, "nav_show_reels"
    const/4 v1, 0x0
    return-void
.end method
""")
        with self.assertRaises(SystemExit):
            profile["patch_reels_nav_default"](self.hiders)

    def test_reels_visible_and_home_hider_present(self) -> None:
        os.environ["HIDE_HOME"] = "true"
        self.hiders.write_text(""".method public static installAll(Landroid/view/ViewGroup;)V
    .locals 3
    new-instance v0, Lcom/feurstagram/extension/Hiders$HomeTabHider;
    const-string v0, "nav_show_reels"
    const/4 v1, 0x0
    return-void
.end method
""")
        profile["patch_reels_nav_default"](self.hiders)
        self.assertIn("const/4 v1, 0x1", self.hiders.read_text())


if __name__ == "__main__":
    unittest.main()
