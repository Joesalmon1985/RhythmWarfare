"""Stages 7 and 8: write the pack (stems as 48 kHz stereo Ogg Vorbis plus track.json, format v2) and the
listening previews.

All stems go through the same path: one common gain (only if a stem would exceed full scale; the inverse is
written as every stem's `gain`, so played at their gains they still sum to the recording), then the same soxr
resampler to 48 kHz, then libvorbis at the same quality. The stems are only re-encoded when the voices changed
(a stamp in stems/.made_from records the voice files they came from), so rerunning the focus or the charts of a
track rewrites track.json in seconds.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np

from audio_io import PACK_RATE, decode, encode_ogg

FORMAT = "rhythm_warfare.track.v2"
HEADROOM = 0.98
CLICK_HZ = {1: 1000.0, 2: 1500.0, 3: 2250.0, 4: 3375.0}  # a fifth apart, rising from pad 1 to pad 4
FORWARD_DB = -9.0  # the other voices and the backing in the focus-forward preview


def common_scale(arrays: list[np.ndarray]) -> float:
    peak = max(float(np.abs(a).max()) for a in arrays)
    return 1.0 if peak <= HEADROOM else HEADROOM / peak


def write_stems(pack_dir: Path, voices: list[dict], backing: list[dict], rate: int, stamp: str) -> dict:
    """Encode every stem unless stems/.made_from already says they came from the same voice files.
    Returns {"gain", "scale", "frames"}."""
    stems_dir = pack_dir / "stems"
    made = stems_dir / ".made_from"
    if made.is_file():
        old = json.loads(made.read_text())
        if old.get("stamp") == stamp and all((stems_dir / f"{e['key']}.ogg").is_file() for e in voices + backing):
            return old
    if stems_dir.exists():
        shutil.rmtree(stems_dir)
    stems_dir.mkdir(parents=True)
    scale = common_scale([v["audio"] for v in voices + backing])
    for e in voices + backing:
        encode_ogg(e["audio"] * scale, rate, stems_dir / f"{e['key']}.ogg")
    # duration from what the encoded files really decode to (the loader compares to within 5 ms)
    lengths = {e["key"]: len(decode(stems_dir / f"{e['key']}.ogg", rate=PACK_RATE)[0]) for e in voices + backing}
    if (max(lengths.values()) - min(lengths.values())) / PACK_RATE > 0.002:
        raise RuntimeError(f"encoded stems disagree in length: {lengths}")
    info = {"stamp": stamp, "scale": scale, "gain": round(1.0 / scale, 6), "frames": min(lengths.values())}
    made.write_text(json.dumps(info))
    return info


def write_pack(pack_dir: Path, meta: dict, voices: list[dict], backing: list[dict], rate: int, stamp: str) -> dict:
    """voices: {key, label, kind, audio}; backing: {key, audio}; meta: the rest of track.json. Returns the json."""
    info = write_stems(pack_dir, voices, backing, rate, stamp)
    gain = info["gain"]
    out_v = [{"key": v["key"], "label": v["label"], "kind": v["kind"], "stem": f"stems/{v['key']}.ogg", "gain": gain}
             for v in voices]
    out_b = [{"key": b["key"], "stem": f"stems/{b['key']}.ogg", "gain": gain} for b in backing]
    tj = {"format": FORMAT, "id": meta["id"], "title": meta["title"], "artist": meta["artist"],
          "duration_s": round(info["frames"] / PACK_RATE, 4), "tempo": meta["tempo"],
          "voices": out_v, "backing": out_b, "sections": meta["sections"], "focus": meta["focus"],
          "charts": meta["charts"], "default_chart": "normal",
          "rules": {"restore_after_idle_beats": 8}, "source": {**meta["source"], "stem_scale": info["scale"]}}
    (pack_dir / "track.json").write_text(json.dumps(tj, indent=1))
    return tj


# ---------------------------------------------------------------- previews

def click(rate: int, hz: float, dur: float = 0.03, level: float = 0.35) -> np.ndarray:
    t = np.arange(int(dur * rate)) / rate
    return (level * np.sin(2 * np.pi * hz * t) * np.exp(-t / (dur / 4))).astype(np.float32)


def marker(rate: int, rising: bool = True, level: float = 0.3) -> np.ndarray:
    """The focus-change sound: three quick bell notes (C5 E5 G5, rising into a stretch; falling into a gap),
    150 ms, softer and longer than any click so it cannot be mistaken for a cue."""
    notes = (523.25, 659.26, 783.99) if rising else (783.99, 659.26, 523.25)
    n = int(0.05 * rate)
    t = np.arange(n) / rate
    out = []
    for hz in notes:
        out.append(np.sin(2 * np.pi * hz * t) * np.exp(-t / 0.03) * (1 - np.exp(-t / 0.002)))
    return (level * np.concatenate(out)).astype(np.float32)


def _add(y: np.ndarray, k: np.ndarray, t: float, rate: int) -> None:
    a = int(round(t * rate))
    if a < 0 or a >= len(y):
        return
    b = min(len(y), a + len(k))
    y[a:b] += k[: b - a, None]


def add_clicks(x: np.ndarray, rate: int, cues: list[dict], focus: list[dict] | None = None,
               t0: float = 0.0) -> np.ndarray:
    """A click on every cue (pitch by pad, softer where a hold ends) and a marker at every change of focus."""
    y = x.copy()
    for c in cues:
        _add(y, click(rate, CLICK_HZ[c["pad"]]), c["t"] - t0, rate)
        if c["dur"] > 0:
            _add(y, click(rate, CLICK_HZ[c["pad"]], level=0.12), c["t"] + c["dur"] - t0, rate)
    for t, rising in focus_changes(focus or []):
        _add(y, marker(rate, rising), t - t0, rate)
    return y


def focus_changes(focus: list[dict]) -> list[tuple[float, bool]]:
    """(time, into a stretch?) of every change: a stretch start, and a stretch end not followed by another."""
    out = []
    for i, f in enumerate(focus):
        out.append((f["start_s"], True))
        nxt = focus[i + 1] if i + 1 < len(focus) else None
        if nxt is None or nxt["start_s"] > f["end_s"] + 1e-6:
            out.append((f["end_s"], False))
    return out


def focus_gain(n: int, rate: int, focus: list[dict], key: str, other_db: float, t0: float = 0.0) -> np.ndarray:
    """Gain per sample for one voice: 1 inside its own stretches and in gaps, 10^(other_db/20) where another voice
    has the focus; 10 ms ramps."""
    lo = 10 ** (other_db / 20)
    g = np.ones(n, np.float32)
    for f in focus:
        if f["voice"] == key:
            continue
        a = max(0, int((f["start_s"] - t0) * rate))
        b = min(n, int((f["end_s"] - t0) * rate))
        if b > a:
            g[a:b] = lo
    r = int(0.01 * rate)
    return np.convolve(g, np.ones(r) / r, mode="same").astype(np.float32) if n > r else g


def _norm(x: np.ndarray) -> np.ndarray:
    p = float(np.abs(x).max())
    return x * (HEADROOM / p) if p > HEADROOM else x


def write_previews(prev_dir: Path, mix: np.ndarray, voices: dict[str, np.ndarray], cues: list[dict],
                   focus: list[dict], rate: int, miss: dict) -> list[Path]:
    """mix_clicks_normal.ogg: the recording with a click on every normal cue and a marker at every focus change.
    focus_forward_normal.ogg: the same, with every voice that is not the focus (and the backing) 9 dB down.
    miss_<key>.ogg: 30 s of a drop with the focus voice silent from a cue until its first cue 4 bars later,
    as a run of missed presses makes it in the game.
    miss = {key, start_s, end_s, mute_from_s, mute_to_s}."""
    prev_dir.mkdir(parents=True, exist_ok=True)
    for old in prev_dir.glob("*.ogg"):  # a rerun may name things differently: no stale files
        old.unlink()
    out = []
    p = prev_dir / "mix_clicks_normal.ogg"
    encode_ogg(_norm(add_clicks(mix, rate, cues, focus)), rate, p, out_rate=rate, quality=5)
    out.append(p)
    n = len(mix)
    lo = 10 ** (FORWARD_DB / 20)
    fwd = (mix - sum(voices.values())) * lo  # the backing
    for k, x in voices.items():
        fwd += x * focus_gain(n, rate, focus, k, FORWARD_DB)[:, None]
    # in gaps nothing is forward: everything at full level there
    gap = np.ones(n, bool)
    for f in focus:
        gap[int(f["start_s"] * rate):int(f["end_s"] * rate)] = False
    fwd[gap] = mix[gap]
    p = prev_dir / "focus_forward_normal.ogg"
    encode_ogg(_norm(add_clicks(fwd, rate, cues, focus)), rate, p, out_rate=rate, quality=5)
    out.append(p)
    del fwd
    a, b = int(miss["start_s"] * rate), int(miss["end_s"] * rate)
    seg = mix[a:b].copy()
    m0, m1 = int((miss["mute_from_s"] - miss["start_s"]) * rate), int((miss["mute_to_s"] - miss["start_s"]) * rate)
    fade = int(0.005 * rate)
    env = np.ones(b - a, np.float32)
    env[m0:m1] = 0.0
    env[max(0, m0 - fade):m0] = np.linspace(1, 0, min(fade, m0))
    env[m1:m1 + fade] = np.linspace(0, 1, len(env[m1:m1 + fade]))
    seg = seg - voices[miss["key"]][a:b] * (1 - env)[:, None]
    local = [c for c in cues if miss["start_s"] <= c["t"] < miss["end_s"] - 0.1]
    loc_focus = [f for f in focus if f["end_s"] > miss["start_s"] and f["start_s"] < miss["end_s"]]
    p = prev_dir / f"miss_{miss['key']}.ogg"
    encode_ogg(_norm(add_clicks(seg, rate, local, [f for f in loc_focus if f["start_s"] >= miss["start_s"]],
                                t0=miss["start_s"])), rate, p, out_rate=rate, quality=5)
    out.append(p)
    return out
