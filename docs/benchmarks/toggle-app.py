#!/usr/bin/env python3
"""Benchmark real app toggles; temporarily moves focus. No production config edits."""
import argparse
import json
import math
import os
from pathlib import Path
import random
import statistics
import subprocess
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASELINE = '54e8ff2ca635d0f8de4a54026774461aacaca18a'


def summary(values):
    values = sorted(values)
    return {"n": len(values), "median_ms": round(statistics.median(values), 2),
            "p95_ms": round(values[max(0, math.ceil(.95 * len(values)) - 1)], 2),
            "min_ms": round(values[0], 2), "max_ms": round(values[-1], 2)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples', type=int, default=20)
    parser.add_argument('--output', type=Path, default=HERE / 'toggle-app-results.json')
    args = parser.parse_args()
    results = {"samples": [], "overheads": {}, "metadata": {}}
    results['metadata'] = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        'os': subprocess.check_output(['sw_vers'], text=True).strip(),
        'cpu': subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string'], text=True).strip(),
        'samples_per_case': args.samples,
        'baseline_commit': BASELINE,
        'note': 'Warm filesystem caches; fresh process per sample; seeded interleaving; observer outside command timing.'}
    with tempfile.TemporaryDirectory(prefix='toggle-app-bench-') as td:
        tmp = Path(td)
        subprocess.run(['swiftc', str(HERE / 'toggle-observer.swift'), '-o', str(tmp / 'observer')], check=True)
        observer = subprocess.Popen([str(tmp / 'observer')], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

        def observe(op='state', pid=-1):
            observer.stdin.write(json.dumps({'op': op, 'pid': pid}) + '\n')
            observer.stdin.flush()
            return json.loads(observer.stdout.readline())

        initial = observe()
        original_pid = initial['front']
        chrome_pids = [a['pid'] for a in initial['apps'] if a['name'] == 'Google Chrome']
        finder_pid = next(a['pid'] for a in initial['apps'] if a['name'] == 'Finder')
        # Main desktop Chrome has no --user-data-dir command-line override.
        chrome_pid = next(pid for pid in chrome_pids if '--user-data-dir' not in subprocess.check_output(['ps', '-p', str(pid), '-o', 'command='], text=True))
        results['metadata']['chrome_pid'] = chrome_pid
        results['metadata']['chrome_instance_count'] = len(chrome_pids)
        env = dict(os.environ, TOGGLE_BENCH_LOG_DIR=str(tmp))
        old = subprocess.check_output(['git', 'show', BASELINE + ':custom/toggle_app.sh'], cwd=ROOT, text=True)
        current = (ROOT / 'custom/toggle_app.sh').read_text()
        for name, source in [('old_applescript', old), ('current_shell_jxa', current)]:
            source = source.replace('KSDIR="$HOME/.local/share/keystat"', 'KSDIR="$TOGGLE_BENCH_LOG_DIR"')
            (tmp / (name + '.sh')).write_text(source)
        variants = {
            'old_applescript': ['bash', str(tmp / 'old_applescript.sh'), 'Google Chrome'],
            'current_shell_jxa': ['bash', str(tmp / 'current_shell_jxa.sh'), 'Google Chrome'],
            'all_jxa': ['osascript', '-l', 'JavaScript', str(HERE / 'toggle-app.jxa.js'), 'Google Chrome'],
            'all_jxa_native_activate': ['osascript', '-l', 'JavaScript', str(HERE / 'toggle-app.jxa.js'), 'Google Chrome', 'Google Chrome', '--native-activate'],
        }
        overheads = {
            'bash_empty': ['bash', '-c', ':'],
            'bash_date': ['bash', '-c', 'date +%s >/dev/null'],
            'applescript_empty': ['osascript', '-e', 'return'],
            'jxa_empty': ['osascript', '-l', 'JavaScript', '-e', 'void 0;'],
            'jxa_appkit_import': ['osascript', '-l', 'JavaScript', '-e', "ObjC.import('AppKit'); void 0;"],
            'jxa_front_read': ['osascript', '-l', 'JavaScript', '-e', "ObjC.import('AppKit'); ObjC.unwrap($.NSWorkspace.sharedWorkspace.frontmostApplication.localizedName); void 0;"],
        }

        def invoke(command):
            start = time.perf_counter_ns()
            p = subprocess.run(command, capture_output=True, text=True, env=env, timeout=10)
            elapsed = (time.perf_counter_ns() - start) / 1e6
            if p.returncode:
                raise RuntimeError(f'{command}: {p.stderr}')
            return elapsed

        try:
            for name, cmd in overheads.items():
                invoke(cmd)
                results['overheads'][name] = summary([invoke(cmd) for _ in range(args.samples)])
                print('OVERHEAD', name, results['overheads'][name], flush=True)
            jobs = [(name, action) for _ in range(args.samples + 2) for name in variants for action in ('hide', 'activate')]
            random.Random(20261021).shuffle(jobs)
            counts = {}
            for name, action in jobs:
                expected_pid = chrome_pid if action == 'hide' else finder_pid
                pre = observe('activate', expected_pid)
                if pre['front'] != expected_pid or pre['hidden']:
                    raise RuntimeError(f'Precondition failed: {name} {action}: {pre}')
                # Let focus transitions settle outside the timed region.
                time.sleep(.08)
                elapsed = invoke(variants[name])
                state = observe(pid=chrome_pid)
                success = state['hidden'] if action == 'hide' else state['frontName'] == 'Google Chrome'
                deadline = time.monotonic() + 1
                while not success and time.monotonic() < deadline:
                    time.sleep(.01)
                    state = observe(pid=chrome_pid)
                    success = state['hidden'] if action == 'hide' else state['frontName'] == 'Google Chrome'
                key = (name, action)
                counts[key] = counts.get(key, 0) + 1
                if counts[key] > 2:
                    results['samples'].append({'variant': name, 'action': action, 'command_ms': round(elapsed, 3), 'success': bool(success)})
                if not success:
                    print('ACTION FAILED', name, action, state, flush=True)
                if len(results['samples']) and len(results['samples']) % 20 == 0:
                    print('SAMPLES', len(results['samples']), flush=True)
            # Check that the same-name automation instance can also be hidden.
            results['same_name_regression'] = []
            other_pids = [pid for pid in chrome_pids if pid != chrome_pid]
            for name in variants:
                for pid in other_pids:
                    pre = observe('activate', pid)
                    if pre['front'] != pid:
                        raise RuntimeError(f'Could not activate regression PID {pid}')
                    invoke(variants[name])
                    time.sleep(.1)
                    state = observe(pid=pid)
                    results['same_name_regression'].append({'variant': name, 'hidden': state['hidden']})
            log_lines = (tmp / 'shell.jsonl').read_text().splitlines()
            results['log_entries'] = len(log_lines)
            results['logs_valid'] = all(json.loads(line)['cmd'] == 'Google Chrome' for line in log_lines)
        finally:
            observe('activate', original_pid)
            observer.stdin.close()
            observer.wait(timeout=5)
    results['summary'] = []
    for name in variants:
        for action in ('hide', 'activate'):
            rows = [s for s in results['samples'] if s['variant'] == name and s['action'] == action]
            if rows:
                result = dict(variant=name, action=action, **summary([r['command_ms'] for r in rows]), successes=sum(r['success'] for r in rows))
                results['summary'].append(result)
                print('RESULT', json.dumps(result), flush=True)
    args.output.write_text(json.dumps(results, indent=2) + '\n')
    print('SAVED', args.output, flush=True)


if __name__ == '__main__':
    main()
