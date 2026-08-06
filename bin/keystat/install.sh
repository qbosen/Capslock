#!/bin/bash
# 编译并安装 keystatd 为登录后常驻的 LaunchAgent
set -e

SRC="$(cd "$(dirname "$0")" && pwd)/keystatd.swift"
BIN="$HOME/.local/bin/keystatd"
PLIST="$HOME/Library/LaunchAgents/com.capslock.keystat.plist"
LABEL="com.capslock.keystat"

mkdir -p "$HOME/.local/bin" "$HOME/Library/LaunchAgents" "$HOME/.local/share/keystat"

echo "编译 $SRC"
swiftc -O -o "$BIN" "$SRC"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array><string>$BIN</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardErrorPath</key><string>$HOME/.local/share/keystat/keystatd.err</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$UID/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$UID" "$PLIST"

echo
echo "已安装并启动：$BIN"
echo "首次运行需要在「系统设置 → 隐私与安全性 → 辅助功能」里勾选 keystatd，"
echo "授权后执行：launchctl kickstart -k gui/$UID/$LABEL"
echo
echo "日志目录：~/.local/share/keystat/"
echo "查看报告：make keystat-report"
echo "停止采集：launchctl bootout gui/$UID/$LABEL"
