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

DIRECT_THREAD = """.class public final LX/02Ru;
.method public static final A00(Lcom/instagram/common/session/UserSession;LX/02Nt;LX/0QaX;LX/02Ru;)V
    .locals 29
    move-object/from16 v6, p3
    iget-object v0, v6, LX/02Ru;->A00:Ljava/lang/Integer;

    move-object/from16 v20, p0

    move-object/from16 v22, p2

    if-nez v0, :cond_3
    const v0, 0x7f0b31dd
    const-string v13, "NF_REACHABILITY_UPSELL_LAST_FIBONACCI_COOL_DOWN_UNTIL"
    const-string v0, "nf_reachability_upsell_limits_direct_thread"
    const v0, 0x7f0b31dc
    new-instance v1, LX/0Ra9;
    :cond_3
    const-string v0, "preserve unrelated conversation banners"
    return-void
.end method
"""


REACHABILITY_FACTORY = """.class public final LX/0STR;
.method public static A00()V
    .locals 5
    new-instance v4, LX/0S6U;
    new-instance v4, LX/0RJO;
    new-instance v4, LX/0S47;
    new-instance v4, LX/0hf6;
    return-void
.end method
"""

REACHABILITY_CLASSES = {
    "0S6U": ("LX/0S6U;->A03:LX/06KJ;", "LX/06KJ;->A01("),
    "0RJO": ("LX/0RJO;->A02:Lcom/instagram/common/session/UserSession;",
             "V2_REACHABILITY_UPSELL_GLOBAL_SHARED_DISMISS_COOLDOWN"),
    "0S47": ("LX/0S47;->A0B:LX/06KJ;", "LX/06KJ;->A01("),
    "0hf6": ("LX/0hf6;->A09:LX/0Jnv;", "LX/06KJ;->A01("),
}

DELAYED_PROMPT = """.class public LX/05QN;
.method public static final A00(Landroid/app/Activity;Landroid/view/View;Lcom/instagram/common/session/UserSession;Ljava/lang/Integer;)V
    .locals 1
    const-string v0, "preference_has_asked_push_permission_in_nux"
    const-string v0, "direct_inbox"
    const-string v0, "notification_feed"
    invoke-virtual {p1, v0, v0}, Landroid/view/View;->postDelayed(Ljava/lang/Runnable;J)Z
    return-void
.end method
"""

REFOREGROUND_TOAST = """.class public LX/0QBE;
.method public static final A01(LX/0QBE;LX/0XFB;Ljava/lang/Integer;Ljava/lang/Integer;LX/1Btm;I)V
    .locals 1
    const-string v0, "V2_REACHABILITY_UPSELL_REFOREGROUND_TOAST_LAST_SHOWN_TIMESTAMP"
    invoke-virtual {v0}, LX/0BfK;->A03()V
    sget-object v0, LX/09qf;->A01:LX/09qf;
    return-void
.end method
"""

PROFILE_STUB = """.class public LX/0QCd;
.method public static final A01(Landroid/content/Context;)V
    .locals 9
    :cond_3b
    const v8, 0x20042
    invoke-virtual {v8, v3}, LX/03ii;->A01(Landroid/content/Context;)Z
    iget-object v8, v0, LX/0Oo4;->A0H:LX/0Jnk;
    invoke-interface {v8, v2}, LX/0Jnk;->setVisibility(I)V
    :cond_3c
    const-string v0, "unrelated follow-button setup preserved"
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
            "thread": put(self.root, "02Ru", DIRECT_THREAD),
            "factory": put(self.root, "0STR", REACHABILITY_FACTORY),
            "delayed": put(self.root, "05QN", DELAYED_PROMPT),
            "toast": put(self.root, "0QBE", REFOREGROUND_TOAST),
            "profile": put(self.root, "0QCd", PROFILE_STUB),
        }
        for klass, markers in REACHABILITY_CLASSES.items():
            method = f""".class public LX/{klass};
.method public final B28()Z
    .locals 1
    const-string v0, "{markers[0]}"
    const-string v0, "{markers[1]}"
    const/4 v0, 0x1
    return v0
