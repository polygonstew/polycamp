"""texlab.py - Texture Lab backend: ComfyUI client (CPU friendly), texture sets on disk, sending sets to
Blender, and exporting models/textures into a Godot project or Kiln game folder.

The pixel work (seamless blending, height/normal/roughness maps) happens in the browser canvas
(web/js/texlab.js) so the server stays dependency-free. Here: files, jobs, ComfyUI and Godot.
"""
import base64
import json
import re
import shutil
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import config

SAFE = re.compile(r"[^A-Za-z0-9._-]")
KINDS = ("base_color", "height", "normal", "roughness", "metallic", "ao", "emission")
JOBS = {}
JOB_LOCK = threading.Lock()

PRESETS = [
    {"id": "wood", "name": "Wood planks", "proc": "planks",
     "prompt": "seamless wood planks texture, top down, flat even lighting, detailed grain, weathered oak"},
    {"id": "stone", "name": "Stone bricks", "proc": "bricks",
     "prompt": "seamless old stone brick wall texture, flat lighting, mossy mortar, top down photo"},
    {"id": "cobble", "name": "Cobblestone", "proc": "cells",
     "prompt": "seamless cobblestone ground texture, top down, flat lighting, worn grey stones"},
    {"id": "rust", "name": "Rusty metal", "proc": "rust",
     "prompt": "seamless rusty corroded metal plate texture, flat lighting, scratches, orange brown patina"},
    {"id": "roof", "name": "Roof shingles", "proc": "shingles",
     "prompt": "seamless wooden roof shingles texture, overlapping, weathered dark brown, flat lighting"},
    {"id": "grass", "name": "Grass", "proc": "grass",
     "prompt": "seamless grass lawn texture, top down, flat lighting, short green grass blades"},
    {"id": "leather", "name": "Leather", "proc": "cells",
     "prompt": "seamless brown leather texture, fine grain, flat lighting, close up"},
    {"id": "plaster", "name": "Plaster wall", "proc": "noise",
     "prompt": "seamless rough plaster wall texture, cream colour, flat lighting, subtle cracks"},
]
NEGATIVE = ("perspective, shadow, vignette, border, frame, text, watermark, logo, object, scene, "
            "blurry, lowres, deformed")
SPEEDS = {   # steps, cfg, sampler, scheduler, use LCM lora   (CPU-box reality: ~30 s/step at 512px)
    "fast": (5, 1.5, "lcm", "sgm_uniform", True),
    "normal": (8, 2.0, "lcm", "sgm_uniform", True),
    "quality": (16, 7.0, "euler", "normal", False),
}


# ------------------------------------------------------------------ ComfyUI

def _comfy(path, payload=None, timeout=15, raw=False):
    url = config.load()["comfy_url"].rstrip("/") + path
    data, headers = None, {}
    if payload is not None:
        data, headers = json.dumps(payload).encode(), {"Content-Type": "application/json"}
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=timeout) as r:
        body = r.read()
    return body if raw else json.loads(body or b"{}")


def comfy_status():
    try:
        stats = _comfy("/system_stats", timeout=3)
        info = _comfy("/object_info/CheckpointLoaderSimple", timeout=5)
        ckpts = info["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
        loras = _comfy("/object_info/LoraLoader", timeout=5)["LoraLoader"]["input"]["required"]["lora_name"][0]
        q = _comfy("/queue", timeout=3)
        return {"ok": True, "version": stats.get("system", {}).get("comfyui_version"), "checkpoints": ckpts,
                "has_lcm": any("lcm" in l.lower() for l in loras), "busy": bool(q.get("queue_running")),
                "ckpt": config.load()["comfy_ckpt"]}
    except Exception as e:
        return {"ok": False, "error": "ComfyUI isn't answering at %s (%s)" % (config.load()["comfy_url"], e)}


def workflow(prompt, negative, side, speed, seed, init_name=None, denoise=0.6):
    s = config.load()
    steps, cfg, sampler, sched, lcm = SPEEDS.get(speed, SPEEDS["fast"])
    model_ref, clip_ref = ["4", 0], ["4", 1]
    wf = {"4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": s["comfy_ckpt"]}}}
    if lcm:
        wf["10"] = {"class_type": "LoraLoader", "inputs": {"model": ["4", 0], "clip": ["4", 1],
                                                           "lora_name": "lcm-lora-sdv1-5.safetensors",
                                                           "strength_model": 1.0, "strength_clip": 1.0}}
        model_ref, clip_ref = ["10", 0], ["10", 1]
    wf["6"] = {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": clip_ref}}
    wf["7"] = {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": clip_ref}}
    if init_name:
        wf["11"] = {"class_type": "LoadImage", "inputs": {"image": init_name}}
        wf["12"] = {"class_type": "ImageScale", "inputs": {"image": ["11", 0], "upscale_method": "bilinear",
                                                           "width": side, "height": side, "crop": "center"}}
        wf["13"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["12", 0], "vae": ["4", 2]}}
        latent, dn = ["13", 0], denoise
    else:
        wf["5"] = {"class_type": "EmptyLatentImage", "inputs": {"width": side, "height": side, "batch_size": 1}}
        latent, dn = ["5", 0], 1.0
    wf["3"] = {"class_type": "KSampler", "inputs": {"seed": seed, "steps": steps, "cfg": cfg, "sampler_name": sampler,
                                                    "scheduler": sched, "denoise": dn, "model": model_ref,
                                                    "positive": ["6", 0], "negative": ["7", 0], "latent_image": latent}}
    wf["8"] = {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}}
    wf["9"] = {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "polycamp"}}
    return wf, steps


