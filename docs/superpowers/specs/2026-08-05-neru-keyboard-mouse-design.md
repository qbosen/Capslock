# 键盘操作鼠标：极简纯 Neru 方案设计

日期：2026-08-05
状态：已批准

## 目标

实现"尽量替代鼠标"的全键盘工作流。核心判断：键盘模拟鼠标的瓶颈在"移动到目标"，
hint 跳转（屏幕元素打标签直达）比恒速盲移在效率上高一个量级，因此放弃 Karabiner
`mouse_key` 移动方案，指点操作全部交给 Neru。

## 背景

- 上游 Capslock mac_v3 提供三套键盘鼠标（HJKL 层 / 方向键层 / 小键盘层），
  均为恒速盲移模型；custom 配置创建时已剔除，仅保留滚轮与前进/后退
- 曾对比三方案：①上游方向键层+Neru ②模式化鼠标层 ③极简纯 Neru。
  用户选择方案三，理由：核心诉求是全键盘操作流程，hint 理论上更高效，先试用再迭代
- Neru（github.com/y3owk1n/neru）：免费 MIT，2026 年活跃维护，
  守护进程 + CLI 触发（`neru hints` / `neru grid`），配置 `~/.config/neru/config.toml`

## 架构

分工：**Neru 管跳转与点击，Karabiner 管唤起与独立点击键**，二者通过
`shell_command` 单向集成（Karabiner → Neru CLI），互不依赖。

### 1. Neru

- 安装：`brew tap y3owk1n/tap && brew install --cask y3owk1n/tap/neru`
- 配置：禁用 Neru 自带全局热键，入口统一走 Hyper 层（保持"CapsLock 唯一入口"哲学）
- config.toml 由 chezmoi 管理（用户现有 dotfiles 体系；不用 `--force`，冲突交用户处理）

### 2. Karabiner（custom/capslock.json 新增）

| 键位 | 行为 | 实现 |
|:--|:--|:--|
| Hyper+F | 呼出 hints 模式 | `shell_command: neru hints` |
| Hyper+G | 呼出 grid 模式 | `shell_command: neru grid` |
| Hyper+⏎ | 鼠标左键点击 | `pointing_button: button1` |
| Hyper+⌘⏎ | 鼠标右键点击 | `pointing_button: button2` |
| Hyper+⌥⏎ | 鼠标中键点击 | `pointing_button: button3` |

F、G、⏎ 在 custom 的 Hyper 层当前均为空闲，无冲突。

### 3. 明确不做（YAGNI，留待试用后迭代）

- 方向键移动层、recursive grid、Neru 滚动模式
- 现有键位全部不动：⇧⌃+HJKL 滚轮、⌥+I/O 前进后退、文本导航

## 收尾动作

1. 同步 custom 配置到 `~/.config/karabiner/`（复用仓库现有同步脚本）
2. 更新 Obsidian `02_Areas/Devices/Hyper 快捷键速查表.md`
3. Capslock 仓库提交

## 验收标准

- Hyper+F 呼出 hints，敲标签完成一次真实点击
- Hyper+⏎ / ⌘⏎ / ⌥⏎ 在光标当前位置发出左/右/中键
- 现有滚轮、前进后退、文本导航键位行为不变
