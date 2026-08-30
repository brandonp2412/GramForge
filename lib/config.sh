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

: "${GRAMFORGE_KEYSTORE:=$HOME/.config/gramforge/signing.keystore}"
: "${HIDE_HOME:=true}"
: "${HIDE_REELS:=false}"
: "${HIDE_DIRECT:=false}"
: "${HIDE_SEARCH:=false}"
: "${HIDE_PROFILE:=false}"
: "${HIDE_CREATE:=false}"

export GRAMFORGE_CONFIG_FILE GRAMFORGE_KEYSTORE
export HIDE_HOME HIDE_REELS HIDE_DIRECT HIDE_SEARCH HIDE_PROFILE HIDE_CREATE