.end method
"""
            self.paths[klass] = put(self.root, klass, method)

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
        thread = self.paths["thread"].read_text()
        self.assertIn("goto/16 :cond_3", thread)
        self.assertNotIn("if-nez v0, :cond_3", thread)
        self.assertIn("preserve unrelated conversation banners", thread)
        for klass in REACHABILITY_CLASSES:
            self.assertIn("const/4 v0, 0x0", self.paths[klass].read_text())
            self.assertNotIn(REACHABILITY_CLASSES[klass][0], self.paths[klass].read_text())
        self.assertNotIn("postDelayed", self.paths["delayed"].read_text())
        self.assertNotIn("REFOREGROUND_TOAST_LAST_SHOWN_TIMESTAMP",
                         self.paths["toast"].read_text())
        profile = self.paths["profile"].read_text()
        self.assertIn("goto/16 :cond_3c", profile)
        self.assertIn("unrelated follow-button setup preserved", profile)

    def test_fails_closed_if_reachability_factory_changes(self) -> None:
        factory = self.paths["factory"]
        factory.write_text(factory.read_text().replace(
            "new-instance v4, LX/0S47;", "new-instance v4, LX/other;"))
        before = {key: path.read_bytes() for key, path in self.paths.items()}
        with self.assertRaisesRegex(NUDGES["PatchMismatch"],
                                    "reachability eligibility factory changed"):
            NUDGES["patch"](self.root)
        self.assertEqual(before, {key: path.read_bytes() for key, path in self.paths.items()})

    def test_fails_closed_if_delayed_prompt_changes(self) -> None:
        delayed = self.paths["delayed"]
        delayed.write_text(delayed.read_text().replace(
            "postDelayed", "otherMethod"))
        before = {key: path.read_bytes() for key, path in self.paths.items()}
        with self.assertRaisesRegex(NUDGES["PatchMismatch"],
                                    "notification-specific marker absent"):
            NUDGES["patch"](self.root)
        self.assertEqual(before, {key: path.read_bytes() for key, path in self.paths.items()})

    def test_fails_closed_if_direct_thread_banner_structure_changes(self) -> None:
        self.paths["thread"].write_text(self.paths["thread"].read_text().replace(
            "nf_reachability_upsell_limits_direct_thread", "unrelated_banner"
        ))
        before = {key: path.read_bytes() for key, path in self.paths.items()}
        with self.assertRaisesRegex(NUDGES["PatchMismatch"], "Direct-thread notification banner"):
            NUDGES["patch"](self.root)
        self.assertEqual(before, {key: path.read_bytes() for key, path in self.paths.items()})

    def test_fails_closed_on_removed_promotion_name(self) -> None:
        self.paths["qp"].write_text(self.paths["qp"].read_text().replace(
            "notification_permission_prompt", "other_promo"
        ))
        before = {key: path.read_bytes() for key, path in self.paths.items()}
        with self.assertRaisesRegex(NUDGES["PatchMismatch"], "notification Quick Promotion"):
            NUDGES["patch"](self.root)
        self.assertEqual(before, {key: path.read_bytes() for key, path in self.paths.items()})


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

    def test_notification_new_reachability_and_quick_promotion(self) -> None:
        put(self.root, "02EI", FEED.replace("05QL", "02EI"))
        put(self.root, "0M8e", ONBOARDING.replace("0gKg", "0M8e"))
        put(self.root, "0DTC", ROW.replace("0C4e", "0DTC").replace(
            "LX/1BaO;", "LX/14xx;").replace("0x7f138dc8", "0x7f138dc6"))
        qp = put(self.root, "02oJ", """.class public LX/02oJ;
.method public final GzO(Landroid/content/Context;LX/099A;Lcom/instagram/common/session/UserSession;LX/0OA1;LX/0lnA;Lcom/instagram/quickpromotion/intf/QuickPromotionSlot;Ljava/util/List;)V
    .locals 12
    :cond_23
    :goto_13
    const/4 v2, 0x1
    :cond_24
    const/4 v12, 0x1

    invoke-static {v5, v2, v1, v12}, LX/0EBO;->A00(LX/0DEM;LX/0EBO;Ljava/util/Set;Z)V
    const-string v0, "notification_permission_prompt"
    return-void
.end method
""")
        put(self.root, "0SE9", """.class public LX/0SE9;
.method public static A00()LX/0Uzz;
    .locals 5
    new-instance v4, LX/0RG1;
    new-instance v4, LX/01I3;
    new-instance v4, LX/0R9T;
    new-instance v4, LX/0kxq;
    check-cast v4, LX/0Uzz;
    return-object v4
.end method
""")
        paths = {}
        for klass in ("0RG1", "01I3", "0R9T", "0kxq"):
            methods = ['B2L()Z'] + (['B2M()Z'] if klass != '0kxq' else [])
            src = f".class public LX/{klass};\n.implements LX/0Uzz;\n"
            for method in methods:
                src += (f".method public final {method}\n    .locals 1\n"
                        f"    iget-object v0, p0, LX/{klass};->A03:LX/02Dv;\n"
                        "    const/4 v0, 0x1\n    return v0\n.end method\n")
            paths[klass] = put(self.root, klass, src)
        inbox = put(self.root, "0YVX", """.class public abstract LX/0YVX;
.method public static final A04(LX/14xx;LX/01KJ;LX/02Lu;LX/01Km;IIZ)V
    .locals 44
    const-string v0, "InboxEmptyStateRow (InboxEmptyStateRow.kt:69)"
    iget-object v4, v1, LX/01KJ;->A08:Ljava/lang/CharSequence;
    move-object/from16 v18, v4
    :goto_8
    iget-object v9, v1, LX/01KJ;->A0I:Ljava/lang/String;
    if-eqz v9, :cond_1
    invoke-static/range {v21 .. v44}, LX/0WVT;->A01(LX/0nuF;LX/14xx;LX/03Um;LX/00wB;LX/11kz;Ljava/lang/CharSequence;Ljava/lang/CharSequence;Ljava/lang/Integer;Ljava/lang/Integer;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Lkotlin/jvm/functions/Function0;Lkotlin/jvm/functions/Function0;Lkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function1;LX/03Zz;IIIJJ)V
    invoke-static {v0, v5, v4, v12, v6}, LX/0T86;->A0I(LX/14xx;LX/14az;Ljava/lang/Integer;Ljava/lang/String;Lkotlin/jvm/functions/Function0;)V
    :cond_1
    return-void
.end method
""")
        original = qp.read_bytes()
        NUDGES["patch"](self.root, check=True)
        self.assertEqual(qp.read_bytes(), original)
        NUDGES["patch"](self.root)
        self.assertIn("if-nez v0, :cond_23", qp.read_text())
        self.assertIn('const-string v4, "Turn on notifications"', inbox.read_text())
        self.assertIn("const/4 v9, 0x0", inbox.read_text())
        self.assertIn("move-object/from16 v18, v19", inbox.read_text())
        self.assertIn("LX/0WVT;->A01", inbox.read_text())
        for path in paths.values():
            self.assertNotIn("const/4 v0, 0x1", path.read_text())


if __name__ == "__main__":
    unittest.main()
