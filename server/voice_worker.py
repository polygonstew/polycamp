#!/usr/bin/env python3
"""voice_worker.py - the speech synthesizer. Runs in the voice venv (see tools/install_voice.py), NOT in the
server's own interpreter, so the web app stays dependency-free.

Protocol: one JSON object per line on stdin, one per line on stdout.
  in : {"id", "voice", "chunks": [[text, pause_s], ...], "out": "/path/key.ogg"}
  out: {"ready": true, "voices": [...]}                       once, after the model has loaded
       {"id", "ok": true, "dur": s, "marks": [[start, end], ...], "ms": n}
       {"id", "ok": false, "error": "..."}
Kokoro-82M through onnxruntime on the CPU. Two threads and a lowered priority so Blender keeps the machine.
"""
import json
import os
import sys
import time


def lower_priority():
    try:
        if os.name == "nt":
            import ctypes
            ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
        else:
            os.nice(10)
    except Exception:
        pass


def main():
    proto = os.fdopen(os.dup(1), "w", buffering=1)          # keep stdout for the protocol only
    os.dup2(2, 1)
    lower_priority()
    models = os.environ.get("POLYCAMP_VOICE_MODELS", "")
    threads = int(os.environ.get("POLYCAMP_VOICE_THREADS", "2"))

    import numpy as np
    import onnxruntime as ort
    import soundfile as sf
    from kokoro_onnx import Kokoro

    model = os.path.join(models, os.environ.get("POLYCAMP_VOICE_MODEL", "kokoro-v1.0.onnx"))
    if not os.path.exists(model):
        model = os.path.join(models, "kokoro-v1.0.int8.onnx")
    so = ort.SessionOptions()
    so.intra_op_num_threads = threads
    so.inter_op_num_threads = 1
    sess = ort.InferenceSession(model, sess_options=so, providers=["CPUExecutionProvider"])
    kokoro = Kokoro.from_session(sess, os.path.join(models, "voices-v1.0.bin"))
    voices = sorted(kokoro.get_voices())
    ogg_ok = "VORBIS" in sf.available_subtypes("OGG")
    sr_out = 24000
    proto.write(json.dumps({"ready": True, "voices": voices, "model": os.path.basename(model), "ogg": ogg_ok}) + "\n")

    def style(spec):
        """'af_heart' or a blend like 'af_heart:0.7+af_nova:0.3'."""
        if "+" not in spec and ":" not in spec:
            return spec
        mix = None
        for part in spec.split("+"):
            name, _, w = part.partition(":")
            v = kokoro.get_voice_style(name.strip()) * float(w or 1)
            mix = v if mix is None else mix + v
        tot = sum(float(p.partition(":")[2] or 1) for p in spec.split("+"))
        return mix / tot

    def trim(a, floor=0.004, keep=0.04):
        idx = np.where(np.abs(a) > floor)[0]
        if not len(idx):
            return a
        lo, hi = max(0, idx[0] - int(sr_out * keep)), min(len(a), idx[-1] + int(sr_out * keep))
        return a[lo:hi]

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        t0 = time.time()
        try:
            voice = style(req["voice"])
            lang = "en-gb" if str(req["voice"])[:1] == "b" else "en-us"
            parts, marks, t = [], [], 0.0
            for text, pause in req["chunks"]:
                a, sr = kokoro.create(text, voice=voice, speed=1.0, lang=lang)
                a = trim(np.asarray(a, dtype="float32"))
                gap = np.zeros(int(sr * float(pause)), dtype="float32")
                marks.append([round(t, 3), round(t + len(a) / sr, 3)])
                parts += [a, gap]
                t += (len(a) + len(gap)) / sr
            audio = np.concatenate(parts) if parts else np.zeros(sr_out // 4, dtype="float32")
            rms = float(np.sqrt(np.mean(audio ** 2))) or 1e-6              # even loudness from segment to segment
            gain = min(10 ** (-21 / 20) / rms, 0.95 / (float(np.abs(audio).max()) or 1))
            audio = (audio * gain).astype("float32")
            out = req["out"]
            tmp = out + ".part"
            if ogg_ok and out.endswith(".ogg"):
                sf.write(tmp, audio, sr_out, format="OGG", subtype="VORBIS")
            else:
                sf.write(tmp, audio, sr_out, format="WAV", subtype="PCM_16")
            os.replace(tmp, out)
            proto.write(json.dumps({"id": req["id"], "ok": True, "dur": round(len(audio) / sr_out, 3), "marks": marks,
                                    "ms": int((time.time() - t0) * 1000)}) + "\n")
        except Exception as e:                                               # one bad segment must not kill the worker
            proto.write(json.dumps({"id": req.get("id"), "ok": False, "error": "%s: %s" % (type(e).__name__, e)}) + "\n")


if __name__ == "__main__":
    main()
