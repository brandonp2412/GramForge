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
printf '%s\n' "$*" >>"$CURL_ARGS_FILE"
# First send fails; repeat failure must retry without acknowledging it.
if [[ "$count" -eq 0 ]]; then exit 22; fi
exit 0
EOF
chmod +x "$tmp_dir/cron-update.sh" "$tmp_dir/update-apps.sh" "$tmp_dir/bin/curl"
common=(
  GRAMFORGE_CONFIG_FILE=/dev/null
  MATRIX_HOMESERVER=https://matrix.test
  MATRIX_ROOM_ID='!room:test'
  MATRIX_ACCESS_TOKEN=test-token
  CURL_COUNT_FILE="$tmp_dir/count"
  CURL_ARGS_FILE="$tmp_dir/curl-args"
  PATH="$tmp_dir/bin:$PATH"
)
if env "${common[@]}" "$tmp_dir/cron-update.sh"; then
  echo "Unexpected updater success" >&2
  exit 1
fi
[[ ! -s "$tmp_dir/.cron-failure-state" ]]
if env "${common[@]}" "$tmp_dir/cron-update.sh"; then
  echo "Unexpected updater success" >&2
  exit 1
fi
grep -Fxq '2' "$tmp_dir/count"
grep -Fq 'GramForge patch needs coding work' "$tmp_dir/curl-args"
grep -Fq 'v456-0-0-53-78' "$tmp_dir/curl-args"
fingerprint_before="$(<"$tmp_dir/.cron-failure-state")"
# Same incompatibility should not generate another message.
if env "${common[@]}" "$tmp_dir/cron-update.sh"; then
  echo "Unexpected updater success" >&2
  exit 1
fi
grep -Fxq '2' "$tmp_dir/count"
printf 'FEUR_TAG=v457-0-0-00-00\nPATCHES_VERSION=v2.8.2\nCLI_VERSION=v2.3.0\n' >"$tmp_dir/.update-state"
if env "${common[@]}" "$tmp_dir/cron-update.sh"; then
  echo "Unexpected updater success" >&2
  exit 1
fi
grep -Fxq '3' "$tmp_dir/count"
[[ "$fingerprint_before" != "$(<"$tmp_dir/.cron-failure-state")" ]]
