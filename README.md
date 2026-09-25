<p align="center">
  <img src="assets/gramforge-banner.svg" alt="GramForge — Forge the Instagram you actually want." width="100%">
</p>

# GramForge

Reproducible command-line Instagram customization built on Morphe.

The default profile:

- removes ads;
- removes the Home navigation tab;
- leaves Reels, Direct, Search, Profile, and Create visible;
- signs the patched APK with a private keystore kept outside the repository;
- can optionally publish new builds and send Matrix notifications.

## Requirements

- Bash
- Java compatible with the current Morphe Desktop release
- `curl`, `jq`, `unzip`, and standard Unix tools
- `APKEditor.jar` in the repository root

GramForge tracks the latest stable FeurStagram release as its current open-source ad-filtering base. The standard APK is selected from GitHub Releases, its GitHub-provided SHA-256 digest is verified, and its package/version are checked before patching. GramForge then normalizes FeurStagram to an ads-only runtime profile, disables FeurStagram-specific update/onboarding prompts, and applies the configured navigation changes with Morphe.

Downloaded APKs, patch bundles, CLI jars, signing keys, logs, and runtime state are intentionally ignored by Git.

## Configuration

Copy the example configuration and edit it locally:

```bash
mkdir -p ~/.config/gramforge
cp config.example.env ~/.config/gramforge/config.env
chmod 600 ~/.config/gramforge/config.env
```

Keep the signing keystore outside the repository and set `GRAMFORGE_KEYSTORE` to its path.

Matrix and APK publishing settings are runtime configuration only. They do not belong in source control.

Navigation choices are also configurable with `HIDE_HOME`, `HIDE_REELS`, `HIDE_DIRECT`, `HIDE_SEARCH`, `HIDE_PROFILE`, and `HIDE_CREATE`.

## Build

```bash
./update-apps.sh
```

GramForge keeps Morphe Desktop, the Morphe navigation patch bundle, and the FeurStagram base current. It downloads a pinned, SHA-256-verified Apktool release on demand, rewrites FeurStagram's runtime defaults so ads remain blocked while feed, Reels, Explore, stories, suggestions, and navigation stay otherwise stock, rebuilds the APK, normalizes its ZIP metadata, then force-applies the narrow Morphe navigation patch to the newer Instagram base. The Morphe result report must prove the navigation patch succeeded before build state is advanced.

The final signed APK is written under apk/ with its Instagram version in the filename. Upstream changes that make the FeurStagram normalizer or navigation fingerprint stop matching fail the build instead of silently weakening the profile.

## Scheduled publishing

`cron-update.sh` runs the same build, publishes a changed APK when `APK_PUBLIC_DIR` and `APK_PUBLIC_URL` are configured, and sends a Matrix notification using the configured homeserver, room ID, and access token.

No deployment hostname, room ID, access token, signing key, or local machine path is stored in the repository.
