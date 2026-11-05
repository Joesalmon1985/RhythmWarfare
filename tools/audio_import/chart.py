"""Stage 5: from each voice's audio to cues a player presses, as three nested charts (easy in normal in hard).

1. events(): what the voice plays. Onsets with strength, refined to the steepest energy rise; for sustained
   kinds (bass, melodic, vocal) also note changes heard as chroma changes, and the note length (how long the
   voice stays within 12 dB of the note's peak before the next note). Every event records how loud the voice is
   there and how loud the voice is against the whole recording, so cues never land where the voice is silent or
   buried.
2. rank(): a score per event: strength, audibility, metric position, and how regularly the same position in the
   2-bar cycle is played across the section (this is what makes patterns repeat when the music repeats). Drum
   events are labelled kick/snare/hat from band energy; the kit's backbone (kick and snare) ranks above hats.
3. select(): per section and voice, the best events up to a budget that depends on the section role and
   difficulty, with a minimum spacing per voice. Hard is chosen from all events, normal from hard, easy from
   normal.
4. resolve(): all four pads together obey the contract's playability rules (checked by the validator's own
   rule function); a conflict keeps the higher-ranked cue, and holds are shortened (or become taps) to make room.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from analysis import band_filter, onset_envelope, pick_onsets, refine_onset
from audio_io import db, frame_rms, mono
from validate_track import playability_violations

DIFFICULTIES = ("hard", "normal", "easy")
# total cues per beat over all four pads in a drop; other roles scale this down
BUDGET = {"hard": 1.15, "normal": 0.62, "easy": 0.32}
ROLE_FACTOR = {"drop": 1.0, "build": 0.7, "other": 0.6, "breakdown": 0.5, "intro": 0.45, "outro": 0.45}
# per voice: max cues per beat and minimum spacing in beats, per difficulty
VOICE_CAP = {"hard": 0.75, "normal": 0.4, "easy": 0.2}
MIN_GAP = {"hard": 0.5, "normal": 0.5, "easy": 1.0}
PRIORITY = {"drums": 1.3, "bass": 1.1, "vocal": 0.9, "melodic": 0.9}
SNAP_MS = 6.0          # an event this close to a 16th grid line is placed on the line
MIN_REL_DB = -24.0     # voice level within 24 dB of the whole recording at the event
MIN_OWN_DB = -30.0     # and within 30 dB of the voice's own loud level
HOLD_MIN_BEATS = 1.0   # a sustained note becomes a hold only if it lasts at least a beat


@dataclass
class Grid:
    bpm: float
    first_downbeat: float
    beats_per_bar: int = 4
    beats: np.ndarray | None = None  # explicit beat times when the tempo is not constant

    @property
    def beat_s(self) -> float:
        return 60.0 / self.bpm

    def position(self, t: np.ndarray) -> np.ndarray:
        """Beats since the first downbeat (float)."""
        if self.beats is not None and len(self.beats) > 1:
            k = np.interp(t, self.beats, np.arange(len(self.beats)), left=np.nan, right=np.nan)
            lo = (t - self.beats[0]) / self.beat_s
            hi = len(self.beats) - 1 + (t - self.beats[-1]) / self.beat_s
            k = np.where(t < self.beats[0], lo, np.where(t > self.beats[-1], hi, k))
            d0 = (self.first_downbeat - self.beats[0]) / self.beat_s
            return k - round(d0)
        return (np.asarray(t) - self.first_downbeat) / self.beat_s

    def time_of(self, pos: np.ndarray) -> np.ndarray:
        if self.beats is not None and len(self.beats) > 1:
            d0 = round((self.first_downbeat - self.beats[0]) / self.beat_s)
            k = np.asarray(pos, dtype=float) + d0
            n = len(self.beats) - 1
            inside = np.interp(k, np.arange(n + 1), self.beats)
            return np.where(k < 0, self.beats[0] + k * self.beat_s,
                            np.where(k > n, self.beats[-1] + (k - n) * self.beat_s, inside))
        return self.first_downbeat + np.asarray(pos) * self.beat_s


@dataclass
class Event:
    t: float
    strength: float
    rel_db: float
    own_db: float
    length: float = 0.0
    kind: str = ""          # kick / snare / hat for drums, onset / change for others
    pos: float = 0.0        # beats since the first downbeat, at the 16th it is nearest
    dev_ms: float = 0.0     # event minus that 16th, ms
    score: float = 0.0
    audible: bool = True
    extra: dict = field(default_factory=dict)


def _level(env_db: np.ndarray, hop_s: float, t: float, span: float) -> float:
    a = int(t / hop_s)
    b = max(a + 1, int((t + span) / hop_s))
    return float(env_db[a:b].max()) if a < len(env_db) else -200.0


def events(x: np.ndarray, mix: np.ndarray, rate: int, kind: str, grid: Grid) -> list[Event]:
    xm = mono(x).astype(np.float32)
    mm = mono(mix).astype(np.float32)
    env = onset_envelope(xm, rate)
    times, strength = pick_onsets(xm, rate, env=env, min_gap=0.06 if kind == "drums" else 0.09)
    hop_s = 0.005
    vdb = db(frame_rms(xm, rate, hop_s, 0.02))
    mdb = db(frame_rms(mm, rate, hop_s, 0.02))
    loud = float(np.percentile(vdb, 95))
    evs: list[Event] = []
    for t, s in zip(times, strength):
        lv = _level(vdb, hop_s, t, 0.06)
        lm = _level(mdb, hop_s, t, 0.06)
        evs.append(Event(t=float(t), strength=float(s), rel_db=lv - lm, own_db=lv - loud, kind="onset"))
    if kind == "drums":
        _label_drums(xm, rate, evs)
    else:
        evs = _add_note_changes(xm, rate, evs, vdb, mdb, loud, hop_s, grid)
        _note_lengths(evs, vdb, hop_s, len(xm) / rate)
    pos = grid.position(np.array([e.t for e in evs])) if evs else np.array([])
    for e, p in zip(evs, pos):
        q = np.round(p * 4) / 4
        e.pos = float(q)
        e.dev_ms = float((p - q) * grid.beat_s * 1000)
        e.audible = e.rel_db >= MIN_REL_DB and e.own_db >= MIN_OWN_DB
    return evs


def _label_drums(xm: np.ndarray, rate: int, evs: list[Event]) -> None:
    """kick / snare / hat from the energy just after each hit in three bands, relative to each band's loud level."""
    bands = {"kick": (None, 150.0), "snare": (150.0, 2500.0), "hat": (5000.0, None)}
    lv = {}
    for name, (lo, hi) in bands.items():
        e = db(frame_rms(band_filter(xm, rate, lo, hi), rate, 0.005, 0.03))
        ref = np.percentile(e, 97)
        lv[name] = np.array([_level(e, 0.005, ev.t, 0.04) for ev in evs]) - ref
    for i, ev in enumerate(evs):
        k, s, h = lv["kick"][i], lv["snare"][i], lv["hat"][i]
        ev.extra = {"kick_db": round(float(k), 1), "snare_db": round(float(s), 1), "hat_db": round(float(h), 1)}
        if k > -9 and k >= s - 3:
            ev.kind = "kick"
        elif s > -9:
            ev.kind = "snare"
        else:
            ev.kind = "hat"


