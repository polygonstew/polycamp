// world.js - one world: its story, its project, and its lessons in order (boss last).
import { h } from '../ui.js';
import { S, api } from '../api.js';
import { md } from '../md.js';
import { icon, worldGlyph } from '../icons.js';

export default async function (root, [wid]) {
  const ov = S.overview || await api('overview');
  const w = ov.worlds.find(x => x.id === wid);
  if (!w) { root.append(h('p', {}, 'No such world.')); return; }
  const pct = Math.round(100 * w.done / Math.max(w.count, 1));
  root.append(
    h('div', { class: 'crumbs' }, h('a', { href: '#/' }, 'Map'), ' / ', w.title),
    h('div', { class: 'row', style: { margin: '12px 0 6px', gap: '18px' } },
      h('div', { style: { color: w.color }, html: worldGlyph(w.id, 52) }),
      h('div', { class: 'grow' }, h('div', { class: 'sheet' }, 'World ' + String(w.order).padStart(2, '0')), h('h1', { style: { margin: 0 } }, w.title), h('div', { class: 'dim', style: { fontFamily: 'var(--serif)' } }, w.tagline)),
      h('div', { style: { width: '230px' } }, h('div', { class: 'row sheet', style: { justifyContent: 'space-between' } }, h('span', {}, `${w.done} of ${w.count}`), h('span', {}, pct + '%')), h('div', { class: 'bar' }, h('i', { style: { width: pct + '%' } })))),
    w.project && h('div', { class: 'sheet', style: { margin: '10px 0' } }, 'Project: ' + w.project),
    h('div', { class: 'card md', style: { maxWidth: '860px', fontFamily: 'var(--serif)' }, html: md(w.body) }),
    h('h2', {}, 'Lessons'),
    h('div', { style: { maxWidth: '860px' } }, w.lessons.map((l, i) => h('a', { class: 'lrow' + (l.done ? ' done' : '') + (l.id === ov.next ? ' next' : '') + (l.boss ? ' boss' : ''), href: '#/lesson/' + l.id },
      h('div', { class: 'n', html: l.done ? icon('check', 16) : (l.boss ? icon('skull', 16) : String(i + 1)) }),
      h('div', {}, h('b', {}, l.title), h('div', { class: 'dim', style: { fontSize: '.88rem' } }, l.summary)),
      h('div', { class: 'row' }, l.boss && h('span', { class: 'pill boss' }, 'Boss'), h('span', { class: 'pill' }, l.minutes + ' min'), h('span', { class: 'pill acc' }, l.xp + ' XP'))))));
}
