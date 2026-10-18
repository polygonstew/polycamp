// home.js - the cover of the manual: where you are, then the trail map of worlds with contour lines behind it.
import { h, $ } from '../ui.js';
import { S, api } from '../api.js';
import { cubby } from '../cubby.js';
import { icon, worldGlyph } from '../icons.js';

export default async function (root) {
  const ov = await api('overview');
  S.overview = ov;
  const all = ov.worlds.flatMap(w => w.lessons.map(l => ({ ...l, world: w })));
  const next = all.find(l => l.id === ov.next);
  const doneN = all.filter(l => l.done).length;
  const p = S.profile;
  const fresh = doneN === 0;
  const name = S.settings.name || 'Maker';
  const lead = (k, v) => h('div', { class: 'lead' }, k, h('i'), h('b', {}, v));

  root.append(h('div', { class: 'hero' },
    h('div', {},
      h('div', { class: 'sheet' }, 'Field manual / Blender 3.3, 4.x and 5.x / no GPU needed'),
      h('h1', {}, fresh ? 'Blender, from the default cube up.' : next ? `Welcome back, ${name}.` : 'You finished the manual.'),
      h('p', { class: 'sub' }, fresh
        ? `${all.length} short lessons and ${ov.worlds.length} bosses. You work in Blender. This page watches your scene through a small add-on and ticks a task off when you have really done it. The last boss is a lantern-lit cabin that you built and rendered yourself.`
        : next ? `Next up: ${next.title}, in ${next.world.title}.` : 'Replay a world, drill hotkeys in the Dojo, or go and make something of your own.'),
      h('div', { class: 'row', style: { marginTop: '14px' } },
        next && h('a', { class: 'btn pri', href: '#/lesson/' + next.id, html: (fresh ? 'Start with ' : 'Continue: ') + next.title + ' ' + icon('arrow', 16) }),
        !S.bridge.connected && h('a', { class: 'btn', href: '#/link', html: icon('plug', 16) + ' Link Blender' }),
        h('a', { class: 'btn ghost', href: '#/dojo', html: icon('keys', 16) + ' Hotkey Dojo' })),
      h('div', { class: 'leaders' }, lead('Lessons', `${doneN} / ${all.length}`), lead('Experience', `${p.xp} XP`), lead('Streak', `${p.streak} day${p.streak === 1 ? '' : 's'}`), lead('Badges', p.badges.length))),
    h('div', { html: cubby(fresh ? 'happy' : 'wink', 'cubby-big') })));

  if (Object.keys(ov.errors || {}).length)
    root.append(h('div', { class: 'note warn' }, h('b', { class: 't' }, 'Content problems'), h('pre', {}, JSON.stringify(ov.errors, null, 1))));

  const map = h('div', { class: 'map' }, h('svg', { class: 'topo' }), h('svg', { class: 'trail' }));
  for (const w of ov.worlds) {
    map.append(h('div', { class: 'wcard' + (w.done === w.count ? ' done' : ''), 'data-n': String(w.order).padStart(2, '0'), style: { '--wc': w.color } },
      h('div', { class: 'row', style: { alignItems: 'flex-start' } },
        h('div', { class: 'em', html: worldGlyph(w.id, 34) }),
        h('div', { class: 'grow' }, h('h3', {}, h('a', { href: '#/world/' + w.id }, w.title)), h('div', { class: 'tag' }, w.tagline))),
      w.project && h('div', { class: 'sheet' }, 'Project: ' + w.project),
      h('div', { class: 'nodes' }, w.lessons.map((l, i) => h('a', {
        href: '#/lesson/' + l.id, title: `${l.title} / ${l.minutes} min / ${l.xp} XP`,
        class: 'node' + (l.done ? ' done' : '') + (l.id === ov.next ? ' cur' : '') + (l.boss ? ' boss' : ''),
      }, l.boss ? '' : (i + 1)))),
      h('div', { class: 'row ticks' }, `${w.done} of ${w.count} done / ${w.xp} XP`, h('span', { class: 'grow' }), h('a', { href: '#/world/' + w.id }, 'Open'))));
  }
  root.append(map);
  const draw = () => { drawTopo(map); drawTrail(map, ov.worlds); };
  requestAnimationFrame(draw);
  addEventListener('resize', draw);
  return () => removeEventListener('resize', draw);
}

const NS = 'http://www.w3.org/2000/svg';
const mk = (tag, attrs) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; };

// contour lines around a few "peaks", so the map looks like a map and not a list of cards
function drawTopo(map) {
  const svg = $('svg.topo', map), box = map.getBoundingClientRect();
  svg.innerHTML = '';
  svg.setAttribute('viewBox', `0 0 ${box.width} ${box.height + 20}`);
  const peaks = [[.18, .12, 1], [.82, .45, 1.3], [.25, .78, 1.1], [.78, .95, .9]];
  peaks.forEach(([fx, fy, k], n) => {
    for (let r = 30; r < 560; r += 30 * k) {
      let d = '';
      for (let i = 0; i <= 96; i++) {
        const a = i / 96 * Math.PI * 2;
        const rr = r * (1 + .12 * Math.sin(3 * a + n) + .07 * Math.sin(5 * a + n * 2.3) + .04 * Math.sin(8 * a + r / 70));
        d += (i ? 'L' : 'M') + (fx * box.width + Math.cos(a) * rr * 1.25).toFixed(1) + ',' + (fy * box.height + Math.sin(a) * rr * .8).toFixed(1);
      }
      svg.append(mk('path', { d: d + 'Z', fill: 'none', stroke: 'rgba(236,229,211,.13)', 'stroke-width': r % 150 < 30 ? 1.6 : 1 }));
    }
  });
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
    svg.append(mk('path', { d: `M${x1},${y1} C${x1},${my} ${x2},${my} ${x2},${y2}`, fill: 'none', stroke: worlds[i].done === worlds[i].count ? '#9ccc5a' : '#8a806a',
      'stroke-width': 3, 'stroke-dasharray': '9 7', 'stroke-linecap': 'butt' }));
  }
}
