#!/usr/bin/env bash
# Regression test: CLI_JAVA may be a command resolved through PATH.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

cp "$repo_dir/update-apps.sh" "$tmp_dir/update-apps.sh"
mkdir -p "$tmp_dir/lib"
cp "$repo_dir/lib/config.sh" "$tmp_dir/lib/config.sh"
chmod +x "$tmp_dir/update-apps.sh"
mkdir -p "$tmp_dir/bin" "$tmp_dir/cli" "$tmp_dir/patches" "$tmp_dir/apk"
touch "$tmp_dir/APKEditor.jar" "$tmp_dir/cli/morphe-cli.jar" "$tmp_dir/test.keystore"
printf 'INSTAGRAM_VERSION=123.0.0\nINSTAGRAM_PATCH_PROFILE=brosssh-v2.8.1-v1.13.1-ads-nav-true-false-false-false-false-false-v1\n' > "$tmp_dir/.patched-app-state"

printf '%s\n' '#!/usr/bin/env bash' 'printf "PATCHES_VERSION=v2.8.1\nPATCHES_ASSET=patches-2.8.1.mpp\nCLI_VERSION=v1.13.1\nCLI_JAVA=java\n" > .update-state' > "$tmp_dir/check-instagram-update.sh"
chmod +x "$tmp_dir/check-instagram-update.sh"

printf '%s\n' '#!/usr/bin/env bash' 'if [[ "$*" == *"list-versions"* ]]; then' '  printf "Most common compatible versions:\n  123.0.0\n"' 'fi' > "$tmp_dir/bin/java"
chmod +x "$tmp_dir/bin/java"

output="$(GRAMFORGE_CONFIG_FILE=/dev/null GRAMFORGE_KEYSTORE="$tmp_dir/test.keystore" PATH="$tmp_dir/bin:$PATH" "$tmp_dir/update-apps.sh")"
grep -Fqx 'instagram: already patched 123.0.0 (brosssh-v2.8.1-v1.13.1-ads-nav-true-false-false-false-false-false-v1)' <<< "$output"
