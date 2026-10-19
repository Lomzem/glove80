#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

if ! command -v nix-build >/dev/null 2>&1; then
  echo 'nix-build is required. Install Nix; see README.md: Build locally.' >&2
  exit 1
fi

mkdir -p build firmware
nix-build config --out-link build/combined "$@"
# Validate before replacing the previous known firmware. The wizard stops on
# any build failure and never falls back to an older file.
python3 scripts/flash-drive.py validate build/combined/glove80.uf2
if [[ -f firmware/glove80.uf2 ]] && ! cmp -s firmware/glove80.uf2 build/combined/glove80.uf2; then
  cp firmware/glove80.uf2 firmware/glove80-previous.uf2
fi
staged_firmware=$(mktemp "$PWD/firmware/.build.XXXXXX")
trap 'rm -f -- "$staged_firmware"' EXIT
cp build/combined/glove80.uf2 "$staged_firmware"
mv -- "$staged_firmware" firmware/glove80.uf2
rm -f firmware/glove80.build.txt
echo 'Built firmware/glove80.uf2 (combined left + right firmware).'
