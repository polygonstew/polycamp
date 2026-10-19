"""speech.py - turn a lesson into a spoken script, plus the Blender highlight cues that go with it.

A script is a list of *segments* (a paragraph, a task, a note...). Each segment is a list of *chunks*
(one sentence each, with the pause that follows it). The voice engine renders a segment to one audio
file and reports where every chunk starts and ends, so a cue attached to a sentence can fire exactly
when that sentence is spoken.

Nothing here needs more than the standard library. The wording rules are versioned (VERSION): changing
them changes every cache key, so old audio is simply never asked for again.
"""
import hashlib
import json
import re

VERSION = 4
MAX_WORDS = 85                      # a segment longer than this is split at a sentence boundary
ON_SCREEN = "the code on screen"

# ------------------------------------------------------------------ markdown units (mirrors web/js/md.js)
BLOCK_START = re.compile(r"^(#{1,4}\s|```|>\s?|\s*[-*]\s+|\s*\d+\.\s+|---+\s*$|\|)")


def md_units(src):
    """Split markdown into the same top-level units md.js turns into DOM elements, in the same order,
    so unit N here is child N of the rendered .md element."""
    lines = str(src or "").replace("\r", "").split("\n")
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if ln.startswith("```"):
            buf = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append({"k": "code", "text": "\n".join(buf)})
        elif m:
            out.append({"k": "h", "text": m.group(2)})
            i += 1
        elif re.match(r"^---+\s*$", ln):
            out.append({"k": "hr"})
            i += 1
        elif re.match(r"^>\s?", ln):
            buf = []
            while i < len(lines) and re.match(r"^>\s?", lines[i]):
                buf.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            out.append({"k": "quote", "text": " ".join(b.strip() for b in buf)})
        elif ln.startswith("|") and re.match(r"^\|?[\s:|-]+\|[\s:|-]*$", lines[i + 1] if i + 1 < len(lines) else ""):
            def row(r):
                return [c.strip() for c in re.sub(r"^\||\|$", "", r.strip()).split("|")]
            head = row(ln)
            i += 2
            body = []
            while i < len(lines) and lines[i].startswith("|"):
                body.append(row(lines[i]))
                i += 1
            out.append({"k": "table", "head": head, "rows": body})
        elif re.match(r"^\s*([-*]|\d+\.)\s+", ln):
            ordered = bool(re.match(r"^\s*\d+\.", ln))
            items = []
            while i < len(lines) and (re.match(r"^(\s*)([-*]|\d+\.)\s+", lines[i]) or (re.match(r"^\s{2,}\S", lines[i]) and items)):
                cur = lines[i]
                if re.match(r"^([-*]|\d+\.)\s+", cur):
                    items.append([re.sub(r"^([-*]|\d+\.)\s+", "", cur)])
                elif items:
                    items[-1].append(cur.strip())
                i += 1
            out.append({"k": "ol" if ordered else "ul", "items": [" ".join(it) for it in items]})
        elif re.match(r"^ {4,}\S", ln):                                  # indented code block
            buf = []
            while i < len(lines) and (re.match(r"^ {4,}\S", lines[i]) or (not lines[i].strip() and re.match(r"^ {4,}\S", lines[i + 1] if i + 1 < len(lines) else ""))):
                buf.append(lines[i][4:])
                i += 1
            out.append({"k": "code", "text": "\n".join(buf)})
        else:
            buf = []
            while i < len(lines) and lines[i].strip() and not (buf and BLOCK_START.match(lines[i])):
                buf.append(lines[i])
                i += 1
            out.append({"k": "p", "text": " ".join(buf)})
    return out


# ------------------------------------------------------------------ words
KEY_WORD = {
    "ctrl": "Control", "control": "Control", "alt": "Alt", "shift": "Shift", "cmd": "Command", "tab": "Tab",
    "esc": "Escape", "enter": "Enter", "return": "Enter", "space": "Space", "del": "Delete", "delete": "Delete",
    "backspace": "Backspace", "lmb": "left click", "rmb": "right click", "mmb": "middle click",
    "wheel": "mouse wheel", "scroll": "scroll wheel", "up": "up arrow", "down": "down arrow", "left": "left arrow",
    "right": "right arrow", "home": "Home", "end": "End", "pgup": "page up", "pgdn": "page down",
    "~": "tilde", "`": "backtick", "/": "slash", ",": "comma", ".": "period", "-": "minus", "+": "plus",
    "=": "equals", "[": "left bracket", "]": "right bracket", "\\": "backslash", "'": "quote", ";": "semicolon",
    "drag": "drag", "click": "click", "dblclick": "double click",
}

