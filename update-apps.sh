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
need flock
[[ -f APKEditor.jar ]] || die "APKEditor.jar is missing from the repo root."

exec 9> .gramforge-update.lock
flock 9

case "${1:-instagram}" in
  instagram) ;;
  *) die "Usage: $0 [instagram]" ;;
esac

if [[ "${GRAMFORGE_SKIP_UPDATE_CHECK:-false}" != "true" ]]; then
  ./check-instagram-update.sh
else
  [[ -f .update-state ]] || { echo "ERROR: pinned update state missing." >&2; exit 1; }
fi
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
  local report="$1" version="$2"
  jq -e --arg version "$version" '
    (.stepResults // .patchingSteps) as $steps
    | .packageName == "com.instagram.android"
      and .packageVersion == $version
      and (.success == null or .success == true)
      and ($steps | type == "array")
      and ([$steps[]? | select(.success != true)] | length == 0)
      and (["PATCHING", "REBUILDING", "SIGNING"] - [$steps[]?.step] | length == 0)
      and (.failedPatches == [])
      and (.appliedPatches |
        if type == "array" then
          map(if type == "string" then . elif type == "object" then .name else null end)
          == ["Hide navigation buttons"]
        else false end)
  ' "$report" >/dev/null
}

patch_instagram() {
  local feur_tag feur_asset feur_base version package_name
  local patches_version cli_version icon_fingerprint reels_patch_fingerprint patch_profile legacy_profile_prefix legacy_profile_suffix legacy_body legacy_cli_version output previous previous_profile
  local apktool profile_patcher reels_patcher not_interested_patcher notification_patcher comment_patcher icon_patcher normalizer tmp_dir framework_dir decoded rebuilt normalized normalized_cache report

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

  icon_fingerprint="$(python3 tools/patch-launcher-icon.py --fingerprint assets/rotta-launcher)"
  reels_patch_fingerprint="$(sha256sum tools/patch-reels-actions.py tools/patch-reels-not-interested.py tools/patch-notification-nudges.py tools/patch-comment-filter.py tools/patch-message-requests-link.py | cut -d' ' -f1 | sha256sum | cut -c1-16)"
  patch_profile="feur-$feur_tag-brosssh-${patches_version:-unknown}-ads-nav-$HIDE_HOME-$HIDE_REELS-$HIDE_DIRECT-$HIDE_SEARCH-$HIDE_PROFILE-$HIDE_CREATE-v5-rotta-$icon_fingerprint-reels-$reels_patch_fingerprint"
  legacy_profile_prefix="feur-$feur_tag-brosssh-${patches_version:-unknown}-"
  legacy_profile_suffix="-ads-nav-$HIDE_HOME-$HIDE_REELS-$HIDE_DIRECT-$HIDE_SEARCH-$HIDE_PROFILE-$HIDE_CREATE-v5-rotta-$icon_fingerprint-reels-$reels_patch_fingerprint"
  output="apk/instagram-patched-$version.apk"
  previous="$(state_get INSTAGRAM_VERSION)"
  previous_profile="$(state_get INSTAGRAM_PATCH_PROFILE)"

  if [[ "$previous" == "$version" && "$previous_profile" == "$patch_profile" && -f "$output" ]]; then
    echo "instagram: already patched $version ($patch_profile)"
    return
  fi

  if [[ "$previous" == "$version" && -f "$output" ]]; then
    legacy_body="${previous_profile#"$legacy_profile_prefix"}"
    legacy_cli_version="${legacy_body%"$legacy_profile_suffix"}"
    if [[ "$legacy_body" != "$previous_profile" && "$legacy_cli_version" != "$legacy_body" && "$legacy_cli_version" == v* ]]; then
      state_set INSTAGRAM_PATCH_PROFILE "$patch_profile"
      state_set INSTAGRAM_TOOLCHAIN_VERSION "$legacy_cli_version"
      echo "instagram: migrated legacy profile without rebuilding $version ($patch_profile)"
      return
    fi
  fi

  echo "instagram: ${previous:-never patched}/${previous_profile:-no profile} -> $version/$patch_profile"

  tmp_dir="$(mktemp -d "apk/.gramforge-$version.XXXXXX")"
  framework_dir="$tmp_dir/framework"
  mkdir -p "$framework_dir"
  report="$tmp_dir/nav-report.json"
  normalized_cache=".tools/feurstagram/gramforge-$feur_tag-profile-v5-home-$HIDE_HOME-rotta-$icon_fingerprint-reels-$reels_patch_fingerprint.apk"

  if [[ -f "$normalized_cache" ]] &&
      [[ "$(apk_info_value "$normalized_cache" package)" == "com.instagram.android" ]] &&
      [[ "$(apk_info_value "$normalized_cache" VersionName)" == "$version" ]]; then
    echo "Reusing normalized FeurStagram base: $normalized_cache"
  else
    rm -f "$normalized_cache"
    [[ -x tools/ensure-apktool.sh ]] || { rm -rf "$tmp_dir"; die "tools/ensure-apktool.sh is missing or not executable."; }
    apktool="$(./tools/ensure-apktool.sh)"
    profile_patcher="${GRAMFORGE_PROFILE_PATCHER:-tools/patch-feurstagram-profile.py}"
    reels_patcher="${GRAMFORGE_REELS_PATCHER:-tools/patch-reels-actions.py}"
    not_interested_patcher="${GRAMFORGE_NOT_INTERESTED_PATCHER:-tools/patch-reels-not-interested.py}"
    notification_patcher="${GRAMFORGE_NOTIFICATION_PATCHER:-tools/patch-notification-nudges.py}"
    comment_patcher="${GRAMFORGE_COMMENT_PATCHER:-tools/patch-comment-filter.py}"
    requests_patcher="${GRAMFORGE_REQUESTS_PATCHER:-tools/patch-message-requests-link.py}"
    icon_patcher="${GRAMFORGE_ICON_PATCHER:-tools/patch-launcher-icon.py}"
    normalizer="${GRAMFORGE_APK_NORMALIZER:-tools/normalize-apk.py}"
    [[ -f "$profile_patcher" ]] || { rm -rf "$tmp_dir"; die "Profile patcher not found: $profile_patcher"; }
    [[ -f "$reels_patcher" ]] || { rm -rf "$tmp_dir"; die "Reels action patcher not found: $reels_patcher"; }
    [[ -f "$not_interested_patcher" ]] || { rm -rf "$tmp_dir"; die "Reels Not interested patcher not found: $not_interested_patcher"; }
    [[ -f "$notification_patcher" ]] || { rm -rf "$tmp_dir"; die "Notification nudge patcher not found: $notification_patcher"; }
    [[ -f "$comment_patcher" ]] || { rm -rf "$tmp_dir"; die "Comment filter patcher not found: $comment_patcher"; }
    [[ -f "$requests_patcher" ]] || { rm -rf "$tmp_dir"; die "Requests link patcher not found: $requests_patcher"; }
    [[ -f "$icon_patcher" ]] || { rm -rf "$tmp_dir"; die "Launcher icon patcher not found: $icon_patcher"; }
    [[ -f "$normalizer" ]] || { rm -rf "$tmp_dir"; die "APK normalizer not found: $normalizer"; }

    decoded="$tmp_dir/decoded"
    rebuilt="$tmp_dir/feur-profile.apk"
    normalized="$tmp_dir/feur-profile-normalized.apk"

    echo "Normalizing FeurStagram to GramForge's ads-only runtime profile..."
    if ! "$JAVA_BIN" -jar "$apktool" d -f -p "$framework_dir" -o "$decoded" "$feur_base"; then
      rm -rf "$tmp_dir"
      die "Could not decode FeurStagram $feur_tag."
    fi
    if ! python3 "$profile_patcher" "$decoded"; then
      rm -rf "$tmp_dir"
      die "FeurStagram internals changed; refusing to build an unverified profile."
    fi
    if ! python3 "$reels_patcher" "$decoded"; then
      rm -rf "$tmp_dir"
      die "Instagram Reels changed; refusing to build without verified Save/Repost removal."
    fi
    if ! python3 "$not_interested_patcher" "$decoded"; then
      rm -rf "$tmp_dir"
      die "Instagram Reels changed; refusing to build without confirmed Not interested."
    fi
    if ! python3 "$notification_patcher" "$decoded"; then
      rm -rf "$tmp_dir"
      die "Notification prompt internals changed; refusing to build without nudge suppression."
    fi
    if ! python3 "$comment_patcher" "$decoded"; then
      rm -rf "$tmp_dir"
      die "Instagram comments changed; refusing to build without the comment filter."
    fi
    if ! python3 "$requests_patcher" "$decoded"; then
      rm -rf "$tmp_dir"
      die "Instagram Direct inbox changed; refusing to build without Requests link removal."
    fi
    if ! python3 "$icon_patcher" "$decoded" assets/rotta-launcher; then
      rm -rf "$tmp_dir"
      die "Instagram launcher resources changed; refusing to build without Rotta's icon."
    fi
    if ! "$JAVA_BIN" -jar "$apktool" b -p "$framework_dir" "$decoded" -o "$rebuilt"; then
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

  if ! verify_patch_report "$report" "$version"; then
    install -m 0600 "$report" .tools/last-invalid-nav-report.json
    rm -f "$output"
    rm -rf "$tmp_dir"
    die "Morphe report did not prove the expected navigation patch applied cleanly."
  fi

  rm -rf "$tmp_dir"
  state_set INSTAGRAM_VERSION "$version"
  state_set INSTAGRAM_PATCH_PROFILE "$patch_profile"
  state_set INSTAGRAM_TOOLCHAIN_VERSION "${cli_version:-unknown}"
  echo "instagram: created $output"
}

patch_instagram
