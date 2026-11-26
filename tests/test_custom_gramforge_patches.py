#!/usr/bin/env python3
"""Deterministic fixtures for the local Reels Not Interested patch."""
from __future__ import annotations

import runpy
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOT_INTERESTED = runpy.run_path(str(ROOT / "tools/patch-reels-not-interested.py"))


def put(root: Path, klass: str, source: str, dex: int = 8) -> Path:
    path = root / f"smali_classes{dex}/X/{klass}.smali"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source)
    return path


MORE = """.class public final LX/09LB;
.super LX/009q;
.method private final A0F(LX/1Bjl;Ljava/lang/Integer;JJ)LX/04BN;
    .locals 12
    iget-object v0, p0, LX/09LB;->A03:LX/0Nwj;
    invoke-interface {v0}, LX/0Nwj;->DZd()Z
    move-result v0
    if-nez v0, :cond_1
    const/4 v1, 0x0
    :cond_0
    return-object v1
    :cond_1
    iget-boolean v0, p0, LX/09LB;->A08:Z
    xor-int/lit8 v10, v0, 0x1
    if-eqz v0, :cond_2
    const-string v4, "clips_paged_card_ufi_more_button_component"
    :goto_0
    iget-object v5, p0, LX/09LB;->A06:Lkotlin/jvm/functions/Function1;
    move-object v1, p1
    move-object v2, p0
    move-object v3, p2
    move-wide v6, p3
    move-wide/from16 v8, p5
    move v11, v10
    invoke-static/range {v1 .. v11}, LX/09LB;->A0E(LX/1Bjl;LX/09LB;Ljava/lang/Integer;Ljava/lang/String;Lkotlin/jvm/functions/Function1;JJZZ)LX/04BN;
    move-result-object v1
    if-eqz v0, :cond_0
    return-object v1
    :cond_2
    const-string v4, "clips_ufi_more_button_component"
    goto :goto_0
.end method
.method public final A0o(LX/00CS;)LX/05x0;
    .locals 8
    new-instance v0, LX/0SgP;
    :goto_f
    invoke-virtual {v5, v0}, LX/00B5;->A00(LX/05x0;)V
    invoke-direct/range {v0 .. v6}, LX/09LB;->A0F(LX/1Bjl;Ljava/lang/Integer;JJ)LX/04BN;
    move-result-object v0
    invoke-virtual {v5, v0}, LX/00B5;->A00(LX/05x0;)V
    return-object v0
.end method
"""

ACTION = """.class public final LX/0D9G;
.super Ljava/lang/Object;
.method public static A04(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
    .locals 2
    const-string v0, "android_purge_26_q3_NotInterestedActionHandler_handleNotInterestedButtonTapped"
    iget-object v1, v1, LX/03RU;->A00:LX/01wu;
    return-object v0
.end method
"""

NATIVE = """.class public final LX/0SgP;
.super LX/009q;
.method public final A0o(LX/00CS;)LX/05x0;
    .locals 1
    const-string v0, "ClipsNotInterestedButtonComponent_render"
    return-object v0
.end method
"""

ORIGINAL_MORE_HANDLER = """.class public final LX/04RW;
.super Ljava/lang/Object;
.method public final AWI(LX/04Pd;LX/05C5;Lcom/instagram/feed/media/Media;Ljava/lang/String;)V
    .locals 1
    return-void
.end method
.method public final A0b(Lcom/instagram/feed/media/mediaoption/MediaOption$Option;)V
    .locals 1
    const-string v0, "android_purge_26_q3_ClipsOrganicMoreOptionsHelper_handleSeeFewer"
    return-void
.end method
"""


class ReelsNotInterestedPatchTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.more = put(self.root, "09LB", MORE)
        self.action = put(self.root, "0D9G", ACTION)
        self.native = put(self.root, "0SgP", NATIVE)
        self.original_more = put(self.root, "04RW", ORIGINAL_MORE_HANDLER)

    def test_check_only(self) -> None:
        original = self.more.read_bytes()
        NOT_INTERESTED["patch"](self.root, check=True)
        self.assertEqual(self.more.read_bytes(), original)

    def test_native_button_dispatches_overflow_action_immediately(self) -> None:
        NOT_INTERESTED["patch"](self.root)
        source = self.more.read_text()
        self.assertIn("->gramForgeNotInterested(JJ)LX/05x0;", source)
        self.assertIn("A0F(LX/1Bjl;Ljava/lang/Integer;JJ)LX/05x0;", source)
        self.assertIn("LX/0SgP;-><init>", source)
        self.assertIn("if-nez v0, :gramforge_original_more", source)
        self.assertIn("const/4 v0, 0x0\n    invoke-virtual {v5, v0}", source)
        self.assertIn("gramForgeSelectNotInterested", source)
        self.assertIn("LX/04RW;->A0b(Lcom/instagram/feed/media/mediaoption/MediaOption$Option;)V", source)
        self.assertIn(".field public gramForgeOwner:LX/09LB;", self.native.read_text())
        action = self.action.read_text()
        callback = NOT_INTERESTED["only_method"](
            action, "A04(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;"
        )
        self.assertIn("->gramForgePerformOverflowNotInterested", callback)
        self.assertNotIn("AlertDialog", action)
        self.assertNotIn("ConfirmNotInterested", action)
        self.assertNotIn("ReelsNotInterested;->show", action)
        self.assertIn("->gramForgeSelectNotInterested", action)
        self.assertIn("->gramForgePerformNotInterested", action)
        self.assertFalse((self.root / "smali_classes8/com/gramforge").exists())

    def test_fails_closed_on_missing_native_action(self) -> None:
        self.action.write_text(self.action.read_text().replace(
            "NotInterestedActionHandler_handleNotInterestedButtonTapped", "OtherAction"
        ))
        with self.assertRaisesRegex(NOT_INTERESTED["PatchMismatch"], "native Not interested action"):
            NOT_INTERESTED["patch"](self.root)
        self.assertFalse((self.root / "smali_classes8/com/gramforge").exists())

    def test_fails_closed_on_missing_more_tag(self) -> None:
        self.more.write_text(self.more.read_text().replace(
            '"clips_ufi_more_button_component"', '"changed_more_tag"'
        ))
        with self.assertRaisesRegex(NOT_INTERESTED["PatchMismatch"], "More factory"):
            NOT_INTERESTED["patch"](self.root)

    def test_fails_closed_if_original_overflow_action_changes(self) -> None:
        self.original_more.write_text(self.original_more.read_text().replace(
            "ClipsOrganicMoreOptionsHelper_handleSeeFewer", "OtherAction"
        ))
        with self.assertRaisesRegex(NOT_INTERESTED["PatchMismatch"], "organic More"):
            NOT_INTERESTED["patch"](self.root)


class CurrentInstagramPatchTest(unittest.TestCase):
    """Self-contained regression for Instagram 454.0.0.54.77 changes."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_organic_reels_action_direct_and_ads_untouched(self) -> None:
        put(self.root, "0Bhj", """.class public LX/0Bhj;
.method private final A0G(LX/14ys;Ljava/lang/Integer;JJ)LX/00e5;
    .locals 2
    const-string v0, "clips_ufi_more_button_component"
    invoke-static {}, LX/0Bhj;->A0F()LX/00e5;
    return-object v0
.end method
.method public static final A0F(LX/14ys;LX/0Bhj;Ljava/lang/Integer;Ljava/lang/String;Lkotlin/jvm/functions/Function1;JJZZ)LX/00e5;
    .locals 22
    const v1, 0x7f13594a

    invoke-static {v7, v1}, LX/00P2;->A0Q(LX/0FY3;I)Ljava/lang/String;
    const v0, 0x7f0827f0
    const v0, 0x7f0827ed
    iget-boolean v0, v5, LX/03f3;->A19:Z
    :cond_6
    invoke-static {v7, v0}, LX/00P2;->A0P(LX/0FY3;I)Landroid/graphics/drawable/Drawable;
    return-object v0
.end method
""")
        callback = put(self.root, "0IAt", """.class public LX/0IAt;
.method public final bridge synthetic invoke(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
    .locals 37
    :pswitch_4
    const-string v0, "ads_more_button_tap"
    :pswitch_5
    check-cast v0, LX/03f3;
    iput-object v8, v3, LX/06UU;->A01:LX/07FC;

    iget-object v1, v3, LX/06UU;->A0P:LX/06UO;
    const-string v0, "ClipsOrganicMediaItemViewMoreOptionsController_showSimplifiedContextMenu"
    :goto_1
    return-object v0
.end method
""")
        put(self.root, "06VX", """.class public LX/06VX;
.method public final A0a(Lcom/instagram/feed/media/mediaoption/MediaOption$Option;)V
    .locals 1
    const-string v0, "ClipsOrganicMoreOptionsHelper_handleSeeFewer"
    invoke-virtual {p0, p1}, LX/06VX;->A0a(Lcom/instagram/feed/media/mediaoption/MediaOption$Option;)V
    return-void
.end method
""")
        before = callback.read_bytes()
        NOT_INTERESTED["patch"](self.root, check=True)
        self.assertEqual(callback.read_bytes(), before)
        NOT_INTERESTED["patch"](self.root)
        updated = callback.read_text()
        self.assertIn("LX/06VX;->A0a(", updated)
        self.assertIn("->NOT_INTERESTED:", updated)
        self.assertIn('ads_more_button_tap', updated)
        self.assertIn('goto/16 :goto_1', updated)
        renderer = NOT_INTERESTED["only_path"](self.root, "0Bhj").read_text()
        self.assertIn("const v0, 0x7f0825a0", renderer)
        self.assertIn("const v1, 0x7f131e9b", renderer)
        self.assertIn("if-nez v14, :gramforge_more_drawable", renderer)


if __name__ == "__main__":
    unittest.main()
