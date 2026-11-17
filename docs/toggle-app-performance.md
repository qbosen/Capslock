# toggle_app 耗时对比

在本机测试中，当前 Bash + JXA 版隐藏 Chrome 的中位数为 65 ms，旧 AppleScript 版为 202 ms。把日志和参数处理也放进 JXA 后，隐藏约 58 ms，唤起约 122 ms，相比当前版本再省 7 ms 和 14 ms。主要收益来自改用 AppKit 获取和隐藏前台实例，移除 Bash 的收益约为 10%。[1]

测试完成于 2026-10-21，本机为 Apple M5 Pro、macOS 27.0.1。下面的数据用于这台机器上的实现选择。

## 完整脚本的测量结果

表内单位为毫秒。每个版本分别采集 30 次隐藏和 30 次唤起，每组另有 2 次预热调用未计入。

| 方案 | 隐藏中位数 | 隐藏 P95 | 唤起中位数 | 唤起 P95 |
|---|---:|---:|---:|---:|
| 旧 Bash + AppleScript + System Events | 201.63 | 257.98 | 201.01 | 280.96 |
| 当前 Bash + JXA + AppKit | 65.21 | 91.01 | 135.79 | 176.28 |
| 全 JXA，保留原有唤起方式 | 57.99 | 77.32 | 121.78 | 175.53 |
| 全 JXA，已运行应用用 AppKit 唤起 | 61.04 | 93.58 | 112.16 | 209.32 |

数据来自 [原始采样及汇总](benchmarks/toggle-app-results.json)。P95 采用排序后的 nearest-rank，第 29 个样本。[1]

当前版本相对旧版本，隐藏耗时减少约 68%，唤起减少约 32%。全 JXA 相对当前版本，隐藏减少 7.22 ms，约 11.1%，唤起减少 14.01 ms，约 10.3%。这说明此前只凭代码推测性能变化不明显，低估了绕过 System Events 的实际收益。[1]

首次探索测试每组 20 次，旧版、当前版、全 JXA 的隐藏中位数分别为 187、60、55 ms，唤起分别为 187、109、100 ms。正式交叉测试中各版本稍慢，但方案排序一致。这也说明后台负载会影响绝对数值。正式 30 次采样保留在 JSON 中。

## 全 JXA 具体省掉什么

当前版本先启动 Bash，检查统计目录，调用外部 `date`，用 Bash 内建 `printf` 追加统计，再启动 `osascript` 执行 JXA。全 JXA 候选把这些操作合进同一个 `osascript` 进程：

- 参数从 `run(argv)` 取得。
- 时间戳用 `Date.now()` 生成。
- 统计文件用 Foundation 的 `NSFileHandle` 追加。
- 前台应用由 `NSWorkspace.frontmostApplication` 取得，匹配后调用该实例的 `hide`。
- 唤起继续用 `Application(appName).activate()`，保留当前按名称激活、应用尚未运行时启动的路径。[2][3][4]

这里的全 JS 是 JXA，通过 Objective-C bridge 调用系统框架。它仍使用 `osascript`，每次按键启动一个新进程。Karabiner 的 `shell_command` 外层执行机制也仍存在，本次没有测量那一层。普通 Node.js 的标准库没有 AppKit 接口，单纯换成 Node 不会自动获得同样的应用控制能力。本次没有测 Node、第三方原生模块或常驻 JS 服务。

完整候选实现在 [toggle-app.jxa.js](benchmarks/toggle-app.jxa.js)。本次仅添加研究和基准文件，线上仍使用 `custom/toggle_app.sh`。

## 单独测启动成本

每项运行 30 次，单位为毫秒。这些是独立命令的总耗时，适合解释数量级，不应把不同项的中位数直接相加，作为完整脚本的精确分解。[1]

| 命令内容 | 中位数 | P95 |
|---|---:|---:|
| Bash 空命令 | 6.28 | 7.43 |
| Bash + 外部 date | 9.35 | 12.95 |
| 空 AppleScript | 36.78 | 58.49 |
| 空 JXA | 27.58 | 32.71 |
| JXA 加载 AppKit | 43.92 | 53.03 |
| JXA 加载 AppKit 并读取前台名称 | 46.28 | 51.73 |

独立 JXA 的最低开销已经有几十毫秒，加载 AppKit 后约 44 ms。去掉 Bash 和 `date` 能改善完整脚本耗时，但无法消除 JXA、桥接框架和进程初始化成本。[1]

若要继续追求远低于 50 ms 的脚本响应，可以另测编译后的 Swift 小程序，或者常驻进程加 IPC。它们分别需要处理二进制构建，或服务生命周期。本次未测量这些方案，不能据此承诺具体速度。

