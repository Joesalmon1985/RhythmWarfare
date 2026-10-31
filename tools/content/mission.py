"""A mission: an arrangement of library clips, its player choices, input cues, sequences, rewards and waves.

content/missions/level_NN.json is the authoring file; `build(...)` turns it into songs/<pack>/level.json (schema 3)
with full-length per-slot stems assembled offline from the clip renders (sample-accurate placement from absolute
ticks, tails mixed, never re-timed), cue blocks per clip option, sequences with rewards, previews and waves.
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
    "kick_sound": ("sound:kick", "kick_sound", "Kick sound"),
    "snare_sound": ("sound:snare", "snare_sound", "Snare sound"),
    "bass_voice": ("sound:bass", "bass_voice", "Bass voice"),
}
FADE = 480  # 10 ms fade where a clip repetition is cut short (a fill replacing a groove's end, a voice change)
STEM_QUALITY = 3.0
PREVIEW_QUALITY = 2.0


@dataclass
class Ref:
    """A phase field: a choice slot ('kick_sound', 1) or a fixed library id."""
    choice: str = ""
    slot: int = 0
    fixed: str = ""

    @property
    def dep(self) -> str:
        return f"{self.choice}#{self.slot}" if self.choice else ""

    def options(self, choices: dict) -> list[str]:
        return list(choices[self.choice]["pool"]) if self.choice else [self.fixed]

    def label(self) -> str:
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
        tick = 0
        for i, p in enumerate(d["phases"]):
            bars = int(p["bars"])
            mode = p.get("mode", "")
            if mode not in ("drums", "bass"):
                self.err(f"phase {i + 1}: mode must be drums or bass")
            ph = {"index": i, "id": p.get("id", f"p{i + 1:02d}"), "start": tick, "end": tick + bars * TICKS_PER_BAR, "bars": bars,
                  "mode": mode, "raw": p, "sequence_bars": int(p.get("sequence_bars", 4)), "rewards": list(p.get("rewards", [])),
                  "pads": {}}
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

    def _ref(self, fld: str, value, phase_index: int) -> Ref:
        if isinstance(value, int):
            if fld not in self.choices:
                self.err(f"phase {phase_index + 1}: {fld} {value} refers to a choice the mission does not offer")
            elif value < 1 or value > self.choices[fld]["count"]:
                self.err(f"phase {phase_index + 1}: {fld} slot {value} is outside the choice count {self.choices[fld]['count']}")
            return Ref(choice=fld, slot=value)
        value = str(value)
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
        acc = self.data.get("accompaniment", [])
        for a in acc:
            clip = self.lib.clips.get(a["clip"])
            if clip is None or clip.kind != "accompaniment":
                self.err(f"accompaniment '{a['clip']}' is not an accompaniment clip")
                continue
            u = self._usage("other", Ref(fixed=a["clip"]), Ref(fixed=a.get("sound", "ensemble")))
            start = (int(a.get("start_bar", 1)) - 1) * TICKS_PER_BAR
            end = start + int(a.get("bars", clip.bars)) * TICKS_PER_BAR
            at = start
            while at < end:
                u.placements.append(Placement("", "other", at, at, -1 if at + clip.length_ticks <= end else end))
                at += clip.length_ticks

    def _block(self, ph: dict, part: str, clip_ref: Ref, sound_ref: Ref, a: int, b: int, loop: int) -> None:
        """Cues of one part over [a, b): one cue list per option of the clip choice. The pad follows the sound slot."""
        family = "bass" if part == "bass" else part
        slot = sound_ref.slot if sound_ref.choice else 1
        pads = RULES["pads"][family]
        if slot > len(pads):
            self.err(f"phase {ph['index'] + 1}: {family} voice slot {slot} has no pad")
            return
        pad = pads[slot - 1]
        ph["pads"][str(pad)] = {"family": family, "ref": sound_ref.label()}
        options = {}
        for opt in clip_ref.options(self.choices):
            clip = self.lib.clips.get(opt)
            if clip is None:
                continue
            cues = []
            first = ph["start"] + ((a - ph["start"]) // loop) * loop
            at = first
            while at < b:
                for n in clip.cue_notes(part):
                    t = at + n["tick"]
                    if a <= t < b:
                        dur = n["duration_ticks"] if family == "bass" and n["duration_ticks"] >= RULES["chart"]["hold_min_ticks"] else 0
                        cues.append([t, dur])
                at += loop
            options[opt] = cues
        self.blocks.append({"phase": ph["index"], "family": family, "part": part, "pad": pad, "voice": sound_ref.label(),
                            "deps": [clip_ref.dep] if clip_ref.dep else [], "start_tick": a, "end_tick": b, "options": options})

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
        bounds = sorted({s["start_tick"] for s in self.sequences} | {self.duration_ticks})
        for ph in self.phases:
            blocks = [b for b in self.blocks if b["phase"] == ph["index"]]
            combos = itertools.product(*[list(b["options"].items()) for b in blocks]) if blocks else [()]
            for combo in combos:
                cues = []
                label = ", ".join(o for o, _ in combo)
                for b, (opt, lst) in zip(blocks, combo):
                    cues += [{"tick": t, "dur": d, "pad": b["pad"], "end": t + d} for t, d in lst]
                cues.sort(key=lambda c: (c["tick"], c["pad"]))
                where = f"phase {ph['index'] + 1} with {label or 'its fixed clips'}"
                for c in cues:
                    if c["dur"] and c["end"] > ph["end"]:
                        self.err(f"{where}: a hold at bar {c['tick'] // TICKS_PER_BAR + 1} runs past the phase end (into a mode change)")
                    nxt = next((x for x in bounds if x > c["tick"]), self.duration_ticks)
                    if c["dur"] and c["end"] > nxt:
                        self.err(f"{where}: a hold at bar {c['tick'] // TICKS_PER_BAR + 1} crosses the sequence boundary at bar {nxt // TICKS_PER_BAR + 1}")
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
        # pitched clips: one key per mission
        keys = set()
        for u in self.usages.values():
            for opt in u.clip_ref.options(self.choices):
                clip = self.lib.clips.get(opt)
                if clip is not None and clip.key:
                    keys.add(clip.key)
        if len(keys) > 1:
            self.err(f"bass lines and accompaniment declare different keys {sorted(keys)}")

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

    def build_audio(self, out_dir: Path, write: bool = True) -> tuple[list[dict], dict]:
        total = bars_to_frames(self.bars + TAIL_BARS)
        stems = []
        default_mix = np.zeros((total, 2), dtype=np.float32)
        stats = {"files": 0, "placeholder_files": 0, "owner_files": 0, "seconds_of_audio": 0.0, "bytes": 0}
        default = {cid: c["default"] for cid, c in self.choices.items()}
        for n, (key, u) in enumerate(sorted(self.usages.items())):
            deps = [d for d in (u.clip_ref.dep, u.sound_ref.dep) if d]
            entry = {"key": f"s{n + 1:02d}", "family": u.family, "deps": deps, "files": {}}
            for clip_id in u.clip_ref.options(self.choices):
                for sound_id in u.sound_ref.options(self.choices):
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
                    is_default = all((ref.fixed or default[ref.choice][ref.slot - 1]) == val for ref, val in ((u.clip_ref, clip_id), (u.sound_ref, sound_id)))
                    if is_default:
                        default_mix += frames
            stems.append(entry)
        stats["default_mix_peak_db"] = round(peak_db(default_mix), 2)
        if stats["default_mix_peak_db"] > -0.1:
            self.err(f"the default mix peaks at {stats['default_mix_peak_db']} dBFS; lower the renders (headroom)")
        return stems, stats

    def build_previews(self, out_dir: Path, write: bool = True) -> dict:
        """Short auditions of single choices (4 bars at most), never the mission's arrangement."""
        out: dict[str, dict] = {}
        default = {cid: c["default"] for cid, c in self.choices.items()}

        def first(fld: str) -> str:
            for ph in self.phases:
                if fld in ph:
                    ref = ph[fld][0] if isinstance(ph[fld], list) else ph[fld]
                    return ref.fixed or default[ref.choice][ref.slot - 1]
            return ""

        groove, kick, snare = first("groove"), first("kick_sound"), first("snare_sound")
        bass, voice = first("bass"), first("bass_voice")
        bars = 4
        total = bars_to_frames(bars)

        def loop(clip_id: str, part: str, sound_id: str) -> np.ndarray:
            r = self.lib.render(clip_id, part, sound_id)["frames"]
            buf = np.zeros((total + bars_to_frames(1), 2), dtype=np.float32)
            step = self.lib.clips[clip_id].length_ticks
            at = 0
            while at < bars * TICKS_PER_BAR:
                s = tick_to_sample(at)
                n = min(len(r), len(buf) - s)
                buf[s:s + n] += r[:n]
                at += step
            return buf[:total]

        for cid, c in self.choices.items():
            if len(c["pool"]) <= c["count"]:
                continue
            out[cid] = {}
            for opt in c["pool"]:
                if cid == "groove":
                    mix = loop(opt, "kick", kick) + loop(opt, "snare", snare)
                elif cid == "fill":
                    mix = loop(opt, "kick", kick) + loop(opt, "snare", snare)
                elif cid == "kick_sound":
                    mix = loop(groove, "kick", opt) + 0.6 * loop(groove, "snare", snare)
                elif cid == "snare_sound":
                    mix = 0.6 * loop(groove, "kick", kick) + loop(groove, "snare", opt)
                elif cid == "bass":
                    mix = loop(opt, "bass", voice)
                else:
                    mix = loop(bass, "bass", opt)
                fade = 2400
                mix[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)[:, None]
                fname = f"preview/{cid}__{opt}.ogg"
                if write:
                    encode_ogg(mix, out_dir / fname, PREVIEW_QUALITY)
                out[cid][opt] = fname
        return out

    # --- output ---------------------------------------------------------------------------------------------------
    def level_json(self, stems: list[dict], previews: dict, stats: dict) -> dict:
        waves_path = ROOT / self.data["battle"]["waves"]
        waves = read_json(waves_path)
        names = {**{s.id: s.name for s in self.lib.sounds.values()}, **{c.id: c.name for c in self.lib.clips.values()}}
        placeholder = stats["placeholder_files"] > 0
        battle = self.data["battle"]
        rules = dict(waves.get("rules", {}))
        rules.update(battle.get("rules", {}))
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
            "battlefield": battle.get("battlefield", waves.get("battlefield", "defense_02")),
            "roster": "openra_mvp_01",
            "rules": rules,
            "sequence_threshold": float(self.data.get("sequence_threshold", RULES["sequence"]["threshold"])),
            "intro": self.data.get("intro", ""),
            "intro_bar": int(self.data.get("intro_bar", 1)),
            "placeholder": placeholder,
            "source": {"mission": rel(self.path), "waves": rel(waves_path), "builder": "tools/content/build.py"},
            "choices": [{"id": cid, "label": c["label"], "count": c["count"], "default": c["default"],
                         "pool": [{"id": o, "name": names.get(o, o)} for o in c["pool"]]} for cid, c in self.choices.items()],
            "names": {k: v for k, v in names.items() if any(k in c["pool"] for c in self.choices.values()) or k in self._fixed_ids()},
            "phases": [{"id": ph["id"], "start_tick": ph["start"], "end_tick": ph["end"], "mode": ph["mode"], "pads": ph["pads"]} for ph in self.phases],
            "stems": stems,
            "cue_blocks": [{k: b[k] for k in ("phase", "family", "pad", "voice", "deps", "start_tick", "end_tick", "options")} for b in self.blocks],
            "sequences": self.sequences,
            "previews": previews,
            "content": {k: stats[k] for k in ("files", "placeholder_files", "owner_files", "default_mix_peak_db")},
            "waves": [self._wave(w) for w in waves["waves"]],
        }

    VIA = {"left": "defense_1", "top": "defense_2", "right": "defense_3"}

    def _wave(self, w: dict) -> dict:
        """Waves are authored by bar (start_bar, 1-based, fractions allowed) or tick; the defense point follows the
        entry and the objective defaults to the command core."""
        out = dict(w)
        if "start_bar" in w and "start_tick" not in w:
            out["start_tick"] = int(round((float(w["start_bar"]) - 1.0) * TICKS_PER_BAR))
        out.setdefault("via_defense_point", self.VIA.get(w["entry"], "defense_1"))
        out.setdefault("target_objective", "command_core")
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
