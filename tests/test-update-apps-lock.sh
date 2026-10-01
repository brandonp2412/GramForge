#!/usr/bin/env bash
# Regression test: concurrent updater invocations are serialized around shared state/artifacts.
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

cp "$repo_dir/update-apps.sh" "$tmp_dir/update-apps.sh"
mkdir -p "$tmp_dir/lib" "$tmp_dir/bin" "$tmp_dir/apk" "$tmp_dir/.tools/feurstagram"
cp "$repo_dir/lib/config.sh" "$tmp_dir/lib/config.sh"
chmod +x "$tmp_dir/update-apps.sh"
touch "$tmp_dir/APKEditor.jar" "$tmp_dir/test.keystore"
touch "$tmp_dir/.tools/feurstagram/feurstagram.apk"
touch "$tmp_dir/apk/instagram-patched-446.0.0.49.77.apk"

profile='feur-v446-0-0-49-77-brosssh-v2.8.2-v1.18.0-ads-nav-true-false-false-false-false-false-v2'
printf 'INSTAGRAM_VERSION=446.0.0.49.77\nINSTAGRAM_PATCH_PROFILE=%s\n' "$profile" > "$tmp_dir/.patched-app-state"

cat > "$tmp_dir/check-instagram-update.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if ! mkdir .update-entered 2>/dev/null; then
  : > .overlap-detected
  exit 70
fi
trap 'rmdir .update-entered' EXIT
sleep 0.5
cat > .update-state <<STATE
PATCHES_VERSION=v2.8.2
PATCHES_ASSET=patches-2.8.2.mpp
CLI_VERSION=v1.18.0
CLI_JAVA=java
FEUR_TAG=v446-0-0-49-77
FEUR_ASSET=feurstagram.apk
FEUR_DIGEST=
STATE
EOF
chmod +x "$tmp_dir/check-instagram-update.sh"

cat > "$tmp_dir/bin/java" <<'EOF'
#!/usr/bin/env bash
if [[ "$*" == *"APKEditor.jar info"* ]]; then
  printf 'package="com.instagram.android"\nVersionName="446.0.0.49.77"\n'
  exit 0
fi
exit 0
EOF
chmod +x "$tmp_dir/bin/java"

common_env=(
  GRAMFORGE_CONFIG_FILE=/dev/null
  GRAMFORGE_KEYSTORE="$tmp_dir/test.keystore"
  PATH="$tmp_dir/bin:$PATH"
)

env "${common_env[@]}" "$tmp_dir/update-apps.sh" > "$tmp_dir/first.out" 2>&1 &
first_pid=$!
sleep 0.1
env "${common_env[@]}" "$tmp_dir/update-apps.sh" > "$tmp_dir/second.out" 2>&1 &
second_pid=$!

wait "$first_pid"
wait "$second_pid"

test ! -e "$tmp_dir/.overlap-detected"
grep -Fqx "instagram: already patched 446.0.0.49.77 ($profile)" "$tmp_dir/first.out"
grep -Fqx "instagram: already patched 446.0.0.49.77 ($profile)" "$tmp_dir/second.out"
