# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a fork of [Vonng/Capslock](https://github.com/Vonng/Capslock) — a Karabiner-Elements configuration that transforms CapsLock into a Hyper modifier key (right Cmd+Ctrl+Option+Shift) on macOS. The `custom/` directory contains the user's personalized version with modified keybindings.

## Repository Structure

- `mac_v3/` — Upstream v3 config (capslock.yml source + compiled capslock.json)
- `mac_v2/`, `mac_v1/` — Older upstream versions (archived)
- `custom/` — **Active custom config** — the user's personalized keybindings
- `win/` — Windows AutoHotKey version (archived)
- `docs/` — Docsify documentation site

## Key Workflow

The configuration is authored in YAML (`capslock.yml`) and compiled to JSON (`capslock.json`) for Karabiner-Elements.

### Compile and install (in `custom/` directory)

```bash
# Compile YAML to JSON
make compile
# Which runs: yq eval capslock.yml -o=json > capslock.json

# Compile and install to Karabiner config directory
make install
# Copies capslock.json to ~/.config/karabiner/assets/complex_modifications/
```

Requires `yq` (YAML processor) to be installed.

### Install full Karabiner config

```bash
make all
# Copies karabiner.json to ~/.config/karabiner/
```

## Configuration Format

The YAML files follow Karabiner-Elements complex modifications format. Each rule contains manipulators with:
- `from` — trigger key + required/optional modifiers
- `to` — output key/action when held
- `to_if_alone` — output when tapped (used for tap-vs-hold behavior)

The Hyper key is implemented as all four right modifiers combined: `right_command + right_control + right_shift + right_option`.

## Custom vs Upstream Differences

The `custom/` config diverges from `mac_v3/` in several areas: navigation (I/O remapped to Cmd+Left/Right instead of Home/End), app shortcuts (Chrome, Logseq, VS Code instead of upstream defaults), shifter keys (`;'` mapped to `_-` / `=+` instead of `!:` / `==`), input source switching on `/`, and reduced clipboard slots (4 instead of 10).