def _add_note_changes(xm, rate, evs, vdb, mdb, loud, hop_s, grid: Grid) -> list[Event]:
    """Legato note changes have no attack: add chroma-change peaks that are not near an onset, placed on the
    nearest 16th when within 40 ms of it (the change itself has no sharp edge to place it on)."""
    import librosa
    hop = 1024
    C = librosa.feature.chroma_stft(y=xm, sr=rate, n_fft=8192, hop_length=hop)
    e = np.sqrt((C ** 2).sum(0)) + 1e-9
    Cn = C / e
    nov = np.r_[0.0, 1.0 - (Cn[:, 1:] * Cn[:, :-1]).sum(0)]
    nov = np.convolve(nov, np.ones(3) / 3, mode="same")
    fps = rate / hop
    rms = librosa.feature.rms(y=xm, frame_length=2048, hop_length=hop)[0]
    nov[db(rms) < loud - 25] = 0.0
    pk = librosa.util.peak_pick(nov, pre_max=4, post_max=4, pre_avg=12, post_avg=4,
                                delta=max(0.05, float(np.percentile(nov, 90))), wait=int(0.15 * fps))
    ts = np.array([e.t for e in evs])
    out = list(evs)
    for k in pk:
        t = k / fps
        if len(ts) and np.min(np.abs(ts - t)) < 0.08:
            continue
        p = grid.position(np.array([t]))[0]
        q = round(p * 4) / 4
        tq = float(grid.time_of(np.array([q]))[0])
        if abs(tq - t) < 0.04:
            t = tq
        lv = _level(vdb, hop_s, t, 0.06)
        lm = _level(mdb, hop_s, t, 0.06)
        out.append(Event(t=t, strength=float(min(1.0, nov[k] / (np.percentile(nov, 99) or 1.0))) * 0.8,
                         rel_db=lv - lm, own_db=lv - loud, kind="change"))
    out.sort(key=lambda e: e.t)
    return out


