// keys.js - turn a browser KeyboardEvent into Blender-style combo text ("Ctrl+Shift+A") and compare combos.
import { S, api, on } from './api.js';

const NAMED = {
  Space: 'Space', Tab: 'Tab', Enter: 'Enter', NumpadEnter: 'Numpad Enter', Escape: 'Esc', Delete: 'Delete', Backspace: 'Backspace',
  Period: '.', Comma: ',', Slash: '/', Backslash: '\\', Minus: '-', Equal: '=', BracketLeft: '[', BracketRight: ']', Backquote: '`',
  Quote: "'", Semicolon: ';', ArrowUp: 'Up', ArrowDown: 'Down', ArrowLeft: 'Left', ArrowRight: 'Right', Home: 'Home', End: 'End',
  PageUp: 'PageUp', PageDown: 'PageDown', Insert: 'Insert', NumpadAdd: 'Numpad +', NumpadSubtract: 'Numpad -',
  NumpadMultiply: 'Numpad *', NumpadDivide: 'Numpad /', NumpadDecimal: 'Numpad .',
};

export function keyName(e) {
  const c = e.code;
  if (/^Key[A-Z]$/.test(c)) return c.slice(3);
  if (/^Digit\d$/.test(c)) return c.slice(5);
  if (/^Numpad\d$/.test(c)) return 'Numpad ' + c.slice(6);
  if (/^F\d+$/.test(c)) return c;
  return NAMED[c] || e.key;
}

export function comboFromEvent(e) {
  if (['Control', 'Shift', 'Alt', 'Meta'].includes(e.key)) return null;      // modifiers alone are not a combo
  const mods = [];
  if (e.ctrlKey || e.metaKey) mods.push('Ctrl');
  if (e.altKey) mods.push('Alt');
  if (e.shiftKey) mods.push('Shift');
  return [...mods, keyName(e)].join('+');
}

export const norm = s => s.split('+').map(x => x.trim().toLowerCase()).sort().join('+');

// Laptop keyboards have no numpad. Blender's "Emulate Numpad" covers the digits (number row); the rest of the numpad keys
// have an obvious stand-in on a laptop, so those count too (a US layout types + as Shift+= and * as Shift+8).
const LAPTOP = { '.': ['.'], '/': ['/'], '-': ['-'], '+': ['Shift+='], '*': ['Shift+8'] };

// Every way of writing the answer that counts: "Shift+A or Ctrl+Space" -> two; "Ctrl+Numpad 1" also "Ctrl+1".
export function alternatives(expected) {
  const out = [];
  for (const alt of expected.split(/\s+or\s+/i)) {
    out.push(alt);
    const m = /^(.*?)Numpad (\S)$/.exec(alt);
    if (m) for (const k of /\d/.test(m[2]) ? [m[2]] : LAPTOP[m[2]] || []) out.push(m[1] + k);
  }
  return out;
}

export function matches(expected, got) {
  // '+' inside key names ("Numpad +") is kept intact by swapping it for a word while comparing
  const fix = s => s.replace('Numpad +', 'Numpad_plus');
  const g = norm(fix(got));
  return alternatives(expected).some(alt => norm(fix(alt)) === g);
}

// The stand-ins a laptop user could press instead of a numpad key, for a hint line ([] when the card has no numpad key).
export function laptopAlternatives(expected) {
  const given = expected.split(/\s+or\s+/i);
  return alternatives(expected).filter(a => !given.includes(a));
}

// "G G" means press G, then G again. Returns the steps, or null for an ordinary single combo.
export function seqOf(expected) {
  if (/\sor\s/i.test(expected) || /Numpad/.test(expected)) return null;
  const t = expected.trim().split(/\s+/);
  return t.length > 1 ? t : null;
}

// Feed one pressed combo to a card. 'ok' = card done, 'more' = a sequence wants more presses, 'wrong'.
// `state` is a {step: 0} object owned by the caller, reset for every card.
export function judge(expected, pressed, state) {
  const seq = seqOf(expected);
  if (!seq) return matches(expected, pressed) ? 'ok' : 'wrong';
  if (matches(seq[state.step], pressed)) {
    if (++state.step < seq.length) return 'more';
    state.step = 0;
    return 'ok';
  }
  state.step = 0;
  return 'wrong';
}

// Hear the keys pressed inside Blender (the add-on relays them while a drill is open), so a drill can be answered with Blender
// focused and nobody has to click back and forth between the two windows. Keeps asking the add-on to watch until stop() is
// called or `alive()` turns false (the drill left the page); the add-on also stops by itself if the asking stops.
// swallow: Blender does not act on the keys (a quiz round: no menus opening, no renders starting). That is only kept up while
// keys keep arriving: after 45 s of silence it goes back to passing keys through, so Blender can never stay locked.
export function watchBlender(onCombo, alive = () => true, { swallow = false } = {}) {
  let last = Date.now(), swallowing = swallow;
  const off = on('key', m => { last = Date.now(); swallowing = swallow; onCombo(m.combo); });
  const ping = () => {
    if (!alive()) return stop();
    if (!(S.bridge && S.bridge.connected)) return;                  // nothing to listen to
    if (swallow && Date.now() - last > 45000) swallowing = false;
    api('bridge/command', { cmd: 'keywatch', args: { on: true, ttl: 12, swallow: swallowing } }).catch(() => {});
  };
  const iv = setInterval(ping, 4000);
  function stop() { clearInterval(iv); off(); api('bridge/command', { cmd: 'keywatch', args: { on: false } }).catch(() => {}); }
  ping();
  return stop;
}

// Browsers keep a few combos for themselves. Cards using them can't be drilled by pressing.
export const RESERVED = /^(ctrl\+(n|t|w|tab|shift\+(n|t|w))|ctrl\+shift\+tab|alt\+f4|f5|f11|f12)$/i;

const heldMods = e => [e.ctrlKey || e.metaKey ? 'Ctrl' : '', e.altKey ? 'Alt' : '', e.shiftKey ? 'Shift' : ''].filter(Boolean);

// Take over the keyboard: handler(combo, event) for every real combo; onHeld(['Shift', ...]) whenever the held modifiers change,
// so the page can show that keys are arriving. Alt on its own is swallowed too (Firefox would open its menu bar).
export function capture(handler, onHeld) {
  const down = e => {
    e.preventDefault(); e.stopPropagation();
    const c = comboFromEvent(e);
    if (!c) { onHeld && onHeld(heldMods(e)); return; }
    handler(c, e);
  };
  const up = e => {
    if (['Control', 'Shift', 'Alt', 'Meta'].includes(e.key)) { e.preventDefault(); onHeld && onHeld(heldMods(e)); }
  };
  addEventListener('keydown', down, true);
  addEventListener('keyup', up, true);
  return () => { removeEventListener('keydown', down, true); removeEventListener('keyup', up, true); };
}
