# Upstream setup notes

Verified against primary sources on 2026-10-19.

## Layout and defaults

[Sunaku's Glorious Engrammer](https://github.com/sunaku/glove80-keymaps/tree/v52) is at v52. The [installation guide](https://github.com/sunaku/glove80-keymaps/tree/v52#installing) chooses the base alphabet by placing it at layer zero. Its [`keymap.json`](https://github.com/sunaku/glove80-keymaps/blob/v52/keymap.json) contains QWERTY alongside Enthium, Dvorak, and Colemak. The export defaults to Linux, difficulty zero, enabled mouse keys and bilateral home-row-mod enforcement, with `HID_POINTING=y`. The author's three personal overrides in the README are additional customizations, not defaults.

A QWERTY-only derivative must remove the other three alpha layers, place QWERTY first, remap numeric layer parameters, and disable Magic's alternate-alphabet selectors. Inspection of the export shows those selectors contain raw `&to 1`, `&to 2`, and `&to 3` strings in Custom parameters. Layer dependencies in the embedded behavior snippet use guarded `LAYER_<name>` symbols. Removing alternate alphabets need not remove functional layers such as Symbol, Number, Gaming, Factory, or macOS.

This repository starts from upstream commit `7d8c0076308c5649614317fd8c6b53b800c46719` (v52). In addition to those changes, the generated numeric combo `layers` lists in the embedded behaviors were converted to symbolic `LAYER_<name>` references, excluding the removed layers. This preserves their original scope after renumbering. Unused alternate-alpha behavior branches remain guarded by undefined layer symbols and are excluded by the C preprocessor. No personal tuning overrides from Sunaku's README were added.

The matching initial JSON and keymap were checked for all 29 layers and 80 key positions per layer, including the remapped Factory and macOS toggles. Builds consume `config/glove80.keymap`; JSON is an editor snapshot, so future edits must explicitly synchronize them when moving between code and editor workflows.

Subsequent personal customizations are synchronized in both files: difficulty 5 (upstream expert preset, 100 ms tapping resolution); right T4/Symbol + h/y/n for double quote/backtick/single quote; left T4/Cursor + h/j/k/l for Left/Down/Up/Right and m/comma for Ctrl+Tab/Ctrl+Shift+Tab. These replace the previous bindings at those positions. The README lists the current behavior; the upstream maps describe the original defaults.

## Firmware generation

[MoErgo's import/export documentation](https://docs.moergo.com/layout-editor-guide/advanced-usage-export-import/) says to enable **Settings → Local Backup and Restore**, then use the editor's bottom-left Import controls for JSON. The editor can also export `.keymap` DTSI for local builds. [MoErgo's build guide](https://docs.moergo.com/layout-editor-guide/building-firmware/) documents hosted firmware generation.

The upstream `rake` command generates snippets and diagrams; it does not compile a UF2. [MoErgo's official config workflow](https://github.com/moergo-sc/glove80-zmk-config/blob/main/.github/workflows/build.yml) checks out `moergo-sc/zmk`, runs `nix-build config -o combined`, and uploads `combined/glove80.uf2`. A reproducible local build should pin the firmware source revision as well as the layout.

The build here pins MoErgo v26.09, commit `ce69e85f585c724142aae37ddf8a7e019ff19e93`, with the unpacked source hash in `config/firmware.nix`. The build expression and Actions setup follow MoErgo's config template (inspected at commit `34888be8c9d9a3d5b168a502b8b191ba43b4a1f3`). The firmware's own Nix expression pins its toolchain dependencies. Its `nix/zmk.nix` builds from `source/app`, so `config/firmware.nix` applies `config/zmk-normalize-diagonals.patch` through `overrideAttrs` with paths relative to `app/`. In v26.09, `app/src/behaviors/behavior_input_two_axis.c` integrates x and y separately, with a fractional remainder for each; it has no diagonal normalization. Zephyr's devicetree tooling rejects properties a binding does not declare, so stock builds fail on `normalize-diagonals` instead of ignoring it.

## First installation and later updates

[MoErgo's firmware-loading instructions](https://docs.moergo.com/glove80-user-guide/customizing-key-layout/#loading-new-zmk-firmware-onto-your-glove80) load the same UF2 onto the right half first, then the left. Each needs a USB data connection while flashing; one cable can be moved between them. Bootloader drives are `GLV80RHBOOT` and `GLV80LHBOOT`. Copying the UF2 makes the drive disappear.

The reliable power-up method works independently of installed key mappings: switch the half off, connect USB, hold physical `C6R6 + C3R3`, and switch it on. On factory keycaps those are **PgDn + I** on the right, **Magic + E** on the left. A slow-pulsing red LED indicates bootloader mode with USB connected.

[Sunaku's flashing guidance](https://github.com/sunaku/glove80-keymaps/tree/v52#flashing) explicitly requires both halves for the first installation, and permits later layout-only updates to the left half. Firmware-version changes require flashing both. MoErgo additionally recommends a configuration reset after firmware-version or Advanced Configuration changes.

## Reset and re-pair

[MoErgo's reset procedure](https://docs.moergo.com/glove80-user-guide/troubleshooting/#configuration-factory-reset-and-re-pairing-left-and-right-halves) clears Bluetooth profiles and saved preferences but preserves the flashed layout. Resetting one half requires resetting both:

1. Turn both halves off. On the left, hold physical `C6R6 + C3R2` (factory **Magic + 3**), turn it on, hold five seconds, and turn it off.
2. With both off, repeat on the right using `C6R6 + C3R2` (factory **PgDn + 8**).
3. Turn both on together. Enable RGB, check both halves, then disable RGB. Wait at least one minute so the configuration persists. Re-pair host Bluetooth devices as needed.

The physical positions are reliable even after changing keymap; factory legends and firmware-level shortcuts can differ after flashing.

## Native configuration and import metadata checks

The v26.09 firmware's [pointing Kconfig](https://github.com/moergo-sc/zmk/blob/v26.09/app/src/pointing/Kconfig) defines `ZMK_POINTING`; its [native mouse-button test configuration](https://github.com/moergo-sc/zmk/blob/v26.09/app/tests/pointing/mkp/native_posix_64.conf) enables `CONFIG_ZMK_POINTING=y`. Use that native symbol when translating the editor's `HID_POINTING` option into a `.conf` file.

Inspection of the [live editor JavaScript bundle](https://my.moergo.com/glove80/assets/index-CkOzY06V.js) found its layout validation schema supplies defaults for missing identity metadata: `uuid`, `parent_uuid`, and `creator` default to empty strings, and `date` defaults to null. These keys can therefore be omitted from a local derivative's import JSON. This is implementation evidence from the deployed editor on the verification date; the public import documentation does not specify a stable JSON schema.
