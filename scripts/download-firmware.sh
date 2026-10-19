#!/usr/bin/env bash
# Fetch a successful build only when its build inputs match this checkout.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
for dependency in gh git python3; do
  command -v "$dependency" >/dev/null || {
    echo "Required command missing: $dependency" >&2
    exit 1
  }
done

build_inputs=(config scripts/build.sh .github/workflows/build.yml)
if [[ -n $(git ls-files --others --exclude-standard -- "${build_inputs[@]}") ]]; then
  echo 'Untracked build inputs found. Commit/push them and wait for a build, or pass a locally built UF2 explicitly.' >&2
  exit 1
fi
branch=$(git branch --show-current)
[[ -n $branch ]] || { echo 'Check out a branch before downloading firmware.' >&2; exit 1; }
run=$(gh run list --workflow build.yml --branch "$branch" --status success --limit 1 \
  --json databaseId,headSha,url)
mapfile -t info < <(python3 -c '
import json,sys
runs=json.load(sys.stdin)
if runs:
    r=runs[0]
    print(r["databaseId"]); print(r["headSha"]); print(r["url"])
' <<< "$run")
if [[ ${#info[@]} -ne 3 ]]; then
  echo 'No successful firmware build exists for this branch yet. Try again when GitHub Actions succeeds.' >&2
  exit 1
fi
if ! git diff --quiet "${info[1]}" -- "${build_inputs[@]}"; then
  echo 'The latest successful firmware does not match this checkout. Refusing to flash stale firmware.' >&2
  echo 'Commit/push build changes, wait for GitHub Actions to succeed, then rerun the wizard.' >&2
  exit 1
fi

mkdir -p firmware
download_dir=$(mktemp -d "$PWD/firmware/.download.XXXXXX")
trap 'rm -rf -- "$download_dir"' EXIT
gh run download "${info[0]}" --name glove80-firmware --dir "$download_dir"
python3 scripts/flash-drive.py validate "$download_dir/glove80.uf2"
if [[ -f firmware/glove80.uf2 ]] && ! cmp -s firmware/glove80.uf2 "$download_dir/glove80.uf2"; then
  cp firmware/glove80.uf2 firmware/glove80-previous.uf2
fi
mv -- "$download_dir/glove80.uf2" firmware/glove80.uf2
printf 'Commit: %s\nBuild: %s\n' "${info[1]}" "${info[2]}" > firmware/glove80.build.txt
printf 'Downloaded firmware from commit %s\n%s\n' "${info[1]:0:7}" "${info[2]}"
