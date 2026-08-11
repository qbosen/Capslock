# 练习页交互翻新 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 翻新键位图练习页——自由模式变闯关清单、闪卡改 Anki 自评、修复考试模式抽题、全套键帽视觉与对错动效。

**Architecture:** 只动 `bin/keymap_template.html` 的练习区 CSS/JS 和 `custom/keymap.yml` 的 `practice.ui` 文案段;产物仍是 `make keymap` 生成的单文件 `keymap.html`。判定原理不变:比对 Karabiner 输出信号(`entry.signal`)与浏览器 keydown。

**Tech Stack:** 原生 JS(模板内联脚本,无依赖)、CSS keyframes、YAML 文案配置、`make keymap`(Python 生成器,不改)。

## Global Constraints

- 模板里**零渲染中文**:所有界面文案一律进 `custom/keymap.yml` 的 `practice.ui`(仓库铁律,见 CLAUDE.md)。
- 不引入任何外部依赖、不改 `bin/keymap.py`、不改 `entry.signal` 判定原理。
- `dStats` 存储结构保持 `{n, ok, ms}`,localStorage key `capslock-drill-stats` 不变,老数据必须兼容。
- 沿用页面现有 CSS 变量(`--hit`、`--key-line`、`--card` 等),深浅色都要正常。
- 对/错色沿用现有硬编码 `#16a34a` / `#dc2626`(和现有 `.ok`/`.bad` 一致)。
- 仓库无 JS 测试框架,不新建。每个任务的机器验证 = 抽出内联脚本跑 `node --check`(语法级);行为验证 = `make keymap` 后浏览器手测,最后一个任务集中过全量清单。
- combo 的数据格式:键帽以空格分隔(如 `⇪ ⇧ H`),别名以 `UI.alias_sep`(值为 `" / "`)连接。
- 提交信息用中文,风格照 `git log`(如 `feat(keymap): ...`)。

**语法检查命令**(每个改模板的任务都用它,记作 `node-check`):

```bash
cd ~/workspace/personal/Capslock && python3 - <<'EOF'
p = 'bin/keymap_template.html'
s = open(p).read().split('<script>')[1].split('</script>')[0]
open('/tmp/keymap-inline.js', 'w').write(s)
EOF
node --check /tmp/keymap-inline.js && echo SYNTAX-OK
```

---

### Task 1: 键帽渲染器 + 练习区新 CSS(纯基建,无行为变化)

**Files:**
- Modify: `bin/keymap_template.html`(CSS 块 228-289 行附近追加;JS 工具区 `esc()` 之后加函数)

**Interfaces:**
- Produces: `kbdCombo(combo: string) → html string`——把 `"⇪ ⇧ H"` 渲染成一排 `<kbd>`;含 `" / "` 别名时各渲染一组,用 `.ksep` 分隔。后续所有任务用它渲染组合键。
- Produces: CSS 类 `.kcombo` `.ksep` `.flash-ok` `.flash-bad` `.qwrap` `.ansbox` `.citem`(及 `.lit/.lock/.just/.cdot/.clabel/.ctag`)`.cdone` `.dots`。

- [ ] **Step 1: 加 kbdCombo 函数**

在 `esc()` 函数定义之后插入:

```js
/** 把「⇪ ⇧ H」渲染成一排键帽;别名(⌘1 / ⌘Q)各渲染一组,用分隔符连接 */
function kbdCombo(combo) {
  return String(combo).split(UI.alias_sep).map(alt =>
    `<span class="kcombo">` + alt.trim().split(/\s+/).map(t => `<kbd>${esc(t)}</kbd>`).join("") + `</span>`
  ).join(`<span class="ksep">${esc(UI.alias_sep.trim())}</span>`);
}
```

解析不出的片段走 `esc()` 原样输出(`split` 天然兜底,不吞字)。

- [ ] **Step 2: 追加练习区 CSS**

在 `/* ── 练习视图 ── */` 段落末尾(`.rpt .big` 规则之后)追加:

```css
  /* 键帽渲染 */
  .kcombo { display: inline-flex; gap: 3px; vertical-align: middle; }
  .kcombo kbd {
    display: inline-block; min-width: 21px; padding: 2px 6px; text-align: center;
    font: 12px/1.4 ui-monospace, "SF Mono", Menlo, monospace;
    background: var(--key); color: var(--fg);
    border: 1px solid var(--key-line); border-bottom-width: 2px; border-radius: 5px;
  }
  .ksep { margin: 0 6px; color: var(--faint); font-size: 11px; }

  /* 对错动效 */
  @keyframes kpulse { from { box-shadow: 0 0 0 0 #16a34a55; } to { box-shadow: 0 0 0 12px #16a34a00; } }
  @keyframes kshake { 0%, 100% { transform: none; } 25% { transform: translateX(-5px); } 75% { transform: translateX(5px); } }
  .flash-ok { animation: kpulse .45s ease-out; }
  .flash-bad { animation: kshake .3s; }

  /* 考试舞台:题干居中、答案盒 */
  .qwrap { text-align: center; padding: 8px 0 2px; }
  .qwrap .qask { font-size: 24px; }
  .ansbox { text-align: center; padding: 16px 0 10px; font-size: 14px; }
  .ansbox .qmeta { margin: 10px 0 0; }

  /* 闯关清单 */
  .citem {
    display: grid; grid-template-columns: 14px auto minmax(0, 1fr) auto;
    gap: 7px; align-items: center; padding: 4px 0; font-size: 12.5px;
  }
  .citem .cdot { width: 8px; height: 8px; border-radius: 50%; border: 1.5px solid var(--key-line); }
  .citem.lit .cdot { background: #16a34a; border-color: #16a34a; }
  .citem.just .cdot { animation: kpulse .45s ease-out; }
  .citem.lit .clabel { color: var(--faint); text-decoration: line-through; }
  .citem.lock { opacity: .45; }
  .citem .ctag {
    font-size: 10px; padding: 1px 6px; border-radius: 999px;
    background: var(--match-soft); color: var(--match); white-space: nowrap;
  }
  .cdone { margin: 10px 0; font-size: 12.5px; color: #16a34a; }

  /* 考试进度点阵 */
  .dots { display: flex; flex-wrap: wrap; gap: 5px; margin: 8px 0; }
  .dots i { width: 9px; height: 9px; border-radius: 50%; border: 1.5px solid var(--key-line); }
  .dots i.ok { background: #16a34a; border-color: #16a34a; }
  .dots i.bad { background: #dc2626; border-color: #dc2626; }
  .dots i.cur { border-color: var(--hit); box-shadow: 0 0 0 2px var(--hit-soft); }

  /* 组选择条降噪:未选中的 chip 收掉边框 */
  #dfilter .chip:not(.on) { border-color: transparent; background: var(--bg); }
```

- [ ] **Step 3: 语法检查**

Run: `node-check`(见 Global Constraints)
Expected: `SYNTAX-OK`

- [ ] **Step 4: 生成并肉眼确认无回归**

Run: `cd ~/workspace/personal/Capslock/custom && make keymap && open ../keymap.html`
Expected: 练习页与改前行为一致(本任务只加未引用的类和函数)。

- [ ] **Step 5: Commit**

```bash
cd ~/workspace/personal/Capslock
git add bin/keymap_template.html keymap.html
git commit -m "feat(keymap): 练习页基建——键帽渲染器 kbdCombo 与对错动效/清单/点阵 CSS"
```

---

### Task 2: 自由模式 → 闯关清单

**Files:**
- Modify: `bin/keymap_template.html`(`freeStage`、`hintsPanel`、全局 keydown 监听、`renderDrill`、状态变量区)
- Modify: `custom/keymap.yml`(`practice.ui` 增删文案)

**Interfaces:**
- Consumes: `kbdCombo()`、`.citem/.cdone` 等 Task 1 的 CSS 类;现有 `dPool()`、`sigOfEvent()`、`dLive()`、`seedPad()`、`target()`、`chips()`。
- Produces: `checklistPanel(p) → html`(替代 `hintsPanel`)、`freeKey(e)`(自由模式按键处理)、状态 `dLit: Set<entry.id>`。侧栏完成块内按钮 id `#dround`。

- [ ] **Step 1: keymap.yml 文案增删**

`practice.ui` 里,把 `tip` 保留给考试模式开场,并做如下修改:

