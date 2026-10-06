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
python3 - "$tmp_dir/apk/instagram-patched-2.0.0.apk" <<'PY'
import sys
import zipfile
with zipfile.ZipFile(sys.argv[1], 'w') as apk:
    apk.writestr('AndroidManifest.xml', b'v2')
    apk.writestr('classes.dex', b'old-code')
PY

# A real patch-profile payload change on the same Instagram version must republish.
cat > "$tmp_dir/update-apps.sh" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$JAVA_TOOL_OPTIONS" > "$JAVA_TMP_OPTS_FILE"
python3 - <<'PY'
import zipfile
with zipfile.ZipFile('apk/instagram-patched-2.0.0.apk', 'w') as apk:
    apk.writestr('AndroidManifest.xml', b'v2')
    apk.writestr('classes.dex', b'new-code')
PY
printf 'INSTAGRAM_VERSION=2.0.0\nINSTAGRAM_PATCH_PROFILE=new-profile\n' > .patched-app-state
EOF
chmod +x "$tmp_dir/update-apps.sh"

printf '%s\n' \
  '#!/usr/bin/env bash' \
  'printf "%s\\n" "$@" > "$CURL_ARGS_FILE"' \
  '[[ " $* " == *" Authorization: Bearer matrix-test-token "* ]]' \
  '[[ " $* " == *" https://matrix.test/_matrix/client/v3/rooms/%21room%3Atest/send/m.room.message/"* ]]' \
  > "$tmp_dir/bin/curl"
chmod +x "$tmp_dir/bin/curl"

CURL_ARGS_FILE="$tmp_dir/curl-args" \
JAVA_TMP_OPTS_FILE="$tmp_dir/java-tool-options" \
PATH="$tmp_dir/bin:$PATH" \
GRAMFORGE_CONFIG_FILE=/dev/null \
MATRIX_HOMESERVER='https://matrix.test' \
MATRIX_ROOM_ID='!room:test' \
MATRIX_ACCESS_TOKEN='matrix-test-token' \
APK_PUBLIC_DIR="$tmp_dir/public" \
APK_PUBLIC_URL='http://apks.test' \
"$tmp_dir/cron-update.sh"

test -d "$tmp_dir/.tools/java-tmp"
grep -Fq -- "-Djava.io.tmpdir=$tmp_dir/.tools/java-tmp" "$tmp_dir/java-tool-options"
grep -Fq 'GramForge APK ready' "$tmp_dir/curl-args"
published_name="$(find "$tmp_dir/public" -maxdepth 1 -type f -name 'instagram-patched-2.0.0-*.apk' -printf '%f\n')"
[[ -n "$published_name" ]]
expected_url="http://apks.test/$published_name"
grep -Fq "$expected_url" "$tmp_dir/curl-args"
test -f "$tmp_dir/public/$published_name"
python3 - "$tmp_dir/curl-args" "$expected_url" <<'PY'
import json
import pathlib
import sys

lines = pathlib.Path(sys.argv[1]).read_text().splitlines()
payload = next(json.loads(line) for line in lines if line.startswith('{'))
assert payload['body'] == f'GramForge APK ready\n\nDownload APK: {sys.argv[2]}'
PY
