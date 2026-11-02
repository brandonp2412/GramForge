# GramForge

Builds signed, customized Instagram APKs from FeurStagram using Morphe.

- Blocks ads and hides the Home tab.
- Removes Reels Save/Repost buttons and their counts.
- Replaces organic Reels’ More button with immediate **Not interested** (sponsored Reels keep More).
- Suppresses notification prompts and customizes the launcher icon.

## Build

Requires Bash, Java, `curl`, `jq`, `flock`, `unzip`, `rg`, and `APKEditor.jar` in the repository root.

```bash
mkdir -p ~/.config/gramforge
cp config.example.env ~/.config/gramforge/config.env
chmod 600 ~/.config/gramforge/config.env
./update-apps.sh
```

Set `GRAMFORGE_KEYSTORE` to a private keystore outside the repository. Configure navigation with the `HIDE_*` options. Signed APKs are saved in `apk/`. Builds fail if upstream changes invalidate a patch.

## Automatic updates

`./cron-update.sh` can publish changed APKs (`APK_PUBLIC_DIR`, `APK_PUBLIC_URL`) and send Matrix notifications with source-linked changelogs (`MATRIX_*`).

For private ADB delivery, set `GRAMFORGE_ADB_SERIAL`, `GRAMFORGE_ADB_EXPECTED_MODEL`, and `GRAMFORGE_ADB_ONLY=true`. Installs preserve app data and retry if the device is unavailable.

Keep keys, tokens, device identifiers, and host-specific settings in the local configuration—never in Git.
