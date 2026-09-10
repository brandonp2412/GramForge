#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
# shellcheck source=lib/config.sh
source lib/config.sh

matrix_enabled=false
if [[ -n "${MATRIX_HOMESERVER:-}${MATRIX_ROOM_ID:-}${MATRIX_ACCESS_TOKEN:-}" ]]; then
  : "${MATRIX_HOMESERVER:?MATRIX_HOMESERVER is required when Matrix notifications are enabled}"
  : "${MATRIX_ROOM_ID:?MATRIX_ROOM_ID is required when Matrix notifications are enabled}"
  : "${MATRIX_ACCESS_TOKEN:?MATRIX_ACCESS_TOKEN is required when Matrix notifications are enabled}"
  matrix_enabled=true
  matrix_room_path="$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$MATRIX_ROOM_ID")"
fi

publish_enabled=false
if [[ -n "${APK_PUBLIC_DIR:-}${APK_PUBLIC_URL:-}" ]]; then
  : "${APK_PUBLIC_DIR:?APK_PUBLIC_DIR is required when publishing is enabled}"
  : "${APK_PUBLIC_URL:?APK_PUBLIC_URL is required when publishing is enabled}"
  publish_enabled=true
fi

matrix_send() {
  [[ "$matrix_enabled" == true ]] || return 0
  local title=$1 message=$2
  local txn payload
  txn="gramforge-$(date +%s%N)-$RANDOM"
  payload="$(python3 -c 'import json, sys; print(json.dumps({"msgtype":"m.text","body":sys.argv[1] + "\n\n" + sys.argv[2]}, separators=(",",":")))' "$title" "$message")"
  curl -fsS -X PUT \
    -H "Authorization: Bearer $MATRIX_ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    --data-binary "$payload" \
    "$MATRIX_HOMESERVER/_matrix/client/v3/rooms/$matrix_room_path/send/m.room.message/$txn" >/dev/null
}

handle_update_failure() {
  local fingerprint previous message
  fingerprint="$(sha256sum "$LOG_FILE" | awk '{print $1}')"
  previous="$(cat "$FAILURE_STATE" 2>/dev/null || true)"
  if [[ "$fingerprint" != "$previous" ]]; then
    message="$(tail -n 8 "$LOG_FILE" | head -c 3000)"
    matrix_send "GramForge update needs attention" "$message" || true
    printf '%s\n' "$fingerprint" >"$FAILURE_STATE"
  fi
}

LOG_FILE=".cron-update.log"
FAILURE_STATE=".cron-failure-state"
NOTIFY_STATE=".cron-notify-state"
before_version="$(awk -F= '$1 == "INSTAGRAM_VERSION" { print $2 }' .patched-app-state 2>/dev/null || true)"
before_profile="$(awk -F= '$1 == "INSTAGRAM_PATCH_PROFILE" { print $2 }' .patched-app-state 2>/dev/null || true)"
before="$before_version|$before_profile"

# Seed the notification checkpoint from the already-patched state on upgrade so
# existing deployments do not re-announce their current APK. New patch/profile
# changes only advance this checkpoint after publishing and Matrix delivery both
# succeed, so transient notification failures are retried on the next run.
if [[ ! -f "$NOTIFY_STATE" ]]; then
  printf '%s\n' "$before" >"$NOTIFY_STATE"
fi

if ! ./update-apps.sh >"$LOG_FILE" 2>&1; then
  handle_update_failure
  exit 1
fi

after_version="$(awk -F= '$1 == "INSTAGRAM_VERSION" { print $2 }' .patched-app-state 2>/dev/null || true)"
after_profile="$(awk -F= '$1 == "INSTAGRAM_PATCH_PROFILE" { print $2 }' .patched-app-state 2>/dev/null || true)"
after="$after_version|$after_profile"
notified="$(cat "$NOTIFY_STATE" 2>/dev/null || true)"

if [[ -n "$after_version" && "$after" != "$notified" ]]; then
  apk="apk/instagram-patched-$after_version.apk"
  [[ -f "$apk" ]] || { printf 'Expected patched APK not found: %s\n' "$apk" >&2; exit 1; }

  message="GramForge Instagram build is ready."
  if [[ "$publish_enabled" == true ]]; then
    build_hash="$(sha256sum "$apk" | awk '{print substr($1, 1, 12)}')"
    published_name="instagram-patched-$after_version-$build_hash.apk"
    install -m 0644 "$apk" "$APK_PUBLIC_DIR/$published_name"
    message="Download APK: $APK_PUBLIC_URL/$published_name"
  fi

  matrix_send "GramForge APK ready" "$message"
  printf '%s\n' "$after" >"$NOTIFY_STATE"
fi

: >"$FAILURE_STATE"
