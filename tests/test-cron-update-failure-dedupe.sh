#!/usr/bin/env bash
# Retried patch failures should notify only once for each upstream version.
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
cp "$repo_dir/cron-update.sh" "$tmp_dir/cron-update.sh"
mkdir -p "$tmp_dir/lib" "$tmp_dir/bin"
cp "$repo_dir/lib/config.sh" "$tmp_dir/lib/config.sh"
cp "$repo_dir/lib/matrix_notification.py" "$tmp_dir/lib/matrix_notification.py"
printf 'FEUR_TAG=v456-0-0-53-78\nPATCHES_VERSION=v2.8.2\nCLI_VERSION=v2.3.0\n' >"$tmp_dir/.update-state"
cat >"$tmp_dir/update-apps.sh" <<'EOF'
#!/usr/bin/env bash
echo "I: Extracting apk/.gramforge-v456.$RANDOM/decoded..."
echo "ERROR: expected exactly one Reels factory, found 0"
echo "ERROR: Reels patch verification failed; refusing unverified build."
exit 1
EOF
cat >"$tmp_dir/bin/curl" <<'EOF'
#!/usr/bin/env bash
count=0
[[ -f "$CURL_COUNT_FILE" ]] && count="$(<"$CURL_COUNT_FILE")"
printf '%s\n' "$((count + 1))" >"$CURL_COUNT_FILE"
exit 0
EOF
chmod +x "$tmp_dir/cron-update.sh" "$tmp_dir/update-apps.sh" "$tmp_dir/bin/curl"
common=(
  GRAMFORGE_CONFIG_FILE=/dev/null
  MATRIX_HOMESERVER=https://matrix.test
  MATRIX_ROOM_ID='!room:test'
  MATRIX_ACCESS_TOKEN=test-token
  CURL_COUNT_FILE="$tmp_dir/count"
  PATH="$tmp_dir/bin:$PATH"
)
for i in 1 2; do
  if env "${common[@]}" "$tmp_dir/cron-update.sh"; then
    echo "Unexpected updater success" >&2
    exit 1
  fi
done
grep -Fxq '1' "$tmp_dir/count"
fingerprint_before="$(<"$tmp_dir/.cron-failure-state")"
printf 'FEUR_TAG=v457-0-0-00-00\nPATCHES_VERSION=v2.8.2\nCLI_VERSION=v2.3.0\n' >"$tmp_dir/.update-state"
if env "${common[@]}" "$tmp_dir/cron-update.sh"; then
  echo "Unexpected updater success" >&2
  exit 1
fi
grep -Fxq '2' "$tmp_dir/count"
[[ "$fingerprint_before" != "$(<"$tmp_dir/.cron-failure-state")" ]]
