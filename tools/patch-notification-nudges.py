#!/usr/bin/env python3
"""Suppress Instagram's notification-permission upsell surfaces.

Targets only UI solicitation: the feed/Direct permission upsell, the activity
feed's Compose upsell row, dynamic onboarding push opt-in, the specifically
named notification-permission Quick Promotion, and the inline Direct-thread
reachability banner. The OS permission API, actual push delivery, per-account
notification controls, and manual settings remain.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


class PatchMismatch(Exception):
    pass


METHOD_RE = re.compile(r"(?ms)^\.method [^\n]+\n.*?^\.end method")


def only_path(root: Path, filename: str) -> Path:
    matches = list(root.rglob(filename))
    if len(matches) != 1:
        raise PatchMismatch(f"expected one {filename}, found {len(matches)}")
    return matches[0]


def replace_method(
    source: str, signature: str, markers: tuple[str, ...], replacement: str
) -> str:
    matches = [m.group() for m in METHOD_RE.finditer(source)
               if m.group().splitlines()[0].endswith(signature)]
    if len(matches) != 1:
        raise PatchMismatch(f"expected one {signature}, found {len(matches)}")
    old = matches[0]
    if any(marker not in old for marker in markers):
        raise PatchMismatch(f"{signature}: expected notification-specific marker absent")
    return source.replace(old, replacement, 1)


FEED_UPSELL_DISABLED = """.method public static final A00(Landroid/content/Context;Lcom/instagram/common/session/UserSession;Ljava/lang/String;)Z
    .locals 1
    const/4 v0, 0x0
    return v0
.end method"""

ONBOARDING_OPT_IN_DISABLED = """.method public final A00()Z
    .locals 1
    const/4 v0, 0x0
    return v0
.end method"""

ACTIVITY_UPSELL_ROW_DISABLED = """.method public static final A0H(LX/1BaO;Ljava/lang/String;Lkotlin/jvm/functions/Function1;I)V
    .locals 0
    return-void
.end method"""

# The Direct conversation's inline notification IgdsBanner is inflated by
# LX/02Ru.A00, independently of the feed/Direct permission check. Only skip
# its first branch; :cond_3 continues unrelated conversation banner logic.
DIRECT_THREAD_BANNER_METHOD = (
    "A00(Lcom/instagram/common/session/UserSession;LX/02Nt;LX/0QaX;LX/02Ru;)V"
)
DIRECT_THREAD_BANNER_ANCHOR = (
    "    iget-object v0, v6, LX/02Ru;->A00:Ljava/lang/Integer;\n\n"
    "    move-object/from16 v20, p0\n\n"
    "    move-object/from16 v22, p2\n\n"
    "    if-nez v0, :cond_3"
)


def suppress_direct_thread_banner(source: str) -> str:
    matches = [m.group() for m in METHOD_RE.finditer(source)
               if m.group().splitlines()[0].endswith(DIRECT_THREAD_BANNER_METHOD)]
    if len(matches) != 1:
        raise PatchMismatch("expected one Direct-thread banner renderer")
    old = matches[0]
    markers = (
        '"NF_REACHABILITY_UPSELL_LAST_FIBONACCI_COOL_DOWN_UNTIL"',
        '"nf_reachability_upsell_limits_direct_thread"',
        "const v0, 0x7f0b31dd",  # push_upsell_viewstub
        "const v0, 0x7f0b31dc",  # push_upsell_composer_banner
        "new-instance v1, LX/0Ra9;",  # notification button callback
        "    :cond_3\n",
    )
    if any(marker not in old for marker in markers) or old.count(DIRECT_THREAD_BANNER_ANCHOR) != 1:
        raise PatchMismatch("Direct-thread notification banner structure changed")
    revised = old.replace(
        DIRECT_THREAD_BANNER_ANCHOR,
        DIRECT_THREAD_BANNER_ANCHOR.replace("if-nez v0, :cond_3", "goto/16 :cond_3"),
        1,
    )
    return source.replace(old, revised, 1)



# The shared reachability factory supplies eligibility for Direct-inbox,
# Direct-thread, and activity-feed/post-follow notification reminders. These
# are the four concrete LX/0Uid implementations created exclusively there.
# Returning false from B28() leaves their lifecycle and other app features
# untouched while preventing presentation in every caller.
REACHABILITY_ELIGIBILITY_MARKERS = {
    "0S6U": ("LX/0S6U;->A03:LX/06KJ;", "LX/06KJ;->A01("),
    "0RJO": ("LX/0RJO;->A02:Lcom/instagram/common/session/UserSession;",
              "V2_REACHABILITY_UPSELL_GLOBAL_SHARED_DISMISS_COOLDOWN"),
    "0S47": ("LX/0S47;->A0B:LX/06KJ;", "LX/06KJ;->A01("),
    "0hf6": ("LX/0hf6;->A09:LX/0Jnv;", "LX/06KJ;->A01("),
}
REACHABILITY_ELIGIBILITY_DISABLED = """.method public final B28()Z
    .locals 1
    const/4 v0, 0x0
    return v0
