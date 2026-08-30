#!/usr/bin/env bash
# Regression test: the Instagram build enables ad removal and hides only the Home navigation tab.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

cp "$repo_dir/update-apps.sh" "$tmp_dir/update-apps.sh"
mkdir -p "$tmp_dir/lib"
cp "$repo_dir/lib/config.sh" "$tmp_dir/lib/config.sh"
chmod +x "$tmp_dir/update-apps.sh"
mkdir -p "$tmp_dir/bin" "$tmp_dir/cli" "$tmp_dir/patches" "$tmp_dir/apk"
touch "$tmp_dir/APKEditor.jar" "$tmp_dir/cli/morphe-cli.jar" "$tmp_dir/patches/instagram.mpp" "$tmp_dir/test.keystore"
touch "$tmp_dir/apk/instagram-124.0.0.apkm"

printf '%s\n' \
  '#!/usr/bin/env bash' \
  'printf "PATCHES_VERSION=v2.8.1\nPATCHES_ASSET=patches-2.8.1.mpp\nCLI_VERSION=v1.14.0\nCLI_JAVA=java\n" > .update-state' \
  > "$tmp_dir/check-instagram-update.sh"
chmod +x "$tmp_dir/check-instagram-update.sh"

printf '%s\n' \
  '#!/usr/bin/env bash' \
  'set -euo pipefail' \
  'args="$*"' \
  'if [[ "$args" == *"list-versions"* ]]; then' \
  '  printf "Most common compatible versions:\n  124.0.0\n"' \
  '  exit 0' \
  'fi' \
  'if [[ "$args" == *"APKEditor.jar"* ]]; then' \
  '  while (($#)); do [[ "$1" == "-o" ]] && { shift; touch "$1"; exit 0; }; shift; done' \
  'fi' \
  'if [[ "$args" == *"morphe-cli.jar patch"* ]]; then' \
  '  printf "%s\n" "$args" > "$PATCH_ARGS_FILE"' \
  '  while (($#)); do [[ "$1" == "-o" ]] && { shift; touch "$1"; exit 0; }; shift; done' \
  'fi' \
  'exit 0' \
  > "$tmp_dir/bin/java"
chmod +x "$tmp_dir/bin/java"

PATCH_ARGS_FILE="$tmp_dir/patch-args" GRAMFORGE_CONFIG_FILE=/dev/null GRAMFORGE_KEYSTORE="$tmp_dir/test.keystore" PATH="$tmp_dir/bin:$PATH" "$tmp_dir/update-apps.sh" >/dev/null

patch_args="$(<"$tmp_dir/patch-args")"
[[ "$patch_args" == *'-e Hide ads'* ]]
[[ "$patch_args" == *'-e Hide navigation buttons'* ]]
[[ "$patch_args" == *'-O hideHome=true'* ]]
[[ "$patch_args" == *'-O hideReels=false'* ]]
[[ "$patch_args" == *'-O hideDirect=false'* ]]
[[ "$patch_args" == *'-O hideSearch=false'* ]]
[[ "$patch_args" == *'-O hideProfile=false'* ]]
[[ "$patch_args" == *'-O hideCreate=false'* ]]
[[ "$patch_args" == *'--bytecode-mode STRIP_FAST'* ]]
[[ "$patch_args" == *'--exclusive'* ]]
grep -Fqx 'INSTAGRAM_VERSION=124.0.0' "$tmp_dir/.patched-app-state"
grep -Fqx 'INSTAGRAM_PATCH_PROFILE=brosssh-v2.8.1-v1.14.0-ads-nav-true-false-false-false-false-false-v1' "$tmp_dir/.patched-app-state"
