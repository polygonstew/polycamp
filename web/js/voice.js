// voice.js - the narrator. Reads the lesson aloud (audio made by the server), waits at each task until Blender confirms
// it, and tells the add-on what to highlight while each sentence is spoken.
//
// One narrator per page (module singleton) so it survives going from one lesson to the next. Only one open page
// narrates at a time: whichever you pressed play on last is the "owner", and it is the one the Blender-side buttons and
// the keyboard media keys control.
import { h, toast } from './ui.js';
import { S, api, on, saveSetting, blenderMajor } from './api.js';
import { icon } from './icons.js';

const N = {
  audio: new Audio(), pid: Math.random().toString(36).slice(2), owner: false, status: null,
  lid: null, title: '', script: null, vis: [], pos: -1, state: 'idle', msg: '', done: new Set(), waitFor: null,
  marks: null, chunk: -1, tok: 0, lineEnd: null, resumable: false, subs: new Set(), onSeg: null, progEl: null,
  sentCues: '', carry: false, leftAt: 0, timer: null,
};
N.audio.preload = 'auto';
const cfg = () => S.settings;
const speed = () => +cfg().voice_speed || 1;
const SPEEDS = [0.85, 1, 1.15, 1.3, 1.5, 1.75];
const visible = s => !s.opt || s.kind === 'task' || (s.kind === 'cubby' && cfg().voice_cubby_on) || (s.kind === 'extra' && cfg().voice_extras);
const engine = () => (N.status && !N.status.installed && 'speechSynthesis' in window ? 'browser' : 'server');
const emit = () => N.subs.forEach(f => { try { f(); } catch (e) { console.error(e); } });
const setState = (st, msg = '') => { N.state = st; N.msg = msg; mediaSession(); emit(); };
const cur = () => N.vis[N.pos] || null;

// ------------------------------------------------------------------ loading
async function loadStatus() { N.status = await api('voice/status').catch(() => null); }

async function refresh(warm) {
  const from = N.script && N.pos >= 0 && cur() ? N.script.segments.findIndex(s => s.key === cur().key) : 0;
  const sc = await api(`voice/script/${N.lid}?major=${blenderMajor()}${warm ? '&warm=1&from=' + Math.max(0, from) : ''}`);
  if (sc.error) return;
  const key = cur() && cur().key;
  N.script = sc;
  N.vis = sc.segments.filter(visible);
  if (key) { const i = N.vis.findIndex(s => s.key === key); if (i >= 0) N.pos = i; }
  emit();
}

async function load(lid) {
  if (N.lid !== lid) {
    stop();
    Object.assign(N, { lid, script: null, vis: [], pos: -1, state: 'idle', msg: '', waitFor: null, done: new Set() });
    const les = await api('lesson/' + lid);
    N.title = les.title || '';
    N.done = new Set(Object.keys((les.state && les.state.done) || {}));
  }
  await refresh(!!cfg().voice_on);
  poll();
}

function poll() {                       // keep the "ready" ticks honest while audio is being made in the background
  clearInterval(N.timer);
  N.timer = setInterval(async () => {
    if (!N.subs.size || document.hidden || !N.script) return;
    if (N.vis.every(s => s.ready)) { clearInterval(N.timer); return; }
    await refresh(false);
    loadStatus().then(emit);
  }, 4000);
}

// ------------------------------------------------------------------ playing
function prefetch(i) {
  const keys = N.vis.slice(i, i + 4).filter(s => !s.ready).map(s => s.key);
  if (keys.length && engine() === 'server') api('voice/ensure', { keys, prio: 1 });
}

function stopAudio() {
  N.audio.pause();
  N.lineEnd = null;
  if ('speechSynthesis' in window) speechSynthesis.cancel();
}

function claim() {
  if (!N.owner) { N.owner = true; api('voice/ctl', { action: 'owner', pid: N.pid }); }
}

