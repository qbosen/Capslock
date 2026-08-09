#!/usr/bin/env python3
"""快捷键使用分析：把 keystatd 采集的事件对回 capslock.yml / external.yml 的键位。

用法：
    python3 bin/keystat/report.py            # 全部数据
    python3 bin/keystat/report.py --days 14  # 只看最近 14 天
    make keystat-report

归因分两条路：
  1) 事件里还带着 Hyper（四个右修饰键都按下）——说明 Karabiner 没有改写它，
     按下的就是原始组合，直接按「位面 + 按键」认领，外部应用注册的热键都走这条。
  2) 事件不带 Hyper 但紧跟在 Hyper 松开之后——说明 Karabiner 已把它换成了别的键，
     只能拿「输出信号」（键码 + 修饰键）反查是哪条规则发出来的。
"""

import argparse
import glob
import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
LOGS = Path.home() / ".local/share/keystat"
HYPER = {"right_command", "right_control", "right_shift", "right_option"}

# 设备相关位：用来分辨左右修饰键
RIGHT_BITS = 0x04 | 0x10 | 0x40 | 0x2000
DEV_LEFT = {0x08: "command", 0x02: "shift", 0x01: "control", 0x20: "option"}
# 通用掩码：判断原生快捷键按了哪些修饰键
GEN = {0x100000: "command", 0x20000: "shift", 0x80000: "option", 0x40000: "control"}

VK = {
    0: "a", 1: "s", 2: "d", 3: "f", 4: "h", 5: "g", 6: "z", 7: "x", 8: "c", 9: "v",
    11: "b", 12: "q", 13: "w", 14: "e", 15: "r", 16: "y", 17: "t", 18: "1", 19: "2",
    20: "3", 21: "4", 22: "6", 23: "5", 24: "equal_sign", 25: "9", 26: "7",
    27: "hyphen", 28: "8", 29: "0", 30: "close_bracket", 31: "o", 32: "u",
    33: "open_bracket", 34: "i", 35: "p", 36: "return_or_enter", 37: "l", 38: "j",
    39: "quote", 40: "k", 41: "semicolon", 42: "backslash", 43: "comma", 44: "slash",
    45: "n", 46: "m", 47: "period", 48: "tab", 49: "spacebar",
    51: "delete_or_backspace", 53: "escape", 96: "f5", 97: "f6", 98: "f7", 99: "f3",
    100: "f8", 101: "f9", 103: "f11", 105: "f13", 109: "f10", 111: "f12",
    115: "home", 116: "page_up", 117: "delete_forward", 118: "f4", 119: "end",
    120: "f2", 121: "page_down", 122: "f1", 123: "left_arrow", 124: "right_arrow",
    125: "down_arrow", 126: "up_arrow",
}

SYM = {"command": "⌘", "shift": "⇧", "option": "⌥", "control": "⌃"}


def base_mod(m):
    return m.replace("left_", "").replace("right_", "")


def load_rules():
    """返回 (按 Hyper 组合索引的键位, 按输出信号索引的键位)"""
    by_combo, by_output = defaultdict(list), defaultdict(list)
    sys.path.insert(0, str(ROOT / "bin"))
    from keymap import label_for, parse_keys, summarize_to  # 复用中文标签与 keys 语法

    cfg = yaml.safe_load((ROOT / "custom/capslock.yml").read_text())
    for rule in cfg.get("rules", []):
        for m in rule.get("manipulators", []):
            f = m.get("from") or {}
            key = f.get("key_code")
            if not key:
                continue
            mods = set((f.get("modifiers") or {}).get("mandatory") or [])
            item = {
                "group": rule.get("description", ""),
                "desc": label_for(m, summarize_to(m.get("to"))),
                "hyper": HYPER <= mods,
                "extra": frozenset(base_mod(x) for x in mods - HYPER),
                "key": key,
                # 带 variable_if 的规则（⇪+Tab 的 wide 层、鼠标模式）和无条件规则会落进
                # 同一个 by_combo 桶里——因为**采集端只看得见物理按键**，看不出 Tab 或
                # 鼠标模式当时开没开。所以标签得挑无条件那条，那才是常态。
                # 不这么做的话，⇪H 会被报成「选中前一词」（wide 层的动作），
                # 而它实际上是最高频的裸「左移」。
                "conds": len(m.get("conditions") or []),
                # 只有会产生键盘事件或跑 shell 的规则才可能被采集到；
                # pointing_button / mouse_key / software_function / set_variable 一律看不见
                "measurable": any("key_code" in t or "shell_command" in t
                                  for t in (m.get("to") or m.get("to_if_alone") or [])),
                "shell": next((t["shell_command"] for t in (m.get("to") or [])
                               if "shell_command" in t), None),
            }
            by_combo[(item["hyper"], item["extra"], key)].append(item)
            for t in m.get("to") or []:
                if "key_code" in t:
                    sig = (t["key_code"], frozenset(base_mod(x) for x in t.get("modifiers") or []))
                    by_output[sig].append(item)
                    break

    ext = ROOT / "custom/external.yml"
    if ext.exists():
        for g in (yaml.safe_load(ext.read_text()) or {}).get("groups", []):
            for it in g.get("items") or []:
                hyper, mods, key = parse_keys(it["keys"])
                if not key:
                    continue
                by_combo[(hyper, frozenset(base_mod(x) for x in mods), key)].append({
                    "group": g["name"], "desc": it["label"], "hyper": hyper,
                    "extra": frozenset(base_mod(x) for x in mods), "key": key,
                    "shell": None, "app": it.get("app", ""),
                })
    return by_combo, by_output