```yaml
    mode_hint:
      free: 清单上的键位按对一个点亮一个,全点亮完成一轮;不计时不计分
      exam: 从选中的组里抽题,答对进下一题,最后给一份生疏度报告
```

删除键:`hints_title`、`hints_toggle`、`live_title`。
新增键(与 `stats_note` 同级):

```yaml
    tip_free: 光标放进输入框直接按。判定的是 Karabiner 发出的信号,物理方向键也算——练手感,别糊弄自己。
    checklist_title: 本轮清单
    checklist_progress: "点亮 {done} / {total}"
    checklist_done: 全部点亮,这一轮完成了。
    another_round: 再来一轮
    free_only_cards: 选中的组都没法在浏览器里真按——切到考试模式,当闪卡练。
```

- [ ] **Step 2: 状态变量与 freeStage 重写**

状态行 `let dMode = "free", ...` 附近增加:

```js
let dLit = new Set();
```

`freeStage` 整体替换为:

```js
function freeStage(p) {
  const hasPointer = p.some(q => q.kind === "pointer");
  const hasText = p.some(q => q.kind === "text");
  if (!hasText && !hasPointer) return `<div class="none">${esc(PUI.free_only_cards)}</div>`;
  return `<div class="qnote">${esc(PUI.tip_free)}</div>
    ${hasText ? `<textarea id="dpad" spellcheck="false"></textarea>` : ""}
    <div class="live" id="dlive">${esc(PUI.live_none)}</div>
    ${hasPointer ? `<div class="qnote" style="margin:12px 0 0">${esc((PUI.kind_note || {}).pointer)}</div>
      <div class="drange" id="drange"><span class="rt">${esc(fmt(PUI.range_hint, { hit: 0 }))}</span></div>` : ""}`;
}
```

- [ ] **Step 3: hintsPanel → checklistPanel**

删除 `hintsPanel`,新增:

```js
/** 闯关清单:text 类条目按对点亮计入进度;闪卡/鼠标类灰显挂标签,不计数 */
function checklistPanel(p) {
  const text = p.filter(q => q.kind === "text");
  const done = text.filter(q => dLit.has(q.id)).length;
  let last = null;
  const rows = p.map(q => {
    const head = q.group_zh === last ? "" : `<div class="hsub">${esc(q.group_zh)}</div>`;
    last = q.group_zh;
    const lock = q.kind !== "text";
    return head + `<div class="citem ${lock ? "lock" : dLit.has(q.id) ? "lit" : ""}" data-cid="${esc(q.id)}">
        <span class="cdot"></span>${kbdCombo(q.combo)}<span class="clabel">${esc(q.label)}</span>
        ${lock ? `<span class="ctag">${esc(KTAG[q.kind] || "")}</span>` : "<span></span>"}
      </div>`;
  }).join("");
  const doneBlock = text.length && done === text.length
    ? `<div class="cdone">${esc(PUI.checklist_done)}
         <button class="btn tiny" id="dround">${esc(PUI.another_round)}</button></div>` : "";
  return `<h4>${esc(PUI.checklist_title)}</h4>
    <div class="prog">${esc(fmt(PUI.checklist_progress, { done, total: text.length }))}
      <div class="bar"><i style="width:${text.length ? Math.round(done / text.length * 100) : 0}%"></i></div></div>
    ${doneBlock}${rows}`;
}
```

`renderDrill` 里 `hintsPanel(p)` 改为 `checklistPanel(p)`。

- [ ] **Step 4: 自由模式按键处理 freeKey**

全局 keydown 监听器整体替换为分派结构(考试分支本任务先原样搬进 `examKey`,下个任务再重写):

```js
document.addEventListener("keydown", e => {
  if (view !== "drill") return;
  if (dMode === "free") { freeKey(e); return; }
  examKey(e);
});

/** 自由模式:实时解码 + 点亮清单。重画侧栏不动主舞台,textarea 焦点和光标不丢 */
function freeKey(e) {
  const sig = sigOfEvent(e);
  if (!sig) return;
  dLive(sig);
  const pool = dPool();
  const fresh = pool.filter(q => q.kind === "text" && q.signal === sig && !dLit.has(q.id));
  if (!fresh.length) return;
  fresh.forEach(q => dLit.add(q.id));
  $("dside").innerHTML = checklistPanel(pool);
  fresh.forEach(q => {
    const el = document.querySelector(`.citem[data-cid="${CSS.escape(q.id)}"]`);
    if (el) el.classList.add("just");
  });
}

function examKey(e) {
  if (!dQ || dQ.kind !== "text") return;
  const sig = sigOfEvent(e);
  if (!sig) return;
  if (sig === dQ.signal) {
    const pad = $("dpad");
    if (pad) pad.className = "ok";
    setTimeout(() => dAnswer(true), 260);
  }
}
```

