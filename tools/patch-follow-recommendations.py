#!/usr/bin/env python3
"""Suppress follow recommendations without disabling organic media or sharing."""
import argparse
import re
from pathlib import Path


class PatchMismatch(Exception):
    pass


def one(text, pattern, replacement):
    out, count = re.subn(pattern, replacement, text, flags=re.M)
    if count != 1:
        raise PatchMismatch(f"expected one anchor, found {count}: {pattern}")
    return out


def find(root, suffix):
    files = list(root.glob("smali*/" + suffix))
    if len(files) != 1:
        raise PatchMismatch(f"expected one {suffix}, found {len(files)}")
    return files[0]


def config(text):
    return one(text, r"^\.method public static isSuggestedBlocked\(\)Z\n(?:(?!^\.end method)[\s\S])*?^\.end method",
               ".method public static isSuggestedBlocked()Z\n    .locals 1\n    const/4 v0, 0x1\n    return v0\n.end method")


def block(text):
    # Keep account-discovery endpoints only; do not break recipient selection,
    # favorites, story sharing, surveys, channels or ordinary Reels.
    for marker in ('"/discover/chaining/"', '"/discover/ayml/"',
                   '"suggested_users"', '"suggested_top_accounts"',
                   '->isSuggestedBlocked()Z'):
        if marker not in text:
            raise PatchMismatch(f"Feur recommendation hook changed: {marker}")
    expected = {
        0: "/discover/ayml/", 1: "/discover/sectioned_ayml/",
        2: "/discover/chaining/", 3: "/discover/recommended_accounts_for_category/",
        4: "/discover/suggested_businesses/", 5: "/discover/recs_from_friends_suggestions/",
        6: "/discover/recs_from_friends_user_info/", 7: "/discover/fetch_suggestion_details/",
        8: "/discover/account_discovery/", 9: "/discover/reshare_suggestions/",
        10: "/fbsearch/accounts_recs/", 11: "/friendships/feed_favorites_suggestions/",
        12: "/friendships/share_to_friends_story_suggested_users/",
        13: "/direct_v2/search_friending_suggestions/",
        14: "/business/discovery/suggest_business/",
    }
    prefix, separator, _ = text.partition("->SUGGESTED:[Ljava/lang/String;")
    if not separator or any(f'const-string v{reg}, "{value}"' not in prefix for reg, value in expected.items()):
        raise PatchMismatch("Feur account discovery register mapping changed")
    if 'const-string v5, "suggested_users"' not in text or 'const-string v6, "suggested_top_accounts"' not in text:
        raise PatchMismatch("Feur feed account unit register mapping changed")
    text = one(text, r"filled-new-array/range \{v0 \.\. v14\}, \[Ljava/lang/String;(?=\s+move-result-object v0\s+sput-object v0, Lcom/feurstagram/extension/Block;->SUGGESTED:)",
               "filled-new-array/range {v0 .. v8}, [Ljava/lang/String;")
    return one(text, r"filled-new-array/range \{v1 \.\. v7\}, \[Ljava/lang/String;(?=\s+move-result-object v0\s+sput-object v0, Lcom/feurstagram/extension/Block;->SUGGESTED_FEED_UNITS:)",
               "filled-new-array {v5, v6}, [Ljava/lang/String;")


def follow_requests(text):
    return one(text, r'(const-string (v\d+), "exclude_suggested_users"\s+)move/from16 (v\d+), p2(?=\s+invoke-static \{v\d+, \2, \3\}, LX/[^;]+;->[^\(]+\(LX/[^;]+;Ljava/lang/String;Z\)V)',
               r'\1const/4 \3, 0x1')


def carousel(text):
    # This is the dedicated similar-accounts carousel, not the Follow button.
    if '0x7f0b3c6b' not in text or '->A09:Lcom/instagram/ui/widget/nestablescrollingview/NestableHorizontalRecyclerPager;' not in text or '"see_all_in_header"' not in text:
        raise PatchMismatch("similar-accounts carousel fingerprint changed")
    match = re.search(r"(?ms)^\.method public static final A01\([^\n]*LX/0O5i;[^\n]*\)V\n    \.locals 15\n.*?^\.end method", text)
    if not match or match.group().count("    return-void") != 1 or "move-object/from16 v3, p9" not in match.group():
        raise PatchMismatch("similar-accounts carousel binder changed")
    body = match.group().replace("    return-void", """    move-object/from16 v0, p9
    iget-object v0, v0, LX/06Nf;->A0I:Landroid/view/View;
    const/16 v1, 0x8
    invoke-virtual {v0, v1}, Landroid/view/View;->setVisibility(I)V
    return-void""", 1)
    return text[:match.start()] + body + text[match.end():]


def patch(root, check=False):
    targets = [
        ("com/feurstagram/extension/Config.smali", config),
        ("com/feurstagram/extension/Block.smali", block),
        ("com/instagram/newsfeed/followrequests/data/FollowRequestsGraphQLDataSource.smali", follow_requests),
        ("X/0H2H.smali", carousel),
    ]
    holder = find(root, "X/06Nf.smali").read_text()
    if '.field public final A0I:Landroid/view/View;' not in holder or 'iput-object p1, p0, LX/06Nf;->A0I:Landroid/view/View;' not in holder:
        raise PatchMismatch("carousel itemView changed")
    edits = []
    for suffix, transform in targets:
        path = find(root, suffix)
        edits.append((path, transform(path.read_text())))
    if not check:
        for path, data in edits:
            path.write_text(data)
    return len(edits)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        count = patch(args.decoded, args.check)
    except PatchMismatch as exc:
        parser.exit(1, f"ERROR: follow recommendation patch incompatible: {exc}\n")
    print(f"GramForge follow recommendations: {count} hooks {'verified' if args.check else 'patched'}")
