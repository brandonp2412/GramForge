#!/usr/bin/env python3
"""Replace the organic Reels More button with immediate Not interested.

Reuses Instagram's own ClipsNotInterestedButtonComponent for the icon and
Instagram's *organic More > Not interested* handler for the action. Tapping
the button acts immediately, with no custom confirmation or reasons sheet.
Sponsored media keep their native More menu.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


class PatchMismatch(Exception):
    pass


METHOD_RE = re.compile(r"(?ms)^\.method [^\n]+\n.*?^\.end method")
REELS_OWNER = "LX/09LB;"
REELS_METHOD = "A0F(LX/1Bjl;Ljava/lang/Integer;JJ)LX/04BN;"
REELS_NEW_METHOD = "A0F(LX/1Bjl;Ljava/lang/Integer;JJ)LX/05x0;"
NATIVE_ACTION_MARKER = "android_purge_26_q3_NotInterestedActionHandler_handleNotInterestedButtonTapped"


def only_path(root: Path, class_name: str) -> Path:
    matches = list(root.glob(f"smali*/X/{class_name}.smali"))
    if len(matches) != 1:
        raise PatchMismatch(f"expected one {class_name} class, found {len(matches)}")
    return matches[0]


def only_method(source: str, signature: str) -> str:
    matches = [m.group() for m in METHOD_RE.finditer(source)
               if m.group().splitlines()[0].endswith(signature)]
    if len(matches) != 1:
        raise PatchMismatch(f"expected one method {signature}, found {len(matches)}")
    return matches[0]


ORGANIC_FACTORY = """.method private final gramForgeNotInterested(JJ)LX/05x0;
    .locals 8
    iget-object v0, p0, LX/09LB;->A03:LX/0Nwj;
    invoke-interface {v0}, LX/0Nwj;->CgY()LX/04Pd;
    move-result-object v1
    if-eqz v1, :none
    invoke-interface {v0}, LX/0Nwj;->Cga()LX/05C5;
    move-result-object v2
    if-eqz v2, :none
    new-instance v3, LX/09MD;
    invoke-direct {v3}, Ljava/lang/Object;-><init>()V
    iput-object v1, v3, LX/09MD;->A00:LX/04Pd;
    iput-object v2, v3, LX/09MD;->A01:LX/05C5;
    iget-object v4, p0, LX/09LB;->A02:LX/0Nzl;
    invoke-interface {v4}, LX/0Nnz;->CxV()LX/03RU;
    move-result-object v4
    iget-object v5, p0, LX/09LB;->A00:Lcom/instagram/common/session/UserSession;
    new-instance v0, LX/0SgP;
    move-object v1, v5
    move-object v2, v3
    move-object v3, v4
    move-wide v4, p1
    move-wide v6, p3
    invoke-direct/range {v0 .. v7}, LX/0SgP;-><init>(Lcom/instagram/common/session/UserSession;LX/09MD;LX/03RU;JJ)V
    iput-object p0, v0, LX/0SgP;->gramForgeOwner:LX/09LB;
    return-object v0
    :none
    const/4 v0, 0x0
    return-object v0
