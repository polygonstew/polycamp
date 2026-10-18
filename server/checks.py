"""checks.py - evaluate lesson checks (tiny Python expressions) against a Blender snapshot.

A check looks like   any(o.type == 'MESH' and o.dims[2] >= 3 for o in objects)
Only a small, safe subset of Python is allowed (see ALLOWED). Missing data reads as None, and any
error simply makes the check False, so half-built scenes never crash anything.
"""
import ast
import math

ALLOWED = (ast.Expression, ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Compare, ast.IfExp, ast.Call, ast.Attribute,
           ast.Subscript, ast.Name, ast.Constant, ast.List, ast.Tuple, ast.Set, ast.Dict, ast.ListComp, ast.SetComp,
           ast.GeneratorExp, ast.DictComp, ast.comprehension, ast.Load, ast.Store, ast.And, ast.Or, ast.Not, ast.USub,
           ast.UAdd, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.Eq, ast.NotEq, ast.Lt,
           ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn, ast.Is, ast.IsNot, ast.Slice, ast.Starred)
SAFE_METHODS = {"get", "lower", "upper", "startswith", "endswith", "count", "index", "items", "values", "keys_"}
BUILTINS = {"len": len, "any": any, "all": all, "sum": sum, "min": min, "max": max, "abs": abs, "round": round,
            "sorted": sorted, "set": set, "list": list, "tuple": tuple, "int": int, "float": float, "str": str,
            "bool": bool, "range": range, "enumerate": enumerate, "zip": zip, "True": True, "False": False,
            "None": None, "pi": math.pi}


class AD:
    """Dict wrapper: d.key reads d['key'], missing -> None (so checks never raise on absent data)."""
    __slots__ = ("_d",)

    def __init__(self, d):
        object.__setattr__(self, "_d", d)

    def __getattr__(self, k):
        if k.startswith("_"):
            raise AttributeError(k)
        return self._d.get(k)

    def __getitem__(self, k):
        return self._d.get(k)

    def __contains__(self, k):
        return k in self._d

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def __bool__(self):
        return bool(self._d)

    def get(self, k, default=None):
        return self._d.get(k, default)

    def items(self):
        return [(k, wrap(v)) for k, v in self._d.items()]

    def values(self):
        return [wrap(v) for v in self._d.values()]


def wrap(v):
    if isinstance(v, dict):
        return AD({k: wrap(x) for k, x in v.items()})
    if isinstance(v, list):
        return [wrap(x) for x in v]
    return v


class _Validator(ast.NodeVisitor):
    def generic_visit(self, node):
        if not isinstance(node, ALLOWED):
            raise ValueError("not allowed in a check: %s" % type(node).__name__)
        super().generic_visit(node)

    def visit_Attribute(self, node):
        if node.attr.startswith("_"):
            raise ValueError("private attribute")
        self.generic_visit(node)

    def visit_Call(self, node):
        f = node.func
        if isinstance(f, ast.Attribute):
            if f.attr not in SAFE_METHODS:
                raise ValueError("method not allowed: " + f.attr)
        elif not isinstance(f, ast.Name):
            raise ValueError("only simple calls")
        self.generic_visit(node)


_cache = {}


def compile_check(expr):
    code = _cache.get(expr)
    if code is None:
        tree = ast.parse(expr.strip(), mode="eval")
        _Validator().visit(tree)
        code = compile(tree, "<check>", "eval")
        _cache[expr] = code
    return code


def validate(expr):
    """Raise on a bad expression (used by the lesson loader so typos show up at load time)."""
    compile_check(expr)


def make_env(snap, base=None):
    """Names available inside checks. base = baseline captured when the lesson started."""
    base = base or {}
    s = wrap(snap or {})
    objs = s.objects or []
    ops = (snap or {}).get("ops", {})
    bops = base.get("ops", {})
    counters = (snap or {}).get("counters", {})
    bcnt = base.get("counters", {})

    def used(op, n=1):
        return ops.get(op, 0) - bops.get(op, 0) >= n

    def near(a, b, tol=0.01):
        if a is None or b is None:
            return False
        if isinstance(a, (list, tuple)):
            return len(a) == len(b) and all(abs(x - y) <= tol for x, y in zip(a, b))
        return abs(a - b) <= tol

    rl = s.render_last or AD({})
    env = dict(BUILTINS)
    env.update(
        snap=s, objects=objs, meshes=[o for o in objs if o.type == "MESH"],
        lights=[o for o in objs if o.type == "LIGHT"], cams=[o for o in objs if o.type == "CAMERA"],
        selected=[o for o in objs if o.sel], active=next((o for o in objs if o.active), None),
        mode=(s.mode or "OBJECT"), edit=(s.mode or "").startswith("EDIT"),
        render=s.render or AD({}), scene=s.scene or AD({}), world=s.world, materials=s.materials or [],
        images=s.images or [], groups=s.node_groups or [], ui=s.ui or AD({}), prefs=s.prefs or AD({}),
        file=s.file or AD({}), totals=s.totals or AD({}), cols=(s.scene.collections if s.scene else []) or [],
        used=used, near=near, ver=tuple((snap or {}).get("bver", [0, 0, 0])),
        view_moves=counters.get("view_changes", 0) - bcnt.get("view_changes", 0),
        sel_changes=counters.get("sel_changes", 0) - bcnt.get("sel_changes", 0),
        rendered=bool(rl.ts and rl.ts > base.get("t0", 0) and rl.ok), render_secs=rl.time or 0,
        render_last=rl,
        by_name=lambda sub: [o for o in objs if sub.lower() in (o.name or "").lower()],
        mat=lambda name: next((m for m in (s.materials or []) if m.name == name), None),
        mods=lambda o, t: [m for m in (o.mods or []) if m.type == t] if o else [],
    )
    return env


def run(expr, env):
    """True/False for one check; any problem is False."""
    try:
        env["__builtins__"] = {}          # env doubles as globals so names resolve inside comprehensions
        return bool(eval(compile_check(expr), env))
    except Exception:
        return False
