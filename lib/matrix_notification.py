#!/usr/bin/env python3
"""Matrix release messages backed by actual, version-scoped upstream release notes."""

import argparse
import html
import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urlencode, urlsplit


class ChangelogUnavailable(RuntimeError):
    """Fetching a complete, trustworthy release range failed; retry later."""


@dataclass(frozen=True)
class Change:
    text: str
    tag: str
    url: str
    source: str


# GramForge explicitly strips FeurStagram onboarding, updater and its settings UI.
# Never announce changes to those removed screens as changes to our APK.
REMOVED_UPSTREAM_UI = re.compile(
    r"\b(?:official account|follow (?:the |our )?account|first[- ]run|first launch|"
    r"onboarding|settings page|settings window|settings screen|update (?:screen|flow|checker|prompt)|"
    r"in[- ]app updates?|background updater|readme|website|download progress|"
    r"what.s new card|force dark toggle)\b", re.IGNORECASE,
)


def fetch_release_range(repo: str, current: str, previous: str) -> list[dict]:
    """Get every stable release after previous, inclusive of current, oldest first."""
    if not current or current == previous:
        return []
    if not re.fullmatch(r"v[0-9][a-zA-Z0-9_.-]*", current):
        raise ChangelogUnavailable(f"Invalid release tag for {repo}: {current!r}")
    if previous and not re.fullmatch(r"v[0-9][a-zA-Z0-9_.-]*", previous):
        raise ChangelogUnavailable(f"Invalid previous release tag for {repo}: {previous!r}")

    releases = []
    try:
        for page in range(1, 6):
            query = urlencode({"per_page": 100, "page": page})
            url = f"https://api.github.com/repos/{repo}/releases?{query}"
            request = urllib.request.Request(url, headers={
                "User-Agent": "GramForge-release-notifier", "Accept": "application/vnd.github+json",
            })
            with urllib.request.urlopen(request, timeout=12) as response:
                chunk = json.load(response)
            if not isinstance(chunk, list):
                raise ChangelogUnavailable(f"Unexpected GitHub releases response for {repo}")
            releases.extend(r for r in chunk if not r.get("draft") and not r.get("prerelease"))
            if previous and any(r.get("tag_name") == previous for r in releases) and any(r.get("tag_name") == current for r in releases):
                break
            if not previous and any(r.get("tag_name") == current for r in releases):
                break
            if len(chunk) < 100:
                break
    except (OSError, ValueError, urllib.error.URLError, TimeoutError) as exc:
        raise ChangelogUnavailable(f"Cannot fetch {repo} changelog: {exc}") from exc

    tags = [r.get("tag_name") for r in releases]
    if current not in tags or (previous and previous not in tags):
        raise ChangelogUnavailable(f"Cannot verify complete {repo} release range {previous!r} → {current!r}")
    start = tags.index(current)
    end = tags.index(previous) if previous else start + 1
    if previous and end <= start:
        raise ChangelogUnavailable(f"{repo} release range is reversed: {previous!r} → {current!r}")
    return list(reversed(releases[start:end]))


def clean_markdown(text: str) -> str:
    text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\*\*|__|`", "", text)
    return re.sub(r"\s+", " ", text).strip()


def actual_bullets(release: dict, repo: str) -> list[Change]:
    """Use original release-note bullets, not inferred or template-generated claims."""
    source = "FeurStagram" if repo == "jean-voila/FeurStagram" else "Morphe"
    tag = release["tag_name"]
    url = release.get("html_url") or f"https://github.com/{repo}/releases/tag/{tag}"
    if not url.startswith(f"https://github.com/{repo}/releases/tag/"):
        raise ChangelogUnavailable(f"Unexpected {repo} release link")
    changes = []
    for line in (release.get("body") or "").splitlines():
        match = re.match(r"^\s*[-*]\s+(.*\S)\s*$", line)
        if not match:
            continue
        original = match.group(1)
        # Only the Instagram navigation patch is applied from Morphe's patch bundle.
        if source == "Morphe" and not re.search(r"\bInstagram(?:\s*[-:]\s*Hide navigation buttons)?\b", original, re.I):
            continue
        if source == "Morphe" and not re.search(r"\bnavigation\b|\bnav(?:igation)? bar\b", original, re.I):
            continue
        text = clean_markdown(original)
        if source == "FeurStagram" and REMOVED_UPSTREAM_UI.search(text):
            continue
        if text:
            changes.append(Change(text=text, tag=tag, url=url, source=source))
    return changes


def upstream_changes(args: argparse.Namespace) -> list[Change]:
    changes = []
    for repo, current, previous in (
        ("jean-voila/FeurStagram", args.release_tag, args.previous_release_tag),
        ("brosssh/morphe-patches", args.patches_tag, args.previous_patches_tag),
    ):
        for release in fetch_release_range(repo, current, previous):
            changes.extend(actual_bullets(release, repo))
    # Cap message size without inventing or modifying any release-note claim.
    return changes[-8:]


def make_payload(args: argparse.Namespace) -> dict[str, str]:
    title = args.title
    if args.error_log is not None:
        plain = title + "\n\n" + args.error_log
        formatted = f"<h3>🚨 {html.escape(title)}</h3><pre>{html.escape(args.error_log)}</pre>"
    else:
        changes = upstream_changes(args)
        version = args.version
        plain = f"{title}\n\nInstagram {version} is ready."
        formatted = f"<h3>📦 {html.escape(title)}</h3><p>Instagram <strong>{html.escape(version)}</strong> is ready.</p>"
        if changes:
            plain += "\n\n📝 Upstream changelog (source-linked):\n" + "\n".join(
                f"• {change.text} ({change.source} {change.tag}: {change.url})" for change in changes
            )
            formatted += "<p>📝 <strong>Upstream changelog</strong></p><ul>" + "".join(
                "<li>" + html.escape(change.text) + " "
                + f'(<a href="{html.escape(change.url, quote=True)}">{html.escape(change.source)} {html.escape(change.tag)}</a>)</li>'
                for change in changes
            ) + "</ul>"
        else:
            plain += "\n\nNo applicable changelog entries for this build."
            formatted += "<p>No applicable changelog entries for this build.</p>"

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
    parser.add_argument("--release-tag", default="")
    parser.add_argument("--previous-release-tag", default="")
    parser.add_argument("--patches-tag", default="")
    parser.add_argument("--previous-patches-tag", default="")
    parser.add_argument("--url", default="")
    args = parser.parse_args()
    try:
        print(json.dumps(make_payload(args), ensure_ascii=False, separators=(",", ":")))
    except ChangelogUnavailable as exc:
        parser.exit(1, f"Changelog unavailable; notification will retry: {exc}\n")


if __name__ == "__main__":
    main()
