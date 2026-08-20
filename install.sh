#!/bin/sh
set -eu

SOURCE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DATA_HOME=${XDG_DATA_HOME:-"$HOME/.local/share"}
CONFIG_HOME=${XDG_CONFIG_HOME:-"$HOME/.config"}
BIN_HOME="$HOME/.local/bin"
APP_DIR="$DATA_HOME/command-palette"
CONFIG_DIR="$CONFIG_HOME/command-palette"

mkdir -p "$APP_DIR" "$CONFIG_DIR" "$BIN_HOME" "$DATA_HOME/applications" "$CONFIG_HOME/autostart"
cp "$SOURCE_DIR/palette.py" "$SOURCE_DIR/style.css" "$APP_DIR/"
chmod 755 "$APP_DIR/palette.py"
[ -e "$CONFIG_DIR/commands.json" ] || cp "$SOURCE_DIR/commands.json" "$CONFIG_DIR/commands.json"
[ -e "$CONFIG_DIR/style.css" ] || cp "$SOURCE_DIR/style.css" "$CONFIG_DIR/style.css"
sed "s|@APP_DIR@|$APP_DIR|g" "$SOURCE_DIR/packaging/command-palette" > "$BIN_HOME/command-palette"
chmod 755 "$BIN_HOME/command-palette"
sed "s|@BIN_HOME@|$BIN_HOME|g" "$SOURCE_DIR/packaging/io.github.commandpalette.CommandPalette.desktop" > "$DATA_HOME/applications/io.github.commandpalette.CommandPalette.desktop"
sed "s|@BIN_HOME@|$BIN_HOME|g" "$SOURCE_DIR/packaging/command-palette-autostart.desktop" > "$CONFIG_HOME/autostart/command-palette.desktop"
printf '%s\n' "Installed. Assign $BIN_HOME/command-palette --toggle to a desktop global shortcut."
