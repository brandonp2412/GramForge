#!/usr/bin/env bash
# Regression test: updater selects and verifies the standard FeurStagram APK, never the clone.
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

cp "$repo_dir/check-instagram-update.sh" "$tmp_dir/check-instagram-update.sh"
chmod +x "$tmp_dir/check-instagram-update.sh"
mkdir -p "$tmp_dir/bin" "$tmp_dir/patches" "$tmp_dir/cli" "$tmp_dir/.tools/feurstagram"
printf 'patch\n' > "$tmp_dir/patches/patches.mpp"
ln -s patches.mpp "$tmp_dir/patches/instagram.mpp"
touch "$tmp_dir/cli/morphe-cli.jar"

cat > "$tmp_dir/.update-state" <<'EOF'
PATCHES_VERSION=v-patches
PATCHES_ASSET=patches.mpp
CLI_VERSION=v-cli
CLI_JAVA=java
FEUR_TAG=none
FEUR_ASSET=
FEUR_DIGEST=
EOF

cat > "$tmp_dir/bin/curl" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
args="$*"
if [[ "$args" == *"api.github.com/repos/brosssh/morphe-patches"* ]]; then
  printf '{"tag_name":"v-patches","assets":[{"name":"patches.mpp","browser_download_url":"https://example.test/patches.mpp"}]}\n'
  exit 0
fi
if [[ "$args" == *"api.github.com/repos/MorpheApp/morphe-desktop"* ]]; then
  printf '{"tag_name":"v-cli","assets":[{"name":"morphe-cli.jar","browser_download_url":"https://example.test/morphe-cli.jar"}]}\n'
  exit 0
fi
if [[ "$args" == *"api.github.com/repos/jean-voila/FeurStagram"* ]]; then
  digest="$(printf 'feur-base\n' | sha256sum | awk '{print $1}')"
  printf '{"tag_name":"v446-0-0-49-77","assets":[{"name":"feurstagram-446-clone.apk","browser_download_url":"https://example.test/clone.apk","digest":"sha256:%s"},{"name":"feurstagram-446.apk","browser_download_url":"https://example.test/standard.apk","digest":"sha256:%s"}]}\n' "$digest" "$digest"
  exit 0
fi

out=""
url="${!#}"
while (($#)); do
  if [[ "$1" == "-o" ]]; then shift; out="$1"; break; fi
  shift
done
[[ "$url" == "https://example.test/standard.apk" ]]
printf 'feur-base\n' > "$out"
EOF
chmod +x "$tmp_dir/bin/curl"

cat > "$tmp_dir/bin/java" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
chmod +x "$tmp_dir/bin/java"

env PATH="$tmp_dir/bin:$PATH" "$tmp_dir/check-instagram-update.sh" >/dev/null

grep -Fqx 'feur-base' "$tmp_dir/.tools/feurstagram/feurstagram-446.apk"
grep -Fqx 'FEUR_TAG=v446-0-0-49-77' "$tmp_dir/.update-state"
grep -Fqx 'FEUR_ASSET=feurstagram-446.apk' "$tmp_dir/.update-state"
! grep -Fq -- '-clone.apk' "$tmp_dir/.update-state"
