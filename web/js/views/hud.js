// hud.js - pop-out window for a second monitor (or a corner of the only one): just the live tasks.
import { h, clear } from '../ui.js';
import { S, api, on } from '../api.js';
import { mountMission } from '../mission.js';

export default async function (root) {
  const wrap = h('div');
  root.append(wrap);
  let mission = null, curId = null;
  const ctx = { lesson: null, hasSolution: () => false, refresh: () => mission && mission.refresh() };

  async function sync() {
    const hud = S.live.hud;
    const id = hud && hud.lesson ? hud.lesson.id : null;
    if (id === curId && mission) return;
    curId = id;
    if (mission) mission.off();
    clear(wrap);
    if (!id) {
      wrap.append(h('div', { class: 'card' }, h('h3', { style: { marginTop: 0 } }, 'No lesson open'), h('p', { class: 'dim' }, 'Pick a lesson in the main Polycamp window and its tasks show up here.')));
      mission = null;
      return;
    }
    const les = await api('lesson/' + id);
    ctx.lesson = les;
    ctx.hasSolution = () => les.state.has_solution;
    const lv = hud.level;
    wrap.append(
      h('div', { class: 'row', style: { marginBottom: '8px' } }, h('b', { class: 'grow' }, les.title), h('a', { class: 'btn sm', href: '#/lesson/' + id, target: '_blank' }, 'open')),
      h('div', { class: 'bar', style: { marginBottom: '10px' }, title: lv.title }, h('i', { style: { width: lv.pct + '%' } })));
    const m = h('aside', { id: 'mission' });
    wrap.append(m);
    mission = mountMission(m, ctx);
  }
  await sync();
  const off = on('live', sync);
  return () => { off(); mission && mission.off(); };
}
