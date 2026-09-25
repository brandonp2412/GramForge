#!/usr/bin/env bash
# Keeps the Morphe CLI/navigation patch and FeurStagram ad-blocking base current.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

STATE_FILE=".update-state"
PATCHES_DIR="patches"
CLI_DIR="cli"
FEUR_DIR=".tools/feurstagram"

PATCHES_REPO="brosssh/morphe-patches"
CLI_REPO="MorpheApp/morphe-desktop"
FEUR_REPO="jean-voila/FeurStagram"

mkdir -p "$PATCHES_DIR" "$CLI_DIR" "$FEUR_DIR"

state_value() {
  local key="$1"
  [[ -f "$STATE_FILE" ]] || return 0
  awk -F= -v key="$key" '$1 == key { print substr($0, length($1) + 2); exit }' "$STATE_FILE"
}

patches_last="$(state_value PATCHES_VERSION)"
patches_asset_last="$(state_value PATCHES_ASSET)"
cli_last="$(state_value CLI_VERSION)"
cli_java="$(state_value CLI_JAVA)"
feur_tag_last="$(state_value FEUR_TAG)"
feur_asset_last="$(state_value FEUR_ASSET)"
feur_digest_last="$(state_value FEUR_DIGEST)"
patches_last="${patches_last:-none}"
cli_last="${cli_last:-none}"
cli_java="${cli_java:-java}"
feur_tag_last="${feur_tag_last:-none}"

save_state() {
  cat > "$STATE_FILE" <<EOF
PATCHES_VERSION=$patches_last
PATCHES_ASSET=$patches_asset_last
CLI_VERSION=$cli_last
CLI_JAVA=$cli_java
FEUR_TAG=$feur_tag_last
FEUR_ASSET=$feur_asset_last
FEUR_DIGEST=$feur_digest_last
EOF
}

gh_latest_asset() {
  local repo="$1" extension="$2" json tag name url
  json="$(curl -sf "https://api.github.com/repos/$repo/releases/latest")"
  tag="$(jq -r '.tag_name // empty' <<<"$json")"
  name="$(jq -r --arg ext "$extension" '.assets[] | select(.name | endswith($ext)) | .name' <<<"$json" | head -n1)"
  url="$(jq -r --arg name "$name" '.assets[] | select(.name == $name) | .browser_download_url' <<<"$json")"
  [[ -n "$tag" && -n "$name" && -n "$url" ]] || return 1
  printf '%s\n%s\n%s\n' "$tag" "$name" "$url"
}

gh_latest_feur() {
  local json tag name url digest
  json="$(curl -sf "https://api.github.com/repos/$FEUR_REPO/releases/latest")"
  tag="$(jq -r '.tag_name // empty' <<<"$json")"
  name="$(jq -r '[.assets[] | select(.name | endswith(".apk")) | select(.name | endswith("-clone.apk") | not)][0].name // empty' <<<"$json")"
  url="$(jq -r --arg name "$name" '.assets[] | select(.name == $name) | .browser_download_url' <<<"$json")"
  digest="$(jq -r --arg name "$name" '.assets[] | select(.name == $name) | .digest // empty' <<<"$json")"
  [[ -n "$tag" && -n "$name" && -n "$url" ]] || return 1
  printf '%s\n%s\n%s\n%s\n' "$tag" "$name" "$url" "$digest"
}

verify_digest() {
  local file="$1" digest="$2"
  [[ -f "$file" ]] || return 1
  [[ -z "$digest" ]] && return 0
  [[ "$digest" == sha256:* ]] || { printf 'Unsupported GitHub asset digest: %s\n' "$digest" >&2; return 1; }
  [[ "$(sha256sum "$file" | awk '{print $1}')" == "${digest#sha256:}" ]]
}

