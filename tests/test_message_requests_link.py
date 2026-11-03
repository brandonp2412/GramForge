#!/usr/bin/env python3
"""Tests for Instagram Direct inbox Message Requests link patch."""
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


class MessageRequestsLinkPatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.file = self.root / "smali_classes26/X/05PM.smali"
        self.file.parent.mkdir(parents=True)
        self.file.write_text(INBOX)
        self.primary_file = self.root / "smali_classes12/X/0RDL.smali"
        self.primary_file.parent.mkdir(parents=True)
        self.primary_file.write_text(PRIMARY)

    def test_check_does_not_write(self):
        before = self.file.read_bytes()
        primary_before = self.primary_file.read_bytes()
        PATCH["patch"](self.root, check=True)
        self.assertEqual(before, self.file.read_bytes())
        self.assertEqual(primary_before, self.primary_file.read_bytes())

    def test_only_requests_link_is_hidden(self):
        PATCH["patch"](self.root)
        updated = self.file.read_text()
        self.assertNotIn(PATCH["REQUEST_ADD"], updated)
        self.assertIn("invoke-virtual {v0, v10}, Ljava/util/AbstractCollection;->add", updated)
        self.assertIn("LX/05Bw;->A07(LX/05Ku;LX/0B7l;)V", updated)
        self.assertIn("LX/01tK;->A00:LX/01tK;", updated)
        self.assertIn(".method public final A07()V", updated)
        primary = self.primary_file.read_text()
        self.assertIn(PATCH["PRIMARY_SKIP"] + PATCH["PRIMARY_ADD"], primary)
        self.assertEqual(primary.count(PATCH["PRIMARY_ADD"]), 1)
        self.assertIn("    sget-object v6, LX/01tK;->A00:LX/01tK;", primary)
        self.assertIn("    goto/16 :goto_4", primary)

    def test_no_write_if_request_mode_changes(self):
        self.file.write_text(INBOX.replace("LX/01tK;", "LX/01tJ;"))
        before = self.file.read_bytes()
        with self.assertRaises(PATCH["PatchMismatch"]):
            PATCH["patch"](self.root)
        self.assertEqual(before, self.file.read_bytes())

    def test_no_write_if_item_addition_changes(self):
        self.file.write_text(INBOX.replace("invoke-virtual {v0, v12}", "invoke-virtual {v0, v13}"))
        before = self.file.read_bytes()
        with self.assertRaises(PATCH["PatchMismatch"]):
            PATCH["patch"](self.root)
        self.assertEqual(before, self.file.read_bytes())

    def test_primary_mismatch_preserves_both_classes(self):
        self.primary_file.write_text(PRIMARY.replace(
            "invoke-virtual {v7, v1}", "invoke-virtual {v7, v2}"
        ))
        legacy_before = self.file.read_bytes()
        primary_before = self.primary_file.read_bytes()
        with self.assertRaises(PATCH["PatchMismatch"]):
            PATCH["patch"](self.root)
        self.assertEqual(legacy_before, self.file.read_bytes())
        self.assertEqual(primary_before, self.primary_file.read_bytes())

    def test_missing_primary_fails_closed(self):
        self.primary_file.unlink()
        with self.assertRaises(PATCH["PatchMismatch"]):
            PATCH["patch"](self.root)
        self.assertEqual(INBOX, self.file.read_text())

    def test_no_write_with_ambiguous_class(self):
        other = self.root / "smali_classes27/X/05PM.smali"
        other.parent.mkdir(parents=True)
        other.write_text(INBOX)
        with self.assertRaises(PATCH["PatchMismatch"]):
            PATCH["patch"](self.root)
        self.assertEqual(INBOX, self.file.read_text())


if __name__ == "__main__":
    unittest.main()
