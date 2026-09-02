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

GramForge automatically acquires the exact supported Instagram bundle when it is not already cached locally. It uses EFF's `apkeep` with APKPure as the source, requests the `arm64-v8a` variant, and verifies the downloaded package name and version before patching. The pinned `apkeep` binary is downloaded on demand and SHA-256 checked before execution.

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

GramForge keeps Morphe Desktop and the Instagram Morphe patch bundle current, determines the supported Instagram version, obtains the matching Instagram bundle automatically when needed, merges it, applies the configured GramForge profile, and writes the result under `apk/`.

Existing `apk/instagram-<version>.apkm` or `apk/instagram-<version>.xapk` files are reused. Otherwise GramForge installs its pinned `apkeep` release under `.tools/`, downloads `com.instagram.android@<version>` from APKPure for `arm64-v8a`, verifies the bundle metadata, and continues without manual intervention.

## Scheduled publishing

`cron-update.sh` runs the same build, publishes a changed APK when `APK_PUBLIC_DIR` and `APK_PUBLIC_URL` are configured, and sends a Matrix notification using the configured homeserver, room ID, and access token.

No deployment hostname, room ID, access token, signing key, or local machine path is stored in the repository.
