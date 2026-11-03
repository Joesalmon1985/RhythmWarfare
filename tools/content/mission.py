"""A mission: an arrangement of library clips, its player choices, input cues, sequences, rewards and waves.

content/missions/level_NN.json is the authoring file; `build(...)` turns it into songs/<pack>/level.json (schema 3)
with full-length per-slot stems assembled offline from the clip renders (sample-accurate placement from absolute
ticks, tails mixed, never re-timed), cue blocks per clip option, sequences with rewards, previews and waves.

Sounds in a phase are a choice slot (`"kick_sound": 1`), a fixed sound id, or `"bound"`: the one render the chosen clip
declares for that part (clip.json "sounds"), so a pattern recorded in Ableton always plays with its own recording. A
sound choice whose options are declared renders of different clips (five sub sounds of one bass line, four of another)
is written to the pack with `depends_on` and per-option `with` lists; the game keeps the selection compatible. The
`accompaniment` choice picks an accompaniment clip (audio-only clips allowed) and its placements say `"clip": 1`.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from common import (ROOT, SONGS, TAIL_BARS, TICKS_PER_BAR, ContentError, bars_to_frames, encode_ogg, peak_db,
                    read_json, rel, tick_to_sample, write_json)
from library import Library

RULES = read_json(ROOT / "data" / "campaign" / "rules.json")
CHOICE_KINDS = {  # choice id -> (what it picks, phase field, label)
    "groove": ("clip:groove", "groove", "Groove"),
    "fill": ("clip:fill", "fill", "Fill"),
    "bass": ("clip:bass", "bass", "Bass line"),
    "accompaniment": ("clip:accompaniment", "accompaniment", "Backing track"),
    "kick_sound": ("sound:kick", "kick_sound", "Kick sound"),
    "snare_sound": ("sound:snare", "snare_sound", "Snare sound"),
    "bass_voice": ("sound:bass", "bass_voice", "Bass voice"),
}
SOUND_FIELDS = ("kick_sound", "snare_sound", "bass_voice")
FADE = 480  # 10 ms fade where a clip repetition is cut short (a fill replacing a groove's end, a voice change)
STEM_QUALITY = 3.0
PREVIEW_QUALITY = 2.0
PREVIEW_BARS = 4
ENVELOPE_BLOCK = 480  # 10 ms blocks for the worst-case mix estimate
BASS_CHART_DEFAULT = {"pads": "slot", "min_gap_ticks": 0, "holds": True}  # = the pad follows the voice slot, every note, holds kept


def pitch_pads(pitches) -> dict:
    """Pitch -> pad for a bass chart that follows pitch: the k distinct pitches, ascending, are spread over pads 1..4
    (the i-th, counting from 0, goes to pad floor(i * 4 / k) + 1); a single pitch uses pad 2."""
    ordered = sorted(set(pitches))
    k = len(ordered)
    if k == 1:
        return {ordered[0]: 2}
    return {p: i * 4 // k + 1 for i, p in enumerate(ordered)}


@dataclass
class Ref:
    """A phase field: a choice slot ('kick_sound', 1), a fixed library id, or (sounds only) bound to the clip."""
    choice: str = ""
    slot: int = 0
    fixed: str = ""
    bound: bool = False

    @property
    def dep(self) -> str:
        return f"{self.choice}#{self.slot}" if self.choice else ""

    def options(self, choices: dict) -> list[str]:
        if self.bound:
            return []
        return list(choices[self.choice]["pool"]) if self.choice else [self.fixed]

    def label(self) -> str:
        if self.bound:
            return "bound"
        return self.dep or self.fixed


@dataclass
class Placement:
    clip: str
    part: str
    at: int  # absolute tick of the clip's bar 1
    keep_from: int  # absolute ticks; audio outside [keep_from, keep_to) is cut (keep_to -1 = natural end with tail)
    keep_to: int


@dataclass
class Usage:
    family: str
    clip_ref: Ref
    sound_ref: Ref
    placements: list = field(default_factory=list)

    @property
    def key(self) -> tuple:
        return (self.family, self.clip_ref.label(), self.sound_ref.label())


class Mission:
    def __init__(self, path: Path, lib: Library):
        self.path = path
        self.lib = lib
        self.data = read_json(path)
        d = self.data
        self.level_id = d["level_id"]
        self.number = int(d["number"])
        self.title = d["title"]
        self.pack = d["pack"]
        self.bars = int(d["bars"])
        self.duration_ticks = self.bars * TICKS_PER_BAR
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.choices: dict[str, dict] = {}
        self.phases: list[dict] = []
        self.usages: dict[tuple, Usage] = {}
        self.blocks: list[dict] = []
        self.sequences: list[dict] = []
        self.intros: list[dict] = []

    def err(self, msg: str) -> None:
        self.errors.append(f"{rel(self.path)}: {msg}")

    # --- parsing -------------------------------------------------------------------------------------------------
    def parse(self) -> None:
        d = self.data
        if d.get("bpm", 174) != 174 or d.get("meter", [4, 4]) != [4, 4]:
            self.err("missions are 174 BPM in 4/4")
        for cid, c in d.get("choices", {}).items():
            if cid not in CHOICE_KINDS:
                self.err(f"unknown choice '{cid}' (use {sorted(CHOICE_KINDS)})")
                continue
            what = CHOICE_KINDS[cid][0]
            pool = list(c.get("pool", []))
            count = int(c.get("count", 1))
            default = list(c.get("default", pool[:count]))
            for item in pool:
                if what.startswith("clip:"):
                    clip = self.lib.clips.get(item)
                    if clip is None or clip.kind != what[5:]:
                        self.err(f"choice {cid}: '{item}' is not a {what[5:]} clip in the library")
                else:
                    snd = self.lib.sounds.get(item)
                    if snd is None or snd.family != what[6:]:
                        self.err(f"choice {cid}: '{item}' is not a {what[6:]} sound in content/sounds.json")
            if count < 1 or count > len(pool):
                self.err(f"choice {cid}: count {count} needs at least that many pool items ({len(pool)})")
            if len(default) != count or len(set(default)) != count or not set(default) <= set(pool):
                self.err(f"choice {cid}: default must be {count} different pool items")
            self.choices[cid] = {"id": cid, "count": count, "pool": pool, "default": default, "label": c.get("label", CHOICE_KINDS[cid][2])}
        base_chart = self._bass_chart(d.get("bass_chart"), BASS_CHART_DEFAULT, "mission")
        tick = 0
        for i, p in enumerate(d["phases"]):
            bars = int(p["bars"])
            mode = p.get("mode", "")
            if mode not in ("drums", "bass"):
                self.err(f"phase {i + 1}: mode must be drums or bass")
            ph = {"index": i, "id": p.get("id", f"p{i + 1:02d}"), "start": tick, "end": tick + bars * TICKS_PER_BAR, "bars": bars,
                  "mode": mode, "raw": p, "sequence_bars": int(p.get("sequence_bars", 4)), "rewards": list(p.get("rewards", [])),
                  "pads": {}, "bass_chart": self._bass_chart(p.get("bass_chart"), base_chart, f"phase {i + 1}")}
            for fld in ("groove", "fill", "bass", "kick_sound", "snare_sound"):
                if fld in p:
                    ph[fld] = self._ref(fld, p[fld], i)
            voices = p.get("bass_voice")
            if voices is not None:
                ph["bass_voice"] = [self._ref("bass_voice", v, i) for v in (voices if isinstance(voices, list) else [voices])]
                ph["voice_every_bars"] = int(p.get("voice_every_bars", bars))
            self.phases.append(ph)
            tick = ph["end"]
        if tick != self.duration_ticks:
            self.err(f"phases cover {tick // TICKS_PER_BAR} bars but the mission has {self.bars}")
        for r_id in [r for ph in self.phases for r in ph["rewards"]]:
            if r_id not in RULES["rewards"]:
                self.err(f"unknown reward '{r_id}' (data/campaign/rules.json rewards)")
        intros = d.get("intros")
        if intros is None:
            intros = [{"bar": int(d.get("intro_bar", 1)), "text": d["intro"]}] if d.get("intro") else []
        for it in intros:
            bar = int(it.get("bar", 1))
            if not 1 <= bar <= self.bars or not str(it.get("text", "")):
                self.err(f"intros: each entry needs a bar inside the song and a text ({it})")
            self.intros.append({"bar": bar, "text": str(it.get("text", ""))})

    def _bass_chart(self, raw, base: dict, where: str) -> dict:
        """`bass_chart` (mission level, a phase may override single keys): how a bass line becomes cues. pads 'slot' (the
        pad follows the voice slot) or 'pitch' (low to high over pads 1..4); min_gap_ticks drops a cue closer than that
        to the last one kept; holds false makes every bass cue a tap."""
        out = dict(base)
        if raw is None:
            return out
        if not isinstance(raw, dict):
            self.err(f"{where}: bass_chart must be an object")
            return out
        for key, value in raw.items():
            if key == "pads":
                if value not in ("slot", "pitch"):
                    self.err(f"{where}: bass_chart pads must be 'slot' or 'pitch', not {value!r}")
                    continue
            elif key == "min_gap_ticks":
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    self.err(f"{where}: bass_chart min_gap_ticks must be an integer of 0 or more, not {value!r}")
                    continue
            elif key == "holds":
                if not isinstance(value, bool):
                    self.err(f"{where}: bass_chart holds must be true or false, not {value!r}")
                    continue
            else:
                self.err(f"{where}: unknown bass_chart key '{key}' (use pads, min_gap_ticks, holds)")
                continue
            out[key] = value
        return out

    def _ref(self, fld: str, value, phase_index: int) -> Ref:
        if isinstance(value, int):
            if fld not in self.choices:
                self.err(f"phase {phase_index + 1}: {fld} {value} refers to a choice the mission does not offer")
            elif value < 1 or value > self.choices[fld]["count"]:
                self.err(f"phase {phase_index + 1}: {fld} slot {value} is outside the choice count {self.choices[fld]['count']}")
            return Ref(choice=fld, slot=value)
        value = str(value)
        if value == "bound":
            if fld not in SOUND_FIELDS:
                self.err(f"phase {phase_index + 1}: only a sound ({', '.join(SOUND_FIELDS)}) can be bound to its clip")
            return Ref(bound=True)
        what = CHOICE_KINDS[fld][0]
        ok = (self.lib.clips.get(value) is not None and self.lib.clips[value].kind == what[5:]) if what.startswith("clip:") \
            else (self.lib.sounds.get(value) is not None and self.lib.sounds[value].family == what[6:])
        if not ok:
            self.err(f"phase {phase_index + 1}: {fld} '{value}' is not in the library")
        return Ref(fixed=value)

    # --- arrangement --------------------------------------------------------------------------------------------
    def _usage(self, family: str, clip_ref: Ref, sound_ref: Ref) -> Usage:
        u = Usage(family, clip_ref, sound_ref)
        return self.usages.setdefault(u.key, u)

    def _clip_bars(self, ref: Ref) -> int:
        bars = {self.lib.clips[o].bars for o in ref.options(self.choices) if o in self.lib.clips}
        if len(bars) != 1:
            self.err(f"the options of {ref.label()} have different lengths {sorted(bars)}; offer clips of one length per choice")
        return bars.pop() if bars else 1

    def sound_options(self, u: Usage, clip_id: str) -> list[str]:
        """The sounds a usage may play one of its clip options with: the bound render, or the pool's compatible sounds."""
        if u.sound_ref.bound:
            try:
                return [self.lib.bound_sound(clip_id, u.family)]
            except ContentError as exc:
                self.err(str(exc))
                return []
        return [s for s in u.sound_ref.options(self.choices) if self.lib.compatible(clip_id, u.family, s)]

    def render_pairs(self):
        """Every (clip id, part, sound id) the mission plays, in stem order."""
        for key, u in sorted(self.usages.items()):
            for c in u.clip_ref.options(self.choices):
                for s in self.sound_options(u, c):
                    yield c, u.family, s

    def arrange(self) -> None:
        for ph in self.phases:
            s, e = ph["start"], ph["end"]
            fill_at = e
            if "fill" in ph:
                fb = self._clip_bars(ph["fill"])
                fill_at = e - fb * TICKS_PER_BAR
                if fill_at < s:
                    self.err(f"phase {ph['index'] + 1}: the fill is longer than the phase")
            if "groove" in ph:
                gb = self._clip_bars(ph["groove"]) * TICKS_PER_BAR
                for part, sref in (("kick", ph.get("kick_sound")), ("snare", ph.get("snare_sound"))):
                    if sref is None:
                        self.err(f"phase {ph['index'] + 1}: a groove needs {part}_sound")
                        continue
                    u = self._usage(part, ph["groove"], sref)
                    at = s
                    while at < fill_at:
                        u.placements.append(Placement("", part, at, at, min(at + gb, fill_at) if at + gb > fill_at else -1))
                        at += gb
                    if (fill_at - s) % gb and fill_at == e:
                        self.warnings.append(f"{rel(self.path)}: phase {ph['index'] + 1} is not a whole number of groove loops; the last one is cut")
                    if ph["mode"] == "drums":
                        self._block(ph, part, ph["groove"], sref, s, fill_at, gb)
                if "fill" in ph:
                    for part, sref in (("kick", ph.get("kick_sound")), ("snare", ph.get("snare_sound"))):
                        if sref is None:
                            continue
                        u = self._usage(part, ph["fill"], sref)
                        u.placements.append(Placement("", part, fill_at, fill_at, -1))
                        if ph["mode"] == "drums":
                            self._block(ph, part, ph["fill"], sref, fill_at, e, e - fill_at)
            elif ph["mode"] == "drums":
                self.err(f"phase {ph['index'] + 1}: a drum phase needs a groove")
            if "bass" in ph:
                bb = self._clip_bars(ph["bass"]) * TICKS_PER_BAR
                voices = ph.get("bass_voice") or []
                if not voices:
                    self.err(f"phase {ph['index'] + 1}: a bass line needs bass_voice")
                    continue
                every = ph.get("voice_every_bars", ph["bars"]) * TICKS_PER_BAR
                windows = []
                w, k = s, 0
                while w < e:
                    windows.append((w, min(w + every, e), voices[k % len(voices)]))
                    w += every
                    k += 1
                for (a, b, vref) in windows:
                    u = self._usage("bass", ph["bass"], vref)
                    at = s + ((a - s) // bb) * bb
                    while at < b:
                        lo, hi = max(at, a), min(at + bb, b)
                        cut_hi = -1 if (hi == at + bb and b == e) or (hi == at + bb and len(voices) == 1) else hi
                        u.placements.append(Placement("", "bass", at, lo, cut_hi))
                        at += bb
                    if ph["mode"] == "bass":
                        self._block(ph, "bass", ph["bass"], vref, a, b, bb)
            elif ph["mode"] == "bass":
                self.err(f"phase {ph['index'] + 1}: a bass phase needs a bass line")
        for a in self.data.get("accompaniment", []):
            clip_ref = self._ref("accompaniment", a["clip"], -1) if isinstance(a["clip"], int) else Ref(fixed=str(a["clip"]))
            options = [o for o in clip_ref.options(self.choices) if o in self.lib.clips]
            if not options or any(self.lib.clips[o].kind != "accompaniment" for o in options):
                self.err(f"accompaniment '{a['clip']}' is not an accompaniment clip (or choice)")
                continue
            sound = a.get("sound")
            if sound is None:
                declared = [bool(self.lib.clips[o].sounds.get("other")) for o in options]
                if all(declared):
                    sound = "bound"
                elif any(declared):
                    self.err(f"accompaniment {clip_ref.label()}: some options declare their renders and some do not; say which sound plays")
                    continue
                else:
                    sound = "ensemble"
            sound_ref = Ref(bound=True) if sound == "bound" else Ref(fixed=str(sound))
            u = self._usage("other", clip_ref, sound_ref)
            length = self._clip_bars(clip_ref) * TICKS_PER_BAR
            start = (int(a.get("start_bar", 1)) - 1) * TICKS_PER_BAR
            end = start + int(a.get("bars", length // TICKS_PER_BAR)) * TICKS_PER_BAR
            at = start
            while at < end:
                u.placements.append(Placement("", "other", at, at, -1 if at + length <= end else end))
                at += length
        self._check_pairs()

    def _check_pairs(self) -> None:
        """Every clip option of every usage has a sound to play it with, the defaults play together, and every option
        of a sound choice plays at least one clip it is offered with."""
        default = {cid: c["default"] for cid, c in self.choices.items()}
        for u in self.usages.values():
            clips = [c for c in u.clip_ref.options(self.choices) if c in self.lib.clips]
            for c in clips:
                if not self.sound_options(u, c):
                    self.err(f"{u.family}: {c} has no sound to play it in {u.sound_ref.label() or 'its sounds'} "
                             f"(declared renders only pair with their own clip)")
            if u.sound_ref.choice:
                for s in u.sound_ref.options(self.choices):
                    if not any(self.lib.compatible(c, u.family, s) for c in clips):
                        self.err(f"choice {u.sound_ref.choice}: {s} plays none of the {u.family} clips it is offered with ({clips})")
            dc = u.clip_ref.fixed or (default[u.clip_ref.choice][u.clip_ref.slot - 1] if u.clip_ref.choice in default else "")
            if dc and not u.sound_ref.bound:
                ds = u.sound_ref.fixed or (default[u.sound_ref.choice][u.sound_ref.slot - 1] if u.sound_ref.choice in default else "")
                if ds and dc in self.lib.clips and not self.lib.compatible(dc, u.family, ds):
                    self.err(f"the default {u.sound_ref.label()} {ds} does not play the default {u.clip_ref.label()} {dc}")

    def _block(self, ph: dict, part: str, clip_ref: Ref, sound_ref: Ref, a: int, b: int, loop: int) -> None:
        """Cues of one part over [a, b): one cue list per option of the clip choice. The pad follows the sound slot
        (a bound sound follows its clip's slot), or for a bass line with bass_chart pads 'pitch' the note's pitch."""
        family = "bass" if part == "bass" else part
        chart = ph["bass_chart"] if family == "bass" else BASS_CHART_DEFAULT
        by_pitch = chart["pads"] == "pitch"
        slot = sound_ref.slot if sound_ref.choice else (clip_ref.slot if sound_ref.bound and clip_ref.choice else 1)
        pads = RULES["pads"][family]
        if slot > len(pads) and not by_pitch:
            self.err(f"phase {ph['index'] + 1}: {family} voice slot {slot} has no pad")
            return
        voice = f"bound:{clip_ref.label()}:{part}" if sound_ref.bound else sound_ref.label()
        per_option = {}  # option -> [(pad, tick, dur)]
        for opt in clip_ref.options(self.choices):
            clip = self.lib.clips.get(opt)
            if clip is None:
                continue
            notes = clip.cue_notes(part)
            pad_of = pitch_pads(n["pitch"] for n in notes) if by_pitch and notes else {}
            cues = []
            first = ph["start"] + ((a - ph["start"]) // loop) * loop
            at = first
            while at < b:
                for n in notes:
                    t = at + n["tick"]
                    if a <= t < b:
                        hold = family != "bass" or chart["holds"]
                        dur = n["duration_ticks"] if family == "bass" and hold and n["duration_ticks"] >= RULES["chart"]["hold_min_ticks"] else 0
                        cues.append((pad_of.get(n["pitch"], pads[slot - 1] if slot <= len(pads) else 2), t, dur))
                at += loop
            if chart["min_gap_ticks"] > 0:
                kept = []
                for c in sorted(cues, key=lambda c: (c[1], c[0])):
                    if not kept or c[1] - kept[-1][1] >= chart["min_gap_ticks"]:
                        kept.append(c)
                cues = kept
            per_option[opt] = cues
        used = sorted({c[0] for cues in per_option.values() for c in cues}) or [pads[slot - 1] if slot <= len(pads) else 2]
        group = len(self.blocks)
        for pad in used:
            ph["pads"][str(pad)] = {"family": family, "ref": voice}
            self.blocks.append({"phase": ph["index"], "family": family, "part": part, "pad": pad, "voice": voice, "group": group,
                                "deps": [clip_ref.dep] if clip_ref.dep else [], "start_tick": a, "end_tick": b,
                                "options": {opt: [[t, d] for p, t, d in cues if p == pad] for opt, cues in per_option.items()}})

    # --- sequences and checks ---------------------------------------------------------------------------------------
    def make_sequences(self) -> None:
        idx = 0
        for ph in self.phases:
            span = ph["sequence_bars"] * TICKS_PER_BAR
            if ph["bars"] % ph["sequence_bars"]:
                self.err(f"phase {ph['index'] + 1}: {ph['bars']} bars do not divide into sequences of {ph['sequence_bars']}")
            if not ph["rewards"]:
                self.err(f"phase {ph['index'] + 1}: rewards list is empty")
                continue
            k = 0
            t = ph["start"]
            while t < ph["end"]:
                self.sequences.append({"index": idx, "phase": ph["index"], "mode": ph["mode"], "start_tick": t,
                                       "end_tick": min(t + span, ph["end"]), "reward": ph["rewards"][k % len(ph["rewards"])]})
                idx += 1
                k += 1
                t += span

    def check(self) -> None:
        chart = RULES["chart"]
        thumb = {int(k): v for k, v in RULES["thumb_of_pad"].items()}
        for ph in self.phases:
            blocks = [b for b in self.blocks if b["phase"] == ph["index"]]
            groups = {}  # blocks that share a group are the pads of one cue list: they take the same option together
            for b in blocks:
                groups.setdefault(b["group"], []).append(b)
            groups = list(groups.values())
            combos = itertools.product(*[list(g[0]["options"]) for g in groups]) if groups else [()]
            for combo in combos:
                cues = []
                label = ", ".join(combo)
                for g, opt in zip(groups, combo):
                    for b in g:
                        cues += [{"tick": t, "dur": d, "pad": b["pad"], "end": t + d} for t, d in b["options"][opt]]
                cues.sort(key=lambda c: (c["tick"], c["pad"]))
                where = f"phase {ph['index'] + 1} with {label or 'its fixed clips'}"
                for c in cues:
                    if c["dur"] and c["end"] > ph["end"]:
                        self.err(f"{where}: a hold at bar {c['tick'] // TICKS_PER_BAR + 1} runs past the phase end (into a mode change)")
                for p in range(1, 5):
                    row = [c for c in cues if c["pad"] == p]
                    for x, y in zip(row, row[1:]):
                        if y["tick"] < x["end"] or (not x["dur"] and y["tick"] - x["tick"] < chart["same_pad_min_gap_ticks"]):
                            self.err(f"{where}: pad {p} cues at bar {x['tick'] // TICKS_PER_BAR + 1} come too close together")
                for th in (0, 1):
                    row = [c for c in cues if thumb[c["pad"]] == th]
                    for x, y in zip(row, row[1:]):
                        if x["pad"] == y["pad"]:
                            continue
                        if x["dur"] and y["tick"] < x["end"] + chart["same_thumb_after_hold_ticks"]:
                            self.err(f"{where}: the {'left' if th == 0 else 'right'} thumb must hold pad {x['pad']} and press pad {y['pad']} at bar {y['tick'] // TICKS_PER_BAR + 1}")
                        elif not x["dur"] and y["tick"] - x["tick"] < chart["same_thumb_min_gap_ticks"]:
                            self.err(f"{where}: the {'left' if th == 0 else 'right'} thumb jumps pads {x['pad']}->{y['pad']} too fast at bar {y['tick'] // TICKS_PER_BAR + 1}")
                for c in cues:
                    held = {x["pad"] for x in cues if x["tick"] == c["tick"] or (x["dur"] and x["tick"] < c["tick"] < x["end"])}
                    if len(held) > RULES["max_touches"]:
                        self.err(f"{where}: more than two touches at bar {c['tick'] // TICKS_PER_BAR + 1}")
                        break
                for s in self.sequences:
                    if s["phase"] == ph["index"] and not any(s["start_tick"] <= c["tick"] < s["end_tick"] for c in cues):
                        self.err(f"{where}: sequence {s['index'] + 1} (bars {s['start_tick'] // TICKS_PER_BAR + 1}..) has no cues")
        self._check_mode_changes(thumb, chart)
        # pitched clips: one key per mission
        keys = set()
        for u in self.usages.values():
            for opt in u.clip_ref.options(self.choices):
                clip = self.lib.clips.get(opt)
                if clip is not None and clip.key:
                    keys.add(clip.key)
        if len(keys) > 1:
            self.err(f"bass lines and accompaniment declare different keys {sorted(keys)}")

    def _check_mode_changes(self, thumb: dict, chart: dict) -> None:
        """A hold that ends at a mode change while the next phase's first cue falls on the same thumb's other pad is
        playable (a release within 0.15 s of the tail is complete) but worth knowing: a warning per boundary."""
        for prev, ph in zip(self.phases, self.phases[1:]):
            s = ph["start"]
            ends = [(b["pad"], t + d) for b in self.blocks if b["phase"] == prev["index"]
                    for lst in b["options"].values() for t, d in lst if d and t + d >= s - chart["same_thumb_after_hold_ticks"]]
            starts = [(b["pad"], t) for b in self.blocks if b["phase"] == ph["index"]
                      for lst in b["options"].values() for t, _ in lst if s <= t < s + chart["same_thumb_after_hold_ticks"]]
            clash = {(p1, p2) for p1, _ in ends for p2, _ in starts if p1 != p2 and thumb[p1] == thumb[p2]}
            for p1, p2 in sorted(clash):
                self.warnings.append(f"{rel(self.path)}: at bar {s // TICKS_PER_BAR + 1} a hold on pad {p1} ends where pad {p2} "
                                     f"(same thumb) is cued; the thumb lifts up to 0.15 s early without losing the hold")

    # --- audio ------------------------------------------------------------------------------------------------------
    def _render_usage(self, u: Usage, clip_id: str, sound_id: str, total: int) -> tuple[np.ndarray, bool]:
        r = self.lib.render(clip_id, u.family, sound_id)
        src = r["frames"]
        out = np.zeros((total, 2), dtype=np.float32)
        for p in u.placements:
            s0 = tick_to_sample(p.at)
            a = tick_to_sample(p.keep_from) - s0
            b = len(src) if p.keep_to < 0 else tick_to_sample(p.keep_to) - s0
            seg = src[a:b].copy()
            if p.keep_to >= 0 and len(seg) > FADE:
                seg[-FADE:] *= np.linspace(1.0, 0.0, FADE, dtype=np.float32)[:, None]
            if p.keep_from > p.at and len(seg) > FADE:
                seg[:FADE] *= np.linspace(0.0, 1.0, FADE, dtype=np.float32)[:, None]
            start = s0 + a
            n = min(len(seg), total - start)
            if n > 0:
                out[start:start + n] += seg[:n]
        return out, r["placeholder"]

    def _is_default(self, u: Usage, clip_id: str, sound_id: str) -> bool:
        default = {cid: c["default"] for cid, c in self.choices.items()}
        for ref, val in ((u.clip_ref, clip_id), (u.sound_ref, sound_id)):
            if ref.bound:
                continue
            if (ref.fixed or default[ref.choice][ref.slot - 1]) != val:
                return False
        return True

    def build_audio(self, out_dir: Path, write: bool = True) -> tuple[list[dict], dict]:
        total = bars_to_frames(self.bars + TAIL_BARS)
        stems = []
        default_mix = np.zeros((total, 2), dtype=np.float32)
        blocks = -(-total // ENVELOPE_BLOCK)
        loudest = np.zeros(blocks, dtype=np.float32)  # sum over stems of the loudest option's envelope (an upper bound)
        stats = {"files": 0, "placeholder_files": 0, "owner_files": 0, "seconds_of_audio": 0.0, "bytes": 0}
        for n, (key, u) in enumerate(sorted(self.usages.items())):
            deps = [d for d in (u.clip_ref.dep, u.sound_ref.dep) if d]
            entry = {"key": f"s{n + 1:02d}", "family": u.family, "deps": deps, "files": {}}
            env = np.zeros(blocks, dtype=np.float32)
            for clip_id in u.clip_ref.options(self.choices):
                for sound_id in self.sound_options(u, clip_id):
                    frames, ph = self._render_usage(u, clip_id, sound_id, total)
                    combo = [o for o, ref in ((clip_id, u.clip_ref), (sound_id, u.sound_ref)) if ref.dep]
                    fname = f"audio/{entry['key']}__{'__'.join([clip_id, sound_id])}.ogg"
                    if write:
                        encode_ogg(frames, out_dir / fname, STEM_QUALITY)
                        stats["bytes"] += (out_dir / fname).stat().st_size
                    entry["files"]["|".join(combo)] = {"file": fname, "placeholder": ph, "clip": clip_id, "sound": sound_id,
                                                       "peak_db": round(peak_db(frames), 2)}
                    stats["files"] += 1
                    stats["placeholder_files" if ph else "owner_files"] += 1
                    stats["seconds_of_audio"] += sum(((p.keep_to if p.keep_to >= 0 else p.at + self.lib.clips[clip_id].length_ticks) - p.keep_from)
                                                     for p in u.placements) * 60.0 / (174 * 960)
                    if self._is_default(u, clip_id, sound_id):
                        default_mix += frames
                    mono = np.abs(frames).max(axis=1)
                    mono = np.pad(mono, (0, blocks * ENVELOPE_BLOCK - len(mono))).reshape(blocks, ENVELOPE_BLOCK).max(axis=1)
                    env = np.maximum(env, mono)
            loudest += env
            stems.append(entry)
        stats["default_mix_peak_db"] = round(peak_db(default_mix), 2)
        stats["loudest_mix_bound_db"] = round(peak_db(loudest), 2)
        if stats["default_mix_peak_db"] > -0.1:
            self.err(f"the default mix peaks at {stats['default_mix_peak_db']} dBFS; lower the renders (headroom)")
        elif stats["loudest_mix_bound_db"] > 0.0:
            self.warnings.append(f"{rel(self.path)}: the loudest combination of options may peak at up to "
                                 f"{stats['loudest_mix_bound_db']} dBFS (an upper bound); leave more headroom in the renders")
        return stems, stats

    # --- previews -------------------------------------------------------------------------------------------------
    def _first_ref(self, fld: str) -> Ref | None:
        for ph in self.phases:
            if fld in ph:
                return ph[fld][0] if isinstance(ph[fld], list) else ph[fld]
        return None

    def _pick(self, ref: Ref | None, fallback: str = "") -> str:
        """The default option of a ref ('' for a bound sound or no ref)."""
        if ref is None or ref.bound:
            return fallback
        return ref.fixed or self.choices[ref.choice]["default"][ref.slot - 1]

    def _sound_for(self, clip_id: str, part: str, ref: Ref | None) -> str:
        """The sound a preview plays `clip_id`'s `part` with: its bound render, else the default (or first compatible) pick."""
        if ref is None:
            return ""
        if ref.bound:
            return self.lib.bound_sound(clip_id, part)
        want = self._pick(ref)
        if self.lib.compatible(clip_id, part, want):
            return want
        return next((s for s in ref.options(self.choices) if self.lib.compatible(clip_id, part, s)), "")

    def _clip_for(self, sound_id: str, part: str, ref: Ref | None) -> str:
        """The clip a sound preview plays: the default clip if the sound fits it, else the first that does."""
        if ref is None:
            return ""
        want = self._pick(ref)
        if want and self.lib.compatible(want, part, sound_id):
            return want
        return next((c for c in ref.options(self.choices) if self.lib.compatible(c, part, sound_id)), "")

    def build_previews(self, out_dir: Path, write: bool = True) -> dict:
        """Short auditions of single choices (4 bars at most), never the mission's arrangement."""
        out: dict[str, dict] = {}
        groove_ref, kick_ref, snare_ref = self._first_ref("groove"), self._first_ref("kick_sound"), self._first_ref("snare_sound")
        bass_ref, voice_ref = self._first_ref("bass"), self._first_ref("bass_voice")
        acc_usage = next((u for u in self.usages.values() if u.family == "other"), None)
        bars = PREVIEW_BARS
        total = bars_to_frames(bars)

        def loop(clip_id: str, part: str, sound_id: str) -> np.ndarray:
            buf = np.zeros((total + bars_to_frames(1), 2), dtype=np.float32)
            if not clip_id or not sound_id:
                return buf[:total]
            r = self.lib.render(clip_id, part, sound_id)["frames"]
            step = self.lib.clips[clip_id].length_ticks
            at = 0
            while at < bars * TICKS_PER_BAR:
                s = tick_to_sample(at)
                n = min(len(r), len(buf) - s)
                buf[s:s + n] += r[:n]
                at += step
            return buf[:total]

        def drums(clip_id: str, kick: str = "", snare: str = "", kick_gain: float = 1.0, snare_gain: float = 1.0) -> np.ndarray:
            return (kick_gain * loop(clip_id, "kick", kick or self._sound_for(clip_id, "kick", kick_ref))
                    + snare_gain * loop(clip_id, "snare", snare or self._sound_for(clip_id, "snare", snare_ref)))

        for cid, c in self.choices.items():
            if len(c["pool"]) <= c["count"]:
                continue
            out[cid] = {}
            for opt in c["pool"]:
                if cid in ("groove", "fill"):
                    mix = drums(opt)
                elif cid == "kick_sound":
                    mix = drums(self._clip_for(opt, "kick", groove_ref), kick=opt, snare_gain=0.6)
                elif cid == "snare_sound":
                    mix = drums(self._clip_for(opt, "snare", groove_ref), snare=opt, kick_gain=0.6)
                elif cid == "bass":
                    mix = loop(opt, "bass", self._sound_for(opt, "bass", voice_ref))
                elif cid == "bass_voice":
                    mix = loop(self._clip_for(opt, "bass", bass_ref), "bass", opt)
                else:  # accompaniment
                    mix = loop(opt, "other", self._sound_for(opt, "other", acc_usage.sound_ref if acc_usage else None))
                fade = 2400
                mix[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)[:, None]
                fname = f"preview/{cid}__{opt}.ogg"
                if write:
                    encode_ogg(mix, out_dir / fname, PREVIEW_QUALITY)
                out[cid][opt] = fname
        return out

    # --- output ---------------------------------------------------------------------------------------------------
    def _choice_entries(self, names: dict) -> list[dict]:
        """The pack's choices, with `depends_on` and per-option `with` where a sound choice pairs with a clip choice."""
        pairs: dict[str, set] = {}
        for u in self.usages.values():
            if u.sound_ref.choice and u.clip_ref.choice:
                pairs.setdefault(u.sound_ref.choice, set()).add((u.clip_ref.choice, u.family))
        out = []
        for cid, c in self.choices.items():
            entry = {"id": cid, "label": c["label"], "count": c["count"], "default": c["default"],
                     "pool": [{"id": o, "name": names.get(o, o)} for o in c["pool"]]}
            if cid in pairs:
                # a sound choice that pairs with several clip choices (a kick sound used by the groove and the fill) is
                # fine while every option plays every clip; only a restricted pairing (declared renders) can be followed,
                # and the game can follow one parent only
                restricted_parents = []
                for parent, family in sorted(pairs[cid]):
                    clips = self.choices[parent]["pool"]
                    with_by_option = {}
                    for o in entry["pool"]:
                        with_ = [cl for cl in clips if self.lib.compatible(cl, family, o["id"])]
                        if len(with_) < len(clips):
                            with_by_option[o["id"]] = with_
                    if with_by_option:
                        restricted_parents.append((parent, with_by_option))
                if len(restricted_parents) > 1:
                    self.err(f"choice {cid} depends on several clip choices {[p for p, _ in restricted_parents]}; "
                             "the game can follow one")
                if restricted_parents:
                    parent, with_by_option = restricted_parents[0]
                    for o in entry["pool"]:
                        if o["id"] in with_by_option:
                            o["with"] = with_by_option[o["id"]]
                    entry["depends_on"] = parent
            out.append(entry)
        return out

    def bound_sounds(self) -> dict:
        out: dict[str, dict] = {}
        for u in self.usages.values():
            if u.sound_ref.bound:
                for c in u.clip_ref.options(self.choices):
                    for s in self.sound_options(u, c):
                        out.setdefault(c, {})[u.family] = s
        return out

    def level_json(self, stems: list[dict], previews: dict, stats: dict) -> dict:
        waves_path = ROOT / self.data["battle"]["waves"]
        waves = read_json(waves_path)
        names = {**{s.id: s.name for s in self.lib.sounds.values()}, **{c.id: c.name for c in self.lib.clips.values()}}
        placeholder = stats["placeholder_files"] > 0
        battle = self.data["battle"]
        rules = dict(waves.get("rules", {}))
        rules.update(battle.get("rules", {}))
        field = battle.get("battlefield", waves.get("battlefield", "defense_02"))
        self._check_walls(rules, field)
        objective = self.primary_objective(field)
        bound = self.bound_sounds()
        used = self._fixed_ids() | {s for d in bound.values() for s in d.values()} | {c for c in bound}
        return {
            "schema_version": 3,
            "mode": "defense",
            "level_id": self.level_id,
            "campaign_level": self.number,
            "title": self.title,
            "bpm": 174,
            "time_signature": [4, 4],
            "ticks_per_beat": 960,
            "song_offset_ms": 0,
            "duration_ticks": self.duration_ticks,
            "seed": int(self.data.get("seed", 1000 + self.number)),
            "battlefield": field,
            "roster": "openra_mvp_01",
            "rules": rules,
            "sequence_threshold": float(self.data.get("sequence_threshold", RULES["sequence"]["threshold"])),
            "intro": self.intros[0]["text"] if self.intros else "",
            "intro_bar": self.intros[0]["bar"] if self.intros else 1,
            "intros": self.intros,
            "placeholder": placeholder,
            "source": {"mission": rel(self.path), "waves": rel(waves_path), "builder": "tools/content/build.py"},
            "choices": self._choice_entries(names),
            "names": {k: v for k, v in names.items() if any(k in c["pool"] for c in self.choices.values()) or k in used},
            "bound_sounds": bound,
            "phases": [{"id": ph["id"], "start_tick": ph["start"], "end_tick": ph["end"], "mode": ph["mode"], "pads": ph["pads"]} for ph in self.phases],
            "stems": stems,
            "cue_blocks": [{k: b[k] for k in ("phase", "family", "pad", "voice", "deps", "start_tick", "end_tick", "options")} for b in self.blocks],
            "sequences": self.sequences,
            "previews": previews,
            "content": {k: stats[k] for k in ("files", "placeholder_files", "owner_files", "default_mix_peak_db", "loudest_mix_bound_db")},
            "waves": [self._wave(w, objective) for w in waves["waves"]],
        }

    VIA = {"left": "defense_1", "top": "defense_2", "right": "defense_3"}

    def _check_walls(self, rules: dict, battlefield: str) -> None:
        """Sandbag cells (rules.walls) must keep every route open and stay off sockets, buildings and the map edge."""
        bf = read_json(ROOT / "data" / "battlefields" / f"{battlefield}.json")
        taken = {(b["x"] + i, b["y"] + j) for b in bf["buildings"] for i in range(b["w"]) for j in range(b["h"])}
        taken |= {(sk["x"], sk["y"]) for sk in bf.get("sockets", [])}
        for x, y in rules.get("walls", []):
            on_route = (19 <= y <= 23 and (x < 28 or x > 50)) or (37 <= x <= 41 and y < 16)
            if on_route or (x, y) in taken or not (0 < x < bf["width"] - 1 and 0 < y < bf["height"] - 1):
                self.err(f"wall cell ({x}, {y}) is on a route, a socket or a building")

    TARGETS = ("defenses", "civilians", "core")

    @staticmethod
    def primary_objective(battlefield: str) -> str:
        """The id of the battlefield's first required objective (the one waves attack by default); the command core when
        the battlefield cannot be read."""
        try:
            bf = read_json(ROOT / "data" / "battlefields" / f"{battlefield}.json")
            return next(o["id"] for o in bf["objectives"] if o.get("required"))
        except (OSError, ValueError, KeyError, StopIteration):
            return "command_core"

    def _wave(self, w: dict, objective: str = "command_core") -> dict:
        """Waves are authored by bar (start_bar, 1-based, fractions allowed) or tick; the defense point follows the
        entry, the objective defaults to the battlefield's first required objective and `target` (what the wave goes
        for: defenses, civilians or core, default core) may be overridden per group."""
        out = dict(w)
        if "start_bar" in w and "start_tick" not in w:
            out["start_tick"] = int(round((float(w["start_bar"]) - 1.0) * TICKS_PER_BAR))
        out.setdefault("via_defense_point", self.VIA.get(w["entry"], "defense_1"))
        out.setdefault("target_objective", objective)
        out.setdefault("target", "core")
        for where, t in [(f"wave {w['id']}", out["target"])] + [(f"wave {w['id']} group {g.get('actor', '?')}", g["target"]) for g in w["groups"] if "target" in g]:
            if t not in self.TARGETS:
                self.err(f"{where}: target '{t}' is not one of {', '.join(self.TARGETS)}")
        out["groups"] = [{**g, "spawn_spacing_ticks": int(g.get("spawn_spacing_ticks", 480))} for g in w["groups"]]
        if not 0 <= out["start_tick"] < self.duration_ticks:
            self.err(f"wave {w['id']} starts outside the song")
        return out

    def _fixed_ids(self) -> set:
        out = set()
        for u in self.usages.values():
            out.add(u.clip_ref.fixed)
            out.add(u.sound_ref.fixed)
        return out - {""}


def build(path: Path, lib: Library, songs: Path = SONGS, write: bool = True) -> Mission:
    m = Mission(path, lib)
    m.parse()
    if not m.errors:
        m.arrange()
    if not m.errors:
        m.make_sequences()
        m.check()
    if m.errors:
        return m
    out_dir = songs / m.pack
    stems, stats = m.build_audio(out_dir, write)
    previews = m.build_previews(out_dir, write)
    m.stats = stats
    if m.errors:
        return m
    if write:
        level = m.level_json(stems, previews, stats)
        if m.errors:
            return m
        write_json(out_dir / "level.json", level)
        keep = {s["files"][k]["file"] for s in stems for k in s["files"]} | {f for c in previews.values() for f in c.values()}
        for sub in ("audio", "preview"):
            for f in (out_dir / sub).glob("*.ogg") if (out_dir / sub).exists() else []:
                if f"{sub}/{f.name}" not in keep:
                    f.unlink()
                    imp = f.with_suffix(".ogg.import")
                    if imp.exists():
                        imp.unlink()
    return m
