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
        self.assertEqual(len(PATCH["patch"](self.root, check=True)), 3)
        self.assertEqual(self.row.read_bytes(), before)
        self.assertFalse((self.root / "smali_classes28/com/gramforge/CommentFilter.smali").exists())

    def test_current_instagram_454_54_77_row(self) -> None:
        updated = (
            ROW.replace(
                "A00(LX/1BaO;LX/05n4;LX/0Il1;LX/0Hxu;LX/0iom;LX/0Hes;IIZZZZZ)V",
                "A00(LX/14xx;LX/03Um;LX/0JBJ;LX/0INL;LX/0loo;LX/0ICJ;IIZZZZZ)V",
            )
            .replace("LX/0Il1;", "LX/0JBJ;")
            .replace("const/4 v10, 0x0", "const/4 v8, 0x0")
            .replace("invoke-static {v5, v10}, LX/00d6;->A0V",
                     "invoke-static {v5, v8}, LX/00f5;->A0W")
            .replace("LX/1BaO;->Hg2(I)V", "LX/14xx;->HgJ(I)V")
        )
        self.row.write_text(updated)
        self.assertEqual(len(PATCH["patch"](self.root, check=True)), 3)
        PATCH["patch"](self.root)
        rendered = self.row.read_text()
        self.assertIn("LX/0JBJ;->A0O:Ljava/lang/String;", rendered)
        self.assertLess(rendered.index("gramforge_comment_visible"),
                        rendered.index("LX/14xx;->HgJ(I)V"))

    def test_hides_entire_row_before_compose_renders(self) -> None:
        PATCH["patch"](self.root)
        result = self.row.read_text()
        helper = (self.root / "smali_classes28/com/gramforge/CommentFilter.smali").read_text()
        self.assertIn("LX/0Il1;->A0O:Ljava/lang/String;", result)
        self.assertIn("Lcom/gramforge/CommentFilter;->shouldHide(Ljava/lang/String;)Z", result)
        self.assertLess(
            result.index("return-void\n\n    :gramforge_comment_visible"),
            result.index("->Hg2(I)V"),
        )
        self.assertIn("if-eqz v0, :gramforge_comment_visible", result)
        self.assertIn("Ljava/text/Normalizer;->normalize(", helper)
        self.assertIn("Ljava/util/Locale;->ROOT:Ljava/util/Locale;", helper)
        self.assertIn("Ljava/lang/String;->toLowerCase(Ljava/util/Locale;)", helper)
        self.assertIn('const-string v1, "[^\\\\p{L}\\\\p{N}]+"', helper)
        self.assertEqual(helper.count("Ljava/util/regex/Pattern;->compile"), len(PATCH["PATTERNS"]))
        self.assertEqual(helper.count("Ljava/util/regex/Matcher;->find"), len(PATCH["PATTERNS"]))

    def test_formulaic_comments_are_hidden(self) -> None:
        matching = [
            "why do i get a warning when i follow your page?",
            "your page is so funny",
            "your page is so crazy",
            "YOUR PAGE is hilarious",
            "I love your page.",
            "your posts are funny",
            "Your profile picture is hilarious!",
            "They said your Instagram page is nice", "What page is this?",
            "You're on my page", "That's so funny", "It's really amazing",
            "Do you accept crypto?",
            "DM me the recipe please",
            "Congratulations on winning!",
            "wow", "so funny", "Great post!", "love this", "BRO 💀",
            "The comments never disappoint", "This is so hilarious",
            "You are so funny", "Anyone else watching in 2026?",
            "Who else is here?", "Is it just me or...",
            "What camera do you use?", "lol 😂😂",
            "🔥🔥🔥", "😂😭❤️", "🙌🏻",
            "Follow for follow!", "Promote it on @hype",
            "DM me for collabs", "Free followers",
            "Check out my profile", "Link in my bio",
            "OnlyFans in my bio", "Click the link",
            "Congratulations you won a prize", "Claim your reward",
            "Recover your funds", "Invest in Bitcoin for guaranteed profits",
            "DM on WhatsApp for crypto profit",
            "Your account has been suspended, verify your account",
            "Copyright violation",
            "ＹＯＵＲ　ＰＡＧＥ is so fun",
        ]
        for comment in matching:
            with self.subTest(comment=comment):
                self.assertTrue(PATCH["should_hide"](comment), comment)

    def test_unusual_specific_comments_stay_visible(self) -> None:
        kept = [
            "The pigeon is invoicing the sky.",
            "I heard the microwave ask for overtime",
            "A committee of potatoes approved this",
            "Who gave that possum a forklift licence?",
            "That blender has better acting range than the entire cast.",
            "The photographer needs a raise for this shot.",
            "Why does the blue chair have a traffic ticket?",
            "I use this camera for slow motion archival footage",
            "A crab could have filed the paperwork faster",
            "I would trust that squirrel with my tax return",
        ]
        for comment in kept:
            with self.subTest(comment=comment):
                self.assertFalse(PATCH["should_hide"](comment), comment)
        self.assertFalse(PATCH["should_hide"](None))

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
