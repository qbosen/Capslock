// keystatd —— 快捷键使用采集器（常驻）
//
// 只记录「带修饰键的按键」，普通打字一律不记，日志里没有可还原成文字的内容。
// 每条记录：秒级时间戳、键码、修饰键位、是否来自 Hyper、当时的前台应用编号。
//
// 为什么要记前台应用：同一个组合在不同应用里是完全不同的功能（⌘K 在编辑器是删到行尾、
// 在浏览器是搜索栏），而且这样才分得清「全局热键」和「某个软件自己的快捷键」。
//
// 为什么要记 Hyper：Karabiner 命中规则时会先松开 CapsLock 映射出的四个右修饰键，
// 再发出替换后的按键（Hyper+O 实际到达系统的是 ⌘→）。按键事件本身看不出 Hyper，
// 只能靠「刚刚松开右修饰键」这个时间窗口判定。
//
// 存储：CSV 而非 JSON，一行约 25 字节；应用名单独存 apps.tsv 用编号引用，不重复写长串包名。
// 编译：swiftc -O -o ~/.local/bin/keystatd keystatd.swift

import AppKit
import CoreGraphics
import Foundation

let RIGHT_BITS: UInt64 = 0x04 /*⇧*/ | 0x10 /*⌘*/ | 0x40 /*⌥*/ | 0x2000 /*⌃*/
let MOD_MASK: UInt64 = CGEventFlags.maskCommand.rawValue | CGEventFlags.maskControl.rawValue
    | CGEventFlags.maskAlternate.rawValue | CGEventFlags.maskSecondaryFn.rawValue
let HYPER_WINDOW: TimeInterval = 0.12

let home = FileManager.default.homeDirectoryForCurrentUser
let logDir = home.appendingPathComponent(".local/share/keystat")
try? FileManager.default.createDirectory(at: logDir, withIntermediateDirectories: true)

// ── 应用编号表：新应用追加一行，事件里只写编号 ──
let appsURL = logDir.appendingPathComponent("apps.tsv")
var appIds: [String: Int] = [:]
if let text = try? String(contentsOf: appsURL, encoding: .utf8) {
    for line in text.split(separator: "\n") {
        let f = line.split(separator: "\t", maxSplits: 1)
        if f.count == 2, let i = Int(f[0]) { appIds[String(f[1])] = i }
    }
}

func appId(_ bundle: String) -> Int {
    if let i = appIds[bundle] { return i }
    let i = appIds.count + 1
    appIds[bundle] = i
    if !FileManager.default.fileExists(atPath: appsURL.path) {
        FileManager.default.createFile(atPath: appsURL.path, contents: nil)
    }
    if let h = try? FileHandle(forWritingTo: appsURL) {
        h.seekToEndOfFile()
        h.write("\(i)\t\(bundle)\n".data(using: .utf8)!)
        h.closeFile()
    }
    return i
}

// 每个事件都去问一次前台应用太贵，改成监听切换通知、缓存当前值
var frontApp = NSWorkspace.shared.frontmostApplication?.bundleIdentifier ?? "?"
var frontId = appId(frontApp)
NSWorkspace.shared.notificationCenter.addObserver(
    forName: NSWorkspace.didActivateApplicationNotification, object: nil, queue: .main
) { note in
    let app = note.userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication
    frontApp = app?.bundleIdentifier ?? "?"
    frontId = appId(frontApp)
}

// ── 按月切分的事件文件 ──
let month = DateFormatter()
month.dateFormat = "yyyy-MM"
var handle: FileHandle?
var handleMonth = ""

func write(_ line: String) {
    let m = month.string(from: Date())
    if m != handleMonth {
        handle?.closeFile()
        let url = logDir.appendingPathComponent("events-\(m).csv")
        if !FileManager.default.fileExists(atPath: url.path) {
            FileManager.default.createFile(
                atPath: url.path, contents: "# t,keycode,flags,hyper,app\n".data(using: .utf8))
        }
        handle = try? FileHandle(forWritingTo: url)
        handle?.seekToEndOfFile()
        handleMonth = m
    }
    handle?.write((line + "\n").data(using: .utf8)!)
}

var hyperDown = false
var hyperReleasedAt: TimeInterval = 0

let mask: CGEventMask = (1 << CGEventType.keyDown.rawValue)
    | (1 << CGEventType.flagsChanged.rawValue)

guard let tap = CGEvent.tapCreate(
    tap: .cgSessionEventTap, place: .tailAppendEventTap, options: .listenOnly,
    eventsOfInterest: mask,
    callback: { _, type, event, _ in
        let now = Date().timeIntervalSince1970
        let flags = event.flags.rawValue

        if type == .flagsChanged {
            let nowDown = (flags & RIGHT_BITS) == RIGHT_BITS
            if hyperDown && !nowDown { hyperReleasedAt = now }
            hyperDown = nowDown
            return Unmanaged.passUnretained(event)
        }

        // 长按不算多次使用，跳过系统重复发出的事件
        if event.getIntegerValueField(.keyboardEventAutorepeat) != 0 {
            return Unmanaged.passUnretained(event)
        }

        let fromHyper = hyperDown || (now - hyperReleasedAt) < HYPER_WINDOW
        if (flags & MOD_MASK) != 0 || fromHyper {
            let code = event.getIntegerValueField(.keyboardEventKeycode)
            write("\(Int(now)),\(code),\(flags),\(fromHyper ? 1 : 0),\(frontId)")
        }
        return Unmanaged.passUnretained(event)
    }, userInfo: nil)
else {
    FileHandle.standardError.write(
        "keystatd: 无法创建事件监听。请在「系统设置 → 隐私与安全性 → 辅助功能」中允许 keystatd。\n"
            .data(using: .utf8)!)
    exit(1)
}

let src = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, tap, 0)
CFRunLoopAddSource(CFRunLoopGetCurrent(), src, .commonModes)
CGEvent.tapEnable(tap: tap, enable: true)

// 系统偶尔会因为回调超时把 tap 关掉，定时确认它还活着
Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { _ in
    if !CGEvent.tapIsEnabled(tap: tap) { CGEvent.tapEnable(tap: tap, enable: true) }
}

FileHandle.standardError.write("keystatd: 已启动，日志写入 \(logDir.path)\n".data(using: .utf8)!)
CFRunLoopRun()
