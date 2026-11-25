"use strict";
const $ = (id) => document.getElementById(id);
const player = $("player");

const state = {
  styleId: 3,
  takes: [],        // {no, id?, duration?, style, status: pending|ok|failed, saved?, error?}
  sel: -1,
  running: false,
  abort: false,
  playingKind: null, // "take" | "output"
};

// ---------------------------------------------------------------- utils
async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: opts.body ? { "Content-Type": "application/json" } : {},
    ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) {
    let msg = res.statusText;
    try { const j = await res.json(); msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail); } catch {}
    throw new Error(msg);
  }
  return res.json();
}
let toastTimer;
function toast(msg, err = false, ms = 0) {
  const t = $("toast");
  t.textContent = msg;
  t.className = "toast show" + (err ? " err" : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (t.className = "toast" + (err ? " err" : "")), ms || (err ? 5000 : 2200));
}
function bindRange(id, fmt) {
  const el = $(id), out = $(id + "V");
  const upd = () => (out.textContent = fmt(+el.value));
  el.addEventListener("input", upd); upd();
  return el;
}
const store = {
  get(k, d) { try { const v = localStorage.getItem("vgui." + k); return v === null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem("vgui." + k, JSON.stringify(v)); } catch {} },
};

// ---------------------------------------------------------------- mascot flipbook
const mascot = { frames: [], i: 0, timer: null };
function startFlipbook() {
  clearInterval(mascot.timer);
  if (mascot.frames.length < 2) return;
  let fps = +$("fps").value;
  if ($("mascot").classList.contains("talk")) fps *= 2; // しゃべってる間は倍速
  mascot.timer = setInterval(() => {
    mascot.i = (mascot.i + 1) % mascot.frames.length;
    $("mascotImg").src = mascot.frames[mascot.i].src;
  }, 1000 / fps);
}
async function loadFrames() {
  const names = await api("/ui/frames");
  mascot.frames = names.map((n) => { const im = new Image(); im.src = "/frames/" + encodeURIComponent(n); return im; });
  if (mascot.frames.length) $("mascotImg").src = $("favicon").href = mascot.frames[0].src;
  $("frameInfo").textContent = `${names.length} コマ（frames/ フォルダ）`;
  startFlipbook();
}
function setMascot(mode) {
  const m = $("mascot");
  m.classList.toggle("talk", mode === "talk");
  m.classList.toggle("busy", mode === "busy");
  startFlipbook();
}

// ---------------------------------------------------------------- styles
function renderStyles(styles) {
  const box = $("styles");
  box.innerHTML = "";
  for (const s of styles) {
    const b = document.createElement("button");
    b.className = "chip" + (s.id === state.styleId ? " on" : "");
    b.textContent = s.name;
    b.onclick = () => {
      state.styleId = s.id; store.set("style", s.id);
      [...box.children].forEach((c) => c.classList.toggle("on", c === b));
    };
    box.appendChild(b);
  }
}

// ---------------------------------------------------------------- takes
function renderTakes() {
  const list = $("takeList");
  list.innerHTML = "";
  $("takeEmpty").style.display = state.takes.length ? "none" : "";
  state.takes.forEach((t, idx) => {
    const li = document.createElement("li");
    li.className = "take " + (t.status !== "ok" ? t.status : "") + (idx === state.sel ? " sel" : "");
    const meta = t.status === "ok" ? `Take ${t.no}　${t.style} | ${t.speed.toFixed(2)}x | ${t.duration.toFixed(2)}s`
      : t.status === "pending" ? `Take ${t.no}　生成中…` : `Take ${t.no}　失敗: ${t.error}`;
    li.innerHTML = `<span class="no">${t.no}</span><span class="meta"></span>
      <span class="saved" title="${t.savedPath ? t.savedPath.replace(/"/g, "&quot;") : ""}">${t.saved ? "✓ 保存済" : ""}</span><span></span>`;
    li.querySelector(".meta").textContent = meta;
    li.querySelector(".meta").title = meta;
    if (t.status === "ok") {
      const btns = li.lastElementChild;
      const save = document.createElement("button");
      save.className = "ghost save"; save.textContent = "保存";
      save.onclick = (e) => { e.stopPropagation(); saveTake(idx); };
      btns.appendChild(save);
      li.onclick = () => { select(idx); playTake(idx); };
    }
    list.appendChild(li);
  });
}
function select(idx) {
  state.sel = idx;
  renderTakes();
  const el = $("takeList").children[idx];
  if (el) el.scrollIntoView({ block: "nearest" });
}
function playUrl(url, kind) {
  player.src = url; state.playingKind = kind;
  player.play().catch(() => {});
}
function playTake(idx) {
  const t = state.takes[idx];
  if (t && t.status === "ok") playUrl(`/ui/take/${t.id}.wav`, "take");
}
async function saveTake(idx) {
  const t = state.takes[idx];
  if (!t || t.status !== "ok") return;
  try {
    const r = await api("/ui/save", { method: "POST", body: { id: t.id, caption: t.text } });
    t.saved = true; t.savedPath = r.path; renderTakes();
    toast("保存したのだ:\n" + r.path, false, 6000);
    loadOutputs();
  } catch (e) { toast("保存失敗: " + e.message, true); }
}

