// ref.js - searchable hotkey cheat sheet; opens fine as a pop-out on the second monitor (#/ref).
import { h, clear } from '../ui.js';
import { api } from '../api.js';
import { keycaps } from '../md.js';

export default async function (root) {
  const { decks } = await api('cheatsheet');
  const out = h('div');
  const q = h('input', { type: 'search', placeholder: 'search: extrude, bevel, F12…', style: { width: '100%', maxWidth: '420px' }, oninput: draw });
  root.append(h('h2', { style: { marginTop: 0 } }, 'Hotkeys'), q, out);
  function draw() {
    const t = q.value.toLowerCase();
    clear(out);
    for (const [name, cards] of Object.entries(decks)) {
      const rows = cards.filter(c => !t || (c.action + c.combo + c.tip).toLowerCase().includes(t));
      if (!rows.length) continue;
      out.append(h('h3', {}, name), h('table', {}, rows.map(c => h('tr', {}, h('td', {}, c.action), h('td', { html: c.combo.split(/\s+or\s+/i).map(keycaps).join(' <span class="dim">or</span> ') }), h('td', { class: 'dim' }, c.tip)))));
    }
  }
  draw();
}
