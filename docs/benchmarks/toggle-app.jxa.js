#!/usr/bin/osascript -l JavaScript
// Benchmark candidate: one JXA process handles logging and app toggling.
ObjC.import('AppKit');

function run(argv) {
    const appName = argv[0];
    const processName = argv[1] || appName;
    const env = $.NSProcessInfo.processInfo.environment;
    const logDir = ObjC.unwrap(env.objectForKey('TOGGLE_BENCH_LOG_DIR'));
    const fm = $.NSFileManager.defaultManager;
    const dir = logDir || ObjC.unwrap($.NSHomeDirectory()) + '/.local/share/keystat';
    if (fm.fileExistsAtPath(dir)) {
        const path = dir + '/shell.jsonl';
        if (!fm.fileExistsAtPath(path)) {
            fm.createFileAtPathContentsAttributes(path, $.NSData.data, $.NSDictionary.dictionary);
        }
        const handle = $.NSFileHandle.fileHandleForWritingAtPath(path);
        if (!handle.isNil()) {
            const line = JSON.stringify({t: Math.floor(Date.now() / 1000), cmd: appName}) + '\n';
            handle.seekToEndOfFile;
            handle.writeData($(line).dataUsingEncoding($.NSUTF8StringEncoding));
            handle.closeFile;
        }
    }
    const front = $.NSWorkspace.sharedWorkspace.frontmostApplication;
    if (ObjC.unwrap(front.localizedName).toLowerCase() === processName.toLowerCase()) {
        front.hide;
    } else {
        if (argv[2] === '--native-activate') {
            // Experimental policy: first running instance with this localized name.
            // This can differ from LaunchServices selection when multiple instances exist.
            const apps = $.NSWorkspace.sharedWorkspace.runningApplications;
            for (let i = 0; i < apps.count; i++) {
                const candidate = apps.objectAtIndex(i);
                if (ObjC.unwrap(candidate.localizedName).toLowerCase() === processName.toLowerCase()) {
                    candidate.activateWithOptions(1);
                    return;
                }
            }
        }
        // Preserve support for applications that are not running yet.
        Application(appName).activate();
    }
}
