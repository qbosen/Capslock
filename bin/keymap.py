#!/usr/bin/env python3
"""把 capslock 配置渲染成可交互键位图 keymap.html。

用法：
    python3 bin/keymap.py          # 生成 keymap.html
    make keymap                    # 同上

所有中文说法、界面文案、键盘布局都在 custom/keymap.yml 里，这个脚本只负责搬运和拼装；
改快捷键改 custom/capslock.yml，改外部热键改 custom/external.yml，改说法改 custom/keymap.yml。
"""

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).with_name("keymap_template.html")
OUTPUT = ROOT / "keymap.html"
UI_CONFIG = ROOT / "custom/keymap.yml"

# Hyper = CapsLock 映射出的四个右修饰键
HYPER = {"right_command", "right_control", "right_shift", "right_option"}

# 第一个是默认加载的配置
SOURCES = [
    ("custom", "custom/capslock.yml"),
    ("mac_v3", "mac_v3/capslock.yml"),
    ("mac_v2", "mac_v2/capslock.json"),
    ("mac_v1", "mac/capslock.json"),
]

UI = yaml.safe_load(UI_CONFIG.read_text())
GROUPS = UI["groups"]
ACTIONS = UI["actions"]
SYMBOL = UI["symbols"]
KEY_SYMBOL = UI["keys"]
LAYERS = UI["layers"]

# 外部快捷键的 keys 语法
EXT_MODS = {
    "cmd": "left_command", "command": "left_command", "⌘": "left_command",
    "shift": "left_shift", "⇧": "left_shift",
    "option": "left_option", "opt": "left_option", "alt": "left_option", "⌥": "left_option",
    "control": "left_control", "ctrl": "left_control", "⌃": "left_control",
    "fn": "fn", "super": "left_command",
}

EXT_KEYS = {
    "space": "spacebar", "esc": "escape", "enter": "return_or_enter", "return": "return_or_enter",
    "delete": "delete_or_backspace", "backspace": "delete_or_backspace",
    "left": "left_arrow", "right": "right_arrow", "up": "up_arrow", "down": "down_arrow",
    "-": "hyphen", "=": "equal_sign", "[": "open_bracket", "]": "close_bracket",
    ";": "semicolon", "'": "quote", ",": "comma", ".": "period", "/": "slash",
    "`": "grave_accent_and_tilde",
}

# ── 输出信号：这条规则打到浏览器里会长什么样 ──────────────────────
# Karabiner 改写发生在浏览器之前，网页只看得见「输出」。练习页就靠比对这个信号来判定
# 「刚才那一下按对了没有」。判定不出来的（鼠标、shell、变量）返回 None，练习页只能当闪卡。
DOM_KEYS = {
    "left_arrow": "ArrowLeft", "right_arrow": "ArrowRight",
    "up_arrow": "ArrowUp", "down_arrow": "ArrowDown",
    "delete_or_backspace": "Backspace", "delete_forward": "Delete",
    "return_or_enter": "Enter", "escape": "Escape", "tab": "Tab", "spacebar": " ",
    "home": "Home", "end": "End", "page_up": "PageUp", "page_down": "PageDown",
}
DOM_PUNCT = {
    "hyphen": "-", "equal_sign": "=", "open_bracket": "[", "close_bracket": "]",
    "semicolon": ";", "quote": "'", "comma": ",", "period": ".", "slash": "/",
    "backslash": "\\", "grave_accent_and_tilde": "`",
}
DOM_MODS = {"command": "cmd", "control": "ctrl", "option": "opt", "shift": "shift"}
# US 布局下按住 shift 实际打出来的字符
SHIFTED = {
    "1": "!", "2": "@", "3": "#", "4": "$", "5": "%", "6": "^", "7": "&", "8": "*",
    "9": "(", "0": ")", "-": "_", "=": "+", "[": "{", "]": "}", ";": ":", "'": '"',
    ",": "<", ".": ">", "/": "?", "\\": "|", "`": "~",
}

_missing = set()


def dom_signal(actions):
    """把 to 动作译成浏览器 keydown 的写法，如 'cmd+ArrowLeft' / '!' / 'Backspace'。"""
    acts = [a for a in (actions or []) if "set_notification_message" not in a]
    if len(acts) != 1 or "key_code" not in acts[0]:
        return None  # 多段动作或非按键输出，判不了
    a = acts[0]
    ch = DOM_KEYS.get(a["key_code"]) or DOM_PUNCT.get(a["key_code"])
    if ch is None:
        ch = a["key_code"] if len(a["key_code"]) == 1 else None
    if ch is None:
        return None
    mods = set()
    for raw in a.get("modifiers") or []:
        base = raw.replace("left_", "").replace("right_", "")
        if base in DOM_MODS:
            mods.add(DOM_MODS[base])
    # 字符键上的 shift 已经体现在字符本身（shift+1 就是 !），不再单列
    if len(ch) == 1 and "shift" in mods:
        ch = SHIFTED.get(ch, ch.upper())
        mods.discard("shift")
    return "+".join([m for m in ("cmd", "ctrl", "opt", "shift") if m in mods] + [ch])


