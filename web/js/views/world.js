// world.js - one world: story, project, and its lessons as a path (boss last).
import { h } from '../ui.js';
import { S, api } from '../api.js';
import { md } from '../md.js';

export default async function (root, [wid]) {
  const ov = S.overview || await api('overview');
  const w = ov.worlds.find(x => x.id === wid);
  if (!w) { root.append(h('p', {}, 'No such world.')); return; }
  const pct = Math.round(100 * w.done / Math.max(w.count, 1));
  root.append(
    h('div', { class: 'crumbs' }, h('a', { href: '#/' }, 'Map'), ' / ', w.title),
    h('div', { class: 'row', style: { margin: '10px 0 4px' } },
      h('div', { style: { fontSize: '3rem' } }, w.emoji),
      h('div', { class: 'grow' }, h('h1', { style: { margin: 0 } }, `World ${w.order}: ${w.title}`), h('div', { class: 'dim' }, w.tagline)),
      h('div', { style: { width: '220px' } }, h('div', { class: 'lbl row', style: { justifyContent: 'space-between', fontSize: '.8rem' } }, h('span', {}, `${w.done}/${w.count} lessons`), h('span', {}, pct + '%')), h('div', { class: 'bar' }, h('i', { style: { width: pct + '%' } })))),
    w.project && h('div', { class: 'pill acc', style: { margin: '6px 0 10px' } }, '🛠 Project: ' + w.project),
    h('div', { class: 'card', style: { maxWidth: '860px' }, html: md(w.body) }),
    h('h2', {}, 'Lessons'),
    h('div', { style: { maxWidth: '860px' } }, w.lessons.map((l, i) => h('a', { class: 'lrow' + (l.done ? ' done' : '') + (l.id === ov.next ? ' next' : '') + (l.boss ? ' boss' : ''), href: '#/lesson/' + l.id },
      h('div', { class: 'n' }, l.done ? '✓' : (l.boss ? '☠' : i + 1)),
      h('div', {}, h('b', {}, l.title), h('div', { class: 'dim', style: { fontSize: '.86rem' } }, l.summary)),
      h('div', { class: 'row' }, l.boss && h('span', { class: 'pill boss' }, 'BOSS'), h('span', { class: 'pill' }, l.minutes + ' min'), h('span', { class: 'pill acc' }, l.xp + ' XP'))))));
}
