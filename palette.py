#!/usr/bin/env python3
"""Cross-desktop GTK command palette."""
import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import webbrowser

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gio, GLib, Gtk

APP_ID = "io.github.commandpalette.CommandPalette"
ICON_NAME = "system-run"
GLib.set_prgname(APP_ID)
GLib.set_application_name("Command Palette")
Gtk.Window.set_default_icon_name(ICON_NAME)
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")), "command-palette")
COMMAND_FILE = os.path.join(CONFIG_DIR, "commands.json")
STYLE_FILE = os.path.join(CONFIG_DIR, "style.css")


def current_environments():
    """Return normalized desktop/session names used by an entry's env filter."""
    values = {os.environ.get("XDG_SESSION_TYPE", "").casefold()}
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
    values.update(part.casefold() for part in desktop.replace(";", ":").split(":") if part)
    if "cinnamon" in values or "x-cinnamon" in values:
        values.update(("cinnamon", "mint"))
    if "kde" in values or "plasma" in values:
        values.update(("kde", "plasma"))
    values.discard("")
    return values


def environment_matches(item):
    """An env string or list is an OR-list; an omitted env runs everywhere."""
    requested = item.get("env")
    if requested is None:
        return True
    if isinstance(requested, str):
        requested = [requested]
    if not isinstance(requested, list):
        return False
    requested = {str(value).casefold() for value in requested}
    return bool(requested & current_environments())


def terminal_command(command):
    configured = os.environ.get("COMMAND_PALETTE_TERMINAL")
    candidates = ([configured] if configured else []) + ["x-terminal-emulator", "konsole", "gnome-terminal", "xfce4-terminal", "mate-terminal"]
    terminal = next((item for item in candidates if item and shutil.which(item)), None)
    if not terminal:
        raise RuntimeError("no supported terminal emulator was found")
    return [terminal, "-e", *command]


def lock_command():
    if shutil.which("loginctl"):
        return ["loginctl", "lock-session"]
    if shutil.which("xdg-screensaver"):
        return ["xdg-screensaver", "lock"]
    raise RuntimeError("no supported screen-lock command was found")


