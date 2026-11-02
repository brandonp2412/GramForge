#!/usr/bin/env python3
"""Small, deterministic fixtures for the two independently owned UI patches."""
from __future__ import annotations

import runpy
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOT_INTERESTED = runpy.run_path(str(ROOT / "tools/patch-reels-not-interested.py"))
NUDGES = runpy.run_path(str(ROOT / "tools/patch-notification-nudges.py"))


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

FEED = """.class public final LX/05QL;
.method public static final A00(Landroid/content/Context;Lcom/instagram/common/session/UserSession;Ljava/lang/String;)Z
    .locals 1
    const-string v0, "notification_feed"
    const-string v0, "direct_inbox"
    const-string v0, "preference_has_allowed_push_system_dialog"
    const/4 v0, 0x1
    return v0
.end method
"""
ONBOARDING = """.class public final LX/0gKg;
.method public final A00()Z
    .locals 1
    const-string v0, "skip_push_opt_in_already_asked"
    const-string v0, "skip_push_opt_in_has_permission_already"
    const/4 v0, 0x1
    return v0
.end method
"""
ROW = """.class public final LX/0C4e;
.method public static final A0H(LX/1BaO;Ljava/lang/String;Lkotlin/jvm/functions/Function1;I)V
    .locals 1
    const-string v0, "com.instagram.newsfeed.fragment.PushNotificationUpsellRow"
    const v0, 0x7f138dc8
    return-void
.end method
"""
QP = """.class public final LX/02jE;
.method public final Gz9(Landroid/content/Context;LX/0Rbe;Lcom/instagram/common/session/UserSession;LX/0CgN;LX/0lhn;Lcom/instagram/quickpromotion/intf/QuickPromotionSlot;Ljava/util/List;)V
    .locals 28
    :goto_0
    invoke-interface {v19}, Ljava/util/Iterator;->next()Ljava/lang/Object;
    move-result-object v6
    move-object v5, v6

    check-cast v5, LX/044I;

    iget-object v1, v5, LX/044I;->A07:Lcom/instagram/quickpromotion/intf/QuickPromotionSurface;
    const-string v0, "notification_permission_prompt"
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


class NotificationNudgePatchTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.paths = {
            "feed": put(self.root, "05QL", FEED),
            "onboarding": put(self.root, "0gKg", ONBOARDING),
            "row": put(self.root, "0C4e", ROW),
            "qp": put(self.root, "02jE", QP),
        }

    def test_check_only(self) -> None:
        before = {key: path.read_bytes() for key, path in self.paths.items()}
        NUDGES["patch"](self.root, check=True)
        self.assertEqual(before, {key: path.read_bytes() for key, path in self.paths.items()})

    def test_nudges_suppressed_without_touching_permission_api(self) -> None:
        NUDGES["patch"](self.root)
        self.assertIn("const/4 v0, 0x0", self.paths["feed"].read_text())
        self.assertNotIn("notification_feed", self.paths["feed"].read_text())
        self.assertNotIn("PushNotificationUpsellRow", self.paths["row"].read_text())
        self.assertIn("if-nez v0, :goto_0", self.paths["qp"].read_text())
        self.assertIn("notification_permission_prompt", self.paths["qp"].read_text())

    def test_fails_closed_on_removed_promotion_name(self) -> None:
        self.paths["qp"].write_text(self.paths["qp"].read_text().replace(
            "notification_permission_prompt", "other_promo"
        ))
        before = {key: path.read_bytes() for key, path in self.paths.items()}
        with self.assertRaisesRegex(NUDGES["PatchMismatch"], "notification Quick Promotion"):
            NUDGES["patch"](self.root)
        self.assertEqual(before, {key: path.read_bytes() for key, path in self.paths.items()})


if __name__ == "__main__":
    unittest.main()
