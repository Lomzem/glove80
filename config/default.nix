{ firmware ? import (builtins.fetchTarball {
    # MoErgo v26.09. Keep this pinned when changing the keymap.
    url = "https://github.com/moergo-sc/zmk/archive/ce69e85f585c724142aae37ddf8a7e019ff19e93.tar.gz";
    sha256 = "sha256-dm/wCNTJblGUdgvFsh5NEQv5xP+a+P/idBNw2un3Enk=";
  }) {}
}:

let
  config = ./.;

  glove80_left  = firmware.zmk.override { board = "glove80_lh"; keymap = "${config}/glove80.keymap"; kconfig = "${config}/glove80.conf"; };
  glove80_right = firmware.zmk.override { board = "glove80_rh"; keymap = "${config}/glove80.keymap"; kconfig = "${config}/glove80.conf"; };

in firmware.combine_uf2 glove80_left glove80_right
