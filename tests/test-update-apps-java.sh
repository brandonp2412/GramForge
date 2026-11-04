#!/usr/bin/env bash
# Regression test: CLI_JAVA may be a command resolved through PATH.
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

cp "$repo_dir/update-apps.sh" "$tmp_dir/update-apps.sh"
mkdir -p "$tmp_dir/lib" "$tmp_dir/bin" "$tmp_dir/cli" "$tmp_dir/patches" "$tmp_dir/apk" "$tmp_dir/.tools/feurstagram" "$tmp_dir/tools"
cp "$repo_dir/lib/config.sh" "$tmp_dir/lib/config.sh"
cp "$repo_dir/tools/ensure-apktool.sh" "$tmp_dir/tools/ensure-apktool.sh"
mkdir -p "$tmp_dir/assets"
cp -r "$repo_dir/assets/rotta-launcher" "$tmp_dir/assets/rotta-launcher"
cp "$repo_dir/tools/patch-launcher-icon.py" "$tmp_dir/tools/patch-launcher-icon.py"
cp "$repo_dir/tools/patch-reels-actions.py" "$tmp_dir/tools/patch-reels-actions.py"
cp "$repo_dir/tools/patch-reels-not-interested.py" "$tmp_dir/tools/patch-reels-not-interested.py"
cp "$repo_dir/tools/patch-notification-nudges.py" "$tmp_dir/tools/patch-notification-nudges.py"
cp "$repo_dir/tools/patch-comment-filter.py" "$tmp_dir/tools/patch-comment-filter.py"
cp "$repo_dir/tools/patch-message-requests-link.py" "$tmp_dir/tools/patch-message-requests-link.py"
reels_hash="$(sha256sum "$repo_dir/tools/patch-reels-actions.py" "$repo_dir/tools/patch-reels-not-interested.py" "$repo_dir/tools/patch-notification-nudges.py" "$repo_dir/tools/patch-comment-filter.py" "$repo_dir/tools/patch-message-requests-link.py" | cut -d' ' -f1 | sha256sum | cut -c1-16)"
icon_hash="$(python3 "$repo_dir/tools/patch-launcher-icon.py" --fingerprint "$repo_dir/assets/rotta-launcher")"
chmod +x "$tmp_dir/update-apps.sh" "$tmp_dir/tools/ensure-apktool.sh"
touch "$tmp_dir/APKEditor.jar" "$tmp_dir/cli/morphe-cli.jar" "$tmp_dir/test.keystore" "$tmp_dir/.tools/feurstagram/base.apk"
touch "$tmp_dir/apk/instagram-patched-446.0.0.49.77.apk"

legacy_profile="feur-v446-0-0-49-77-brosssh-v2.8.2-v1.16.0-ads-nav-true-false-false-false-false-false-v5-rotta-$icon_hash-reels-$reels_hash"
profile="feur-v446-0-0-49-77-brosssh-v2.8.2-ads-nav-true-false-false-false-false-false-v5-rotta-$icon_hash-reels-$reels_hash"
printf 'INSTAGRAM_VERSION=446.0.0.49.77\nINSTAGRAM_PATCH_PROFILE=%s\n' "$legacy_profile" > "$tmp_dir/.patched-app-state"

cat > "$tmp_dir/check-instagram-update.sh" <<'EOF'
#!/usr/bin/env bash
printf 'PATCHES_VERSION=v2.8.2\nPATCHES_ASSET=patches.mpp\nCLI_VERSION=v1.16.0\nCLI_JAVA=java\nFEUR_TAG=v446-0-0-49-77\nFEUR_ASSET=base.apk\nFEUR_DIGEST=\n' > .update-state
EOF
chmod +x "$tmp_dir/check-instagram-update.sh"

cat > "$tmp_dir/bin/java" <<'EOF'
#!/usr/bin/env bash
if [[ "$*" == *"APKEditor.jar info"* ]]; then
  printf 'package="com.instagram.android"\nVersionName="446.0.0.49.77"\n'
fi
EOF
chmod +x "$tmp_dir/bin/java"

output="$(GRAMFORGE_CONFIG_FILE=/dev/null GRAMFORGE_KEYSTORE="$tmp_dir/test.keystore" PATH="$tmp_dir/bin:$PATH" "$tmp_dir/update-apps.sh")"
grep -Fqx "instagram: migrated legacy profile without rebuilding 446.0.0.49.77 ($profile)" <<< "$output"
grep -Fqx "INSTAGRAM_PATCH_PROFILE=$profile" "$tmp_dir/.patched-app-state"
grep -Fqx 'INSTAGRAM_TOOLCHAIN_VERSION=v1.16.0' "$tmp_dir/.patched-app-state"

# A patcher-only version update is maintenance, not a new GramForge app profile.
sed -i 's/CLI_VERSION=v1.16.0/CLI_VERSION=v1.18.1/' "$tmp_dir/check-instagram-update.sh"
output="$(GRAMFORGE_CONFIG_FILE=/dev/null GRAMFORGE_KEYSTORE="$tmp_dir/test.keystore" PATH="$tmp_dir/bin:$PATH" "$tmp_dir/update-apps.sh")"
grep -Fqx "instagram: already patched 446.0.0.49.77 ($profile)" <<< "$output"
grep -Fqx 'INSTAGRAM_TOOLCHAIN_VERSION=v1.16.0' "$tmp_dir/.patched-app-state"
