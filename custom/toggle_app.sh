#!/bin/bash
# Toggle app: activate if not frontmost, hide if frontmost
# Usage: toggle_app.sh "App Name" ["Process Name"]
# Process Name is optional, defaults to App Name
APP="$1"
PROCESS="${2:-$APP}"
osascript -e "
tell application \"System Events\"
    set frontApp to name of first application process whose frontmost is true
    if frontApp is \"$PROCESS\" then
        set visible of process \"$PROCESS\" to false
    else
        tell application \"$APP\" to activate
    end if
end tell
"
