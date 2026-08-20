# Command Palette

A keyboard-first GTK 3 command palette for Linux. It supports Linux Mint Cinnamon on X11 and KDE Plasma on Wayland or X11.

The application uses `Gtk.Application` single-instance activation, chooses an installed terminal automatically, uses desktop-independent screen locking, and refuses X11-only keystroke simulation when running on Wayland.

## Requirements

- Python 3
- PyGObject with GTK 3 (`python3-gi` and `gir1.2-gtk-3.0` on Ubuntu/Mint)
- `xdg-utils`

Optional commands may need their own programs, such as `pkexec`, `xdotool`, or an SSH client.

## Install

```sh
git clone YOUR_REPOSITORY_URL command-palette
cd command-palette
./install.sh
```

The installer puts the program in `~/.local/share/command-palette`, creates `~/.local/bin/command-palette`, installs desktop and autostart entries, and preserves an existing `~/.config/command-palette/commands.json`.

Assign this command to the global shortcut you want:

```text
/home/YOUR_USER/.local/bin/command-palette --toggle
```

On KDE Plasma, use **System Settings → Keyboard → Shortcuts → Add New → Command or Script**. On Cinnamon, use **System Settings → Keyboard → Shortcuts → Custom Shortcuts**.

Run it without a shortcut with `command-palette`. Use Escape to hide it, the arrow keys to select, and Enter to execute.

## Configure commands

Edit `~/.config/command-palette/commands.json`. Changes are loaded whenever the window opens.

Common fields are `name`, `description`, `category`, `keywords`, and `type`.

### Limit a command to an environment

Add `env` to show and run an entry only in matching environments. It accepts one name or a list of alternatives. Matching is case-insensitive.

```json
"env": "Wayland"
```

```json
"env": ["Mint", "Cinnamon"]
```

Recognized values include `Mint`, `Cinnamon`, `KDE`, `Plasma`, `X11`, and `Wayland`. A list means **any** listed environment may run the command. Omit `env` to make an entry available everywhere.

### Command

Arguments are separate array elements and are launched without a shell. Set `terminal` to true for an interactive command. The palette selects `x-terminal-emulator`, Konsole, GNOME Terminal, XFCE Terminal, or MATE Terminal in that order. Set `COMMAND_PALETTE_TERMINAL` in the service environment to override it.

```json
{
  "name": "SSH to server",
  "type": "command",
  "command": ["ssh", "user@example.local"],
  "terminal": true
}
```

`~` and environment variables are expanded in command arguments.

### Directory, URL, and script

```json
{"name": "Downloads", "type": "directory", "path": "~/Downloads"}
```

```json
{"name": "Router", "type": "url", "url": "http://192.168.1.1"}
```

```json
{"name": "Backup", "type": "script", "script": "~/.local/bin/backup"}
```

### Lock screen

```json
{"name": "Lock Screen", "type": "lock-screen"}
```

This uses `loginctl lock-session`, which works with both Plasma and Cinnamon.

### Keystroke (X11 only)

```json
{"name": "Send shortcut", "type": "keystroke", "keys": "super+g"}
```

This uses `xdotool`. Wayland intentionally prevents applications from injecting arbitrary global keys, so this action is rejected on Wayland. Use KDE or Cinnamon's native global-shortcut settings for cross-desktop shortcuts.

### Restart the palette

```json
{"name": "Restart Command Palette", "type": "restart-palette"}
```

## Development

Validate without installing:

```sh
python3 -m py_compile palette.py
python3 -m json.tool commands.json >/dev/null
```

Re-run `./install.sh` after changing program files. User configuration is not overwritten.

## Uninstall

```sh
./uninstall.sh
```

The uninstaller preserves `~/.config/command-palette` so personal commands are not lost.
