#!/bin/sh
set -eu
DATA_HOME=${XDG_DATA_HOME:-"$HOME/.local/share"}
CONFIG_HOME=${XDG_CONFIG_HOME:-"$HOME/.config"}
rm -f "$HOME/.local/bin/command-palette"
rm -f "$DATA_HOME/applications/io.github.commandpalette.CommandPalette.desktop"
rm -f "$CONFIG_HOME/autostart/command-palette.desktop"
rm -rf "$DATA_HOME/command-palette"
printf '%s\n' "Removed the application. Configuration remains in $CONFIG_HOME/command-palette."
