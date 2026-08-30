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
- `curl`, `jq`, and standard Unix tools
- `APKEditor.jar` in the repository root
- an Instagram APKMirror bundle matching the version supported by the current patch bundle

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

GramForge keeps Morphe Desktop and the Instagram Morphe patch bundle current, determines the supported Instagram version, merges the matching local APK bundle, applies the configured GramForge profile, and writes the result under `apk/`.

If the supported Instagram version changes, place the matching APKMirror bundle at:

```text
apk/instagram-<version>.apkm
```

and run the updater again.

## Scheduled publishing

`cron-update.sh` runs the same build, publishes a changed APK when `APK_PUBLIC_DIR` and `APK_PUBLIC_URL` are configured, and sends a Matrix notification using the configured homeserver, room ID, and access token.

No deployment hostname, room ID, access token, signing key, or local machine path is stored in the repository.
