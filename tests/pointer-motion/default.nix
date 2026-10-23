# Runs the patched pointer behavior in ZMK's native_posix_64 simulator and
# captures its HID log. tests/test_pointer_motion.py checks the motion.
# Accepts the same optional `firmware` argument as config/firmware.nix.
args@{ ... }:

let firmware = import ../../config/firmware.nix args; in

firmware.callPackage ({ lib, gcc }:
  (firmware.zmk.override {
    board = "native_posix_64";
    keymap = ./native_posix_64.keymap;
    kconfig = ./native_posix_64.conf;
  }).overrideAttrs (old: {
    name = "zmk_pointer_motion_log";
    nativeBuildInputs = old.nativeBuildInputs ++ [ gcc ];
    cmakeFlags = lib.filter (flag: !(lib.any (prefix: lib.hasPrefix prefix flag) [
      "-DZEPHYR_TOOLCHAIN_VARIANT=" "-DGNUARMEMB_TOOLCHAIN_PATH=" "-DCMAKE_C_COMPILER="
      "-DCMAKE_CXX_COMPILER=" "-DCMAKE_AR=" "-DCMAKE_RANLIB=" "-DBOARD_ROOT="
    ])) old.cmakeFlags ++ [
      "-DZEPHYR_TOOLCHAIN_VARIANT=host"
      "-DCMAKE_C_COMPILER=${gcc}/bin/gcc"
      "-DCMAKE_CXX_COMPILER=${gcc}/bin/g++"
    ];
    installPhase = ''
      mkdir $out
      ./zephyr/zmk.exe > $out/zmk.log
    '';
  })
) {}
