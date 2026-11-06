#!/usr/bin/env python3
"""Regression tests for the Instagram 454 Direct inbox Requests patch."""
from __future__ import annotations

import runpy
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCH = runpy.run_path(str(ROOT / "tools/patch-message-requests-link.py"))

INBOX = """.class public final LX/05PM;
.super Ljava/lang/Object;

.method public final A06()V
    .locals 23
    new-instance v0, Ljava/util/ArrayList;
    invoke-direct {v0}, Ljava/util/ArrayList;-><init>()V
    const v4, 0x7f133e29
    sget-object v12, LX/00TD;->A00:LX/00TD;
    invoke-virtual {v0, v10}, Ljava/util/AbstractCollection;->add(Ljava/lang/Object;)Z
    const v7, 0x7f133e2b
    invoke-static {v7}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;
    sget-object v14, LX/01tK;->A00:LX/01tK;
    new-instance v12, LX/0X7V;
    invoke-direct/range {v12 .. v22}, LX/0X7V;-><init>(LX/0RDO;LX/06Zx;Ljava/lang/Integer;Ljava/lang/Integer;Ljava/lang/Integer;Ljava/lang/Integer;Ljava/util/Set;ZZZ)V
    invoke-virtual {v0, v12}, Ljava/util/AbstractCollection;->add(Ljava/lang/Object;)Z
    new-instance v5, LX/05Ku;
    invoke-direct {v5, v2, v1, v0, v6}, LX/05Ku;-><init>(LX/06Zx;LX/0Jnp;Ljava/util/List;Z)V
    invoke-virtual {v3, v5, v4}, LX/05Bw;->A07(LX/05Ku;LX/0B7l;)V
    return-void
.end method

.method public final A07()V
    .locals 0
    return-void
.end method
"""

PRIMARY = """.class public final LX/0RDL;
.super Ljava/lang/Object;

.method public final A01(Lcom/instagram/common/session/UserSession;LX/06Zx;LX/0Jnp;IZZZ)LX/05Ku;
    .locals 32
    :goto_4
    iget-object v1, v4, Landroid/util/Pair;->second:Ljava/lang/Object;
    sget-object v6, LX/01tK;->A00:LX/01tK;
    invoke-static {v1, v6}, LX/00d6;->areEqual(Ljava/lang/Object;Ljava/lang/Object;)Z
    move-result v1
    new-instance v1, LX/0X7V;
    invoke-direct/range {v21 .. v31}, LX/0X7V;-><init>(LX/0RDO;LX/06Zx;Ljava/lang/Integer;Ljava/lang/Integer;Ljava/lang/Integer;Ljava/lang/Integer;Ljava/util/Set;ZZZ)V
    invoke-virtual {v7, v1}, Ljava/util/AbstractCollection;->add(Ljava/lang/Object;)Z
    goto/16 :goto_4
.end method
"""

HEADER = """.class public abstract LX/0ZY5;
.super Ljava/lang/Object;

.method public static final A01(LX/1BaO;LX/05KL;Lkotlin/jvm/functions/Function0;Lkotlin/jvm/functions/Function0;I)V
    .locals 22
    const-string v0, "instagram.features.direct.inbox.feature.inboxheader.ui.DefaultHeader"
    const-string v0, "header_action_button"
    iget-object v2, v6, LX/05KL;->A02:Ljava/lang/String;
    const-string v0, "Messages"
    invoke-static {v10}, LX/04cX;->renderTitle(Ljava/lang/String;)V
    move-object v10, v7

    move-object v13, v2

    move-wide/from16 v14, v19

    invoke-static/range {v10 .. v15}, LX/04cX;->A1T(LX/1BaO;LX/05n4;LX/04cD;Ljava/lang/String;J)V
    return-void
.end method

.method public static final A03()V
    .locals 1
    const-string v0, "Messages sort"
    return-void
.end method
"""


CONTROLLER = """.class public final LX/04TH;
.super Ljava/lang/Object;

.method public final A0I(Landroid/view/View;)V
    .locals 42

    move-object/from16 v8, p1
    const-string v2, "DirectInboxController.onCreateView"
    const v2, 0x7f0b2067
    :cond_2a
    return-void
.end method
"""



class MessageRequestsLinkPatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.legacy = self.root / "smali_classes26/X/05PM.smali"
        self.primary = self.root / "smali_classes12/X/0RDL.smali"
        self.header = self.root / "smali_classes26/X/0ZY5.smali"
        self.controller = self.root / "smali_classes26/X/04TH.smali"
        self.helper = self.root / "smali_classes26/com/gramforge/DirectRequestsHeaderFilter.smali"
        for path, content in ((self.legacy, INBOX), (self.primary, PRIMARY), (self.header, HEADER), (self.controller, CONTROLLER)):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

    def contents(self):
        return tuple(path.read_bytes() for path in (self.legacy, self.primary, self.header, self.controller))

    def test_check_does_not_write(self):
        before = self.contents()
        PATCH["patch"](self.root, check=True)
        self.assertEqual(before, self.contents())
        self.assertFalse(self.helper.exists())

    def test_hides_only_requests_navigation_and_compose_action(self):
        PATCH["patch"](self.root)
        legacy = self.legacy.read_text()
        self.assertNotIn(PATCH["REQUEST_ADD"], legacy)
        self.assertIn("invoke-virtual {v0, v10}, Ljava/util/AbstractCollection;->add", legacy)
        self.assertIn(".method public final A07()V", legacy)
        primary = self.primary.read_text()
        self.assertIn(PATCH["PRIMARY_SKIP"] + PATCH["PRIMARY_ADD"], primary)
        self.assertEqual(primary.count(PATCH["PRIMARY_ADD"]), 1)
        header = self.header.read_text()
        self.assertNotIn("invoke-static/range {v10 .. v15}, LX/04cX;->A1T", header)
        self.assertIn('const-string v0, "Messages"', header)
        self.assertIn("renderTitle(Ljava/lang/String;)V", header)
        self.assertIn('.method public static final A03()V', header)
        self.assertEqual(header.count('header_action_button'), 1)
        self.assertEqual(len(list(self.root.rglob("*.smali"))), 5)
        controller = self.controller.read_text()
        self.assertIn(PATCH["CONTROLLER_HOOK"], controller)
        self.assertEqual(controller.count("DirectRequestsHeaderFilter;->install"), 1)
        helper = self.helper.read_text()
        self.assertIn('const-string v2, "Requests"', helper)
        self.assertIn("Landroid/view/ViewTreeObserver$OnGlobalLayoutListener;", helper)

    def test_fails_closed_when_compose_action_changed(self):
        self.header.write_text(HEADER.replace(
            "invoke-static/range {v10 .. v15}", "invoke-static/range {v10 .. v14}"
        ))
        before = self.contents()
        with self.assertRaises(PATCH["PatchMismatch"]):
            PATCH["patch"](self.root)
        self.assertEqual(before, self.contents())

    def test_fails_closed_when_compose_label_moved(self):
        self.header.write_text(HEADER.replace('"header_action_button"', '"action_changed"'))
        before = self.contents()
        with self.assertRaises(PATCH["PatchMismatch"]):
            PATCH["patch"](self.root)
        self.assertEqual(before, self.contents())

    def test_fails_closed_when_primary_changed(self):
        self.primary.write_text(PRIMARY.replace("invoke-virtual {v7, v1}", "invoke-virtual {v7, v2}"))
        before = self.contents()
        with self.assertRaises(PATCH["PatchMismatch"]):
            PATCH["patch"](self.root)
        self.assertEqual(before, self.contents())

    def test_fails_closed_when_legacy_changed(self):
        self.legacy.write_text(INBOX.replace("invoke-virtual {v0, v12}", "invoke-virtual {v0, v13}"))
        before = self.contents()
        with self.assertRaises(PATCH["PatchMismatch"]):
            PATCH["patch"](self.root)
        self.assertEqual(before, self.contents())

    def test_fails_closed_when_header_is_missing(self):
        self.header.unlink()
        before = (self.legacy.read_bytes(), self.primary.read_bytes())
        with self.assertRaises(PATCH["PatchMismatch"]):
            PATCH["patch"](self.root)
        self.assertEqual(before, (self.legacy.read_bytes(), self.primary.read_bytes()))

    def test_fails_closed_when_header_is_ambiguous(self):
        other = self.root / "smali_classes27/X/0ZY5.smali"
        other.parent.mkdir(parents=True)
        other.write_text(HEADER)
        before = self.contents()
        with self.assertRaises(PATCH["PatchMismatch"]):
            PATCH["patch"](self.root)
        self.assertEqual(before, self.contents())


    def test_fails_closed_when_controller_changed(self):
        self.controller.write_text(CONTROLLER.replace("0x7f0b2067", "0x7f0b2066"))
        before = self.contents()
        with self.assertRaises(PATCH["PatchMismatch"]):
            PATCH["patch"](self.root)
        self.assertEqual(before, self.contents())
        self.assertFalse(self.helper.exists())

    def test_fails_closed_when_helper_exists(self):
        self.helper.parent.mkdir(parents=True)
        self.helper.write_text("already owned")
        before = self.contents()
        with self.assertRaises(PATCH["PatchMismatch"]):
            PATCH["patch"](self.root)
        self.assertEqual(before, self.contents())
        self.assertEqual(self.helper.read_text(), "already owned")

    def test_fails_closed_when_controller_is_missing(self):
        self.controller.unlink()
        before = (self.legacy.read_bytes(), self.primary.read_bytes(), self.header.read_bytes())
        with self.assertRaises(PATCH["PatchMismatch"]):
            PATCH["patch"](self.root)
        self.assertEqual(before, (self.legacy.read_bytes(), self.primary.read_bytes(), self.header.read_bytes()))
        self.assertFalse(self.helper.exists())

if __name__ == "__main__":
    unittest.main()
