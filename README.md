# Glove80 configuration

This configuration uses [Glorious Engrammer v52](https://github.com/sunaku/glove80-keymaps/tree/v52) with QWERTY as the only alphabet layout. It removes Enthium, Dvorak, Colemak, and their Magic layer selectors. It keeps all other layers, including Gaming, Factory QWERTY, and the macOS modifier overlay.

The firmware version is MoErgo v26.09. Home-row modifiers use upstream difficulty **5 (expert)**: 100 ms tapping resolution, with the upstream per-finger hold-time offsets. Linux shortcuts and bilateral enforcement remain enabled: home-row modifiers usually require the letter and modifier on opposite hands. Set your computer's input layout to US QWERTY.

Personal bindings (letter names refer to their QWERTY positions):

- Hold **right T4** (Space / Symbol): `h` types a double quote (`"`), `y` types a backtick, and `n` types a single quote (`'`).
- On **Symbol**, `w` / `e` type `(` / `)`, and `2` / `3` type `{` / `}`.
- Hold **left T4** (Backspace / Cursor): `h`, `j`, `k`, `l` send Left, Down, Up, Right; `m` sends Ctrl+Tab; comma sends Ctrl+Shift+Tab.

Other layer bindings retain their upstream behavior. The full upstream preset definitions are [documented in the keymap](https://github.com/sunaku/glove80-keymaps/blob/v52/keymap.dtsi).

## Build

To build on GitHub:

1. Commit and push the configuration to this repository.
2. Open [Actions](https://github.com/Lomzem/glove80/actions/workflows/build.yml) and select the successful Build run. A configuration push starts a build. You can also select Run workflow.
3. Download and extract the `glove80-firmware` artifact to get `glove80.uf2`.

To build locally, install [Nix](https://nixos.org/download/) and run:

```sh
./scripts/build.sh
```

The script downloads the specified firmware source and dependencies. It writes `firmware/glove80.uf2`.

## Install

Save your current firmware or export your layout before installation. Use the same `glove80.uf2` file for both halves.

For the first installation, connect each half with a USB data cable. Install the right half first. The key names below refer to the factory keycaps. Use the specified physical positions if your keycaps differ.

### Guided installation on Linux

Run the reusable wizard from a terminal:

```sh
./scripts/flash-wizard.sh
# Or use a firmware file downloaded from GitHub:
./scripts/flash-wizard.sh ~/Downloads/glove80.uf2
```

It validates the combined firmware, guides the physical buttons and cable changes, detects the correct bootloader by its volume label, and asks before copying to each half. Confirmation prompts default to **Yes** on Enter; type `n` to decline. It offers both-halves installation or a left-only keymap update, followed by an optional pairing reset. For keymap-only updates, choose `left` and answer `n` to the reset prompt. Requirements: Bash, Python 3, and `lsblk`; `udisksctl` is needed if your desktop does not mount the drive automatically. It does not require sudo.

If `/run/media/$USER/GLV80RHBOOT` does not exist, the keyboard is either not in bootloader mode yet or its drive is unmounted. Do not create that directory yourself. The wizard waits for the actual device and mounts it if needed. To inspect devices manually, run `lsblk -o NAME,LABEL,MOUNTPOINTS`.

### Manual installation

1. Turn off the right half. Connect it to your computer.
2. Hold PgDn and I at positions `C6R6` and `C3R3`. Turn on the right half. Release the keys when the red LED pulses slowly.
3. Copy `glove80.uf2` to the `GLV80RHBOOT` USB drive. Wait for the drive to disappear and the half to restart before you disconnect it.
4. Turn off the left half. Move the USB cable to it.
5. Hold Magic and E at positions `C6R6` and `C3R3`. Turn on the left half. Release the keys when the red LED pulses slowly.
6. Copy the same file to `GLV80LHBOOT`. Wait for the half to restart.

On Linux, you can use these commands after the drive mounts. Change the paths if necessary.

```sh
# Install on the right half first.
cp firmware/glove80.uf2 "/run/media/$USER/GLV80RHBOOT/"
sync

# Move the cable and start the left half in bootloader mode.
cp firmware/glove80.uf2 "/run/media/$USER/GLV80LHBOOT/"
sync
```

For a GitHub build, use the path to the downloaded file. If no drive appears, check the keys and use a USB cable that supports data.

After installation, wired use requires only the left half to be connected. The right half connects wirelessly.

For later keymap changes, install on the left half only. Install on both halves if you change the firmware version or advanced configuration. See the [MoErgo installation instructions](https://docs.moergo.com/glove80-user-guide/customizing-key-layout/#loading-new-zmk-firmware-onto-your-glove80) and [upstream instructions](https://github.com/sunaku/glove80-keymaps/tree/v52#flashing).

## Reset and pair

After a firmware version or advanced configuration change, install on both halves and reset them. The reset clears saved Bluetooth pairings and preferences. It keeps this keymap.

1. Turn off both halves.
2. On the left, hold Magic and 3 at positions `C6R6` and `C3R2`. Turn it on. Hold the keys for five seconds, then turn it off.
3. On the right, repeat step 2 with PgDn and 8 at positions `C6R6` and `C3R2`.
4. Turn on both halves together. Enable RGB. Check that both halves light up, then disable RGB.
5. Wait at least one minute for the settings to save. Pair your Bluetooth devices again if necessary.

See the [MoErgo reset procedure](https://docs.moergo.com/glove80-user-guide/troubleshooting/#configuration-factory-reset-and-re-pairing-left-and-right-halves).

## Customize

Edit these files:

- `config/glove80.keymap` defines the keymap. Change settings near `OPERATING_SYSTEM` and key positions in the layer bindings near the end.
- `config/glove80.conf` enables mouse support.
- `config/default.nix` specifies the firmware version and builds both halves.

To use the [MoErgo Layout Editor](https://my.moergo.com/glove80/):

1. Sign in and create a layout.
2. Enable Local Backup and Restore in Settings.
3. Use Import at the bottom left to load `layout/glove80.json`.
4. Keep QWERTY on layer 0 and use firmware 26.09. Keep `HID_POINTING = y` in Advanced Configuration for mouse support.
5. Build and download the firmware in the editor, or export the files for a GitHub build.

After editor changes, export the JSON to `layout/glove80.json` and the ZMK keymap to `config/glove80.keymap`. Check advanced configuration changes against `config/glove80.conf`.

The JSON file does not update when you edit the keymap directly. Do not import an older JSON file over those changes.

Use the QWERTY diagrams in the [interactive layer guide](https://sunaku.github.io/moergo-glove80-keyboard.html#layers) and [printable maps](https://github.com/sunaku/glove80-keymaps/blob/v52/README/all-layer-diagrams.pdf). Their alternate alphabet shortcuts are disabled here. See [upstream notes](docs/upstream-notes.md) for source and implementation details.
