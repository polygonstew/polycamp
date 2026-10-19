#!/usr/bin/env python3
"""Install the narration voice engine (Kokoro-82M on the CPU). Run once on the PC that runs Polycamp:

    python3 tools/install_voice.py            full-quality model (about 330 MB download)
    python3 tools/install_voice.py --small    8-bit model (about 90 MB; sounds a touch rougher, same speed on most CPUs)

What it does: makes a private virtual environment in ~/.polycamp/voice/venv (so nothing is installed into your
system Python), pip-installs kokoro-onnx + soundfile into it, downloads the model and voice files next to it, then
synthesizes one sentence through the real worker to prove it works. Safe to run again; finished steps are skipped.
Windows, Linux and macOS. No GPU needed; synthesis runs at roughly 0.7x real time on a 2-core laptop CPU.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME = Path(os.environ.get("POLYCAMP_VOICE_HOME", Path.home() / ".polycamp" / "voice"))
BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
FILES = {"voices-v1.0.bin": 25_000_000, "kokoro-v1.0.onnx": 300_000_000, "kokoro-v1.0.int8.onnx": 85_000_000}


def say(msg):
    print(msg, flush=True)


def venv_python():
    return HOME / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def make_venv():
    py = venv_python()
    if py.exists():
        say("venv: already there (%s)" % py)
        return
    say("venv: creating %s" % (HOME / "venv"))
    venv.EnvBuilder(with_pip=True, clear=False).create(str(HOME / "venv"))


def pip_install():
    say("pip: installing kokoro-onnx and soundfile (a minute or two)")
    r = subprocess.run([str(venv_python()), "-m", "pip", "install", "--upgrade", "--quiet", "--disable-pip-version-check",
                        "kokoro-onnx", "soundfile"])
    if r.returncode:
        sys.exit("pip failed. Check your internet connection, then run this again.")


def download(name):
    dest = HOME / "models" / name
    need = FILES[name]
    if dest.exists() and dest.stat().st_size > need:
        say("model: %s already downloaded" % name)
        return
    part = dest.with_suffix(dest.suffix + ".part")
    dest.parent.mkdir(parents=True, exist_ok=True)
    have = part.stat().st_size if part.exists() else 0
    req = urllib.request.Request(BASE + name, headers={"Range": "bytes=%d-" % have} if have else {})
    say("model: downloading %s%s" % (name, " (resuming at %d MB)" % (have >> 20) if have else ""))
    with urllib.request.urlopen(req, timeout=60) as r, open(part, "ab" if have and r.status == 206 else "wb") as f:
        total = int(r.headers.get("Content-Length") or 0) + (have if r.status == 206 else 0)
        done = have if r.status == 206 else 0
        t0 = last = time.time()
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if time.time() - last > 2:
                last = time.time()
                say("        %3d%%  %d / %d MB" % (100 * done // max(total, 1), done >> 20, total >> 20))
    if part.stat().st_size <= need:
        sys.exit("%s came down too small (%d bytes). Delete %s and run this again." % (name, part.stat().st_size, part))
    part.replace(dest)


def selftest():
    say("test: making a sentence with the real worker")
    env = dict(os.environ, POLYCAMP_VOICE_MODELS=str(HOME / "models"), POLYCAMP_VOICE_THREADS="2")
    out = HOME / "install-test.ogg"
    p = subprocess.Popen([str(venv_python()), "-u", str(ROOT / "server" / "voice_worker.py")], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env=env)
    try:
        ready = json.loads(p.stdout.readline())
        req = {"id": "t", "voice": "af_heart", "out": str(out),
               "chunks": [["Voice engine installed.", 0.2], ["Press G, X, 3, Enter, and the cube moves three metres along X.", 0.2]]}
        p.stdin.write(json.dumps(req) + "\n")
        p.stdin.flush()
        res = json.loads(p.stdout.readline())
    finally:
        p.terminate()
    if not res.get("ok"):
        sys.exit("test failed: %s" % res.get("error"))
    say("test: ok. %.1f s of audio in %.1f s (%.2fx real time), %d voices, model %s" % (
        res["dur"], res["ms"] / 1000, res["ms"] / 1000 / res["dur"], len(ready["voices"]), ready["model"]))
    say("      sample: %s" % out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--small", action="store_true", help="download the 8-bit model instead of the full one")
    ap.add_argument("--check", action="store_true", help="only report what is installed")
    a = ap.parse_args()
    if sys.version_info < (3, 9):
        sys.exit("Python 3.9 or newer is needed.")
    if a.check:
        ok = venv_python().exists() and (HOME / "models" / "voices-v1.0.bin").exists()
        say("installed" if ok else "not installed")
        return 0 if ok else 1
    HOME.mkdir(parents=True, exist_ok=True)
    make_venv()
    pip_install()
    download("voices-v1.0.bin")
    download("kokoro-v1.0.int8.onnx" if a.small else "kokoro-v1.0.onnx")
    selftest()
    say("\nDone. Reload Polycamp, open a lesson and press Listen. Settings > Narration lets you pick the voices.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
