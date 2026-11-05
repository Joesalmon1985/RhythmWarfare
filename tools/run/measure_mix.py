"""Measure every scene's mix as the run plays it: the ears of an agent that cannot listen (docs/HANDOVER.md "Audio polish").

    python tools/run/measure_mix.py                         # main run + every path, markdown to stdout
    python tools/run/measure_mix.py --out docs/shots/audio/mix_after.md --json docs/shots/audio/mix_after.json
    python tools/run/measure_mix.py --run squadron          # one run only (main, gospel, squadron, ember, stub)

It renders each scene's 64-beat phase OFFLINE from the packs' loops, the way RunAudio plays it under perfect play: block b is mix stage b (content/run/run.json `stages`, a path's
own when it has them), the drums from the phase downbeat, the bass and synth from the reveal (beat 16), an arrangement's sections switching packs on the grid with their recipe gains
(content/music/mix_recipes.json; `mix.recipe_bass_floor` lifts the bass of a recipe in the run), the bass through the bass bus as RunAudio builds it (`mix.bass_bus`: high-pass,
low shelf, Godot's WAVESHAPE distortion, post gain; per path in the path's run.json `mix`, per scene in music.json `bass_bus`) and, in block 0, the previous scene's bass carried
over (`mix.carry_bass`) when the previous scene plays the same music family. Gain ramps (0.35 s) and the hotspot dip are left out of the render (the dip is reported in the dwell
table). The linear filters are applied in the frequency domain over one loop (a looped signal's steady state, exact for an LTI filter); the waveshaper sample by sample, as Godot does.

LAPS (docs/HANDOVER.md A12, docs/CONTINUOUS_RUN.md "Two laps"): a scene of a path may play `laps` phases in a row (path.laps / the scene's `laps`; `--force-laps N` overrides every scene). The render is then
laps x 64 beats: block g of the scene (g = 4 * lap + block) is mix stage min(g, 3) under perfect play, so the bass revealed at beat 16 stays in, at its strongest, through every later lap and the loops simply go on
(every loop tiles a lap). The seconds are per SCENE (laps x the phase), the LUFS and the peak over the whole scene.

Per scene it reports: seconds each voice is audible per phase (gain > 0 and within 20 dB of the mix in that block) and the block it enters; the seconds the bass LEADS (its RMS
within 1 dB of the loudest voice or above it); integrated loudness (BS.1770 K-weighted, gated, LUFS); the sample peak of the mix before the run's limiter (dBFS); BASS PROMINENCE
= the mix's energy in 30-250 Hz over its whole energy, and the sub (30-80 Hz) share, over the blocks with the bass in; bass RMS minus drums RMS and minus synth RMS (dB, as heard,
same blocks); PHONE BASS = the bass voice's energy in 150-1000 Hz relative to the mix's energy in 150-8000 Hz (dB): how much of what a phone speaker can play is the bass
(it cannot play the sub, so this is the bass a phone listener hears). Plus a DWELL table per run.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]  # (--root measures another checkout with this same tool: the "before" table)
FORCE_LAPS = 0  # --force-laps N: every scene plays N laps whatever the data says (0 = the data)
RATE = 48000
RUNS = ["main", "gospel", "squadron", "ember"]
DEFAULT_BUS = {"enabled": False, "highpass_hz": 0.0, "shelf_hz": 100.0, "shelf_db": 0.0, "drive": 0.0, "pre_gain_db": 0.0, "gain_db": 0.0, "keep_hf_hz": 16000.0}


# --- data, as RunData resolves it ------------------------------------------------------------------------------------------

def _json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def merged_mix(base: dict, over: dict | None) -> dict:
    """A path's `mix` (or a scene's `bass_bus`) over the main run's: key by key, `bass_bus` and `carry_bass` merged one level deeper (RunData.merge_mix does the same)."""
    out = json.loads(json.dumps(base))
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = {**out[k], **v}
        else:
            out[k] = v
    return out


