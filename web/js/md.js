// md.js - the small markdown subset lessons use: headings, lists, code, tables, quotes, [[Key]] caps, images.
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

export function keycaps(k) {
  return k.split(/\s*\+\s*(?=\S)/).map(x => `<kbd>${esc(x.trim())}</kbd>`).join('+');
}

export function inline(s) {
  const codes = [];
  s = s.replace(/`([^`]+)`/g, (_, c) => { codes.push(c); return '\u0000' + (codes.length - 1) + '\u0000'; });
  s = esc(s);
  s = s.replace(/\[\[([^\]]+)\]\]/g, (_, k) => keycaps(k));
  s = s.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_, a, src) => `<img alt="${a}" src="${src.startsWith('img:') ? '/cimg/' + src.slice(4) : src}">`);
  s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  s = s.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>').replace(/(^|[^*\w])\*([^*\n]+)\*/g, '$1<i>$2</i>').replace(/~~([^~]+)~~/g, '<s>$1</s>');
  return s.replace(/\u0000(\d+)\u0000/g, (_, i) => '<code>' + esc(codes[i]) + '</code>');
}

const isBlockStart = l => /^(#{1,4}\s|```|>\s?|\s*[-*]\s+|\s*\d+\.\s+|---+\s*$|\|)/.test(l);

export function md(src) {
  const lines = String(src || '').replace(/\r/g, '').split('\n');
  const out = [];
  let i = 0;
  while (i < lines.length) {
    const l = lines[i];
    if (!l.trim()) { i++; continue; }
    let m;
    if (/^```/.test(l)) {
      const buf = [];
      i++;
      while (i < lines.length && !/^```/.test(lines[i])) buf.push(lines[i++]);
      i++;
      out.push(`<pre><code>${esc(buf.join('\n'))}</code></pre>`);
    } else if ((m = /^(#{1,4})\s+(.*)$/.exec(l))) {
      out.push(`<h${m[1].length + 1 > 4 ? 4 : m[1].length + 1}>${inline(m[2])}</h${m[1].length + 1 > 4 ? 4 : m[1].length + 1}>`); i++;
    } else if (/^---+\s*$/.test(l)) { out.push('<hr>'); i++; }
    else if (/^>\s?/.test(l)) {
      const buf = [];
      while (i < lines.length && /^>\s?/.test(lines[i])) buf.push(lines[i++].replace(/^>\s?/, ''));
      out.push(`<blockquote>${md(buf.join('\n'))}</blockquote>`);
    } else if (/^\|/.test(l) && /^\|?[\s:|-]+\|[\s:|-]*$/.test(lines[i + 1] || '')) {
      const row = r => r.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim());
      const head = row(l);
      i += 2;
      const body = [];
      while (i < lines.length && /^\|/.test(lines[i])) body.push(row(lines[i++]));
      out.push('<table><thead><tr>' + head.map(c => `<th>${inline(c)}</th>`).join('') + '</tr></thead><tbody>' +
        body.map(r => '<tr>' + r.map(c => `<td>${inline(c)}</td>`).join('') + '</tr>').join('') + '</tbody></table>');
    } else if (/^\s*([-*]|\d+\.)\s+/.test(l)) {
      const ordered = /^\s*\d+\./.test(l);
      const items = [];
      while (i < lines.length && (/^(\s*)([-*]|\d+\.)\s+/.test(lines[i]) || (/^\s{2,}\S/.test(lines[i]) && items.length))) {
        const ln = lines[i];
        if (/^([-*]|\d+\.)\s+/.test(ln)) items.push([ln.replace(/^([-*]|\d+\.)\s+/, '')]);
        else items[items.length - 1].push(ln.replace(/^ {2,4}/, ''));
        i++;
      }
      out.push(`<${ordered ? 'ol' : 'ul'}>` + items.map(it => '<li>' + (it.length > 1 ? md(it.join('\n')).replace(/^<p>|<\/p>$/g, '') : inline(it[0])) + '</li>').join('') + `</${ordered ? 'ol' : 'ul'}>`);
    } else if (/^ {4,}\S/.test(l)) {                                  // indented code block
      const buf = [];
      while (i < lines.length && (/^ {4,}\S/.test(lines[i]) || (!lines[i].trim() && /^ {4,}\S/.test(lines[i + 1] || '')))) buf.push(lines[i++].replace(/^ {4}/, ''));
      out.push(`<pre><code>${esc(buf.join('\n'))}</code></pre>`);
    } else {
      const buf = [];
      while (i < lines.length && lines[i].trim() && !(buf.length && isBlockStart(lines[i]))) buf.push(lines[i++]);
      out.push('<p>' + inline(buf.join(' ').replace(/ {2,}/g, ' ')) + '</p>');
    }
  }
  return out.join('\n');
}