class CommandPalette(Gtk.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application, title="Command Palette")
        self.set_icon_name(ICON_NAME)
        self.set_default_size(480, 360)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_accept_focus(True)
        self.set_focus_on_map(True)
        self.set_skip_taskbar_hint(True)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_name("palette_window")
        self.connect("key-press-event", self.on_key_press)
        self.commands = []
        self.filtered_commands = []
        self.load_css()
        self.build_ui()
        self.reload()

    def load_css(self):
        path = STYLE_FILE if os.path.isfile(STYLE_FILE) else os.path.join(APP_DIR, "style.css")
        if not os.path.isfile(path):
            return
        provider = Gtk.CssProvider()
        try:
            provider.load_from_path(path)
        except GLib.Error as error:
            print(f"Unable to load {path}: {error}", file=sys.stderr)
            return
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def load_commands(self):
        try:
            with open(COMMAND_FILE, encoding="utf-8") as source:
                value = json.load(source).get("commands", [])
            self.commands = value if isinstance(value, list) else []
        except (OSError, json.JSONDecodeError) as error:
            print(f"Unable to load {COMMAND_FILE}: {error}", file=sys.stderr)
            self.commands = []

    def build_ui(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(12)
        self.add(box)
        self.search_entry = Gtk.Entry(name="search_entry")
        self.search_entry.set_placeholder_text("Type a command…")
        self.search_entry.connect("changed", lambda _entry: self.update_results())
        box.pack_start(self.search_entry, False, False, 0)
        self.listbox = Gtk.ListBox(name="command_list")
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-activated", self.execute_now)
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.add(self.listbox)
        box.pack_start(self.scroll, True, True, 0)

    def reload(self):
        self.load_commands()
        self.update_results()

    def update_results(self):
        query = self.search_entry.get_text().casefold().strip()
        for row in self.listbox.get_children():
            self.listbox.remove(row)
        self.filtered_commands = []
        for command in self.commands:
            if not isinstance(command, dict):
                continue
            if not environment_matches(command):
                continue
            text = " ".join([str(command.get("name", "")), str(command.get("description", "")), str(command.get("category", "")), " ".join(map(str, command.get("keywords", [])))])
            if not query or query in text.casefold():
                self.filtered_commands.append(command)
        for command in self.filtered_commands:
            row = Gtk.ListBoxRow(name="command_row")
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            box.set_border_width(8)
            name = Gtk.Label(label=str(command.get("name", "Unnamed")), xalign=0)
            name.get_style_context().add_class("command_name")
            box.pack_start(name, False, False, 0)
            detail = " — ".join(filter(None, [command.get("category", ""), command.get("description", "")]))
            if detail:
                secondary = Gtk.Label(label=detail, xalign=0)
                secondary.set_ellipsize(3)
                secondary.get_style_context().add_class("command_description")
                box.pack_start(secondary, False, False, 0)
            row.add(box)
            self.listbox.add(row)
        self.listbox.show_all()
        first = self.listbox.get_row_at_index(0)
        if first:
            self.listbox.select_row(first)

    def on_key_press(self, _widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.hide()
            return True
        if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            row = self.listbox.get_selected_row()
            if row:
                self.execute_now(self.listbox, row)
            return True
        if event.keyval in (Gdk.KEY_Down, Gdk.KEY_Up):
            self.move_selection(1 if event.keyval == Gdk.KEY_Down else -1)
            return True
        return False

    def move_selection(self, direction):
        selected = self.listbox.get_selected_row()
        row = self.listbox.get_row_at_index(selected.get_index() + direction if selected else 0)
        if not row:
            return
        self.listbox.select_row(row)
        adjustment = self.scroll.get_vadjustment()
        allocation = row.get_allocation()
        if allocation.y < adjustment.get_value():
            adjustment.set_value(allocation.y)
        elif allocation.y + allocation.height > adjustment.get_value() + adjustment.get_page_size():
            adjustment.set_value(allocation.y + allocation.height - adjustment.get_page_size())

    def execute_now(self, _listbox, row):
        if 0 <= row.get_index() < len(self.filtered_commands):
            self.execute_command(self.filtered_commands[row.get_index()])

    def execute_command(self, item):
        try:
            if not environment_matches(item):
                raise RuntimeError("this command is disabled in the current environment")
            kind = item.get("type")
            if kind == "command":
                command = item.get("command")
                if not isinstance(command, list) or not command:
                    raise ValueError("command must be a non-empty array")
                command = [os.path.expandvars(os.path.expanduser(str(part))) for part in command]
                subprocess.Popen(terminal_command(command) if item.get("terminal", False) else command)
            elif kind == "url":
                webbrowser.open(str(item.get("url", "")))
            elif kind == "directory":
                path = os.path.expandvars(os.path.expanduser(str(item.get("path", ""))))
                application = item.get("application")
                subprocess.Popen([str(application), path] if application else ["xdg-open", path])
            elif kind == "script":
                subprocess.Popen([os.path.expandvars(os.path.expanduser(str(item.get("script", ""))))])
            elif kind == "lock-screen":
                subprocess.Popen(lock_command())
            elif kind == "restart-palette":
                GLib.idle_add(self.get_application().restart)
            elif kind == "keystroke":
                if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
                    raise RuntimeError("keystroke actions are unavailable on Wayland")
                subprocess.Popen(["xdotool", "key", str(item.get("keys", ""))])
            else:
                raise ValueError(f"unknown command type: {kind}")
        except (OSError, ValueError, RuntimeError) as error:
            print(f"Error executing {item.get('name', 'command')}: {error}", file=sys.stderr)
        self.hide()
        self.search_entry.set_text("")

    def show_palette(self):
        self.reload()
        self.show_all()
        self.present_with_time(Gdk.CURRENT_TIME)
        self.search_entry.grab_focus()

    def toggle(self):
        self.hide() if self.get_visible() else self.show_palette()


class PaletteApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        signal.signal(signal.SIGUSR1, lambda _sig, _frame: GLib.idle_add(self.toggle))

    def ensure_window(self):
        if self.window is None:
            self.window = CommandPalette(self)
        return self.window

    def do_activate(self):
        self.ensure_window().show_palette()

    def toggle(self):
        self.ensure_window().toggle()
        return False

    def restart(self):
        os.execl(sys.executable, sys.executable, os.path.abspath(__file__), "--background")
        return False

    def do_command_line(self, command_line):
        parser = argparse.ArgumentParser(prog="command-palette")
        parser.add_argument("--background", action="store_true")
        parser.add_argument("--toggle", action="store_true")
        try:
            args = parser.parse_args(command_line.get_arguments()[1:])
        except SystemExit as error:
            return int(error.code or 0)
        if args.background:
            self.ensure_window()
            self.hold()
        elif args.toggle:
            self.toggle()
        else:
            self.activate()
        return 0


if __name__ == "__main__":
    raise SystemExit(PaletteApplication().run(sys.argv))
