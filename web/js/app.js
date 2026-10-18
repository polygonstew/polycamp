// app.js - boot, hash router, top bar, and the global reactions to live events (toasts, confetti, level-ups).
import { h, $, clear, toast, modal, confetti, beep } from './ui.js';
import { S, on, api, loadState, connectEvents, layoutMode, saveSetting, applySettings } from './api.js';
import { cubby, logoSvg, quip } from './cubby.js';

const VIEWS = {
  '': 'home', world: 'world', lesson: 'lesson', dojo: 'dojo', lab: 'lab', uv: 'uv', trophies: 'trophies',
  badges: 'badges', settings: 'settings', link: 'link', hud: 'hud', ref: 'ref',
};
let cleanup = null;

function parse() {
  const [, name = '', ...rest] = location.hash.replace(/^#/, '').split('/');
  return { name, params: rest.map(decodeURIComponent) };
}

async function route() {
  const { name, params } = parse();
  const mod = VIEWS[name] || 'home';
  if (cleanup) { try { cleanup(); } catch (e) { console.error(e); } cleanup = null; }
  document.body.classList.toggle('hudonly', name === 'hud' || name === 'ref');
  const root = clear($('#view'));
  window.scrollTo(0, 0);
  try {
    const m = await import(`./views/${mod}.js`);
    cleanup = (await m.default(root, params)) || null;
  } catch (e) {
    console.error(e);
    root.append(h('div', { class: 'card' }, h('h2', {}, 'Something broke'), h('pre', {}, String(e.stack || e))));
  }
  renderTop();
}

// ---------------------------------------------------------------- top bar
function renderTop() {
  const { name } = parse();
  const top = clear($('#top'));
  const p = S.profile || { level: { n: 1, title: 'Default Cube', pct: 0, xp: 0 }, gems: 0, streak: 0 };
  const lv = p.level;
  const conn = S.bridge.connected;
  const cl = (S.bridge.clients || []).find(c => c.alive);
  const nav = [['', 'Map'], ['dojo', 'Hotkey Dojo'], ['lab', 'Texture Lab'], ['uv', 'UV Lab'], ['trophies', 'Trophy Room'], ['badges', 'Badges']];
  top.append(
    h('a', { class: 'logo', href: '#/', html: logoSvg() + '<span>Polycamp</span>' }),
    h('nav', { class: 'main' }, nav.map(([k, t]) => h('a', { href: '#/' + k, class: name === k ? 'on' : '' }, t))),
    h('div', { class: 'grow' }),
    h('a', { class: 'chip', href: '#/link', title: conn ? 'Blender is linked' : 'Click to set up the Blender link' },
      h('span', { class: 'dot' + (conn ? ' on' : '') }),
      conn ? `Blender ${cl ? cl.blender.replace(/ LTS/, '') : ''}${cl && cl.file ? ' · ' + cl.file : ''}` : 'Blender not linked'),
    h('button', { class: 'chip', title: 'Layout: ' + (S.settings.layout || 'auto') + ' (click to change)', onclick: cycleLayout },
      layoutMode() === 'dual' ? '🖥🖥 Dual' : '🖥 Single'),
    h('button', { class: 'chip', title: 'Open a small always-on-top-able task window for your second screen', onclick: popHud }, '⧉ HUD'),
    h('span', { class: 'chip', title: 'Day streak' }, '🔥 ' + p.streak),
    h('span', { class: 'chip', title: 'Gems: spend them on hints and solution peeks' }, '💎 ' + p.gems),
    h('a', { class: 'xpbar', href: '#/badges', title: lv.xp + ' XP' },
      h('div', { class: 'lbl' }, h('b', {}, `Lv ${lv.n} ${lv.title}`), h('span', {}, lv.to ? `${lv.xp}/${lv.to}` : `${lv.xp} XP`)),
      h('div', { class: 'bar' }, h('i', { style: { width: lv.pct + '%' } }))),
    h('a', { class: 'chip', href: '#/settings', title: 'Settings' }, '⚙'),
  );
}

async function cycleLayout() {
  const order = ['auto', 'dual', 'single'];
  const cur = S.settings.layout || 'auto';
  const next = order[(order.indexOf(cur) + 1) % 3];
  await saveSetting({ layout: next });
  toast(`Layout: <b>${next}</b>${next === 'auto' ? ' (switches by window width)' : ''}`, 'info', 2200);
  route();
}

export function popHud() {
  const w = window.open(location.origin + '/#/hud', 'polycamp-hud', 'width=440,height=720,left=40,top=40');
  if (!w) toast('The browser blocked the pop-up. Allow pop-ups for this site.', 'bad');
}

// ---------------------------------------------------------------- live reactions
on('live', renderTop);
on('profile', renderTop);
on('award', m => {
  const parts = [];
  if (m.xp) parts.push(`+${m.xp} XP`);
  if (m.gems > 0) parts.push(`+${m.gems} 💎`);
  if (m.gems < 0) parts.push(`${m.gems} 💎`);
  if (m.streak_bonus) parts.push(`streak bonus +${m.streak_bonus} 💎`);
  if (parts.length && m.kind !== 'dojo') toast(`<div class="big">${parts.join('  ')}</div><div class="dim">${m.note || ''}</div>`, m.xp ? 'good' : 'info', 3200);
  if (m.level_up) {
    beep('level', S.settings.sound);
    confetti(innerWidth / 2, innerHeight / 3, 160);
    const mo = modal([h('div', { html: cubby('wink', 'cubby-big') }), h('h2', {}, `Level ${m.level.n}: ${m.level.title}`),
      h('p', { class: 'dim' }, quip('done')), h('button', { class: 'btn pri', onclick: () => mo.close() }, 'Keep going')]);
  }
});
on('task_done', m => {
  beep('task', S.settings.sound);
  confetti(innerWidth * .62, innerHeight * .4, 50);
  toast(`<div class="big">✔ ${m.title}</div><div class="dim">${m.how === 'auto' ? 'Blender confirmed it' : m.how}</div>`, 'good', 3500);
});
on('lesson_done', m => {
  confetti(innerWidth / 2, innerHeight / 3, m.boss ? 260 : 150);
  const mo = modal([h('div', { html: cubby(m.boss ? 'shock' : 'happy', 'cubby-big') }),
    h('h2', {}, m.boss ? '⚔ Boss defeated!' : 'Lesson complete'), h('p', {}, h('b', {}, m.title)),
    h('p', { class: 'dim' }, `+${m.xp} XP bonus. ${quip('done')}`),
    h('div', { class: 'row', style: { justifyContent: 'center' } },
      m.next ? h('a', { class: 'btn pri', href: '#/lesson/' + m.next, onclick: () => mo.close() }, 'Next: ' + m.next_title) : h('a', { class: 'btn pri', href: '#/', onclick: () => mo.close() }, 'Back to the map'),
      h('button', { class: 'btn', onclick: () => mo.close() }, 'Stay here'))]);
});
on('badge', m => { confetti(innerWidth - 120, innerHeight - 120, 40); toast(`<div class="big">${m.badge.emoji} Badge: ${m.badge.title}</div><div class="dim">${m.badge.desc}</div>`, 'good', 5000); });
on('render', m => toast(`<div class="big">🖼 New render saved</div><a href="#/trophies">Open the Trophy Room</a>`, 'info', 6000));
on('texture', m => toast(`Texture set <b>${m.set}</b> saved.`, 'info', 3000));
on('model', m => toast(m.exported ? `Model exported to <code>${m.exported}</code>` : 'Model received (set a Godot folder in Settings to copy it).', 'info', 5000));

// ---------------------------------------------------------------- boot
window.addEventListener('hashchange', route);
window.addEventListener('resize', () => { const was = document.body.classList.contains('single'); applySettings(); if (was !== document.body.classList.contains('single')) route(); });
(async () => {
  await loadState();
  connectEvents();
  await route();
})();