async function playAt(i) {
  if (i < 0 || i >= N.vis.length) return finish();
  claim();
  const seg = N.vis[i], tok = ++N.tok;
  stopAudio();
  N.pos = i; N.waitFor = null; N.marks = null; N.chunk = -1; N.resumable = false;
  N.onSeg && N.onSeg(seg);
  setState('loading');
  prefetch(i);
  if (engine() === 'browser') return speakBrowser(seg, tok);
  try {
    const r = await fetch(`/voice/${seg.key}.json`);
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || 'HTTP ' + r.status);
    N.marks = (await r.json()).marks;
  } catch (e) {
    if (tok === N.tok) setState('error', String(e.message || e));
    return;
  }
  if (tok !== N.tok) return;
  seg.ready = true;
  N.audio.src = `/voice/${seg.key}.ogg`;
  N.audio.playbackRate = speed();
  try { await N.audio.play(); }
  catch (e) { if (tok === N.tok) setState('paused', 'Press play. The browser held back the sound until you click.'); return; }
  if (tok === N.tok) { N.resumable = true; setState('playing'); }
}

function speakBrowser(seg, tok) {
  const u = new SpeechSynthesisUtterance(seg.text);
  u.rate = speed();
  const vs = speechSynthesis.getVoices().filter(v => /^en/i.test(v.lang));
  u.voice = vs.find(v => /natural|neural|google|samantha|aria|jenny/i.test(v.name)) || vs[0] || null;
  u.onend = () => { if (tok === N.tok) afterSegment(); };
  speechSynthesis.speak(u);
  const first = (seg.cues || []).find(c => c && c.length);
  if (first) sendCues(first, 10);
  setState('playing');
}

function onTime() {
  const a = N.audio;
  if (a.duration && N.progEl) N.progEl.style.width = (100 * a.currentTime / a.duration).toFixed(1) + '%';
  if (!N.marks || !cur() || N.lineEnd) return;
  const t = a.currentTime;
  let k = -1;
  for (let j = 0; j < N.marks.length; j++) { if (t >= N.marks[j][0] - 0.05) k = j; else break; }
  if (k !== N.chunk) {
    N.chunk = k;
    const m = N.marks[k] || [0, 3];
    sendCues((cur().cues || [])[k] || [], Math.max(2.5, (m[1] - m[0]) / speed() + 1.5));
  }
}
N.audio.addEventListener('timeupdate', onTime);
N.audio.addEventListener('ended', () => { const f = N.lineEnd; N.lineEnd = null; N.resumable = false; f ? f() : afterSegment(); });
N.audio.addEventListener('error', () => { if (N.audio.src && N.state === 'playing') setState('error', 'The audio could not be played.'); });

// ------------------------------------------------------------------ cues (highlights in Blender)
function sendCues(cues, ttl = 6) {
  if (!cfg().voice_cues || !S.bridge.connected || !cues.length) return;
  const sig = JSON.stringify(cues);
  if (sig === N.sentCues) return;
  N.sentCues = sig;
  api('voice/cue', { cues, ttl, src: N.lid });
}
function clearCues() {
  if (!N.sentCues) return;
  N.sentCues = '';
  if (S.bridge.connected) api('voice/cue', { cues: [], ttl: 0 });
}
function showHere() {                   // "show me": everything this segment points at, held for a while
  const seg = cur();
  if (!seg) return;
  const all = [], seen = new Set();
  for (const c of (seg.cues || []).flat()) { const k = JSON.stringify(c); if (!seen.has(k) && c.t !== 'keys') { seen.add(k); all.push(c); } }
  const keys = (seg.cues || []).flat().find(c => c.t === 'keys');
  if (keys) all.push(keys);
  if (!all.length) return toast('Nothing in this part points at a place in Blender.', 'info', 2500);
  if (!S.bridge.connected) return toast('Blender is not linked.', 'bad', 2500);
  N.sentCues = '';
  api('voice/cue', { cues: all.slice(0, 5), ttl: 14, src: N.lid });
}