ACRONYM = {
    "UVs": "U Vees", "UV": "U V", "PBR": "P B R", "HDRI": "H D R I", "HDR": "H D R", "GPU": "G P U", "CPU": "C P U",
    "RGB": "R G B", "RGBA": "R G B A", "SSS": "S S S", "AO": "A O", "BSDF": "B S D F", "FPS": "F P S",
    "PNG": "P N G", "JPG": "J P G", "JPEG": "J peg", "EXR": "E X R", "GLB": "G L B", "GLTF": "G L T F",
    "glTF": "G L T F", "FBX": "F B X", "OBJ": "O B J", "STL": "S T L", "USD": "U S D", "SVG": "S V G",
    "API": "A P I", "GUI": "G U I", "UI": "U I", "HUD": "H U D", "LMB": "left mouse button",
    "RMB": "right mouse button", "MMB": "middle mouse button", "FOV": "F O V", "DOF": "depth of field",
    "IK": "I K", "FK": "F K", "NLA": "N L A", "VSE": "V S E", "XYZ": "X Y Z", "XY": "X Y", "XZ": "X Z",
    "YZ": "Y Z", "XP": "X P", "IOR": "I O R", "RAM": "ram", "AI": "A I", "PC": "P C", "LCM": "L C M",
    "FFMPEG": "F F mpeg", "MPEG": "M peg", "SDF": "S D F", "UDIM": "you dim", "OSL": "O S L", "NPR": "N P R",
    "GB": "gigabytes", "MB": "megabytes", "KB": "kilobytes", "OK": "okay", "ID": "I D", "IDs": "I Ds",
    "EEVEE": "Eevee", "CYCLES": "Cycles", "ComfyUI": "Comfy U I", "LoRA": "Laura", "Godot": "Godo",
    "matcap": "mat cap", "ngon": "n-gon", "ngons": "n-gons", "Numpad": "numpad", "numpad": "numpad",
    "Mixamo": "Mixamo", "Polycamp": "Polly camp", "Z-up": "Z up", "UV-unwrap": "U V unwrap",
}
EXT = {"png": "P N G", "jpg": "J P G", "jpeg": "J peg", "exr": "E X R", "glb": "G L B", "gltf": "G L T F",
       "fbx": "F B X", "obj": "O B J", "mp4": "M P 4", "svg": "S V G", "py": "P Y", "json": "jason", "blend": "blend",
       "hdr": "H D R", "tif": "tiff", "tiff": "tiff", "webp": "web P", "wav": "wave", "ogg": "ogg"}
ACRONYM_RE = re.compile(r"(?<![\w-])(" + "|".join(sorted(map(re.escape, ACRONYM), key=len, reverse=True)) + r")(?![\w-])")

UNITS = [  # (regex after a number, spoken)
    (r"mm", "millimetres"), (r"cm", "centimetres"), (r"km", "kilometres"), (r"m", "metres"),
    (r"px", "pixels"), (r"fps", "frames per second"), (r"spp", "samples per pixel"), (r"ms", "milliseconds"),
    (r"min", "minutes"), (r"sec", "seconds"), (r"kg", "kilograms"), (r"GHz", "gigahertz"), (r"Hz", "hertz"),
    (r"K", "K"),
]
UNIT_RE = re.compile(r"(?<=\d)\s?(" + "|".join(u for u, _ in UNITS[:-1]) + r")\b(\s+[a-z]+)?")
UNIT_MAP = dict(UNITS)
UNIT_ONE = {"metres": "metre", "centimetres": "centimetre", "millimetres": "millimetre", "kilometres": "kilometre",
            "pixels": "pixel", "minutes": "minute", "seconds": "second", "kilograms": "kilogram"}
UNIT_STAY = {"along", "apart", "away", "from", "above", "below", "high", "tall", "wide", "long", "per", "of", "in",
             "to", "and", "or", "on", "at", "up", "down", "by", "with", "for", "the", "a", "is", "are", "so", "then",
             "if", "when", "before", "after", "off", "out", "deep", "thick", "across", "over", "under", "between"}


def _unit(m):
    word, nxt = UNIT_MAP[m.group(1)], m.group(2) or ""
    if nxt and nxt.strip() not in UNIT_STAY and word in UNIT_ONE:      # "a 2 m cube" reads better as "metre"
        word = UNIT_ONE[word]
    return " " + word + nxt
ORD = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth"]

TOKEN = re.compile(r"\[\[([^\]]+)\]\]|`([^`]+)`")


def speak_key(k):
    k = k.strip()
    parts = [p for p in re.split(r"\s*\+\s*(?=\S)", k) if p]
    words = []
    for p in parts:
        low = p.lower()
        if low in KEY_WORD:
            words.append(KEY_WORD[low])
        elif re.fullmatch(r"numpad\s*(.+)", low):
            v = re.fullmatch(r"numpad\s*(.+)", low).group(1)
            words.append("numpad " + KEY_WORD.get(v, v))
        elif re.fullmatch(r"f\d{1,2}", low):
            words.append("F " + low[1:])
        else:
            words.append(p)
    return " ".join(words)


