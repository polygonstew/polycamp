// lesson.js - the lesson screen: reading column + Mission Control (right column in Dual, bottom dock in Single).
import { h, $, $$, toast, confetti } from '../ui.js';
import { S, api, on, blenderMajor } from '../api.js';
import { md } from '../md.js';
import { cubby, quip } from '../cubby.js';
import { WIDGETS } from '../widgets.js';
import { mountMission } from '../mission.js';
import { keycaps } from '../md.js';
import { icon } from '../icons.js';
import { mountPlayer, currentSegment } from '../voice.js';

export function verMatch(spec, major) {
  if (!spec || spec === 'any') return true;
  return spec.split(',').some(tok => {
    tok = tok.trim();
    let m;
    if ((m = /^(\d+)\+$/.exec(tok))) return major >= +m[1];
    if ((m = /^(\d+)-(\d+)$/.exec(tok))) return major >= +m[1] && major <= +m[2];
    return +tok === major;
  });
}

export default async function (root, [lid]) {
  const les = await api('lesson/' + lid);
  if (les.error) { root.append(h('div', { class: 'card' }, `No lesson called "${lid}".`)); return; }
  const started = await api('lesson/start', { id: lid });
  S.active = lid;
  const st = { done: { ...(started.state || les.state).done }, completed: (started.state || les.state).completed };
  const ov = S.overview || await api('overview');
  S.overview = ov;
  const world = ov.worlds.find(w => w.id === les.world);
  const seq = ov.worlds.flatMap(w => w.lessons);
  const idx = seq.findIndex(l => l.id === lid);
  const prev = seq[idx - 1], next = seq[idx + 1];

  const body = h('div', { class: 'body' });
  const narrHost = h('div', { class: 'narr-host' });
  const missionEl = h('aside', { id: 'mission' });
  root.append(h('div', { class: 'lesson' }, body, missionEl));
  let major = blenderMajor();

  const build = () => {
    body.replaceChildren();
    body.append(
      h('div', { class: 'head' },
        h('div', { class: 'crumbs' }, h('a', { href: '#/' }, 'Map'), ' / ', h('a', { href: '#/world/' + world.id }, world.title), ' / ', 'sheet ' + (idx + 1) + ' of ' + seq.length),
        h('h1', { style: { marginTop: '6px' } }, les.title),
        h('div', { class: 'meta' }, les.boss && h('span', { class: 'pill boss' }, 'Boss'), h('span', { class: 'pill' }, les.minutes + ' min'),
          h('span', { class: 'pill acc' }, S.overview.worlds.flatMap(w => w.lessons).find(l => l.id === lid).xp + ' XP'),
          st.completed && h('span', { class: 'pill', style: { color: 'var(--good)', borderColor: 'var(--good)' } }, 'Completed'),
          h('span', { class: 'pill' }, `Blender ${major}.x notes`))),
      narrHost);
    if (les.scene !== 'keep') {
      body.append(h('div', { class: 'setup-bar' }, h('span', { html: icon('cube', 20) }),
        h('div', { class: 'grow' }, h('b', {}, 'This lesson starts from a prepared scene. '),
          h('span', { class: 'dim' }, les.scene === 'fresh' ? 'You get the factory scene: Cube, Light, Camera.' : 'It builds the starting model for you, so nothing depends on how an earlier lesson went.')),
        h('button', { class: 'pri sm', onclick: async e => {
          e.target.disabled = true;
          const r = await api('lesson/prep', {});
          e.target.disabled = false;
          toast(r.msg || r.error, r.ok === false || r.error ? 'bad' : 'good', 5000);
        } }, 'Set up scene in Blender')));
    }
    les.blocks.forEach((b, bi) => { const el = renderBlock(b); if (el) { el.dataset.b = bi; body.append(el); } });
    body.append(footer());
    refreshCards();
    highlight(currentSegment());
  };

  // the narrator tells us which part of the page it is reading; mark it and keep it in view
  function highlight(seg) {
    $$('.speaking', body).forEach(e => e.classList.remove('speaking'));
    if (!seg) return;
    let els = [];
    if (seg.b != null) {
      const blk = body.querySelector(`[data-b="${seg.b}"]`);
      if (blk) els = seg.u && blk.classList.contains('md') && blk.children.length > seg.u[1] ? [...blk.children].slice(seg.u[0], seg.u[1] + 1) : [blk];
    } else {
      const sel = { intro: '.head', setup: '.setup-bar', outro: '.body > .card:last-child' }[seg.kind];
      const el = sel && $(sel, body);
      if (el) els = [el];
    }
    els.forEach(e => e.classList.add('speaking'));
    const r = els[0] && els[0].getBoundingClientRect();
    if (r && (r.top < 130 || r.bottom > innerHeight - 90)) els[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function renderBlock(b) {
    switch (b.t) {
      case 'md': return h('div', { class: 'md', html: md(b.text) });
      case 'cubby': return h('div', { class: 'cubby' }, h('div', { html: cubby(b.mood || 'happy') }), h('div', { class: 'bub', html: md(b.text) }));
      case 'note': return h('div', { class: 'note ' + b.kind }, h('b', { class: 't' }, b.title || { tip: 'Tip', warn: 'Careful', cpu: 'CPU tip', info: 'Note' }[b.kind] || b.kind), h('div', { html: md(b.text) }));
      case 'v': return verMatch(b.spec, major) ? h('div', { class: 'vblock' }, h('div', { class: 'vl' }, 'Blender ' + b.spec.replace('+', '.x and newer').replace(/^(\d)$/, '$1.x')), h('div', { html: md(b.text) })) : null;
      case 'reveal': return h('details', { class: 'reveal' }, h('summary', {}, b.title), h('div', { html: md(b.text) }));
      case 'goal': return h('div', { class: 'goal' }, b.img && h('img', { src: '/cimg/' + b.img, onclick: () => import('../ui.js').then(m => m.lightbox('/cimg/' + b.img)) }), h('div', { html: md(b.text) }));
      case 'img': return h('figure', {}, h('img', { src: '/cimg/' + b.src }), b.caption && h('figcaption', { html: md(b.caption) }));
      case 'task': return quest(b);
      default: if (WIDGETS[b.t]) return WIDGETS[b.t](b, !!st.done[b.id], onSolved); return null;
    }
  }

  function quest(b) {
    return h('div', { class: 'quest', 'data-id': b.id },
      h('div', { class: 'qh' }, h('span', { class: 'tag' }, b.optional ? 'Stretch' : 'Task'), h('b', {}, b.title), h('span', { class: 'xp' }, '+' + b.xp + ' XP')),
      h('div', { class: 'qb', html: md(b.text) }),
      b.keys.length ? h('div', { class: 'keys-card', html: b.keys.map(keycaps).join(' ') }) : null,
      b.why && h('div', { class: 'dim', style: { fontSize: '.88rem', marginTop: '6px' } }, b.why),
      h('div', { class: 'qs dim', style: { marginTop: '8px', fontSize: '.85rem' } }));
  }

  function refreshCards() {
    const live = (S.live.hud && S.live.hud.lesson && S.live.hud.lesson.id === lid) ? S.live.hud.tasks : [];
    $$('.quest', body).forEach(card => {
      const id = card.dataset.id, d = !!st.done[id];
      card.classList.toggle('done', d);
      const t = live.find(x => x.id === id);
      const n = t ? t.checks.filter(c => c.ok).length : 0;
      $('.qs', card).textContent = d ? (st.done[id].how === 'auto' ? 'Blender confirmed it.' : 'Marked done.') :
        t ? (S.bridge.connected ? `Watching your scene: ${n} of ${t.checks.length} checks passing` : 'Blender is not linked. Use Mark done in the panel.') : '';
    });
  }

  function onSolved(r) { if (r && r.first) { /* award toast comes from SSE */ } refreshState(); }
  async function refreshState() {
    const fresh = await api('lesson/' + lid);
    st.done = fresh.state.done; st.completed = fresh.state.completed;
    refreshCards();
  }

  function footer() {
    return h('div', { class: 'card', style: { marginTop: '36px', display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' } },
      prev ? h('a', { class: 'btn', href: '#/lesson/' + prev.id }, '← ' + prev.title) : null, h('span', { class: 'grow' }),
      h('span', { class: 'dim', style: { fontSize: '.88rem' } }, quip('idle')),
      next ? h('a', { class: 'btn pri', href: '#/lesson/' + next.id }, next.title + ' →') : h('a', { class: 'btn pri', href: '#/' }, 'Back to the map'));
  }

  build();
  const unPlayer = mountPlayer(narrHost, { lid, highlight });
  const mission = mountMission(missionEl, { lesson: les, hasSolution: () => (S.overview && les.blocks) && (started.state || les.state).has_solution });
  const offs = [
    on('live', () => {
      const m = blenderMajor();
      if (m !== major) { major = m; build(); mission.refresh(); }
      refreshCards();
    }),
    on('task_done', m => {
      if (m.lesson !== lid) return;
      st.done[m.id] = { how: m.how };
      refreshCards();
      const card = $(`.quest[data-id="${m.id}"]`, body);
      if (card) { card.classList.add('pulse'); setTimeout(() => card.classList.remove('pulse'), 1100); }
    }),
    on('lesson_done', m => { if (m.lesson === lid) { st.completed = true; refreshState(); } }),
  ];
  return () => { offs.forEach(f => f()); mission.off(); unPlayer(); };
}
