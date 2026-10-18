// badges.js - rank, XP and achievement badges.
import { h } from '../ui.js';
import { S, api } from '../api.js';
import { cubby } from '../cubby.js';

export default async function (root) {
  const { badges } = await api('badges');
  const p = S.profile, lv = p.level;
  root.append(
    h('div', { class: 'hero' }, h('div', {},
      h('div', { class: 'faint' }, 'Current rank'), h('h1', {}, `Level ${lv.n}: ${lv.title}`),
      h('div', { class: 'bar', style: { maxWidth: '420px', margin: '8px 0' } }, h('i', { style: { width: lv.pct + '%' } })),
      h('div', { class: 'dim' }, lv.to ? `${lv.xp} / ${lv.to} XP to the next rank` : `${lv.xp} XP. Top rank!`),
      h('div', { class: 'stats' }, h('div', { class: 'stat' }, h('b', {}, p.gems), 'gems'), h('div', { class: 'stat' }, h('b', {}, p.streak), 'day streak'),
        h('div', { class: 'stat' }, h('b', {}, p.dojo.right), 'dojo hits'), h('div', { class: 'stat' }, h('b', {}, badges.filter(b => b.have).length + '/' + badges.length), 'badges'))),
      h('div', { html: cubby('smug', 'cubby-big') })),
    h('h2', {}, 'Badges'),
    h('div', { class: 'badges' }, badges.map(b => h('div', { class: 'card badge' + (b.have ? '' : ' locked') }, h('div', { class: 'e' }, b.emoji), h('b', {}, b.title), h('div', { class: 'dim', style: { fontSize: '.84rem' } }, b.desc)))));
}
