// dojo.js - Hotkey Dojo: a flash-card arena. Press the real keys; spaced repetition brings missed cards back.
import { h, beep, clear } from '../ui.js';
import { S, api } from '../api.js';
import { capture, matches, RESERVED } from '../keys.js';
import { keycaps } from '../md.js';

export default async function (root) {
  const { decks, totals } = await api('dojo/decks');
  const picked = new Set(decks.length ? [decks[0].name] : []);
  let stopCap = null, timer = 0;
  const stage = h('div');
  root.append(h('div', { class: 'dojo' },
    h('h1', {}, '⌨ Hotkey Dojo'),
    h('p', { class: 'dim' }, 'The fastest way to get “pro” is to stop hunting menus. Pick decks, press the keys on your real keyboard, and the cards you miss come back sooner. Correct answers earn a little XP and 💎 for hints.'),
    stage));

  const menu = () => {
    clear(stage);
    stage.append(
      h('div', { class: 'decks' }, decks.map(d => {
        const el = h('div', { class: 'card deck' + (picked.has(d.name) ? ' sel' : ''), onclick: () => { picked.has(d.name) ? picked.delete(d.name) : picked.add(d.name); el.classList.toggle('sel'); } },
          h('b', {}, d.name), h('div', { class: 'dim', style: { fontSize: '.85rem' } }, `${d.cards} cards · ${d.due} due · ${d.known} known`),
          h('div', { class: 'bar', style: { marginTop: '8px' } }, h('i', { style: { width: Math.round(100 * d.known / d.cards) + '%' } })));
        return el;
      })),
      h('div', { class: 'row', style: { marginTop: '16px' } },
        h('button', { class: 'pri', onclick: () => run(10, false) }, '▶ Quick round (10)'),
        h('button', { onclick: () => run(25, false) }, '25 cards'),
        h('button', { onclick: () => run(15, true) }, '⏱ Speed round (6 s per card)'),
        h('span', { class: 'grow' }), h('span', { class: 'dim' }, `lifetime: ${totals.right} right, ${totals.wrong} wrong`)),
      h('p', { class: 'faint', style: { fontSize: '.82rem' } }, 'The browser keeps a few combos for itself (Ctrl+N, Ctrl+T, Ctrl+W, F5, F11, F12). Those cards live in the cheat sheet only.'));
  };

  async function run(n, speed) {
    const r = await api('dojo/queue?n=' + (n * 2) + '&decks=' + encodeURIComponent([...picked].join('|')));
    const cards = r.cards.filter(c => !RESERVED.test(c.combo.replace(/\s/g, '')) && !/mouse|lmb|mmb|rmb|wheel|drag/i.test(c.combo)).slice(0, n);
    if (!cards.length) { clear(stage); stage.append(h('div', { class: 'card' }, 'No cards in those decks.'), h('button', { onclick: menu }, 'Back')); return; }
    let i = 0, right = 0, combo = 0, best = 0, locked = false;
    const arena = h('div', { class: 'arena' });
    clear(stage); stage.append(arena);
    const finish = () => {
      stopCap && stopCap();
      clear(arena);
      arena.append(h('h2', {}, right === cards.length ? '🏆 Perfect round' : 'Round complete'), h('p', { class: 'dim' }, `${right}/${cards.length} correct · best streak ${best}`),
        h('div', { class: 'row', style: { justifyContent: 'center' } }, h('button', { class: 'pri', onclick: () => run(n, speed) }, 'Again'), h('button', { onclick: () => { api('dojo/decks').then(d => { decks.splice(0, decks.length, ...d.decks); Object.assign(totals, d.totals); menu(); }); } }, 'Decks')));
    };
    const show = () => {
      clearTimeout(timer);
      locked = false;
      const c = cards[i];
      arena.className = 'arena';
      clear(arena);
      const bar = h('div', { class: 'bar timer' }, h('i', { style: { width: '100%', transition: speed ? 'width 6s linear' : 'none' } }));
      arena.append(h('div', { class: 'combo' }, combo > 1 ? `🔥 ${combo}` : ''), h('div', { class: 'faint' }, `${c.deck} · ${i + 1}/${cards.length}`),
        h('div', { class: 'q' }, c.action), h('div', { class: 'tip' }, c.tip || ''), h('div', { class: 'got' }, 'press the keys…'), speed ? bar : null);
      if (speed) { requestAnimationFrame(() => requestAnimationFrame(() => { bar.firstChild.style.width = '0%'; })); timer = setTimeout(() => answer(null), 6000); }
    };
    const answer = async (got) => {
      if (locked) return;
      locked = true; clearTimeout(timer);
      const c = cards[i];
      const ok = got != null && matches(c.combo, got);
      right += ok ? 1 : 0; combo = ok ? combo + 1 : 0; best = Math.max(best, combo);
      beep(ok ? 'tick' : 'bad', S.settings.sound);
      arena.classList.add(ok ? 'ok' : 'no');
      arena.querySelector('.got').innerHTML = ok ? `✔ ${keycaps(got)}` : `${got ? 'You pressed ' + keycaps(got) + '. ' : 'Time! '}It is ${keycaps(c.combo)}`;
      api('dojo/result', { id: c.id, ok });
      setTimeout(() => { i++; i >= cards.length ? finish() : show(); }, ok ? 650 : 1700);
    };
    stopCap && stopCap();
    stopCap = capture(combo => answer(combo));
    show();
  }

  menu();
  return () => { stopCap && stopCap(); clearTimeout(timer); };
}
