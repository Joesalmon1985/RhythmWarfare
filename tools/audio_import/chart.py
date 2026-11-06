"""From each voice's audio to the cues a player presses (track pack format v2: all four pads play the focus voice).

1. events(): what a voice plays. Onsets with strength, refined to the steepest energy rise; for sustained kinds
   (bass, melodic, vocal) also note changes and note lengths. Every event records how loud the voice is there and
   against the whole recording, so cues never land where the voice is silent or buried.
2. describe(): how high each event is. Pitched parts by pitch (the bass by its tracked note, other parts by the
   predominant pitch of a harmonic-summed constant-Q spectrum just after the attack); drum hits by how low or
   bright they are (the spectral centroid of the first 40 ms, plus the low / mid / high band balance used to tell
   one drum sound from another). Nothing is named.
3. rank(): a score per event: strength, audibility, metric position, and how regularly the same position in the
   cycle is played across the stretch (this is what makes patterns repeat when the music repeats).
4. build_charts(): per focus stretch, the strongest recurring positions of the focus voice up to a budget per
   difficulty (pattern_pick), laid across the pads by height (layout.py), then made playable across the whole
   chart with the validator's own rule function. Hard is chosen from all events, normal from hard, easy from
   normal; the pad of an event is decided once, from the hard selection, so the three charts agree.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from analysis import band_filter, onset_envelope, pick_onsets
from audio_io import db, frame_rms, mono
from validate_track import playability_violations

DIFFICULTIES = ("hard", "normal", "easy")
# cues per beat for the focus voice in a drop; other section roles scale this down. Normal drums at 1.0 is the
# kick and snare of a two-step bar (four hits); hard adds the hats and ghost notes.
RATE = {"hard": {"drums": 1.75, "pitched": 1.25}, "normal": {"drums": 1.0, "pitched": 0.75},
        "easy": {"drums": 0.5, "pitched": 0.4}}
ROLE_FACTOR = {"drop": 1.0, "build": 0.9, "other": 0.85, "breakdown": 0.8, "intro": 0.75, "outro": 0.75}
# minimum spacing in beats between two picked events of the part (two thumbs: hard may ask for 16ths that
# alternate thumbs; the layout and resolve() keep one thumb at half a beat or more)
MIN_GAP = {"hard": 0.25, "normal": 0.5, "easy": 1.0}
CYCLE_BEATS = {"drums": 4, "bass": 8, "melodic": 16, "vocal": 16}
SNAP_MS = 6.0          # an event this close to a 16th grid line is placed on the line
MIN_REL_DB = -24.0     # voice level within 24 dB of the whole recording at the event
MIN_OWN_DB = -30.0     # and within 30 dB of the voice's own loud level
MIN_ATTACK = 0.4       # melodic/vocal onsets weaker than this (flux / the voice's 99th pct) are not cued: on
                       # Go Back only 14-27% of those below 0.3 were confirmed by an independent onset detector,
                       # 70-98% of those at 0.4 and above
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
    height: float = float("nan")  # pitch (MIDI) or, for drum hits, log2 of the attack's spectral centroid
    feat: list = field(default_factory=list)  # what tells one sound from another (see describe())

    def to_json(self) -> dict:
        return {"t": round(self.t, 4), "s": round(self.strength, 3), "rel": round(self.rel_db, 1),
                "own": round(self.own_db, 1), "len": round(self.length, 3), "kind": self.kind, "pos": self.pos,
                "dev": round(self.dev_ms, 1), "aud": self.audible,
                "h": None if not np.isfinite(self.height) else round(self.height, 2),
                "f": [round(float(v), 1) for v in self.feat], "x": self.extra}

    @staticmethod
    def from_json(d: dict) -> "Event":
        return Event(t=d["t"], strength=d["s"], rel_db=d["rel"], own_db=d["own"], length=d["len"], kind=d["kind"],
                     pos=d["pos"], dev_ms=d["dev"], audible=d["aud"], extra=dict(d.get("x", {})),
                     height=float("nan") if d.get("h") is None else d["h"], feat=list(d.get("f", [])))


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
    elif kind == "bass":
        evs = bass_notes(xm, rate, times, vdb, mdb, loud, hop_s, grid)
    else:
        evs = _add_note_changes(xm, rate, evs, vdb, mdb, loud, hop_s, grid)
        _note_lengths(evs, vdb, hop_s, len(xm) / rate)
    pos = grid.position(np.array([e.t for e in evs])) if evs else np.array([])
    for e, p in zip(evs, pos):
        q = np.round(p * 4) / 4
        e.pos = float(q)
        e.dev_ms = float((p - q) * grid.beat_s * 1000)
        e.audible = e.rel_db >= MIN_REL_DB and e.own_db >= MIN_OWN_DB
        if kind in ("melodic", "vocal") and e.kind == "onset" and e.strength < MIN_ATTACK:
            e.audible = False  # sounding, but no clear attack to press on (filter movement inside a held sound)
    return evs


def _label_drums(xm: np.ndarray, rate: int, evs: list[Event]) -> None:
    """kick / snare / hat from the energy just after each hit in three bands, each relative to that band's
    loudest moment within 5 s (so a quieter intro kit is judged on its own terms). The 150-2500 Hz band holds
    the kick's body as well as the snare, so a kick is a hit whose sub band is near its local peak and not far
    below its body band; a snare is loud in both the body and the top; everything else is a hat or ghost."""
    from scipy.ndimage import maximum_filter1d
    bands = {"kick": (None, 150.0), "snare": (150.0, 2500.0), "hat": (5000.0, None)}
    hop = 0.005
    lv = {}
    for name, (lo, hi) in bands.items():
        e = db(frame_rms(band_filter(xm, rate, lo, hi), rate, hop, 0.03))
        ref = maximum_filter1d(e, size=int(10.0 / hop), mode="nearest")
        lv[name] = np.array([_level(e, hop, ev.t, 0.04) - ref[min(int(ev.t / hop), len(ref) - 1)] for ev in evs])
    for i, ev in enumerate(evs):
        k, s, h = lv["kick"][i], lv["snare"][i], lv["hat"][i]
        ev.extra = {"kick_db": round(float(k), 1), "snare_db": round(float(s), 1), "hat_db": round(float(h), 1)}
        if k > -10 and k - s > -8:
            ev.kind = "kick"
        elif s > -12 and h > -12:
            ev.kind = "snare"
        else:
            ev.kind = "hat"


def bass_notes(xm, rate, onsets, vdb, mdb, loud, hop_s, grid: Grid) -> list[Event]:
    """Notes of a bass line by pitch (pyin at 11 kHz, 23 ms frames), not by amplitude: a held sub or reese
    pumps with the kick's sidechain, and those swells are not notes. A note starts where the pitch moves by
    at least 0.75 semitone and stays there for 70 ms, or where the bass comes back after a rest; a glide
    counts once, at its start. The start is placed on an amplitude attack within 15 ms if there is one,
    else on the 16th line within 40 ms (a legato change has no edge), else where the pitch changed. Length
    runs to the next note or rest."""
    import librosa
    sr = 11025
    hop = 256
    y = librosa.resample(xm, orig_sr=rate, target_sr=sr)
    f0, voiced, _ = librosa.pyin(y, fmin=28, fmax=400, sr=sr, frame_length=2048, hop_length=hop)
    fr = hop / sr
    midi = librosa.hz_to_midi(np.where(voiced, f0, np.nan))
    lvl = np.array([_level(vdb, hop_s, k * fr, fr) for k in range(len(midi))])
    on = (lvl >= loud - 25) & ~np.isnan(midi)
    from scipy.ndimage import median_filter
    m = median_filter(np.nan_to_num(midi, nan=0.0), size=3)
    stable = int(round(0.07 / fr))
    notes = []  # [start_frame, end_frame, pitch]
    cur = None
    k = 0
    while k < len(m):
        if not on[k]:
            if cur:
                cur[1] = k
                notes.append(cur)
                cur = None
            k += 1
            continue
        if cur is None:
            cur = [k, k + 1, m[k]]
        else:
            ref = float(np.median(m[max(cur[0], k - 13):k]))  # the note's pitch over the last 0.3 s follows slow drift
            seg = m[k:k + stable]
            if (abs(m[k] - ref) >= 0.9 and len(seg) == stable and np.ptp(seg) < 0.75 and on[k:k + stable].all()
                    and abs(float(np.median(seg)) - ref) >= 0.9 and abs(m[min(k + 1, len(m) - 1)] - m[max(k - 2, 0)]) >= 0.9):
                cur[1] = k
                notes.append(cur)
                cur = [k, k + 1, float(np.median(seg))]
            # else a glide, a wobble or a detuned reese drifting: it stays inside the current note
        k += 1
    if cur:
        cur[1] = len(m)
        notes.append(cur)
    evs = []
    for a, b, p in notes:
        t = max(0.0, (a - 0.5) * fr)
        if (b - a) * fr < 0.06:
            continue
        near = onsets[np.abs(onsets - t) <= 0.015] if len(onsets) else []
        if len(near):
            t = float(near[np.argmin(np.abs(near - t))])
        else:
            q = round(grid.position(np.array([t]))[0] * 4) / 4
            tq = float(grid.time_of(np.array([q]))[0])
            if abs(tq - t) <= 0.04:
                t = max(0.0, tq)  # a grid line before the start of the file is not a time
        lv = _level(vdb, hop_s, t, 0.08)
        lm = _level(mdb, hop_s, t, 0.08)
        e = Event(t=t, strength=float(np.clip((lv - loud + 20) / 20, 0, 1.2)), rel_db=lv - lm, own_db=lv - loud,
                  kind="note", length=float(b * fr - t))
        e.extra["pitch"] = round(float(p), 1)
        evs.append(e)
    return evs


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


# ---------------------------------------------------------------- height

SAL_BPO = 36  # constant-Q bins per octave for the pitch salience


def _salience(xm: np.ndarray, rate: int) -> tuple[np.ndarray, float, float]:
    """Harmonic-summed constant-Q magnitude (C1 up, 8 octaves, 1/3 semitone): (salience, frames per s, MIDI of bin 0).
    The bin with the most salience is the predominant pitch: robust on chords and stabs as well as single lines."""
    import librosa
    sr = 22050
    hop = 256
    y = librosa.resample(xm.astype(np.float32), orig_sr=rate, target_sr=sr)
    fmin = float(librosa.note_to_hz("C1"))
    C = np.abs(librosa.cqt(y, sr=sr, hop_length=hop, fmin=fmin, n_bins=SAL_BPO * 8, bins_per_octave=SAL_BPO))
    sal = np.zeros_like(C)
    for h, w in ((1, 1.0), (2, 0.8), (3, 0.6), (4, 0.5), (5, 0.4)):
        off = int(round(SAL_BPO * np.log2(h)))
        sal[: C.shape[0] - off] += w * C[off:]
    return sal, sr / hop, float(librosa.hz_to_midi(fmin))


def describe(evs: list[Event], x: np.ndarray, rate: int, kind: str) -> None:
    """Set height and feat of every event (module doc, step 2)."""
    if not evs:
        return
    xm = mono(x).astype(np.float32)
    if kind == "drums":
        import librosa
        hop = 256
        S = np.abs(librosa.stft(xm, n_fft=2048, hop_length=hop)) ** 2
        f = librosa.fft_frequencies(sr=rate, n_fft=2048)
        fps = rate / hop
        lo, mid, hi = f < 150, (f >= 150) & (f < 2500), f >= 5000
        for e in evs:
            a = int(round(e.t * fps))
            p = S[:, a:a + max(1, int(0.04 * fps))].mean(1) + 1e-12
            tot = p.sum()
            e.height = float(np.log2((p * f).sum() / tot + 1.0))
            lv = [10 * np.log10(p[m].sum() / tot) for m in (lo, mid, hi)]
            # band balance against the mid band: kick-like hits are high on the first, hat-like on the second
            e.feat = [float(np.clip(lv[0] - lv[1], -40, 40)), float(np.clip(lv[2] - lv[1], -40, 40))]
        return
    if kind == "bass":
        for e in evs:
            p = e.extra.get("pitch")
            if p:
                e.height = float(p)
                e.feat = [float(p)]
        return
    sal, fps, m0 = _salience(xm, rate)
    for e in evs:
        a = int((e.t + 0.02) * fps)
        b = max(a + 1, int((e.t + 0.10) * fps) + 1)
        if a >= sal.shape[1]:
            continue
        v = sal[:, a:b].mean(1)
        if v.max() <= 0:
            continue
        e.height = float(m0 + int(np.argmax(v)) / (SAL_BPO / 12))
        e.feat = [e.height]


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
    """Score every event 0..1 (see module doc). sections: the spans over which recurrence is counted (the
    voice's focus stretches)."""
    if not evs:
        return
    s = np.array([e.strength for e in evs])
    r = np.array([e.rel_db for e in evs])
    s_pct = np.argsort(np.argsort(s)) / max(len(s) - 1, 1)
    r_pct = np.argsort(np.argsort(r)) / max(len(r) - 1, 1)
    cycle = 2 * beats_per_bar * 4  # 16ths in a 2-bar cycle
    sec_of = _section_index(evs, sections)
    recur = np.zeros(len(evs))
    for si in set(sec_of) - {-1}:  # events outside every section (stretch) get no recurrence
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
            # the kit's backbone first: the low and the mid hits (kick- and snare-like by band level) carry the
            # pattern of the bar; bright hits (hats) are what hard adds. Weighted above metric position so an
            # off-beat kick (the "and" of 3 in a two-step) beats a hat on the beat.
            bonus = {"snare": 1.0, "kick": 0.9, "hat": 0.2}.get(e.kind, 0.5)
            score = 0.25 * s_pct[i] + 0.10 * r_pct[i] + 0.30 * recur[i] + 0.10 * m + 0.25 * bonus
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
        k = -1
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
    natural: float = 0.0  # how long the note sounds (capped at the end of its focus stretch)
    ev: Event | None = None
    prio: float = 0.0     # decides playability conflicts: the higher survives
    stretch: int = -1

    def as_json(self) -> dict:
        return {"t": round(self.t, 4), "pad": self.pad, "dur": round(self.dur, 3), "conf": round(self.conf, 2),
                "voice": self.voice}


def cue_time(e: Event, grid: Grid) -> float:
    if abs(e.dev_ms) <= SNAP_MS:
        return float(grid.time_of(np.array([e.pos]))[0])
    return e.t


def confidence(e: Event, sep_quality: float) -> float:
    a = np.clip((e.rel_db - MIN_REL_DB) / 18.0, 0, 1)
    g = 1.0 if abs(e.dev_ms) <= 15 else 0.6
    return float(np.clip(0.15 + 0.3 * sep_quality + 0.25 * min(1.0, e.strength) + 0.2 * a + 0.1 * g, 0, 1))


def pattern_pick(evs: list[Event], quota: int, gap_beats: float, cycle_beats: int, B: float) -> list[Event]:
    """Choose positions in the repeating cycle (1 bar for drums, 2 for bass, 4 for melodic and vocal parts),
    best first by how strongly and how regularly the part plays there (summed score / number of cycles), then
    take every event at those positions: the same pattern in every cycle where the part plays it. Positions
    closer than gap_beats (cyclically) are not combined. Leftover budget goes to the best remaining events
    (accents and one-off phrases), still keeping gap_beats between picked events."""
    if quota <= 0 or not evs:
        return []
    n16 = cycle_beats * 4
    gap16 = int(round(gap_beats * 4))
    by_slot: dict[int, list[Event]] = {}
    for e in evs:
        by_slot.setdefault(int(round(e.pos * 4)) % n16, []).append(e)
    first = min(e.pos for e in evs)
    last = max(e.pos for e in evs)
    n_cycles = max(1.0, (last - first) / cycle_beats)
    slot_score = {sl: sum(e.score for e in es) / n_cycles for sl, es in by_slot.items()}
    chosen_slots: list[int] = []
    count = 0
    for sl in sorted(slot_score, key=lambda k: (-slot_score[k], k)):
        if count >= quota:
            break
        if any(min((sl - c) % n16, (c - sl) % n16) < gap16 for c in chosen_slots):
            continue
        if count + len(by_slot[sl]) > quota * 1.2 and count > 0:
            continue
        chosen_slots.append(sl)
        count += len(by_slot[sl])
    picked: list[Event] = []
    for e in sorted((e for sl in chosen_slots for e in by_slot[sl]), key=lambda e: (-e.score, e.t)):
        if all(abs(e.t - p.t) >= gap_beats * B - 1e-6 for p in picked):
            picked.append(e)
    for e in sorted(evs, key=lambda e: (-e.score, e.t)):
        if len(picked) >= quota:
            break
        if e not in picked and all(abs(e.t - p.t) >= gap_beats * B - 1e-6 for p in picked):
            picked.append(e)
    return sorted(picked, key=lambda e: e.t)


def stretch_role(st: dict, sections: list[dict]) -> str:
    best, role = 0.0, "other"
    for s in sections:
        ov = min(st["end_s"], s["end_s"]) - max(st["start_s"], s["start_s"])
        if ov > best:
            best, role = ov, s["role"]
    return role


def stretch_events(evs: list[Event], st: dict, duration: float, B: float) -> list[Event]:
    """Audible events of the stretch's voice that can carry a cue: inside the stretch (not in its last quarter
    beat, so even a tap belongs to it), after the first second and before the last 0.6 s."""
    return [e for e in evs if e.audible and st["start_s"] <= e.t < st["end_s"] - 0.25 * B
            and 1.0 <= e.t <= duration - 0.6]


# ceilings in cues per beat of focus time (Go Back, the reference chart, is under all of them): per stretch, by
# kind, in a drop (other section roles scale by ROLE_FACTOR); and over the whole chart, where the densest
# stretches are thinned (by score, whole positions of the cycle first) until the chart is under it
CAP = {"hard": {"drums": 1.45, "pitched": 1.0}, "normal": {"drums": 1.0, "pitched": 0.75},
       "easy": {"drums": 0.5, "pitched": 0.45}}
CEILING = {"hard": 0.84, "normal": 0.67, "easy": 0.41}
ONE_PAD_MIN = 4  # a stretch with at least this many cues, all on one pad, is spread over two (spread_one_pad)


def apply_relaxed(voice_events: dict[str, list[Event]], focus: list[dict]) -> int:
    """Mark as audible the events that the focus stage counted as playable under its relaxed rules (focus.py,
    rule 6) in the units of a stretch where it used them; returns how many were marked."""
    from focus import relaxed_playable
    n = 0
    for st in focus:
        for a, b in st.get("relaxed_spans") or []:
            for e in relaxed_playable([e for e in voice_events[st["voice"]] if a <= e.t < b]):
                if not e.audible:
                    e.audible = True
                    e.extra["relaxed"] = True
                    n += 1
    return n


def _water_cap(counts: list[int], beats: list[float], ceiling: float) -> float | None:
    """The largest per-beat cap X with sum(min(n_i, X * beats_i)) <= ceiling * sum(beats), or None if the
    chart is already under the ceiling."""
    total = ceiling * sum(beats)
    if sum(counts) <= total:
        return None
    lo, hi = 0.0, max(n / b for n, b in zip(counts, beats) if b > 0)
    for _ in range(40):
        mid = (lo + hi) / 2
        if sum(min(n, mid * b) for n, b in zip(counts, beats)) > total:
            hi = mid
        else:
            lo = mid
    return lo


def spread_one_pad(cues: list["Cue"]) -> tuple[list["Cue"], int]:
    """A stretch whose cues (at least ONE_PAD_MIN) all sit on one pad is spread over two by position in the bar:
    off the beat, else beats 2 and 4, else the second half of the bar, go to the inner pad of the other thumb
    when the part is on the left thumb (they are the higher side), or the on-beat side goes to the inner pad of
    the left thumb when it is on the right. Position in the bar decides, so a repeated phrase gets the same pads.
    Returns the cues and how many stretches were spread."""
    by: dict[int, list[Cue]] = {}
    for c in cues:
        by.setdefault(c.stretch, []).append(c)
    n = 0
    for si, cs in by.items():
        pads = {c.pad for c in cs}
        if len(cs) < ONE_PAD_MIN or len(pads) != 1:
            continue
        pad = pads.pop()
        pos = np.array([c.ev.pos if c.ev is not None else 0.0 for c in cs])
        for side in (np.abs(pos - np.round(pos)) > 1e-6, (np.floor(pos + 1e-6) % 2) == 1, (pos % 4) >= 2 - 1e-6):
            if 0.2 <= side.mean() <= 0.8:
                break
        else:
            side = np.arange(len(cs)) % 2 == 1  # no metric contrast at all: every other cue
        for c, hi in zip(cs, side):
            if pad <= 2 and hi:
                c.pad = 3
            elif pad >= 3 and not hi:
                c.pad = 2
        n += 1
    return cues, n


def build_charts(voice_events: dict[str, list[Event]], focus: list[dict], kinds: dict[str, str],
                 sections: list[dict], grid: Grid, duration: float, sep_quality: dict[str, float],
                 sound_check=None, stats: dict | None = None) -> tuple[dict[str, list[Cue]], list[dict]]:
    """Charts easy / normal / hard and, per stretch, the pad layout (see layout.py) with its reasons.

    sound_check(cue_json) -> problem or None: the validator's audibility test (validate_track.SoundLevels);
    every cue that fails it is removed (holds first become taps) and counted in stats["sound_check_removed"]."""
    from layout import layout_stretch
    B = grid.beat_s
    charts: dict[str, list[Cue]] = {}
    layouts: list[dict] = []
    pad_of: dict[tuple[int, float], int] = {}
    pool: set | None = None
    stats = stats if stats is not None else {}
    stats.setdefault("sound_check_removed", {})
    stats.setdefault("sound_check_shortened", {})
    stats.setdefault("ceiling_cap_per_beat", {})
    stats.setdefault("one_pad_spread", {})
    beats_of = [(st["end_s"] - st["start_s"]) / B for st in focus]
    for diff in DIFFICULTIES:
        cand: dict[int, list[Event]] = {}
        quota0: dict[int, float] = {}
        cap0: dict[int, float] = {}
        for si, st in enumerate(focus):
            v = st["voice"]
            kind = kinds[v]
            fam = "drums" if kind == "drums" else "pitched"
            cand[si] = [e for e in stretch_events(voice_events[v], st, duration, B)
                        if pool is None or (si, round(e.t, 4)) in pool]
            role = ROLE_FACTOR.get(stretch_role(st, sections), 0.85)
            quota0[si] = RATE[diff][fam] * role * beats_of[si]
            cap0[si] = CAP[diff][fam] * beats_of[si]

        def build(limits: dict[int, float]) -> list[Cue]:
            cues: list[Cue] = []
            for si, st in enumerate(focus):
                v = st["voice"]
                cyc = CYCLE_BEATS.get(kinds[v], 8)
                q = quota0[si] if si not in limits else min(quota0[si], np.floor(limits[si] + 1e-9))
                picked = pattern_pick(cand[si], int(round(q)), MIN_GAP[diff], cyc, B)
                if si in limits and len(picked) > limits[si] + 1e-9:  # the 1.2 slack of pattern_pick: by score
                    n = int(np.floor(limits[si] + 1e-9))
                    drop = {id(e) for e in sorted(picked, key=lambda e: (e.score, -e.t))[:len(picked) - n]}
                    picked = [e for e in picked if id(e) not in drop]
                if diff == "hard":
                    lay = layout_stretch(picked, kinds[v], B)
                    lay["stretch"] = si
                    lays[si] = lay
                    for e, p in zip(picked, lay["pads"]):
                        pad_of[(si, round(e.t, 4))] = p
                for e in picked:
                    cues.append(Cue(t=cue_time(e, grid), pad=pad_of[(si, round(e.t, 4))], dur=0.0,
                                    conf=confidence(e, sep_quality.get(v, 0.5)), score=e.score, voice=v,
                                    natural=max(0.0, min(e.length, st["end_s"] - 0.01 - cue_time(e, grid))),
                                    ev=e, prio=e.score, stretch=si))
            cues.sort(key=lambda c: (c.t, c.pad))
            return resolve(cues, B, duration, {"bass", "melodic", "vocal"}, kinds)

        lays: dict[int, dict] = {}
        limits: dict[int, float] = {}
        cues = build(limits)
        for _ in range(3):
            # ceilings, judged on the playable chart: each stretch under its cap, the chart under CEILING
            counts = [0] * len(focus)
            for c in cues:
                counts[c.stretch] += 1
            new = {si: cap0[si] for si in range(len(focus)) if counts[si] > cap0[si] + 1e-9}
            capped = [min(n, cap0[si]) for si, n in enumerate(counts)]
            x = _water_cap(capped, beats_of, CEILING[diff])
            if x is not None:
                for si in range(len(focus)):
                    if counts[si] > x * beats_of[si] + 1e-9:
                        new[si] = min(new.get(si, cap0[si]), x * beats_of[si], limits.get(si, np.inf))
            new = {si: v for si, v in new.items() if v < limits.get(si, np.inf) - 1e-9 or si not in limits}
            if not new:
                break
            limits.update(new)
            cues = build(limits)
        stats["ceiling_cap_per_beat"][diff] = {str(si): round(v / beats_of[si], 3) for si, v in limits.items()}
        if diff == "hard":
            layouts = [lays[si] for si in sorted(lays)]
        cues, stats["one_pad_spread"][diff] = spread_one_pad(cues)
        if stats["one_pad_spread"][diff]:
            cues.sort(key=lambda c: (c.t, c.pad))
            cues = resolve(cues, B, duration, {"bass", "melodic", "vocal"}, kinds)
        if sound_check is not None:
            cues, removed, shortened = self_check(cues, sound_check)
            stats["sound_check_removed"][diff] = removed
            stats["sound_check_shortened"][diff] = shortened
        charts[diff] = cues
        pool = {(c.stretch, round(c.ev.t, 4)) for c in cues}
    for lay in layouts:
        lay.pop("pads", None)
    return charts, layouts


def self_check(cues: list[Cue], sound_check) -> tuple[list[Cue], int, int]:
    """The last word before a chart is written: every cue must pass the validator's audibility test. A hold
    that fails becomes a tap and is tested again; a tap that fails is removed. Removing a cue or shortening a
    hold never breaks a playability rule. Returns (cues, removed, shortened)."""
    keep, removed, shortened = [], 0, 0
    for c in cues:
        if sound_check(c.as_json()) is None:
            keep.append(c)
            continue
        if c.dur > 0:
            c.dur = 0.0
            if sound_check(c.as_json()) is None:
                keep.append(c)
                shortened += 1
                continue
        removed += 1
    return keep, removed, shortened


def resolve(cues: list[Cue], beat_s: float, duration: float, hold_kinds: set[str], kinds: dict[str, str]) -> list[Cue]:
    """Make the chart playable across all pads: taps first in score order, then holds as long as the rules and
    the note allow, then a final check with the validator's rule function, dropping the lowest-scored offender
    until there is nothing to drop."""
    B = beat_s
    keep: list[Cue] = []
    for c in sorted(cues, key=lambda c: (-c.prio, c.t)):
        c.dur = 0.0
        if not playability_violations([x.as_json() for x in sorted(keep + [c], key=lambda x: (x.t, x.pad))], 60.0 / B):
            keep.append(c)
    keep.sort(key=lambda c: (c.t, c.pad))
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
        worst = min(idx, key=lambda i: keep[i].prio)
        if keep[worst].dur > 0:
            keep[worst].dur = 0.0
        else:
            keep.pop(worst)
    return keep
