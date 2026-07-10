# NvimPad

A lightweight GTK3 A floating multi-tab plain-text scratchpad for Hyprland/arch linux with a Neovim-inspired Catppuccin Mocha interface for taking qicknotes.

<img width="649" height="426" alt="Image" src="https://github.com/user-attachments/assets/15d5facb-2bd7-4bbf-a56b-ee1c9883a9be" />

## Requirements

- Python 3
- GTK3 Python bindings (`python-gobject` on Arch, `python3-gi` on Debian/Ubuntu)
- A monospace font; JetBrains Mono Nerd Font is recommended

## Install

From this project directory, run:

```bash
bash ' install-NvimPad.sh'
```

The installer copies the application to `~/.local/bin/nvimpad`, creates a
desktop entry, and can add the Hyprland rule and keybinding.

To update an existing installation after editing the source, run the installer
again.

## Hyprland binding

Use only one binding in your Hyprland configuration:

```ini
bind = SUPER, N, exec, nvimpad
windowrule = float on, match:class nvimpad
windowrule = size 640 420, match:class nvimpad
windowrule = center on, match:class nvimpad
```

Duplicate `SUPER + N` bindings launch more than one window.

## Shortcuts

| Shortcut | Action |
| --- | --- |
| `Win+N`  | launch the nvimpad |
| `Ctrl+S` | Save the active note now |
| `Ctrl+Q` | Save all notes and close |
| `Ctrl+T` | Create a tab |
| `Ctrl+W` | Close the active tab |



## Data storage

All data stays locally under:

```text
~/.local/share/nvimpad/
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
python3 NvimPad.py
```

Basic syntax checks:

```bash
python3 -m py_compile NvimPad.py
bash -n ' install-NvimPad.sh'
```
