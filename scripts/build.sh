#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

if ! command -v nix-build >/dev/null 2>&1; then
  echo 'nix-build is required. Install Nix, or use the GitHub Actions Build workflow.' >&2
  exit 1
fi

mkdir -p build firmware
nix-build config --out-link build/combined "$@"
cp build/combined/glove80.uf2 firmware/glove80.uf2
echo 'Built firmware/glove80.uf2 (combined left + right firmware).'
