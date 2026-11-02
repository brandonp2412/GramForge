#!/usr/bin/env python3
"""Deterministic tests for the Instagram Compose comment-row filter."""
from __future__ import annotations

import runpy
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCH = runpy.run_path(str(ROOT / "tools/patch-comment-filter.py"))
ROW = """.class public abstract LX/0Hex;
.super Ljava/lang/Object;
.method public static final A00(LX/1BaO;LX/05n4;LX/0Il1;LX/0Hxu;LX/0iom;LX/0Hes;IIZZZZZ)V
    .locals 59

    const/4 v10, 0x0

    move-object/from16 v5, p2

    invoke-static {v5, v10}, LX/00d6;->A0V(Ljava/lang/Object;I)V

    const/4 v14, 0x1

    const v1, 0x2a42899e

    move-object/from16 v0, p0

    invoke-interface {v0, v1}, LX/1BaO;->Hg2(I)V

    iget-object v9, v5, LX/0Il1;->A0O:Ljava/lang/String;

    const-string v3, "com.instagram.comments.mvvm.view.compose.CommentRow (CommentRow.kt:62)"

    return-void
.end method
"""


class CommentFilterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.row = self.root / "smali_classes28/X/0Hex.smali"
        self.row.parent.mkdir(parents=True)
        self.row.write_text(ROW)

    def test_only_checks_without_mutation(self) -> None:
        before = self.row.read_bytes()
        self.assertEqual(len(PATCH["patch"](self.root, check=True)), 1)
        self.assertEqual(self.row.read_bytes(), before)

    def test_hides_entire_row_before_compose_renders(self) -> None:
        PATCH["patch"](self.root)
        result = self.row.read_text()
        self.assertIn('LX/0Il1;->A0O:Ljava/lang/String;', result)
        self.assertIn('Ljava/util/Locale;->ROOT:Ljava/util/Locale;', result)
        self.assertIn('Ljava/lang/String;->toLowerCase(Ljava/util/Locale;)Ljava/lang/String;', result)
        self.assertIn('const-string v1, "your page"', result)
        self.assertIn('Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z', result)
        self.assertLess(result.index('return-void\n\n    :gramforge_comment_visible'), result.index('->Hg2(I)V'))
        self.assertIn('if-eqz v0, :gramforge_comment_visible', result)

    def test_examples_match_phrase_independent_of_case(self) -> None:
        matching = [
            "why do i get a warning when i follow your page?",
            "your page is so funny",
            "your page is so crazy",
            "YOUR PAGE is hilarious",
            "I love your page.",
        ]
        not_matching = [
            "your posts are funny",
            "What page is this?",
            "You're on my page",
            "They said your Instagram page is nice",
        ]
        for comment in matching:
            with self.subTest(comment=comment):
                self.assertIn("your page", comment.lower())
        for comment in not_matching:
            with self.subTest(comment=comment):
                self.assertNotIn("your page", comment.lower())

    def test_refuses_second_application(self) -> None:
        PATCH["patch"](self.root)
        with self.assertRaisesRegex(PATCH["PatchMismatch"], "already applied"):
            PATCH["patch"](self.root)

    def test_fails_closed_if_comment_body_field_changes(self) -> None:
        self.row.write_text(ROW.replace("->A0O:Ljava/lang/String;", "->A0N:Ljava/lang/String;"))
        original = self.row.read_bytes()
        with self.assertRaisesRegex(PATCH["PatchMismatch"], "model text field changed"):
            PATCH["patch"](self.root)
        self.assertEqual(self.row.read_bytes(), original)

    def test_fails_closed_if_renderer_changes(self) -> None:
        self.row.write_text(ROW.replace("CommentRow (CommentRow.kt:62)", "RenamedRow (CommentRow.kt:62)"))
        with self.assertRaisesRegex(PATCH["PatchMismatch"], "expected one Compose CommentRow"):
            PATCH["patch"](self.root)


if __name__ == "__main__":
    unittest.main()
