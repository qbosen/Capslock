# 通知中心快捷键失效调查

## 本机证据

- macOS 27.0.1，Build 26A434。
- Dimble 0.3.3（81）及 DimbleItems-Hidden 正在运行。
- 系统「显示通知中心」已启用，快捷键为 Option + Shift + 数字行 0。
- EventViewer 捕获到 0 的 key_down / key_up，修饰键为 left_option、left_shift，来自 Karabiner 虚拟键盘。
- Carbon CopySymbolicHotKeys 返回该组合已启用。
- 刷新 activateSettings 和重启 NotificationCenter 后，用户仍报告不响应。
- 用户已验证：退出 Dimble 后，同一系统快捷键立即恢复。结合按键正常输出的记录，确认本次失效与 Dimble 运行时的菜单栏隐藏状态有关。

## 最相关的公开报告

### Dimble / 原 Pelmet issue #44

https://github.com/fif7y/dimble/issues/44

报告环境：macOS 27，Pelmet 0.2.39。隐藏菜单栏图标时，系统设置中的通知中心快捷键仍启用，但不执行；退出 Pelmet 后立即恢复，触控板手势可正常打开。

维护者说明：隐藏图标时 macOS 拒绝执行自己的通知中心快捷键；应用因此新增自身的通知中心快捷键，通过已有时钟点击路径打开面板。2026-09-22 的发布评论指出，0.3.0-beta.2 已包含该功能，位于 Menu Bar 标签页的时钟开关下，默认 Option + Command + N。

维护者原文及发布说明：
https://github.com/fif7y/dimble/issues/44#issuecomment-5776644463

本机 Dimble 版本为 0.3.3，但未读取或修改其自有快捷键设置，不能断言本机仍使用默认快捷键。

### Thaw issue #1146

https://github.com/thaw-app/Thaw/issues/1146

报告同类菜单栏隐藏兼容问题。评论中有与本机完全相同的 macOS 27.0.1（26A434）环境，隐藏图标时通知中心与控制中心快捷键不工作；切换隐藏方式为 Native 后，报告者确认恢复。

https://github.com/thaw-app/Thaw/issues/1146#issuecomment-6120897575
https://github.com/thaw-app/Thaw/issues/1146#issuecomment-6121173528

该报告证明类似症状可由菜单栏隐藏方式引发，但本机未发现 Thaw 进程。

## 历史及官方资料

- Ventura 用户报告任意自定义通知中心快捷键都不工作；另一用户同版本测试成功，不能视为所有系统均有同一 bug：https://apple.stackexchange.com/questions/456727/does-the-show-notification-center-shortcut-works-for-you （正文和答案通过 Stack Exchange 官方 API 读取）。
- Apple 官方列出 Fn + N 为显示或隐藏通知中心：https://support.apple.com/en-us/102650 。这不保证能绕过上述菜单栏隐藏状态造成的限制。

## 机制与处理方向

用户已完成退出 Dimble 后重测的对照实验，系统快捷键恢复。

维护者说明和当前公开源码表明，macOS 27 的隐藏引擎持有菜单栏可见性限制（assessment-mode assertion）；该限制生效时，ControlCenter 的时钟动作拒绝打开通知中心。系统快捷键的保存、启用和按键到达，与动作是否执行是不同环节。

Dimble 自有快捷键走时钟 relay：临时释放隐藏限制，调用时钟动作，再恢复隐藏。初始发布说明使用 AXPress，无需移动指针。当前 ClockClickRelay.swift 还记录了某些 macOS build 的 AXPress 兼容问题，会检测结果并回退到点击重放，因此不应保证所有版本完全不涉及鼠标事件或毫无闪烁。

源码核对版本：57d6ac1767a145efde5475a80bffd5d5cb20fefc（在线 HEAD，不等同于本机二进制的精确源码）。

- https://github.com/fif7y/dimble/blob/57d6ac1767a145efde5475a80bffd5d5cb20fefc/Pelmet/Events/ClockClickRelay.swift
- https://github.com/fif7y/dimble/blob/57d6ac1767a145efde5475a80bffd5d5cb20fefc/Packages/PelmetEngine/Sources/PelmetEngine/AgentBarEngine.swift

保留 Dimble 时，优先使用它提供的通知中心动作；若在应用中绑定 Option + Shift + 0，应取消系统中相同绑定，避免两套处理路径同时争用。
