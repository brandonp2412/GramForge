#!/usr/bin/env bash
# Loads shared GramForge runtime configuration.
# Default location:
#   ~/.config/gramforge/config.env

configured_file="${GRAMFORGE_CONFIG_FILE:-}"
default_config_file="$HOME/.config/gramforge/config.env"
GRAMFORGE_CONFIG_FILE="${configured_file:-$default_config_file}"

load_env_file() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  set -a
  # shellcheck disable=SC1090
  source "$file"
  set +a
}

if [[ -n "$configured_file" ]]; then
  load_env_file "$GRAMFORGE_CONFIG_FILE"
elif [[ -f "$default_config_file" ]]; then
  load_env_file "$default_config_file"
else
  # Existing deployments may keep notification and publishing settings split.
  load_env_file "$HOME/.config/gramforge/matrix.env"
  load_env_file "$HOME/.config/gramforge/publish.env"
fi

property_value() {
  local file="$1" key="$2"
  sed -n "s/^$key=//p" "$file" | tr -d '\r' | head -n 1
}

# Signing credentials are a bundle: never borrow a password/alias from a
# properties file that points at a different keystore.
configured_signing_properties="${GRAMFORGE_SIGNING_PROPERTIES:-}"
gramforge_signing_properties="$HOME/.config/gramforge/signing.properties"
fdroid_signing_properties="$HOME/.config/android-signing/fdroid.properties"
selected_signing_properties=""

if [[ -n "$configured_signing_properties" ]]; then
  [[ -f "$configured_signing_properties" ]] || {
    echo "Configured signing properties not found: $configured_signing_properties" >&2
    return 1 2>/dev/null || exit 1
  }
  selected_signing_properties="$configured_signing_properties"
else
  for candidate in "$gramforge_signing_properties" "$fdroid_signing_properties"; do
    [[ -f "$candidate" ]] || continue
    candidate_store="$(property_value "$candidate" storeFile)"
    if [[ -z "${GRAMFORGE_KEYSTORE:-}" || "$GRAMFORGE_KEYSTORE" == "$candidate_store" ]]; then
      selected_signing_properties="$candidate"
      break
    fi
  done
fi

if [[ -n "$selected_signing_properties" ]]; then
  property_store="$(property_value "$selected_signing_properties" storeFile)"
  if [[ -n "${GRAMFORGE_KEYSTORE:-}" && "$GRAMFORGE_KEYSTORE" != "$property_store" ]]; then
    echo "Signing properties point at a different keystore than GRAMFORGE_KEYSTORE." >&2
    return 1 2>/dev/null || exit 1
  fi
  : "${GRAMFORGE_KEYSTORE:=$property_store}"
  : "${GRAMFORGE_KEYSTORE_PASSWORD:=$(property_value "$selected_signing_properties" storePassword)}"
  : "${GRAMFORGE_KEY_ALIAS:=$(property_value "$selected_signing_properties" keyAlias)}"
  : "${GRAMFORGE_KEY_PASSWORD:=$(property_value "$selected_signing_properties" keyPassword)}"
  GRAMFORGE_SIGNING_PROPERTIES="$selected_signing_properties"
else
  : "${GRAMFORGE_KEYSTORE:=$HOME/.config/gramforge/signing.keystore}"
  : "${GRAMFORGE_KEYSTORE_PASSWORD:=}"
  : "${GRAMFORGE_KEY_ALIAS:=Morphe}"
  : "${GRAMFORGE_KEY_PASSWORD:=}"
  GRAMFORGE_SIGNING_PROPERTIES=""
fi

: "${HIDE_HOME:=true}"
: "${HIDE_REELS:=false}"
: "${HIDE_DIRECT:=false}"
: "${HIDE_SEARCH:=false}"
: "${HIDE_PROFILE:=false}"
: "${HIDE_CREATE:=false}"

export GRAMFORGE_CONFIG_FILE GRAMFORGE_SIGNING_PROPERTIES
export GRAMFORGE_KEYSTORE GRAMFORGE_KEYSTORE_PASSWORD GRAMFORGE_KEY_ALIAS GRAMFORGE_KEY_PASSWORD
export HIDE_HOME HIDE_REELS HIDE_DIRECT HIDE_SEARCH HIDE_PROFILE HIDE_CREATE
