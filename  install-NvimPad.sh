#!/usr/bin/env bash
# install-scratchpad.sh — Sets up the Neovim-aesthetic scratchpad for Omarchy/Hyprland

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
NOTES_DIR="$HOME/.local/share/scratchpad"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  scratchpad — Neovim-aesthetic quick notes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Check deps
echo ""
echo "[1/4] Checking dependencies..."

if ! python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk" 2>/dev/null; then
    echo "  → Installing python3-gi (GTK bindings)..."
    sudo pacman -S --noconfirm python-gobject gtk3 2>/dev/null || \
    sudo apt-get install -y python3-gi gir1.2-gtk-3.0 2>/dev/null || \
    echo "  ✗ Please install python-gobject / python3-gi manually"
else
    echo "  ✓ python3-gi (GTK) available"
fi

# Check for a good monospace font
if fc-list | grep -qi "JetBrains\|Fira Code\|Cascadia\|Hack"; then
    echo "  ✓ Monospace font found"
else
    echo "  ⚠ No Nerd Font detected — install JetBrainsMono Nerd Font for best look:"
    echo "    yay -S ttf-jetbrains-mono-nerd"
fi

# 2. Install script
echo ""
echo "[2/4] Installing scratchpad..."
mkdir -p "$INSTALL_DIR"
cp "$SCRIPT_DIR/scratchpad.py" "$INSTALL_DIR/scratchpad"
chmod +x "$INSTALL_DIR/scratchpad"
echo "  ✓ Installed to $INSTALL_DIR/scratchpad"

# 3. Create notes dir
mkdir -p "$NOTES_DIR"
echo "  ✓ Notes directory: $NOTES_DIR/notes.txt"

# 4. Desktop entry (for rofi/wofi launcher)
echo ""
echo "[3/4] Creating desktop entry..."
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/scratchpad.desktop" << 'EOF'
[Desktop Entry]
Name=Scratchpad
Comment=Quick notes with Neovim aesthetics
Exec=scratchpad
Icon=text-editor
Type=Application
Categories=Utility;TextEditor;
Keywords=notes;scratchpad;quick;
StartupNotify=false
EOF
echo "  ✓ Desktop entry created (searchable in rofi/wofi)"

# 5. Hyprland keybind instructions
echo ""
echo "[4/4] Hyprland keybind setup..."
echo ""
echo "  Add this to your ~/.config/hypr/hyprland.conf:"
echo ""
echo "  ┌─────────────────────────────────────────────────────┐"
echo "  │  # Scratchpad quick notes                           │"
echo "  │  bind = SUPER, N, exec, scratchpad                  │"
echo "  │                                                     │"
echo "  │  # Float the window automatically                   │"
echo "  │  windowrule = float on, match:class scratchpad         │"
echo "  │  windowrule = size 640 420, match:class scratchpad  │"
echo "  │  windowrule = center on, match:class scratchpad        │"
echo "  └─────────────────────────────────────────────────────┘"
echo ""
echo "  Or use Omarchy's binding style:"
echo "  bind = \$mainMod, N, exec, scratchpad"
echo ""

# Check if hyprland.conf exists and offer to append
HYPR_CONF="$HOME/.config/hypr/hyprland.conf"
if [ -f "$HYPR_CONF" ]; then
    echo -n "  Auto-add keybind to hyprland.conf? [y/N] "
    read -r answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        cat >> "$HYPR_CONF" << 'EOF'

# Scratchpad quick notes (Neovim aesthetic)
bind = SUPER, N, exec, scratchpad
windowrule = float on, match:class scratchpad
windowrule = size 640 420, match:class scratchpad
windowrule = center on, match:class scratchpad
EOF
        echo "  ✓ Added to hyprland.conf — press Super+N to open"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✓ Done! Run: scratchpad"
echo ""
echo "  Keybinds inside the app:"
echo "    Ctrl+S   force save"
echo "    Ctrl+Q   close (auto-saves)"
echo "    –        minimize button (or Super+H in Hyprland)"
echo "    Drag     move window by title bar"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"