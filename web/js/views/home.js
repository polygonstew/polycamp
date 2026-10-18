// home.js - the campaign map: hero with "continue", then world cards joined by a winding trail.
import { h, $ } from '../ui.js';
import { S, api } from '../api.js';
import { cubby } from '../cubby.js';

export default async function (root) {
  const ov = await api('overview');
  S.overview = ov;
  const all = ov.worlds.flatMap(w => w.lessons.map(l => ({ ...l, world: w })));
  const next = all.find(l => l.id === ov.next);
  const doneN = all.filter(l => l.done).length;
  const p = S.profile;
  const fresh = doneN === 0;

  root.append(h('div', { class: 'hero' },
    h('div', {},
      h('div', { class: 'faint', style: { fontSize: '.8rem', letterSpacing: '.1em', textTransform: 'uppercase' } }, 'Zero to pro · Blender 3.3 / 4.x / 5.x · CPU friendly'),
      h('h1', {}, fresh ? 'Ready to boot?' : (next ? 'Welcome back, ' + (S.settings.name || 'Maker') : 'You finished the campaign!')),
      h('p', { class: 'sub' }, fresh
        ? 'Ten worlds, one goal: a lantern-lit cabin diorama you modelled, textured, lit, animated and rendered yourself. Blender runs on one screen, this page on the other, and the link checks your work as you go.'
        : next ? `Next up in ${next.world.emoji} ${next.world.title}: ${next.title}.` : 'Replay a world, hit the Hotkey Dojo, or build something of your own.'),
      h('div', { class: 'row', style: { marginTop: '14px' } },
        next && h('a', { class: 'btn pri', href: '#/lesson/' + next.id }, (fresh ? 'Start: ' : 'Continue: ') + next.title),
        !S.bridge.connected && h('a', { class: 'btn', href: '#/link' }, '🔌 Link Blender'),
        h('a', { class: 'btn ghost', href: '#/dojo' }, '⌨ Hotkey Dojo')),
      h('div', { class: 'stats' },
        h('div', { class: 'stat' }, h('b', {}, doneN + '/' + all.length), 'lessons'),
        h('div', { class: 'stat' }, h('b', {}, p.xp), 'XP'),
        h('div', { class: 'stat' }, h('b', {}, p.streak), 'day streak'),
        h('div', { class: 'stat' }, h('b', {}, p.badges.length), 'badges'))),
    h('div', { html: cubby(fresh ? 'happy' : 'wink', 'cubby-big') })));

  if (Object.keys(ov.errors || {}).length)
    root.append(h('div', { class: 'note warn' }, h('b', { class: 't' }, 'Content problems'), h('pre', {}, JSON.stringify(ov.errors, null, 1))));

  const map = h('div', { class: 'map' }, h('svg', { class: 'trail' }));
  for (const w of ov.worlds) {
    const pct = Math.round(100 * w.done / Math.max(w.count, 1));
    map.append(h('div', { class: 'wcard' + (w.done === w.count ? ' done' : ''), style: { '--wc': w.color } },
      h('div', { class: 'row' },
        h('div', { class: 'em' }, w.emoji),
        h('div', { class: 'grow' }, h('h3', {}, h('a', { href: '#/world/' + w.id, style: { color: 'inherit' } }, `${w.order}. ${w.title}`)), h('div', { class: 'tag' }, w.tagline)),
        h('div', { class: 'ring', style: { '--p': pct }, 'data-t': `${w.done}/${w.count}` })),
      w.project && h('div', { class: 'dim', style: { fontSize: '.85rem' } }, '🛠 Project: ' + w.project),
      h('div', { class: 'nodes' }, w.lessons.map((l, i) => h('a', {
        href: '#/lesson/' + l.id, title: `${l.title} · ${l.minutes} min · ${l.xp} XP`,
        class: 'node' + (l.done ? ' done' : '') + (l.id === ov.next ? ' cur' : '') + (l.boss ? ' boss' : ''),
      }, l.boss ? '☠' : (i + 1)))),
      h('div', { class: 'row faint', style: { fontSize: '.8rem', marginTop: '6px' } }, `${w.xp} XP`, h('span', { class: 'grow' }), h('a', { href: '#/world/' + w.id }, 'Open world →'))));
  }
  root.append(map);
  const draw = () => drawTrail(map, ov.worlds);
  requestAnimationFrame(draw);
  addEventListener('resize', draw);
  return () => removeEventListener('resize', draw);
}

function drawTrail(map, worlds) {
  const svg = $('svg.trail', map);
  const cards = [...map.querySelectorAll('.wcard')];
  const box = map.getBoundingClientRect();
  svg.innerHTML = '';
  svg.setAttribute('viewBox', `0 0 ${box.width} ${box.height}`);
  const pts = cards.map(c => { const r = c.getBoundingClientRect(); return [r.left - box.left + r.width / 2, r.top - box.top + r.height / 2]; });
  for (let i = 0; i < pts.length - 1; i++) {
    const [x1, y1] = pts[i], [x2, y2] = pts[i + 1];
    const my = (y1 + y2) / 2;
    const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    p.setAttribute('d', `M${x1},${y1} C${x1},${my} ${x2},${my} ${x2},${y2}`);
    p.setAttribute('fill', 'none');
    p.setAttribute('stroke', worlds[i].done === worlds[i].count ? '#5fd08a' : '#4a505a');
    p.setAttribute('stroke-width', '4'); p.setAttribute('stroke-dasharray', '2 11'); p.setAttribute('stroke-linecap', 'round');
    svg.append(p);
  }
}
