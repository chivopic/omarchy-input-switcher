# Usage and setup

[Back to README](../README.md) · [简体中文](USAGE.zh-CN.md)

## Requirements and installation

Input Switch is a Quickshell bar-widget and service plugin. It needs Omarchy's Quickshell plugin system, Python 3 with `python-dbus`, and a running Fcitx5 with `rime` and `keyboard-us` in the same input-method group.

For precise Chinese-mode switching, the running `org.fcitx.Fcitx.Rime1` interface must expose `GetCurrentSchema`, `IsAsciiMode` and `SetAsciiMode`. The plugin checks support at runtime; another distribution may expose different capabilities even with the same package versions.

Tested on Omarchy **4.0.6-1**, Quickshell **0.3.2.r7.g2b4501a-1**, Fcitx5 **5.1.23-1**, and fcitx5-rime **5.1.16-1**.

Install missing packages only:

```bash
omarchy pkg add python-dbus fcitx5 fcitx5-rime
```

### Omarchy plugin manager

Choose **one** installation method below. Do not use the plugin manager and local checkout installer for the same plugin at once.

```bash
omarchy plugin add https://github.com/chivopic/omarchy-input-switcher --enable
```

The badge is added to the center section of the bar. To move it:

```bash
omarchy bar move io.github.chivopic.input-switch --section right
```

Update or remove a plugin-manager installation:

```bash
omarchy plugin update io.github.chivopic.input-switch
omarchy plugin remove io.github.chivopic.input-switch
```

### Local checkout

```bash
git clone https://github.com/chivopic/omarchy-input-switcher.git
cd omarchy-input-switcher
./scripts/input-switch --doctor
./scripts/install --dry-run
./scripts/install
```

The local installer copies the plugin to `~/.config/omarchy/plugins/io.github.chivopic.input-switch/` and inserts its badge after the existing keyboard-layout widget. It preserves other settings and makes a backup before each change. Re-run `./scripts/install` after editing; use `./scripts/uninstall` to remove this installation.

Backups live in `~/.config/omarchy/input-switch-backups/`. The installer refuses to overwrite a same-name checkout it does not manage. It does not edit `/usr/share/omarchy/`, Hyprland keybindings or your Rime scheme.

## Controls and state

| Action | Result |
| --- | --- |
| Left-click the badge | Toggle Chinese / English |
| Right-click the badge | Open language panel |
| Middle-click the badge | Check the connection again |
| Choose 中文 / English in the panel | Close panel, then apply the language |
| Use an existing Fcitx5 shortcut | Existing behavior remains; badge follows the result |

Chinese selects Rime and clears `ascii_mode`; English explicitly selects `keyboard-us`. The bridge verifies the resulting state through Fcitx5 and Rime. Rime alone does not prove Chinese mode.

| Badge | Meaning |
| :---: | --- |
| `中` | Confirmed Rime Chinese mode |
| `EN` | Confirmed English input, including Rime's internal English mode |
| `RIME` | Rime selected, internal mode not confirmed |
| `…` | Request in progress |
| `!` | Input service unavailable |

The plugin registers no extra shortcuts by default. `EN` describes input mode, not Caps Lock.

## Options

Set options on this plugin's bar entry in `~/.config/omarchy/shell.json`:

```json
{
  "id": "io.github.chivopic.input-switch",
  "showOsd": true,
  "osdDuration": 700
}
```

`osdDuration` is in milliseconds and clamped to 250–3000ms. Set `showOsd` to `false` for a bar-only experience. The OSD is focus-free and does not block clicks.

## CLI and shell IPC

From a local checkout:

```bash
./scripts/input-switch --status
./scripts/input-switch --set zh
./scripts/input-switch --set en
./scripts/input-switch --toggle
```

With the plugin enabled:

```bash
omarchy-shell input-switch status
omarchy-shell input-switch set zh
omarchy-shell input-switch set en
omarchy-shell input-switch toggle
omarchy-shell shell toggle io.github.chivopic.input-switch
```

IPC returns `queued` when a request is accepted and `busy` when another request is in progress. Check `status` for final `state`, `pending` and `error` fields; acceptance does not confirm the switch.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `!` badge | Run `./scripts/input-switch --doctor` or inspect `omarchy-shell input-switch status`. Check Fcitx5 is running in the same desktop session. |
| `RIME`, Chinese unavailable | Check `preciseRime` in status. Your Rime build may not expose the precise mode API; the plugin will not guess. |
| Switch not confirmed | Focus an input field and retry. Missing context or Rime maintenance can make the submode unreadable. |
| External shortcut updates badge slightly later | The shared fallback poll runs every 500ms; this is separate from request verification. |

## Scope and validation

The plugin supports manual switching. Per-application rules, application-specific memory and editor-mode integration are not implemented. Multi-screen sharing is implemented, but dual-monitor hardware and every GTK/Qt/Chromium/Electron input-field flow have not been individually validated. See [validation notes](../VALIDATION.md) for what has actually been checked.
