// dojo.js - Hotkey Dojo: a flash-card arena. Press the real keys; spaced repetition brings missed cards back.
// Some combos never reach a web page (the browser or the desktop keeps them), so every card can be skipped, and a key
// tester on the menu shows exactly what the page receives.
import { h, beep, clear } from '../ui.js';
import { S, api } from '../api.js';
import { capture, matches, judge, seqOf, laptopAlternatives, watchBlender, RESERVED } from '../keys.js';
import { keycaps } from '../md.js';

const SKIP_KEY = 'pc_dojo_skipped';
const loadSkipped = () => { try { return new Set(JSON.parse(localStorage.getItem(SKIP_KEY) || '[]')); } catch (e) { return new Set(); } };
const saveSkipped = s => { try { localStorage.setItem(SKIP_KEY, JSON.stringify([...s])); } catch (e) { /* private window: skips last for this visit only */ } };

export default async function (root) {
  const { decks, totals } = await api('dojo/decks');
  const picked = new Set(decks.length ? [decks[0].name] : []);
  const skipped = loadSkipped();
  let stopCap = null, timer = 0, idle = 0;
  const stage = h('div');
  root.append(h('div', { class: 'dojo' },
    h('div', { class: 'sheet' }, 'Drill'), h('h1', {}, 'Hotkey Dojo'),
    h('p', { class: 'dim' }, 'Menus are slow. Pick a deck and press the real keys on your real keyboard. The cards you miss come back sooner. Right answers earn a little XP, and now and then a gem for hints.'),
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
        h('button', { class: 'pri', onclick: () => run(10, false) }, 'Quick round (10)'),
        h('button', { onclick: () => run(25, false) }, '25 cards'),
        h('button', { onclick: () => run(15, true) }, 'Speed round, 6 s a card'),
        h('span', { class: 'grow' }), h('span', { class: 'dim' }, `lifetime: ${totals.right} right, ${totals.wrong} wrong`)),
      keyTester(),
      h('p', { class: 'faint', style: { fontSize: '.82rem' } },
        'No numpad? The number row counts for the numpad digits, and . / - count for the other numpad keys. ',
        'The browser keeps a few combos for itself (Ctrl+N, Ctrl+T, Ctrl+W, F5, F11, F12) and your desktop may keep others. Those can be skipped in a round, or live in the cheat sheet only.',
        skipped.size ? [' ', h('b', {}, `${skipped.size} card${skipped.size > 1 ? 's' : ''} skipped as unpressable. `), h('a', { href: '#', onclick: e => { e.preventDefault(); skipped.clear(); saveSkipped(skipped); menu(); } }, 'Bring them back')] : null));
  };

  // A box you click and then press anything in: shows what the page receives, so "nothing happens" can be told apart from
  // "your desktop keeps that key".
  function keyTester() {
    const out = h('div', { class: 'out' }, 'Click here, then press any key or combo.');
    let stop = null;
    const box = h('div', { class: 'keytest', tabindex: '0', onfocus: () => {
      if (stop) return;
      box.classList.add('live');
      out.textContent = 'Listening. Press something.';
      stop = capture((combo, e) => { out.innerHTML = `${keycaps(combo)} <span class="faint mono"> code ${e.code || '-'} · key ${JSON.stringify(e.key)}</span>`; },
        held => { if (held.length) out.innerHTML = held.map(k => keycaps(k)).join(' + ') + ' …'; });
    }, onblur: () => { stop && stop(); stop = null; box.classList.remove('live'); out.textContent = 'Click here, then press any key or combo.'; } },
      h('b', {}, 'Key tester'), out,
      h('div', { class: 'faint', style: { fontSize: '.8rem' } }, 'If a key shows nothing here, your browser or desktop is keeping it. It can not be drilled on this page.'));
    return box;
  }

  async function run(n, speed) {
    const r = await api('dojo/queue?n=' + (n * 3) + '&decks=' + encodeURIComponent([...picked].join('|')));
    const cards = r.cards.filter(c => !skipped.has(c.id) && !RESERVED.test(c.combo.replace(/\s/g, '')) && !/mouse|lmb|mmb|rmb|wheel|drag/i.test(c.combo)).slice(0, n);
    if (!cards.length) { clear(stage); stage.append(h('div', { class: 'card' }, 'No cards in those decks.'), h('button', { onclick: menu }, 'Back')); return; }
    let i = 0, right = 0, combo = 0, best = 0, locked = false, step = 0;
    const arena = h('div', { class: 'arena' });
    clear(stage); stage.append(arena);
    const finish = () => {
      stopCap && stopCap(); clearTimeout(idle);
      clear(arena);
      arena.append(h('h2', {}, right === cards.length ? 'Perfect round' : 'Round over'), h('p', { class: 'dim' }, `${right} of ${cards.length} right, best run ${best}`),
        h('div', { class: 'row', style: { justifyContent: 'center' } }, h('button', { class: 'pri', onclick: () => run(n, speed) }, 'Again'), h('button', { onclick: () => { api('dojo/decks').then(d => { decks.splice(0, decks.length, ...d.decks); Object.assign(totals, d.totals); menu(); }); } }, 'Decks')));
    };
    const next = () => { i++; step = 0; i >= cards.length ? finish() : show(); };
    const show = () => {
      clearTimeout(timer); clearTimeout(idle);
      locked = false; step = 0;
      const c = cards[i];
      arena.className = 'arena';
      clear(arena);
      const bar = h('div', { class: 'bar timer' }, h('i', { style: { width: '100%', transition: speed ? 'width 6s linear' : 'none' } }));
      const lap = laptopAlternatives(c.combo);
      const seq = seqOf(c.combo);
      const skipBtn = h('button', { class: 'sm ghost skip', onclick: () => skip() }, 'Can’t press this one: skip');
      const linked = S.bridge && S.bridge.connected;
      arena.append(h('div', { class: 'combo' }, combo > 1 ? `x${combo}` : ''), h('div', { class: 'faint' }, `${c.deck} · ${i + 1}/${cards.length}`),
        h('div', { class: 'q' }, c.action), h('div', { class: 'tip' }, c.tip || ''),
        h('div', { class: 'lap', html: lap.length ? 'No numpad? ' + lap.map(a => keycaps(a)).join(' or ') + ' works too.' : (seq ? `Press ${seq.length} times in a row, one after the other.` : '') }),
        h('div', { class: 'got' }, 'press the keys…'), ...(speed ? [bar] : []),
        h('div', { class: 'skiprow' }, skipBtn),
        h('div', { class: 'faint', style: { fontSize: '.8rem', marginTop: '10px' } }, linked ? 'Blender is linked: press the keys in Blender if you like (it just listens during a round, nothing happens in your scene), no need to click back here.' : 'Link Blender and you can press the keys in Blender instead of here.'));
      // nothing has reached the page for a while: say so, and make the way out obvious
      idle = setTimeout(() => {
        const g = arena.querySelector('.got');
        if (g && !locked) { g.textContent = 'Nothing arriving? Your browser or desktop may be keeping this one.'; skipBtn.classList.add('pri'); }
      }, 7000);
      if (speed) { requestAnimationFrame(() => requestAnimationFrame(() => { bar.firstChild.style.width = '0%'; })); timer = setTimeout(() => answer(null), 6000); }
    };
    const skip = () => {
      if (locked) return;
      locked = true; clearTimeout(timer); clearTimeout(idle);
      skipped.add(cards[i].id); saveSkipped(skipped);
      next();
    };
    const answer = async (got) => {
      if (locked) return;
      locked = true; clearTimeout(timer); clearTimeout(idle);
      const c = cards[i];
      const ok = got != null && matches(c.combo, got);
      right += ok ? 1 : 0; combo = ok ? combo + 1 : 0; best = Math.max(best, combo);
      beep(ok ? 'tick' : 'bad', S.settings.sound);
      arena.classList.add(ok ? 'ok' : 'no');
      arena.querySelector('.got').innerHTML = ok ? keycaps(got) : `${got ? 'You pressed ' + keycaps(got) + '. ' : 'Out of time. '}It is ${keycaps(c.combo)}`;
      api('dojo/result', { id: c.id, ok });
      setTimeout(next, ok ? 650 : 1700);
    };
    const onKey = pressed => {
      if (locked) return;
      clearTimeout(idle);
      const c = cards[i], st = { step };
      const r = judge(c.combo, pressed, st);
      step = st.step;
      if (r === 'more') { arena.querySelector('.got').innerHTML = seqOf(c.combo).slice(0, step).map(k => keycaps(k)).join(' then ') + ' then …'; return; }
      answer(r === 'ok' && seqOf(c.combo) ? c.combo : pressed);
    };
    const onHeld = held => {
      if (locked) return;
      clearTimeout(idle);
      const got = arena.querySelector('.got');
      if (got) got.innerHTML = held.length ? held.map(k => keycaps(k)).join(' + ') + ' + …' : 'press the keys…';
    };
    stopCap && stopCap();
    const stopBrowser = capture(onKey, onHeld);
    const stopBlender = watchBlender(onKey, () => arena.isConnected, { swallow: true });   // keys pressed in Blender count too, and do nothing there
    stopCap = () => { stopBrowser(); stopBlender(); };
    show();
  }

  menu();
  return () => { stopCap && stopCap(); clearTimeout(timer); clearTimeout(idle); };
}
