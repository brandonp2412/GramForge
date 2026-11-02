#!/usr/bin/env python3
"""Suppress Instagram's notification-permission upsell surfaces.

Targets only UI solicitation: the feed/Direct permission upsell, the activity
feed's Compose upsell row, dynamic onboarding push opt-in, and the specifically
named notification-permission Quick Promotion. The OS permission API, actual
push delivery, per-account notification controls, and manual settings remain.
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


def patch(root: Path, *, check: bool = False) -> list[str]:
    if not root.is_dir():
        raise PatchMismatch(f"decoded APK missing: {root}")
    feed_path = only_path(root, "05QL.smali")
    onboarding_path = only_path(root, "0gKg.smali")
    row_path = only_path(root, "0C4e.smali")
    qp_path = only_path(root, "02jE.smali")

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

    if not check:
        feed_path.write_text(feed)
        onboarding_path.write_text(onboarding)
        row_path.write_text(row)
        qp_path.write_text(updated_qp)
    return ["feed/Direct upsells", "activity-feed row", "onboarding push opt-in", "notification Quick Promotion"]


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
