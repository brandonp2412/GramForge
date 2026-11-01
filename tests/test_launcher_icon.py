#!/usr/bin/env python3
from __future__ import annotations

import runpy
import tempfile
import unittest
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
icon = runpy.run_path(str(repo / "tools/patch-launcher-icon.py"))
assets = repo / "assets/rotta-launcher"


class LauncherIconTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.decoded = Path(self.tmp.name)
        xml = self.decoded / "res/mipmap-anydpi/icon.xml"
        xml.parent.mkdir(parents=True)
        xml.write_text('<adaptive-icon><background drawable="ig_launcher_background"/><foreground drawable="ig_launcher_foreground"/><monochrome/></adaptive-icon>')
        for density in icon["DENSITIES"]:
            folder = self.decoded / f"res/mipmap-{density}"
            folder.mkdir(parents=True)
            for variant in icon["VARIANTS"]:
                name = "icon" if variant == "icon" else f"ig_launcher_{variant}"
                (folder / f"{name}.png").write_bytes(b"old")

    def test_replaces_all_legacy_and_adaptive_resources(self) -> None:
        icon["patch"](self.decoded, assets)
        xml = (self.decoded / "res/mipmap-anydpi/icon.xml").read_text()
        self.assertEqual(xml, icon["ADAPTIVE"])
        self.assertNotIn("monochrome", xml)
        for source, density, variant in icon["artwork"](assets):
            name = "icon" if variant == "icon" else f"ig_launcher_{variant}"
            self.assertEqual((self.decoded / f"res/mipmap-{density}/{name}.png").read_bytes(), source.read_bytes())

    def test_fails_closed_on_missing_upstream_resource(self) -> None:
        (self.decoded / "res/mipmap-mdpi/icon.png").unlink()
        with self.assertRaises(SystemExit):
            icon["patch"](self.decoded, assets)
        self.assertEqual((self.decoded / "res/mipmap-hdpi/icon.png").read_bytes(), b"old")

    def test_fingerprint_is_stable(self) -> None:
        first = icon["fingerprint"](assets)
        self.assertEqual(len(first), 16)
        self.assertEqual(first, icon["fingerprint"](assets))


if __name__ == "__main__":
    unittest.main()