def _upload_to_comfy(png_bytes):
    boundary = uuid.uuid4().hex
    name = "polycamp_init_%s.png" % uuid.uuid4().hex[:8]
    parts = [("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\nContent-Type: image/png\r\n\r\n"
              % (boundary, name)).encode(), png_bytes,
             ("\r\n--%s\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--%s--\r\n"
              % (boundary, boundary)).encode()]
    req = urllib.request.Request(config.load()["comfy_url"].rstrip("/") + "/upload/image", data=b"".join(parts),
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())["name"]


def start_job(d):
    with JOB_LOCK:
        if any(j["status"] == "running" for j in JOBS.values()):
            return {"ok": False, "error": "A texture is already cooking. The CPU can only do one at a time."}
        jid = uuid.uuid4().hex[:8]
        JOBS[jid] = {"id": jid, "status": "running", "t0": time.time(), "steps": 0, "image": None, "error": None,
                     "prompt": d.get("prompt", "")}
    threading.Thread(target=_run_job, args=(jid, d), daemon=True).start()
    return {"ok": True, "job": jid}


def _run_job(jid, d):
    job = JOBS[jid]
    try:
        side = max(256, min(int(d.get("side") or config.load()["comfy_side"]), 640)) // 64 * 64
        seed = int(d.get("seed") or int(time.time()) % 1_000_000_000)
        init = None
        if d.get("init"):
            init = _upload_to_comfy(base64.b64decode(d["init"].split(",", 1)[-1]))
        wf, steps = workflow(d["prompt"], d.get("negative") or NEGATIVE, side, d.get("speed", "fast"), seed, init,
                             float(d.get("denoise", 0.6)))
        job.update(steps=steps, side=side, seed=seed)
        pid = _comfy("/prompt", {"prompt": wf, "client_id": "polycamp"}, timeout=20)["prompt_id"]
        job["comfy_id"] = pid
        deadline = time.time() + 3600
        while time.time() < deadline:
            time.sleep(2.0)
            hist = _comfy("/history/" + pid, timeout=10)
            if pid in hist:
                outs = hist[pid].get("outputs", {})
                imgs = next((o["images"] for o in outs.values() if o.get("images")), None)
                if not imgs:
                    raise RuntimeError("ComfyUI finished without an image: %s" % json.dumps(hist[pid].get("status", {}))[:200])
                im = imgs[0]
                raw = _comfy("/view?filename=%s&subfolder=%s&type=%s" % (im["filename"], im.get("subfolder", ""),
                                                                           im.get("type", "output")), raw=True, timeout=30)
                out = config.DATA / "textures" / "_gen"
                out.mkdir(exist_ok=True)
                (out / ("gen-%s.png" % jid)).write_bytes(raw)
                job.update(status="done", image="/files/textures/_gen/gen-%s.png" % jid)
                return
        raise RuntimeError("Timed out waiting for ComfyUI")
    except Exception as e:
        job.update(status="error", error=str(e)[:300])


def job_view(jid):
    j = JOBS.get(jid)
    if j is None:
        return {"error": "no such job"}
    return dict(j, elapsed=round(time.time() - j["t0"], 1))


def cancel_jobs():
    try:
        _comfy("/interrupt", {}, timeout=5)
    except Exception:
        pass
    for j in JOBS.values():
        if j["status"] == "running":
            j.update(status="error", error="cancelled")


# ------------------------------------------------------------------ texture sets

def set_dir(name):
    return config.DATA / "textures" / SAFE.sub("_", name)[:60]


def save_set(name, maps, meta=None):
    d = set_dir(name)
    d.mkdir(parents=True, exist_ok=True)
    saved = []
    for kind, url in maps.items():
        if kind in KINDS and url:
            (d / (kind + ".png")).write_bytes(base64.b64decode(url.split(",", 1)[-1]))
            saved.append(kind)
    (d / "meta.json").write_text(json.dumps(dict(meta or {}, kinds=saved, ts=time.time())))
    return {"ok": True, "set": d.name, "kinds": saved}


def list_sets():
    out = []
    for d in sorted((config.DATA / "textures").iterdir(), key=lambda p: -p.stat().st_mtime):
        if d.is_dir() and not d.name.startswith("_"):
            kinds = [k for k in KINDS if (d / (k + ".png")).exists()]
            if kinds:
                out.append({"name": d.name, "kinds": kinds, "mtime": d.stat().st_mtime,
                            "thumb": "/files/textures/%s/%s.png" % (d.name, "base_color" if "base_color" in kinds else kinds[0])})
    return out


