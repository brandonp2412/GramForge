#!/usr/bin/env python3
"""Hide formulaic Instagram comments, including spam, bait and stock reactions.

The on-device matcher keeps no personal data and makes no network calls.
It filters the whole Compose CommentRow (including replies and action buttons).
The obfuscated renderer and model field are verified before modifying an APK.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import unicodedata
from pathlib import Path


class PatchMismatch(Exception):
    pass


MARKER = "com.instagram.comments.mvvm.view.compose.CommentRow (CommentRow.kt:"
METHOD_HEADER = (
    ".method public static final "
    "A00(LX/1BaO;LX/05n4;LX/0Il1;LX/0Hxu;LX/0iom;LX/0Hes;IIZZZZZ)V"
)
MODEL_FIELD = "LX/0Il1;->A0O:Ljava/lang/String;"
RUNTIME_CLASS = "Lcom/gramforge/CommentFilter;"
ANCHOR = (
    "    invoke-static {v5, v10}, LX/00d6;->A0V(Ljava/lang/Object;I)V\n\n"
    "    const/4 v14, 0x1"
)
METHOD_RE = re.compile(r"(?ms)^\.method [^\n]+\n.*?^\.end method")

# The exact phrases are intentionally broad: this is a *personal* high-noise
# filter, not a moderation decision about what other people are allowed to say.
SPAM_PHRASES = (
    r"\b(?:your (?:instagram )?page|"
    r"promote (?:it|this) on|send (?:pic|picture|it) (?:on|to)|"
    r"dm (?:it on|to collab|(?:me )?for (?:promos?|promotions?|collabs?|collaborations?))|"
    r"(?:grow|boost|increase) your (?:page|account|followers)|"
    r"(?:buy|free|get more) followers|follow for follow|like for like|"
    r"link in (?:my|your|the) bio|check (?:out )?(?:my|our) (?:profile|bio|story)|"
    r"(?:visit|click) (?:my|our) (?:profile|page)|see my story|"
    r"claim your (?:prize|reward)|you (?:have|ve) been selected|"
    r"congratulations you won|(?:guaranteed|daily) (?:profit|returns?)|"
    r"(?:forex|crypto|bitcoin) (?:mentor|expert|investment)|"
    r"recover your (?:funds|account)|recovery expert|"
    r"your (?:page|account) (?:will be|has been) (?:disabled|suspended|restricted)|"
    r"verify your (?:page|account)|copyright violation|"
    r"(?:watch|view) my (?:story|profile)|(?:onlyfans|linktree) (?:in|on) (?:my )?bio|"
    r"message (?:me|us) (?:for|on) (?:whatsapp|telegram)|"
    r"official support team|"
    r"click (?:the|this|my) link|"
    r"check out (?:my|our) page)\b"
)

GENERIC_EXACT = (
    "lol", "lmao", "lmfao", "rofl", "haha", "hahaha", "hehe", "omg",
    "wtf", "bro", "bruh", "fr", "real", "facts", "same", "agreed",
    "true", "exactly", "wow", "nice", "amazing", "awesome",
    "beautiful", "cute", "cool", "slay", "iconic", "ate", "legend",
    "legendary", "incredible", "perfect", "fire", "first", "second",
    "third", "this", "yes", "no", "yep", "nah", "no way", "love it",
    "love this", "i love this", "so funny", "so good", "so true",
    "this is so true", "great content", "well said", "good job",
    "keep going", "keep it up", "i agree", "this made my day",
    "made my day", "this is gold", "this is crazy",
    "this is hilarious", "i cant stop laughing",
    "i can t stop laughing", "too funny", "i m dead", "im dead",
    "dead", "crying", "literally crying", "this wins the internet",
    "i needed this today", "facts bro", "so relatable", "relatable",
    "same energy", "the best", "great post", "great video", "great reel",
    "funny", "hilarious", "bro understood the assignment",
    "who let bro cook", "i can t unsee this",
    "the comments never disappoint", "this comment section",
    "what page is this", "you re on my page",
    "this is a masterpiece", "my favorite", "my favourite",
    "you win", "i am crying", "im crying", "i m crying",
    "literally me", "thats me", "that s me", "this is me",
    "i feel attacked", "i feel called out", "not me", "deadass",
)
GENERIC_EXACT_PATTERN = (
    r"^(?:" + "|".join(re.escape(phrase) for phrase in GENERIC_EXACT) + r")$"
)

# These are only stock sentence *shapes*. A punchline with additional original
# detail (e.g. "the pigeon is invoicing the sky") stays visible.
GENERIC_TEMPLATES = (
    r"^(?:"
    r"(?:your (?:(?:instagram )?(?:page|profile|posts?|reels?|videos?|pictures?|"
    r"content|photos?)|profile picture)|this|that|it|these|you)"
    r" (?:is|are|was|were|looks?|seems?)"
    r" (?:(?:so|very|really|absolutely|literally|too|super) )?"
    r"(?:funny|hilarious|crazy|amazing|great|good|beautiful|cute|wild|"
    r"iconic|perfect|awesome|incredible|cool|insane|fire|the best|accurate)"
    r"|(?:that s|it s|this is|that is) (?:so |very |really )?"
    r"(?:funny|hilarious|crazy|amazing|good|beautiful|awesome|perfect|iconic|insane)"
    r"|(?:nice|great|amazing|awesome|beautiful|funny|cool|perfect)"
    r" (?:video|reel|post|content|pic|picture|photo|work|job|one|stuff|edit|page)"
    r"|(?:do (?:you|u) accept|(?:can|could|would) (?:you|u)"
    r" (?:dm|send|share)|(?:dm|message|inbox) me|"
    r"(?:congratulations|congrats) (?:on|to|you)|"
    r"anyone else|who else|is it just me|"
    r"does anyone (?:else |know|remember)|"
    r"when (?:you|u) (?:realize|realise|remember)|"
    r"how (?:is|are) (?:this|these|you) (?:so|even)|"
    r"why (?:is|are) (?:this|these|you) (?:so|even)|"
    r"i (?:can t|cant|cannot) (?:stop|believe|wait)|"
    r"i (?:love|adore|enjoy) (?:your|this|that|these)|"
    r"you(?: re| are)? (?:so |very |literally )?(?:funny|amazing|awesome|cute|beautiful|hilarious)|"
    r"what (?:camera|app|filter) (?:do|did) (?:you|u) (?:use|have)|"
    r"where (?:is|was) (?:this|that) (?:filmed|taken|from)|"
    r"if (?:you|you re|you are) reading this|"
    r"the algorithm brought me here|here from|first to comment|"
    r"please follow|follow me|like this comment|can we appreciate|"
    r"let s take a moment|where can i get|how can i get)"
    r"(?: .*)?"
    r")$"
)

INVESTMENT_BAIT = (
    r"^(?=.*\b(?:bitcoin|crypto|forex|investment|trading|dogecoin|btc)\b)"
    r"(?=.*\b(?:profit|returns?|earn|earned|made|double|guaranteed|"
    r"invest|invested|money|mentor|expert|dm|whatsapp)\b).*$"
)

PATTERNS = (
    SPAM_PHRASES,
    GENERIC_EXACT_PATTERN,
    GENERIC_TEMPLATES,
    INVESTMENT_BAIT,
)
HOOK = (
    "    # gramforge: hide formulaic comment rows before Compose opens a group.\n"
    f"    iget-object v0, v5, {MODEL_FIELD}\n\n"
    f"    invoke-static {{v0}}, {RUNTIME_CLASS}->shouldHide(Ljava/lang/String;)Z\n\n"
    "    move-result v0\n\n"
    "    if-eqz v0, :gramforge_comment_visible\n\n"
    "    return-void\n\n"
    "    :gramforge_comment_visible\n\n"
)


def normalize_comment(comment: str) -> str:
    """Python reference for the same normalization emitted in the Smali helper."""
    value = unicodedata.normalize("NFKC", comment).lower()
    return " ".join("".join(
        char if unicodedata.category(char)[0] in ("L", "N") else " "
        for char in value
    ).split())


def should_hide(comment: str | None) -> bool:
    """Reference behavior for fixture and false-positive testing."""
    if comment is None:
        return False
    normalized = normalize_comment(comment)
    return not normalized or any(re.search(pattern, normalized) for pattern in PATTERNS)


def runtime_smali() -> str:
    fields = "".join(
        f".field private static final A{index:02d}:Ljava/util/regex/Pattern;\n"
        for index in range(len(PATTERNS))
    )
    setup = ""
    checks = ""
    for index, pattern in enumerate(PATTERNS):
        field = f"A{index:02d}"
        setup += (
            f"    const-string v0, {json.dumps(pattern, ensure_ascii=True)}\n\n"
            "    invoke-static {v0}, Ljava/util/regex/Pattern;->compile(Ljava/lang/String;)Ljava/util/regex/Pattern;\n\n"
            "    move-result-object v0\n\n"
            f"    sput-object v0, {RUNTIME_CLASS}->{field}:Ljava/util/regex/Pattern;\n\n"
        )
        checks += (
            f"    sget-object v1, {RUNTIME_CLASS}->{field}:Ljava/util/regex/Pattern;\n\n"
            "    invoke-virtual {v1, v0}, Ljava/util/regex/Pattern;->matcher(Ljava/lang/CharSequence;)Ljava/util/regex/Matcher;\n\n"
            "    move-result-object v1\n\n"
            "    invoke-virtual {v1}, Ljava/util/regex/Matcher;->find()Z\n\n"
            "    move-result v1\n\n"
            "    if-nez v1, :gramforge_hide\n\n"
        )
    return (
        f".class public final {RUNTIME_CLASS}\n"
        ".super Ljava/lang/Object;\n\n"
        f"{fields}\n"
        ".method static constructor <clinit>()V\n"
        "    .locals 1\n\n"
        f"{setup}"
        "    return-void\n"
        ".end method\n\n"
        ".method public static shouldHide(Ljava/lang/String;)Z\n"
        "    .locals 3\n\n"
        "    if-eqz p0, :gramforge_visible\n\n"
        "    sget-object v1, Ljava/text/Normalizer$Form;->NFKC:Ljava/text/Normalizer$Form;\n\n"
        "    invoke-static {p0, v1}, Ljava/text/Normalizer;->normalize(Ljava/lang/CharSequence;Ljava/text/Normalizer$Form;)Ljava/lang/String;\n\n"
        "    move-result-object v0\n\n"
        "    sget-object v1, Ljava/util/Locale;->ROOT:Ljava/util/Locale;\n\n"
        "    invoke-virtual {v0, v1}, Ljava/lang/String;->toLowerCase(Ljava/util/Locale;)Ljava/lang/String;\n\n"
        "    move-result-object v0\n\n"
        f'    const-string v1, {json.dumps(r"[^\p{L}\p{N}]+")}\n\n'
        '    const-string v2, " "\n\n'
        "    invoke-virtual {v0, v1, v2}, Ljava/lang/String;->replaceAll(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;\n\n"
        "    move-result-object v0\n\n"
        "    invoke-virtual {v0}, Ljava/lang/String;->trim()Ljava/lang/String;\n\n"
        "    move-result-object v0\n\n"
        "    invoke-virtual {v0}, Ljava/lang/String;->isEmpty()Z\n\n"
        "    move-result v1\n\n"
        "    if-nez v1, :gramforge_hide\n\n"
        f"{checks}"
        "    :gramforge_visible\n"
        "    const/4 v0, 0x0\n"
        "    return v0\n\n"
        "    :gramforge_hide\n"
        "    const/4 v0, 0x1\n"
        "    return v0\n"
        ".end method\n"
    )


def locate_row(root: Path) -> Path:
    search = subprocess.run(
        ["rg", "--no-ignore", "-l", "-F", MARKER, "--glob", "*.smali", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )
    if search.returncode not in (0, 1):
        raise PatchMismatch(f"comment renderer search failed: {search.stderr.strip()}")
    matches = [Path(line) for line in search.stdout.splitlines()]
    if len(matches) != 1:
        raise PatchMismatch(f"expected one Compose CommentRow, found {len(matches)}")
    return matches[0]


def patch(root: Path, *, check: bool = False) -> list[str]:
    if not root.is_dir():
        raise PatchMismatch(f"decoded APK directory not found: {root}")
    path = locate_row(root)
    source = path.read_text()
    matches = [match for match in METHOD_RE.finditer(source) if MARKER in match.group()]
    if len(matches) != 1:
        raise PatchMismatch(f"expected one Compose CommentRow method, found {len(matches)}")
    method = matches[0].group()
    if not method.startswith(METHOD_HEADER + "\n"):
        raise PatchMismatch("CommentRow signature changed")
    if "gramforge_comment_visible" in source:
        raise PatchMismatch("comment filter already applied")
    if (
        ".locals 59" not in method
        or method.count(ANCHOR) != 1
        or method.count(MODEL_FIELD) != 1
        or "invoke-interface {v0, v1}, LX/1BaO;->Hg2(I)V" not in method
    ):
        raise PatchMismatch("CommentRow body or model text field changed")
    helper = root / path.relative_to(root).parts[0] / "com/gramforge/CommentFilter.smali"
    if helper.exists() or any(root.glob("smali*/com/gramforge/CommentFilter.smali")):
        raise PatchMismatch("comment filter helper already exists")
    updated = method.replace(
        ANCHOR, ANCHOR.replace("    const/4 v14, 0x1", HOOK + "    const/4 v14, 0x1"), 1
    )
    if not check:
        helper.parent.mkdir(parents=True, exist_ok=True)
        helper.write_text(runtime_smali())
        path.write_text(source.replace(method, updated, 1))
    return ["spam templates", "generic reactions", "formulaic comments"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decoded_apk", type=Path)
    parser.add_argument("--check", action="store_true", help="validate without modifying smali")
    args = parser.parse_args()
    try:
        labels = patch(args.decoded_apk, check=args.check)
    except PatchMismatch as exc:
        parser.exit(1, f"ERROR: Instagram comment filter incompatible: {exc}\n")
    print("GramForge comment filter " + ("verified" if args.check else "patched") + ": " + ", ".join(labels))


if __name__ == "__main__":
    main()
