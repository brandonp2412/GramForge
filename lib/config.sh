#!/usr/bin/env bash
# Shared GramForge runtime configuration loader.
#
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

fdroid_signing_properties="$HOME/.config/android-signing/fdroid.properties"
if [[ -f "$fdroid_signing_properties" ]]; then
  property_value() {
    sed -n "s/^$1=//p" "$fdroid_signing_properties" | tr -d '\r' | head -n 1
  }
  : "${GRAMFORGE_KEYSTORE:=$(property_value storeFile)}"
  : "${GRAMFORGE_KEYSTORE_PASSWORD:=$(property_value storePassword)}"
  : "${GRAMFORGE_KEY_ALIAS:=$(property_value keyAlias)}"
  : "${GRAMFORGE_KEY_PASSWORD:=$(property_value keyPassword)}"
else
  : "${GRAMFORGE_KEYSTORE:=$HOME/.config/gramforge/signing.keystore}"
  : "${GRAMFORGE_KEYSTORE_PASSWORD:=}"
  : "${GRAMFORGE_KEY_ALIAS:=Morphe}"
  : "${GRAMFORGE_KEY_PASSWORD:=}"
fi
: "${HIDE_HOME:=true}"
: "${HIDE_REELS:=false}"
: "${HIDE_DIRECT:=false}"
: "${HIDE_SEARCH:=false}"
: "${HIDE_PROFILE:=false}"
: "${HIDE_CREATE:=false}"

export GRAMFORGE_CONFIG_FILE GRAMFORGE_KEYSTORE GRAMFORGE_KEYSTORE_PASSWORD
export GRAMFORGE_KEY_ALIAS GRAMFORGE_KEY_PASSWORD
export HIDE_HOME HIDE_REELS HIDE_DIRECT HIDE_SEARCH HIDE_PROFILE HIDE_CREATE
