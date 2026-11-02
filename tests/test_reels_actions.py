#!/usr/bin/env python3
"""Regression tests for the GramForge-owned Reels Save/Repost smali patch."""
from __future__ import annotations

import runpy
import tempfile
import unittest
from pathlib import Path


MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "tools/patch-reels-actions.py"))
patch = MODULE["patch"]
PatchMismatch = MODULE["PatchMismatch"]


class ReelsActionPatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.smali = self.root / "smali_classes27/X"
        self.smali.mkdir(parents=True)
        self.ufi = self.smali / "Ufi.smali"
        self.ufi.write_text("""\
.class public final LX/Ufi;
.super Ljava/lang/Object;

.method private final A0J(LX/Param;JJZ)LX/Animated;
    .locals 1
    new-instance v0, LX/Animated;
    invoke-direct {v0}, LX/Animated;-><init>()V
    return-object v0
.end method

.method private final A0K(LX/Param;JJ)LX/Save;
    .locals 1
    const-string v0, "ClipsUfiComponent_maybeCreateSaveButtonComponent"
    new-instance v0, LX/Save;
    invoke-direct {v0}, LX/Save;-><init>()V
    return-object v0
.end method

.method private final A04(LX/Param;JJ)LX/00Ax;
    .locals 2
    invoke-interface {v3}, LX/Data;->DMp()LX/0Ndt;
    const-string v1, "ufi_count"
    new-instance v0, LX/00Ax;
    return-object v0
.end method

.method private final A05(LX/Param;JJ)LX/00Ax;
    .locals 1
    const-string v0, "ClipsUfiComponent_maybeCreateSaveCountComponent"
    const-string v0, "save_count"
    new-instance v0, LX/00Ax;
    return-object v0
.end method

.method public final render()V
    .locals 15
    invoke-direct/range {v7 .. v14}, LX/Ufi;->A0J(LX/Param;JJZ)LX/Animated;
    move-result-object v0
    invoke-virtual {v5, v0}, LX/Builder;->A00(LX/05x0;)V
    invoke-direct/range {v7 .. v12}, LX/Ufi;->A04(LX/Param;JJ)LX/00Ax;
    move-result-object v0
    invoke-virtual {v5, v0}, LX/Builder;->A00(LX/05x0;)V
    invoke-direct/range {v7 .. v12}, LX/Ufi;->A0K(LX/Param;JJ)LX/Save;
    move-result-object v0
    invoke-virtual {v5, v0}, LX/Builder;->A00(LX/05x0;)V
    invoke-direct/range {v7 .. v12}, LX/Ufi;->A05(LX/Param;JJ)LX/00Ax;
    move-result-object v0
    invoke-virtual {v5, v0}, LX/Builder;->A00(LX/05x0;)V
    return-void
.end method
""")
        (self.smali / "Save.smali").write_text("""\
.class public final LX/Save;
.super LX/05x0;
.method public final A0o()V
    .locals 1
    const-string v0, "ClipsSaveButtonComponent_render"
    return-void
.end method
""")
        (self.smali / "Animated.smali").write_text("""\
.class public final LX/Animated;
.super LX/05x0;
.method public final A0o()V
    .locals 1
    const-string v0, "ClipsAnimatedRepostButtonComponent_render"
    new-instance v0, LX/RepostChild;
    return-void
.end method
""")
        (self.smali / "RepostChild.smali").write_text("""\
.class public final LX/RepostChild;
.super LX/05x0;
.method public final A0o()V
    .locals 1
    const-string v0, "ClipsRepostButtonComponent_render"
    return-void
.end method
""")
        self.builder = self.smali / "Builder.smali"
        self.builder.write_text("""\
.class public final LX/Builder;
.super Ljava/lang/Object;
.method public final A00(LX/05x0;)V
    .locals 1
    if-eqz p1, :cond_0
    iget-object v0, p0, LX/Builder;->A00:Ljava/util/List;
    invoke-interface {v0, p1}, Ljava/util/List;->add(Ljava/lang/Object;)Z
    :cond_0
    return-void
.end method
""")
        self.post = self.smali / "FeedPost.smali"
        self.post.write_text(".class public final LX/FeedPost;\n# Feed Save/Repost untouched\n")

    def test_removes_only_reels_action_factories(self) -> None:
        before_post = self.post.read_bytes()
        before_save = (self.smali / "Save.smali").read_bytes()
        before_child = (self.smali / "RepostChild.smali").read_bytes()
        self.assertEqual(patch(self.root), ["Save", "Repost", "Save count", "Repost count"])
        changed = self.ufi.read_text()
        self.assertEqual(changed.count("const/4 v0, 0x0"), 4)
        self.assertEqual(changed.count("new-instance v0, LX/Save;"), 0)
        self.assertEqual(changed.count("new-instance v0, LX/Animated;"), 0)
        self.assertEqual(changed.count("new-instance v0, LX/00Ax;"), 0)
        self.assertIn("invoke-virtual {v5, v0}, LX/Builder;->A00", changed)
        self.assertEqual(self.post.read_bytes(), before_post)
        self.assertEqual((self.smali / "Save.smali").read_bytes(), before_save)
        self.assertEqual((self.smali / "RepostChild.smali").read_bytes(), before_child)

    def test_check_does_not_mutate(self) -> None:
        original = self.ufi.read_bytes()
        self.assertEqual(patch(self.root, check=True), ["Save", "Repost", "Save count", "Repost count"])
        self.assertEqual(self.ufi.read_bytes(), original)

    def test_fails_closed_if_builder_no_longer_skips_null(self) -> None:
        self.builder.write_text(self.builder.read_text().replace("if-eqz p1", "if-nez p1"))
        before = self.ufi.read_bytes()
        with self.assertRaisesRegex(PatchMismatch, "no longer safely skips null"):
            patch(self.root)
        self.assertEqual(self.ufi.read_bytes(), before)

    def test_fails_closed_if_repost_factory_changes(self) -> None:
        self.ufi.write_text(self.ufi.read_text().replace("new-instance v0, LX/Animated;", "new-instance v0, LX/Other;"))
        with self.assertRaisesRegex(PatchMismatch, "expected one Reels factory"):
            patch(self.root)

    def test_fails_closed_if_append_behavior_changes(self) -> None:
        self.ufi.write_text(self.ufi.read_text().replace(
            "invoke-virtual {v5, v0}, LX/Builder;->A00(LX/05x0;)V",
            "invoke-virtual {v5, v0}, LX/Builder;->A01(LX/05x0;)V",
            1,
        ))
        with self.assertRaisesRegex(PatchMismatch, "Reels buttons and count rows no longer share one action builder"):
            patch(self.root)

    def test_fails_closed_if_repost_child_changes(self) -> None:
        animated = self.smali / "Animated.smali"
        animated.write_text(animated.read_text().replace("LX/RepostChild;", "LX/Other;"))
        with self.assertRaisesRegex(PatchMismatch, "Reels Repost child no longer present"):
            patch(self.root)

    def test_fails_closed_if_save_count_marker_disappears(self) -> None:
        self.ufi.write_text(self.ufi.read_text().replace(
            "ClipsUfiComponent_maybeCreateSaveCountComponent",
            "ObsoleteSaveCountMarker",
        ))
        with self.assertRaisesRegex(PatchMismatch, "save_count component marker"):
            patch(self.root)

    def test_fails_closed_if_repost_count_is_detached(self) -> None:
        self.ufi.write_text(self.ufi.read_text().replace(
            "invoke-direct/range {v7 .. v12}, LX/Ufi;->A04(LX/Param;JJ)LX/00Ax;",
            "invoke-direct/range {v7 .. v12}, LX/Ufi;->Other(LX/Param;JJ)LX/00Ax;",
        ))
        with self.assertRaisesRegex(PatchMismatch, "Repost count factory"):
            patch(self.root)


if __name__ == "__main__":
    unittest.main()
