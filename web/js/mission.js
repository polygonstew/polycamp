// mission.js - "Mission Control": the live checklist, hints, scene mirror and key cards.
// Used on the lesson screen (right column / bottom dock) and as the stand-alone pop-out HUD for a second monitor.
import { h, clear, toast } from './ui.js';
import { S, api, on } from './api.js';
import { inline, keycaps } from './md.js';

const hints = {};          // task id -> [hint texts shown so far]
let solution = null;

on('hint', m => { (hints[m.task] ||= []); if (!hints[m.task].includes(m.text)) hints[m.task].push(m.text); });

export function mountMission(el, ctx) {
  // ctx: {lesson (public obj or null), doneIds: () => Set}
  let last = '';
  const render = () => {
    const live = S.live.hud, scene = S.live.scene;
    const les = ctx.lesson;
    const sig = JSON.stringify([live, scene, S.bridge.connected, Object.keys(hints).map(k => hints[k].length), !!solution, les && les.id]);
    if (sig === last) return;
    last = sig;
    const top = el.scrollTop;
    clear(el);
    el.append(linkSection(les), tasksSection(live, les), sceneSection(scene), keysSection(live, les), solutionSection(les));
    el.scrollTop = top;
  };
  const offs = [on('live', render), on('task_done', () => { last = ''; setTimeout(render, 50); }), on('hint', () => { last = ''; render(); })];
  render();
  return { render, off: () => offs.forEach(f => f()), refresh: () => { last = ''; render(); } };

  // ---- sections ----
  function linkSection(les) {
    const cl = (S.bridge.clients || []).find(c => c.alive);
    const sec = h('section', {}, h('h4', {}, h('span', {}, 'Blender link'), cl && h('span', { class: 'faint' }, cl.host || '')));
    if (!cl) {
      sec.append(h('div', { class: 'row' }, h('span', { class: 'dot' }), h('b', {}, 'Not linked')),
        h('p', { class: 'dim', style: { margin: '6px 0' } }, 'Checks need Blender. You can still read, take quizzes and mark tasks on your word.'),
        h('a', { class: 'btn sm pri', href: '#/link' }, 'Set up the link'));
      return sec;
    }
    sec.append(h('div', { class: 'row' }, h('span', { class: 'dot on' }), h('b', {}, 'Blender ' + cl.blender.replace(' LTS', '')),
      h('span', { class: 'faint' }, cl.file || 'unsaved file')));
    if (les && les.scene !== 'keep') {
      sec.append(h('div', { class: 'row', style: { marginTop: '8px' } },
        h('button', { class: 'pri sm', onclick: prep }, '🧱 Set up this lesson’s scene'),
        h('span', { class: 'faint', style: { fontSize: '.78rem' } }, 'unsaved work is backed up first')));
    }
    return sec;
  }

  async function prep(e) {
    e.target.disabled = true;
    const r = await api('lesson/prep', {});
    e.target.disabled = false;
    toast(r.msg || r.error || 'Done', r.ok === false || r.error ? 'bad' : 'good', 4500);
  }

  function tasksSection(live, les) {
    const tasks = (live && les && live.lesson && live.lesson.id === les.id) ? live.tasks : null;
    const sec = h('section', {});
    const total = tasks ? tasks.filter(t => !t.optional).length : 0;
    const done = tasks ? tasks.filter(t => !t.optional && t.done).length : 0;
    sec.append(h('h4', {}, h('span', {}, les && les.boss ? '☠ Boss fight' : 'Quest log'), h('span', {}, tasks ? `${done}/${total}` : '')));
    if (les && les.boss && tasks) sec.append(h('div', { class: 'bar boss', style: { marginBottom: '8px' }, title: 'Boss HP' }, h('i', { style: { width: Math.round(100 * (total - done) / Math.max(total, 1)) + '%' } })));
    else if (tasks) sec.append(h('div', { class: 'bar', style: { marginBottom: '8px' } }, h('i', { style: { width: Math.round(100 * done / Math.max(total, 1)) + '%' } })));
    if (!tasks) { sec.append(h('p', { class: 'dim' }, 'Open a lesson to see its tasks here.')); return sec; }
    for (const t of tasks) sec.append(taskRow(t));
    return sec;
  }

  function taskRow(t) {
    const connected = S.bridge.connected;
    const row = h('div', { class: 'mtask' },
      h('div', { class: 't' }, h('span', { class: 'box' + (t.done ? ' ok' : t.pre ? ' pre' : '') }, t.done || t.pre ? '✓' : ''),
        h('span', {}, t.title, t.optional && h('span', { class: 'pill', style: { marginLeft: '6px' } }, 'optional'))));
    if (!t.done) {
      for (const c of t.checks) row.append(h('div', { class: 'chk' + (c.ok ? ' ok' : '') }, h('i', {}, c.ok ? '✔' : '○'), c.label));
      if (t.pre) row.append(h('div', { class: 'hintbox' }, 'This is already true in your scene before you did anything. Press Claim, or undo and redo it.'));
      const acts = h('div', { class: 'acts' }, h('button', { class: 'sm', onclick: () => hint(t.id) }, '💡 Hint'));
      if (t.pre || !t.checks.length || (t.checks.every(c => !c.ok) && false)) acts.append(h('button', { class: 'sm pri', onclick: () => claim(t.id, false) }, t.checks.length ? 'Claim ✓' : 'Mark done'));
      if (!connected && t.checks.length) acts.append(h('button', { class: 'sm ghost', title: 'Half XP, on your word', onclick: () => claim(t.id, true) }, 'I did it (½ XP)'));
      else if (connected && t.checks.length && !t.pre) acts.append(h('button', { class: 'sm ghost', title: 'Re-check right now', onclick: () => claim(t.id, false) }, 'Check now'));
      row.append(acts);
      for (const txt of hints[t.id] || []) row.append(h('div', { class: 'hintbox', html: '💡 ' + inline(txt) }));
    }
    return row;
  }

  async function hint(id) {
    const r = await api('lesson/hint', { task: id });
    if (r.error) return toast(r.error, 'bad', 5000);
    (hints[id] ||= []);
    if (!hints[id].includes(r.text)) hints[id].push(r.text);
    if (r.cost) toast(`That hint cost ${r.cost} 💎`, 'info', 2500);
    ctx.refresh && ctx.refresh();
    last = ''; render();
  }

  async function claim(id, honor) {
    const r = await api('lesson/claim', { task: id, honor });
    toast(r.msg || r.error, r.ok ? 'good' : 'bad', 3500);
  }

  function sceneSection(sc) {
    const sec = h('section', {}, h('h4', {}, h('span', {}, 'Scene mirror'), sc && h('span', { class: 'faint' }, sc.mode)));
    if (!sc) { sec.append(h('p', { class: 'dim' }, 'Waiting for Blender…')); return sec; }
    sec.append(h('div', { class: 'scene-list' }, sc.objects.map(o => h('div', { class: 'sobj' + (o.sel ? ' sel' : '') + (o.active ? ' act' : '') },
      h('span', {}, icon(o.type)), h('span', {}, o.name), o.mods.length ? h('span', { class: 'faint' }, '🔧' + o.mods.length) : null,
      o.keys ? h('span', { class: 'faint' }, '🔑' + o.keys) : null, h('span', { class: 'ty' }, o.verts != null ? o.verts + 'v' : o.type)))));
    const r = sc.render || {};
    sec.append(h('div', { class: 'kv', style: { marginTop: '8px' } },
      h('b', {}, 'Render'), h('span', {}, `${r.engine} · ${r.res_x}×${r.res_y} @${r.res_pct}%${r.cy_samples && r.engine === 'CYCLES' ? ' · ' + r.cy_samples + ' spp' : ''}`),
      h('b', {}, 'Totals'), h('span', {}, sc.totals ? `${sc.totals.verts} verts · ${sc.totals.faces} faces · ${sc.totals.lights} lights` : '–'),
      h('b', {}, 'Frame'), h('span', {}, `${r.frame} (${r.frame_start}–${r.frame_end} @${r.fps})`)));
    return sec;
  }

  function keysSection(live, les) {
    if (!les || !les.keys.length) return h('div');
    return h('section', {}, h('h4', {}, h('span', {}, 'Keys for this lesson')), h('div', { class: 'keys-card', html: les.keys.map(k => keycaps(k)).join(' ') }));
  }

  function solutionSection(les) {
    if (!les || !(ctx.hasSolution && ctx.hasSolution())) return h('div');
    const sec = h('section', {}, h('h4', {}, h('span', {}, 'Stuck?')));
    if (!solution || solution.lesson !== les.id) {
      sec.append(h('button', { class: 'sm', onclick: async () => {
        const r = await api('lesson/solution', {});
        if (r.error) return toast(r.error, 'bad');
        solution = { lesson: les.id, code: r.code };
        if (r.cost) toast(`Peeked: -${r.cost} 💎. Cubby saw that.`, 'info');
        last = ''; render();
      } }, '👀 Peek at the solution script'), h('div', { class: 'faint', style: { fontSize: '.78rem', marginTop: '4px' } }, 'Costs 5 💎 the first time. It is Python: you can read how it works.'));
    } else {
      sec.append(h('pre', {}, solution.code), h('button', { class: 'sm pri', onclick: async () => {
        const r = await api('lesson/solution', { run: true });
        toast((r.ran && r.ran.msg) || r.error || 'Sent to Blender', r.error ? 'bad' : 'good');
      } }, '▶ Run it in Blender'));
    }
    return sec;
  }
}

const ICONS = { MESH: '▧', LIGHT: '💡', CAMERA: '🎥', EMPTY: '✚', CURVE: '〰', ARMATURE: '🦴', FONT: 'T', SURFACE: '◠' };
const icon = t => ICONS[t] || '◇';
