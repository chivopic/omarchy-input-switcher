# Development guide

## Repository map

```text
BarWidget.qml           Bar badge and delayed panel selection
InputPanel.qml          Native Omarchy language panel
Osd.qml                 Focus-free, click-through language feedback
Service.qml             Shared process, state, recovery and IPC
InputModel.js           Display labels and descriptions
bridge/input_bridge.py  Fcitx5 / Rime control and NDJSON protocol
scripts/                Local install, uninstall and standalone CLI
tests/                  Model, backend, installer and desktop tests
docs/                   Public images and reproducible QML previews
```

## Checks

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
node tests/model.test.cjs
omarchy plugin validate .
bash -n scripts/install scripts/uninstall scripts/input-switch
```

Unit tests use a fake D-Bus transport and temporary installation roots. They do not change the desktop. Node is a development-only dependency for the display-model assertions.

### Wayland component loading

```bash
python3 tests/run_qml_smoke.py
```

This requires the installed Omarchy UI kit and a running Hyprland/Wayland session. It loads the real service and UI in an independent, invisible Quickshell instance. UI actions use a simulated service, and the real service’s OSD is disabled for the test.

### Real desktop round trips

With no uncommitted input composition, run:

```bash
python3 tests/desktop_roundtrip.py --allow-switch

# Also check the installed plugin’s shared IPC service:
python3 tests/desktop_roundtrip.py --allow-switch --via-shell
```

These explicitly opted-in tests briefly change the real input method, check Rime-internal English and external-change polling, then restore the original engine, activation state and ASCII mode in `finally`. They do not inject text into applications. See [VALIDATION.md](../VALIDATION.md) for the distinction between mode/API checks and application typing tests.

## Bridge protocol

The bridge accepts UTF-8 NDJSON on stdin and emits NDJSON on stdout. Requests are handled serially. A request needs a string or integer `id`:

```json
{"id":1,"op":"status"}
{"id":2,"op":"set","language":"zh"}
{"id":3,"op":"toggle"}
```

Successful requests publish a confirmed snapshot followed by a result with the matching id:

```json
{"type":"state","backend":"fcitx5","available":true,"engine":"rime","active":true,"asciiMode":false,"effectiveLanguage":"zh","schema":"rime_ice","engines":["keyboard-us","rime"],"preciseRime":true,"error":""}
{"type":"result","id":2,"ok":true}
```

Errors use `ok:false` and an `error` object containing `code` and `message`. A partially applied or unconfirmed switch publishes the actual observable state before reporting failure.

`asciiMode:null` means unknown, not false. Do not infer Chinese from the engine name alone. The backend only claims Chinese after a usable Rime schema and ASCII-mode result are available.

## Reproduce the documentation images

```bash
python3 docs/render-previews.py
```

This uses the actual `InputPanel.qml`, Omarchy’s UI kit, sample states and an explicit sample palette. Quickshell runs with the offscreen software renderer and saves 3× PNG previews into `docs/assets/`. It does not capture the desktop, change the user’s theme or control the actual input method. Some offscreen Qt platforms print harmless window-mask warnings.

The hero is an illustrated overview, and the architecture image is a diagram. Both are editable SVG files. The panel PNGs are real component renders, rather than illustrations of a different UI.

## Local installation lifecycle

`scripts/install` manages copied installations marked by `.install-state.json`. It stages a copy, backs up the current configuration and prior plugin, atomically writes the updated config, and rolls back the plugin directory if the write fails. Updates preserve the existing bar position and options. Uninstall removes only this plugin’s entries.

The installed copy is separate from the development checkout. Run the installer after code changes. For installations created by `omarchy plugin add`, use the Omarchy plugin manager for updates and removal instead.