def _note_lengths(evs: list[Event], vdb: np.ndarray, hop_s: float, dur: float) -> None:
    for i, e in enumerate(evs):
        nxt = evs[i + 1].t if i + 1 < len(evs) else dur
        a = int(e.t / hop_s)
        b = max(a + 1, int(nxt / hop_s))
        seg = vdb[a:b]
        if not len(seg):
            continue
        peak = seg[: max(1, int(0.08 / hop_s))].max()
        below = np.nonzero(seg < peak - 12.0)[0]
        # ignore dips shorter than 40 ms
        end = len(seg)
        for j in below:
            if np.all(seg[j:j + int(0.04 / hop_s)] < peak - 12.0):
                end = j
                break
        e.length = float(end * hop_s)


# ---------------------------------------------------------------- ranking

def metric_weight(pos: float, dev_ms: float) -> float:
    if abs(dev_ms) > 40:
        return 0.3
    f = pos % 4
    if abs(f) < 1e-6:
        return 1.0
    if abs(f - 2) < 1e-6:
        return 0.9
    if abs(f - round(f)) < 1e-6:
        return 0.8
    if abs(f * 2 - round(f * 2)) < 1e-6:
        return 0.6
    return 0.4


def rank(evs: list[Event], kind: str, sections: list[dict], beats_per_bar: int = 4) -> None:
    """Score every event 0..1 (see module doc)."""
    if not evs:
        return
    s = np.array([e.strength for e in evs])
    r = np.array([e.rel_db for e in evs])
    s_pct = np.argsort(np.argsort(s)) / max(len(s) - 1, 1)
    r_pct = np.argsort(np.argsort(r)) / max(len(r) - 1, 1)
    cycle = 2 * beats_per_bar * 4  # 16ths in a 2-bar cycle
    sec_of = _section_index(evs, sections)
    recur = np.zeros(len(evs))
    for si in set(sec_of):
        idx = [i for i, x in enumerate(sec_of) if x == si]
        if not idx:
            continue
        slots = np.array([int(round(evs[i].pos * 4)) % cycle for i in idx])
        cycles = np.array([int(np.floor(evs[i].pos * 4 / cycle)) for i in idx])
        n_cycles = max(1, cycles.max() - cycles.min() + 1)
        hist = np.zeros(cycle)
        for sl, i in zip(slots, idx):
            hist[sl] += min(1.0, evs[i].strength) if evs[i].audible else 0.0
        hist = hist / n_cycles
        for sl, i in zip(slots, idx):
            recur[i] = min(1.0, hist[sl])
    prev_t = -10.0
    for i, e in enumerate(evs):
        m = metric_weight(e.pos, e.dev_ms)
        if kind == "drums":
            bonus = {"kick": 1.0, "snare": 1.0, "hat": 0.3}.get(e.kind, 0.5)
            score = 0.25 * s_pct[i] + 0.10 * r_pct[i] + 0.35 * recur[i] + 0.15 * m + 0.15 * bonus
        else:
            phrase = 1.0 if e.t - prev_t > 0.6 else 0.0
            held = min(1.0, e.length / 0.7)
            score = 0.30 * s_pct[i] + 0.15 * r_pct[i] + 0.25 * recur[i] + 0.10 * m + 0.10 * phrase + 0.10 * held
        if e.kind == "change":
            score *= 0.9
        e.score = float(score)
        e.extra["recur"] = round(float(recur[i]), 3)
        if e.audible:
            prev_t = e.t


def _section_index(evs: list[Event], sections: list[dict]) -> list[int]:
    out = []
    for e in evs:
        k = 0
        for i, s in enumerate(sections):
            if s["start_s"] <= e.t < s["end_s"]:
                k = i
                break
        out.append(k)
    return out


# ---------------------------------------------------------------- selection

@dataclass
class Cue:
    t: float
    pad: int
    dur: float
    conf: float
    score: float
    voice: str
    natural: float = 0.0  # note length before any shortening
    ev: Event | None = None

    def as_json(self) -> dict:
        return {"t": round(self.t, 4), "pad": self.pad, "dur": round(self.dur, 3), "conf": round(self.conf, 2)}


def cue_time(e: Event, grid: Grid) -> float:
    if abs(e.dev_ms) <= SNAP_MS:
        return float(grid.time_of(np.array([e.pos]))[0])
    return e.t


def confidence(e: Event, sep_quality: float) -> float:
    a = np.clip((e.rel_db - MIN_REL_DB) / 18.0, 0, 1)
    g = 1.0 if abs(e.dev_ms) <= 15 else 0.6
    return float(np.clip(0.15 + 0.3 * sep_quality + 0.25 * min(1.0, e.strength) + 0.2 * a + 0.1 * g, 0, 1))


