#!/usr/bin/env bash
# Regression test: Matrix publications use the configured bearer credential and room.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

cp "$repo_dir/cron-update.sh" "$tmp_dir/cron-update.sh"
mkdir -p "$tmp_dir/lib"
cp "$repo_dir/lib/config.sh" "$tmp_dir/lib/config.sh"
chmod +x "$tmp_dir/cron-update.sh"
mkdir -p "$tmp_dir/bin" "$tmp_dir/public" "$tmp_dir/apk"
printf 'INSTAGRAM_VERSION=2.0.0\nINSTAGRAM_PATCH_PROFILE=old-profile\n' > "$tmp_dir/.patched-app-state"
touch "$tmp_dir/apk/instagram-patched-2.0.0.apk"

# A patch-profile change on the same Instagram version must still republish.
printf '%s\n' '#!/usr/bin/env bash' 'printf "INSTAGRAM_VERSION=2.0.0\\nINSTAGRAM_PATCH_PROFILE=new-profile\\n" > .patched-app-state' > "$tmp_dir/update-apps.sh"
chmod +x "$tmp_dir/update-apps.sh"

printf '%s\n' \
  '#!/usr/bin/env bash' \
  'printf "%s\\n" "$@" > "$CURL_ARGS_FILE"' \
  '[[ " $* " == *" Authorization: Bearer matrix-test-token "* ]]' \
  '[[ " $* " == *" https://matrix.test/_matrix/client/v3/rooms/%21room%3Atest/send/m.room.message/"* ]]' \
  > "$tmp_dir/bin/curl"
chmod +x "$tmp_dir/bin/curl"

CURL_ARGS_FILE="$tmp_dir/curl-args" \
PATH="$tmp_dir/bin:$PATH" \
GRAMFORGE_CONFIG_FILE=/dev/null \
MATRIX_HOMESERVER='https://matrix.test' \
MATRIX_ROOM_ID='!room:test' \
MATRIX_ACCESS_TOKEN='matrix-test-token' \
APK_PUBLIC_DIR="$tmp_dir/public" \
APK_PUBLIC_URL='http://apks.test' \
"$tmp_dir/cron-update.sh"

grep -Fq 'GramForge APK ready' "$tmp_dir/curl-args"
grep -Fq 'http://apks.test/instagram-patched-2.0.0-e3b0c44298fc.apk' "$tmp_dir/curl-args"
test -f "$tmp_dir/public/instagram-patched-2.0.0-e3b0c44298fc.apk"
python3 - "$tmp_dir/curl-args" <<'PY'
import json
import pathlib
import sys

lines = pathlib.Path(sys.argv[1]).read_text().splitlines()
payload = next(json.loads(line) for line in lines if line.startswith('{'))
assert payload['body'] == 'GramForge APK ready\n\nDownload APK: http://apks.test/instagram-patched-2.0.0-e3b0c44298fc.apk'
PY