- [ ] **Step 5: 「再来一轮」与选组重置**

`$("dfilter").onclick` 里 `dQ = null; dExam = null;` 处追加 `dLit = new Set();`(选组变了清单重开)。`$("config").onchange` 同样追加。
新增侧栏点击处理(放在 `$("dstage").onclick` 旁):

```js
$("dside").onclick = e => {
  if (e.target.closest("#dround")) { dLit = new Set(); renderDrill(); }
};
```

- [ ] **Step 6: 语法检查 + 生成手测**

Run: `node-check`,然后 `cd custom && make keymap && open ../keymap.html`
Expected: 自由模式右侧是键帽清单;按 `⇪H` 等点亮对应项并推进进度条;闪卡/鼠标条目灰显;全点亮出完成块,「再来一轮」清零;textarea 光标不因点亮而丢失。

- [ ] **Step 7: Commit**

```bash
git add bin/keymap_template.html custom/keymap.yml keymap.html
git commit -m "feat(keymap): 自由模式改闯关清单——按对点亮、进度条、再来一轮"
```

---

### Task 3: 考试模式舞台重构(文本题反馈 + 点阵进度)

**Files:**
- Modify: `bin/keymap_template.html`(`examStage`、`progressPanel`、`report`、`examKey`、`dNext`、`dstage` 事件、删 `dCheck`/`dVerdict`)
- Modify: `custom/keymap.yml`(`practice.ui` 增删文案)

**Interfaces:**
- Consumes: `kbdCombo()`、`.qwrap/.ansbox/.dots/.flash-*` 类、Task 2 的 `examKey` 挂载点。
- Produces: `bodyOf(q) → html`(题型主体,Task 4 往里加闪卡分支)、状态 `dRevealed`、`dAdvancing`;`wrongFlash(sig)`。

- [ ] **Step 1: keymap.yml 文案增删**

删除键:`answer_placeholder`、`check`、`right`、`wrong`、`revealed`。
新增键:

```yaml
    answer_title: 答案
    continue_hint: 空格 / 回车 继续
    pressed_other: "你按出的是 {combo} · {label}"
```

- [ ] **Step 2: 状态与 dNext**

状态区 `let dMode = ...` 行:删掉 `dVerdict = null`,追加:

```js
let dRevealed = false, dFlipped = false, dAdvancing = false;
```

`dNext` 里 `dVerdict = null;` 替换为 `dRevealed = dFlipped = dAdvancing = false;`,并把焦点行改为:

```js
  const box = $("dpad");
  if (box) { box.focus(); seedPad(box); }
```

- [ ] **Step 3: examStage + bodyOf 重写**

`examStage` 整体替换(`dgo` 开始/重开逻辑不变):

```js
function examStage(p) {
  if (!dExam) return `<div class="qnote">${esc(PUI.tip)}</div>
    <div class="drow"><button class="btn primary" id="dgo">${esc(PUI.start)}</button></div>`;
  if (!dQ) return report();
  const note = (PUI.kind_note || {})[dQ.kind] || "";
  return `<div class="qwrap">
      <span class="qkind ${dQ.kind === "card" ? "card" : ""}">${esc(PUI["kind_" + dQ.kind])}</span>
      <div class="qask">${esc(dQ.label)}</div>
      <div class="qmeta">${esc(dQ.group_zh)}　·　${esc(PUI.prompt)}？</div>
    </div>
    <div class="qnote">${esc(note)}</div>
    ${bodyOf(dQ)}
    <div class="live" id="qfb"></div>
    <div class="drow">
      <span class="spacer"></span>
      ${dQ.kind === "text" && !dRevealed ? `<button class="btn tiny" id="dreveal">${esc(PUI.reveal)}</button>` : ""}
      <button class="btn tiny" id="dskip">${esc(PUI.skip)}</button>
    </div>`;
}

/** 题型主体。闪卡分支在下一任务补 Anki 流,本任务先渲染答案盒占位 */
function bodyOf(q) {
  if (q.kind === "text") {
    if (dRevealed) return `<div class="ansbox">${esc(PUI.answer_title)}　${kbdCombo(q.combo)}
      <div class="qmeta">${esc(PUI.continue_hint)}</div></div>`;
    return `<textarea id="dpad" spellcheck="false"></textarea>`;
  }
  if (q.kind === "pointer")
    return `<div class="drange" id="drange"><span class="rt">${esc(fmt(PUI.range_hint, { hit: 0 }))}</span></div>`;
  return `<div class="ansbox">${kbdCombo(q.combo)}</div>`;
}
```

