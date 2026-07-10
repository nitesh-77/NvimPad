#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import os, json, uuid

# Paths
DATA_DIR   = os.path.expanduser("~/.local/share/scratchpad")
NOTES_DIR  = os.path.join(DATA_DIR, "notes")
STATE_FILE = os.path.join(DATA_DIR, "state.json")
DEBOUNCE   = 400  # ms

# Catppuccin Mocha palette
C = {
    "base":    "#1e1e2e",
    "mantle":  "#181825",
    "surface": "#313244",
    "overlay": "#45475a",
    "muted":   "#6c7086",
    "text":    "#cdd6f4",
    "green":   "#a6e3a1",
    "blue":    "#89b4fa",
    "yellow":  "#f9e2af",
    "red":     "#f38ba8",
    "mauve":   "#cba6f7",
}

CSS = f"""
* {{
    font-family: "JetBrainsMono Nerd Font", "JetBrains Mono", "Fira Code", monospace;
}}
window, .root {{
    background-color: {C['base']};
}}

/* ── Title bar ── */
.titlebar {{
    background-color: {C['mantle']};
    border-bottom: 1px solid {C['overlay']};
    padding: 5px 10px;
}}
.app-name {{
    color: {C['text']};
    font-size: 13px;
    font-weight: bold;
}}
.app-path {{
    color: {C['muted']};
    font-size: 10px;
}}
.wm-btn {{
    background: transparent;
    border: 1px solid {C['overlay']};
    color: {C['muted']};
    font-size: 12px;
    padding: 1px 7px;
    border-radius: 2px;
    min-height: 0;
    min-width: 0;
}}
.wm-btn:hover {{
    background-color: {C['surface']};
    color: {C['text']};
}}
.wm-btn-close {{
    border-color: {C['red']};
    color: {C['red']};
}}
.wm-btn-close:hover {{
    background-color: {C['red']};
    color: {C['base']};
}}

/* ── Tab bar ── */
.tabbar {{
    background-color: {C['mantle']};
    border-bottom: 1px solid {C['overlay']};
    padding: 0 4px;
}}
.tab-btn {{
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    border-radius: 0;
    color: {C['muted']};
    font-size: 12px;
    padding: 4px 10px 3px 10px;
    min-height: 0;
    min-width: 0;
}}
.tab-btn:hover {{
    color: {C['text']};
    background-color: {C['surface']};
}}
.tab-btn-active {{
    color: {C['text']};
    border-bottom-color: {C['green']};
}}
.tab-close {{
    background: transparent;
    border: none;
    color: {C['muted']};
    font-size: 10px;
    padding: 2px 4px;
    min-height: 0;
    min-width: 0;
    border-radius: 2px;
}}
.tab-close:hover {{
    background-color: {C['red']};
    color: {C['base']};
}}
.tab-add {{
    background: transparent;
    border: none;
    color: {C['muted']};
    font-size: 14px;
    padding: 2px 8px;
    min-height: 0;
    min-width: 0;
}}
.tab-add:hover {{
    color: {C['green']};
}}

/* ── Editor ── */
.line-numbers {{
    background-color: {C['base']};
    color: {C['muted']};
    font-size: 14px;
    padding: 14px 6px;
    border: none;
}}
.line-numbers text {{
    background-color: {C['base']};
    color: {C['muted']};
}}
.gutter-sep {{
    background-color: {C['overlay']};
    min-width: 1px;
}}
textview {{
    background-color: {C['base']};
    color: {C['text']};
    font-size: 14px;
    padding: 14px 18px 14px 10px;
    caret-color: {C['green']};
}}
textview text {{
    background-color: {C['base']};
    color: {C['text']};
}}
textview text selection {{
    background-color: {C['surface']};
    color: {C['text']};
}}
scrolledwindow {{
    background-color: {C['base']};
    border: none;
}}
scrollbar {{
    background-color: {C['mantle']};
    border: none;
}}
scrollbar slider {{
    background-color: {C['overlay']};
    border-radius: 4px;
    min-width: 4px;
    min-height: 4px;
}}
scrollbar slider:hover {{
    background-color: {C['muted']};
}}

/* ── Status bar ── */
.statusbar {{
    background-color: {C['mantle']};
    border-top: 1px solid {C['overlay']};
    padding: 3px 10px;
}}
.mode {{
    background-color: {C['green']};
    color: {C['base']};
    font-size: 11px;
    font-weight: bold;
    padding: 1px 7px;
    border-radius: 2px;
}}
.status-file {{
    color: {C['blue']};
    font-size: 11px;
    padding: 0 6px;
}}
.status-saved {{
    color: {C['green']};
    font-size: 11px;
}}
.status-unsaved {{
    color: {C['yellow']};
    font-size: 11px;
}}
.status-pos {{
    color: {C['muted']};
    font-size: 11px;
    padding: 0 6px;
}}
"""


