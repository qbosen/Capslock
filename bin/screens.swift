// 探测屏幕布局，给鼠标模式的「跳到第 N 块屏幕」算编号。
//
// 编号规则：按屏幕摆放位置从左到右、从上到下数，和系统内部顺序无关。
// 系统有两套内部顺序（NSScreen 和 CoreGraphics），都不保证跟摆放位置一致，
// 所以两套都打出来，方便对照 Karabiner 规则里的 screen 参数。
//
// 用法：swift bin/screens.swift   或   make screens

import AppKit
import CoreGraphics

struct Screen {
    let ns: Int
    let cg: Int
    let name: String
    let x: Int
    let y: Int
    let w: Int
    let h: Int
}

// CoreGraphics 的显示器顺序
var cgIds = [CGDirectDisplayID](repeating: 0, count: 16)
var cgCount: UInt32 = 0
CGGetActiveDisplayList(16, &cgIds, &cgCount)
var cgOrder: [CGDirectDisplayID: Int] = [:]
for i in 0..<Int(cgCount) { cgOrder[cgIds[i]] = i }

var list: [Screen] = []
for (i, s) in NSScreen.screens.enumerated() {
    let f = s.frame
    let did = (s.deviceDescription[NSDeviceDescriptionKey("NSScreenNumber")] as? NSNumber)?
        .uint32Value ?? 0
    list.append(Screen(ns: i, cg: cgOrder[did] ?? -1, name: s.localizedName,
                       x: Int(f.origin.x), y: Int(f.origin.y),
                       w: Int(f.width), h: Int(f.height)))
}

// 从左到右、从上到下：先比 x，x 相同再比 y（NSScreen 的 y 向上，所以取负）
let ordered = list.sorted { ($0.x, -$0.y) < ($1.x, -$1.y) }

print("编号  屏幕                        位置              尺寸         NSScreen  CoreGraphics")
for (i, s) in ordered.enumerated() {
    let pos = "(\(s.x),\(s.y))"
    print(String(format: "%-5d %-26s %-16s %-11s %-9d %d",
                 i + 1, (s.name as NSString).utf8String!, (pos as NSString).utf8String!,
                 ("\(s.w)x\(s.h)" as NSString).utf8String!, s.ns, s.cg))
}

print("\n供 capslock.yml 的鼠标模式使用（若按下去跳错屏，把 screen 换成另一列的值）：")
for (i, s) in ordered.enumerated() {
    print("  数字键 \(i + 1) → \(s.name)：screen: \(s.ns)   （CoreGraphics 序为 \(s.cg)）")
}
