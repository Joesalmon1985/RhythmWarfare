"""Stages 6 and 7: write the pack (stems as 48 kHz stereo Ogg Vorbis plus track.json) and the listening previews.

All stems go through the same path: one common gain (only if a stem would exceed full scale; the inverse is
written as every stem's `gain`, so played at their gains they still sum to the recording), then the same soxr
resampler to 48 kHz, then libvorbis at the same quality.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np

from audio_io import PACK_RATE, decode, encode_ogg

FORMAT = "rhythm_warfare.track.v1"
HEADROOM = 0.98
CLICK_HZ = {1: 1000.0, 2: 1500.0, 3: 2250.0, 4: 3375.0}  # a fifth apart, low to high from left to right


def common_scale(arrays: list[np.ndarray]) -> float:
    peak = max(float(np.abs(a).max()) for a in arrays)
    return 1.0 if peak <= HEADROOM else HEADROOM / peak


def write_pack(pack_dir: Path, meta: dict, voices: list[dict], backing: list[dict], rate: int) -> dict:
    """voices/backing entries: {key, label?, pad?, audio}. meta: the rest of track.json. Returns the json."""
    stems_dir = pack_dir / "stems"
    if stems_dir.exists():
        shutil.rmtree(stems_dir)
    stems_dir.mkdir(parents=True)
    scale = common_scale([v["audio"] for v in voices + backing])
    gain = round(1.0 / scale, 6)
    out_v, out_b = [], []
    for v in voices:
        encode_ogg(v["audio"] * scale, rate, stems_dir / f"{v['key']}.ogg")
        out_v.append({"key": v["key"], "label": v["label"], "pad": v["pad"], "stem": f"stems/{v['key']}.ogg", "gain": gain})
    for b in backing:
        encode_ogg(b["audio"] * scale, rate, stems_dir / f"{b['key']}.ogg")
        out_b.append({"key": b["key"], "stem": f"stems/{b['key']}.ogg", "gain": gain})
    # duration from what the encoded files really decode to (the loader compares to within 5 ms)
    lengths = {e["key"]: len(decode(pack_dir / e["stem"], rate=PACK_RATE)[0]) for e in out_v + out_b}
    if (max(lengths.values()) - min(lengths.values())) / PACK_RATE > 0.002:
        raise RuntimeError(f"encoded stems disagree in length: {lengths}")
    out_frames = min(lengths.values())
    tj = {"format": FORMAT, "id": meta["id"], "title": meta["title"], "artist": meta["artist"],
          "duration_s": round(out_frames / PACK_RATE, 4), "tempo": meta["tempo"],
          "voices": sorted(out_v, key=lambda v: v["pad"]), "backing": out_b, "sections": meta["sections"],
          "charts": meta["charts"], "default_chart": "normal",
          "rules": {"restore_after_idle_beats": 8}, "source": {**meta["source"], "stem_scale": scale}}
    (pack_dir / "track.json").write_text(json.dumps(tj, indent=1))
    return tj


# ---------------------------------------------------------------- previews

def click(rate: int, hz: float, dur: float = 0.03, level: float = 0.35) -> np.ndarray:
    t = np.arange(int(dur * rate)) / rate
    return (level * np.sin(2 * np.pi * hz * t) * np.exp(-t / (dur / 4))).astype(np.float32)


def add_clicks(x: np.ndarray, rate: int, cues: list[dict], pads: set[int] | None = None) -> np.ndarray:
    y = x.copy()
    for c in cues:
        if pads is not None and c["pad"] not in pads:
            continue
        for t, lvl in [(c["t"], 0.35)] + ([(c["t"] + c["dur"], 0.12)] if c["dur"] > 0 else []):
            k = click(rate, CLICK_HZ[c["pad"]], level=lvl)
            a = int(t * rate)
            b = min(len(y), a + len(k))
            if a < len(y):
                y[a:b] += k[: b - a, None]
    return y


def _norm(x: np.ndarray) -> np.ndarray:
    p = float(np.abs(x).max())
    return x * (HEADROOM / p) if p > HEADROOM else x


def write_previews(prev_dir: Path, mix: np.ndarray, voices: list[dict], cues: list[dict], rate: int,
                   miss: dict) -> list[Path]:
    """mix with every cue clicked (one pitch per pad), each voice solo with its clicks, and one miss demo:
    miss = {key, start_s, end_s, mute_from_s, mute_to_s}: the voice drops out like a missed cue would make it."""
    prev_dir.mkdir(parents=True, exist_ok=True)
    out = []
    p = prev_dir / "mix_clicks_normal.ogg"
    encode_ogg(_norm(add_clicks(mix, rate, cues)), rate, p, out_rate=rate, quality=5)
    out.append(p)
    for v in voices:
        p = prev_dir / f"solo_pad{v['pad']}_{v['key']}_clicks.ogg"
        encode_ogg(_norm(add_clicks(v["audio"], rate, cues, {v["pad"]})), rate, p, out_rate=rate, quality=5)
        out.append(p)
    a, b = int(miss["start_s"] * rate), int(miss["end_s"] * rate)
    v = next(v for v in voices if v["key"] == miss["key"])
    seg = mix[a:b].copy()
    m0, m1 = int((miss["mute_from_s"] - miss["start_s"]) * rate), int((miss["mute_to_s"] - miss["start_s"]) * rate)
    fade = int(0.005 * rate)
    env = np.ones(b - a, np.float32)
    env[m0:m1] = 0.0
    env[max(0, m0 - fade):m0] = np.linspace(1, 0, min(fade, m0))
    env[m1:m1 + fade] = np.linspace(0, 1, len(env[m1:m1 + fade]))
    seg = seg - v["audio"][a:b] * (1 - env)[:, None]
    local = [{**c, "t": c["t"] - miss["start_s"]} for c in cues if miss["start_s"] <= c["t"] < miss["end_s"] - 0.1]
    p = prev_dir / f"miss_{miss['key']}.ogg"
    encode_ogg(_norm(add_clicks(seg, rate, local)), rate, p, out_rate=rate, quality=5)
    out.append(p)
    return out
