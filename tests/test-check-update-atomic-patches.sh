#!/usr/bin/env bash
# Regression test: a failed patch download must not corrupt the last known-good bundle.
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

cp "$repo_dir/check-instagram-update.sh" "$tmp_dir/check-instagram-update.sh"
chmod +x "$tmp_dir/check-instagram-update.sh"
mkdir -p "$tmp_dir/bin" "$tmp_dir/patches" "$tmp_dir/cli" "$tmp_dir/.tools/feurstagram"
printf 'known-good\n' > "$tmp_dir/patches/patches.mpp"
ln -s patches.mpp "$tmp_dir/patches/instagram.mpp"
touch "$tmp_dir/cli/morphe-cli.jar" "$tmp_dir/.tools/feurstagram/base.apk"

cat > "$tmp_dir/.update-state" <<'EOF'
PATCHES_VERSION=v-old
PATCHES_ASSET=patches.mpp
CLI_VERSION=v-cli
CLI_JAVA=java
FEUR_TAG=v-feur
FEUR_ASSET=base.apk
FEUR_DIGEST=
EOF

cat > "$tmp_dir/bin/curl" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ "$*" == *"api.github.com/repos/brosssh/morphe-patches"* ]]; then
  printf '{"tag_name":"v-new","assets":[{"name":"patches.mpp","browser_download_url":"https://example.test/patches.mpp"}]}\n'
  exit 0
fi
if [[ "$*" == *"api.github.com/repos/MorpheApp/morphe-desktop"* ]]; then
  printf '{"tag_name":"v-cli","assets":[{"name":"morphe-cli.jar","browser_download_url":"https://example.test/morphe-cli.jar"}]}\n'
  exit 0
fi
if [[ "$*" == *"api.github.com/repos/jean-voila/FeurStagram"* ]]; then
  printf '{"tag_name":"v-feur","assets":[{"name":"base.apk","browser_download_url":"https://example.test/base.apk"}]}\n'
  exit 0
fi
out=""
while (($#)); do
  if [[ "$1" == "-o" ]]; then shift; out="$1"; break; fi
  shift
done
[[ -n "$out" ]]
printf 'partial-download\n' > "$out"
exit 22
EOF
chmod +x "$tmp_dir/bin/curl"
printf '%s\n' '#!/usr/bin/env bash' 'exit 0' > "$tmp_dir/bin/java"
chmod +x "$tmp_dir/bin/java"

if env PATH="$tmp_dir/bin:$PATH" "$tmp_dir/check-instagram-update.sh" >/dev/null 2>&1; then
  echo 'expected failed download to make updater fail' >&2
  exit 1
fi

grep -Fqx 'known-good' "$tmp_dir/patches/patches.mpp"
grep -Fqx 'PATCHES_VERSION=v-old' "$tmp_dir/.update-state"
