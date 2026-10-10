#!/usr/bin/env python3
"""Only actual release-note changes appear as Matrix changelog bullets."""

import argparse
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "lib" / "matrix_notification.py"
spec = importlib.util.spec_from_file_location("matrix_notification", MODULE_PATH)
notification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notification)

FEUR = "jean-voila/FeurStagram"
MORPHE = "brosssh/morphe-patches"


def release(repo, tag, body):
    return {"tag_name": tag, "body": body, "html_url": f"https://github.com/{repo}/releases/tag/{tag}"}


class MatrixNotificationTests(unittest.TestCase):
    def options(self, **changes):
        values = dict(
            title="GramForge APK ready", error_log=None, version="450.0.0.50.77",
            release_tag="v450-0-0-50-77", previous_release_tag="v446-0-0-49-77",
            patches_tag="v2.8.2", previous_patches_tag="v2.8.1",
            url="https://apks.test/a.apk?x=1&download=true",
        )
        values.update(changes)
        return argparse.Namespace(**values)

    def test_exact_upstream_bullets_and_source_hyperlinks(self):
        real = release(FEUR, "v450-0-0-50-77", """## Changes
- **Fixed shared post deep links** so profiles open reliably.
- Added FeurStagram onboarding and an official account card.
- **Improved ad filtering in stories.**
""")
        morphe = release(MORPHE, "v2.8.2", """- **Instagram - Hide navigation buttons:** Fix hiding Search
- **park4night:** Updated support
- **Instagram:** Fix suggested stories
""")
        def releases(repo, new, old):
            return [real] if repo == FEUR else [morphe]
        with patch.object(notification, "fetch_release_range", side_effect=releases):
            msg = notification.make_payload(self.options())
        self.assertIn("• Fixed shared post deep links so profiles open reliably.", msg["body"])
        self.assertIn("• Improved ad filtering in stories.", msg["body"])
        self.assertIn("Instagram - Hide navigation buttons: Fix hiding Search", msg["body"])
        self.assertNotIn("onboarding", msg["body"])
        self.assertNotIn("park4night", msg["body"])
        self.assertNotIn("suggested stories", msg["body"])
        self.assertNotIn("🛡️ FeurStagram ad filtering retained", msg["body"])
        self.assertNotIn("🔧 GramForge patch profile", msg["body"])
        self.assertIn('href="https://github.com/jean-voila/FeurStagram/releases/tag/v450-0-0-50-77"', msg["formatted_body"])
        self.assertIn('href="https://github.com/brosssh/morphe-patches/releases/tag/v2.8.2"', msg["formatted_body"])
        self.assertIn('href="https://apks.test/a.apk?x=1&amp;download=true"', msg["formatted_body"])
        self.assertIn('>Download APK</a>', msg["formatted_body"])

    def test_no_static_bullets_when_unchanged_or_no_notes(self):
        with patch.object(notification, "fetch_release_range", return_value=[]) as fetch:
            msg = notification.make_payload(self.options(
                previous_release_tag="v450-0-0-50-77",
                previous_patches_tag="v2.8.2", url="",
            ))
        self.assertEqual(msg["body"].count("• "), 0)
        self.assertIn("No applicable changelog entries", msg["body"])
        self.assertNotIn("Navigation:", msg["body"])
        self.assertNotIn("Download APK", msg["body"])
        self.assertEqual(fetch.call_count, 2)

    def test_multiple_versions_between_previous_and_current(self):
        newer = release(FEUR, "v450-0-0-50-77", "- Fixed ad blocking after Instagram 450 update.")
        middle = release(FEUR, "v446-0-0-49-77", "- Fixed deep link routing.")
        previous = release(FEUR, "v445-0-0-45-83", "- Old change must not repeat.")
        with patch.object(notification, "urllib") as api:
            api.request.Request.side_effect = lambda url, **kwargs: url
            response = api.request.urlopen.return_value.__enter__.return_value
            response.read.return_value = b''
            with patch.object(notification.json, "load", return_value=[newer, middle, previous]):
                releases = notification.fetch_release_range(FEUR, "v450-0-0-50-77", "v445-0-0-45-83")
        self.assertEqual([r["tag_name"] for r in releases], ["v446-0-0-49-77", "v450-0-0-50-77"])
        self.assertNotIn("Old change", " ".join(c.text for r in releases for c in notification.actual_bullets(r, FEUR)))

    def test_missing_old_tag_raises_instead_of_claiming_complete_changelog(self):
        current = release(FEUR, "v450-0-0-50-77", "- Real fix")
        with patch.object(notification.urllib.request, "urlopen") as opening:
            with patch.object(notification.json, "load", return_value=[current]):
                with self.assertRaises(notification.ChangelogUnavailable):
                    notification.fetch_release_range(FEUR, "v450-0-0-50-77", "v446-0-0-49-77")

    def test_changelog_fetch_failure_blocks_message(self):
        with patch.object(notification, "fetch_release_range", side_effect=notification.ChangelogUnavailable("rate limited")):
            with self.assertRaises(notification.ChangelogUnavailable):
                notification.make_payload(self.options())

    def test_failed_build_escapes_html_log_without_fetching_notes(self):
        with patch.object(notification, "fetch_release_range", side_effect=AssertionError("unexpected fetch")):
            msg = notification.make_payload(self.options(error_log="error <unsafe> & \"quoted\"", url=""))
        self.assertIn("error <unsafe>", msg["body"])
        self.assertIn("error &lt;unsafe&gt; &amp;", msg["formatted_body"])
        self.assertNotIn("<unsafe>", msg["formatted_body"])


if __name__ == "__main__":
    unittest.main()
