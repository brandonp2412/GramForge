#!/usr/bin/env bash
# Regression test: byte-different rebuilds with the same APK payload must not notify.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

cp "$repo_dir/cron-update.sh" "$tmp_dir/cron-update.sh"
mkdir -p "$tmp_dir/lib" "$tmp_dir/bin" "$tmp_dir/apk" "$tmp_dir/public"
cp "$repo_dir/lib/config.sh" "$tmp_dir/lib/config.sh"
cp "$repo_dir/lib/matrix_notification.py" "$tmp_dir/lib/matrix_notification.py"
chmod +x "$tmp_dir/cron-update.sh"

printf 'INSTAGRAM_VERSION=2.0.0
INSTAGRAM_PATCH_PROFILE=old-profile
' > "$tmp_dir/.patched-app-state"
python3 - "$tmp_dir/apk/instagram-patched-2.0.0.apk" <<'PY'
import sys
import zipfile
with zipfile.ZipFile(sys.argv[1], 'w') as apk:
    apk.writestr('AndroidManifest.xml', b'v2')
    apk.writestr('classes.dex', b'dex-a')
    apk.writestr('classes2.dex', b'dex-b')
    apk.writestr('META-INF/MANIFEST.MF', b'old-signing-manifest')
    apk.writestr('META-INF/MORPHE.SF', b'old-signature')
PY
old_sha="$(sha256sum "$tmp_dir/apk/instagram-patched-2.0.0.apk" | awk '{print $1}')"

cat > "$tmp_dir/update-apps.sh" <<'EOF'
#!/usr/bin/env bash
python3 - <<'PY'
import zipfile
with zipfile.ZipFile('apk/instagram-patched-2.0.0.apk', 'w') as apk:
    apk.writestr('classes.dex', b'dex-b')
    apk.writestr('classes2.dex', b'dex-a')
    apk.writestr('AndroidManifest.xml', b'v2')
    apk.writestr('META-INF/MANIFEST.MF', b'new-signing-manifest')
    apk.writestr('META-INF/MORPHE.RSA', b'new-signature')
PY
printf 'INSTAGRAM_VERSION=2.0.0
INSTAGRAM_PATCH_PROFILE=new-profile
' > .patched-app-state
EOF
chmod +x "$tmp_dir/update-apps.sh"

cat > "$tmp_dir/bin/curl" <<'EOF'
#!/usr/bin/env bash
: > "$CURL_CALLED"
exit 0
EOF
chmod +x "$tmp_dir/bin/curl"

CURL_CALLED="$tmp_dir/curl-called" PATH="$tmp_dir/bin:$PATH" GRAMFORGE_CONFIG_FILE=/dev/null MATRIX_HOMESERVER=https://matrix.test MATRIX_ROOM_ID='!room:test' MATRIX_ACCESS_TOKEN=matrix-test-token APK_PUBLIC_DIR="$tmp_dir/public" APK_PUBLIC_URL=http://apks.test "$tmp_dir/cron-update.sh"

new_sha="$(sha256sum "$tmp_dir/apk/instagram-patched-2.0.0.apk" | awk '{print $1}')"
[[ "$new_sha" != "$old_sha" ]]
test ! -e "$tmp_dir/curl-called"
test -z "$(find "$tmp_dir/public" -maxdepth 1 -type f -print -quit)"
checkpoint="$(<"$tmp_dir/.cron-notify-state")"
[[ "$checkpoint" == payload-v1:* ]]