注:鼠标题从旧版的「打字作答」改为舞台内出靶子——`renderDrill` 已有 `$("drange")` 挂靶逻辑,`target()` 命中时已调用 `dAnswer(true)`,不用改。

- [ ] **Step 4: examKey 重写(答对推进、按错红闪、看答案后空格继续)**

Task 2 的临时 `examKey` 整体替换:

```js
function examKey(e) {
  const goBtn = $("dgo");
  if (goBtn && (e.key === " " || e.key === "Enter")) { e.preventDefault(); dStart(); return; }
  if (!dExam || !dQ) return;
  if (dQ.kind !== "text") return;   // 闪卡键位在下一任务;鼠标题用点击
  if (dRevealed) {
    if (e.key === " " || e.key === "Enter") { e.preventDefault(); dAnswer(false); }
    return;
  }
  const sig = sigOfEvent(e);
  if (!sig || dAdvancing) return;
  if (sig === dQ.signal) {
    dAdvancing = true;
    const pad = $("dpad");
    if (pad) pad.classList.add("ok", "flash-ok");
    setTimeout(() => dAnswer(true), 260);
    return;
  }
  if (/(?:cmd|ctrl|opt|shift)\+/.test(sig)) wrongFlash(sig);
}

/** 按出了带修饰键但不匹配的信号:红闪 + 告诉你实际触发了什么。纯打字不惩罚 */
function wrongFlash(sig) {
  const pad = $("dpad"), fb = $("qfb");
  if (pad) {
    pad.classList.remove("flash-bad"); void pad.offsetWidth;
    pad.classList.add("bad", "flash-bad");
    setTimeout(() => pad.classList.remove("bad"), 500);
  }
  if (!fb) return;
  const hit = cfg().entries.find(en => en.signal === sig);
  fb.innerHTML = hit ? esc(fmt(PUI.pressed_other, { combo: hit.combo, label: hit.label }))
    : esc(fmt(PUI.live_unknown, { sig }));
}
```

- [ ] **Step 5: 事件与死代码清理**

`$("dstage").onclick` 替换为:

```js
$("dstage").onclick = e => {
  if (e.target.closest("#dgo")) return dStart();
  if (e.target.closest("#dskip")) return dAnswer(false);
  if (e.target.closest("#dreveal")) { dRevealed = true; renderDrill(); }
};
```

删除:`dCheck` 函数、`$("dstage").addEventListener("keydown", ...)`(dans 的 Enter 判定)、所有 `dVerdict` 残留引用。

- [ ] **Step 6: progressPanel 点阵 + report 键帽化**

`progressPanel` 整体替换:

```js
function progressPanel() {
  const title = esc((PUI.modes || {}).exam || "");
  if (!dExam) return `<h4>${title}</h4><div class="rpt">${esc(PUI.tip)}</div>`;
  const ok = dExam.log.filter(x => x.ok).length;
  const dots = Array.from({ length: dExam.n }, (_, i) => {
    const a = dExam.log[i];
    return `<i class="${a ? (a.ok ? "ok" : "bad") : i === dExam.i ? "cur" : ""}"></i>`;
  }).join("");
  return `<h4>${title}</h4>
    <div class="prog">${esc(fmt(PUI.progress, { i: Math.min(dExam.i + 1, dExam.n), n: dExam.n, ok }))}</div>
    <div class="dots">${dots}</div>
    <div class="rpt">${esc(PUI.stats_note)}</div>`;
}
```

