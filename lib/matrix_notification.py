#!/usr/bin/env python3
"""Produce Matrix plain-text and HTML events for GramForge release notifications."""

import argparse
import html
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote, urlsplit


RELEVANT = ("ad block", "ads", "advert", "promot", "deep link", "deeplink", "shared link", "feed", "reels", "signature", "crash", "stability", "performance", "fix")
IRRELEVANT = ("official account", "follow", "first launch", "what's new", "settings page", "update flow", "update checker", "updater", "readme", "website", "release notes", "download progress", "onboarding")


def release_highlights(tag: str) -> list[str]:
    """Only cite upstream changes that may survive GramForge's ads-only profile."""
    if not re.fullmatch(r"v[0-9][0-9A-Za-z_.-]*", tag):
        return []
    fixture = os.environ.get("GRAMFORGE_RELEASE_NOTES_FILE")
    try:
        if fixture:
            notes = Path(fixture).read_text(encoding="utf-8")
        else:
            url = f"https://api.github.com/repos/jean-voila/FeurStagram/releases/tags/{quote(tag)}"
            request = urllib.request.Request(url, headers={"User-Agent": "GramForge-release-notifier", "Accept": "application/vnd.github+json"})
            with urllib.request.urlopen(request, timeout=5) as response:
                notes = json.load(response).get("body", "")
    except (OSError, ValueError, urllib.error.URLError):
        return []

    highlights = []
    for line in notes.splitlines():
        match = re.match(r"^\s*[-*]\s+(.+)", line)
        if not match:
            continue
        item = match.group(1)
        item = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", item)
        item = re.sub(r"[*_`#]", "", item).strip()
        lowered = item.lower()
        if any(term in lowered for term in IRRELEVANT):
            continue
        if "updated to instagram" in lowered or "updated to the latest instagram" in lowered:
            continue
        if not any(term in lowered for term in RELEVANT):
            continue
        # Keep the upstream claim attributable, short, and readable on mobile.
        item = item[:175].rsplit(" ", 1)[0] + "…" if len(item) > 175 else item
        highlights.append("🐛 Upstream: " + item)
        if len(highlights) == 2:
            break
    return highlights


def navigation_summary() -> str:
    tabs = ("Home", "Reels", "Direct", "Search", "Profile", "Create")
    hidden = [tab for tab in tabs if os.environ.get("HIDE_" + tab.upper(), "true" if tab == "Home" else "false").lower() == "true"]
    if hidden:
        return "🧭 Navigation: " + ", ".join(hidden) + " hidden; other tabs retained"
    return "🧭 Navigation: all tabs retained"


def make_payload(args: argparse.Namespace) -> dict[str, str]:
    title = args.title
    if args.error_log is not None:
        plain = title + "\n\n" + args.error_log
        formatted = f"<h3>🚨 {html.escape(title)}</h3><pre>{html.escape(args.error_log)}</pre>"
    else:
        version = args.version
        items = []
        if args.previous_version and args.previous_version != version:
            items.append(f"📱 Instagram {args.previous_version} → {version}")
        else:
            items.append(f"📦 Updated GramForge APK for Instagram {version}")
        if args.release_tag and args.release_tag != args.previous_release_tag:
            items.append(f"🛡️ FeurStagram ad-filtering base updated to {args.release_tag}")
            items.extend(release_highlights(args.release_tag))
        else:
            items.append("🛡️ FeurStagram ad filtering retained in ads-only mode")
        if args.previous_profile and args.profile and args.previous_profile != args.profile:
            items.append("🔧 GramForge patch profile changed")
        items.append(navigation_summary())

        plain = title + f"\n\nInstagram {version} is ready.\n\n📝 Build highlights\n" + "\n".join("• " + item for item in items)
        formatted = (
            f"<h3>📦 {html.escape(title)}</h3>"
            f"<p>Instagram <strong>{html.escape(version)}</strong> is ready.</p>"
            "<p>📝 <strong>Build highlights</strong></p><ul>"
            + "".join("<li>" + html.escape(item) + "</li>" for item in items)
            + "</ul>"
        )
        if args.url:
            parsed = urlsplit(args.url)
            if parsed.scheme not in ("https", "http") or not parsed.netloc:
                raise ValueError("APK download URL must be HTTP(S)")
            plain += "\n\n🔗 Download APK: " + args.url
            formatted += f'<p>🔗 <a href="{html.escape(args.url, quote=True)}">Download APK</a></p>'

    return {"msgtype": "m.text", "body": plain, "format": "org.matrix.custom.html", "formatted_body": formatted}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--error-log")
    parser.add_argument("--version", default="")
    parser.add_argument("--previous-version", default="")
    parser.add_argument("--release-tag", default="")
    parser.add_argument("--previous-release-tag", default="")
    parser.add_argument("--profile", default="")
    parser.add_argument("--previous-profile", default="")
    parser.add_argument("--url", default="")
    print(json.dumps(make_payload(parser.parse_args()), ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