def load_screens():
    """屏幕编号来自 custom/screens.yml，据此给「跳到第 N 块屏幕」生成中文标签。"""
    path = ROOT / "custom/screens.yml"
    if not path.exists():
        return
    for s in (yaml.safe_load(path.read_text()) or {}).get("screens", []):
        ACTIONS[f"jump to screen {s['n']}"] = UI["ui"]["screen_jump"].format(**s)


def load(path):
    text = path.read_text()
    return yaml.safe_load(text) if path.suffix in (".yml", ".yaml") else json.loads(text)


def key_name(code):
    return KEY_SYMBOL.get(code, code.upper() if len(code) == 1 else code)


def layer(hyper, extra):
    """位面标识：Hyper 系与非 Hyper 系各自按「额外按住的修饰键」区分。"""
    syms = [SYMBOL.get(m, m) for m in extra]
    if hyper:
        if not extra:
            return "hyper", LAYERS["hyper_alone"], []
        return "hyper+" + "+".join(extra), LAYERS["hyper_prefix"] + "".join(syms), syms
    if not extra:
        return "mod:none", LAYERS["no_modifier"], []
    return "mod:" + "+".join(extra), "".join(syms), syms


def layer_of(manipulator):
    """带 variable_if 条件的规则只在某个模式里生效，单独归为一个位面。"""
    from_ = manipulator.get("from") or {}
    mods = set((from_.get("modifiers") or {}).get("mandatory") or [])
    is_hyper = HYPER <= mods
    # 一条规则可能同时挂几个模式条件（区域定位就是「鼠标模式」套「按住 Tab」），
    # 全部收下才能说清它到底什么时候生效——只取第一个会把子层当成父层。
    modes = [c["name"] for c in manipulator.get("conditions") or []
             if c.get("type") == "variable_if" and c.get("name") in LAYERS.get("modes", {})]
    if modes:
        # 模式里的规则一样可能带 Hyper（比如「已在鼠标模式时再按 ⇪R 退出」）。
        # 不先剥掉的话，四个 right_* 会被当成普通修饰键摊成 ⌘⌃⌥⇧，看着像另一个位面。
        extra = sorted(mods - HYPER) if is_hyper else sorted(mods)
        syms = ([SYMBOL["hyper"]] if is_hyper else []) + [SYMBOL.get(m, m) for m in extra]
        # 修饰键要进位面 ID，否则「⇪R 退出」和普通模式键会共用一个 ID 却顶着两个名字
        lid = "mode:" + "+".join(modes + (["hyper"] if is_hyper else []) + extra)
        name = LAYERS["mode_sep"].join(LAYERS["modes"][m] for m in modes)
        return lid, name + ("".join(syms) and " + " + "".join(syms)), syms
    return layer(is_hyper, sorted(mods - HYPER if is_hyper else mods))


def summarize_to(actions):
    """把 to 数组转成一行可读文本，例如 '⌘→' 或 'shell: toggle_app Obsidian'。"""
    out = []
    for a in actions or []:
        if "key_code" in a:
            mods = "".join(SYMBOL.get(m, m) for m in a.get("modifiers") or [])
            out.append(mods + key_name(a["key_code"]))
        elif "shell_command" in a:
            out.append("shell: " + a["shell_command"])
        elif "consumer_key_code" in a:
            out.append("media: " + a["consumer_key_code"])
        elif "pointing_button" in a:
            out.append("button " + a["pointing_button"])
        elif "mouse_key" in a:
            out.append("mouse_key " + json.dumps(a["mouse_key"], ensure_ascii=False))
        elif "set_variable" in a:
            v = a["set_variable"]
            out.append(f"variable {v.get('name')}={v.get('value')}")
        elif "software_function" in a:
            out.append("software_function " + json.dumps(a["software_function"], ensure_ascii=False))
        elif "set_notification_message" in a:
            continue  # 只是屏幕提示，不算动作
        else:
            out.append(json.dumps(a, ensure_ascii=False))
    return " → ".join(out) if out else UI["ui"]["no_output"]


