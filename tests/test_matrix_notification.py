#!/usr/bin/env python3
"""Regression tests for Matrix release messages and upstream changelog filtering."""

import argparse
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "lib" / "matrix_notification.py"
spec = importlib.util.spec_from_file_location("matrix_notification", MODULE_PATH)
notification = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = notification
spec.loader.exec_module(notification)


class MatrixNotificationTests(unittest.TestCase):
    def options(self, **changes):
        values = dict(
            title="GramForge APK ready", error_log=None, version="450.0.0.50.77",
            previous_version="446.0.0.49.77", release_tag="v450-0-0-50-77",
            previous_release_tag="v446-0-0-49-77", profile="new", previous_profile="old",
            url="https://apks.test/a.apk?x=1&download=true",
        )
        values.update(changes)
        return argparse.Namespace(**values)

    def test_html_download_link_and_plain_fallback(self):
        with patch.dict(os.environ, {"GRAMFORGE_RELEASE_NOTES_FILE": "/missing-notes"}):
            msg = notification.make_payload(self.options())
        self.assertEqual(msg["msgtype"], "m.text")
        self.assertEqual(msg["format"], "org.matrix.custom.html")
        self.assertIn("📱 Instagram 446.0.0.49.77 → 450.0.0.50.77", msg["body"])
        self.assertIn("🛡️ FeurStagram", msg["body"])
        self.assertIn("🔧 GramForge patch profile changed", msg["body"])
        self.assertIn('href="https://apks.test/a.apk?x=1&amp;download=true"', msg["formatted_body"])
        self.assertIn('>Download APK</a>', msg["formatted_body"])
        self.assertIn("https://apks.test/a.apk?x=1&download=true", msg["body"])

    def test_filters_removed_upstream_ui_but_keeps_applicable_fixes(self):
        notes = """## ✨ New
- **Official account changes.** Follow @feurstagram_off for more.
- **A smoother settings page.** First launch after the update.
## 🐛 Fixes
- **Ads are blocked in the feed again** after Instagram 444 changed the timeline.
- **Deep links keep working** for shared posts and profiles.
- Updated to Instagram 450.0.0.50.77.
"""
        with tempfile.TemporaryDirectory() as folder:
            fixture = Path(folder) / "notes.md"
            fixture.write_text(notes)
            with patch.dict(os.environ, {"GRAMFORGE_RELEASE_NOTES_FILE": str(fixture)}):
                msg = notification.make_payload(self.options())
        self.assertIn("🐛 Upstream: Ads are blocked", msg["body"])
        self.assertIn("🐛 Upstream: Deep links", msg["body"])
        self.assertNotIn("Official account", msg["body"])
        self.assertNotIn("settings page", msg["body"])

    def test_unrelated_release_notes_not_claimed_as_app_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            fixture = Path(folder) / "notes.md"
            fixture.write_text("- Changed official account and follow card.\n- Updated to Instagram 450.0.0.50.77.\n")
            with patch.dict(os.environ, {"GRAMFORGE_RELEASE_NOTES_FILE": str(fixture)}):
                msg = notification.make_payload(self.options())
        self.assertNotIn("Upstream:", msg["body"])
        self.assertIn("Navigation:", msg["body"])

    def test_failed_build_escapes_html_log(self):
        msg = notification.make_payload(self.options(error_log="error <unsafe> & \"quoted\"", url=""))
        self.assertIn("error <unsafe>", msg["body"])
        self.assertIn("error &lt;unsafe&gt; &amp;", msg["formatted_body"])
        self.assertNotIn("<unsafe>", msg["formatted_body"])

    def test_same_version_patch_change(self):
        msg = notification.make_payload(self.options(previous_version="450.0.0.50.77", previous_release_tag="v450-0-0-50-77", url=""))
        self.assertIn("Updated GramForge APK for Instagram", msg["body"])
        self.assertNotIn("Upstream:", msg["body"])
        self.assertNotIn("Download APK", msg["body"])


if __name__ == "__main__":
    unittest.main()
