# Configure a key binding

## 1. Resolve the request

Identify the Layer, physical Position, and desired Output for every binding. Letter names refer to their **QWERTY Positions**, even on another Layer. Resolve left/right Thumb keys separately: inspect their QWERTY bindings to find the Layer activation. Ask only when two requested Outputs still conflict at the same Position on the same Layer.

Use the compact lookup below instead of loading the full keymap or JSON. For a named Position, find its array offset with `rg '^#define POS_RH_T6 ' config/glove80.keymap` (substitute the requested Position). For a letter, inspect QWERTY first; home-row letters appear inside `Custom` hold-tap bindings.

Done when each requested change has a Layer, array offset, and Output, including the hand of each Thumb key.

## 2. Edit both representations

- **Firmware authority:** `config/glove80.keymap`. Change the binding at that offset inside `layer_<name> { bindings = <...>; };`.
- **Editor snapshot:** `layout/glove80.json`. Find the Layer by `layer_names.index(name)`, then change `layers[layer_offset][position_offset]`. Replace outdated decorations with labels describing the new Output, or omit them.

Keep both representations synchronized. A Layer contains 80 bindings; replacing a binding preserves their order. Use a JSON parser for edits: its embedded behavior strings are large and appear on single lines. Keep QWERTY as the sole alphabet Layer.

For example, Ctrl+Shift+Tab is `&kp LC(LS(TAB))` in the keymap and `{"value":"&kp","params":[{"value":"LC","params":[{"value":"LS","params":[{"value":"TAB"}]}]}]}` in JSON. Use `Custom` with a raw binding string for behaviors that the editor cannot otherwise represent.

For timing changes, find the user overrides near the start of `custom_defined_behaviors` in JSON and the matching section of the keymap. Read the setting's comments/defaults only as needed. Update the override in both files. For new behaviors or combos, synchronize the embedded behavior/devicetree snippets as well as their binding references.

Done when every requested binding/setting agrees in both files and unrelated bindings remain unchanged. Update the README's personal bindings when their described behavior changes.

## 3. Build and deliver

Verify the changed Positions, stage the task's files, and commit. The Lefthook firmware check builds a snapshot of the staged inputs, validates the combined UF2, and updates `firmware/glove80.uf2`. It skips commits without firmware changes. Set up the hook once using the [README](../../README.md#commit-checks). For simple remaps, rely on this real build rather than adding tests that restate the bindings.

Require the hook's `[firmware] PASS` before reporting a firmware change as built. On failure, read the diagnostic excerpt and `build/firmware-pre-commit.log`, fix and stage the inputs, then retry. Run `python3 scripts/check-firmware.py` to reproduce the staged check directly, or `./scripts/build.sh` to build working-tree edits. Push after the commit succeeds; monitor GitHub Actions only when requested. Leave unrelated work intact.

The user performs the hardware steps with `./scripts/flash-wizard.sh`, which builds locally by default. An explicit UF2 argument skips building. For keymap-only changes on the same firmware/advanced configuration, tell them to choose `left` and decline the optional pairing reset. For firmware/advanced-configuration changes, follow the [README installation and reset instructions](../../README.md#install).

Done when a validated local UF2 is available, the changes are committed/pushed, and the user has the applicable flashing instructions. Describe hardware behavior as verified only after the user confirms it.

## Compact lookup

Run from the repo root. Change `QWERTY` to the target Layer; add array offsets after it to limit output. Omit offsets to inspect its 80 bindings. This prints only values and parameters, excluding decorations and embedded snippets.

```sh
python3 - QWERTY <<'PY'
import json, sys
x = json.load(open('layout/glove80.json'))
name = sys.argv[1]
selected = {int(p) for p in sys.argv[2:]}
layer = x['layers'][x['layer_names'].index(name)]
for offset, binding in enumerate(layer):
    if not selected or offset in selected:
        print(offset, json.dumps({k: binding[k] for k in ('value', 'params') if k in binding}))
PY
```

For implementation provenance or upstream behavior questions, consult [upstream notes](../upstream-notes.md) and follow only the relevant source link.
