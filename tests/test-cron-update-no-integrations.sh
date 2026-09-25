#!/usr/bin/env bash
# Regression test: scheduled builds work without Matrix or a publishing destination.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

cp "$repo_dir/cron-update.sh" "$tmp_dir/cron-update.sh"
mkdir -p "$tmp_dir/lib"
cp "$repo_dir/lib/config.sh" "$tmp_dir/lib/config.sh"
chmod +x "$tmp_dir/cron-update.sh"

printf 'INSTAGRAM_VERSION=1.0.0\nINSTAGRAM_PATCH_PROFILE=stable\n' > "$tmp_dir/.patched-app-state"
printf '%s\n' '#!/usr/bin/env bash' 'exit 0' > "$tmp_dir/update-apps.sh"
chmod +x "$tmp_dir/update-apps.sh"

GRAMFORGE_CONFIG_FILE=/dev/null "$tmp_dir/cron-update.sh"