def bass_bus_of(mix: dict, scene_bus: dict | None) -> dict:
    bb = {**DEFAULT_BUS, **(mix.get("bass_bus") or {})}
    bb.update(scene_bus or {})
    bb.pop("note", None)
    return bb


def load_run(rid: str) -> dict:
    base = _json(ROOT / "content/run/run.json")
    if rid == "main":
        run, music, path_id = base, _json(ROOT / "content/story/music.json"), ""
    else:
        run = _json(ROOT / "content/paths" / rid / "run.json")
        music, path_id = _json(ROOT / "content/paths" / rid / "music.json"), rid
        for k in ("judgement", "energy", "stages", "effects", "treatments"):
            run.setdefault(k, base[k])
        run["mix"] = merged_mix(base["mix"], run.get("mix"))
    packs = {}
    for pj in (ROOT / "songs/packs").glob("*/pack.json"):
        p = _json(pj)
        if str(p.get("path", "")) == path_id:
            p["dir"] = pj.parent
            packs[str(p["id"])] = p
    recipes = _json(ROOT / "content/music/mix_recipes.json")["recipes"]
    arr_dir = ROOT / "content/music/arrangements" if rid == "main" else ROOT / "content/paths" / rid / "arrangements"
    arrs = {}
    if arr_dir.is_dir():
        for f in arr_dir.glob("*.json"):
            a = _json(f)
            arrs[str(a.get("id", f.stem))] = a
    m = {str(n["id"]): n for n in music["nodes"]}
    nodes = {}
    for n in run["nodes"]:
        nid = str(n["id"])
        mu = m[nid]
        node = {"id": nid, "world": str(n["world"]), "next": [str(e["to"]) for e in n.get("next", [])], "music": mu,
                "laps": FORCE_LAPS or int(n.get("laps", (run.get("path") or {}).get("laps", 1)))}
        if "arrangement" in mu:
            arr = arrs[str(mu["arrangement"])]  # (the scene's own arrangement: the seed may pick an alternate of the same family in the game)
            first = int(mu.get("slot", 0)) * 16 % int(arr["bars"])
            secs, bar = [], 0
            for s in arr["sections"]:
                b = int(s["bars"])
                if first <= bar < first + 16:
                    mx = s.get("mix", "full")
                    g = recipes[mx] if isinstance(mx, str) else mx
                    secs.append({"pack": str(s["pack"]), "start": (bar - first) * 4, "beats": b * 4, "recipe": {k: float(g.get(k, 1.0)) for k in ("drums", "bass", "other")}, "mix": str(mx)})
                bar += b
            node["sections"] = secs
            node["family"] = str(arr.get("family", ""))
        else:
            node["sections"] = [{"pack": str(mu["audio"]), "start": 0, "beats": 64, "recipe": {"drums": 1.0, "bass": 1.0, "other": 1.0}, "mix": "-"}]
            node["family"] = str(mu["audio"])
        node["bass_bus"] = bass_bus_of(run["mix"], mu.get("bass_bus"))
        nodes[nid] = node
    hot = 0
    hdirs = [ROOT / "content/run/hotspots"] if rid == "main" else [ROOT / "content/paths" / rid / "hotspots"]
    for hd in hdirs:
        for f in sorted(hd.glob("*.json")):
            hot += f.read_text(encoding="utf-8").count('"music": "dip"')
    start = str(run.get("start_node", run["nodes"][0]["id"]))
    if path_id:
        start = str((run.get("path") or {}).get("start", start))
        if start not in nodes:
            start = str(run["nodes"][0]["id"])
    return {"id": rid, "run": run, "nodes": nodes, "order": [str(n["id"]) for n in run["nodes"]], "packs": packs, "bpm": float(run["timing"]["bpm"]), "dips": hot, "start": start}


# --- the bass bus (RunAudio._apply_bass_bus) ----------------------------------------------------------------------------------

def _biquad_h(b: tuple, a: tuple, f: np.ndarray) -> np.ndarray:
    z = np.exp(-1j * 2 * np.pi * f / RATE)
    return (b[0] + b[1] * z + b[2] * z * z) / (a[0] + a[1] * z + a[2] * z * z)