def speak_code(c):
    c = c.strip()
    if not c:
        return ""
    if re.fullmatch(r"-?\d+(\.\d+)?", c):
        return c.replace("-", "minus ", 1)
    if c in KEY_WORD:
        return KEY_WORD[c]
    if len(c) > 30 or re.search(r"[(){}\[\]$|\\]|--|;", c) or c.count("\n"):
        return ON_SCREEN
    m = re.fullmatch(r"\.?([\w-]+)\.(\w{2,5})", c)
    if m and m.group(2).lower() in EXT:                                  # a file name
        return "%s dot %s" % (m.group(1).replace("_", " ").replace("-", " "), EXT[m.group(2).lower()])
    if c.startswith("."):
        c = "dot " + c[1:]
    c = c.replace("~/", "home slash ").replace("/", " slash ")
    c = re.sub(r"(?<=[A-Za-z_])\.(?=[A-Za-z])", " dot ", c)
    c = c.replace("_", " ").replace("=", " equals ").replace("*", " times ")
    return re.sub(r"\s+", " ", c).strip()


def _runs(s):
    """Replace [[Key]] caps and `code` spans by speech. Neighbouring ones (a key sequence) are joined with
    commas so they come out as 'G, X, 3, Enter' instead of a run-on."""
    pieces, pos = [], 0
    for m in TOKEN.finditer(s):
        if m.start() > pos:
            pieces.append(("t", s[pos:m.start()]))
        pieces.append(("k", speak_key(m.group(1))) if m.group(1) is not None else ("c", speak_code(m.group(2))))
        pos = m.end()
    pieces.append(("t", s[pos:]))
    out, i = [], 0
    while i < len(pieces):
        kind, val = pieces[i]
        if kind == "t":
            out.append(val)
            i += 1
            continue
        run, j = [val], i
        while j + 2 < len(pieces) and pieces[j + 1][0] == "t" and not pieces[j + 1][1].strip() and pieces[j + 2][0] in "kc" \
                and pieces[j + 2][1] != ON_SCREEN and val != ON_SCREEN:
            run.append(pieces[j + 2][1])
            j += 2
        text = ", ".join(run)
        nxt = pieces[j + 1][1] if j + 1 < len(pieces) else ""
        if len(run) > 1 and re.match(r"\s+[A-Za-z]", nxt):
            text += ","
        out.append(text)
        i = j + 1
    return "".join(out)


def clean(s):
    """Markdown-ish lesson text -> something a voice can read."""
    s = re.sub(r"^\[[ xX]\]\s*", "", s.strip())                                  # task-list boxes
    s = s.replace("\\*", "\u0003")                                               # an escaped * is not emphasis
    s = _runs(s)
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"(^|[^*\w])\*([^*\n]+)\*", r"\1\2", s)
    s = re.sub(r"~~([^~]+)~~", r"\1", s)
    s = re.sub(r"(\w)\.?\u0003", r"\1 something", s).replace("\u0003", " star ")   # Rock.* -> "Rock something"
    s = re.sub(r"\\([_`\[\]\\])", r"\1", s)
    s = re.sub(r"(?<=\w)_(?=\w)", " ", s)                                       # Cabin_Walls -> Cabin Walls
    s = re.sub(r"(?<=\w)(?:\.\.\.|…)(?=[,;)])", "", s)
    s = re.sub(r"(?:\.\.\.|…)(?=\s)", ",", s)
    s = re.sub(r"(?:\.\.\.|…)$", ".", s)
    s = re.sub(r"\b(?:Ctrl|Alt|Shift|Cmd)(?:\+[A-Za-z0-9]+)+", lambda m: speak_key(m.group(0)), s)
    s = re.sub(r"\b([A-Z])/([A-Z])(?:/([A-Z]))?\b", lambda m: ", ".join(g for g in m.groups() if g), s)
    s = re.sub(r"\be\.g\.,?", "for example,", s)
    s = re.sub(r"\bi\.e\.,?", "that is,", s)
    s = re.sub(r"\betc\.", "and so on.", s)
    s = re.sub(r"\bvs\.?", "versus", s)
    s = re.sub(r"\((-?[\d.]+(?:\s*,\s*-?[\d.]+)+)\)", r"\1", s)               # (3, 0, 0) -> 3, 0, 0
    s = re.sub(r"(?<=\d)\s?[×x]\s?(?=\d)", " by ", s)
    s = s.replace("×", " times ")
    s = re.sub(r"(?<=\d)\s?°", " degrees", s).replace("°", " degrees")
    s = re.sub(r"(?<=\d)\s?%", " percent", s)
    s = UNIT_RE.sub(_unit, s)
    s = re.sub(r"(?<=\d)\+(?!\d)", " and newer", s)
    s = re.sub(r"(^|[\s(,])[-−](?=\d)", r"\1minus ", s)
    s = re.sub(r"\+(?=\d)", "plus ", s)
    s = re.sub(r"~(?=\d)", "about ", s)
    s = s.replace("≈", " about ").replace("≥", " at least ").replace("≤", " at most ").replace("±", " plus or minus ")
    s = re.sub(r"(?<=\d)[–-](?=\d)", " to ", s)
    s = re.sub(r"\s*(→|->|►|▸|›|\s>\s)\s*", ", ", s)
    s = re.sub(r"\s=\s?|\s?=\s", " equals ", s)
    s = re.sub(r"\s+[–—]\s+|\s*—\s*", ", ", s)
    s = re.sub(r"(?<=[a-z])/(?=[a-z])", " or ", s)
    s = s.replace("&", " and ").replace("·", ", ").replace("²", " squared").replace("−", "minus ")
    s = re.sub(r"[─│┘┐└┌┬┴┼▲▼■□●○◆◇▶◀✓✔✗✘★☆]", "", s)
    s = re.sub(r"(?<=\w)\+(?=\w)", " plus ", s)
    s = ACRONYM_RE.sub(lambda m: ACRONYM[m.group(1)], s)
    s = re.sub(r"\s*\(([^()]+)\)", r", \1,", s)                                 # asides become phrases
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    s = re.sub(r",\s*([.!?:;])", r"\1", s)
    s = re.sub(r",(\s*,)+", ",", s)
    s = re.sub(r"^[\s,]+", "", s)
    return re.sub(r"\s+", " ", s).strip(" ,")


