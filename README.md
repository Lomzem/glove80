# Glove80 configuration

[Glorious Engrammer v52](https://github.com/sunaku/glove80-keymaps/tree/v52), with **QWERTY as the base and only alphabet layout**. Enthium, Dvorak, and Colemak are removed, and their Magic-layer selectors are disabled. The functional layers (including Gaming, Factory QWERTY, and the macOS modifier overlay) remain.

Everything else uses upstream defaults: Linux shortcuts, difficulty 0, home-row modifiers with bilateral enforcement, mouse keys, layer access, colors, and timing. Home-row modifiers generally need the letter and modifier on opposite hands. Keep your computer's input layout set to US QWERTY. Firmware is pinned to MoErgo **v26.09**, rather than following a moving branch.

## Build the firmware

The easiest build runs on GitHub, without installing a toolchain:

1. Commit and push this configuration to this repository.
2. Open [Actions → Build](https://github.com/Lomzem/glove80/actions/workflows/build.yml). A configuration push starts a build; you can also select **Run workflow**.
3. Open the successful run and download the **glove80-firmware** artifact. Unzip it to obtain `glove80.uf2`.

The artifact contains **one combined UF2 for both halves**. Use that same file on each half. Keep a copy of your current firmware or export your existing layout before replacing it.

For a local build, install [Nix](https://nixos.org/download/) and run:

```sh
./scripts/build.sh
```

This downloads the pinned MoErgo source and its build dependencies and writes `firmware/glove80.uf2`. The first build can take a while. GitHub Actions uses MoErgo's binary cache.

## Install over USB-C

**The first installation needs both halves connected by USB, one at a time.** A single USB data cable is enough: flash the **right half first**, then move the cable to the left. Both halves need the same firmware version. Normal wired use afterward only needs the left connected; the right communicates wirelessly.

Use the physical power-up bootloader shortcut below, which works regardless of the layout currently installed. The names are the original factory keycap legends; the physical positions are what matter.

1. Turn the **right** half off and connect it to your computer with a USB data cable.
2. Hold **PgDn + I** (physical `C6R6 + C3R3` on the right), then turn that half on. Release the keys once bootloader mode starts. Its red LED pulses slowly.
3. Open the **GLV80RHBOOT** USB drive. Copy `glove80.uf2` into it. The drive disappears as the half reboots; wait for it to finish before unplugging.
4. Turn the **left** half off, move the USB cable to it, hold **Magic + E** (physical `C6R6 + C3R3` on the left), and turn it on.
5. Copy the **same** `glove80.uf2` into **GLV80LHBOOT** and let it reboot.

On Linux you can copy from a terminal once your desktop has mounted the bootloader drive. Adjust the paths if your system mounts removable drives elsewhere:

```sh
# Right half first, while GLV80RHBOOT is mounted:
cp firmware/glove80.uf2 "/run/media/$USER/GLV80RHBOOT/"
sync

# Move the cable and enter bootloader mode on the left, then:
cp firmware/glove80.uf2 "/run/media/$USER/GLV80LHBOOT/"
sync
```

Use the downloaded UF2's path instead if you built through GitHub. Merely plugging in a half does not put it in bootloader mode. If no drive appears, check the power-up chord and that the USB cable supports data.

For later **keymap-only** changes on this same firmware version and advanced configuration, flashing the left half is sufficient. Flash both again whenever updating the firmware version or advanced configuration. See [MoErgo's loading instructions](https://docs.moergo.com/glove80-user-guide/customizing-key-layout/#loading-new-zmk-firmware-onto-your-glove80) and [upstream's flashing guidance](https://github.com/sunaku/glove80-keymaps/tree/v52#flashing).

## Reset and re-pair after a firmware change

If moving from another firmware version or changing advanced configuration, follow [MoErgo's configuration reset procedure](https://docs.moergo.com/glove80-user-guide/troubleshooting/#configuration-factory-reset-and-re-pairing-left-and-right-halves) after flashing both halves. This clears saved Bluetooth pairings and preferences, while preserving this keymap.

1. Turn both halves off. On the left, hold **Magic + 3** (physical `C6R6 + C3R2`), turn it on, hold for five seconds, then turn it off.
2. With both halves off again, repeat on the right using **PgDn + 8** (physical `C6R6 + C3R2`).
3. Turn both halves on together. Enable RGB and check that both halves light up, then disable it. Wait at least a minute for settings to persist. Re-pair Bluetooth hosts if needed.

## Customize later

- `config/glove80.keymap` is the firmware build's source of truth. Edit its settings near `OPERATING_SYSTEM` to change OS or behavior; edit layer bindings near the bottom for key placement.
- `config/glove80.conf` enables pointing support for the default mouse layer.
- `config/default.nix` pins the firmware and builds both halves.
- `layout/glove80.json` is the matching initial Layout Editor snapshot. It does not automatically stay in sync with direct keymap edits.

To edit visually, sign into the [MoErgo Layout Editor](https://my.moergo.com/glove80/), create a layout, enable **Settings → Local Backup and Restore**, and import `layout/glove80.json` using the bottom-left Import control. Keep QWERTY at layer 0 and use firmware **26.09**. The default mouse layer needs **HID_POINTING = y** in Advanced Configuration (already present in the JSON). The editor can build and download firmware directly, too.

After visual edits, export both the JSON and the ZMK `.keymap` file back to their paths in this repository before using the GitHub build. Review any Advanced Configuration changes against `config/glove80.conf`. Avoid importing the initial JSON over later code-only changes.

For learning the default layers, use [Sunaku's interactive guide](https://sunaku.github.io/moergo-glove80-keyboard.html#layers) and [printable maps](https://github.com/sunaku/glove80-keymaps/blob/v52/README/all-layer-diagrams.pdf), choosing the QWERTY base diagram. Alternate-alphabet shortcuts in those upstream guides are disabled here. Provenance and implementation details are in [upstream notes](docs/upstream-notes.md).
