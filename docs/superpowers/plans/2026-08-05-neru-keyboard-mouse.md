# 键盘鼠标（纯 Neru 方案）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用 Neru（hint 跳转点击）+ 5 个 Karabiner Hyper 键位实现全键盘鼠标操作。

**Architecture:** Neru 守护进程负责跳转与点击，Karabiner 通过 `shell_command` 唤起 Neru CLI，并提供 3 个独立点击键。二者单向集成、互不依赖。配置源文件是 `custom/capslock.yml`（yq 编译为 JSON 后由 `sync_karabiner.py` 合并进 karabiner.json）。

**Tech Stack:** Neru (brew cask, y3owk1n/tap) · Karabiner-Elements · yq · make · chezmoi

## Global Constraints

- 改 `custom/capslock.yml`，**永远不要手改 `custom/capslock.json`**（它是编译产物）
- Hyper 修饰键写法固定为 `[ right_command,right_control,right_shift,right_option ]`
- chezmoi 操作**禁止 `--force`**，冲突时停下来交给用户
- 现有键位一律不动（⇧⌃+HJKL 滚轮、⌥+I/O 前进后退、文本导航）
- Neru 自带全局热键必须全部禁用，入口只走 Hyper 层

---

### Task 1: 安装 Neru 并验证 CLI 可用

**Files:**
- 无文件改动（brew 安装 + 系统权限）

**Interfaces:**
- Produces: 可执行的 `neru` CLI（绝对路径），Task 2/3 依赖

- [ ] **Step 1: brew 安装**

```bash
brew tap y3owk1n/tap && brew install --cask y3owk1n/tap/neru
```

- [ ] **Step 2: 确定 CLI 绝对路径**

```bash
command -v neru || ls /opt/homebrew/bin/neru || ls /Applications/Neru.app/Contents/MacOS/
```

预期：得到一个绝对路径（大概率 `/opt/homebrew/bin/neru`）。记下它，Task 3 的 `shell_command` 必须用绝对路径（Karabiner 的 shell 环境没有完整 PATH）。若在 app bundle 内且无 CLI 链接，用 bundle 内二进制的绝对路径。

- [ ] **Step 3: 启动并授权（用户手动）**

打开 Neru.app，按提示在 系统设置 → 隐私与安全性 中授予**辅助功能**权限（hints 模式读取 UI 元素必需；若用 OCR hints 还需屏幕录制权限，本期不启用可跳过）。

- [ ] **Step 4: 终端验证 hints 模式**

```bash
<neru绝对路径> hints
```

预期：当前屏幕的可点元素浮现字母标签，敲标签完成一次左键点击。失败则回查权限。

### Task 2: Neru 配置（禁用自带热键）并纳入 chezmoi

**Files:**
- Create: `~/.config/neru/config.toml`（`neru config init` 生成后修改）

**Interfaces:**
- Consumes: Task 1 的 neru CLI
- Produces: 无全局热键的 Neru 守护配置

- [ ] **Step 1: 生成默认配置**

```bash
neru config init
```

预期：生成 `~/.config/neru/config.toml`。

- [ ] **Step 2: 注释掉 `[hotkeys]` 段的全部绑定**

编辑 `~/.config/neru/config.toml`，把 `[hotkeys]` 下的四行全部注释：

```toml
[hotkeys]
# "Primary+Shift+Space" = "hints"
# "Primary+Shift+G" = "grid"
# "Primary+Shift+C" = "recursive_grid"
# "Primary+Shift+S" = "scroll"
```

其余段保持默认（hints 模式内 Shift+L/R/M/I/U 动作键保留，那是模式内键位，不冲突）。

- [ ] **Step 3: 重载并验证热键已禁用**

```bash
neru config reload
```

按 `⌘⇧Space`，预期：**无反应**（热键已禁用）；再跑 `neru hints` CLI，预期：正常出标签。

- [ ] **Step 4: 纳入 chezmoi**

```bash
chezmoi add ~/.config/neru/config.toml
chezmoi diff
```

预期：diff 为空或仅显示本次新增。**如有冲突提示，停下来交给用户处理，禁止 --force**。

### Task 3: capslock.yml 新增 "Hyper Mouse (Neru)" 规则组并同步

**Files:**
- Modify: `~/workspace/personal/Capslock/custom/capslock.yml`（在 rules 列表末尾追加规则组）

**Interfaces:**
- Consumes: Task 1 确定的 neru 绝对路径（下方 YAML 以 `/opt/homebrew/bin/neru` 为准，若实际路径不同则替换）
- Produces: karabiner.json 中 5 条生效规则，description 分别为 `f = neru hints` / `g = neru grid` / `enter = mouse left click` / `command + enter = mouse right click` / `option + enter = mouse middle click`