def sentences(raw):
    """Split raw markdown into sentences without breaking inside code spans or key caps."""
    held = []

    def hold(m):
        held.append(m.group(0))
        return "\u0001%d\u0001" % (len(held) - 1)
    s = TOKEN.sub(hold, raw)
    s = re.sub(r"\be\.g\.", "e\u0002g\u0002", s)
    s = re.sub(r"\bi\.e\.", "i\u0002e\u0002", s)
    s = re.sub(r"\betc\.(?=\s+[a-z])", "etc\u0002", s)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\u0001\"“(\d])", s)
    out = []
    for p in parts:
        p = p.replace("\u0002", ".")
        p = re.sub("\u0001(\\d+)\u0001", lambda m: held[int(m.group(1))], p).strip()
        if p:
            out.append(p)
    return out


def _split_long(text, limit=240):
    if len(text) <= limit:
        return [text]
    mid = len(text) // 2
    cuts = [m.end() for m in re.finditer(r"[,;:] ", text)]
    if not cuts:
        return [text]
    at = min(cuts, key=lambda c: abs(c - mid))
    return _split_long(text[:at].strip(), limit) + _split_long(text[at:].strip(), limit)


def words(text):
    return len(re.findall(r"[\w']+", text))


# ------------------------------------------------------------------ highlight cues
SPACE_WORDS = [  # regex on lower-case plain text -> (space, label)
    (r"\boutliner\b", ("OUTLINER", "Outliner")),
    (r"\bproperties (?:editor|panel|window)\b", ("PROPERTIES", "Properties editor")),
    (r"\btimeline\b", ("TIMELINE", "Timeline")),
    (r"\bdope ?sheet\b", ("DOPESHEET_EDITOR", "Dope Sheet")),
    (r"\bgraph editor\b", ("GRAPH_EDITOR", "Graph Editor")),
    (r"\b(?:shader|geometry node|compositor|node) editor\b|\bcompositor\b", ("NODE_EDITOR", "Node editor")),
    (r"\buv editor\b|\bimage editor\b", ("IMAGE_EDITOR", "Image / UV editor")),
    (r"\bvideo sequencer\b|\bsequencer\b", ("SEQUENCE_EDITOR", "Video Sequencer")),
    (r"\btext editor\b", ("TEXT_EDITOR", "Text editor")),
    (r"\bspreadsheet\b", ("SPREADSHEET", "Spreadsheet")),
    (r"\b3d viewport\b|\bthe viewport\b|\bviewport\b", ("VIEW_3D", "3D Viewport")),
]
PROPS_TABS = [
    (r"\bmodifiers? (?:tab|panel|properties)\b|\bwrench\b|\badd modifier\b", ("MODIFIERS", "Modifiers tab")),
    (r"\bmaterials? (?:tab|properties|panel)\b", ("MATERIAL", "Material tab")),
    (r"\brender (?:properties|tab|settings)\b", ("RENDER", "Render tab")),
    (r"\boutput (?:properties|tab|settings)\b", ("OUTPUT", "Output tab")),
    (r"\bworld (?:properties|tab)\b", ("WORLD", "World tab")),
    (r"\bobject (?:properties|tab)\b", ("OBJECT", "Object tab")),
    (r"\b(?:object )?data (?:properties|tab)\b|\bmesh data\b", ("DATA", "Data tab")),
    (r"\bphysics (?:tab|properties)\b", ("PHYSICS", "Physics tab")),
    (r"\bconstraints? (?:tab|properties)\b", ("CONSTRAINTS", "Constraints tab")),
    (r"\bparticles? (?:tab|properties)\b", ("PARTICLES", "Particles tab")),
    (r"\bscene (?:properties|tab)\b", ("SCENE", "Scene tab")),
    (r"\bview layer (?:properties|tab)\b", ("VIEW_LAYER", "View Layer tab")),
    (r"\btexture (?:properties|tab)\b", ("TEXTURE", "Texture tab")),
]
OBJ_WORDS = r"cube|camera|light|lamp|plane|sphere|cylinder|cone|torus|monkey|suzanne|empty|armature|curve"
CUE_SPACES = {"viewport": "VIEW_3D", "outliner": "OUTLINER", "props": "PROPERTIES", "properties": "PROPERTIES",
              "timeline": "TIMELINE", "dopesheet": "DOPESHEET_EDITOR", "graph": "GRAPH_EDITOR", "nodes": "NODE_EDITOR",
              "shader": "NODE_EDITOR", "uv": "IMAGE_EDITOR", "image": "IMAGE_EDITOR", "sequencer": "SEQUENCE_EDITOR",
              "text": "TEXT_EDITOR", "spreadsheet": "SPREADSHEET"}


