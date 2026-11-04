#!/usr/bin/env python3
"""Hide Requests navigation and the separate Direct inbox header (454).

Drops the inbox_requests menu item and hides only the visible Requests header
beside Messages in the Direct inbox. The underlying folder and data remain.
Fail closed when Instagram's Smali structure changes.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


class PatchMismatch(Exception):
    pass


METHOD_RE = re.compile(r"(?ms)^\.method public final A06\(\)V\n.*?^\.end method$")
REQUEST_TITLE = "    const v7, 0x7f133e2b"
REQUEST_MODE = "    sget-object v14, LX/01tK;->A00:LX/01tK;"
REQUEST_CONSTRUCTOR = (
    "    invoke-direct/range {v12 .. v22}, LX/0X7V;-><init>"
    "(LX/0RDO;LX/06Zx;Ljava/lang/Integer;Ljava/lang/Integer;"
    "Ljava/lang/Integer;Ljava/lang/Integer;Ljava/util/Set;ZZZ)V"
)
REQUEST_ADD = (
    "    invoke-virtual {v0, v12}, "
    "Ljava/util/AbstractCollection;->add(Ljava/lang/Object;)Z\n"
)
LIST_COMMIT = "    new-instance v5, LX/05Ku;"
PRIMARY_CLASS = ".class public final LX/0RDL;"
PRIMARY_METHOD_RE = re.compile(
    r"(?ms)^\.method public final A01\(Lcom/instagram/common/session/UserSession;"
    r"LX/06Zx;LX/0Jnp;IZZZ\)LX/05Ku;\n.*?^\.end method$"
)
PRIMARY_REQUEST_MODE = "    sget-object v6, LX/01tK;->A00:LX/01tK;"
PRIMARY_CONSTRUCTOR = (
    "    invoke-direct/range {v21 .. v31}, LX/0X7V;-><init>"
    "(LX/0RDO;LX/06Zx;Ljava/lang/Integer;Ljava/lang/Integer;"
    "Ljava/lang/Integer;Ljava/lang/Integer;Ljava/util/Set;ZZZ)V"
)
PRIMARY_ADD = (
    "    invoke-virtual {v7, v1}, "
    "Ljava/util/AbstractCollection;->add(Ljava/lang/Object;)Z"
)
PRIMARY_SKIP = """    iget-object v2, v4, Landroid/util/Pair;->second:Ljava/lang/Object;

    sget-object v3, LX/01tK;->A00:LX/01tK;

    invoke-static {v2, v3}, LX/00d6;->areEqual(Ljava/lang/Object;Ljava/lang/Object;)Z

    move-result v2

    if-nez v2, :goto_4

"""

# The Requests text beside Messages is a separate header in the Direct inbox
# RecyclerView, not a folder navigation entry. DirectInboxController owns this
# view. Watch only that RecyclerView's layouts, retaining the underlying inbox.
CONTROLLER_CLASS = ".class public final LX/04TH;"
CONTROLLER_METHOD_RE = re.compile(
    r"(?ms)^\.method public final A0I\(Landroid/view/View;\)V\n.*?^\.end method$"
)
CONTROLLER_RETURN = "    :cond_2a\n    return-void\n"
CONTROLLER_HOOK = (
    "    :cond_2a\n"
    "    invoke-static {v8}, Lcom/gramforge/DirectRequestsHeaderFilter;"
    "->install(Landroid/view/View;)V\n\n"
    "    return-void\n"
)
DIRECT_HEADER_FILTER_SMALI = """.class public final Lcom/gramforge/DirectRequestsHeaderFilter;
.super Ljava/lang/Object;
.implements Landroid/view/ViewTreeObserver$OnGlobalLayoutListener;

.field private final inbox:Landroid/view/View;

.method private constructor <init>(Landroid/view/View;)V
    .locals 0

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    iput-object p1, p0, Lcom/gramforge/DirectRequestsHeaderFilter;->inbox:Landroid/view/View;

    return-void
.end method

