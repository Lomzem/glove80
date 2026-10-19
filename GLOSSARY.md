# Glove80 keymap

A personal ZMK keymap for the MoErgo Glove80 (Glorious Engrammer, QWERTY-only) and the tools that build, flash, and visualize it.

## Keyboard

**Position**:
One of the 80 physical keys, named by hand, column, and row (`LH_C3R4`) or by thumb slot (`RH_T4`).
_Avoid_: key index, keycode

**Thumb key**:
One of the six thumb-cluster Positions on each hand, numbered T1–T6; left T4 and right T4 are different keys.
_Avoid_: thumb button

**Layer**:
A named set of bindings for all 80 Positions, stacked above QWERTY while active.
_Avoid_: keymap (for a single layer), mode

**Layer activation**:
How a Layer becomes active: holding a Thumb key, toggling, a combo, or a conditional rule over other Layers.
_Avoid_: layer key, layer switch

## Visualizer

**Output**:
What the host receives from a key press: a character (`"`, `Í`, `₿`), a string (`..`), or a named action (Volume Up, Copy).
_Avoid_: result, symbol

**Recipe**:
One complete way to produce an Output: the Layer activation needed, the modifiers held, and the Position (or combo) pressed.
_Avoid_: shortcut, path, way

**Recipe kind**:
How the Recipe produces its Output: direct, shifted, layer, combo, or macro.
_Avoid_: type, category
