#!/usr/bin/env bash
# Keeps the Morphe CLI and Instagram patch bundle current.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

STATE_FILE=".update-state"
PATCHES_DIR="patches"
CLI_DIR="cli"

PATCHES_REPO="brosssh/morphe-patches"
CLI_REPO="MorpheApp/morphe-desktop"

patches_last="none"
patches_asset_last=""
cli_last="none"
cli_java="java"
if [[ -f "$STATE_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$STATE_FILE"
  patches_last="${PATCHES_VERSION:-none}"
  patches_asset_last="${PATCHES_ASSET:-}"
  cli_last="${CLI_VERSION:-none}"
  cli_java="${CLI_JAVA:-java}"
fi

save_state() {
  cat > "$STATE_FILE" <<EOF
PATCHES_VERSION=$patches_last
PATCHES_ASSET=$patches_asset_last
CLI_VERSION=$cli_last
CLI_JAVA=$cli_java
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

read -r patches_tag patches_asset patches_url <<< "$(gh_latest_asset "$PATCHES_REPO" '.mpp' | tr '\n' ' ')"
if [[ "$patches_tag" == "$patches_last" && -f "$PATCHES_DIR/$patches_asset" ]]; then
  printf 'Instagram Morphe patches: no update (%s).\n' "$patches_tag"
else
  printf 'Instagram Morphe patches: %s -> %s\n' "$patches_last" "$patches_tag"
  curl -sfL -o "$PATCHES_DIR/$patches_asset" "$patches_url"
  if [[ -n "$patches_asset_last" && "$patches_asset_last" != "$patches_asset" ]]; then
    rm -f "$PATCHES_DIR/$patches_asset_last"
  fi
  ln -sfn "$patches_asset" "$PATCHES_DIR/instagram.mpp"
  patches_last="$patches_tag"
  patches_asset_last="$patches_asset"
  patches_changed=1
fi

read -r cli_tag cli_asset cli_url <<< "$(gh_latest_asset "$CLI_REPO" '.jar' | tr '\n' ' ')"
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

save_state

if [[ "$patches_changed" == 0 && "$cli_changed" == 0 ]]; then
  exit 0
fi

printf '\nCurrent Instagram build recipe:\n'
printf '  %s -jar %s/morphe-cli.jar list-versions --patches %s/instagram.mpp -f com.instagram.android\n' "$cli_java" "$CLI_DIR" "$PATCHES_DIR"
printf '  Hide ads + Hide navigation buttons with hideHome=true (other navigation buttons retained).\n'
