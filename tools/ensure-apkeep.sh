#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tools_dir="$repo_dir/.tools"
apkeep_bin="${GRAMFORGE_APKEEP_BIN:-$tools_dir/apkeep}"
version="1.0.0"
base_url="https://github.com/EFForg/apkeep/releases/download/$version"

if [[ -x "$apkeep_bin" ]]; then
  "$apkeep_bin" --version | grep -Fqx "apkeep $version" || {
    printf 'Existing apkeep has unexpected version: %s\n' "$apkeep_bin" >&2
    exit 1
  }
  printf '%s\n' "$apkeep_bin"
  exit 0
fi

case "$(uname -s):$(uname -m)" in
  Linux:x86_64)
    asset="apkeep-x86_64-unknown-linux-gnu"
    sha256="a23579a3ba366d25a6d69848189b983d65662f4ecf4b9e11e16510811659de4e"
    ;;
  Linux:aarch64|Linux:arm64)
    asset="apkeep-aarch64-unknown-linux-gnu"
    sha256="5410acebd1b69427adcf98ccfdda6fa4dd3201e0540e5e2c01037b68e0a84049"
    ;;
  *)
    printf 'Unsupported platform for pinned apkeep binary: %s %s\n' "$(uname -s)" "$(uname -m)" >&2
    exit 1
    ;;
esac

mkdir -p "$tools_dir"
tmp="$(mktemp "$tools_dir/apkeep.XXXXXX")"
trap 'rm -f "$tmp"' EXIT

printf 'Installing apkeep %s (%s)...\n' "$version" "$asset" >&2
curl -fsSL --retry 3 --retry-delay 2 -o "$tmp" "$base_url/$asset"
printf '%s  %s\n' "$sha256" "$tmp" | sha256sum -c - >/dev/null
chmod 0755 "$tmp"
mv "$tmp" "$apkeep_bin"
trap - EXIT

"$apkeep_bin" --version | grep -Fqx "apkeep $version"
printf '%s\n' "$apkeep_bin"
