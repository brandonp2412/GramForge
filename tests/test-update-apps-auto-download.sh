#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

cp "$repo_dir/update-apps.sh" "$tmp_dir/update-apps.sh"
mkdir -p "$tmp_dir/lib" "$tmp_dir/tools" "$tmp_dir/bin" "$tmp_dir/cli" "$tmp_dir/patches" "$tmp_dir/apk"
cp "$repo_dir/lib/config.sh" "$tmp_dir/lib/config.sh"
cp "$repo_dir/tools/ensure-apkeep.sh" "$tmp_dir/tools/ensure-apkeep.sh"
chmod +x "$tmp_dir/update-apps.sh" "$tmp_dir/tools/ensure-apkeep.sh"
touch "$tmp_dir/APKEditor.jar" "$tmp_dir/cli/morphe-cli.jar" "$tmp_dir/patches/instagram.mpp" "$tmp_dir/test.keystore"

printf '%s\n' \
  '#!/usr/bin/env bash' \
  'printf "PATCHES_VERSION=v2.8.2\nPATCHES_ASSET=patches-2.8.2.mpp\nCLI_VERSION=v1.14.0\nCLI_JAVA=java\n" > .update-state' \
  > "$tmp_dir/check-instagram-update.sh"
chmod +x "$tmp_dir/check-instagram-update.sh"

printf '%s\n' \
  '#!/usr/bin/env bash' \
  'set -euo pipefail' \
  'if [[ "${1:-}" == "--version" ]]; then printf "apkeep 1.0.0\n"; exit 0; fi' \
  'printf "%s\n" "$*" > "$APKEEP_ARGS_FILE"' \
  'out_dir="${!#}"' \
  'python3 - "$out_dir" <<'"'"'PY'"'"'' \
  'import io, json, pathlib, sys, zipfile' \
  'out = pathlib.Path(sys.argv[1])' \
  'base = io.BytesIO()' \
  'with zipfile.ZipFile(base, "w") as z: z.writestr("lib/arm64-v8a/libtest.so", b"x")' \
  'manifest = {"package_name":"com.instagram.android","version_name":"124.0.0"}' \
  'with zipfile.ZipFile(out / "com.instagram.android@124.0.0@arm64-v8a.xapk", "w") as z:' \
  '    z.writestr("manifest.json", json.dumps(manifest))' \
  '    z.writestr("com.instagram.android.apk", base.getvalue())' \
  'PY' \
  > "$tmp_dir/bin/apkeep"
chmod +x "$tmp_dir/bin/apkeep"

printf '%s\n' \
  '#!/usr/bin/env bash' \
  'set -euo pipefail' \
  'args="$*"' \
  'if [[ "$args" == *"list-versions"* ]]; then printf "Most common compatible versions:\n  124.0.0\n"; exit 0; fi' \
  'if [[ "$args" == *"APKEditor.jar"* ]]; then while (($#)); do [[ "$1" == "-o" ]] && { shift; touch "$1"; exit 0; }; shift; done; fi' \
  'if [[ "$args" == *"morphe-cli.jar patch"* ]]; then while (($#)); do [[ "$1" == "-o" ]] && { shift; touch "$1"; exit 0; }; shift; done; fi' \
  'exit 0' \
  > "$tmp_dir/bin/java"
chmod +x "$tmp_dir/bin/java"

APKEEP_ARGS_FILE="$tmp_dir/apkeep-args" \
GRAMFORGE_APKEEP_BIN="$tmp_dir/bin/apkeep" \
GRAMFORGE_CONFIG_FILE=/dev/null \
GRAMFORGE_KEYSTORE="$tmp_dir/test.keystore" \
PATH="$tmp_dir/bin:$PATH" \
"$tmp_dir/update-apps.sh" >/dev/null

grep -Fq -- '-a com.instagram.android@124.0.0 -d apk-pure -o arch=arm64-v8a' "$tmp_dir/apkeep-args"
test -f "$tmp_dir/apk/instagram-124.0.0.xapk"
test -f "$tmp_dir/apk/instagram-patched-124.0.0.apk"
grep -Fqx 'INSTAGRAM_VERSION=124.0.0' "$tmp_dir/.patched-app-state"
