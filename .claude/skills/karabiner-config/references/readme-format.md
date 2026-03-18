# README.md Documentation Format

The `custom/README.md` documents all keybindings using markdown tables. Follow these conventions when updating.

## Structure

The README has these sections in order:

1. 介绍 (Introduction)
2. 功能 (Features)
   - 基础功能 (Basic)
   - 导航功能 (Navigation)
   - 删除功能 (Deletion)
   - 窗口管理 (Window Management)
   - 应用捷径 (App Shortcuts)
   - 终端控制 (Terminal)
   - 文本剪贴 (Clipboard)
   - 上档变换 (Shifter)
   - 指定输入法 (Input Source)

## Table Format

### Navigation Table (most complex)

Uses a wide table with modifier columns:

```markdown
| **功能** | **移动** | **选择** | **快速选择** | **窗口管理** | **桌面管理** | **快速移动** | **滚轮侧键** |
| -------- | -------- | -------- | ------------ | ------------ | ------------ | ------------ | ------------ |
| 键\修饰  | ✱        | ⌘        | ⌘⌥           | ⇧            | ⌃            | ⌥            | ⇧⌃           |
| H        | 左移     | 左选一字 | 左选一词     | 先前Tab      | 上个桌面     | 左移一词     | 滚轮左移     |
```

Column mapping:
- ✱ = Hyper only (base)
- ⌘ = Command + Hyper
- ⌘⌥ = Option + Command + Hyper
- ⇧ = Shift + Hyper
- ⌃ = Control + Hyper
- ⌥ = Option + Hyper
- ⇧⌃ = Shift + Control + Hyper

### Simple Tables (Deletion, Application, Terminal, etc.)

Use a simpler format with fewer modifier columns:

```markdown
| 键\修饰 | ✱        | ⌘            | ⌥        |
| ------- | -------- | ------------ | -------- |
| N       | 前删一词 | 删至行首     | 整行删除 |
```

### Application Table

```markdown
| 键\修饰 |          ✱          |         ⌘          |     ⌥      |
| :-----: | :-----------------: | :----------------: | :--------: |
|    E    |       Chrome        |       Finder       |  Calender  |
```

## Symbols Reference

Use these symbols consistently:
- ✱ — Hyper (CapsLock held)
- ⌘ — Command
- ⌥ — Option/Alt
- ⇧ — Shift
- ⌃ — Control
- ⎋ — Escape
- ⇪ — CapsLock
- ␣ — Spacebar
- ⌫ — Delete/Backspace

## Language

Documentation is written in Chinese (简体中文). Keep all descriptions in Chinese when adding or modifying entries.