// ------------------------------------------------------------------ flow
const isDone = id => N.done.has(id);
function nextIndex(from) {
  const coach = cfg().voice_mode === 'coach';
  for (let j = from; j < N.vis.length; j++) {
    const s = N.vis[j];
    if (coach && ((s.kind === 'task' && isDone(s.task)) || (s.kind === 'quiz' && s.quiz && isDone(s.quiz)))) continue;
    return j;
  }
  return -1;
}
function advance() { const j = nextIndex(N.pos + 1); if (j < 0) finish(); else playAt(j); }
function finish() { clearCues(); N.waitFor = null; setState('done'); }
function afterSegment() {
  clearCues();
  const s = cur();
  if (s && cfg().voice_mode === 'coach') {
    if (s.kind === 'task' && !isDone(s.task)) { N.waitFor = { kind: 'task', id: s.task }; return setState('waiting'); }
    if (s.kind === 'quiz' && s.quiz && !isDone(s.quiz)) { N.waitFor = { kind: 'quiz', id: s.quiz }; return setState('waiting'); }
  }
  advance();
}

async function playLine(line, then) {              // a short spoken aside ("Got it.") that is not part of the script
  if (!line || !line.ready) return then && then();
  const tok = ++N.tok;
  stopAudio();
  N.lineEnd = then || (() => {});
  N.audio.src = `/voice/${line.key}.ogg`;
  N.audio.playbackRate = speed();
  try { await N.audio.play(); setState('playing', line.text); }
  catch (e) { N.lineEnd = null; if (tok === N.tok) then && then(); }
}

