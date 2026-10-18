// keys.js - turn a browser KeyboardEvent into Blender-style combo text ("Ctrl+Shift+A") and compare combos.
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
export function matches(expected, got) {
  // "Shift+A or Ctrl+Space" -> any alternative; '+' inside names ("Numpad +") is kept intact.
  // "Numpad 1" also accepts the number row key: that is what Blender's Emulate Numpad setting does for laptops.
  const alts = expected.split(/\s+or\s+/i);
  for (const a of [...alts]) { const m = /^Numpad ([\d.])$/.exec(a); if (m) alts.push(m[1]); }
  return alts.some(alt => {
    const a = alt.replace('Numpad +', 'Numpad_plus');
    return norm(a) === norm(got.replace('Numpad +', 'Numpad_plus'));
  });
}

// Browsers keep a few combos for themselves. Cards using them can't be drilled by pressing.
export const RESERVED = /^(ctrl\+(n|t|w|tab|shift\+(n|t|w))|ctrl\+shift\+tab|alt\+f4|f5|f11|f12)$/i;
export function capture(handler) {
  const fn = e => {
    const c = comboFromEvent(e);
    if (!c) return;
    e.preventDefault(); e.stopPropagation();
    handler(c, e);
  };
  addEventListener('keydown', fn, true);
  return () => removeEventListener('keydown', fn, true);
}
