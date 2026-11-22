#!/usr/bin/env python3
"""Instagram 456 one-tap Not interested preserves ads' native More button."""
from __future__ import annotations

import runpy
import tempfile
import unittest
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
patcher = runpy.run_path(str(repo / "tools/patch-reels-not-interested.py"))
patch = patcher["patch"]
PatchMismatch = patcher["PatchMismatch"]

REELS = """.class public final LX/0FAp;
.method public static final A0F(LX/0BY7;LX/0FAp;Ljava/lang/Integer;Ljava/lang/String;Lkotlin/jvm/functions/Function1;JJZZ)LX/01Vj;
    .locals 21

    iget-object v10, v6, LX/0FAp;->A04:LX/0Nfu;
    invoke-interface {v10}, LX/0Nfu;->ClC()LX/04Dh;
    move-result-object v5
    const v1, 0x7f135acc

    invoke-static {v7, v1}, LX/01LA;->A0N(LX/0mnw;I)Ljava/lang/String;

    move-result-object v1

    const v0, 0x7f082848

    if-eqz v2, :cond_6

    const v0, 0x7f082845

    :cond_6
    return-object v0
.end method
"""

CALLBACK = """.class public final LX/0JcX;
.method public static A00(ILjava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
    .locals 13
    :pswitch_11
    check-cast v2, LX/0FAp;
    iget-object v0, v2, LX/0FAp;->A04:LX/0Nfu;

    invoke-interface {v0}, LX/0Nfu;->ClC()LX/04Dh;

    move-result-object v2

    invoke-interface {v0}, LX/0Nfu;->ClE()LX/09YX;

    move-result-object v1

    invoke-virtual {p2}, LX/00gM;->A00()Landroid/view/View;

    move-result-object v0

    invoke-virtual {v3, v0, v2, v1}, LX/09CX;->A01(Landroid/view/View;LX/04Dh;LX/09YX;)V
    :goto_6
    return-object v0
.end method
"""


class Reels456NotInterestedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.x = self.root / "smali_classes29/X"
        self.x.mkdir(parents=True)
        self.reels = self.x / "0FAp.smali"
        self.callback = self.x / "0JcX.smali"
        self.reels.write_text(REELS)
        self.callback.write_text(CALLBACK)

    def test_456_organic_native_row_tapped_but_ads_unchanged(self):
        before = (self.reels.read_bytes(), self.callback.read_bytes())
        self.assertEqual(len(patch(self.root, check=True)), 3)
        self.assertEqual(before, (self.reels.read_bytes(), self.callback.read_bytes()))
        self.assertFalse(list(self.root.glob("smali*/com/gramforge/*.smali")))
        self.assertEqual(len(patch(self.root)), 3)
        callback = self.callback.read_text()
        reels = self.reels.read_text()
        self.assertIn("NotInterestedTapper;->schedule", callback)
        self.assertIn("LX/04Dh;->A19:Z", callback)
        self.assertIn("if-nez v4, :gramforge_original_more", callback)
        self.assertEqual(callback.count("LX/09CX;->A01("), 1)
        self.assertIn('const-string v1, "Not interested"', reels)
        self.assertIn("0x7f0825f6", reels)
        self.assertIn("0x7f082848", reels)
        names = sorted(x.name for x in self.root.glob("smali*/com/gramforge/*.smali"))
        self.assertEqual(names, [
            "NotInterestedTapper$1.smali", "NotInterestedTapper.smali"
        ])

    def test_456_unrecognized_native_menu_does_not_mutate(self):
        before = CALLBACK.replace("LX/09CX;->A01(", "LX/09CX;->A04(")
        self.callback.write_text(before)
        with self.assertRaisesRegex(PatchMismatch, "organic Reels More action changed"):
            patch(self.root)
        self.assertEqual(before, self.callback.read_text())
        self.assertEqual(REELS, self.reels.read_text())
        self.assertFalse(list(self.root.glob("smali*/com/gramforge/*.smali")))

    def test_456_unknown_drawable_fails_closed(self):
        self.reels.write_text(REELS.replace("0x7f082848", "0x7f080000"))
        with self.assertRaisesRegex(PatchMismatch, "drawable/accessibility"):
            patch(self.root)


if __name__ == "__main__":
    unittest.main()