.method public static install(Landroid/view/View;)V
    .locals 3

    const v0, 0x7f0b2067

    invoke-virtual {p0, v0}, Landroid/view/View;->findViewById(I)Landroid/view/View;

    move-result-object v0

    if-eqz v0, :done

    new-instance v1, Lcom/gramforge/DirectRequestsHeaderFilter;

    invoke-direct {v1, v0}, Lcom/gramforge/DirectRequestsHeaderFilter;-><init>(Landroid/view/View;)V

    invoke-virtual {v0}, Landroid/view/View;->getViewTreeObserver()Landroid/view/ViewTreeObserver;

    move-result-object v2

    invoke-virtual {v2, v1}, Landroid/view/ViewTreeObserver;->addOnGlobalLayoutListener(Landroid/view/ViewTreeObserver$OnGlobalLayoutListener;)V

    invoke-static {v0}, Lcom/gramforge/DirectRequestsHeaderFilter;->hide(Landroid/view/View;)V

    :done
    return-void
.end method

.method public onGlobalLayout()V
    .locals 1

    iget-object v0, p0, Lcom/gramforge/DirectRequestsHeaderFilter;->inbox:Landroid/view/View;

    invoke-static {v0}, Lcom/gramforge/DirectRequestsHeaderFilter;->hide(Landroid/view/View;)V

    return-void
.end method

