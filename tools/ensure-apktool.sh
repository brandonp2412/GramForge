#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [[ -n "${GRAMFORGE_APKTOOL_JAR:-}" ]]; then
  [[ -f "$GRAMFORGE_APKTOOL_JAR" ]] || { echo "Configured Apktool jar not found: $GRAMFORGE_APKTOOL_JAR" >&2; exit 1; }
  printf '%s\n' "$GRAMFORGE_APKTOOL_JAR"
  exit 0
fi

version="3.0.3"
sha256="dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423"
url="https://github.com/iBotPeaches/Apktool/releases/download/v${version}/apktool_${version}.jar"
target=".tools/apktool-${version}.jar"
mkdir -p .tools

verify() {
  [[ -f "$1" ]] && [[ "$(sha256sum "$1" | awk '{print $1}')" == "$sha256" ]]
}

if ! verify "$target"; then
  tmp="$(mktemp ".tools/.apktool-${version}.XXXXXX")"
  trap 'rm -f "$tmp"' EXIT
  curl -fL --retry 3 -o "$tmp" "$url"
  verify "$tmp" || { echo "Apktool SHA-256 verification failed." >&2; exit 1; }
  mv "$tmp" "$target"
  trap - EXIT
fi

printf '%s\n' "$target"
