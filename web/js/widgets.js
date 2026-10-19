// widgets.js - the in-lesson question widgets: quiz, order, match, fill and the hotkey drill.
import { h } from './ui.js';
import { api } from './api.js';
import { md, inline, keycaps } from './md.js';
import { capture, judge, seqOf, laptopAlternatives, watchBlender } from './keys.js';
import { icon } from './icons.js';
const tick = icon('check', 14) + ' ';

const shuffle = a => { a = [...a]; for (let i = a.length - 1; i > 0; i--) { const j = Math.random() * (i + 1) | 0; [a[i], a[j]] = [a[j], a[i]]; } return a; };

function frame(b, label, done, ...kids) {
  return h('div', { class: 'widget' + (done ? ' done' : ''), 'data-id': b.id },
    h('div', { class: 'wt' }, h('span', {}, label), h('span', {}, done ? 'solved' : `+${b.xp} XP`)),
    h('div', { html: md(b.q || b.text || '') }), ...kids);
}
const feedback = () => h('div', { class: 'fb hide' });
function say(fb, ok, text) { fb.className = 'fb ' + (ok ? 'ok' : 'no'); fb.innerHTML = text; }

export function quiz(b, done, onSolved) {
  const picked = new Set();
  const fb = feedback();
  const opts = b.options.map((o, i) => h('div', { class: 'opt', onclick: () => {
    if (btn.disabled && done) return;
    if (b.multi) picked.has(i) ? picked.delete(i) : picked.add(i);
    else { picked.clear(); picked.add(i); }
    opts.forEach((el, k) => { el.classList.remove('wrong'); el.classList.toggle('sel', picked.has(k)); });
  } }, h('span', { html: inline(o) })));
  const btn = h('button', { class: 'pri sm', onclick: async () => {
    if (!picked.size) return;
    const r = await api('answer', { id: b.id, value: [...picked] });
    if (r.correct) { opts.forEach((el, k) => el.classList.toggle('right', picked.has(k))); say(fb, true, tick + inline(r.explain || 'Correct.')); btn.disabled = true; onSolved(r); }
    else { picked.forEach(k => opts[k].classList.add('wrong')); say(fb, false, 'Not quite. Read it again.'); }
  } }, 'Check');
  if (done) { btn.disabled = true; btn.textContent = 'Solved'; }
  return frame(b, b.multi ? 'Quiz · pick all that apply' : 'Quiz', done, ...opts, h('div', { class: 'row' }, btn), fb);
}

export function order(b, done, onSolved) {
  let items = shuffle(b.items);
  const list = h('div');
  const fb = feedback();
  const draw = () => {
    list.replaceChildren(...items.map((t, i) => h('div', { class: 'opt sortli', draggable: 'true',
      ondragstart: e => e.dataTransfer.setData('text/plain', i),
      ondragover: e => e.preventDefault(),
      ondrop: e => { e.preventDefault(); const from = +e.dataTransfer.getData('text/plain'); const [m] = items.splice(from, 1); items.splice(i, 0, m); draw(); } },
    h('b', { class: 'faint' }, (i + 1) + '.'), h('span', { class: 'grow', html: inline(t) }),
    h('button', { class: 'sm ghost', onclick: () => { if (i) { [items[i - 1], items[i]] = [items[i], items[i - 1]]; draw(); } } }, '▲'),
    h('button', { class: 'sm ghost', onclick: () => { if (i < items.length - 1) { [items[i + 1], items[i]] = [items[i], items[i + 1]]; draw(); } } }, '▼'))));
  };
  draw();
  const btn = h('button', { class: 'pri sm', onclick: async () => {
    const r = await api('answer', { id: b.id, value: items });
    if (r.correct) { say(fb, true, tick + inline(r.explain || 'That is the order.')); btn.disabled = true; onSolved(r); }
    else say(fb, false, 'Not the right order yet. Drag or use the arrows.');
  } }, 'Check order');
  if (done) { items = [...b.items]; draw(); btn.disabled = true; btn.textContent = 'Solved'; }
  return frame(b, 'Put in order', done, list, h('div', { class: 'row' }, btn), fb);
}