def highpass_h(fc: float, f: np.ndarray, q: float = 0.5) -> np.ndarray:
    w = 2 * np.pi * fc / RATE
    c, s = math.cos(w), math.sin(w)
    al = s / (2 * q)
    return _biquad_h(((1 + c) / 2, -(1 + c), (1 + c) / 2), (1 + al, -2 * c, 1 - al), f)


def lowshelf_h(fc: float, gain_db: float, f: np.ndarray, q: float = 0.5) -> np.ndarray:
    """Godot's AudioFilterSW LOWSHELF: A = sqrt(gain), beta = sqrt(A) / sqrt(resonance) (the RBJ shelf with Q = sqrt(resonance))."""
    w = 2 * np.pi * fc / RATE
    c, s = math.cos(w), math.sin(w)
    A = math.sqrt(10 ** (gain_db / 20.0))
    beta = math.sqrt(A) / math.sqrt(q)
    b = (A * ((A + 1) - (A - 1) * c + beta * s), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - beta * s))
    a = ((A + 1) + (A - 1) * c + beta * s, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - beta * s)
    return _biquad_h(b, a, f)


def onepole_lp_h(fc: float, f: np.ndarray) -> np.ndarray:
    c = math.exp(-2 * np.pi * fc / RATE)
    z = np.exp(-1j * 2 * np.pi * f / RATE)
    return (1 - c) / (1 - c * z)


def apply_h(x: np.ndarray, h_of) -> np.ndarray:
    """A linear filter over one loop (circular: the steady state of a looped signal)."""
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(x.shape[0], 1.0 / RATE)
    return np.fft.irfft(X * h_of(f)[:, None], n=x.shape[0], axis=0)


def bass_bus(loop: np.ndarray, gain: float, bb: dict) -> np.ndarray:
    """The bass voice as it leaves the bass bus: the player's gain first (it is the player's volume), then the bus effects in RunAudio's order."""
    x = loop * gain
    if not bb.get("enabled", False):
        return x
    hp, sh = float(bb["highpass_hz"]), float(bb["shelf_db"])
    if hp > 0 or abs(sh) > 1e-9:
        def h(f: np.ndarray) -> np.ndarray:
            out = np.ones_like(f, dtype=complex)
            if hp > 0:
                out = out * highpass_h(hp, f)
            if abs(sh) > 1e-9:
                out = out * lowshelf_h(float(bb["shelf_hz"]), sh, f)
            return out
        x = apply_h(x, h)
    drive, pre, post = float(bb["drive"]), float(bb["pre_gain_db"]), float(bb["gain_db"])
    if drive > 0 or abs(pre) > 1e-9 or abs(post) > 1e-9:
        lo = apply_h(x, lambda f: onepole_lp_h(float(bb["keep_hf_hz"]), f))  # AudioEffectDistortion: only the part under keep_hf_hz is shaped
        hi = x - lo
        a = lo * 10 ** (pre / 20.0)
        k = 2 * drive / (1.00001 - drive)
        a = (1.0 + k) * a / (1.0 + k * np.abs(a))
        x = a * 10 ** (post / 20.0) + hi
    return x


# --- rendering ------------------------------------------------------------------------------------------------------------

_LOOPS: dict = {}


def loop_of(pack: dict, stem: str) -> np.ndarray:
    key = (str(pack["id"]), stem)
    if key not in _LOOPS:
        with wave.open(str(Path(pack["dir"]) / pack["stems"][stem]), "rb") as w:
            assert w.getframerate() == RATE and w.getsampwidth() == 2
            a = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float64).reshape(-1, w.getnchannels()) / 32768.0
        if a.shape[1] == 1:  # a stem stored mono (tools/content/stems.py) plays as the same signal on both sides
            a = np.repeat(a, 2, axis=1)
        n = int(pack.get("loop_frames", len(a)))
        _LOOPS[key] = a[:n] if len(a) >= n else np.concatenate([a, np.zeros((n - len(a), a.shape[1]))])
    return _LOOPS[key]


