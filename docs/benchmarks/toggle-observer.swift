// Native observer for the benchmark. Runs outside each timed command.
import AppKit
import Foundation

func snapshot(_ pid: pid_t) -> [String: Any] {
    RunLoop.current.run(until: Date().addingTimeInterval(0.003))
    let target = NSRunningApplication(processIdentifier: pid)
    let front = NSWorkspace.shared.frontmostApplication
    return ["front": Int(front?.processIdentifier ?? -1),
            "frontName": front?.localizedName ?? "",
            "hidden": target?.isHidden ?? true]
}

while let line = readLine() {
    do {
        let request = try JSONSerialization.jsonObject(with: Data(line.utf8)) as! [String: Any]
        let pid = pid_t(request["pid"] as? Int ?? -1)
        if request["op"] as? String == "activate", let app = NSRunningApplication(processIdentifier: pid) {
            app.unhide()
            for _ in 0..<40 {
                app.activate(options: [.activateAllWindows])
                RunLoop.current.run(until: Date().addingTimeInterval(0.025))
                if NSWorkspace.shared.frontmostApplication?.processIdentifier == pid && !app.isHidden { break }
            }
        }
        var result = snapshot(pid)
        result["apps"] = NSWorkspace.shared.runningApplications.filter {
            ["Google Chrome", "Finder"].contains($0.localizedName ?? "")
        }.map { ["pid": Int($0.processIdentifier), "name": $0.localizedName ?? "", "hidden": $0.isHidden] as [String: Any] }
        let data = try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
        print(String(decoding: data, as: UTF8.self))
        fflush(stdout)
    } catch {
        print("{}")
        fflush(stdout)
    }
}