if [[ -f "$CLI_DIR/morphe-cli.jar" ]] && ! "$cli_java" -jar "$CLI_DIR/morphe-cli.jar" --help >/dev/null 2>&1; then
  cli_java=""
  for candidate in java /usr/lib/jvm/*/bin/java; do
    command -v "$candidate" >/dev/null 2>&1 || continue
    if "$candidate" -jar "$CLI_DIR/morphe-cli.jar" --help >/dev/null 2>&1; then
      cli_java="$candidate"
      break
    fi
  done
  [[ -n "$cli_java" ]] || { printf 'No Java runtime can run %s\n' "$CLI_DIR/morphe-cli.jar" >&2; exit 1; }
fi

patches_changed=0
cli_changed=0
feur_changed=0

patches_release="$(gh_latest_asset "$PATCHES_REPO" '.mpp')"
mapfile -t patches_release_lines <<< "$patches_release"
patches_tag="${patches_release_lines[0]}"
patches_asset="${patches_release_lines[1]}"
patches_url="${patches_release_lines[2]}"
if [[ "$patches_tag" == "$patches_last" && -f "$PATCHES_DIR/$patches_asset" ]]; then
  printf 'Instagram Morphe navigation patches: no update (%s).\n' "$patches_tag"
else
  printf 'Instagram Morphe navigation patches: %s -> %s\n' "$patches_last" "$patches_tag"
  patch_tmp="$(mktemp "$PATCHES_DIR/.${patches_asset}.XXXXXX")"
  if ! curl -sfL -o "$patch_tmp" "$patches_url"; then
    rm -f "$patch_tmp"
    exit 1
  fi
  mv "$patch_tmp" "$PATCHES_DIR/$patches_asset"
  if [[ -n "$patches_asset_last" && "$patches_asset_last" != "$patches_asset" ]]; then
    rm -f "$PATCHES_DIR/$patches_asset_last"
  fi
  ln -sfn "$patches_asset" "$PATCHES_DIR/instagram.mpp"
  patches_last="$patches_tag"
  patches_asset_last="$patches_asset"
  patches_changed=1
fi

cli_release="$(gh_latest_asset "$CLI_REPO" '.jar')"
mapfile -t cli_release_lines <<< "$cli_release"
cli_tag="${cli_release_lines[0]}"
cli_asset="${cli_release_lines[1]}"
cli_url="${cli_release_lines[2]}"
if [[ "$cli_tag" == "$cli_last" && -f "$CLI_DIR/morphe-cli.jar" ]]; then
  printf 'Morphe CLI: no update (%s).\n' "$cli_tag"
else
  printf 'Morphe CLI: %s -> %s\n' "$cli_last" "$cli_tag"
  tmp="$(mktemp)"
  curl -sfL -o "$tmp" "$cli_url"
  working_java=""
  for candidate in java /usr/lib/jvm/*/bin/java; do
    command -v "$candidate" >/dev/null 2>&1 || continue
    if "$candidate" -jar "$tmp" --help >/dev/null 2>&1; then
      working_java="$candidate"
      break
    fi
  done
  if [[ -z "$working_java" ]]; then
    printf 'Downloaded %s but no available Java runtime can run it; keeping the existing CLI.\n' "$cli_asset" >&2
    rm -f "$tmp"
  else
    find "$CLI_DIR" -maxdepth 1 -name '*.jar' ! -name "$cli_asset" -delete
    mv "$tmp" "$CLI_DIR/$cli_asset"
    ln -sfn "$cli_asset" "$CLI_DIR/morphe-cli.jar"
    cli_last="$cli_tag"
    cli_java="$working_java"
    cli_changed=1
  fi
fi

feur_release="$(gh_latest_feur)"
mapfile -t feur_release_lines <<< "$feur_release"
feur_tag="${feur_release_lines[0]}"
feur_asset="${feur_release_lines[1]}"
feur_url="${feur_release_lines[2]}"
feur_digest="${feur_release_lines[3]:-}"
feur_target="$FEUR_DIR/$feur_asset"
if [[ "$feur_tag" == "$feur_tag_last" && "$feur_asset" == "$feur_asset_last" && "$feur_digest" == "$feur_digest_last" ]] && verify_digest "$feur_target" "$feur_digest"; then
  printf 'FeurStagram ad-blocking base: no update (%s).\n' "$feur_tag"
else
  printf 'FeurStagram ad-blocking base: %s -> %s\n' "$feur_tag_last" "$feur_tag"
  feur_tmp="$(mktemp "$FEUR_DIR/.${feur_asset}.XXXXXX")"
  if ! curl -sfL -o "$feur_tmp" "$feur_url"; then
    rm -f "$feur_tmp"
    exit 1
  fi
  if ! verify_digest "$feur_tmp" "$feur_digest"; then
    rm -f "$feur_tmp"
    printf 'FeurStagram asset digest verification failed.\n' >&2
    exit 1
  fi
  mv "$feur_tmp" "$feur_target"
  if [[ -n "$feur_asset_last" && "$feur_asset_last" != "$feur_asset" ]]; then
    rm -f "$FEUR_DIR/$feur_asset_last"
  fi
  feur_tag_last="$feur_tag"
  feur_asset_last="$feur_asset"
  feur_digest_last="$feur_digest"
  feur_changed=1
fi

save_state

if [[ "$patches_changed" == 0 && "$cli_changed" == 0 && "$feur_changed" == 0 ]]; then
  exit 0
fi

printf '\nCurrent Instagram build recipe:\n'
printf '  FeurStagram %s provides current open-source ad filtering.\n' "$feur_tag_last"
printf '  %s -jar %s/morphe-cli.jar applies the GramForge navigation profile.\n' "$cli_java" "$CLI_DIR"
