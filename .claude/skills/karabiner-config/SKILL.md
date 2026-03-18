---
name: karabiner-config
description: >-
  This skill should be used when the user asks to "add a keybinding", "modify a shortcut",
  "add a key mapping", "change key mapping", "compile config", "install karabiner config",
  "update keybinding docs", "add an app shortcut", "map a key", "remap capslock",
  or any task involving editing capslock.yml, compiling to JSON, updating README documentation,
  or applying Karabiner-Elements configuration.
---

# Karabiner Capslock Configuration Skill

Manage the custom Capslock/Hyper key configuration for Karabiner-Elements. The workflow covers editing YAML config, compiling to JSON, updating documentation, and installing to Karabiner.

## Project Layout

- `custom/capslock.yml` — Source configuration (YAML), the single source of truth
- `custom/capslock.json` — Compiled output for Karabiner-Elements (auto-generated, do not edit)
- `custom/sync_karabiner.py` — Sync script that merges capslock rules into karabiner.json
- `custom/README.md` — Documentation of all keybindings
- `custom/makefile` — Build, install & sync targets

## Core Concepts

The Hyper key = CapsLock held = `right_command + right_control + right_shift + right_option` (all four right modifiers). Additional left modifiers (⌘ ⌥ ⇧ ⌃) combine with Hyper for extended functionality.

### Rule Sections in capslock.yml

| Section | Keys | Purpose |
|---------|------|---------|
| F13 to Fn | F13 | Keychron Q10 workaround |
| CapsLock to Hyper | CapsLock, Esc, Space | Core Hyper setup |
| Hyper Navigation | H/J/K/L, U/I/O/P | Vim-style cursor, selection, tabs, desktops |
| Hyper Deletion | N/M/,/. | Delete char/word/line |
| Hyper Application | E/W/F/Q | Launch apps |
| Hyper Terminal | D/Z/X/C/V/B | Terminal signals, IDE commands |
| Hyper Clipboard | 1/2/3/4 | Multi-slot clipboard |
| Hyper Shifter | [/]/;/'/\/ | Symbol shortcuts, input source |

### Modifier Convention

Each key typically has up to 6 modifier variants:

| Modifier | Symbol | Typical Role | YAML mandatory field |
|----------|--------|-------------|---------------------|
| (none) | ✱ | Base action | `[right_command,right_control,right_shift,right_option]` |
| Command | ⌘ | Selection / extended | `[left_command, right_command,right_control,right_shift,right_option]` |
| Option+Command | ⌘⌥ | Word/paragraph selection | `[left_option,left_command, right_command,right_control,right_shift,right_option]` |
| Shift | ⇧ | Tab/window management | `[left_shift, right_command,right_control,right_shift,right_option]` |
| Control | ⌃ | Desktop management | `[left_control, right_command,right_control,right_shift,right_option]` |
| Option | ⌥ | Word move / alternate | `[left_option, right_command,right_control,right_shift,right_option]` |

## Workflow

### 1. Edit Configuration

Edit `custom/capslock.yml` following the existing YAML format. Each manipulator entry looks like:

```yaml
- description: 'modifier + key = action description'
  type: basic
  from: { key_code: <key>, modifiers: { mandatory: [ <modifiers> ] } }
  to: [ { key_code: <target_key>, modifiers: [ <target_modifiers> ] } ]
```

For app launching, use `shell_command`:
```yaml
to: [ { shell_command: "open -a 'App Name'" } ]
```

For consumer keys (media):
```yaml
to: [ { consumer_key_code: "play_or_pause" } ]
```

For mouse actions:
```yaml
to: [ { pointing_button: button4 } ]           # mouse back
to: [ { mouse_key: { vertical_wheel: 64 } } ]  # scroll
```

For input source switching:
```yaml
to: [ { select_input_source: { input_source_id: "^com\\.apple\\.keylayout\\.ABC$", language: "en" } } ]
```

**Important rules when editing:**
- Place more specific modifier combos (e.g. `option + command`) BEFORE less specific ones (e.g. `command`) in the same key group, as Karabiner matches top-down
- The base Hyper variant (no extra modifier) must come LAST in each key group
- Follow existing comment/section style with `#===` separators
- Keep description format consistent: `'modifier + key = action'`

### 2. Compile

After editing, compile YAML to JSON:

```bash
cd custom && make compile
```

This runs `yq eval capslock.yml -o=json > capslock.json`. Requires `yq` installed.

### 3. Update Documentation

Update `custom/README.md` to reflect any changes made to the keybindings. Match the existing table format. Refer to `references/readme-format.md` for the documentation structure.

### 4. Sync to Karabiner

Apply changes by syncing capslock rules into the live `~/.config/karabiner/karabiner.json`:

```bash
cd custom && make sync
```

This runs `compile` first, then executes `sync_karabiner.py` which:
- Reads the compiled `capslock.json` rules
- Reads `~/.config/karabiner/karabiner.json` (the selected profile)
- Replaces rules with matching descriptions from capslock.json
- Preserves rules that only exist in karabiner.json (e.g. "Rime 候选项", "application = fn")
- Appends new capslock rules not yet present
- Writes back to karabiner.json — Karabiner-Elements auto-reloads on file change

To preview without writing:

```bash
cd custom && python3 sync_karabiner.py --dry-run
```

### Legacy: install (copy to complex_modifications)

```bash
cd custom && make install
```

Copies `capslock.json` to `~/.config/karabiner/assets/complex_modifications/`. This requires manually enabling rules in Karabiner preferences. Prefer `make sync` for automatic application.

## Full Workflow Command

To edit, compile, update docs, and apply in one go:

```bash
cd custom && make sync
```

The `sync` target depends on `compile`, so both run automatically. Karabiner-Elements picks up the change instantly.

## Additional Resources

### Reference Files

- **`references/readme-format.md`** — Documentation table format and structure for README.md updates