`report` 里生疏清单一行改为键帽渲染:

```js
      + weak.map(x => `<div class="hrow"><span>${kbdCombo(x.q.combo)}</span><span>${esc(x.q.label)}</span></div>`).join("")
```

- [ ] **Step 7: 语法检查 + 生成手测**

Run: `node-check`,然后 `cd custom && make keymap && open ../keymap.html`
Expected: 考试模式开场按钮可用(此时 pickNext 仍是 TODO,开考即空报告——预期,Task 5 修);题面居中、键帽渲染;文本题答对绿闪进下一题、按错组合键红抖并显示实际触发;「看答案」显示键帽答案,空格记错继续;点阵随作答变色。

- [ ] **Step 8: Commit**

```bash
git add bin/keymap_template.html custom/keymap.yml keymap.html
git commit -m "feat(keymap): 考试模式舞台重构——键帽题面、按错红闪、点阵进度"
```

---

### Task 4: 闪卡改 Anki 自评流

**Files:**
- Modify: `bin/keymap_template.html`(`bodyOf` 闪卡分支、`examKey` 闪卡分支、`dstage` 点击)
- Modify: `custom/keymap.yml`(`practice.ui` 文案)

**Interfaces:**
- Consumes: Task 3 的 `bodyOf`/`examKey`/`dFlipped` 状态、`kbdCombo()`。
- Produces: 按钮 id `#dflip` `#dremember` `#dforgot`;键位 `空格`=翻面、`1`=记得、`2`=忘了。

- [ ] **Step 1: keymap.yml 文案**

修改与新增:

```yaml
    kind_card: 闪卡自测 · 心里默想按法
    kind_note:
      card: 这条会把浏览器切走,没法真按——先默想怎么按,翻面对答案,自己评记得没记得。
    flip: 翻面看答案（空格）
    remember: 记得（1）
    forgot: 忘了（2）
    card_output: "实际输出 {sig}"
```

(`kind_note` 的 `text`/`pointer` 两行保持原样。)

- [ ] **Step 2: bodyOf 闪卡分支**

Task 3 中 `bodyOf` 末行的占位 `return` 替换为:

```js
  if (!dFlipped) return `<div class="drow" style="justify-content:center">
      <button class="btn primary" id="dflip">${esc(PUI.flip)}</button></div>`;
  return `<div class="ansbox">${kbdCombo(q.combo)}
      ${q.signal ? `<div class="qmeta">${esc(fmt(PUI.card_output, { sig: q.signal }))}</div>` : ""}
    </div>
    <div class="drow" style="justify-content:center">
      <button class="btn primary" id="dremember">${esc(PUI.remember)}</button>
      <button class="btn" id="dforgot">${esc(PUI.forgot)}</button>
    </div>`;
```

同时把 `examStage` 里「看答案」按钮的条件保持为仅 text 题(闪卡的翻面就是看答案,不重复出按钮)。

- [ ] **Step 3: examKey 闪卡分支**

`examKey` 中 `if (dQ.kind !== "text") return;` 替换为:

```js
  if (dQ.kind === "card") {
    if (!dFlipped) {
      if (e.key === " ") { e.preventDefault(); dFlipped = true; renderDrill(); }
    } else if (e.key === "1") dAnswer(true);
    else if (e.key === "2") dAnswer(false);
    return;
  }
  if (dQ.kind !== "text") return;
```

- [ ] **Step 4: dstage 点击补三个按钮**

`$("dstage").onclick` 里 `#dreveal` 分支之后追加:

```js
  if (e.target.closest("#dflip")) { dFlipped = true; renderDrill(); return; }
  if (e.target.closest("#dremember")) return dAnswer(true);
  if (e.target.closest("#dforgot")) return dAnswer(false);
```

- [ ] **Step 5: 语法检查 + 生成手测**

Run: `node-check`,然后 `cd custom && make keymap && open ../keymap.html`
Expected: 选「窗口」组考试(全闪卡):正面只有题干和翻面按钮;空格翻面出键帽答案与实际输出;1/2 或点按钮评分并进下一题;自评结果写入 dStats(报告正确率随之变化)。

- [ ] **Step 6: Commit**

