#!/bin/bash
# Toggle 默认输入设备：内置麦 <-> 小米遥控器虚拟麦 (MiRemoteV 2ch)
# 配合 SayAll.app：遥控器语音键发 Fn 长按触发微信输入法，
# 但微信输入法没有独立麦克风选择器，只读系统默认输入设备，所以要手动切。

BUILTIN="MacBook Pro Microphone"
REMOTE="MiRemoteV 2ch"

SAS=/opt/homebrew/bin/SwitchAudioSource

notify() {
    osascript -e "display notification \"$1\" with title \"麦克风\"" >/dev/null 2>&1
}

[ -x "$SAS" ] || { notify "SwitchAudioSource 未安装"; exit 1; }

CURRENT="$("$SAS" -c -t input)"
AVAILABLE="$("$SAS" -a -t input)"

# 应用切换类规则只发 shell_command、不产生按键事件，keystatd 看不见，这里自己记一笔
KSDIR="$HOME/.local/share/keystat"
[ -d "$KSDIR" ] && printf '{"t":%s,"cmd":"%s"}\n' "$(date +%s)" "toggle_mic" >> "$KSDIR/shell.jsonl"

# TODO(human): 根据 $CURRENT 和 $AVAILABLE 决定要切到哪个设备，赋值给 TARGET。
# 可用变量：
#   $CURRENT   当前默认输入设备名，如 "MacBook Pro Microphone"
#   $AVAILABLE 所有可用输入设备，每行一个（遥控器断连时 "$REMOTE" 可能不在里面）
#   $BUILTIN / $REMOTE  两个目标设备名
# 决定不了时可以 notify "..." 然后 exit 1。
TARGET=""

if [ -z "$TARGET" ]; then
    notify "未决定目标设备"
    exit 1
fi

if "$SAS" -t input -s "$TARGET" >/dev/null 2>&1; then
    notify "已切到 $TARGET"
else
    notify "切换失败：$TARGET"
    exit 1
fi