.end method"""

# This is the same action used by the *organic overflow menu* in Instagram
# 454: 0kpo(3) -> 04RT.A0F -> 04RW.AWI -> 04RW.A0b(NOT_INTERESTED).
# The native standalone UFI Not interested component has a different callback
# that opens an extra "why?" sheet, so we intentionally do not use it.
ORIGINAL_MORE_ACTION = """.method public final gramForgeSelectNotInterested(LX/09MD;)V
    .locals 5
    iget-object v0, p0, LX/09LB;->A02:LX/0Nzl;
    invoke-interface {v0}, LX/0Nnc;->DyW()LX/03QK;
    move-result-object v0
    iget-object v0, v0, LX/03QK;->A0U:Lkotlin/jvm/functions/Function3;
    instance-of v1, v0, LX/0D33;
    if-eqz v1, :done
    check-cast v0, LX/0D33;
    iget-object v0, v0, LX/00Y9;->receiver:Ljava/lang/Object;
    instance-of v1, v0, LX/04ST;
    if-eqz v1, :done
    check-cast v0, LX/04ST;
    iget-object v0, v0, LX/04ST;->A00:Lkotlin/jvm/functions/Function3;
    instance-of v1, v0, LX/0kpo;
    if-eqz v1, :done
    check-cast v0, LX/0kpo;
    iget-object v0, v0, LX/0kpo;->A00:Ljava/lang/Object;
    instance-of v1, v0, LX/04QS;
    if-eqz v1, :done
    check-cast v0, LX/04QS;
    iget-object v0, v0, LX/04QS;->A0Z:LX/0OVA;
    invoke-interface {v0}, LX/0OVA;->getValue()Ljava/lang/Object;
    move-result-object v0
    check-cast v0, LX/04RT;
    iget-object v0, v0, LX/04RT;->A0F:LX/04RW;
    iget-object v1, p1, LX/09MD;->A00:LX/04Pd;
    iget-object v2, p1, LX/09MD;->A01:LX/05C5;
    iget-object v3, v1, LX/04Pd;->A0g:Lcom/instagram/feed/media/Media;
    if-eqz v3, :done
    const-string v4, "simplified_overflow_menu"
    invoke-virtual/range {v0 .. v4}, LX/04RW;->AWI(LX/04Pd;LX/05C5;Lcom/instagram/feed/media/Media;Ljava/lang/String;)V
    sget-object v1, Lcom/instagram/feed/media/mediaoption/MediaOption$Option;->NOT_INTERESTED:Lcom/instagram/feed/media/mediaoption/MediaOption$Option;
    invoke-virtual {v0, v1}, LX/04RW;->A0b(Lcom/instagram/feed/media/mediaoption/MediaOption$Option;)V
    :done
    return-void