def _key_seq(raw):
    """The keys named in a sentence, in order: [[caps]] and the `typed values` between them."""
    seq = []
    for m in TOKEN.finditer(raw):
        if m.group(1) is not None:
            seq.append(m.group(1).strip())
        elif re.fullmatch(r"-?\d+(\.\d+)?", m.group(2).strip()) and seq:
            seq.append(m.group(2).strip())
    return seq[:7]


def derive_cues(raw):
    """What to point at in Blender while this sentence is spoken. Each cue is a small dict the add-on draws."""
    cues = []
    seq = _key_seq(raw)
    if seq:
        cues.append({"t": "keys", "seq": seq})
    lt = re.sub(r"[`*_\[\]]", "", raw).lower()
    m = re.search(r"\b(?:n panel|n-panel|sidebar|side bar)\b", lt)
    if m:
        tab = re.search(r"\b(item|tool|view|edit)\b", lt[m.end():m.end() + 40])
        cue = {"t": "area", "space": "VIEW_3D", "region": "UI", "label": "Sidebar (N)"}
        if tab:
            cue["tab"] = tab.group(1).capitalize()
            cue["label"] = "Sidebar > " + cue["tab"]
        cues.append(cue)
    if re.search(r"\b(?:toolbar|tool shelf)\b", lt):
        cues.append({"t": "area", "space": "VIEW_3D", "region": "TOOLS", "label": "Toolbar"})
    props_hit = False
    for rx, (tab, label) in PROPS_TABS:
        if re.search(rx, lt):
            cues.append({"t": "area", "space": "PROPERTIES", "region": "WINDOW", "label": label, "tab": tab})
            props_hit = True
            break
    for rx, (space, label) in SPACE_WORDS:
        if space == "PROPERTIES" and props_hit:
            continue
        if re.search(rx, lt):
            cues.append({"t": "area", "space": space, "region": "WINDOW", "label": label})
            if space == "VIEW_3D" and cues and any(c.get("region") == "UI" for c in cues):
                cues.pop()                                    # "sidebar of the viewport": the sidebar is enough
    if re.search(r"\b3d cursor\b", lt):
        cues.append({"t": "cursor"})
    if re.search(r"\bworld origin\b", lt):
        cues.append({"t": "world_origin"})
    elif re.search(r"\b(?:object'?s? origin|origin point|set origin|origin dot)\b", lt):
        cues.append({"t": "origin"})
    if re.search(r"\b(?:navigation |axis |view )?gizmo\b", lt):
        cues.append({"t": "gizmo"})
    if re.search(r"\b(?:selected objects?|the selection|what you selected)\b", lt):
        cues.append({"t": "obj", "sel": True})
    elif re.search(r"\bactive object\b", lt):
        cues.append({"t": "obj", "active": True})
    else:
        names = []
        for mm in re.finditer(r"\b(?:the|your|a|that)\s+(" + OBJ_WORDS + r")\b", lt):
            if mm.group(1) not in names:
                names.append(mm.group(1))
        for n in names[:2]:
            cues.append({"t": "obj", "m": n})
    seen, out = set(), []
    for c in cues:
        k = json.dumps(c, sort_keys=True)
        if k not in seen:
            seen.add(k)
            out.append(c)
    return out[:4]


