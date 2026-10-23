# Patched firmware package set shared by the Glove80 build (default.nix) and
# tests/pointer-motion. Pass `firmware` to patch a different MoErgo checkout.
{ firmware ? import (builtins.fetchTarball {
    # MoErgo v26.09. Keep this pinned when changing the keymap.
    url = "https://github.com/moergo-sc/zmk/archive/ce69e85f585c724142aae37ddf8a7e019ff19e93.tar.gz";
    sha256 = "sha256-dm/wCNTJblGUdgvFsh5NEQv5xP+a+P/idBNw2un3Enk=";
  }) {}
}:

firmware // {
  # Adds the opt-in normalize-diagonals property to two-axis input behaviors.
  # Paths are relative to the firmware's app/ directory, its source root.
  zmk = firmware.zmk.overrideAttrs (old: {
    patches = (old.patches or []) ++ [ ./zmk-normalize-diagonals.patch ];
  });
}