.method public static hide(Landroid/view/View;)V
    .locals 4

    if-eqz p0, :done

    instance-of v0, p0, Landroid/widget/TextView;

    if-eqz v0, :container

    move-object v0, p0

    check-cast v0, Landroid/widget/TextView;

    invoke-virtual {v0}, Landroid/widget/TextView;->getText()Ljava/lang/CharSequence;

    move-result-object v1

    const-string v2, "Requests"

    invoke-static {v1, v2}, Landroid/text/TextUtils;->equals(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Z

    move-result v1

    if-eqz v1, :done

    const/16 v1, 0x8

    invoke-virtual {p0, v1}, Landroid/view/View;->setVisibility(I)V

    return-void

    :container
    instance-of v0, p0, Landroid/view/ViewGroup;

    if-eqz v0, :done

    move-object v0, p0

    check-cast v0, Landroid/view/ViewGroup;

    invoke-virtual {v0}, Landroid/view/ViewGroup;->getChildCount()I

    move-result v1

    const/4 v2, 0x0

    :loop
    if-ge v2, v1, :done

    invoke-virtual {v0, v2}, Landroid/view/ViewGroup;->getChildAt(I)Landroid/view/View;

    move-result-object v3

    invoke-static {v3}, Lcom/gramforge/DirectRequestsHeaderFilter;->hide(Landroid/view/View;)V

    add-int/lit8 v2, v2, 0x1

    goto :loop

    :done
    return-void
.end method
"""


def transform(source: str) -> str:
    if ".class public final LX/05PM;" not in source:
        raise PatchMismatch("Direct inbox navigation class changed")
    matches = list(METHOD_RE.finditer(source))
    if len(matches) != 1:
        raise PatchMismatch(f"expected one inbox navigation builder, found {len(matches)}")
    method = matches[0].group()
    for marker in (REQUEST_TITLE, REQUEST_MODE, REQUEST_CONSTRUCTOR, LIST_COMMIT):
        if method.count(marker) != 1:
            raise PatchMismatch(f"Requests navigation fingerprint missing/duplicated: {marker}")
    title = method.index(REQUEST_TITLE)
    mode = method.index(REQUEST_MODE)
    constructor = method.index(REQUEST_CONSTRUCTOR)
    list_commit = method.index(LIST_COMMIT)
    additions = [m.start() for m in re.finditer(re.escape(REQUEST_ADD), method)]
    if len(additions) != 1 or not (title < mode < constructor < additions[0] < list_commit):
        raise PatchMismatch("Requests navigation insertion changed")
    updated = method.replace(REQUEST_ADD, "", 1)
    return source[:matches[0].start()] + updated + source[matches[0].end():]


def transform_primary(source: str) -> str:
    """Omit Requests from the live folder list built by A07 -> 0RDL.A01."""
    if PRIMARY_CLASS not in source:
        raise PatchMismatch("primary Direct inbox navigation class changed")
    matches = list(PRIMARY_METHOD_RE.finditer(source))
    if len(matches) != 1:
        raise PatchMismatch(f"expected one primary inbox builder, found {len(matches)}")
    method = matches[0].group()
    for marker in (PRIMARY_REQUEST_MODE, PRIMARY_CONSTRUCTOR, PRIMARY_ADD):
        if method.count(marker) != 1:
            raise PatchMismatch(f"primary Requests fingerprint missing/duplicated: {marker}")
    mode = method.index(PRIMARY_REQUEST_MODE)
    constructor = method.index(PRIMARY_CONSTRUCTOR)
    addition = method.index(PRIMARY_ADD)
    if not (mode < constructor < addition < method.index("    goto/16 :goto_4", addition)):
        raise PatchMismatch("primary Requests navigation insertion changed")
    updated = method.replace(PRIMARY_ADD, PRIMARY_SKIP + PRIMARY_ADD, 1)
    return source[:matches[0].start()] + updated + source[matches[0].end():]


def transform_controller(source: str) -> str:
    if CONTROLLER_CLASS not in source:
        raise PatchMismatch("DirectInboxController class changed")
    matches = list(CONTROLLER_METHOD_RE.finditer(source))
    if len(matches) != 1:
        raise PatchMismatch(f"expected one Direct inbox view setup, found {len(matches)}")
    method = matches[0].group()
    for marker in ("DirectInboxController.onCreateView", "    .locals 42", "0x7f0b2067"):
        if marker not in method:
            raise PatchMismatch(f"Direct inbox view fingerprint changed: {marker}")
    if method.count(CONTROLLER_RETURN) != 1:
        raise PatchMismatch("Direct inbox view return changed")
    updated = method.replace(CONTROLLER_RETURN, CONTROLLER_HOOK, 1)
    return source[:matches[0].start()] + updated + source[matches[0].end():]


def patch(root: Path, *, check: bool = False) -> Path:
    if not root.is_dir():
        raise PatchMismatch(f"decoded APK missing: {root}")
    legacy_paths = list(root.rglob("05PM.smali"))
    primary_paths = list(root.rglob("0RDL.smali"))
    controller_paths = list(root.rglob("04TH.smali"))
    if len(legacy_paths) != 1 or len(primary_paths) != 1 or len(controller_paths) != 1:
        raise PatchMismatch(
            "expected one of each Direct inbox navigation/view builder; "
            f"found {len(legacy_paths)} legacy, {len(primary_paths)} primary, "
            f"and {len(controller_paths)} view controllers"
        )
    # Validate all paths before writing any of them, so an upstream mismatch
    # cannot leave the decoded APK half-patched.
    legacy_path, primary_path, controller_path = legacy_paths[0], primary_paths[0], controller_paths[0]
    helper_path = controller_path.parent.parent / "com/gramforge/DirectRequestsHeaderFilter.smali"
    if helper_path.exists():
        raise PatchMismatch(f"Direct inbox header helper already present: {helper_path}")
    legacy_updated = transform(legacy_path.read_text())
    primary_updated = transform_primary(primary_path.read_text())
    controller_updated = transform_controller(controller_path.read_text())
    if not check:
        legacy_path.write_text(legacy_updated)
        primary_path.write_text(primary_updated)
        controller_path.write_text(controller_updated)
        helper_path.parent.mkdir(parents=True, exist_ok=True)
        helper_path.write_text(DIRECT_HEADER_FILTER_SMALI)
    return controller_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded_apk", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        patch(args.decoded_apk, check=args.check)
    except PatchMismatch as exc:
        parser.exit(1, f"ERROR: Message Requests link patch incompatible: {exc}\n")
    print("GramForge Message Requests link " + ("verified" if args.check else "hidden"))
