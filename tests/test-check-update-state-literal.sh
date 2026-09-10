#!/usr/bin/env bash
# Regression test: cached release metadata must never be evaluated as shell code.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

cp "$repo_dir/check-instagram-update.sh" "$tmp_dir/check-instagram-update.sh"
chmod +x "$tmp_dir/check-instagram-update.sh"
mkdir -p "$tmp_dir/bin" "$tmp_dir/patches" "$tmp_dir/cli"
touch "$tmp_dir/cli/morphe-cli.jar"
touch "$tmp_dir/patches/\$(touch PWNED).mpp"

printf '%s\n' \
  'PATCHES_VERSION=v-patches' \
  'PATCHES_ASSET=$(touch PWNED).mpp' \
  'CLI_VERSION=v-cli' \
  'CLI_JAVA=java' \
  > "$tmp_dir/.update-state"

printf '%s\n' \
  '#!/usr/bin/env bash' \
  'if [[ "$*" == *"morphe-patches"* ]]; then' \
  '  printf '\''{"tag_name":"v-patches","assets":[{"name":"$(touch PWNED).mpp","browser_download_url":"https://example.test/patch"}]}\n'\''' \
  'else' \
  '  printf '\''{"tag_name":"v-cli","assets":[{"name":"morphe-cli.jar","browser_download_url":"https://example.test/cli"}]}\n'\''' \
  'fi' \
  > "$tmp_dir/bin/curl"
chmod +x "$tmp_dir/bin/curl"

printf '%s\n' '#!/usr/bin/env bash' 'exit 0' > "$tmp_dir/bin/java"
chmod +x "$tmp_dir/bin/java"

env PATH="$tmp_dir/bin:$PATH" "$tmp_dir/check-instagram-update.sh" >/dev/null
[[ ! -e "$tmp_dir/PWNED" ]]
grep -Fqx 'PATCHES_ASSET=$(touch PWNED).mpp' "$tmp_dir/.update-state"