def label_for(manipulator, to_summary):
    """键帽上显示的中文短标签：取描述里等号右边的动作，查 actions 表。"""
    desc = (manipulator.get("description") or "").strip()
    if not desc:
        return to_summary
    action = desc.split("=", 1)[1].strip() if "=" in desc else desc
    # 'mouse mode: h = ...' 这类前缀不参与查表
    zh = ACTIONS.get(action)
    if zh:
        return zh
    _missing.add(action)
    return action or to_summary


def parse_keys(spec):
    """'hyper+cmd+1' → (是否含 Hyper, [修饰键...], 按键)"""
    parts = [p.strip().lower() for p in str(spec).split("+") if p.strip()]
    hyper = "hyper" in parts
    parts = [p for p in parts if p != "hyper"]
    mods, key = [], None
    for p in parts:
        # 单独一个 fn 是按键本身，和别的修饰键连用时才是修饰键
        if p in EXT_MODS and not (p == "fn" and len(parts) == 1):
            mods.append(EXT_MODS[p])
        else:
            key = EXT_KEYS.get(p, p)
    return hyper, sorted(set(mods)), key


def collect_external():
    path = ROOT / "custom/external.yml"
    if not path.exists():
        return [], []
    cfg = yaml.safe_load(path.read_text()) or {}
    entries, groups = [], []
    for g in cfg.get("groups", []):
        if g.get("hidden"):
            continue
        gid = "ext:" + g["name"]
        items = [it for it in (g.get("items") or []) if not it.get("hidden")]
        for it in items:
            hyper, mods, key = parse_keys(it["keys"])
            if not key:
                print(f"跳过（解析不出按键）：{it}", file=sys.stderr)
                continue
            lid, lname, syms = layer(hyper, mods)
            combo = (SYMBOL["hyper"] + " " if hyper else "") + " ".join(syms + [key_name(key)])
            src = it.get("app", "")
            if it.get("verified"):
                src += " · " + UI["ui"].get("verified", "已验证")
            elif it.get("note"):
                src += " · " + it["note"]
            entries.append({
                "key": key, "key_label": key_name(key),
                "layer": lid, "layer_name": lname, "combo": combo.strip(),
                "group": gid, "group_zh": g["name"],
                "desc": it.get("verified") or it.get("note", ""),
                "to": src, "label": it["label"],
            })
        if items:
            groups.append({"id": gid, "zh": g["name"], "note": g.get("note", ""), "n": len(items)})
    return entries, groups


def collect_apps():
    """应用内快捷键：只在某个应用前台时生效，位面独立于全局热键。"""
    path = ROOT / "custom/apps.yml"
    if not path.exists():
        return [], []
    cfg = yaml.safe_load(path.read_text()) or {}
    entries, groups = [], []
    for app in cfg.get("apps", []):
        for g in app.get("groups", []):
            if g.get("hidden"):
                continue
            gid = f"app:{app['app']}:{g['name']}"
            zh = f"{app['app']} · {g['name']}"
            short = g["name"]  # 一级分类已经是应用名，二级导航里不必重复
            items = [it for it in (g.get("items") or []) if not it.get("hidden")]
            for it in items:
                _, mods, key = parse_keys(it["keys"])
                if not key:
                    print(f"跳过（解析不出按键）：{it}", file=sys.stderr)
                    continue
                syms = [SYMBOL.get(m, m) for m in mods]
                entries.append({
                    "key": key, "key_label": key_name(key),
                    "layer": f"app:{app['app']}", "layer_name": app["app"],
                    "combo": " ".join(syms + [key_name(key)]),
                    "group": gid, "group_zh": zh,
                    "desc": it.get("action", ""),
                    "to": it.get("action", ""), "label": it["label"],
                })
            if items:
                groups.append({"id": gid, "zh": zh, "short": short,
                               "note": g.get("note", ""), "n": len(items)})
    return entries, groups


def collect_keyboard():
    """Q10 固件层：键盘自己发出的键，不经 Karabiner，单独成一个位面。"""
    path = ROOT / "custom/keyboard.yml"
    if not path.exists():
        return [], []
    cfg = yaml.safe_load(path.read_text()) or {}
    lname = LAYERS.get("firmware", "firmware")
    entries, groups = [], []
    for g in cfg.get("groups", []):
        gid = "hw:" + g["name"]
        items = g.get("items") or []
        for it in items:
            entries.append({
                "key": it["key"], "key_label": key_name(it["key"]),
                "layer": "hw", "layer_name": lname,
                "combo": key_name(it["key"]),
                "group": gid, "group_zh": g["name"],
                "desc": it.get("note", ""),
                "to": it.get("emits", ""), "label": it["label"],
            })
        if items:
            groups.append({"id": gid, "zh": g["name"], "note": g.get("note", ""), "n": len(items)})
    return entries, groups