```bash
git add bin/keymap_template.html custom/keymap.yml keymap.html
git commit -m "feat(keymap): 闪卡改 Anki 自评——空格翻面,1/2 自评记得忘了"
```

---

### Task 5: pickNext 生疏度加权抽题(用户实现 · Learn by Doing)

**Files:**
- Modify: `bin/keymap_template.html`(`pickNext` 函数体,现存 `// TODO(human)` 处)

**Interfaces:**
- Consumes: `dStats[id] = {n, ok, ms}`(没练过的条目查不到);`pool` 每项 `{id, combo, label, group_zh, kind, signal}`;`asked: Set<id>`。
- Produces: `pickNext(pool, asked) → 题对象 | null`。契约:不返回 `asked` 里出过的题;池子耗尽返回 `null`。

**执行方式:这是设计阶段就定好的人工贡献点。** 执行者(主会话)把 Task 1-4 完成后,向用户发起 Learn by Doing 请求,请用户在 `TODO(human)` 处实现加权逻辑,方向已在设计文档定为:没练过 > 错误率高 > 平均耗时长,加少量随机扰动。**执行者不要代写此函数**;用户写完后执行者继续 Step 2。

- [ ] **Step 1: 向用户发起 Learn by Doing 请求并等待实现**

- [ ] **Step 2: 语法检查 + 行为验证**

Run: `node-check`,然后 `cd custom && make keymap && open ../keymap.html`
Expected: 「开始考试」能连续出题到 `exam_size` 道并出报告;故意答错几题后再来一轮,错过的题明显更早出现。

- [ ] **Step 3: Commit**

```bash
git add bin/keymap_template.html keymap.html
git commit -m "feat(keymap): 考试抽题按生疏度加权,修复空 pickNext"
```

---

### Task 6: 全量回归手测 + 收尾

**Files:**
- Modify: `keymap.html`(最终重新生成)
- Verify: `custom/keymap.yml`(确认无死键残留)

- [ ] **Step 1: 死键扫描**

Run:

```bash
cd ~/workspace/personal/Capslock
for k in answer_placeholder check hints_title hints_toggle live_title revealed; do
  grep -n "$k" bin/keymap_template.html custom/keymap.yml && echo "残留: $k"; done; echo SCAN-DONE
```

Expected: 只输出 `SCAN-DONE`(`wrong`/`right` 是常见词不扫,靠下面手测覆盖)。

- [ ] **Step 2: 重新生成 + 全量手测清单**

Run: `cd custom && make keymap && open ../keymap.html`,逐项过:

1. 自由模式:点亮流程、进度、完成块、再来一轮、灰显条目挂标签、实时解码、鼠标靶子。
2. 考试模式:文本/闪卡/鼠标三题型各答对、答错(或忘了)、看答案一遍;点阵进度;报告与生疏清单键帽渲染。
3. 抽题:答错的题下一轮更早被抽中;`exam_size`(12)与小题池取小。
4. 组切换、配置下拉切换、清空练习记录按钮、旧 localStorage 成绩不报错。
5. 深色模式(系统切换)下键帽、点阵、动效可读。
6. 其余四个视图(速查表/总览/键盘/功能)无回归,PNG 导出正常。

- [ ] **Step 3: 让用户实际按一遍验证(仓库规矩:合成按键测不了,涉及 Karabiner 的验证只能真手按)**

- [ ] **Step 4: Commit(如手测触发小修)**

```bash
git add -A && git commit -m "fix(keymap): 练习页翻新回归手测收尾"
```

---

## Self-Review 记录

- 规格覆盖:闯关清单(Task 2)、Anki 闪卡(Task 4)、pickNext(Task 5)、文本题反馈/点阵/键帽/布局(Task 1+3)、鼠标题(Task 3 注)、错误处理三条(free_only_cards=Task 2;旧 id 忽略=现状无改动;渲染兜底=Task 1)、验证(各任务 + Task 6)。
- 文案铁律:所有新中文都在 keymap.yml 步骤里,模板代码块中无中文字符串字面量(注释除外,注释不渲染)。
- 类型一致:`dLit`/`dRevealed`/`dFlipped`/`dAdvancing` 在 Task 2/3 声明,后续任务只消费;`bodyOf`/`examKey` 的替换点已写明承接关系。
