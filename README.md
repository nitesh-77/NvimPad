# NvimPad

A lightweight GTK3 scratchpad for Hyprland/Omarchy with a Neovim-inspired
Catppuccin Mocha interface. for qicknotes


## Requirements

- Python 3
- GTK3 Python bindings (`python-gobject` on Arch, `python3-gi` on Debian/Ubuntu)
- A monospace font; JetBrains Mono Nerd Font is recommended

## Install

From this project directory, run:

```bash
bash ' install-scratchpad.sh'
```

The installer copies the application to `~/.local/bin/scratchpad`, creates a
desktop entry, and can add the Hyprland rule and keybinding.

To update an existing installation after editing the source, run the installer
again.

## Hyprland binding

Use only one binding in your Hyprland configuration:

```ini
bind = SUPER, N, exec, scratchpad
windowrule = float on, match:class scratchpad
windowrule = size 640 420, match:class scratchpad
windowrule = center on, match:class scratchpad
```

Duplicate `SUPER + N` bindings launch more than one window.

## Shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl+S` | Save the active note now |
| `Ctrl+Q` | Save all notes and close |
| `Ctrl+T` | Create a tab |
| `Ctrl+W` | Close the active tab |



## Data storage

All data stays locally under:

```text
~/.local/share/scratchpad/
├── notes/       # One UTF-8 .txt file per note
└── state.json   # Open-tab order and active tab
```

Each new note receives a unique ID, preventing an old note from being
overwritten after a restart. If an earlier version created duplicate entries in
`state.json`, the current version loads each unique note once and rewrites a
clean state file when it closes.

## Development

Run directly from the repository with:

```bash
python3 scratchpad.py
```

Basic syntax checks:

```bash
python3 -m py_compile scratchpad.py
bash -n ' install-scratchpad.sh'
```