_BUSSED: dict = {}


def bussed(pack: dict, gain: float, bb: dict) -> np.ndarray:
    key = (str(pack["id"]), round(gain, 6), json.dumps(bb, sort_keys=True))
    if key not in _BUSSED:
        _BUSSED[key] = bass_bus(loop_of(pack, "bass"), gain, bb)
    return _BUSSED[key]


def place(out: np.ndarray, loop: np.ndarray, s0: int, s1: int, origin: int) -> None:
    """Adds samples s0..s1 of a loop that started at sample `origin` (negative: it began before the phase)."""
    if s1 <= s0:
        return
    idx = np.mod(np.arange(s0, s1) - origin, len(loop))
    out[s0:s1] += loop[idx]


def stage_gains(R: dict, b: int) -> dict:
    return R["run"]["stages"][b]["gains"]


def section_at(node: dict, beat: float) -> dict:
    cur = node["sections"][0]
    for s in node["sections"]:
        if s["start"] <= beat:
            cur = s
    return cur


def recipe_gain(R: dict, sec: dict, voice: str) -> float:
    g = float(sec["recipe"][voice])
    if voice == "bass":
        g = max(g, float(R["run"]["mix"].get("recipe_bass_floor", 0.0)))
    return g


def predecessor(R: dict, nid: str) -> str:
    """A scene that leads here by its default route, else by any route ("" for none)."""
    anyp = ""
    for oid in R["order"]:
        nx = R["nodes"][oid]["next"]
        if nx and nx[0] == nid:
            return oid
        if nid in nx and not anyp:
            anyp = oid
    return anyp


def render(R: dict, nid: str) -> dict:
    node = R["nodes"][nid]
    beat_n = 60.0 / R["bpm"] * RATE
    laps = int(node.get("laps", 1))
    N = int(round(64 * laps * beat_n))
    bb = node["bass_bus"]
    voices = {k: np.zeros((N, 2)) for k in ("drums", "bass", "other", "carry")}
    gains = []
    for g in range(4 * laps):  # the scene's blocks, lap after lap: the stage steps on a block at a time under perfect play and stays at the strongest (stage 4) in the laps after the first
        b, lap = g % 4, g // 4
        s_stage = min(g, 3)
        st = stage_gains(R, s_stage)
        # the sections that play in this block (a switch is always on a block boundary at 32-beat sections; cut at the section start anyway)
        for sec in node["sections"]:
            lo, hi = max(sec["start"], 16 * b), min(sec["start"] + sec["beats"], 16 * (b + 1))
            if hi <= lo:
                continue
            p = R["packs"][sec["pack"]]
            off = 64 * lap
            a0, a1 = int(round((lo + off) * beat_n)), int(round((hi + off) * beat_n))
            gd = float(st["drums"]) * recipe_gain(R, sec, "drums")
            place(voices["drums"], loop_of(p, "drums") * gd, a0, a1, int(round(sec["start"] * beat_n)))
            if g >= 1:  # revealed at beat 16 (perfect play); the bass and synth start with the reveal, or with the section when it starts later
                origin = int(round(max(16, sec["start"]) * beat_n))
                gbass = float(st["bass"]) * recipe_gain(R, sec, "bass")
                go = float(st["other"]) * recipe_gain(R, sec, "other")
                if gbass > 0:
                    place(voices["bass"], bussed(p, gbass, bb), a0, a1, origin)
                place(voices["other"], loop_of(p, "other") * go, a0, a1, origin)
            gains.append({"block": g, "section": sec["pack"], "drums": round(gd, 3), "bass": round(float(st["bass"]) * recipe_gain(R, sec, "bass"), 3) if g >= 1 else 0.0,
                          "other": round(float(st["other"]) * recipe_gain(R, sec, "other"), 3) if g >= 1 else 0.0})
    carry = R["run"]["mix"].get("carry_bass") or {}
    cg = float(carry.get("gain", 0.0))
    prev = predecessor(R, nid)
    carried = False
    if cg > 0 and prev and R["nodes"][prev]["family"] == node["family"]:
        pn = R["nodes"][prev]
        last = pn["sections"][-1]
        p = R["packs"][last["pack"]]
        beats = float(carry.get("beats", 16))
        origin = -int(round((64 * int(pn.get("laps", 1)) - max(16, last["start"])) * beat_n))  # it started at the previous scene's reveal (or its last section) and runs on
        place(voices["carry"], bussed(p, cg, pn["bass_bus"]), 0, int(round(beats * beat_n)), origin)
        carried = True
    lvl = 10 ** (float(R["run"]["mix"].get("gain_db", 0.0)) / 20.0)  # the run's level (RunMix's volume): every voice, as heard
    for k in voices:
        voices[k] *= lvl
    mix = sum(voices.values())
    return {"N": N, "beat_n": beat_n, "voices": voices, "mix": mix, "gains": gains, "carried": carried}


