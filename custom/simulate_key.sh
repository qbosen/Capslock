#!/usr/bin/env zsh
# simulate_key.sh — Simulate a keyboard shortcut after a delay.
# Useful for setting hotkeys in apps that require pressing the combo
# while a recording dialog is open.
#
# Uses CoreGraphics CGEvent API (via inline Swift) to post events at
# kCGHIDEventTap — the lowest software-accessible tap point.
# No external dependencies needed (Swift is built into macOS).
#
# Usage:
#   ./simulate_key.sh <delay> <key_combo>
#
# Examples:
#   ./simulate_key.sh 3 option+cmd+f16
#   ./simulate_key.sh 2 ctrl+shift+a
#   ./simulate_key.sh 1 cmd+space
#   ./simulate_key.sh 3 f16
#
# Supported modifiers: cmd/command, option/alt, ctrl/control, shift
# Supported keys: a-z, 0-9, f1-f20, space, tab, escape, return,
#                 delete, up, down, left, right, and more.

set -euo pipefail

# --- Key code mapping (macOS virtual key codes) ---
typeset -A KEY_CODES=(
  a 0   b 11  c 8   d 2   e 14  f 3   g 5   h 4
  i 34  j 38  k 40  l 37  m 46  n 45  o 31  p 35
  q 12  r 15  s 1   t 17  u 32  v 9   w 13  x 7
  y 16  z 6
  0 29  1 18  2 19  3 20  4 21  5 23  6 22  7 26
  8 28  9 25
  f1 122  f2 120  f3 99   f4 118  f5 96   f6 97
  f7 98   f8 100  f9 101  f10 109 f11 103 f12 111
  f13 105 f14 107 f15 113 f16 106 f17 64  f18 79
  f19 80  f20 90
  space 49      tab 48       escape 53    return 36
  delete 51     forwarddelete 117
  up 126        down 125     left 123     right 124
  home 115      end 119      pageup 116   pagedown 121
  hyphen 27     equal 24     minus 27
  leftbracket 33  rightbracket 30
  semicolon 41  quote 39     backslash 42
  comma 43      period 47    slash 44     grave 50
)

# --- CGEvent modifier flags ---
typeset -A MOD_FLAGS=(
  cmd 0x100000  command 0x100000
  opt 0x80000   option  0x80000   alt 0x80000
  ctrl 0x40000  control 0x40000
  shift 0x20000
  fn 0x800000
)

usage() {
  echo "Usage: $0 <delay_seconds> <key_combo>"
  echo ""
  echo "Examples:"
  echo "  $0 3 option+cmd+f16"
  echo "  $0 2 ctrl+shift+a"
  echo "  $0 1 cmd+space"
  echo ""
  echo "Supported modifiers: cmd, option/alt, ctrl, shift"
  echo "Supported keys: a-z, 0-9, f1-f20, space, tab, escape, return, etc."
  exit 1
}

[[ $# -lt 2 ]] && usage

delay="$1"
combo="$2"

# Parse combo
mod_names=()
mod_flag_total=0
key=""

for part in ${(s:+:)combo}; do
  p="${part:l}"
  flag="${MOD_FLAGS[$p]:-}"
  if [[ -n "$flag" ]]; then
    mod_names+=("$p")
    (( mod_flag_total = mod_flag_total | flag ))
  else
    key="$p"
  fi
done

if [[ -z "$key" ]]; then
  echo "Error: no key specified in combo '$combo'"
  usage
fi

key_code="${KEY_CODES[$key]:-}"
if [[ -z "$key_code" ]]; then
  echo "Error: unknown key '$key'"
  echo "Supported keys: ${(ok)KEY_CODES}"
  exit 1
fi

echo "Will simulate: $combo"
echo "  → key code $key_code, modifier flags 0x$(printf '%x' $mod_flag_total) [${mod_names[*]:-none}]"
echo "  → waiting ${delay}s... (switch to target app now!)"

sleep "$delay"

# Post CGEvent via inline Swift (no dependencies needed)
swift -e "
import CoreGraphics
import Foundation

let keyCode = CGKeyCode($key_code)
let flags = CGEventFlags(rawValue: UInt64($mod_flag_total))

// Key down
if let keyDown = CGEvent(keyboardEventSource: nil, virtualKey: keyCode, keyDown: true) {
    keyDown.flags = flags
    keyDown.post(tap: .cghidEventTap)
}

Thread.sleep(forTimeInterval: 0.05)

// Key up
if let keyUp = CGEvent(keyboardEventSource: nil, virtualKey: keyCode, keyDown: false) {
    keyUp.flags = flags
    keyUp.post(tap: .cghidEventTap)
}
"

echo "Done!"