def collect(name, rel):
    path = ROOT / rel
    if not path.exists():
        return None
    cfg = load(path)
    entries, groups = [], []
    for rule in cfg.get("rules", []):
        group = rule.get("description", "")
        meta = GROUPS.get(group, {})
        group_zh, group_note = meta.get("zh", group), meta.get("note", "")
        items = 0
        for m in rule.get("manipulators", []):
            from_ = m.get("from") or {}
            code = from_.get("key_code") or from_.get("pointing_button")
            if not code:
                continue
            # 快慢档之类的变体条件不单列，只保留基础那条
            if any(c.get("name") in LAYERS.get("variant_conditions", [])
                   for c in (m.get("conditions") or [])):
                continue
            lid, lname, syms = layer_of(m)
            to_summary = summarize_to(m.get("to") or m.get("to_if_alone"))
            combo = (SYMBOL["hyper"] + " " if lid.startswith("hyper") else "") + " ".join(syms + [key_name(code)])
            entries.append({
                "key": code, "key_label": key_name(code),
                "layer": lid, "layer_name": lname, "combo": combo.strip(),
                "group": group, "group_zh": group_zh,
                "desc": m.get("description", ""),
                "to": to_summary,
                "label": label_for(m, to_summary),
                "signal": dom_signal(m.get("to") or m.get("to_if_alone")),
            })
            items += 1
        if items:
            groups.append({"id": group, "zh": group_zh, "note": group_note, "n": items})
    return {
        "title": cfg.get("title", name),
        "source": rel,
        "groups": groups,
        "entries": entries,
    }


def main():
    load_screens()
    configs = {}
    for name, rel in SOURCES:
        got = collect(name, rel)
        if got:
            configs[name] = got
        else:
            print(f"跳过（文件不存在）：{rel}", file=sys.stderr)

    if not configs:
        sys.exit("没有找到任何配置文件")

    # 外部快捷键和键盘固件层都是这台机器的现状，只并入当前使用的那份配置
    hw_entries, hw_groups = collect_keyboard()
    if hw_entries and SOURCES[0][0] in configs:
        configs[SOURCES[0][0]]["entries"] += hw_entries
        configs[SOURCES[0][0]]["groups"] += hw_groups
        print(f"并入键盘固件层 {len(hw_entries)} 条 / {len(hw_groups)} 组")

    app_entries, app_groups = collect_apps()
    if app_entries and SOURCES[0][0] in configs:
        configs[SOURCES[0][0]]["entries"] += app_entries
        configs[SOURCES[0][0]]["groups"] += app_groups
        print(f"并入应用内快捷键 {len(app_entries)} 条 / {len(app_groups)} 组")

    ext_entries, ext_groups = collect_external()
    if ext_entries and SOURCES[0][0] in configs:
        cur = configs[SOURCES[0][0]]
        index = {(e["layer"], e["key"]): e for e in cur["entries"]}
        added, merged = [], 0
        for x in ext_entries:
            hit = index.get((x["layer"], x["key"]))
            if hit:
                # Karabiner 只负责把键发出去，真正接手的是这个应用——标注而非重复列一行
                hit["to"] = f'{hit["to"]}　⟵ {x["to"]}'
                merged += 1
            else:
                added.append(x)
        cur["entries"] += added
        for g in ext_groups:
            g["n"] = sum(1 for e in added if e["group"] == g["id"])
        cur["groups"] += [g for g in ext_groups if g["n"]]
        print(f"并入外部快捷键：新增 {len(added)} 条，与 Karabiner 规则合并标注 {merged} 条")

    data = {
        "default": SOURCES[0][0],
        "configs": configs,
        "ui": UI["ui"],
        "layers": LAYERS,
        "keyboards": UI["keyboards"],
        "categories": UI.get("categories", []),
        # 练习页判定答案时复用配置文件同一套按键写法（space/esc/enter…），保持一致
        "practice": {**UI.get("practice", {}), "key_aliases": EXT_KEYS},
    }
    html = TEMPLATE.read_text().replace("/*__DATA__*/{}", json.dumps(data, ensure_ascii=False))
    OUTPUT.write_text(html)

    total = sum(len(c["entries"]) for c in configs.values())
    print(f"已生成 {OUTPUT.relative_to(ROOT)} · {len(configs)} 份配置 · {total} 条映射")
    if _missing:
        print(f"以下 {len(_missing)} 个动作暂无中文，已按原文显示（补进 custom/keymap.yml 的 actions）：")
        for a in sorted(_missing):
            print("   ", a)


if __name__ == "__main__":
    main()