def select(voice_events: dict[str, list[Event]], pads: dict[str, int], kinds: dict[str, str],
           sections: list[dict], grid: Grid, duration: float, sep_quality: dict[str, float],
           pool: dict[str, set] | None, diff: str) -> list[Cue]:
    """Pick cues per section and voice up to the budget, best score first, keeping the voice's own spacing.
    pool (voice -> event times allowed) restricts the choice to a harder chart's cues."""
    B = grid.beat_s
    chosen: list[Cue] = []
    for sec in sections:
        beats = (sec["end_s"] - sec["start_s"]) / B
        total = BUDGET[diff] * ROLE_FACTOR.get(sec["role"], 0.6) * beats
        avail = {}
        for v, evs in voice_events.items():
            ok = [e for e in evs if e.audible and sec["start_s"] <= e.t < sec["end_s"]
                  and 1.0 <= e.t <= duration - 0.6 and (pool is None or round(e.t, 4) in pool[v])]
            avail[v] = ok
        w = {v: PRIORITY.get(kinds[v], 1.0) * np.sqrt(len(ok) / max(beats, 1)) for v, ok in avail.items()}
        wsum = sum(w.values()) or 1.0
        for v, ok in avail.items():
            quota = int(round(min(total * w[v] / wsum, VOICE_CAP[diff] * beats)))
            picked: list[float] = []
            for e in sorted(ok, key=lambda e: -e.score):
                if len(picked) >= quota:
                    break
                if all(abs(e.t - p) >= MIN_GAP[diff] * B - 1e-6 for p in picked):
                    picked.append(e.t)
                    t = cue_time(e, grid)
                    chosen.append(Cue(t=t, pad=pads[v], dur=0.0, conf=confidence(e, sep_quality.get(v, 0.5)),
                                      score=e.score, voice=v, natural=e.length, ev=e))
    chosen.sort(key=lambda c: (c.t, c.pad))
    return chosen


def resolve(cues: list[Cue], beat_s: float, duration: float, hold_kinds: set[str], kinds: dict[str, str]) -> list[Cue]:
    """Make the chart playable across all pads: taps first in score order, then holds as long as the rules and
    the note allow, then a final check with the validator's rule function, dropping the lowest-scored offender
    until there is nothing to drop."""
    B = beat_s
    keep: list[Cue] = []
    for c in sorted(cues, key=lambda c: -c.score):
        c.dur = 0.0
        if not playability_violations([x.as_json() for x in sorted(keep + [c], key=lambda x: (x.t, x.pad))], 60.0 / B):
            keep.append(c)
    keep.sort(key=lambda c: (c.t, c.pad))
    # holds
    for i, c in enumerate(keep):
        if kinds.get(c.voice) not in hold_kinds or c.natural < HOLD_MIN_BEATS * B:
            continue
        limit = min(c.natural, duration - 0.5 - c.t)
        thumb = (c.pad - 1) // 2
        for d in keep[i + 1:]:
            if d.pad == c.pad:
                limit = min(limit, d.t - c.t - 0.25 * B - 0.005)
                break
        for d in keep[i + 1:]:
            if d.pad != c.pad and (d.pad - 1) // 2 == thumb:
                limit = min(limit, d.t - c.t - 0.005)
                break
        if limit >= max(0.5 * B, HOLD_MIN_BEATS * B * 0.75):
            c.dur = float(np.floor(limit * 100) / 100)
    for _ in range(len(keep) + 1):
        v = playability_violations([x.as_json() for x in keep], 60.0 / B)
        if not v:
            break
        idx = {i for (i, _msg) in v}
        worst = min(idx, key=lambda i: keep[i].score)
        if keep[worst].dur > 0:
            keep[worst].dur = 0.0
        else:
            keep.pop(worst)
    return keep


def build_charts(voice_events: dict[str, list[Event]], pads: dict[str, int], kinds: dict[str, str],
                 sections: list[dict], grid: Grid, duration: float, sep_quality: dict[str, float]) -> dict[str, list[Cue]]:
    hold_kinds = {"bass", "melodic", "vocal"}
    charts: dict[str, list[Cue]] = {}
    pool = None
    for diff in DIFFICULTIES:
        cues = select(voice_events, pads, kinds, sections, grid, duration, sep_quality, pool, diff)
        cues = resolve(cues, grid.beat_s, duration, hold_kinds, kinds)
        charts[diff] = cues
        pool = {v: {round(c.ev.t, 4) for c in cues if c.voice == v} for v in voice_events}
    return charts