def parse_cue_spec(spec):
    """The `cue:` line of a task, e.g. `cue: outliner, obj:Cube, sidebar:Item, keys:Ctrl+A`."""
    cues = []
    for tok in [t.strip() for t in spec.split(",") if t.strip()]:
        name, _, arg = tok.partition(":")
        name, arg = name.strip().lower(), arg.strip()
        if name == "sidebar":
            c = {"t": "area", "space": "VIEW_3D", "region": "UI", "label": "Sidebar (N)"}
            if arg:
                c.update(tab=arg.capitalize(), label="Sidebar > " + arg.capitalize())
            cues.append(c)
        elif name == "toolbar":
            cues.append({"t": "area", "space": "VIEW_3D", "region": "TOOLS", "label": "Toolbar"})
        elif name == "header":
            cues.append({"t": "area", "space": "VIEW_3D", "region": "HEADER", "label": "Header"})
        elif name in ("props", "properties") and arg:
            cues.append({"t": "area", "space": "PROPERTIES", "region": "WINDOW", "label": arg.capitalize() + " tab", "tab": arg.upper()})
        elif name in CUE_SPACES:
            label = {"viewport": "3D Viewport"}.get(name, name.capitalize())
            cues.append({"t": "area", "space": CUE_SPACES[name], "region": "WINDOW", "label": label})
        elif name == "obj":
            cues.append({"t": "obj", "m": arg.lower()})
        elif name == "sel":
            cues.append({"t": "obj", "sel": True})
        elif name == "active":
            cues.append({"t": "obj", "active": True})
        elif name in ("cursor", "origin", "gizmo", "world_origin"):
            cues.append({"t": name})
        elif name == "keys" and arg:
            cues.append({"t": "keys", "seq": arg.split()[:7]})
    return cues


# ------------------------------------------------------------------ script building
def _spec_matches(spec, major):
    if not spec or spec == "any":
        return True
    for tok in (t.strip() for t in spec.split(",")):
        m = re.fullmatch(r"(\d+)\+", tok)
        if m and major >= int(m.group(1)):
            return True
        m = re.fullmatch(r"(\d+)-(\d+)", tok)
        if m and int(m.group(1)) <= major <= int(m.group(2)):
            return True
        if tok.isdigit() and int(tok) == major:
            return True
    return False


def _spec_words(spec):
    if spec.endswith("+"):
        return "Blender %s and newer" % spec[:-1]
    if re.fullmatch(r"\d+-\d+", spec):
        return "Blender %s to %s" % tuple(spec.split("-"))
    return "Blender %s point x" % spec


def _unit_lines(u, first_ordinal=1):
    """A markdown unit -> [(raw sentence, pause)]."""
    k = u["k"]
    if k == "h":
        return [(u["text"].rstrip(".:") + ".", 0.65)]
    if k in ("p", "quote"):
        ss = sentences(u["text"])
        return [(s, 0.32) for s in ss[:-1]] + [(ss[-1], 0.45)] if ss else []
    if k in ("ul", "ol"):
        out = []
        for n, item in enumerate(u["items"], first_ordinal):
            ss = sentences(item)
            for j, s in enumerate(ss):
                if k == "ol" and j == 0:
                    s = "Step %d: %s" % (n, s) if len(u["items"]) > 1 else s
                out.append((s, 0.28 if j < len(ss) - 1 else 0.5))
        return out
    if k == "table":
        n_cols = len(u["head"])
        if len(u["rows"]) > 12:
            return [("There is a table of %d rows on screen." % len(u["rows"]), 0.5)]
        out = []
        for r in u["rows"]:
            cells = [c for c in r if c]
            out.append(((": " if n_cols > 2 else ", ").join(cells[:2]) + (", " + ", ".join(cells[2:]) if n_cols > 2 and len(cells) > 2 else "") + ".", 0.4))
        return out
    if k == "code":
        return [("Have a look at the code on screen.", 0.5)]
    return []


def _chunks(lines, cue_override=None, cues_on=True):
    ch = []
    for raw, pause in lines:
        text = clean(raw)
        if not re.search(r"\w", text):
            continue
        cues = derive_cues(raw) if cues_on else []
        for n, part in enumerate(_split_long(text)):
            ch.append({"t": part if re.search(r"[.!?:]$", part) else part + ".", "p": pause, "cues": cues if n == 0 else []})
    if cue_override and ch:
        ch[0]["cues"] = (cue_override + ch[0]["cues"])[:4]
    return ch