## 直接用 AppKit 唤起的收益和边界

额外候选枚举 `NSWorkspace.runningApplications`，取第一个名称匹配的实例，再调用 `activateWithOptions(1)`。应用未运行时仍回退到原唤起路径。它的唤起中位数比全 JXA 基础版少约 10 ms，P95 则从 176 ms 增至 209 ms，样本不支持它能稳定改善尾部延迟。[1][2]

这个候选还改变了行为：多实例时取枚举顺序中的第一个，选出的实例可能与原来的系统激活路径不同。Apple 头文件明确说明运行应用列表的顺序没有定义，因此不能把这种选择规则直接推广到全部应用。用 bundle ID 和明确的实例选择规则会更可靠，但这属于另一项行为设计。[2]

此外，原生 activate 发送请求后可能在界面切换完成前返回。这里测的是命令进程运行时间，未测窗口动画完成时间，不能将其直接当成完整的用户可见延迟。[2]

## 正确性校验与测试方法

基准用单独运行的 Swift/AppKit 观察器设置前台状态，并检查结果。每次隐藏前激活日常 Chrome，每次唤起前激活 Finder，随后在计时外等待 80 ms 稳定状态。用 Python 单调时钟测量目标命令从启动到退出的时间，计时包含 Bash、date、osascript 及脚本自身日志写入，不包含预置焦点和结果检查。[1][5]

四个版本的隐藏和唤起任务使用固定随机种子交错运行，减少先后顺序影响。文件缓存经过预热，每次目标调用启动新进程。本次没有重启系统或清理缓存，因此不代表开机后第一次调用的耗时。[5]

所有版本都写相同的隔离临时统计文件。260 条 JSONL 记录均能解析且应用名正确，未写入真实快捷键统计。候选仅通过 Foundation 写日志，没有调用 shell。[1][3][4]

正式性能采样的每组 30 次均通过后置校验。另对第二个同名 Chrome 实例做定向测试，旧版未隐藏该实例，当前版和两个全 JXA 候选均正确隐藏。这证明旧版的退出成功不足以代表功能成功。第一轮探索测试也出现过旧版返回成功但隐藏失败。[1]

Apple SDK 还说明，`NSRunningApplication` 的 `hidden` 等动态属性可能缓存到下一次主运行循环。观察器每次查询前运行主循环，避免在同一个 JXA 实例中立即回读缓存状态产生误判。`hide` 的返回值表示请求是否发出，不能替代实际状态检查。[2][5]

复现命令会短暂切换应用焦点，结束时尝试恢复原前台应用：

```bash
cd ~/workspace/personal/Capslock
python3 docs/benchmarks/toggle-app.py --samples 30
```

需要本机已运行的 Chrome 和 Finder，以及 Xcode Command Line Tools。脚本在临时目录编译观察器并生成旧版、当前版的隔离副本，退出时删除临时文件。旧版固定为 Git 提交 `54e8ff2ca635d0f8de4a54026774461aacaca18a` 的脚本，当前版读取工作区文件。[5]

## 建议

如果继续优化，优先采用全 JXA 基础版：保留现有唤起行为，把统计和参数处理移进去，隐藏和唤起分别能省约 7 ms 和 14 ms，也减少 Bash 和外部 `date` 调用。当前候选已完成 Chrome 隐藏、唤起和同名实例测试，接入前还应验证 Ghostty、Finder 等现有绑定，检查应用名与 `localizedName` 的对应关系。[1][2]

直接 AppKit 唤起暂时保留为实验选项。需要明确多实例选择、无窗口时是否重开窗口等行为后，再决定是否替换现有激活路径。

## 来源

1. 本机实测：[原始结果](benchmarks/toggle-app-results.json)，环境和每次采样均在文件中。
2. Apple SDK：[NSRunningApplication.h](/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/System/Library/Frameworks/AppKit.framework/Versions/C/Headers/NSRunningApplication.h)，包含单实例对象、动态属性缓存、hide、activate 和列表顺序的说明。
3. Apple SDK：[NSWorkspace.h](/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/System/Library/Frameworks/AppKit.framework/Versions/C/Headers/NSWorkspace.h)，包含前台应用属性及应用启动接口说明。
4. Apple SDK：[NSFileHandle.h](/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/System/Library/Frameworks/Foundation.framework/Versions/C/Headers/NSFileHandle.h)，以及系统 `man osascript`，后者说明 JavaScript 语言选择、脚本文件执行和 argv 传递。
5. 可复现实现：[驱动脚本](benchmarks/toggle-app.py)、[观察器](benchmarks/toggle-observer.swift)、[全 JXA 候选](benchmarks/toggle-app.jxa.js)。
