#!/usr/bin/env bash
# Regression tests for Morphe report format compatibility and fail-closed validation.
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

eval "$(sed -n '/^verify_patch_report() {/,/^}/p' "$repo_dir/update-apps.sh")"

version=453.0.0.57.79
new_report="$tmp_dir/current.json"
old_report="$tmp_dir/legacy.json"
report="$tmp_dir/case.json"

printf '%s\n' '{"success":true,"packageName":"com.instagram.android","packageVersion":"453.0.0.57.79","appliedPatches":["Hide navigation buttons"],"failedPatches":[],"stepResults":[{"step":"PATCHING","success":true},{"step":"REBUILDING","success":true},{"step":"SIGNING","success":true}]}' > "$new_report"
printf '%s\n' '{"packageName":"com.instagram.android","packageVersion":"453.0.0.57.79","appliedPatches":[{"name":"Hide navigation buttons","options":[]}],"failedPatches":[],"patchingSteps":[{"step":"PATCHING","success":true},{"step":"REBUILDING","success":true},{"step":"SIGNING","success":true}]}' > "$old_report"

expect_accept() {
  if ! verify_patch_report "$1" "$version"; then
    echo "Expected valid Morphe report: $2" >&2
    exit 1
  fi
}
expect_reject() {
  if verify_patch_report "$report" "$version"; then
    echo "Accepted invalid Morphe report: $1" >&2
    exit 1
  fi
}
reject_change() {
  jq "$2" "$new_report" > "$report"
  expect_reject "$1"
}

expect_accept "$new_report" current-string-patch-format
expect_accept "$old_report" legacy-object-patch-format

reject_change wrong-package '.packageName = "com.example.other"'
reject_change wrong-version '.packageVersion = "452.0.0.48.64"'
reject_change explicit-failure '.success = false'
reject_change no-step-results 'del(.stepResults)'
reject_change missing-signing-step 'del(.stepResults[2])'
reject_change failed-rebuilding-step '.stepResults[1].success = false'
reject_change missing-applied-patches 'del(.appliedPatches)'
reject_change missing-navigation-patch '.appliedPatches = []'
reject_change additional-patch '.appliedPatches += ["Unknown patch"]'
reject_change failed-patch '.failedPatches = ["Hide navigation buttons"]'
reject_change missing-failed-patch-array 'del(.failedPatches)'

jq -n '{success:true,packageName:"com.instagram.android",packageVersion:"453.0.0.57.79",stepResults:[],appliedPatches:["Hide navigation buttons"],failedPatches:[]}' > "$report"
expect_reject empty-stages

printf 'Morphe report verification: current and legacy schemas accepted; 12 invalid reports rejected.\n'