def _segments_from_chunks(chunks, **meta):
    """Cut a long run of chunks into segments of at most MAX_WORDS."""
    out, cur, w = [], [], 0
    for c in chunks:
        n = words(c["t"])
        if cur and w + n > MAX_WORDS:
            out.append(dict(meta, chunks=cur))
            cur, w = [], 0
        cur.append(c)
        w += n
    if cur:
        out.append(dict(meta, chunks=cur))
    return out


def lesson_segments(les, major, pos=None):
    """Plain segment dicts for a lesson, before voices/keys are attached. `les` is a lessons.Lesson;
    `pos` = {idx, total, world, next, next_id} for the opening and closing lines."""
    pos = pos or {}
    segs = []
    req = [b for b in les.blocks if b["t"] == "task" and not b.get("optional")]
    intro = []
    head = "Boss fight. " if les.boss and not les.title.lower().startswith("boss") else ""
    where = "Sheet %d of %d. " % (pos["idx"], pos["total"]) if pos.get("idx") else ""
    mins = "About %d minutes. " % les.minutes if les.minutes else ""
    intro.append((head + clean(les.title) + ".", 0.7))
    intro.append((where + mins, 0.4))
    if les.summary:
        intro.append((les.summary, 0.5))
    if les.keys:
        intro.append(("Keys for this one: " + ", ".join(speak_key(k) for k in les.keys) + ".", 0.5))
    segs.append({"kind": "intro", "label": "Intro", "b": None, "u": None, "task": None, "opt": False, "chunks": _chunks(intro)})
    if les.scene != "keep":
        segs.append({"kind": "setup", "label": "Scene setup", "b": None, "u": None, "task": None, "opt": False,
                     "chunks": _chunks([("This lesson starts from a prepared scene. Press Set up scene in Blender, in the lesson or in the Polycamp panel, before you begin.", 0.5)])})
    tn = 0
    for bi, b in enumerate(les.blocks):
        t = b["t"]
        if t == "md":
            units = md_units(b["text"])
            pending, start = [], None
            def flush_pending(upto):
                nonlocal pending, start
                if pending:
                    for s in _segments_from_chunks(_chunks(pending), kind="text", label=_label(pending[0][0]), b=bi, u=[start, upto], task=None, opt=False):
                        segs.append(s)
                pending, start = [], None
            for ui, u in enumerate(units):
                lines = _unit_lines(u)
                if u["k"] == "code":
                    flush_pending(ui - 1)
                    segs.append({"kind": "code", "label": "Code", "b": bi, "u": [ui, ui], "task": None, "opt": False, "chunks": _chunks(lines)})
                    continue
                if not lines:
                    continue
                if u["k"] == "h":
                    flush_pending(ui - 1)
                    pending, start = list(lines), ui
                    continue
                if start is None:
                    start = ui
                pending += lines
                flush_pending(ui)
            flush_pending(len(units) - 1)
        elif t == "task":
            tn += 1 if not b.get("optional") else 0
            lead = ("Stretch task: " if b.get("optional") else "Task %d of %d: " % (tn, len(req))) + b["title"]
            lines = [(lead.rstrip(".") + ".", 0.55)]
            for u in md_units(b["text"]):
                lines += _unit_lines(u)
            ch = _chunks(lines, parse_cue_spec(" , ".join(b["cue"])) if b.get("cue") else None)
            segs.append({"kind": "task", "label": ("Task %d: " % tn if not b.get("optional") else "Stretch: ") + _plain(b["title"]),
                         "b": bi, "u": None, "task": b["id"], "opt": bool(b.get("optional")), "chunks": ch})
        elif t == "cubby":
            lines = [(s, 0.4) for s in sentences(b["text"])]
            segs.append({"kind": "cubby", "label": "Cubby", "b": bi, "u": None, "task": None, "opt": True, "voice": "cubby", "chunks": _chunks(lines)})
        elif t == "note":
            lead = {"tip": "Tip.", "warn": "Careful.", "cpu": "CPU tip.", "info": "Note."}.get(b["kind"], "Note.")
            lines = [((lead + " " + b["title"].rstrip(".") + ".") if b.get("title") else lead, 0.45)]
            for u in md_units(b["text"]):
                lines += _unit_lines(u)
            segs.append({"kind": "note", "label": b.get("title") or lead.rstrip("."), "b": bi, "u": None, "task": None, "opt": False, "chunks": _chunks(lines)})
        elif t == "v":
            if _spec_matches(b["spec"], major):
                lines = [(_spec_words(b["spec"]) + ":", 0.4)]
                for u in md_units(b["text"]):
                    lines += _unit_lines(u)
                segs.append({"kind": "text", "label": _spec_words(b["spec"]), "b": bi, "u": None, "task": None, "opt": False, "chunks": _chunks(lines)})
        elif t == "reveal":
            lines = [(b["title"].rstrip(".") + ".", 0.5)]
            for u in md_units(b["text"]):
                lines += _unit_lines(u)
            segs.append({"kind": "extra", "label": b["title"], "b": bi, "u": None, "task": None, "opt": True, "chunks": _chunks(lines)})
        elif t == "goal":
            lines = [("Here is what you are building toward.", 0.45)]
            for u in md_units(b["text"]):
                lines += _unit_lines(u)
            segs.append({"kind": "text", "label": "The goal", "b": bi, "u": None, "task": None, "opt": False, "chunks": _chunks(lines)})
        elif t == "img":
            if b.get("caption"):
                segs.append({"kind": "extra", "label": "Figure", "b": bi, "u": None, "task": None, "opt": True,
                             "chunks": _chunks([("On screen: " + b["caption"], 0.4)])})
        elif t in ("quiz", "order", "match", "fill", "keys"):
            lines = [({"quiz": "Quick question.", "order": "Put these in order.", "match": "Match these up.",
                       "fill": "Fill in the blank.", "keys": "Name the shortcuts."}[t], 0.4)]
            for u in md_units(b.get("q", "")):
                lines += _unit_lines(u)
            if t == "quiz":
                lines += [("%s: %s" % (ORD[n].capitalize() if n < len(ORD) else "Next", o), 0.35) for n, o in enumerate(b["options"])]
            elif t == "order":
                lines.append(("The steps are on screen: " + "; ".join(b["items"]) + ".", 0.4))
            elif t == "match":
                lines.append(("The items are on screen: " + "; ".join(b["left"]) + ".", 0.4))
            elif t == "keys":
                lines.append(("The actions are on screen: " + "; ".join(r["action"] for r in b["rows"]) + ".", 0.4))
            segs.append({"kind": "quiz", "label": "Quiz", "b": bi, "u": None, "task": None, "opt": False, "quiz": b["id"], "chunks": _chunks(lines, cues_on=False)})
    outro = [("That is everything on this sheet.", 0.4)]
    if pos.get("next"):
        outro.append(("Next up: " + pos["next"] + ".", 0.4))
    segs.append({"kind": "outro", "label": "Wrap-up", "b": None, "u": None, "task": None, "opt": False, "chunks": _chunks(outro)})
    return [s for s in segs if s["chunks"]]