async function sayText(text) {                     // hints: synthesize on demand
  if (engine() === 'browser') { const u = new SpeechSynthesisUtterance(text.replace(/[`*]|\[\[|\]\]/g, '')); u.rate = speed(); speechSynthesis.speak(u); return; }
  const r = await api('voice/say', { text });
  if (!r.key) return;
  const wait = N.waitFor, tok = ++N.tok;
  const back = () => { N.waitFor = wait; setState('waiting'); };
  stopAudio();
  setState('loading', 'Hint');
  try {
    const m = await fetch(`/voice/${r.key}.json`);
    if (!m.ok || tok !== N.tok) throw new Error('superseded');
    N.lineEnd = back;
    N.audio.src = `/voice/${r.key}.ogg`;
    N.audio.playbackRate = speed();
    await N.audio.play();
    setState('playing', 'Hint');
  } catch (e) { N.lineEnd = null; if (tok === N.tok) back(); }
}

function ack() {
  const names = Object.keys((N.script && N.script.lines) || {}).filter(n => n.startsWith('ack'));
  const L = names.length ? N.script.lines[names[Math.floor(Math.random() * names.length)]] : null;
  setState('playing', 'Got it');
  playLine(L, advance);
}

on('task_done', m => {
  if (m.lesson !== N.lid) return;
  N.done.add(m.id);
  if (N.owner && N.state === 'waiting' && N.waitFor && N.waitFor.id === m.id) ack(); else emit();
});
on('award', m => {
  if (m.kind !== 'quiz' || !N.lid || !(m.ref || '').startsWith(N.lid + '/')) return;
  N.done.add(m.ref);
  if (N.owner && N.state === 'waiting' && N.waitFor && N.waitFor.id === m.ref) setTimeout(advance, 900); else emit();
});
on('lesson_done', m => {
  if (m.lesson !== N.lid || !N.owner || !['playing', 'waiting', 'loading'].includes(N.state)) return;
  const L = N.script && N.script.lines && N.script.lines.done;
  N.waitFor = null;
  playLine(L, finish);
});
on('hint', m => {
  if (!N.owner || m.task.split('/')[0] !== N.lid || N.state !== 'waiting') return;
  sayText(m.text);
});
on('settings', () => { if (N.script) refresh(false); });
on('voice_ctl', m => {
  if (m.action === 'owner') {
    if (m.pid !== N.pid && N.owner) { N.owner = false; if (N.state === 'playing') pause(); }
    return;
  }
  if (!N.owner) return;
  ({ toggle, next, prev, replay, show: showHere })[m.action]?.();
});

// ------------------------------------------------------------------ controls
function pause() {
  if (N.state !== 'playing') return;
  if (engine() === 'browser') { speechSynthesis.cancel(); N.resumable = false; } else N.audio.pause();
  clearCues();
  setState('paused');
}
function toggle() {
  claim();
  const st = N.state;
  if (st === 'playing') return pause();
  if (st === 'paused') { if (N.resumable && engine() === 'server') { N.audio.play(); return setState('playing'); } return playAt(Math.max(0, N.pos)); }
  if (st === 'waiting') return replay();
  if (st === 'loading') return;
  playAt(st === 'done' ? 0 : Math.max(0, N.pos));
}
function next() { claim(); if (N.state === 'waiting') return advance(); const j = N.pos + 1; j >= N.vis.length ? finish() : playAt(j); }
function prev() { claim(); playAt(N.audio.currentTime > 3 && N.state === 'playing' ? N.pos : Math.max(0, N.pos - 1)); }
function replay() { claim(); playAt(Math.max(0, N.pos)); }
function stop() {
  N.tok++;
  stopAudio();
  clearCues();
  N.waitFor = null; N.resumable = false;
  N.onSeg && N.onSeg(null);
  if (N.state !== 'idle') setState('idle');
}
function setSpeed(v) { saveSetting({ voice_speed: v }); N.audio.playbackRate = v; }

function mediaSession() {                           // keyboard media keys / headset buttons work even while Blender has focus
  if (!('mediaSession' in navigator)) return;
  const ms = navigator.mediaSession, s = cur();
  if (s && window.MediaMetadata) ms.metadata = new MediaMetadata({ title: s.label || 'Polycamp', artist: N.title, album: 'Polycamp lesson' });
  ms.playbackState = N.state === 'playing' ? 'playing' : 'paused';
}
if ('mediaSession' in navigator) {
  for (const [a, f] of [['play', toggle], ['pause', toggle], ['nexttrack', next], ['previoustrack', prev]]) {
    try { navigator.mediaSession.setActionHandler(a, f); } catch (e) { /* not supported here */ }
  }
}

document.addEventListener('keydown', e => {
  if (!N.owner || N.state === 'idle' || e.ctrlKey || e.metaKey || e.altKey) return;
  const t = e.target;
  if (t && (/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName) || t.isContentEditable)) return;
  const f = { ' ': toggle, ArrowRight: next, ArrowLeft: prev, r: replay }[e.key];
  if (f) { e.preventDefault(); f(); }
});

export const currentSegment = cur;

// ------------------------------------------------------------------ the bar
export function mountPlayer(host, ctx) {
  const bar = h('div', { class: 'narr' + (ctx.compact ? ' compact' : '') });
  host.replaceChildren(bar);
  N.onSeg = ctx.highlight || null;

  const btn = (name, title, fn, cls = '', label = '') =>
    h('button', { class: 'nb ' + cls, title, onclick: fn, html: icon(name, cls.includes('big') ? 22 : 16) + (label ? `<span>${label}</span>` : '') });

  function statusText() {
    const s = cur(), st = N.state;
    const task = N.waitFor && N.waitFor.kind === 'task' && N.vis.find(v => v.task === N.waitFor.id);
    if (st === 'loading') return ['Preparing the audio', N.status && N.status.queued ? `${N.status.queued} queued` : '', ''];
    if (st === 'waiting' && task) return ['Your turn in Blender', task.label, 'acc'];
    if (st === 'waiting') return ['Your turn', 'answer on the page, then it carries on', 'acc'];
    if (st === 'playing') return N.msg ? [N.msg, '', ''] : [s && s.voice === 'cubby' ? 'Cubby says' : 'Reading', s ? s.label : '', ''];
    if (st === 'paused') return ['Paused', N.msg || (s ? s.label : ''), ''];
    if (st === 'done') return ['End of the sheet', 'press play to hear it again', ''];
    if (st === 'error') return ['Could not play', N.msg, 'bad'];
    return ['Narration', 'reads the lesson to you while you work in Blender', ''];
  }

  function draw() {
    const st = N.state, st0 = N.status;
    bar.className = 'narr' + (ctx.compact ? ' compact' : '') + ' ' + st;
    if (!st0) return bar.replaceChildren(h('span', { class: 'dim' }, 'Checking the voice…'));
    if (!st0.installed && engine() === 'server') {
      return bar.replaceChildren(h('div', { class: 'row' }, h('span', { html: icon('speaker', 18) }),
        h('div', { class: 'grow' }, h('b', {}, 'Narration needs the voice engine. '), h('span', { class: 'dim' }, 'Run '), h('code', {}, 'python3 tools/install_voice.py'), h('span', { class: 'dim' }, ' once on the Polycamp PC (about 400 MB, no GPU).'))));
    }
    if (!cfg().voice_on && st === 'idle') {
      return bar.replaceChildren(h('div', { class: 'row' }, h('span', { html: icon('speaker', 18) }),
        h('div', { class: 'grow' }, h('b', {}, 'Have this lesson read to you. '), h('span', { class: 'dim' }, 'Eyes on Blender, ears on Polycamp. It waits for you at every task.')),
        h('button', { class: 'pri sm', onclick: async () => { await saveSetting({ voice_on: true }); await refresh(true); toggle(); } }, 'Listen')));
    }
    const [head, sub, tone] = statusText();
    const main = N.state === 'playing' ? btn('pause', 'Pause (Space)', toggle, 'big pri') : btn('play', 'Play (Space)', toggle, 'big pri');
    const top = h('div', { class: 'nrow' },
      main, btn('prev', 'Previous (←)', prev), btn('next', 'Next (→)', next), btn('replay', 'Say that again (R)', replay),
      h('div', { class: 'ntxt ' + tone }, h('b', {}, head), sub ? h('span', {}, sub) : null),
      h('span', { class: 'grow' }),
      !ctx.compact && S.bridge.connected ? btn('target', 'Point at it in Blender', showHere, 'txt', 'Show me') : null,
      N.state === 'waiting' && N.waitFor && N.waitFor.kind === 'task' && !ctx.compact ? btn('bulb', 'Read the next hint aloud', async () => {
        const r = await api('lesson/hint', { task: N.waitFor.id });
        if (r.error) toast(r.error, 'bad', 4000);
      }, 'txt', 'Hint') : null,
      h('select', { class: 'nsel', title: 'Speed', onchange: e => setSpeed(+e.target.value) }, SPEEDS.map(v => h('option', { value: v, selected: Math.abs(v - speed()) < .01 }, v.toFixed(2).replace(/0$/, '') + '×'))),
      h('button', { class: 'nb txt', title: cfg().voice_mode === 'coach' ? 'Coach: waits at each task until Blender confirms it. Click for Audiobook (reads straight through).' : 'Audiobook: reads straight through. Click for Coach.',
        onclick: () => saveSetting({ voice_mode: cfg().voice_mode === 'coach' ? 'book' : 'coach' }).then(emit) }, cfg().voice_mode === 'coach' ? 'Coach' : 'Audiobook'),
      btn('cross', 'Close narration', () => { stop(); saveSetting({ voice_on: false }).then(emit); }, 'quiet'));
    const prog = h('div', { class: 'nprog' }, h('i'));
    N.progEl = prog.firstChild;
    const ticks = ctx.compact ? null : h('div', { class: 'nticks' }, N.vis.map((s, i) => h('button', {
      class: 'tick k-' + s.kind + (i < N.pos ? ' played' : '') + (i === N.pos ? ' now' : '') + (s.ready ? ' ready' : ''),
      title: s.label + (s.ready ? '' : ' (audio still being made)'), onclick: () => playAt(i) })));
    bar.replaceChildren(top, ticks || '', prog);
  }

  N.subs.add(draw);
  draw();
  (async () => {
    await loadStatus();
    await load(ctx.lid);
    draw();
    const resume = N.carry && performance.now() - N.leftAt < 2500 && cfg().voice_on;
    N.carry = false;
    if (resume) playAt(N.lid === ctx.lid && N.pos >= 0 ? N.pos : 0);
    else if (cur() && N.state !== 'idle') N.onSeg && N.onSeg(cur());
  })();

  return () => {
    N.subs.delete(draw);
    N.onSeg = null;
    N.progEl = null;
    if (N.owner && ['playing', 'loading', 'waiting'].includes(N.state)) { N.carry = true; N.leftAt = performance.now(); }
    if (N.state !== 'idle') { N.tok++; stopAudio(); clearCues(); N.state = 'idle'; N.msg = ''; }
    if (ctx.highlight) ctx.highlight(null);
  };
}