# --- metrics ----------------------------------------------------------------------------------------------------------------

def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x ** 2))) if x.size else 0.0


def _db(v: float) -> float:
    return 20 * math.log10(v) if v > 1e-12 else -120.0


def band_energy(x: np.ndarray, lo: float, hi: float) -> float:
    mono = x.mean(axis=1) if x.ndim == 2 else x
    S = np.abs(np.fft.rfft(mono)) ** 2
    f = np.fft.rfftfreq(len(mono), 1.0 / RATE)
    return float(S[(f >= lo) & (f < hi)].sum())


def k_weight(x: np.ndarray) -> np.ndarray:
    # BS.1770 at 48 kHz: the high shelf and the RLB high-pass
    b1, a1 = (1.53512485958697, -2.69169618940638, 1.19839281085285), (1.0, -1.69065929318241, 0.73248077421585)
    b2, a2 = (1.0, -2.0, 1.0), (1.0, -1.99004745483398, 0.99007225036621)
    return apply_h(x, lambda f: _biquad_h(b1, a1, f) * _biquad_h(b2, a2, f))


def lufs(x: np.ndarray) -> float:
    y = k_weight(x)
    blk, hop = int(0.4 * RATE), int(0.1 * RATE)
    ms = []
    for s in range(0, len(y) - blk + 1, hop):
        seg = y[s:s + blk]
        ms.append(float((seg ** 2).mean(axis=0).sum()))
    ms = np.array(ms)
    L = -0.691 + 10 * np.log10(ms + 1e-20)
    g = ms[L > -70]
    if not len(g):
        return -120.0
    rel = -0.691 + 10 * math.log10(g.mean()) - 10
    g2 = ms[(L > -70) & (L > rel)]
    return -0.691 + 10 * math.log10(g2.mean())


def measure(R: dict, nid: str) -> dict:
    r = render(R, nid)
    N, bn, v, mix = r["N"], r["beat_n"], r["voices"], r["mix"]
    blk_s = 16 * 60.0 / R["bpm"]
    aud = {k: 0.0 for k in ("drums", "bass", "other")}
    entry = {k: None for k in aud}
    lead = 0.0
    laps = int(R["nodes"][nid].get("laps", 1))
    for b in range(4 * laps):
        s0, s1 = int(round(16 * b * bn)), int(round(16 * (b + 1) * bn))
        m = _rms(mix[s0:s1])
        lv = {k: _rms(v[k][s0:s1]) + (_rms(v["carry"][s0:s1]) if k == "bass" else 0.0) for k in aud}
        for k in aud:
            if lv[k] > 0 and _db(lv[k]) >= _db(m) - 20:
                aud[k] += blk_s
                if entry[k] is None:
                    entry[k] = b + 1
        if lv["bass"] > 0 and _db(lv["bass"]) >= max(_db(lv["drums"]), _db(lv["other"])) - 1.0:
            lead += blk_s
    s16 = int(round(16 * bn))
    mb, bb = mix[s16:], v["bass"][s16:]
    tot = band_energy(mb, 0, RATE / 2)
    out = {
        "scene": nid, "family": R["nodes"][nid]["family"], "carry": r["carried"], "laps": laps, "scene_s": laps * 64 * 60.0 / R["bpm"],
        "aud": aud, "entry": entry, "bass_lead_s": lead,
        "lufs": lufs(mix), "peak_db": _db(float(np.abs(mix).max())),
        "bass_band": band_energy(mb, 30, 250) / tot, "sub_band": band_energy(mb, 30, 80) / tot,
        "bass_vs_drums_db": _db(_rms(bb)) - _db(_rms(v["drums"][s16:])),
        "bass_vs_other_db": _db(_rms(bb)) - _db(_rms(v["other"][s16:])),
        "phone_bass_db": 10 * math.log10(max(band_energy(bb, 150, 1000), 1e-20) / max(band_energy(mb, 150, 8000), 1e-20)),
        "bass_rms_db": _db(_rms(bb)),
        "gains": r["gains"],
    }
    return out