def send_to_blender(bridge, d):
    name = SAFE.sub("_", d["set"])
    kinds = [k for k in KINDS if (set_dir(name) / (k + ".png")).exists()]
    if not kinds:
        raise ValueError("That texture set has no maps yet.")
    files = {k: "/files/textures/%s/%s.png" % (name, k) for k in kinds}
    return bridge.command("make_material", {
        "name": name, "files": files, "apply": d.get("apply", "selected"), "tiling": d.get("tiling", [1, 1]),
        "normal_strength": float(d.get("normal_strength", 1.0)), "bump_strength": float(d.get("bump_strength", 0.2))},
        d.get("cid"), wait=30)


# ------------------------------------------------------------------ Godot / Kiln

def kiln_games():
    root = Path.home() / ".jcodes" / "kiln" / "library" / "games"
    return [str(p) for p in sorted(root.iterdir()) if p.is_dir()] if root.exists() else []


def project_root(dirpath):
    p = Path(dirpath)
    for q in [p, *p.parents]:
        if (q / "project.godot").exists():
            return q
    return p


def export_set_to_godot(name):
    gd = config.load()["godot_dir"]
    if not gd:
        raise ValueError("Pick a Godot / Kiln folder first (Settings > Godot).")
    src = set_dir(name)
    dst = Path(gd) / "textures" / src.name
    dst.mkdir(parents=True, exist_ok=True)
    kinds = [k for k in KINDS if (src / (k + ".png")).exists()]
    for k in kinds:
        shutil.copy2(src / (k + ".png"), dst / (k + ".png"))
    root = project_root(gd)
    rel = lambda k: "res://" + (dst / (k + ".png")).relative_to(root).as_posix()
    ids, lines = {}, []
    for i, k in enumerate(kinds, 1):
        ids[k] = i
        lines.append('[ext_resource type="Texture2D" path="%s" id="%d"]' % (rel(k), i))
    body = ["[resource]"]
    if "base_color" in ids:
        body.append('albedo_texture = ExtResource("%d")' % ids["base_color"])
    if "normal" in ids:
        body += ["normal_enabled = true", 'normal_texture = ExtResource("%d")' % ids["normal"]]
    if "roughness" in ids:
        body.append('roughness_texture = ExtResource("%d")' % ids["roughness"])
    if "ao" in ids:
        body += ["ao_enabled = true", 'ao_texture = ExtResource("%d")' % ids["ao"]]
    if "height" in ids:
        body += ["heightmap_enabled = true", 'heightmap_texture = ExtResource("%d")' % ids["height"], "heightmap_scale = 1.0"]
    tres = '[gd_resource type="StandardMaterial3D" load_steps=%d format=3]\n\n%s\n\n%s\n' % (
        len(ids) + 1, "\n".join(lines), "\n".join(body))
    (dst / (src.name + ".tres")).write_text(tres)
    return {"ok": True, "folder": str(dst), "material": str(dst / (src.name + ".tres")), "kinds": kinds}


def export_model_file(name, engine):
    """A .glb arrived from Blender: copy it into <godot_dir>/models when one is configured."""
    gd = config.load()["godot_dir"]
    if not gd:
        return {"exported": None}
    dst = Path(gd) / "models"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(config.DATA / "models" / name, dst / name)
    engine.set_flag("godot")
    return {"exported": str(dst / name)}


# ------------------------------------------------------------------ routes

def get(route, qs, engine, bridge):
    if route == "comfy/status":
        return comfy_status()
    if route == "tex/presets":
        return {"presets": PRESETS, "negative": NEGATIVE, "speeds": {k: {"steps": v[0], "lcm": v[4]} for k, v in SPEEDS.items()}}
    if route == "tex/list":
        return {"sets": list_sets()}
    if route == "tex/job":
        return job_view(qs.get("id", ""))
    if route == "kiln/info":
        s = config.load()
        return {"godot_dir": s["godot_dir"], "kiln_games": kiln_games(),
                "project_root": str(project_root(s["godot_dir"])) if s["godot_dir"] else ""}
    return None


def post(route, qs, data, engine, bridge, hub):
    if route == "tex/generate":
        return start_job(data)
    if route == "tex/cancel":
        cancel_jobs()
        return {"ok": True}
    if route == "tex/save":
        r = save_set(data["name"], data["maps"], data.get("meta"))
        engine.set_flag("textures")
        hub.publish("texture", set=r["set"])
        return r
    if route == "tex/to_blender":
        return send_to_blender(bridge, data)
    if route == "tex/export_godot":
        r = export_set_to_godot(SAFE.sub("_", data["set"]))
        engine.set_flag("godot")
        return r
    if route == "tex/delete":
        shutil.rmtree(set_dir(data["set"]), ignore_errors=True)
        return {"ok": True}
    if route == "uv/request":
        return bridge.command("uv_layout", {"object": data.get("object"), "size": int(data.get("size", 1024))},
                              data.get("cid"), wait=30)
    return None
