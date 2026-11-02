#!/usr/bin/env bash
# ADB-only delivery is safe, independent, and retries failed installations.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

cp "$repo_dir/cron-update.sh" "$tmp_dir/cron-update.sh"
mkdir -p "$tmp_dir/lib" "$tmp_dir/apk" "$tmp_dir/bin" "$tmp_dir/public"
cp "$repo_dir/lib/config.sh" "$tmp_dir/lib/config.sh"
cp "$repo_dir/lib/matrix_notification.py" "$tmp_dir/lib/matrix_notification.py"
printf '#!/usr/bin/env bash\nexit 0\n' > "$tmp_dir/update-apps.sh"
chmod +x "$tmp_dir/cron-update.sh" "$tmp_dir/update-apps.sh"

printf 'INSTAGRAM_VERSION=1.0\nINSTAGRAM_PATCH_PROFILE=test\n' > "$tmp_dir/.patched-app-state"
python3 - "$tmp_dir/apk/instagram-patched-1.0.apk" one <<'PY'
import sys
import zipfile
with zipfile.ZipFile(sys.argv[1], 'w') as apk:
    apk.writestr('AndroidManifest.xml', b'mock-manifest')
    apk.writestr('classes.dex', sys.argv[2].encode())
PY

cat > "$tmp_dir/bin/adb" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ "$1" == connect ]]; then exit 0; fi
[[ "$1" == -s && "$2" == test-device.example:5555 ]] || exit 91
shift 2
case "$1" in
  get-state)
    printf 'device\n'
    ;;
  shell)
    [[ "$2" == getprop && "$3" == ro.product.model ]] || exit 92
    printf '%s\n' "${MOCK_ADB_MODEL:-Mock Android Device}"
    ;;
  install)
    [[ "$2" == -r && -f "$3" ]] || exit 93
    printf 'install\n' >> "$MOCK_ADB_CALLS"
    [[ ! -f "$MOCK_ADB_FAIL" ]] || exit 94
    printf 'Success\n'
    ;;
  *)
    exit 95
    ;;
esac
EOF
cat > "$tmp_dir/bin/curl" <<'EOF'
#!/usr/bin/env bash
printf 'request\n' >> "$MOCK_MATRIX_CALLS"
exit 0
EOF
chmod +x "$tmp_dir/bin/adb" "$tmp_dir/bin/curl"

run_cron() {
  env \
    GRAMFORGE_CONFIG_FILE=/dev/null \
    GRAMFORGE_ADB_SERIAL=test-device.example:5555 \
    GRAMFORGE_ADB_EXPECTED_MODEL='Mock Android Device' \
    GRAMFORGE_ADB_ONLY=true \
    MOCK_ADB_CALLS="$tmp_dir/install-calls" \
    MOCK_ADB_FAIL="$tmp_dir/fail-install" \
    MOCK_MATRIX_CALLS="$tmp_dir/matrix-calls" \
    MOCK_ADB_MODEL="${MOCK_ADB_MODEL:-Mock Android Device}" \
    MATRIX_HOMESERVER=https://matrix.example.test \
    MATRIX_ROOM_ID='!room:example.test' \
    MATRIX_ACCESS_TOKEN=dummy \
    APK_PUBLIC_DIR="$tmp_dir/public" \
    APK_PUBLIC_URL=https://apk.example.test \
    PATH="$tmp_dir/bin:$PATH" \
    "$tmp_dir/cron-update.sh"
}

# First run installs the existing signed APK once, without publishing/notifying.
run_cron
[[ "$(wc -l < "$tmp_dir/install-calls")" -eq 1 ]]
[[ "$(< "$tmp_dir/.cron-adb-install-state")" == sha256:* ]]
[[ ! -e "$tmp_dir/matrix-calls" ]]
[[ -z "$(find "$tmp_dir/public" -type f -print -quit)" ]]
run_cron
[[ "$(wc -l < "$tmp_dir/install-calls")" -eq 1 ]]

# Payload changes trigger a new install. A failure must NOT advance state.
first_state="$(< "$tmp_dir/.cron-adb-install-state")"
python3 - "$tmp_dir/apk/instagram-patched-1.0.apk" two <<'PY'
import sys
import zipfile
with zipfile.ZipFile(sys.argv[1], 'w') as apk:
    apk.writestr('AndroidManifest.xml', b'mock-manifest')
    apk.writestr('classes.dex', sys.argv[2].encode())
PY
touch "$tmp_dir/fail-install"
if run_cron; then
  echo 'Expected install failure' >&2
  exit 1
fi
[[ "$(< "$tmp_dir/.cron-adb-install-state")" == "$first_state" ]]
[[ "$(wc -l < "$tmp_dir/install-calls")" -eq 2 ]]
[[ "$(wc -l < "$tmp_dir/matrix-calls")" -eq 1 ]]

rm "$tmp_dir/fail-install"
run_cron
[[ "$(wc -l < "$tmp_dir/install-calls")" -eq 3 ]]
[[ "$(< "$tmp_dir/.cron-adb-install-state")" != "$first_state" ]]
[[ "$(wc -l < "$tmp_dir/matrix-calls")" -eq 1 ]]

# Even with a configured serial, refuse a different model before install.
python3 - "$tmp_dir/apk/instagram-patched-1.0.apk" three <<'PY'
import sys
import zipfile
with zipfile.ZipFile(sys.argv[1], 'w') as apk:
    apk.writestr('AndroidManifest.xml', b'mock-manifest')
    apk.writestr('classes.dex', sys.argv[2].encode())
PY
MOCK_ADB_MODEL='Wrong Device' run_cron && exit 1
[[ "$(wc -l < "$tmp_dir/install-calls")" -eq 3 ]]
