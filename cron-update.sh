#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

JAVA_TMP_DIR="${GRAMFORGE_JAVA_TMPDIR:-$PWD/.tools/java-tmp}"
mkdir -p "$JAVA_TMP_DIR"
export JAVA_TOOL_OPTIONS="-Djava.io.tmpdir=$JAVA_TMP_DIR${JAVA_TOOL_OPTIONS:+ $JAVA_TOOL_OPTIONS}"

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

apk_payload_fingerprint() {
  local apk="$1"
  [[ -f "$apk" ]] || return 1
  python3 - "$apk" <<'PY'
import hashlib
import re
import sys
import zipfile

path = sys.argv[1]

def content_hash(archive, info):
    digest = hashlib.sha256()
    with archive.open(info) as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()

rows = []
dex_payloads = []
with zipfile.ZipFile(path) as archive:
    for info in archive.infolist():
        if info.is_dir():
            continue
        name = info.filename
        upper = name.upper()
        if upper.startswith("META-INF/") and (
            upper == "META-INF/MANIFEST.MF"
            or upper.endswith((".SF", ".RSA", ".DSA", ".EC"))
        ):
            continue
        digest = content_hash(archive, info)
        if re.fullmatch(r"classes(?:\d+)?\.dex", name):
            dex_payloads.append((digest, info.file_size))
        else:
            rows.append((name, info.file_size, digest))

for digest, size in sorted(dex_payloads):
    rows.append(("<dex>", size, digest))

canonical = hashlib.sha256()
for name, size, digest in sorted(rows):
    canonical.update(name.encode("utf-8"))
    canonical.update(b"\0")
    canonical.update(str(size).encode("ascii"))
    canonical.update(b"\0")
    canonical.update(digest.encode("ascii"))
    canonical.update(b"\n")
print(canonical.hexdigest())
PY
}

LOG_FILE=".cron-update.log"
FAILURE_STATE=".cron-failure-state"
NOTIFY_STATE=".cron-notify-state"
before_version="$(awk -F= '$1 == "INSTAGRAM_VERSION" { print $2 }' .patched-app-state 2>/dev/null || true)"
before_payload=""
if [[ -n "$before_version" && -f "apk/instagram-patched-$before_version.apk" ]]; then
  before_payload="$(apk_payload_fingerprint "apk/instagram-patched-$before_version.apk")"
fi

# Migrate the old version/profile checkpoint to a canonical APK payload fingerprint.
# This deliberately ignores signing metadata, ZIP layout, and classesN.dex numbering,
# so toolchain-only rebuilds do not masquerade as app updates.
notified="$(cat "$NOTIFY_STATE" 2>/dev/null || true)"
if [[ "$notified" != payload-v1:* && -n "$before_payload" ]]; then
  notified="payload-v1:$before_payload"
  printf '%s\n' "$notified" >"$NOTIFY_STATE"
fi

if ! ./update-apps.sh >"$LOG_FILE" 2>&1; then
  handle_update_failure
  exit 1
fi

after_version="$(awk -F= '$1 == "INSTAGRAM_VERSION" { print $2 }' .patched-app-state 2>/dev/null || true)"
[[ -n "$after_version" ]] || { printf 'Patched Instagram version is missing after update.\n' >&2; exit 1; }
apk="apk/instagram-patched-$after_version.apk"
[[ -f "$apk" ]] || { printf 'Expected patched APK not found: %s\n' "$apk" >&2; exit 1; }
after_payload="$(apk_payload_fingerprint "$apk")"
after="payload-v1:$after_payload"
notified="$(cat "$NOTIFY_STATE" 2>/dev/null || true)"

if [[ "$after" != "$notified" ]]; then
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