.end method"""
AUTO_PROMPT_DISABLED = """.method public static final A00(Landroid/app/Activity;Landroid/view/View;Lcom/instagram/common/session/UserSession;Ljava/lang/Integer;)V
    .locals 0
    return-void
.end method"""
REFOREGROUND_TOAST_DISABLED = """.method public static final A01(LX/0QBE;LX/0XFB;Ljava/lang/Integer;Ljava/lang/Integer;LX/1Btm;I)V
    .locals 0
    return-void
.end method"""


def suppress_profile_notification_stub(source: str) -> str:
    matches = [m.group() for m in METHOD_RE.finditer(source)
               if m.group().splitlines()[0].startswith(".method public static final A01(")]
    if len(matches) != 1:
        raise PatchMismatch("profile notification upsell renderer missing")
    old = matches[0]
    anchor = "    :cond_3b\n    const v8, 0x20042"
    markers = ("LX/0Oo4;->A0H:LX/0Jnk;", "LX/03ii;->A01(Landroid/content/Context;)Z",
               "    :cond_3c\n", "LX/0Jnk;->setVisibility(I)V")
    if any(marker not in old for marker in markers) or old.count(anchor) != 1:
        raise PatchMismatch("profile notification upsell structure changed")
    revised = old.replace(anchor, anchor.replace(
        "    const v8, 0x20042", "    goto/16 :cond_3c\n    const v8, 0x20042"), 1)
    return source.replace(old, revised, 1)


def additional_notification_updates(root: Path) -> dict[Path, str]:
    factory = only_path(root, "0STR.smali").read_text()
    if any(factory.count(f"new-instance v4, LX/{name};") != 1
           for name in REACHABILITY_ELIGIBILITY_MARKERS):
        raise PatchMismatch("reachability eligibility factory changed")
    updates = {}
    for name, markers in REACHABILITY_ELIGIBILITY_MARKERS.items():
        path = only_path(root, f"{name}.smali")
        updates[path] = replace_method(
            path.read_text(), "B28()Z", markers, REACHABILITY_ELIGIBILITY_DISABLED
        )

    delayed = only_path(root, "05QN.smali")
    updates[delayed] = replace_method(
        delayed.read_text(),
        "A00(Landroid/app/Activity;Landroid/view/View;Lcom/instagram/common/session/UserSession;Ljava/lang/Integer;)V",
        ("preference_has_asked_push_permission_in_nux", '"direct_inbox"',
         '"notification_feed"', "Landroid/view/View;->postDelayed("),
        AUTO_PROMPT_DISABLED,
    )

    toast = only_path(root, "0QBE.smali")
    updates[toast] = replace_method(
        toast.read_text(),
        "A01(LX/0QBE;LX/0XFB;Ljava/lang/Integer;Ljava/lang/Integer;LX/1Btm;I)V",
        ("V2_REACHABILITY_UPSELL_REFOREGROUND_TOAST_LAST_SHOWN_TIMESTAMP",
         "LX/0BfK;->A03()V", "LX/09qf;->A01"),
        REFOREGROUND_TOAST_DISABLED,
    )

    profile = only_path(root, "0QCd.smali")
    updates[profile] = suppress_profile_notification_stub(profile.read_text())
    return updates


def suppress_current_compose_empty_inbox_notification(source: str) -> str:
    """Remove the exact push CTA copy/action from the Compose empty inbox row."""
    signature = "A04(LX/14xx;LX/01KJ;LX/02Lu;LX/01Km;IIZ)V"
    matches = [m.group() for m in METHOD_RE.finditer(source)
               if m.group().splitlines()[0] == ".method public static final " + signature]
    if len(matches) != 1:
        raise PatchMismatch("current Compose inbox empty state renderer changed")
    old = matches[0]
    markers = (
        "InboxEmptyStateRow (InboxEmptyStateRow.kt:69)",
        "iget-object v4, v1, LX/01KJ;->A08:Ljava/lang/CharSequence;",
        "move-object/from16 v18, v4",
        "LX/0WVT;->A01(LX/0nuF;LX/14xx;LX/03Um;",
        "LX/0T86;->A0I(LX/14xx;LX/14az;Ljava/lang/Integer;Ljava/lang/String;Lkotlin/jvm/functions/Function0;)V",
    )
    anchor = "    :goto_8\n    iget-object v9, v1, LX/01KJ;->A0I:Ljava/lang/String;\n"
    if any(marker not in old for marker in markers) or old.count(anchor) != 1:
        raise PatchMismatch("current Compose inbox empty state notification CTA changed")
    guard = """    :goto_8
    iget-object v9, v1, LX/01KJ;->A0I:Ljava/lang/String;
    const-string v4, "Turn on notifications"
    invoke-static {v9, v4}, Landroid/text/TextUtils;->equals(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Z
    move-result v4
    if-eqz v4, :gramforge_keep_empty_cta
    const-string v19, "Turn on notifications so you don't miss new messages."
    invoke-static/range {v18 .. v19}, Landroid/text/TextUtils;->equals(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Z
    move-result v4
    const/16 v19, 0x0
    if-eqz v4, :gramforge_keep_empty_cta
    const/4 v9, 0x0
    move-object/from16 v18, v19
    :gramforge_keep_empty_cta
"""
    return source.replace(old, old.replace(anchor, guard, 1), 1)


def patch_current(root: Path, *, check: bool = False) -> list[str]:
    """Rebase suppression at the 454.0.0.54.77 UI eligibility gates."""
    feed_path = only_path(root, "02EI.smali")
    onboarding_path = only_path(root, "0M8e.smali")
    row_path = only_path(root, "0DTC.smali")
    qp_path = only_path(root, "02oJ.smali")
    reach_factory_path = only_path(root, "0SE9.smali")
    factory = reach_factory_path.read_text()
    implementations = ("0RG1", "01I3", "0R9T", "0kxq")
    if (any(factory.count(f"new-instance v4, LX/{name};") != 1 for name in implementations)
            or factory.count("LX/0Uzz;") < 2):
        raise PatchMismatch("new reachability factory changed")
    feed = replace_method(
        feed_path.read_text(),
        "A00(Landroid/content/Context;Lcom/instagram/common/session/UserSession;Ljava/lang/String;)Z",
        ("notification_feed", "direct_inbox", "preference_has_allowed_push_system_dialog"),
        FEED_UPSELL_DISABLED,
    )
    onboarding = replace_method(
        onboarding_path.read_text(), "A00()Z",
        ("skip_push_opt_in_already_asked", "skip_push_opt_in_has_permission_already"),
        ONBOARDING_OPT_IN_DISABLED,
    )
    row = replace_method(
        row_path.read_text(),
        "A0H(LX/14xx;Ljava/lang/String;Lkotlin/jvm/functions/Function1;I)V",
        ("PushNotificationUpsellRow", "0x7f138dc6"),
        ACTIVITY_UPSELL_ROW_DISABLED.replace("LX/1BaO;", "LX/14xx;"),
    )
    qp = qp_path.read_text()
    qp_method = [m.group() for m in METHOD_RE.finditer(qp)
                 if m.group().splitlines()[0].startswith(".method public final GzO(")]
    if len(qp_method) != 1 or '"notification_permission_prompt"' not in qp_method[0]:
        raise PatchMismatch("new notification Quick Promotion resolver changed")
    anchor = """    :cond_24
    const/4 v12, 0x1

    invoke-static {v5, v2, v1, v12}, LX/0EBO;->A00(LX/0DEM;LX/0EBO;Ljava/util/Set;Z)V"""
    if qp_method[0].count(anchor) != 1 or "    :cond_23\n    :goto_13" not in qp_method[0]:
        raise PatchMismatch("new Quick Promotion eligibility branch changed")
    guarded = """    :cond_24
    iget-object v0, v5, LX/0DEM;->A0A:LX/0EGo;
    iget-object v0, v0, LX/0EGo;->A00:Ljava/lang/String;
    const-string v3, "notification_permission_prompt"
    invoke-virtual {v3, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    if-nez v0, :cond_23
    const/4 v12, 0x1

    invoke-static {v5, v2, v1, v12}, LX/0EBO;->A00(LX/0DEM;LX/0EBO;Ljava/util/Set;Z)V"""
    qp = qp.replace(qp_method[0], qp_method[0].replace(anchor, guarded, 1), 1)
    updates = {feed_path: feed, onboarding_path: onboarding, row_path: row,
               qp_path: qp}
    disabled = """.method public final B2L()Z
    .locals 1
    const/4 v0, 0x0
    return v0
.end method"""
    disabled_secondary = disabled.replace("B2L()", "B2M()")
    for name in implementations:
        path = only_path(root, f"{name}.smali")
        source = path.read_text()
        if ".implements LX/0Uzz;" not in source:
            raise PatchMismatch(f"{name} is no longer a reachability implementation")
        source = replace_method(
            source, "B2L()Z",
            (f"LX/{name};", "LX/02Dv;"), disabled,
        )
        if name != "0kxq":
            source = replace_method(
                source, "B2M()Z",
                (f"LX/{name};", "LX/02Dv;"), disabled_secondary,
            )
        updates[path] = source
    empty_path = only_path(root, "0YVX.smali")
    updates[empty_path] = suppress_current_compose_empty_inbox_notification(empty_path.read_text())
    if not check:
        for path, source in updates.items():
            path.write_text(source)
    return [
        "feed/Direct permission nudges", "activity row", "onboarding opt-in",
        "notification Quick Promotion", "four reachability implementations (Direct, activity, profile)",
        "Compose empty inbox push CTA",
    ]


def patch(root: Path, *, check: bool = False) -> list[str]:
    if list(root.glob("smali*/X/02EI.smali")):
        return patch_current(root, check=check)
    if not root.is_dir():
        raise PatchMismatch(f"decoded APK missing: {root}")
    feed_path = only_path(root, "05QL.smali")
    onboarding_path = only_path(root, "0gKg.smali")
    row_path = only_path(root, "0C4e.smali")
    qp_path = only_path(root, "02jE.smali")
    thread_path = only_path(root, "02Ru.smali")

    feed = replace_method(
        feed_path.read_text(),
        "A00(Landroid/content/Context;Lcom/instagram/common/session/UserSession;Ljava/lang/String;)Z",
        ("notification_feed", "direct_inbox", "preference_has_allowed_push_system_dialog"),
        FEED_UPSELL_DISABLED,
    )
    onboarding = replace_method(
        onboarding_path.read_text(), "A00()Z",
        ("skip_push_opt_in_already_asked", "skip_push_opt_in_has_permission_already"),
        ONBOARDING_OPT_IN_DISABLED,
    )
    row = replace_method(
        row_path.read_text(),
        "A0H(LX/1BaO;Ljava/lang/String;Lkotlin/jvm/functions/Function1;I)V",
        ("PushNotificationUpsellRow", "0x7f138dc8"),
        ACTIVITY_UPSELL_ROW_DISABLED,
    )

    # Filter only the named notification-permission promotion at the point
    # where Quick Promotions are iterated, before it can reach presentation.
    qp = qp_path.read_text()
    found = [m.group() for m in METHOD_RE.finditer(qp)
             if m.group().splitlines()[0].startswith(".method public final Gz9(")]
    if len(found) != 1:
        raise PatchMismatch("Quick Promotion resolver missing")
    old = found[0]
    if '"notification_permission_prompt"' not in old:
        raise PatchMismatch("notification Quick Promotion type no longer identifiable")
    anchor = ("    move-object v5, v6\n\n"
              "    check-cast v5, LX/044I;\n\n"
              "    iget-object v1, v5, LX/044I;->A07:")
    if old.count(anchor) != 1 or ":goto_0" not in old:
        raise PatchMismatch("Quick Promotion loop structure changed")
    guarded = ("    move-object v5, v6\n\n"
               "    check-cast v5, LX/044I;\n\n"
               "    iget-object v0, v5, LX/044I;->A0A:LX/09ZY;\n"
               "    iget-object v0, v0, LX/09ZY;->A00:Ljava/lang/String;\n"
               "    const-string v1, \"notification_permission_prompt\"\n"
               "    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z\n"
               "    move-result v0\n"
               "    if-nez v0, :goto_0\n\n"
               "    iget-object v1, v5, LX/044I;->A07:")
    updated_qp = qp.replace(old, old.replace(anchor, guarded, 1), 1)
    updated_thread = suppress_direct_thread_banner(thread_path.read_text())
    updates = {
        feed_path: feed,
        onboarding_path: onboarding,
        row_path: row,
        qp_path: updated_qp,
        thread_path: updated_thread,
    }
    updates.update(additional_notification_updates(root))

    if not check:
        for path, source in updates.items():
            path.write_text(source)
    return [
        "feed/Direct upsells", "activity-feed row", "onboarding push opt-in",
        "notification Quick Promotion", "Direct-thread inline banner",
        "shared reachability banners", "delayed Direct/feed permission prompts",
        "ref foreground notification toast", "profile notification upsell",
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded_apk", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        labels = patch(args.decoded_apk, check=args.check)
    except PatchMismatch as exc:
        parser.exit(1, f"ERROR: notification nudge patch incompatible: {exc}\n")
    print("GramForge notification nudges " + ("verified" if args.check else "patched") + ": " + ", ".join(labels))