export function match(b, done, onSolved) {
  const pool = shuffle(b.right);
  const sels = b.left.map(() => h('select', {}, h('option', { value: '' }, 'choose…'), ...pool.map(r => h('option', { value: r }, r))));
  const fb = feedback();
  const grid = h('div', { class: 'matchgrid' }, ...b.left.flatMap((l, i) => [h('div', { html: inline(l) }), sels[i]]));
  const btn = h('button', { class: 'pri sm', onclick: async () => {
    const r = await api('answer', { id: b.id, value: sels.map(s => s.value) });
    if (r.correct) { say(fb, true, tick + inline(r.explain || 'All matched.')); btn.disabled = true; onSolved(r); }
    else say(fb, false, 'At least one pair is off.');
  } }, 'Check');
  if (done) { sels.forEach((s, i) => (s.value = b.right[i])); btn.disabled = true; btn.textContent = 'Solved'; }
  return frame(b, 'Match up', done, grid, h('div', { class: 'row', style: { marginTop: '8px' } }, btn), fb);
}

export function fill(b, done, onSolved) {
  const inp = h('input', { type: 'text', placeholder: 'type your answer', style: { width: '260px' } });
  const fb = feedback();
  const go = async () => {
    const r = await api('answer', { id: b.id, value: inp.value });
    if (r.correct) { say(fb, true, tick + inline(r.explain || 'Yes.')); btn.disabled = true; onSolved(r); }
    else say(fb, false, 'No. Try again.');
  };
  inp.addEventListener('keydown', e => { if (e.key === 'Enter') go(); });
  const btn = h('button', { class: 'pri sm', onclick: go }, 'Check');
  if (done) { inp.disabled = true; btn.disabled = true; btn.textContent = 'Solved'; }
  return frame(b, 'Fill in', done, h('div', { class: 'row' }, inp, btn), fb);
}

export function keys(b, done, onSolved) {
  const rows = b.rows;
  let i = 0, stop = null, stopBlender = null;
  const st = { step: 0 };
  const big = h('div', { class: 'big' });
  const hint = h('div', { class: 'dim' });
  const lap = h('div', { class: 'faint', style: { fontSize: '.85rem' } });
  const prog = h('div', { class: 'prog' }, rows.map(() => h('i')));
  const area = h('div', { class: 'keydrill', tabindex: '0' }, big, hint, lap, prog);
  const idle = 'Click here to start. Then press the keys: on this page or in Blender.';
  const show = () => {
    big.textContent = rows[i] ? rows[i].action : 'Done';
    prog.childNodes.forEach((n, k) => n.className = k < i ? 'ok' : '');
    const r = rows[i], alts = r ? laptopAlternatives(r.combo) : [], seq = r && seqOf(r.combo);
    lap.innerHTML = alts.length ? 'No numpad? ' + alts.map(a => keycaps(a)).join(' or ') + ' works too.' : seq ? `Press ${seq.length} times in a row.` : '';
  };
  const stopCap = () => { if (stop) { stop(); stop = null; } };
  const stopAll = () => { stopCap(); if (stopBlender) { stopBlender(); stopBlender = null; } };
  const advance = async () => {
    i++; st.step = 0; show();
    if (i >= rows.length) {
      stopAll(); hint.textContent = 'Done.'; skip.classList.add('hide');
      const r = await api('answer', { id: b.id, value: true });
      onSolved(r);
    }
  };
  const press = combo => {
    if (i >= rows.length) return;
    const row = rows[i], r = judge(row.combo, combo, st);
    if (r === 'ok') { hint.innerHTML = 'Yes: ' + keycaps(combo); advance(); }
    else if (r === 'more') hint.innerHTML = keycaps(combo) + ' then …';
    else hint.innerHTML = `You pressed ${keycaps(combo)}. Expected ${keycaps(row.combo)}.`;
  };
  const start = () => {                                      // the page listens while this box has focus ...
    if (i >= rows.length) return;
    if (!stop) stop = capture(press, held => { if (held.length) hint.innerHTML = held.map(k => keycaps(k)).join(' + ') + ' + …'; });
    if (!stopBlender) stopBlender = watchBlender(press, () => area.isConnected);   // ... and Blender's keys count until it is solved
    hint.textContent = 'Listening. Press the keys, here or in Blender.';
  };
  area.addEventListener('focus', start);
  area.addEventListener('blur', () => { stopCap(); if (i < rows.length) hint.textContent = stopBlender ? 'Listening for keys pressed in Blender. Click here to type them on this page instead.' : idle; });
  if (done) { i = rows.length; hint.textContent = 'Solved.'; } else hint.textContent = idle;
  show();
  const skip = h('button', { class: 'sm ghost', onclick: () => { if (i < rows.length) advance(); } }, 'Can’t press this one: skip');
  return frame(b, 'Hotkey drill', done, area, done ? null : skip);
}

export const WIDGETS = { quiz, order, match, fill, keys };
