// badges.js - rank, XP and achievement badges.
import { h } from '../ui.js';
import { S, api } from '../api.js';
import { cubby } from '../cubby.js';
import { icon } from '../icons.js';

export default async function (root) {
  const { badges } = await api('badges');
  const p = S.profile, lv = p.level;
  root.append(
    h('div', { class: 'hero' }, h('div', {},
      h('div', { class: 'sheet' }, 'Current rank'), h('h1', {}, `Level ${lv.n}: ${lv.title}`),
      h('div', { class: 'bar', style: { maxWidth: '420px', margin: '8px 0' } }, h('i', { style: { width: lv.pct + '%' } })),
      h('div', { class: 'dim' }, lv.to ? `${lv.xp} of ${lv.to} XP to the next rank` : `${lv.xp} XP. Top rank.`),
      h('div', { class: 'leaders' }, ...[['Gems', p.gems], ['Day streak', p.streak], ['Dojo hits', p.dojo.right], ['Badges', badges.filter(b => b.have).length + ' / ' + badges.length]].map(([k, v]) => h('div', { class: 'lead' }, k, h('i'), h('b', {}, v))))),
      h('div', { html: cubby('smug', 'cubby-big') })),
    h('h2', {}, 'Badges'),
    h('div', { class: 'badges' }, badges.map(b => h('div', { class: 'card badge' + (b.have ? '' : ' locked') }, h('div', { class: 'e', html: icon(b.emoji, 38) }), h('b', {}, b.title), h('div', { class: 'dim', style: { fontSize: '.84rem' } }, b.desc)))));
}