# --- dwell --------------------------------------------------------------------------------------------------------------------

def default_route(R: dict) -> list:
    seq, seen, cur = [], set(), R["start"]
    while cur in R["nodes"] and cur not in seen:
        seen.add(cur)
        seq.append(cur)
        nx = R["nodes"][cur]["next"]
        cur = nx[0] if nx else ""
    return seq


def dwell(R: dict) -> dict:
    beat = 60.0 / R["bpm"]
    phase = 64 * beat
    seq = default_route(R)
    scene_s = [int(R["nodes"][n].get("laps", 1)) * phase for n in seq]  # seconds the player sits in each scene of the default route
    runs_family, runs_world = [], []
    for key, store in (("family", runs_family), ("world", runs_world)):
        cur, n = None, 0
        for s in seq:
            k = R["nodes"][s][key]
            if k == cur:
                n += 1
            else:
                if cur is not None:
                    store.append(n)
                cur, n = k, 1
        if cur is not None:
            store.append(n)
    secs = [len(R["nodes"][n]["sections"]) for n in R["order"]]
    min_sec = min(s["beats"] for n in R["order"] for s in R["nodes"][n]["sections"]) * beat
    st = R["run"]["stages"]
    mixd = R["run"]["mix"]
    carry = float((mixd.get("carry_bass") or {}).get("gain", 0.0))
    return {
        "bpm": R["bpm"], "phase_s": phase, "block_s": 16 * beat, "scenes": len(R["order"]), "default_route": len(seq),
        "scene_s_mean": float(np.mean(scene_s)), "scene_s_min": float(min(scene_s)), "scene_s_max": float(max(scene_s)), "route_s": float(sum(scene_s)),
        "laps": sorted({int(R["nodes"][n].get("laps", 1)) for n in R["order"]}),
        "phases_per_family": runs_family, "phases_per_world": runs_world,
        "sections_per_phase": (min(secs), max(secs)), "min_section_s": min_sec,
        "arrangement_changes_per_phase": 3 + max(secs) - 1,
        "stage_bass": [float(s["gains"]["bass"]) for s in st],
        "bass_on_s": 48 * beat, "bass_off_s": 16 * beat, "carry_gain": carry,
        "dip_hotspots": R["dips"], "dip_gain": float(mixd.get("dip_gain", 0.35)), "dip_beats": float(mixd.get("dip_beats", 8.0)),
        "dip_s": float(mixd.get("dip_beats", 8.0)) * beat, "phase_fade_s": float(mixd["phase_fade_s"]),
        "recipe_bass_floor": float(mixd.get("recipe_bass_floor", 0.0)), "gain_db": float(mixd.get("gain_db", 0.0)),
    }


# --- report -------------------------------------------------------------------------------------------------------------------

def fmt_entry(e) -> str:
    return "-" if e is None else str(e)


