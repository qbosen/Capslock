#!/bin/bash
# 切换应用：已在前台则隐藏，否则唤起（未运行时启动）。
# 用法：toggle_app.sh "应用名称" ["前台名称"]
# 应用名称供 Application(...).activate() 解析；前台名称匹配 NSRunningApplication.localizedName。
# 两者通常相同，第二个参数默认取第一个；名称不同时必须显式传入，否则只能唤起、无法隐藏。
# 例如：toggle_app.sh 'Codex' 'ChatGPT'（当前本机 Codex 的 localizedName 是 ChatGPT）。
APP="$1"
PROCESS="${2:-$APP}"

# 应用切换类规则只发 shell_command、不产生按键事件，keystatd 看不见，这里自己记一笔
KSDIR="$HOME/.local/share/keystat"
[ -d "$KSDIR" ] && printf '{"t":%s,"cmd":"%s"}\n' "$(date +%s)" "$APP" >> "$KSDIR/shell.jsonl"
osascript -l JavaScript - "$APP" "$PROCESS" <<'JXA'
ObjC.import('AppKit');

function run(argv) {
    const front = $.NSWorkspace.sharedWorkspace.frontmostApplication;
    // 判断的是系统返回的前台名称，不一定等于用于唤起的应用名称。
    const frontName = ObjC.unwrap(front.localizedName);
    if (frontName.toLowerCase() === argv[1].toLowerCase()) {
        // 直接隐藏当前实例；System Events 按名称查找时可能选中另一个同名实例。
        front.hide;
    } else {
        // 保留系统按应用名称唤起的行为，同时支持应用尚未运行的情况。
        Application(argv[0]).activate();
    }
}
JXA