.end method"""

DIRECT_WRAPPER = """.method public static A04(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
    .locals 1
    invoke-static {p0, p1}, LX/0D9G;->gramForgePerformOverflowNotInterested(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
    move-result-object v0
    return-object v0
.end method"""

DISPATCH_MORE_ACTION = """.method public static gramForgePerformOverflowNotInterested(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
    .locals 3
    move-object v0, p0
    check-cast v0, LX/0D9G;
    iget-object v0, v0, LX/0D9G;->A01:Ljava/lang/Object;
    check-cast v0, LX/0SgP;
    iget-object v1, v0, LX/0SgP;->gramForgeOwner:LX/09LB;
    if-eqz v1, :original
    iget-object v2, v0, LX/0SgP;->A01:LX/09MD;
    invoke-virtual {v1, v2}, LX/09LB;->gramForgeSelectNotInterested(LX/09MD;)V
    goto :done
    :original
    invoke-static {p0, p1}, LX/0D9G;->gramForgePerformNotInterested(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
    :done
    sget-object v0, LX/00F8;->A00:LX/00F8;
    return-object v0
.end method"""

def patch(root: Path, *, check: bool = False) -> list[str]:
    reels_path = only_path(root, "09LB")
    action_path = only_path(root, "0D9G")
    reels = reels_path.read_text()
    action = action_path.read_text()

    old = only_method(reels, REELS_METHOD)
    if '"clips_ufi_more_button_component"' not in old or '->A0E(' not in old:
        raise PatchMismatch("Reels More factory no longer matches expected renderer")
    if reels.count(f"{REELS_OWNER}->{REELS_METHOD}") < 1:
        raise PatchMismatch("Reels More factory has no call sites")
    if "gramForgeNotInterested" in reels or "gramForgePerformNotInterested" in action:
        raise PatchMismatch("patch has already been applied")
    native = only_method(action, "A04(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;")
    if NATIVE_ACTION_MARKER not in native or "LX/03RU;->A00:LX/01wu;" not in native:
        raise PatchMismatch("native Not interested action has changed")
    native_button_path = only_path(root, "0SgP")
    native_button = native_button_path.read_text()
    if 'ClipsNotInterestedButtonComponent_render' not in native_button or 'gramForgeOwner' in native_button:
        raise PatchMismatch("native Not interested component is missing")
    original_more = only_path(root, "04RW").read_text()
    if not all(marker in original_more for marker in (
        "ClipsOrganicMoreOptionsHelper_handleSeeFewer",
        ".method public final AWI(LX/04Pd;LX/05C5;Lcom/instagram/feed/media/Media;Ljava/lang/String;)V",
        ".method public final A0b(Lcom/instagram/feed/media/mediaoption/MediaOption$Option;)V",
    )):
        raise PatchMismatch("organic More > Not interested action has changed")
    component = only_method(reels, "A0o(LX/00CS;)LX/05x0;")
    duplicate = re.compile(r"(:goto_f\s+)invoke-virtual \{v5, v0\}, LX/00B5;->A00\(LX/05x0;\)V")
    if len(duplicate.findall(component)) != 1:
        raise PatchMismatch("cannot suppress the native duplicate Not interested row")

    # Keep the original More renderer for ads, replacing only its organic path.
    idx = old.find("    iget-boolean v0, p0, LX/09LB;->A08:Z")
    if idx < 0:
        raise PatchMismatch("More factory eligibility branch changed")
    entry = old[:idx]
    if "    :cond_1\n" not in entry:
        raise PatchMismatch("More factory entry label changed")
    hook = ("    iget-object v0, p0, LX/09LB;->A03:LX/0Nwj;\n"
            "    invoke-interface {v0}, LX/0Nwj;->CgY()LX/04Pd;\n"
            "    move-result-object v0\n"
            "    iget-boolean v0, v0, LX/04Pd;->A19:Z\n"
            "    if-nez v0, :gramforge_original_more\n"
            "    move-object/from16 v0, p0\n"
            "    move-wide/from16 v1, p3\n"
            "    move-wide/from16 v3, p5\n"
            "    invoke-direct/range {v0 .. v4}, LX/09LB;->gramForgeNotInterested(JJ)LX/05x0;\n"
            "    move-result-object v1\n"
            "    return-object v1\n"
            "    :gramforge_original_more\n\n")
    updated_factory = old[:idx] + hook + old[idx:]
    updated_factory = updated_factory.replace(REELS_METHOD, REELS_NEW_METHOD, 1)
    updated_component = duplicate.sub(r"\1const/4 v0, 0x0\n    invoke-virtual {v5, v0}, LX/00B5;->A00(LX/05x0;)V", component, count=1)
    updated_reels = reels.replace(old, updated_factory, 1).replace(component, updated_component, 1)
    updated_reels = updated_reels.replace(f"{REELS_OWNER}->{REELS_METHOD}", f"{REELS_OWNER}->{REELS_NEW_METHOD}")
    updated_reels += "\n" + ORGANIC_FACTORY + "\n" + ORIGINAL_MORE_ACTION + "\n"
    original_perform = native.replace(" A04(", " gramForgePerformNotInterested(", 1)
    updated_action = action.replace(native, DIRECT_WRAPPER + "\n\n" + original_perform + "\n\n" + DISPATCH_MORE_ACTION, 1)
    updated_native_button = native_button.replace(
        ".super LX/009q;", ".super LX/009q;\n\n.field public gramForgeOwner:LX/09LB;", 1
    )
    if updated_native_button == native_button:
        raise PatchMismatch("native Not interested component superclass changed")
    if not check:
        reels_path.write_text(updated_reels)
        action_path.write_text(updated_action)
        native_button_path.write_text(updated_native_button)
    return ["organic Reels action", "immediate More-menu Not interested callback"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded_apk", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        labels = patch(args.decoded_apk, check=args.check)
    except PatchMismatch as exc:
        parser.exit(1, f"ERROR: Reels Not interested patch incompatible: {exc}\n")
    print("GramForge Reels Not interested " + ("verified" if args.check else "patched") + ": " + ", ".join(labels))
