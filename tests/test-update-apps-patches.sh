#!/usr/bin/env bash
# Regression test: Feur supplies ad removal; Morphe hides only configured navigation.
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

cp "$repo_dir/update-apps.sh" "$tmp_dir/update-apps.sh"
mkdir -p "$tmp_dir/lib" "$tmp_dir/tools" "$tmp_dir/bin" "$tmp_dir/cli" "$tmp_dir/patches" "$tmp_dir/apk" "$tmp_dir/.tools/feurstagram"
cp "$repo_dir/lib/config.sh" "$tmp_dir/lib/config.sh"
cp "$repo_dir/tools/ensure-apktool.sh" "$tmp_dir/tools/ensure-apktool.sh"
chmod +x "$tmp_dir/update-apps.sh" "$tmp_dir/tools/ensure-apktool.sh"
touch "$tmp_dir/APKEditor.jar" "$tmp_dir/cli/morphe-cli.jar" "$tmp_dir/patches/instagram.mpp" "$tmp_dir/test.keystore" "$tmp_dir/fake-apktool.jar"
touch "$tmp_dir/.tools/feurstagram/feurstagram.apk"

cat > "$tmp_dir/check-instagram-update.sh" <<'EOF'
#!/usr/bin/env bash
cat > .update-state <<STATE
PATCHES_VERSION=v2.8.2
PATCHES_ASSET=patches-2.8.2.mpp
CLI_VERSION=v1.16.0
CLI_JAVA=java
FEUR_TAG=v446-0-0-49-77
FEUR_ASSET=feurstagram.apk
FEUR_DIGEST=
STATE
EOF
chmod +x "$tmp_dir/check-instagram-update.sh"

cat > "$tmp_dir/profile.py" <<'EOF'
import pathlib, sys
assert pathlib.Path(sys.argv[1]).is_dir()
EOF
cat > "$tmp_dir/normalize.py" <<'EOF'
import shutil, sys
shutil.copyfile(sys.argv[1], sys.argv[2])
EOF

cat > "$tmp_dir/bin/java" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
args="$*"
if [[ "$args" == *"APKEditor.jar info"* ]]; then
  printf 'package="com.instagram.android"\nVersionName="446.0.0.49.77"\n'
  exit 0
fi
if [[ "$args" == *"fake-apktool.jar d "* ]]; then
  while (($#)); do [[ "$1" == "-o" ]] && { shift; mkdir -p "$1"; exit 0; }; shift; done
fi
if [[ "$args" == *"fake-apktool.jar b "* ]]; then
  while (($#)); do [[ "$1" == "-o" ]] && { shift; : > "$1"; exit 0; }; shift; done
fi
if [[ "$args" == *"morphe-cli.jar patch"* ]]; then
  printf '%s\n' "$args" > "$PATCH_ARGS_FILE"
  report=""
  output=""
  while (($#)); do
    case "$1" in
      -r) shift; report="$1" ;;
      -o) shift; output="$1" ;;
    esac
    shift || true
  done
  : > "$output"
  cat > "$report" <<JSON
{"packageName":"com.instagram.android","packageVersion":"446.0.0.49.77","patchingSteps":[{"step":"PATCHING","success":true},{"step":"REBUILDING","success":true},{"step":"SIGNING","success":true}],"appliedPatches":[{"name":"Hide navigation buttons","options":[]}],"failedPatches":[]}
JSON
  exit 0
fi
exit 0
EOF
chmod +x "$tmp_dir/bin/java"

PATCH_ARGS_FILE="$tmp_dir/patch-args" GRAMFORGE_APKTOOL_JAR="$tmp_dir/fake-apktool.jar" GRAMFORGE_PROFILE_PATCHER="$tmp_dir/profile.py" GRAMFORGE_APK_NORMALIZER="$tmp_dir/normalize.py" GRAMFORGE_CONFIG_FILE=/dev/null GRAMFORGE_KEYSTORE="$tmp_dir/test.keystore" PATH="$tmp_dir/bin:$PATH" "$tmp_dir/update-apps.sh" >/dev/null

patch_args="$(<"$tmp_dir/patch-args")"
[[ "$patch_args" != *'-e Hide ads'* ]]
[[ "$patch_args" == *'-e Hide navigation buttons'* ]]
[[ "$patch_args" == *'-O hideHome=true'* ]]
[[ "$patch_args" == *'-O hideReels=false'* ]]
[[ "$patch_args" == *'-O hideDirect=false'* ]]
[[ "$patch_args" == *'-O hideSearch=false'* ]]
[[ "$patch_args" == *'-O hideProfile=false'* ]]
[[ "$patch_args" == *'-O hideCreate=false'* ]]
[[ "$patch_args" == *'--bytecode-mode STRIP_FAST'* ]]
[[ "$patch_args" == *'--exclusive'* ]]
[[ "$patch_args" == *' -f '* ]]
grep -Fqx 'INSTAGRAM_VERSION=446.0.0.49.77' "$tmp_dir/.patched-app-state"
grep -Fqx 'INSTAGRAM_PATCH_PROFILE=feur-v446-0-0-49-77-brosssh-v2.8.2-v1.16.0-ads-nav-true-false-false-false-false-false-v2' "$tmp_dir/.patched-app-state"

rm -f "$tmp_dir/apk/instagram-patched-446.0.0.49.77.apk" "$tmp_dir/patch-args"
PATCH_ARGS_FILE="$tmp_dir/patch-args" GRAMFORGE_APKTOOL_JAR="$tmp_dir/fake-apktool.jar" GRAMFORGE_PROFILE_PATCHER="$tmp_dir/profile.py" GRAMFORGE_APK_NORMALIZER="$tmp_dir/normalize.py" GRAMFORGE_CONFIG_FILE=/dev/null GRAMFORGE_KEYSTORE="$tmp_dir/test.keystore" PATH="$tmp_dir/bin:$PATH" "$tmp_dir/update-apps.sh" >/dev/null
test -f "$tmp_dir/apk/instagram-patched-446.0.0.49.77.apk"
test -f "$tmp_dir/patch-args"