async function generate() {
  if (state.running) return;
  const text = $("text").value.trim();
  if (!text) { toast("セリフを入力してほしいのだ", true); $("text").focus(); return; }
  const n = +$("takes").value;
  const params = {
    text, style_id: state.styleId,
    kana: $("kana").value.trim() || null,
    speed: +$("speed").value, temperature: +$("temp").value,
    top_k: +$("topk").value, top_p: +$("topp").value,
  };
  const styleName = [...$("styles").children].find((c) => c.classList.contains("on"))?.textContent || "";
  state.takes = Array.from({ length: n }, (_, i) => ({ no: i + 1, status: "pending", style: styleName, speed: params.speed, text }));
  state.sel = -1; state.running = true; state.abort = false;
  $("gen").disabled = true; $("stop").disabled = false;
  $("bar").style.width = "0";
  setMascot("busy");
  renderTakes();

  for (let i = 0; i < n; i++) {
    if (state.abort) { state.takes = state.takes.filter((t) => t.status !== "pending"); break; }
    try {
      const r = await api("/ui/synthesize", { method: "POST", body: params });
      Object.assign(state.takes[i], { status: "ok", id: r.id, duration: r.duration, style: r.style });
      if (state.sel < 0) { select(i); if (player.paused) playTake(i); }
    } catch (e) {
      Object.assign(state.takes[i], { status: "failed", error: e.message });
      if (i === 0) { toast(e.message, true); state.takes = state.takes.slice(0, 1); renderTakes(); break; }
    }
    $("bar").style.width = `${((i + 1) / n) * 100}%`;
    renderTakes();
  }
  state.running = false;
  $("gen").disabled = false; $("stop").disabled = true;
  setMascot(player.paused ? "" : "talk");
}

// ---------------------------------------------------------------- outputs
async function loadOutputs() {
  try {
    const files = await api("/ui/outputs");
    const ul = $("outList");
    ul.innerHTML = "";
    for (const f of files) {
      const li = document.createElement("li");
      li.textContent = f.name; li.title = f.name;
      li.onclick = () => {
        [...ul.children].forEach((c) => c.classList.remove("playing"));
        li.classList.add("playing");
        playUrl("/ui/outputs/" + encodeURIComponent(f.name), "output");
      };
      ul.appendChild(li);
    }
    if (!files.length) ul.innerHTML = '<li class="hint">まだないのだ</li>';
  } catch (e) { /* ignore */ }
}

// ---------------------------------------------------------------- kana
async function fetchKana() {
  const text = $("text").value.trim();
  if (!text) return;
  try {
    const r = await api("/ui/pronunciation", { method: "POST", body: { text } });
    if (r.editable) { $("kana").value = r.kana; toast("読みを取得したのだ"); }
    else toast("英語が混ざっている文は読み編集できないのだ", true);
  } catch (e) { toast(e.message, true); }
}

// ---------------------------------------------------------------- init
function wire() {
  bindRange("speed", (v) => v.toFixed(2));
  bindRange("takes", (v) => v);
  bindRange("temp", (v) => v.toFixed(2));
  bindRange("topk", (v) => v);
  bindRange("topp", (v) => v.toFixed(2));
  const fps = bindRange("fps", (v) => v);
  fps.value = store.get("fps", 6); fps.dispatchEvent(new Event("input"));
  fps.addEventListener("input", () => { store.set("fps", +fps.value); startFlipbook(); });

  $("gen").onclick = generate;
  $("stop").onclick = () => { state.abort = true; toast("今のテイクが終わったら止めるのだ"); };
  $("kanaFetch").onclick = fetchKana;
  $("kanaClear").onclick = () => ($("kana").value = "");
  $("refresh").onclick = loadOutputs;
  $("text").addEventListener("input", () => { if ($("kana").value) $("kana").value = ""; store.set("text", $("text").value); });
  $("text").value = store.get("text", "");

  player.addEventListener("play", () => setMascot("talk"));
  player.addEventListener("pause", () => setMascot(state.running ? "busy" : ""));
  player.addEventListener("ended", () => {
    setMascot(state.running ? "busy" : "");
    [...$("outList").children].forEach((c) => c.classList.remove("playing"));
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); generate(); return; }
    const tag = document.activeElement?.tagName;
    if (tag === "TEXTAREA" || tag === "INPUT") return;
    const ok = state.takes.map((t, i) => (t.status === "ok" ? i : -1)).filter((i) => i >= 0);
    if (!ok.length) return;
    const pos = ok.indexOf(state.sel);
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      const next = ok[Math.max(0, Math.min(ok.length - 1, pos + (e.key === "ArrowDown" ? 1 : -1)))];
      select(next); playTake(next);
    } else if (e.key === " ") {
      e.preventDefault();
      if (!player.paused && state.playingKind === "take") player.pause(); else playTake(state.sel);
    } else if (e.key === "Enter") {
      e.preventDefault(); saveTake(state.sel);
    } else if (/^[1-9]$/.test(e.key) && ok.includes(+e.key - 1)) {
      select(+e.key - 1); playTake(+e.key - 1);
    }
  });
}

async function init() {
  wire();
  loadFrames().catch(() => {});
  try {
    const info = await api("/ui/info");
    state.styleId = store.get("style", info.defaults.style_id);
    if (!info.styles.some((s) => s.id === state.styleId)) state.styleId = info.defaults.style_id;
    renderStyles(info.styles);
    const d = info.defaults;
    $("speed").value = d.speed; $("takes").value = d.take_count;
    $("temp").value = d.temperature; $("topk").value = d.top_k; $("topp").value = d.top_p;
    ["speed", "takes", "temp", "topk", "topp"].forEach((id) => $(id).dispatchEvent(new Event("input")));
    $("outDir").textContent = `${info.output_dir}（${info.output_format}）`;
    $("status").textContent = `${info.character} エンジン OK`;
    $("status").className = "status ok";
  } catch (e) {
    $("status").textContent = "エンジンエラー: " + e.message;
    $("status").className = "status err";
  }
  renderTakes();
  loadOutputs();
}
init();