def report(results: dict, title: str) -> str:
    L = [f"# {title}", "", "Written by `python tools/run/measure_mix.py` (offline render from the packs, perfect play, block b = mix stage b, the bass revealed at beat 16; see the script's docstring).",
         "Voice seconds are per 64-beat phase; `in` = the block (1-4) the voice is first audible; peak is before the run's limiter.", ""]
    for rid, res in results.items():
        d = res["dwell"]
        L += [f"## {rid} ({d['bpm']:g} BPM)", "",
              f"Dwell: phase {d['phase_s']:.1f} s (4 blocks of {d['block_s']:.2f} s), laps per scene {d.get('laps', [1])}: a scene lasts {d.get('scene_s_min', d['phase_s']):.1f}-{d.get('scene_s_max', d['phase_s']):.1f} s "
              f"(mean {d.get('scene_s_mean', d['phase_s']):.1f} s) and the default route {d.get('route_s', d['phase_s'] * d['default_route']):.0f} s; {d['scenes']} scenes; default route {d['default_route']} phases; phases per music family along it {d['phases_per_family']}, per world {d['phases_per_world']}; "
              f"{d['sections_per_phase'][0]}-{d['sections_per_phase'][1]} arrangement sections per phase (shortest {d['min_section_s']:.1f} s); up to {d['arrangement_changes_per_phase']} mix/arrangement changes per phase; "
              f"stage bass gains {d['stage_bass']}; recipe bass floor {d['recipe_bass_floor']:g}; bass in {d['bass_on_s']:.1f} s then out {d['bass_off_s']:.1f} s at every scene change (carried at {d['carry_gain']:g} within a family); "
              f"{d['dip_hotspots']} hotspots dip the music to {d['dip_gain']:g} ({_db(d['dip_gain']):.1f} dB) for {d['dip_beats']:g} beats ({d['dip_s']:.1f} s); phase fade {d['phase_fade_s']:g} s; run level {d.get('gain_db', 0.0):+g} dB.", "",
              "| scene | family | drums s (in) | bass s (in) | synth s (in) | bass leads s | LUFS | peak dBFS | bass band 30-250 | sub 30-80 | bass-drums dB | bass-synth dB | phone bass dB | carry |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for m in res["scenes"]:
            L.append(f"| {m['scene']} | {m['family']} | {m['aud']['drums']:.1f} ({fmt_entry(m['entry']['drums'])}) | {m['aud']['bass']:.1f} ({fmt_entry(m['entry']['bass'])}) | {m['aud']['other']:.1f} ({fmt_entry(m['entry']['other'])}) | "
                     f"{m['bass_lead_s']:.1f} | {m['lufs']:.1f} | {m['peak_db']:.1f} | {m['bass_band'] * 100:.0f}% | {m['sub_band'] * 100:.0f}% | {m['bass_vs_drums_db']:+.1f} | {m['bass_vs_other_db']:+.1f} | {m['phone_bass_db']:.1f} | {'yes' if m['carry'] else ''} |")
        s = summary(res)
        L += ["", f"Mean over the {len(res['scenes'])} scenes: bass band {s['bass_band'] * 100:.1f}%, sub {s['sub_band'] * 100:.1f}%, bass-drums {s['bass_vs_drums_db']:+.1f} dB, phone bass {s['phone_bass_db']:.1f} dB, "
              f"bass audible {s['bass_s']:.1f} s and leading {s['lead_s']:.1f} s of {s['scene_s']:.1f} s in a scene, LUFS {s['lufs']:.1f}, worst peak {s['peak_max']:.1f} dBFS.", ""]
    return "\n".join(L) + "\n"


def comparison(before: dict, after: dict) -> str:
    """The before/after table: one row per run, the means over its scenes (`before` is a --json file of an earlier measurement)."""
    L = ["## Before and after", "", "Means over each run's scenes (bass seconds include a carried bass in block 0); worst peak = the loudest scene, before any limiter (the run has none).", "",
         "| run | bass band 30-250 | sub 30-80 | bass-drums dB | phone bass dB | bass audible s / phase | bass leads s / phase | scenes with a carry | LUFS | worst peak dBFS |",
         "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for rid in after:
        if rid not in before:
            continue
        b, a = before[rid]["summary"], after[rid]["summary"]
        cb = sum(1 for m in before[rid]["scenes"] if m["carry"])
        ca = sum(1 for m in after[rid]["scenes"] if m["carry"])
        ph = after[rid]["summary"].get("scene_s", after[rid]["dwell"]["phase_s"])
        phb = before[rid]["summary"].get("scene_s", before[rid]["dwell"]["phase_s"])
        L.append(f"| {rid} | {b['bass_band'] * 100:.1f}% -> {a['bass_band'] * 100:.1f}% | {b['sub_band'] * 100:.1f}% -> {a['sub_band'] * 100:.1f}% | {b['bass_vs_drums_db']:+.1f} -> {a['bass_vs_drums_db']:+.1f} | "
                 f"{b['phone_bass_db']:.1f} -> {a['phone_bass_db']:.1f} | {b['bass_s']:.1f} of {phb:.1f} -> {a['bass_s']:.1f} of {ph:.1f} | {b['lead_s']:.1f} -> {a['lead_s']:.1f} | {cb} -> {ca} of {len(after[rid]['scenes'])} | "
                 f"{b['lufs']:.1f} -> {a['lufs']:.1f} | {b['peak_max']:.1f} -> {a['peak_max']:.1f} |")
    return "\n".join(L) + "\n\n"


def summary(res: dict) -> dict:
    sc = res["scenes"]
    mean = lambda k: float(np.mean([m[k] for m in sc]))  # noqa: E731
    return {"bass_band": mean("bass_band"), "sub_band": mean("sub_band"), "bass_vs_drums_db": mean("bass_vs_drums_db"), "phone_bass_db": mean("phone_bass_db"),
            "bass_s": float(np.mean([m["aud"]["bass"] for m in sc])), "lead_s": mean("bass_lead_s"), "lufs": mean("lufs"), "peak_max": max(m["peak_db"] for m in sc),
            "bass_band_min": min(m["bass_band"] for m in sc), "scene_s": float(np.mean([m.get("scene_s", 0.0) for m in sc]))}


def measure_run(rid: str, scenes: list | None = None) -> dict:
    R = load_run(rid)
    ids = scenes or R["order"]
    return {"dwell": dwell(R), "scenes": [measure(R, n) for n in ids]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="append", help="main, gospel, squadron, ember (default: all four)")
    ap.add_argument("--out", help="markdown file (default stdout)")
    ap.add_argument("--json", help="also write the numbers as JSON")
    ap.add_argument("--title", default="Mix measurement")
    ap.add_argument("--before", help="a --json file of an earlier measurement: adds the before/after table")
    ap.add_argument("--root", help="measure another checkout (its content and packs) with this tool")
    ap.add_argument("--force-laps", type=int, default=0, help="every scene plays this many laps whatever the data says (1 = the single phase of before the two laps)")
    args = ap.parse_args()
    global ROOT, FORCE_LAPS
    FORCE_LAPS = max(args.force_laps, 0)
    if args.root:
        ROOT = Path(args.root).resolve()
    results = {}
    for rid in args.run or RUNS:
        results[rid] = measure_run(rid)
        _BUSSED.clear()
        print(f"measured {rid}: {len(results[rid]['scenes'])} scenes", file=sys.stderr)
    text = report(results, args.title)
    if args.before:
        before = json.loads(Path(args.before).read_text(encoding="utf-8"))
        after = {k: {"dwell": v["dwell"], "summary": summary(v), "scenes": v["scenes"]} for k, v in results.items()}
        head, _, rest = text.partition("\n## ")
        text = head + "\n" + comparison(before, after) + "## " + rest
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(text)
    if args.json:
        Path(args.json).write_text(json.dumps({k: {"dwell": v["dwell"], "summary": summary(v), "scenes": v["scenes"]} for k, v in results.items()}, indent=1), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
