#!/usr/bin/env bash
# Patches a newly supported Instagram release when one is available.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
# shellcheck source=lib/config.sh
source lib/config.sh

STATE_FILE=".patched-app-state"
mkdir -p apk

die() { echo "ERROR: $*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"; }
need jq
need curl
need unzip
need python3
[[ -f APKEditor.jar ]] || die "APKEditor.jar is missing from the repo root."

case "${1:-instagram}" in
  instagram) ;;
  *) die "Usage: $0 [instagram]" ;;
esac

./check-instagram-update.sh
JAVA_BIN="$(awk -F= '/^CLI_JAVA=/{print $2}' .update-state)"
if [[ "$JAVA_BIN" == */* ]]; then
  [[ -x "$JAVA_BIN" ]] || die "The Java runtime recorded in .update-state is unavailable: $JAVA_BIN"
else
  JAVA_BIN="$(command -v "$JAVA_BIN")" || die "The Java runtime recorded in .update-state is unavailable: $JAVA_BIN"
fi

state_get() {
  local key="$1"
  [[ -f "$STATE_FILE" ]] || return 0
  awk -F= -v key="$key" '$1 == key { print $2 }' "$STATE_FILE"
}

state_set() {
  local key="$1" value="$2" tmp
  tmp="$(mktemp)"
  if [[ -f "$STATE_FILE" ]]; then
    awk -F= -v key="$key" '$1 != key' "$STATE_FILE" > "$tmp"
  fi
  printf '%s=%s\n' "$key" "$value" >> "$tmp"
  mv "$tmp" "$STATE_FILE"
}

instagram_version() {
  "$JAVA_BIN" -jar cli/morphe-cli.jar list-versions \
    --patches patches/instagram.mpp -f com.instagram.android 2>&1 |
    sed -n '/Most common compatible versions:/{n;s/^[[:space:]]*//;s/ .*//;p;q;}'
}

download_instagram_bundle() {
  local version="$1" target="apk/instagram-$1.xapk"
  local tmp_dir apkeep_bin downloaded manifest package_name version_name

  [[ -x tools/ensure-apkeep.sh ]] || die "tools/ensure-apkeep.sh is missing or not executable."
  apkeep_bin="$(./tools/ensure-apkeep.sh)"
  tmp_dir="$(mktemp -d "apk/.instagram-$version.XXXXXX")"

  echo "Downloading Instagram $version arm64-v8a with apkeep..."
  if ! "$apkeep_bin" -a "com.instagram.android@$version" -d apk-pure -o 'arch=arm64-v8a' "$tmp_dir"; then
    rm -rf "$tmp_dir"
    die "Could not automatically download Instagram $version with apkeep."
  fi

  downloaded="$(find "$tmp_dir" -maxdepth 1 -type f \( -name '*.xapk' -o -name '*.apkm' \) -print -quit)"
  [[ -n "$downloaded" && -f "$downloaded" ]] || {
    rm -rf "$tmp_dir"
    die "apkeep completed without producing an Instagram bundle."
  }

  manifest="$(unzip -p "$downloaded" manifest.json 2>/dev/null || true)"
  [[ -n "$manifest" ]] || {
    rm -rf "$tmp_dir"
    die "Downloaded Instagram bundle has no manifest.json."
  }
  package_name="$(jq -r '.package_name // .package // empty' <<<"$manifest")"
  version_name="$(jq -r '.version_name // .versionName // empty' <<<"$manifest")"
  [[ "$package_name" == "com.instagram.android" ]] || {
    rm -rf "$tmp_dir"
    die "Downloaded bundle package is $package_name, expected com.instagram.android."
  }
  [[ "$version_name" == "$version" ]] || {
    rm -rf "$tmp_dir"
    die "Downloaded bundle version is $version_name, expected $version."
  }
  if ! python3 - "$downloaded" <<'PY'
import io
import sys
import zipfile

with zipfile.ZipFile(sys.argv[1]) as outer:
    base_name = next((name for name in outer.namelist() if name == 'com.instagram.android.apk' or name.endswith('/com.instagram.android.apk')), None)
    if base_name is None:
        raise SystemExit(1)
    base = outer.read(base_name)
with zipfile.ZipFile(io.BytesIO(base)) as apk:
    raise SystemExit(0 if any(name.startswith('lib/arm64-v8a/') for name in apk.namelist()) else 1)
PY
  then
    rm -rf "$tmp_dir"
    die "Downloaded Instagram bundle does not contain arm64-v8a native libraries."
  fi

  mv "$downloaded" "$target"
  rm -rf "$tmp_dir"
  echo "Downloaded and verified Instagram bundle: $target"
}

patch_instagram() {
  local version input output previous previous_profile source downloaded
  local patches_version cli_version patch_profile
  patches_version="$(awk -F= '/^PATCHES_VERSION=/{print $2}' .update-state)"
  cli_version="$(awk -F= '/^CLI_VERSION=/{print $2}' .update-state)"
  patch_profile="brosssh-${patches_version:-unknown}-${cli_version:-unknown}-ads-nav-${HIDE_HOME}-${HIDE_REELS}-${HIDE_DIRECT}-${HIDE_SEARCH}-${HIDE_PROFILE}-${HIDE_CREATE}-v1"
  version="$(instagram_version)"
  [[ -n "$version" ]] || die "Could not determine the supported Instagram version."
  input="apk/instagram-${version}-arm64.apk"
  output="apk/instagram-patched-${version}.apk"
  previous="$(state_get INSTAGRAM_VERSION)"
  previous_profile="$(state_get INSTAGRAM_PATCH_PROFILE)"
  if [[ "$previous" == "$version" && "$previous_profile" == "$patch_profile" ]]; then
    echo "instagram: already patched $version ($patch_profile)"
    return
  fi

  echo "instagram: ${previous:-never patched}/${previous_profile:-no profile} -> $version/$patch_profile"
  source=""
  for candidate in "apk/instagram-$version.apkm" "apk/instagram-$version.xapk"; do
    [[ -f "$candidate" ]] && source="$candidate" && break
  done
  if [[ -z "$source" ]]; then
    while IFS= read -r info; do
      if [[ "$(jq -r '.release_version // empty' "$info")" == "$version" ]]; then
        source="$(dirname "$info")"
        break
      fi
    done < <(find apk -mindepth 2 -maxdepth 2 -name info.json -type f)
  fi
  if [[ -z "$source" ]]; then
    download_instagram_bundle "$version"
    source="apk/instagram-$version.xapk"
  fi
  downloaded="$source"
  echo "Using compatible Instagram bundle: $downloaded"
  echo "Merging APK splits..."
  if ! "$JAVA_BIN" -jar APKEditor.jar m -f -i "$downloaded" -o "$input"; then
    die "Could not merge Instagram $version."
  fi
  [[ -f "$GRAMFORGE_KEYSTORE" ]] || die "Signing keystore not found: $GRAMFORGE_KEYSTORE"
  echo "Applying GramForge profile with Morphe: Hide ads + configured navigation tabs"
  if ! "$JAVA_BIN" -jar cli/morphe-cli.jar patch "$input" \
      -p patches/instagram.mpp \
      -e "Hide ads" \
      -e "Hide navigation buttons" \
      -O hideHome="$HIDE_HOME" \
      -O hideReels="$HIDE_REELS" \
      -O hideDirect="$HIDE_DIRECT" \
      -O hideSearch="$HIDE_SEARCH" \
      -O hideProfile="$HIDE_PROFILE" \
      -O hideCreate="$HIDE_CREATE" \
      --bytecode-mode STRIP_FAST \
      --exclusive \
      -o "$output" --keystore "$GRAMFORGE_KEYSTORE"; then
    die "Patching failed; INSTAGRAM_VERSION was not updated."
  fi
  state_set INSTAGRAM_VERSION "$version"
  state_set INSTAGRAM_PATCH_PROFILE "$patch_profile"
  echo "instagram: created $output"
}

patch_instagram
