#!/bin/bash
# Toggle Espanso search bar: open if not focused, close (Escape) if focused.

front_app=$(osascript -e 'tell application "System Events" to get name of first application process whose frontmost is true' 2>/dev/null)

if [[ "$front_app" == "espanso" ]]; then
  osascript -e 'tell application "System Events" to key code 53'  # Escape
else
  /opt/homebrew/bin/espanso cmd search
fi
