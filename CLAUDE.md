# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 这是什么

Fork 自 [Vonng/Capslock](https://github.com/Vonng/Capslock)，把 CapsLock 变成 Hyper 键（右 ⌘⌃⇧⌥）。
现在已经超出原项目范围，是这台机器**全部快捷键的单一事实来源**：Karabiner 规则 + 外部应用热键 + 键盘固件层 + 应用内快捷键，统一渲染成可交互键位图，并配了使用频率统计。

`custom/` 是唯一在用的配置；`mac_v3/`、`mac_v2/`、`mac/`、`win/` 是上游存档，只读。

## 输入链路的四层

改动前先确认要改的东西属于哪一层，**每层只看得见它的上游**：

1. **键盘固件（QMK/VIA）** — M1–M5 统一发 F20–F24 裸键，语义不在固件里
2. **Karabiner** — 绝大部分逻辑在这层；看不见自己的输出，也看不见合成事件
3. **应用全局热键** — Contexts / Magnet / Bob / Shottr 等，看得见 Karabiner 的输出
4. **应用内快捷键** — Ghostty 等，只在该应用前台生效

常见误判：想让 Karabiner 发出的键触发另一条 Karabiner 规则——**做不到**，输出不回流引擎，同层联动必须在同一条规则里用变量和条件表达。

## 配置文件分工

| 文件 | 管什么 |
|---|---|
| `custom/capslock.yml` | Karabiner 规则（唯一需要 `make sync` 的） |
| `custom/external.yml` | 各应用注册的全局热键 |
| `custom/apps.yml` | 应用内快捷键（只在该应用前台生效） |
| `custom/keyboard.yml` | Q10 固件层记录（改这里不生效，要去 VIA） |
| `custom/screens.yml` | 屏幕编号缓存，供鼠标模式跳屏 |
| `custom/keymap.yml` | 键位图的**全部**中文说法、界面文案、键盘布局 |

`bin/keymap.py` 和模板里**不放任何会被渲染的中文**。要改说法、加动作翻译、调布局，一律改 `custom/keymap.yml`。

## 命令

```bash
cd custom && make sync   # 编译 capslock.yml 并同步进 ~/.config/karabiner/（改规则后必跑）
make keymap              # 重新生成 keymap.html
make screens             # 换显示器后重测屏幕编号
make keystat-report      # 快捷键使用统计（--json 可喂给 AI 分析）
```

## 硬约束

- **规则顺序 = if-else**：Karabiner 取第一条匹配就停止。带条件的必须排在无条件的前面，否则永远不命中（开关类功能全靠这个）。
- **合成按键测不了**：`osascript` 发出的事件注入在 Karabiner 之后，它收不到。涉及 Karabiner 规则的验证只能让用户手按。
- **位面难度取决于手指冲突**：Hyper 由左小指按住，`⌘`/`⌥`（拇指）好按，`⌃`/`⇧`（同为小指）极难。所以易按位面只有三层，这是物理上限——功能放不下时用**模式**（变量 + 条件）或 **M3/M4 单键触发**，不要继续叠修饰键。
- **改了 `custom/toggle_app.sh` 等脚本**也要 `make sync`（它会一并安装到 `~/.local/bin/`）。

## 键位图的几个约定

- **别名自动合并**：同组内标签和动作完全相同的多个键位，在速查表/功能视图合并成一行（如 `1 / Q`），键盘视图仍各自高亮。不需要声明，写成一样的动作描述即可。
- **变体不单列**：带 `variant_conditions`（如 `mouse_speed`）的规则是同一个键的快慢档，生成器会跳过，不占键位图行数。
- **位面触发器**：`layers.triggers` 声明某位面可由宏键单键进入（M3/M4），键位图显示徽标，速查表可切换成 M 键写法。
- **速查表可隐藏组**：勾选状态存在浏览器里，导出的 PNG / PDF 跟着变，应用类快捷键太多时用它裁掉。
- **练习页靠输出信号判定**：生成器把每条规则的输出算成 `entry.signal`（如 `cmd+ArrowLeft`），
  和浏览器 keydown 一比就知道按对没有。信号算不出、或会把浏览器切走（`practice.block_signals`）的，
  自动降级成闪卡。所以**它判的是结果不是按法**——物理方向键也能过，这是 Karabiner 不回流的必然结果。

## 改动后的自检

改规则 → `make sync` → `make keymap` → 让用户实际按一下验证。涉及键位分配时，先看 `keymap.html` 或 `make keystat-report` 确认目标位面是否已被占用。
