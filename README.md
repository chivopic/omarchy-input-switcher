# Input Switch

A small Omarchy bar widget for switching between Chinese (Fcitx5 + Rime) and English (`keyboard-us`). Click to toggle, right-click to choose a language, and keep your existing Fcitx5 shortcuts.

[简体中文](README.zh-CN.md) · [Usage & setup](docs/USAGE.md) · [Development](docs/DEVELOPMENT.md)

## Install

```bash
omarchy plugin add https://github.com/chivopic/omarchy-input-switcher --enable
```

Requires Omarchy's Quickshell plugin system, Python 3 with `python-dbus`, and Fcitx5 with `rime` and `keyboard-us` in the same input-method group. See [full requirements and other install options](docs/USAGE.md#requirements-and-installation).

## Chinese ↔ English

![Two language panel states rendered from the plugin's QML component: Chinese with Rime and rime_ice, and English with the US keyboard](docs/assets/language-panels.png)

*Actual QML component previews with sample states and a sample theme; these are not desktop screenshots. The installed widget follows your Omarchy theme.*

## What it does

- Left-click toggles; right-click opens direct Chinese/English choices; middle-click checks the connection.
- Chinese is confirmed through Rime's mode API; English explicitly selects `keyboard-us`. The badge reflects observed state, not just the selected engine.
- Existing Fcitx5 shortcuts continue to work. A shared 500 ms poll picks up changes made outside the widget.
- The short confirmation OSD does not take keyboard focus. All bar instances share one Python D-Bus service.
- Unknown Rime mode displays `RIME`; a disconnected service displays `!`.

The bridge reads engine and mode metadata only. It does not read typed text, candidate words or window titles. No pip install or Node runtime is needed to run the plugin. See the [development guide](docs/DEVELOPMENT.md#state-flow) for the request and verification flow.

## Scope

This version supports manual switching. Per-application rules and editor-mode integration are not implemented. Multi-screen sharing is implemented, but dual-monitor hardware and individual GTK, Qt, Chromium and Electron input flows have not all been validated.

For precise Chinese-mode detection, the running `org.fcitx.Fcitx.Rime1` interface must provide `GetCurrentSchema`, `IsAsciiMode` and `SetAsciiMode`. The plugin detects these capabilities at runtime and will not guess when mode is unknown. See [troubleshooting](docs/USAGE.md#troubleshooting) and [validation notes](VALIDATION.md).

## Project

[MIT License](LICENSE) · [Report an issue](https://github.com/chivopic/omarchy-input-switcher/issues) · [Development guide](docs/DEVELOPMENT.md)