def _plain(s):
    return re.sub(r"[`*_\[\]]", "", s)


def _label(raw):
    t = _plain(raw).strip().rstrip(".:")
    return (t[:44] + "…") if len(t) > 46 else t


ACKS = ["Got it.", "That one is done.", "Nice, checked off.", "There it is.", "Good, that registered.", "Done. Onward."]
LESSON_DONE = "Lesson complete. Well done."


def seg_key(voice, chunks):
    blob = json.dumps([VERSION, voice, [[c["t"], round(c["p"], 2)] for c in chunks]], ensure_ascii=False)
    return hashlib.sha1(blob.encode()).hexdigest()[:16]


def build_script(les, major, voices, pos=None):
    """-> (public script, specs). `voices` = {'narrator': id, 'cubby': id}. specs maps key -> what the engine needs."""
    segs, specs, pub = lesson_segments(les, major, pos), {}, []
    for n, s in enumerate(segs):
        voice = voices.get(s.get("voice", "narrator"), voices["narrator"])
        key = seg_key(voice, s["chunks"])
        specs[key] = {"voice": voice, "chunks": [[c["t"], c["p"]] for c in s["chunks"]]}
        pub.append({"i": n, "key": key, "kind": s["kind"], "voice": s.get("voice", "narrator"), "label": s["label"],
                    "b": s["b"], "u": s["u"], "task": s["task"], "opt": s["opt"], "quiz": s.get("quiz"),
                    "text": " ".join(c["t"] for c in s["chunks"]), "cues": [c["cues"] for c in s["chunks"]],
                    "words": sum(words(c["t"]) for c in s["chunks"])})
    return pub, specs


def line_spec(text, voice):
    ch = [{"t": text, "p": 0.1}]
    key = seg_key(voice, ch)
    return key, {"voice": voice, "chunks": [[text, 0.1]]}


def say_spec(raw, voice):
    """Arbitrary lesson-style text (a hint, a preview) -> (key, spec), cleaned the same way as the script."""
    ch = _chunks([(s, 0.3) for s in sentences(raw)], cues_on=False)
    if not ch:
        return None, None
    return seg_key(voice, ch), {"voice": voice, "chunks": [[c["t"], c["p"]] for c in ch]}