def load_apps():
    p = LOGS / "apps.tsv"
    if not p.exists():
        return {}
    out = {}
    for line in p.read_text().splitlines():
        f = line.split("\t", 1)
        if len(f) == 2 and f[0].isdigit():
            out[int(f[0])] = f[1]
    return out


def load_events(days):
    cutoff = time.time() - days * 86400 if days else 0
    events, shell = [], []
    for p in sorted(glob.glob(str(LOGS / "events-*.csv"))):
        for line in open(p):
            if line.startswith("#"):
                continue
            f = line.strip().split(",")
            if len(f) < 5:
                continue
            try:
                t, k, fl, h, a = (int(x) for x in f[:5])
            except ValueError:
                continue
            if t < cutoff:
                continue
            events.append({"t": t, "k": k, "f": fl, "h": h, "a": a})
    sp = LOGS / "shell.jsonl"
    if sp.exists():
        for line in open(sp):
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get("t", 0) >= cutoff:
                shell.append(e)
    return events, shell


def combo_text(hyper, extra, key):
    return ("⇪ " if hyper else "") + " ".join(
        [SYM.get(m, m) for m in sorted(extra)] + [key.upper() if len(key) == 1 else key])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=0, help="只看最近 N 天，默认全部")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--json", action="store_true", help="输出结构化数据，便于交给 AI 分析")
    args = ap.parse_args()

    if not LOGS.exists() or not list(LOGS.glob("events-*.csv")):
        sys.exit(f"还没有采集数据。先跑 bin/keystat/install.sh 安装采集器。\n日志目录：{LOGS}")

    by_combo, by_output = load_rules()
    events, shell = load_events(args.days)
    if not events:
        sys.exit("这段时间没有采集到事件。")

    span = (max(e["t"] for e in events) - min(e["t"] for e in events)) / 86400
    days = max(span, 1 / 24)

    apps = load_apps()
    hits = Counter()          # (hyper, extra, key) -> 次数
    native = Counter()        # 应用内 / 原生快捷键 (app, mods, key) -> 次数
    per_app = Counter()       # 每个应用里按了多少次快捷键
    unknown = 0

    for e in events:
        per_app[apps.get(e["a"], "?")] += 1
        f, k = e["f"], e["k"]
        key = VK.get(k)
        if not key:
            unknown += 1
            continue
        if (f & RIGHT_BITS) == RIGHT_BITS:
            # 路径一：Hyper 原样透传，按下的就是原始组合
            extra = frozenset(v for bit, v in DEV_LEFT.items() if f & bit)
            hits[(True, extra, key)] += 1
        elif e.get("h"):
            # 路径二：Karabiner 已改写，拿输出信号反查
            mods = frozenset(v for bit, v in GEN.items() if f & bit)
            found = by_output.get((key, mods))
            if found:
                # 多条规则可能发出**一模一样**的输出（⇪⌘⌥H 和 ⇪+Tab 的三份变体都发 ⌥⇧←），
                # 反查时根本分不开。取无条件那条当代表：它是这个动作的"正牌"键位，
                # 条件规则只是它的替身。取 found[0] 会把账全记到写在文件最前面的
                # wide 变体上——那条的 combo 是裸 ⇪H，于是「⇪⌘⌥ 整层没人用」是假象，
                # 而 ⇪H 的次数被灌了水。
                it = min(found, key=lambda i: i.get("conds", 0))
                hits[(it["hyper"], it["extra"], it["key"])] += 1
            else:
                unknown += 1
        else:
            # 不经 Hyper 的组合：可能是 external.yml 里登记的全局热键，
            # 也可能只是这个应用自己的快捷键。
            #
            # 先查 external.yml。以前直接全丢进 native，后果是**所有非 Hyper 的
            # 全局热键永远显示「从未用过」**——⌘space 的 Alfred、⌥A 的 Bob、
            # ⌘⇧4 的截图都在这份名单上，而它们天天在按。同样是「测不到」被当成
            # 「没人用」，和鼠标模式那批是一个毛病。
            mods = frozenset(v for bit, v in GEN.items() if f & bit)
            if mods:
                if (False, mods, key) in by_combo:
                    hits[(False, mods, key)] += 1
                else:
                    native[(apps.get(e["a"], "?"), mods, key)] += 1

    for s in shell:
        for k, items in by_combo.items():
            if any(it.get("shell") and s.get("cmd", "") in it["shell"] for it in items):
                hits[k] += 1
                break

    rows = []
    for k, items in by_combo.items():
        # 无条件的那条优先当标签；同为无条件时保持文件里的先后
        it = min(items, key=lambda i: i.get("conds", 0))
        # 同一物理组合下还有别的解释（wide 层 / 鼠标模式）时标一下：
        # 计数是合并的，采集端分不开，看的人得知道这一点
        alt = len({i["desc"] for i in items if i["desc"] != it["desc"]})
        c = hits.get(k, 0)
        rows.append({
            "combo": combo_text(*k),
            "desc": (it["desc"] or it.get("app", "")) + (f" (+{alt})" if alt else ""),
            "group": it["group"], "count": c, "per_day": c / days,
            # 跟标签取同一条代表规则，别用 any()：⇪⌥I 的常态是「鼠标后退」（测不到），
            # 只有按住 Tab 才是「选到行首」（测得到）。用 any() 会判成"可测且没人用"，
            # 正好把一个天天在用的键推进待删名单。
            "measurable": it.get("measurable", True),
            "hyper": k[0], "extra": k[1],
        })
    used = sorted((r for r in rows if r["count"]), key=lambda r: -r["count"])
    unused = [r for r in rows if not r["count"]]

    if args.json:
        print(json.dumps({
            "days": round(days, 2),
            "总命中": sum(hits.values()),
            "原生快捷键次数": sum(native.values()),
            "键位": [{k: (sorted(v) if isinstance(v, frozenset) else
                          round(v, 2) if isinstance(v, float) else v)
                      for k, v in r.items()} for r in sorted(rows, key=lambda r: -r["count"])],
            "各应用快捷键次数": dict(per_app.most_common()),
            "原生快捷键": [
                {"应用": app, "修饰键": sorted(mods), "键": key, "次数": c}
                for (app, mods, key), c in native.most_common(40)],
        }, ensure_ascii=False, indent=2))
        return

    print(f"\n采集区间 {days:.1f} 天 · 命中键位 {sum(hits.values())} 次 · "
          f"原生快捷键 {sum(native.values())} 次 · 未归因 {unknown} 次\n")

    print(f"── 用得最多的 {args.top} 个键位 " + "─" * 30)
    for r in used[:args.top]:
        print(f"  {r['combo']:<14} {r['desc'][:22]:<24} {r['count']:>5} 次   {r['per_day']:.1f}/天")

    # 「从未用过」是删键决策的输入，所以必须先把**测不到的**摘出去。
    # 采集器挂的是键盘事件，靠输出信号反查。发鼠标键 / 光标定位 / 只设变量的规则
    # 压根不产生键盘事件，永远是 0 次——那不是"没人用"，是"看不见"。
    # 鼠标模式整组 41 条都属于这一类，混在一起会诱导人删掉天天在用的键。
    blind = [r for r in unused if not r.get("measurable", True)]
    dead = [r for r in unused if r.get("measurable", True)]

    def dump(title, rows):
        by_group = defaultdict(list)
        for r in rows:
            by_group[r["group"]].append(r["combo"])
        for g, cs in sorted(by_group.items(), key=lambda x: -len(x[1])):
            print(f"  {g}：{'  '.join(cs)}")

    print(f"\n── 从未用过（{len(dead)} 个，这些才是可以考虑腾掉的） " + "─" * 12)
    dump(None, dead)
    if blind:
        print(f"\n── 测不到（{len(blind)} 个，不代表没用） " + "─" * 22)
        print("  发的是鼠标键 / 光标定位 / 只设变量，不产生键盘事件，采集器看不见。")
        dump(None, blind)

    print(f"\n── 快捷键用得最多的应用 " + "─" * 30)
    for app, c in per_app.most_common(8):
        print(f"  {app:<38} {c:>5} 次   {c / days:.1f}/天")

    print(f"\n── 高频原生快捷键（还没进 Hyper 层） " + "─" * 20)
    for (app, mods, key), c in native.most_common(12):
        combo = "".join(SYM.get(m, m) for m in sorted(mods)) + (key.upper() if len(key) == 1 else key)
        print(f"  {combo:<12} {app.split('.')[-1][:20]:<22} {c:>5} 次   {c / days:.1f}/天")

    print(f"\n想让 AI 分析并给优化建议，把结构化数据交给它："
          f"\n  python3 bin/keystat/report.py --json | pbcopy\n")


if __name__ == "__main__":
    main()
