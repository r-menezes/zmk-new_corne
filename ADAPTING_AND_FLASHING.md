## Adapting this repository's ZMK configuration and flashing your Eyelash Corne

This document explains, step-by-step, how to adapt the keymap and configuration in this repository for your own needs using a graphical editor (preferred: https://nickcoutsos.github.io/keymap-editor/), how to convert/export those changes into the repository's ZMK keymap format, how to build, and how to flash both halves of the Eyelash Corne.

The instructions assume you're on Linux (zsh) and that this repository is the working repo root. Commands and filenames refer to files in this repo (for example `config/eyelash_corne.keymap` and `boards/arm/eyelash_corne/eyelash_corne.keymap`).

## Quick overview (what you'll do)
- Design your layout visually in keymap-editor.
- Export the JSON or copy the layout labels.
- Convert each key into the repository's ZMK `bindings` block syntax.
- Edit `config/eyelash_corne.keymap` (or `boards/arm/eyelash_corne/eyelash_corne.keymap`) to add/replace layers.
- Build with West/Zephyr.
- Flash the left and right halves.

## 1) Prerequisites

- A working ZMK build environment. At minimum you'll need:
  - Python 3 and pip
  - west (Zephyr meta-tool)
  - Zephyr SDK and the GNU Arm toolchain (or the toolchain variant you prefer)
  - dfu-util or nrfjprog (depending on your board bootloader and programmer)

Refer to the official ZMK docs for the exact environment setup for your OS: https://zmk.dev/docs (and Zephyr docs: https://docs.zephyrproject.org). Below are common Linux commands to install basic tools — adapt to your distro.

Example (Ubuntu/Debian-like minimal setup):

```bash
# install packages (may require sudo)
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv cmake ninja-build gperf dfu-util device-tree-compiler
python3 -m pip install --user west
```

Important: installing Zephyr SDK and toolchains is more involved — follow Zephyr and ZMK setup docs. Once Zephyr is available and `west` works, you can build.

## 2) Understand this repo's keymap format

This project already contains ZMK keymap files. See these two important files:

- `boards/arm/eyelash_corne/eyelash_corne.keymap` — board-level keymap + behaviors; good as a reference and examples of advanced bindings (tap-dance, rgb, bt selectors).
- `config/eyelash_corne.keymap` — configuration-level keymap overrides and lux settings.

Open either file to see how layers are written. The important pattern is the `keymap` node with `bindings = < ... >;`. Each layer is a block of key tokens arranged visually across rows. Example tokens (from the repo) include:

- `&kp Q` — press Key Q
- `&kp SPACE` — press Space
- `&mo 1` — momentary layer switch to layer 1 while held
- `&lt 3 SPACE` — hold for layer 3, tap for space (see repo examples)
- `&td0` — tap-dance behavior (defined in the same file)
- `&bt BT_SEL 0` — Bluetooth profile selection

The `bindings` block is a whitespace-separated list of key tokens arranged row-by-row and visually aligned in the file. When you convert from a graphical layout, preserve that row-major ordering.

## 3) Designing your layout in the keymap-editor (nickcoutsos)

1. Open https://nickcoutsos.github.io/keymap-editor/ in your browser.
2. Choose or create a custom layout that matches your Eyelash Corne physical layout (split keyboard, two halves, usually 3x6 main keys plus thumb cluster). The editor supports adding rows and resizing keys.
3. Build the left-half layout first (or build both halves as separate canvases). Keep a consistent ordering: left half rows left-to-right, top-to-bottom. The repository's `bindings` follow this order.
4. Fill each key with the desired label (A, B, ENTER, LT(3, SPACE), etc.) or a QMK-style keycode. The keymap-editor uses a "   ,  " label system — it's easiest to maintain simple labels and then convert them to ZMK tokens (see next section).
5. When satisfied, export or copy the layout. The editor can export JSON; save that JSON as `my_layout.json` for reference.

Note: keymap-editor may use QMK-style keycode names (KC_A, KC_ENT). You will map those to ZMK tokens like `&kp A` or `&kp ENTER`.

## 4) Converting keymap-editor layouts to ZMK `bindings` format

You will turn your visual layout (rows and keys) into a `bindings` list in a layer block. Follow these steps:

1. Decide which file to edit. For local configuration, edit `config/eyelash_corne.keymap`. If you need board-specific functionality (behaviors, sensors), edit the board keymap at `boards/arm/eyelash_corne/eyelash_corne.keymap`.
2. For each layer you designed in the editor, create a block like this inside the `keymap` node:

```dts
layer_name {
    display-name = "My Layer";
    bindings = <
        &kp TAB &kp Q &kp W &kp E ...   (and so on, row by row)
    >;
};
```

3. Mapping labels to ZMK tokens (common conversions)

- Printable letters/digits: label `A` → `&kp A`
- Space: `&kp SPACE`
- Enter/Return: `&kp ENTER` (or `&kp RET` usage exists in some example files)
- Backspace: `&kp BSPC`
- Tab: `&kp TAB`
- Escape: `&kp ESC`
- Arrow keys: `&kp UP`, `&kp DOWN`, `&kp LEFT`, `&kp RIGHT`
- Numbers: `&kp N1`, `&kp N2`, ... (examples in repo use `&kp N1` etc.)
- Symbols: `&kp EXCL` (`!`), `&kp AT` (`@`), `&kp HASH` (`#`), `&kp DLLR` (`$`), etc. (see repo's SYMBOL layer for examples)
- Momentary layer: `&mo <layer_index>` — e.g. `&mo 1`
- Layer tap (tap a key to send code, hold to switch): `&lt <layer_index> <keycode>` e.g. `&lt 3 SPACE` (tap space, hold to go to layer 3) — the repo uses this pattern.
- Tap-dance: use the named behavior `&td0` (behavior defined earlier in file). If you add a new tap-dance, define a behavior in the file's `behaviors` node.
- Bluetooth selection: `&bt BT_SEL <n>` — chooses stored BLE pairing index.

4. Keep the same visual spacing for readability. The `bindings` block is a linear sequence: left-to-right across the top row, then the second row, etc. Make sure the number of tokens per row matches the physical positions.

5. Example conversion snippet (small excerpt):

From your editor row: [TAB] [Q] [W] [E] [R] [T]  ... [UP] [Y] [U] [I] [O] [P] [BSPC]

Becomes in the `bindings` block:

```dts
&kp TAB    &kp Q  &kp W      &kp E     &kp R  &kp T                              &kp UP                &kp Y        &kp U  &kp I      &kp O    &kp P     &kp BSPC
```

6. Layer numbering: layers in the file (example: `default_layer`, `lower_layer`, `raise_layer`, `layer_3`) commonly correspond to numeric indices when used with `&mo` or `&lt`. The repository already orders layers; when you add new layers, keep them in order. Use `&mo 1` to call the second layer (index 1) if `default_layer` is index 0.

7. Special elements and sensors

- If your layout uses encoders, RGB, or pointing devices, match the `sensor-bindings` values in the layer blocks (see examples in `config/eyelash_corne.keymap`).
- Combos: if you want combos (multiple keys together to produce an action), add `combos` definitions in the top `/` node and set `key-positions`. To get a key's position number, count tokens in the `bindings` block left-to-right, top-to-bottom (starting at 0). Example in this repo: `combos { softoff { key-positions = <1 15 29>; bindings = <&soft_off>; }; };` — choose positions corresponding to the 3 keys you want.

## 5) Edit files in this repo

1. Make a branch for your changes:

```bash
git checkout -b my/keymap-changes
```

2. Back up the current config file(s) before you change them (recommended):

```bash
cp config/eyelash_corne.keymap config/eyelash_corne.keymap.bak
cp boards/arm/eyelash_corne/eyelash_corne.keymap boards/arm/eyelash_corne/eyelash_corne.keymap.bak
```

3. Edit `config/eyelash_corne.keymap` (or the board file) with your new `bindings` blocks. You can use any editor (vim, code, etc.). Keep your layers named clearly and use the examples in the repo as templates.

4. Save changes and run a quick textual sanity check: make sure every `bindings = <` block ends with `>;` and there are no stray tokens.

## 6) Build the firmware

Before building, check the board name(s) exposed by this repo. The boards folder includes `eyelash_corne_left_defconfig` and `eyelash_corne_right_defconfig`. Inspect `boards/arm/eyelash_corne/eyelash_corne.zmk.yml` to confirm the ZMK board identifiers that West uses (example names might be `eyelash_corne_left` and `eyelash_corne_right`).

Typical build steps (from repo root):

```bash
# initialize west and update submodules (only if you do a fresh checkout)
west init -l .
west update

# build left half (use the correct -b name per the board YAML; adapt if different)
west build -b eyelash_corne_left -s app -d build-left

# build right half
west build -b eyelash_corne_right -s app -d build-right
```

If the repo expects you to build from a top-level `app` directory (common in ZMK module setups), the `-s app` argument points the build at the application sources. If your layout uses a custom top-level path, adapt the `-s` argument accordingly. If West/Zephyr errors, read the error output — most issues are missing Zephyr SDK/toolchain or Python deps.

## 7) Flashing the board

There are several flashing workflows depending on how your Corne bootloader is set up. Try the simpler `west flash` first (it uses the same transport as your build config).

1. Using west (preferred if configured):

```bash
# flash left (from the build directory or add -d build-left)
west flash -d build-left
# flash right
west flash -d build-right
```

2. If your board needs a raw hex file flashed with nrfjprog or dfu-util:

```bash
# find the firmware file (example path)
ls build-left/zephyr/zephyr.bin  build-left/zephyr/zephyr.hex
# nrfjprog (Nordic programmers)
nrfjprog --program build-left/zephyr/zephyr.hex --chiperase --verify
nrfjprog --reset
# or dfu-util if the board exposes USB DFU
dfu-util -d VID:PID -a 0 -D build-left/zephyr/zephyr.bin
```

Note: the exact flashing command depends on your bootloader (BSD bootloader, USB DFU, or using a J-Link/nrfjprog). If you have a USB bootloader (mass storage), you might be able to drag-and-drop the `.bin`/`.uf2` to the device when it is in DFU mode. Check your keyboard vendor instructions.

3. Putting the board into bootloader mode

- Many split keyboards require you to press and hold a physical reset button or a specific key combination while connecting to USB to enter DFU. For the Eyelash Corne this repo documents a soft-off function and a reset switch (see README and the `soft_off` combo). Use the physical reset or consult the board PCB to find the reset button.

## 8) Flashing notes for split keyboards (left/right halves)

- Build and flash each half using its appropriate defconfig/board name. Typically the left and right halves run independent firmwares.
- If one half acts as the central master you must ensure the correct config defines the same dongle/host behavior.

## 9) Testing and debug

- After flashing, plug the keyboard to a host and test each key, layer and special function.
- If something doesn't work: rebuild with more verbose logs or enable `CONFIG_LOG=y` in the build config to get debug output.
- If keys are swapped or rows misaligned: re-check the token order in your `bindings` and ensure row/column order matches the physical PCB.

## 10) Useful examples from this repo (copy and adapt)

- Look at `config/eyelash_corne.keymap` which includes:
  - examples of `&lt 3 SPACE` (tap for space, hold for layer 3)
  - RGB encoder sensor-binding examples
  - combos defined in the `/` node including `key-positions` mapping

- The `boards/arm/eyelash_corne/eyelash_corne.keymap` file shows multiple layers named `default_layer`, `lower_layer`, `raise_layer`, `layer_3`. Use these as templates.

## 11) Troubleshooting common issues

- Build fails: probably missing Zephyr SDK/toolchain or west submodules. Re-run `west update` and read errors.
- Flash fails: ensure you have permissions for the USB device (run as root or add udev rules). Check if the board requires a programmer like `nrfjprog`.
- Layers don't register: check that your `&mo` or `&lt` use the correct layer index and that your layers are declared in the file in the order you expect.
- Combos or key-position off by one: count tokens left-to-right, top-to-bottom. If combos are not firing, double-check positions and that combo definitions are in the root `/` node.

## 12) Next steps and improvements

- Add multiple keymap files for different users or languages and script the conversion from keymap-editor JSON -> ZMK `bindings` if you plan to iterate often.
- Add comments in your keymap file to document which token corresponds to each physical key (makes counting easier for combos).
- Version control: keep your modified `config/*.keymap` in a branch, and consider creating a small conversion script to quickly map JSON exports to ZMK tokens.

## Appendix A — Example full layer block (copy/paste and adapt)

```dts
my_layer {
  display-name = "MyLayer";
  bindings = <
    &kp TAB    &kp Q  &kp W      &kp E     &kp R  &kp T    &kp UP    &kp Y    &kp U  &kp I  &kp O  &kp P  &kp BSPC
    &td0       &kp A  &kp S      &kp D     &kp F  &kp G    &kp LEFT  &kp ENTER  &kp RIGHT  &kp H  &kp J  &kp K  &kp L  &kp SEMI  &kp SQT
    &kp LCTRL  &kp Z  &kp X      &kp C     &kp V  &kp B    &kp SPACE              &kp DOWN  &kp N  &kp M  &kp COMMA  &kp DOT  &kp FSLH  &kp ESC
                      &kp LGUI  &mo 1  &lt 3 SPACE                &lt 3 ENTER  &mo 2  &kp RALT
  >;
  sensor-bindings = <&inc_dec_kp C_VOLUME_UP C_VOLUME_DOWN>;
};
```

## Appendix B — Where to look in this repo

- `README.md` (top-level) — general project info
- `boards/arm/eyelash_corne/eyelash_corne.keymap` — board-level keymap examples
- `config/eyelash_corne.keymap` — config-level keymap (use this for local changes)
- `boards/arm/eyelash_corne/eyelash_corne.zmk.yml` — board metadata and build target names (inspect this file to find exact `-b` names for west)

---

If you want, I can:

- convert a keymap-editor JSON export to a ready-to-paste `bindings` block for you (upload your JSON and I will produce the dts block), or
- generate a small conversion script in Python to automate the mapping between editor JSON and ZMK tokens.

Tell me which half layout (left/right) you want converted first or upload your keymap-editor JSON and I'll create the appropriate `bindings` block ready to paste into `config/eyelash_corne.keymap`.
