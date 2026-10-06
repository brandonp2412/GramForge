#!/usr/bin/env bash
# Regression test: a transient Matrix send failure must be retried without repatching.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

cp "$repo_dir/cron-update.sh" "$tmp_dir/cron-update.sh"
mkdir -p "$tmp_dir/lib"
cp "$repo_dir/lib/config.sh" "$tmp_dir/lib/config.sh"
chmod +x "$tmp_dir/cron-update.sh"
mkdir -p "$tmp_dir/bin" "$tmp_dir/apk"
printf 'INSTAGRAM_VERSION=2.0.0\nINSTAGRAM_PATCH_PROFILE=old-profile\n' > "$tmp_dir/.patched-app-state"
python3 - "$tmp_dir/apk/instagram-patched-2.0.0.apk" <<'PY'
import sys
import zipfile
with zipfile.ZipFile(sys.argv[1], 'w') as apk:
    apk.writestr('AndroidManifest.xml', b'v2')
    apk.writestr('classes.dex', b'old-code')
PY

cat > "$tmp_dir/update-apps.sh" <<'EOF'
#!/usr/bin/env bash
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
  'count=0' \
  '[[ -f "$CURL_COUNT_FILE" ]] && count="$(<"$CURL_COUNT_FILE")"' \
  'count=$((count + 1))' \
  'printf "%s\\n" "$count" > "$CURL_COUNT_FILE"' \
  'if [[ "$count" -eq 1 ]]; then exit 22; fi' \
  'exit 0' \
  > "$tmp_dir/bin/curl"
chmod +x "$tmp_dir/bin/curl"

common_env=(
  GRAMFORGE_CONFIG_FILE=/dev/null
  MATRIX_HOMESERVER=https://matrix.test
  MATRIX_ROOM_ID='!room:test'
  MATRIX_ACCESS_TOKEN=matrix-test-token
  CURL_COUNT_FILE="$tmp_dir/curl-count"
  PATH="$tmp_dir/bin:$PATH"
)

set +e
env "${common_env[@]}" "$tmp_dir/cron-update.sh"
first_status=$?
set -e
[[ "$first_status" -ne 0 ]]
old_checkpoint="$(<"$tmp_dir/.cron-notify-state")"
[[ "$old_checkpoint" == payload-v1:* ]]

env "${common_env[@]}" "$tmp_dir/cron-update.sh"
grep -Fxq '2' "$tmp_dir/curl-count"
new_checkpoint="$(<"$tmp_dir/.cron-notify-state")"
[[ "$new_checkpoint" == payload-v1:* ]]
[[ "$new_checkpoint" != "$old_checkpoint" ]]