- [ ] **Step 1: 确认 F、G、⏎ 无占用（防御性检查）**

```bash
grep -cE "key_code: (f|g|return_or_enter)," ~/workspace/personal/Capslock/custom/capslock.yml; grep -nE "'(f|g) = |enter = " ~/workspace/personal/Capslock/custom/capslock.yml
```

预期：无 Hyper 层的 f/g/enter 既有绑定（f13 不算）。若有占用，停下来报告。

- [ ] **Step 2: 在 capslock.yml 的 rules 末尾追加规则组**

```yaml
  ################################################################
  #                      Hyper Mouse (Neru)                      #
  ################################################################
  - description: Hyper Mouse (Neru)
    manipulators:

      - description: 'f = neru hints'
        type: basic
        from: { key_code: f, modifiers: { mandatory: [ right_command,right_control,right_shift,right_option ] } }
        to: [ { shell_command: '/opt/homebrew/bin/neru hints' } ]

      - description: 'g = neru grid'
        type: basic
        from: { key_code: g, modifiers: { mandatory: [ right_command,right_control,right_shift,right_option ] } }
        to: [ { shell_command: '/opt/homebrew/bin/neru grid' } ]

      - description: 'enter = mouse left click'
        type: basic
        from: { key_code: return_or_enter, modifiers: { mandatory: [ right_command,right_control,right_shift,right_option ] } }
        to: [ { pointing_button: button1 } ]

      - description: 'command + enter = mouse right click'
        type: basic
        from: { key_code: return_or_enter, modifiers: { mandatory: [ right_command,right_control,right_shift,right_option,left_command ] } }
        to: [ { pointing_button: button2 } ]

      - description: 'option + enter = mouse middle click'
        type: basic
        from: { key_code: return_or_enter, modifiers: { mandatory: [ right_command,right_control,right_shift,right_option,left_option ] } }
        to: [ { pointing_button: button3 } ]
```

缩进对齐现有规则组（rules 子项 2 空格起）。

- [ ] **Step 3: 编译 + 同步**

```bash
cd ~/workspace/personal/Capslock/custom && make sync
```

预期：yq 编译无报错，sync_karabiner.py 输出合并结果（新增 1 条规则组）。

- [ ] **Step 4: 验证规则已进 karabiner.json**

```bash
python3 -c "
import json,pathlib
k=json.load(open(pathlib.Path.home()/'.config/karabiner/karabiner.json'))
p=next(x for x in k['profiles'] if x.get('selected'))
descs=[r['description'] for r in p['complex_modifications']['rules']]
print('Hyper Mouse (Neru)' in descs, descs[-3:])
"
```

预期：输出 `True`（Karabiner 检测到文件变化会自动重载）。

- [ ] **Step 5: 功能验证（用户手动）**

- `Hyper+F`：出 hints 标签，敲标签完成点击
- `Hyper+G`：出网格
- `Hyper+⏎` / `Hyper+⌘⏎` / `Hyper+⌥⏎`：在光标位置发出左/右/中键（可在任意网页上验证右键菜单、中键关标签页）
- 回归：`Hyper+⇧⌃+J/K` 滚轮、`Hyper+⌥+I/O` 前进后退仍正常

- [ ] **Step 6: 提交**

```bash
cd ~/workspace/personal/Capslock && git add custom/capslock.yml custom/capslock.json && git commit -m "feat: Hyper Mouse (Neru) — f/g 唤起 hints/grid，enter 系点击"
```

### Task 4: 更新 Obsidian 速查表

**Files:**
- Modify: `~/obsidian/Notes/02_Areas/Devices/Hyper 快捷键速查表.md`

**Interfaces:**
- Consumes: Task 3 的最终键位表

- [ ] **Step 1: 新增"鼠标操作"小节**

在滚轮相关表格附近新增：

```markdown
## Mouse — 鼠标操作（Neru + 点击键）

| 键位 | 功能 |
|:-----|:-----|
| `Hyper + F` | Neru hints：元素标签跳转+点击（模式内 Shift+R 右键、Shift+M 中键、Shift+I/U 拖拽） |
| `Hyper + G` | Neru grid：网格跳转（hints 识别不到时兜底） |
| `Hyper + ⏎` | 左键点击（光标当前位置） |
| `Hyper + ⌘⏎` | 右键点击 |
| `Hyper + ⌥⏎` | 中键点击 |

滚轮（`⇧⌃+HJKL`）与前进/后退（`⌥+I/O`）见 Navigation 表。
```

- [ ] **Step 2: 核对笔记与 capslock.yml 一致后保存**

对照 Task 3 Step 2 的 YAML 逐行核对键位描述无出入。
