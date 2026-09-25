#!/usr/bin/env bash
# Builds GramForge from the latest verified FeurStagram base plus our nav profile.
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
need python3
need sha256sum
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

update_state_get() {
  local key="$1"
  awk -F= -v key="$key" '$1 == key { print substr($0, length($1) + 2); exit }' .update-state
}

state_get() {
  local key="$1"
  [[ -f "$STATE_FILE" ]] || return 0
  awk -F= -v key="$key" '$1 == key { print substr($0, length($1) + 2); exit }' "$STATE_FILE"
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

apk_info_value() {
  local apk="$1" key="$2"
  "$JAVA_BIN" -jar APKEditor.jar info -i "$apk" 2>/dev/null |
    sed -n "s/^$key=\"\(.*\)\"$/\1/p" | head -n1
}

verify_patch_report() {
  local report="$1"
  jq -e '
    .packageName == "com.instagram.android"
    and ([.patchingSteps[] | select(.success != true)] | length == 0)
    and ([.failedPatches[]?] | length == 0)
    and ([.appliedPatches[]? | select(.name == "Hide navigation buttons")] | length == 1)
  ' "$report" >/dev/null
}

patch_instagram() {
  local feur_tag feur_asset feur_base version package_name
  local patches_version cli_version patch_profile output previous previous_profile
  local apktool profile_patcher normalizer tmp_dir decoded rebuilt normalized normalized_cache report

  feur_tag="$(update_state_get FEUR_TAG)"
  feur_asset="$(update_state_get FEUR_ASSET)"
  patches_version="$(update_state_get PATCHES_VERSION)"
  cli_version="$(update_state_get CLI_VERSION)"
  [[ -n "$feur_tag" && -n "$feur_asset" ]] || die "FeurStagram release state is incomplete."

  feur_base=".tools/feurstagram/$feur_asset"
  [[ -f "$feur_base" ]] || die "FeurStagram base APK is missing: $feur_base"

  package_name="$(apk_info_value "$feur_base" package)"
  version="$(apk_info_value "$feur_base" VersionName)"
  [[ "$package_name" == "com.instagram.android" ]] || die "FeurStagram base package is $package_name, expected com.instagram.android."
  [[ -n "$version" ]] || die "Could not read Instagram version from $feur_base."

  patch_profile="feur-$feur_tag-brosssh-${patches_version:-unknown}-${cli_version:-unknown}-ads-nav-$HIDE_HOME-$HIDE_REELS-$HIDE_DIRECT-$HIDE_SEARCH-$HIDE_PROFILE-$HIDE_CREATE-v2"
  output="apk/instagram-patched-$version.apk"
  previous="$(state_get INSTAGRAM_VERSION)"
  previous_profile="$(state_get INSTAGRAM_PATCH_PROFILE)"

  if [[ "$previous" == "$version" && "$previous_profile" == "$patch_profile" && -f "$output" ]]; then
    echo "instagram: already patched $version ($patch_profile)"
    return
  fi

  echo "instagram: ${previous:-never patched}/${previous_profile:-no profile} -> $version/$patch_profile"

  tmp_dir="$(mktemp -d "apk/.gramforge-$version.XXXXXX")"
  report="$tmp_dir/nav-report.json"
  normalized_cache=".tools/feurstagram/gramforge-$feur_tag-profile-v2.apk"

  if [[ -f "$normalized_cache" ]] &&
      [[ "$(apk_info_value "$normalized_cache" package)" == "com.instagram.android" ]] &&
      [[ "$(apk_info_value "$normalized_cache" VersionName)" == "$version" ]]; then
    echo "Reusing normalized FeurStagram base: $normalized_cache"
  else
    rm -f "$normalized_cache"
    [[ -x tools/ensure-apktool.sh ]] || { rm -rf "$tmp_dir"; die "tools/ensure-apktool.sh is missing or not executable."; }
    apktool="$(./tools/ensure-apktool.sh)"
    profile_patcher="${GRAMFORGE_PROFILE_PATCHER:-tools/patch-feurstagram-profile.py}"
    normalizer="${GRAMFORGE_APK_NORMALIZER:-tools/normalize-apk.py}"
    [[ -f "$profile_patcher" ]] || { rm -rf "$tmp_dir"; die "Profile patcher not found: $profile_patcher"; }
    [[ -f "$normalizer" ]] || { rm -rf "$tmp_dir"; die "APK normalizer not found: $normalizer"; }

    decoded="$tmp_dir/decoded"
    rebuilt="$tmp_dir/feur-profile.apk"
    normalized="$tmp_dir/feur-profile-normalized.apk"

    echo "Normalizing FeurStagram to GramForge's ads-only runtime profile..."
    if ! "$JAVA_BIN" -jar "$apktool" d -f -o "$decoded" "$feur_base"; then
      rm -rf "$tmp_dir"
      die "Could not decode FeurStagram $feur_tag."
    fi
    if ! python3 "$profile_patcher" "$decoded"; then
      rm -rf "$tmp_dir"
      die "FeurStagram internals changed; refusing to build an unverified profile."
    fi
    if ! "$JAVA_BIN" -jar "$apktool" b "$decoded" -o "$rebuilt"; then
      rm -rf "$tmp_dir"
      die "Could not rebuild the normalized FeurStagram APK."
    fi
    if ! python3 "$normalizer" "$rebuilt" "$normalized"; then
      rm -rf "$tmp_dir"
      die "Could not normalize rebuilt APK ZIP metadata."
    fi
    mv "$normalized" "$normalized_cache"
  fi

  [[ -f "$GRAMFORGE_KEYSTORE" ]] || { rm -rf "$tmp_dir"; die "Signing keystore not found: $GRAMFORGE_KEYSTORE"; }
  echo "Applying GramForge navigation profile with Morphe..."
  if ! "$JAVA_BIN" -jar cli/morphe-cli.jar patch "$normalized_cache"       -f       -p patches/instagram.mpp       -e "Hide navigation buttons"       -O hideHome="$HIDE_HOME"       -O hideReels="$HIDE_REELS"       -O hideDirect="$HIDE_DIRECT"       -O hideSearch="$HIDE_SEARCH"       -O hideProfile="$HIDE_PROFILE"       -O hideCreate="$HIDE_CREATE"       --bytecode-mode STRIP_FAST       --exclusive       -r "$report"       -o "$output"       --keystore "$GRAMFORGE_KEYSTORE"       --keystore-password "$GRAMFORGE_KEYSTORE_PASSWORD"       --keystore-entry-alias "$GRAMFORGE_KEY_ALIAS"       --keystore-entry-password "$GRAMFORGE_KEY_PASSWORD"; then
    rm -rf "$tmp_dir"
    die "Navigation patching/signing failed; installed-state metadata was not updated."
  fi

  if ! verify_patch_report "$report"; then
    rm -f "$output"
    rm -rf "$tmp_dir"
    die "Morphe report did not prove the expected navigation patch applied cleanly."
  fi

  rm -rf "$tmp_dir"
  state_set INSTAGRAM_VERSION "$version"
  state_set INSTAGRAM_PATCH_PROFILE "$patch_profile"
  echo "instagram: created $output"
}

patch_instagram
