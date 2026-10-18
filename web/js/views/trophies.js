// trophies.js - the Trophy Room: every render Blender finished while linked.
import { h, lightbox, ago, fmtTime } from '../ui.js';
import { api } from '../api.js';

export default async function (root) {
  const { renders } = await api('trophies');
  root.append(h('h1', {}, '🖼 Trophy Room'), h('p', { class: 'dim' }, 'Every render you finish in Blender (F12) while linked lands here automatically, with how long your CPU suffered for it.'));
  if (!renders.length) {
    root.append(h('div', { class: 'card', style: { maxWidth: '640px' } }, h('h3', { style: { marginTop: 0 } }, 'Empty wall'),
      h('p', {}, 'Press ', h('kbd', {}, 'F12'), ' in Blender. A Draft render (960×540, 24 samples) of the default cube is a fine first trophy.'),
      h('p', { class: 'dim' }, 'Tip: the Polycamp tab in Blender has a CPU-friendly render preset button.')));
    return;
  }
  root.append(h('div', { class: 'gallery' }, renders.map(r => h('div', { class: 'card trophy' },
    h('img', { src: '/files/renders/' + r.name, loading: 'lazy', onclick: () => lightbox('/files/renders/' + r.name) }),
    h('div', { class: 'cap' },
      h('div', { class: 'row' }, h('b', { class: 'grow' }, r.lesson ? 'During ' + r.lesson : 'Render'), h('button', { class: 'sm ghost', onclick: async e => { r.fav = r.fav ? 0 : 1; await api('trophies/fav', { n: r.n, fav: r.fav }); e.target.textContent = r.fav ? '★' : '☆'; } }, r.fav ? '★' : '☆')),
      h('div', { class: 'dim' }, [r.meta.engine && r.meta.engine.replace('BLENDER_', ''), r.meta.res && r.meta.res.join('×'), r.meta.samples && r.meta.samples + ' spp', r.meta.time && '⏱ ' + fmtTime(r.meta.time)].filter(Boolean).join(' · ')),
      h('div', { class: 'faint', style: { fontSize: '.8rem' } }, ago(r.ts) + (r.meta.blend ? ' · ' + r.meta.blend : '')))))));
}