def first_line(text):
    """Return first non-empty line, stripped, max 24 chars."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:24]
    return "untitled"


def note_path(note_id):
    return os.path.join(NOTES_DIR, f"{note_id}.txt")


class Tab:
    """Holds per-tab state: id, buffer, save timer, modified flag."""

    def __init__(self, note_id=None, content=""):
        if note_id is None:
            # A process-local counter restarts at zero after restoring tabs,
            # which can overwrite a previously saved note.
            note_id = f"note-{uuid.uuid4().hex}"
        self.id = note_id
        self.save_timer = None
        self.modified = False

        self.buf = Gtk.TextBuffer()
        self.buf.set_text(content)
        self.buf.place_cursor(self.buf.get_end_iter())

    @property
    def text(self):
        return self.buf.get_text(self.buf.get_start_iter(), self.buf.get_end_iter(), False)

    @property
    def label(self):
        return first_line(self.text)

    def save(self):
        try:
            with open(note_path(self.id), "w", encoding="utf-8") as f:
                f.write(self.text)
            self.modified = False
            return True
        except Exception:
            return False

    def delete_file(self):
        p = note_path(self.id)
        if os.path.exists(p):
            os.remove(p)


class Scratchpad(Gtk.Window):
    def __init__(self):
        super().__init__(title="scratchpad")
        self._tabs = []          # list of Tab
        self._active = None      # current Tab
        self._drag = None        # drag state for title bar

        os.makedirs(NOTES_DIR, exist_ok=True)

        self._setup_window()
        self._apply_css()
        self._build_ui()
        self._restore_state()

        if not self._tabs:
            self._new_tab()

    # Window setup 

    def _setup_window(self):
        self.set_default_size(660, 440)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_decorated(False)
        self.connect("delete-event", self._on_quit)
        self.connect("key-press-event", self._on_key)

    def _apply_css(self):
        p = Gtk.CssProvider()
        p.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), p,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    # UI construction 

    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.get_style_context().add_class("root")
        self.add(root)

        root.pack_start(self._build_titlebar(), False, False, 0)
        root.pack_start(self._build_tabbar(),   False, False, 0)

        # Editor stack — one ScrolledWindow per tab, shown/hidden
        self._stack = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._stack.set_vexpand(True)
        root.pack_start(self._stack, True, True, 0)

        root.pack_start(self._build_statusbar(), False, False, 0)

    def _build_titlebar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        bar.get_style_context().add_class("titlebar")

        # Draggable area
        drag = Gtk.EventBox()
        drag.set_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON1_MOTION_MASK)
        drag.connect("button-press-event", self._drag_start)
        drag.connect("motion-notify-event", self._drag_move)
        drag.set_hexpand(True)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        name = Gtk.Label(label=" scratchpad")
        name.get_style_context().add_class("app-name")
        name.set_halign(Gtk.Align.START)
        path = Gtk.Label(label=NOTES_DIR)
        path.get_style_context().add_class("app-path")
        path.set_halign(Gtk.Align.START)
        info.pack_start(name, False, False, 0)
        info.pack_start(path, False, False, 0)
        drag.add(info)

        bar.pack_start(drag, True, True, 0)
        return bar

    def _build_tabbar(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        outer.get_style_context().add_class("tabbar")

        # Scrollable tab list
        self._tabrow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self._tabrow.set_hexpand(True)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        scroll.set_hexpand(True)
        scroll.add(self._tabrow)

        add_btn = Gtk.Button(label="+")
        add_btn.get_style_context().add_class("tab-add")
        add_btn.set_tooltip_text("New tab")
        add_btn.connect("clicked", lambda _: self._new_tab())

        outer.pack_start(scroll,  True,  True,  0)
        outer.pack_start(add_btn, False, False, 0)
        return outer

    def _build_statusbar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        bar.get_style_context().add_class("statusbar")

        self._lbl_mode  = Gtk.Label(label=" INSERT ")
        self._lbl_mode.get_style_context().add_class("mode")

        self._lbl_file  = Gtk.Label(label="")
        self._lbl_file.get_style_context().add_class("status-file")

        self._lbl_save  = Gtk.Label(label="✓ saved")
        self._lbl_save.get_style_context().add_class("status-saved")

        self._lbl_pos   = Gtk.Label(label="1:1")
        self._lbl_pos.get_style_context().add_class("status-pos")

        self._lbl_chars = Gtk.Label(label="0 chars")
        self._lbl_chars.get_style_context().add_class("status-pos")

        bar.pack_start(self._lbl_mode,  False, False, 0)
        bar.pack_start(self._lbl_file,  False, False, 0)
        bar.pack_start(self._lbl_save,  False, False, 0)
        bar.pack_end(self._lbl_chars,   False, False, 0)
        bar.pack_end(self._lbl_pos,     False, False, 2)
        return bar

    # ── Tab management ────────────────────────────────────────────────────────

    def _new_tab(self, note_id=None, content="", switch=True):
        tab = Tab(note_id=note_id, content=content)
        self._tabs.append(tab)

        # Build line-number gutter
        gutter_buf = Gtk.TextBuffer()
        gutter_tv = Gtk.TextView(buffer=gutter_buf)
        gutter_tv.set_editable(False)
        gutter_tv.set_cursor_visible(False)
        gutter_tv.set_wrap_mode(Gtk.WrapMode.NONE)
        gutter_tv.set_left_margin(0)
        gutter_tv.set_right_margin(0)
        # The CSS supplies the shared outer inset. Match the editor's small
        # inner margin so line numbers and text retain the same baseline.
        gutter_tv.set_top_margin(4)
        gutter_tv.set_bottom_margin(4)
        gutter_tv.get_style_context().add_class("line-numbers")
        gutter_tv.set_size_request(44, -1)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.get_style_context().add_class("gutter-sep")

        # Main editor
        tv = Gtk.TextView()
        tv.set_buffer(tab.buf)
        tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        tv.set_left_margin(4)
        tv.set_right_margin(4)
        tv.set_top_margin(4)
        tv.set_bottom_margin(4)
        tv.set_accepts_tab(True)

        # Editor in its own ScrolledWindow (handles scroll + scrollbar)
        editor_sw = Gtk.ScrolledWindow()
        editor_sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        editor_sw.set_vexpand(True)
        editor_sw.set_hexpand(True)
        editor_sw.add(tv)

        # Outer hbox: fixed gutter | sep | scrollable editor
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(gutter_tv, False, False, 0)
        hbox.pack_start(sep,       False, False, 0)
        hbox.pack_start(editor_sw, True,  True,  0)

        # Wrapper (shown/hidden per tab switch)
        sw = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sw.set_vexpand(True)
        sw.pack_start(hbox, True, True, 0)
        sw.show_all()
        sw.set_no_show_all(True)
        sw.hide()

        tab._widget    = sw
        tab._textview  = tv
        tab._editor_sw = editor_sw
        tab._gutter_buf = gutter_buf
        tab._gutter_tv  = gutter_tv
        tab._gutter_line_count = None

        # Sync gutter on text change and scroll
        tab.buf.connect("changed", lambda b, t=tab: self._on_changed(t))
        tab.buf.connect("notify::cursor-position", lambda b, p, t=tab: self._update_pos(t))
        tv.connect("size-allocate",     lambda w, a, t=tab: self._sync_gutter(t))
        editor_sw.get_vadjustment().connect("value-changed", lambda adj, t=tab: self._scroll_gutter(t, adj))

        self._stack.pack_start(sw, True, True, 0)
        self._add_tab_button(tab)
        self._update_gutter(tab)

        if switch:
            self._switch_tab(tab)
        return tab

    # Line number gutter 

    def _update_gutter(self, tab):
        """Rewrite line numbers only when adding/removing a line requires it."""
        n = tab.buf.get_line_count()
        if n == tab._gutter_line_count:
            return

        width = len(str(n))
        lines = '\n'.join(str(i + 1).rjust(width) for i in range(n))
        tab._gutter_buf.set_text(lines)
        tab._gutter_line_count = n
        # Resize gutter width to fit
        char_px = 9  # approx px per char at 14px monospace
        tab._gutter_tv.set_size_request(max(30, width * char_px + 20), -1)

    def _scroll_gutter(self, tab, adj):
        """Keep gutter scroll in sync with editor scroll."""
        # Gutter TextView has its own vadjustment; sync it to editor's
        gadj = tab._gutter_tv.get_vadjustment()
        if gadj and gadj.get_upper() > 0:
            gadj.set_value(min(adj.get_value(), gadj.get_upper() - gadj.get_page_size()))

    def _sync_gutter(self, tab):
        self._update_gutter(tab)

    def _add_tab_button(self, tab):
        """Create a tab's controls once; edits only update its label."""
        box = Gtk.Box(spacing=2)
        label_btn = Gtk.Button(label=tab.label)
        label_btn.get_style_context().add_class("tab-btn")
        label_btn.connect("clicked", lambda _, t=tab: self._switch_tab(t))

        close_btn = Gtk.Button(label="×")
        close_btn.get_style_context().add_class("tab-close")
        close_btn.connect("clicked", lambda _, t=tab: self._close_tab(t))

        box.pack_start(label_btn, False, False, 0)
        box.pack_start(close_btn, False, False, 0)
        self._tabrow.pack_start(box, False, False, 0)
        tab._tab_box = box
        tab._tab_label = label_btn
        box.show_all()

    def _refresh_tab_selection(self):
        for tab in self._tabs:
            context = tab._tab_label.get_style_context()
            if tab is self._active:
                context.add_class("tab-btn-active")
            else:
                context.remove_class("tab-btn-active")

    def _refresh_tab_label(self, tab):
        label = tab.label
        if tab._tab_label.get_label() != label:
            tab._tab_label.set_label(label)

    def _switch_tab(self, tab):
        if self._active and self._active._widget:
            self._active._widget.hide()

        self._active = tab
        tab._widget.show()
        tab._textview.grab_focus()

        self._refresh_tab_selection()
        self._update_status()

    def _close_tab(self, tab):
        if len(self._tabs) == 1:
            # Last tab — just clear it instead of closing
            tab.buf.set_text("")
            return

        idx = self._tabs.index(tab)

        # A pending debounce callback would otherwise recreate the note after
        # it has been deleted.
        if tab.save_timer:
            GLib.source_remove(tab.save_timer)
            tab.save_timer = None

        # Save then delete file
        tab.save()
        tab.delete_file()

        # Remove editor and its persistent tab controls.
        self._stack.remove(tab._widget)
        self._tabrow.remove(tab._tab_box)
        self._tabs.remove(tab)

        if tab is self._active:
            # Switch to neighbour only when the visible tab was closed.
            new_idx = min(idx, len(self._tabs) - 1)
            self._active = None
            self._switch_tab(self._tabs[new_idx])
        else:
            self._refresh_tab_selection()

    # Text change & saving 

    def _on_changed(self, tab):
        tab.modified = True
        self._update_gutter(tab)

        if tab is self._active:
            ctx = self._lbl_save.get_style_context()
            ctx.remove_class("status-saved")
            ctx.add_class("status-unsaved")
            self._lbl_save.set_text("● unsaved")
            self._update_status()

        # Refresh only the edited tab's title, rather than rebuilding all tabs.
        self._refresh_tab_label(tab)

        # Debounced save
        if tab.save_timer:
            GLib.source_remove(tab.save_timer)
        tab.save_timer = GLib.timeout_add(DEBOUNCE, self._do_save, tab)

    def _do_save(self, tab):
        tab.save()
        tab.save_timer = None
        if tab is self._active:
            ctx = self._lbl_save.get_style_context()
            ctx.remove_class("status-unsaved")
            ctx.add_class("status-saved")
            self._lbl_save.set_text("✓ saved")
        return False

    def _save_all(self):
        for tab in self._tabs:
            if tab.modified:
                tab.save()

    # Status bar

    def _update_status(self):
        if not self._active:
            return
        tab = self._active
        text = tab.text
        self._lbl_file.set_text(f"{tab.id}.txt")
        self._lbl_chars.set_text(f"{len(text)} chars")
        self._update_pos(tab)

    def _update_pos(self, tab):
        if tab is not self._active:
            return
        cur = tab.buf.get_iter_at_mark(tab.buf.get_insert())
        self._lbl_pos.set_text(f"{cur.get_line()+1}:{cur.get_line_offset()+1}")

    # State persistence 

    def _save_state(self):
        state = {
            "active": self._active.id if self._active else None,
            "tabs": [t.id for t in self._tabs],
        }
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)

    def _restore_state(self):
        if not os.path.exists(STATE_FILE):
            return
        try:
            with open(STATE_FILE) as f:
                state = json.load(f)
        except Exception:
            return

        active_id = state.get("active")
        restored_active = None
        restored_ids = set()

        for note_id in state.get("tabs", []):
            # Older versions could save the same ID twice.  Loading it twice
            # creates two tabs backed by the same file, so retain the first
            # entry and let the next normal exit rewrite a clean state file.
            if not isinstance(note_id, str) or note_id in restored_ids:
                continue
            restored_ids.add(note_id)

            p = note_path(note_id)
            content = ""
            if os.path.exists(p):
                with open(p, encoding="utf-8") as f:
                    content = f.read()
            tab = self._new_tab(note_id=note_id, content=content, switch=False)
            if note_id == active_id:
                restored_active = tab

        if self._tabs:
            self._switch_tab(restored_active or self._tabs[0])

    # Input

    def _on_key(self, widget, event):
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        if ctrl and event.keyval == ord('q'):
            self._on_quit(None, None)
            return True
        if ctrl and event.keyval == ord('s'):
            if self._active:
                self._do_save(self._active)
            return True
        if ctrl and event.keyval == ord('t'):
            self._new_tab()
            return True
        if ctrl and event.keyval == ord('w'):
            if self._active:
                self._close_tab(self._active)
            return True
        return False

    # Window drag

    def _drag_start(self, widget, event):
        if event.button == 1:
            self._drag = (event.x_root, event.y_root, *self.get_position())

    def _drag_move(self, widget, event):
        if self._drag:
            ox, oy, wx, wy = self._drag
            self.move(int(wx + event.x_root - ox), int(wy + event.y_root - oy))

    # Quit

    def _on_quit(self, widget, event):
        self._save_all()
        self._save_state()
        Gtk.main_quit()
        return False


if __name__ == "__main__":
    win = Scratchpad()
    win.show_all()
    Gtk.main()
