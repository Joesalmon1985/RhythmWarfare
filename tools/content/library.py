"""The loop library: sounds, clips, their MIDI and their renders (owner WAV or generated placeholder).

    content/sounds.json                         sound ids, family, friendly name, placeholder synth settings
    content/library/<clip_id>/clip.json         kind, name, bars, key, source (derived / generated / owner / imported),
                                                optional "sounds" (the renders the clip declares, see below) and
                                                "audio_only" (accompaniment with no MIDI), "atonal" (an audio_only
                                                percussion backing may leave out its key: it then goes with every bass line)
    content/library/<clip_id>/<part>.mid        the clip's structure, one file per part (kick, snare, bass, other)
    content/library/<clip_id>/<part>__<sound>.wav            an owner render (drop-in, never written by the build)
    content/library/<clip_id>/placeholder/<part>__<sound>.wav a generated placeholder (rewritten by the build)
    content/build_state.json                    what the build generated and which MIDI each owner render was made from

The build never overwrites an owner file: a part MIDI the owner edited (it no longer matches what the build last wrote)
is kept and becomes the source of truth, and owner WAVs are only read.

Declared renders: a clip whose clip.json lists `"sounds": {"bass": ["bass_sub_deep", ...]}` is played only by those
sounds, each of which must exist as `<part>__<sound>.wav` in the folder (the build refuses to stand in a placeholder
for them, and never pairs the clip with another sound). That is how a pattern exported from Ableton stays paired with
the recordings made from it (tools/content/import_ableton.py writes such clips). A sound with no `synth` in
sounds.json can only be used this way.

The game plays 8-bar loops, not whole songs: `build_loops` turns every (clip, part, sound) into songs/library/loops/
<clip>__<part>__<sound>.ogg (a 2-bar groove tiled four times, a fill placed in bar 8, a long backing cut to 16 bars, the
release tail folded onto the loop's start) and `index` describes them with their cues (tools/content/chart.py).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

import synth
import chart
from common import (BPM, CONTENT, KINDS, LIBRARY, PPQ, ROOT, TAIL_BARS, TICKS_PER_BAR, ContentError, bars_to_frames,
                    encode_ogg, notes_signature, peak_db, read_json, read_midi, read_wav, rel, sha256_bytes, sha256_file,
                    tick_to_sample, write_json, write_midi, write_wav)

STATE_PATH = CONTENT / "build_state.json"
SYNTH_SOURCE = sha256_file(Path(synth.__file__))  # any change to the synthesiser refreshes every placeholder
NOTE_NAMES = {"C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3, "E": 4, "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8,
              "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11}
CHORDS = {"m": [0, 3, 7], "": [0, 4, 7], "maj": [0, 4, 7], "sus2": [0, 2, 7], "sus4": [0, 5, 7], "m7": [0, 3, 7, 10]}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_]*$")
LOOP_QUALITY = 3.0
LOOP_VERSION = "loop-1"  # bump when the way loops are assembled changes: every loop is re-encoded
BACKING_FADE = 480  # 10 ms fade where a long backing is cut to 16 bars
INDEX_KIND = {"groove": "groove", "fill": "fill", "bass": "bass", "accompaniment": "backing"}


def pitch_of(name: str | int) -> int:
    """'C#2' -> 37 (C4 = 60), or a MIDI number unchanged."""
    if isinstance(name, int):
        return name
    m = re.match(r"^([A-Ga-g][#b]?)(-?\d)$", name.strip())
    if not m:
        raise ContentError(f"pitch '{name}' is not a note name like C#2")
    return NOTE_NAMES[m.group(1).upper()] + 12 * (int(m.group(2)) + 1)


def pos_to_tick(pos: str) -> int:
    """'bar:beat' or 'bar:beat:sixteenth', all 1-based, inside the clip."""
    bits = [int(b) for b in str(pos).split(":")]
    while len(bits) < 3:
        bits.append(1)
    bar, beat, six = bits
    return (bar - 1) * TICKS_PER_BAR + (beat - 1) * PPQ + (six - 1) * (PPQ // 4)


@dataclass
class Sound:
    id: str
    family: str
    name: str
    synth: dict


@dataclass
class Clip:
    id: str
    kind: str
    name: str
    bars: int
    folder: Path
    data: dict
    parts: tuple = ()
    key: str = ""
    cue_min_velocity: int = 1
    notes: dict = field(default_factory=dict)  # part -> [{tick, duration_ticks, pitch, velocity}]
    midi_sha: dict = field(default_factory=dict)  # part -> sha256 of the part MIDI file
    midi_origin: dict = field(default_factory=dict)  # part -> generated | owner_edited | owner | audio_only
    tempo_source: dict = field(default_factory=dict)
    sounds: dict = field(default_factory=dict)  # part -> [declared render sound ids] (absent: any sound of the family)
    audio_only: bool = False  # accompaniment with no MIDI: never cued, only played
    atonal: bool = False  # an audio_only percussion backing with no key: the loadout offers it with every bass line

    @property
    def length_ticks(self) -> int:
        return self.bars * TICKS_PER_BAR

    @property
    def index_kind(self) -> str:
        return INDEX_KIND[self.kind]

    def cue_notes(self, part: str) -> list[dict]:
        return [n for n in self.notes[part] if n["velocity"] >= self.cue_min_velocity]


class Library:
    def __init__(self, root: Path = LIBRARY, sounds_path: Path = CONTENT / "sounds.json", state_path: Path = STATE_PATH,
                 write: bool = True):
        self.write = write  # False (--check): nothing is written, not even a missing MIDI or placeholder
        self.root = root
        self.sounds_path = sounds_path
        self.state_path = state_path
        self.sounds: dict[str, Sound] = {}
        self.clips: dict[str, Clip] = {}
        self.state: dict = {"clips": {}}
        self.warnings: list[str] = []
        self.log: list[str] = []
        self.encoded = 0  # loops encoded by build_loops (the rest were up to date)

    # --- loading ---------------------------------------------------------------------------------------------------
    def load(self) -> "Library":
        if self.state_path.exists():
            self.state = read_json(self.state_path)
        self.state.setdefault("clips", {})
        data = read_json(self.sounds_path)
        for s in data["sounds"]:
            if not ID_RE.match(s["id"]):
                raise ContentError(f"sounds.json: id '{s['id']}' must be lower case letters, digits and _")
            if s["family"] not in ("kick", "snare", "bass", "other"):
                raise ContentError(f"sounds.json: sound {s['id']} has unknown family '{s['family']}'")
            self.sounds[s["id"]] = Sound(s["id"], s["family"], s.get("name", s["id"]), s.get("synth", {}))
        for clip_json in sorted(self.root.glob("*/clip.json")):
            clip = self._load_clip(clip_json)
            self.clips[clip.id] = clip
        return self

    def _load_clip(self, path: Path) -> Clip:
        d = read_json(path)
        cid = d.get("id", "")
        if cid != path.parent.name:
            raise ContentError(f"{rel(path)}: id '{cid}' must equal the folder name '{path.parent.name}'")
        if not ID_RE.match(cid):
            raise ContentError(f"{rel(path)}: id must be lower case letters, digits and _")
        kind = d.get("kind", "")
        if kind not in KINDS:
            raise ContentError(f"{rel(path)}: kind must be one of {sorted(KINDS)}")
        bars = int(d.get("bars", 0))
        if bars <= 0:
            raise ContentError(f"{rel(path)}: bars must be a positive whole number")
        if float(d.get("tempo_bpm", BPM)) != BPM or d.get("meter", [4, 4]) != [4, 4]:
            raise ContentError(f"{rel(path)}: library clips are 174 BPM 4/4 (tempo_bpm / meter)")
        clip = Clip(cid, kind, d.get("name", cid), bars, path.parent, d, KINDS[kind], d.get("key", ""),
                    int(d.get("cue_min_velocity", 1)))
        clip.audio_only = bool(d.get("audio_only", False))
        clip.atonal = bool(d.get("atonal", False))
        if clip.atonal and not (kind == "accompaniment" and clip.audio_only):
            raise ContentError(f"{rel(path)}: only an audio_only accompaniment (a percussion loop) can be atonal")
        if kind in ("bass", "accompaniment") and not clip.key and not clip.atonal:
            raise ContentError(f"{rel(path)}: pitched clips declare their key (\"key\": \"C# minor\"); an atonal percussion backing says \"atonal\": true")
        if clip.audio_only and kind != "accompaniment":
            raise ContentError(f"{rel(path)}: only accompaniment clips can be audio_only (every cued part needs its MIDI)")
        declared = d.get("sounds", {})
        if not isinstance(declared, dict):
            raise ContentError(f"{rel(path)}: \"sounds\" maps a part to the list of sound ids it was rendered with")
        for part, ids in declared.items():
            if part not in clip.parts:
                raise ContentError(f"{rel(path)}: \"sounds\" names part '{part}', which a {kind} clip does not have ({list(clip.parts)})")
            if not isinstance(ids, list) or not ids:
                raise ContentError(f"{rel(path)}: \"sounds\".{part} must be a non-empty list of sound ids")
            for sid in ids:
                snd = self.sounds.get(sid)
                if snd is None or snd.family != part:
                    raise ContentError(f"{rel(path)}: \"sounds\".{part} names '{sid}', which is not a {part} sound in content/sounds.json")
                wav = path.parent / f"{part}__{sid}.wav"
                if not wav.exists():
                    raise ContentError(f"{rel(path)}: declares the render {part}__{sid}.wav but the file is missing "
                                       f"(declared renders are never replaced by placeholders)")
            clip.sounds[part] = list(ids)
        if clip.audio_only and set(clip.sounds) != set(clip.parts):
            raise ContentError(f"{rel(path)}: an audio_only clip declares its renders (\"sounds\": {{\"other\": [...]}})")
        st = self.state["clips"].setdefault(cid, {})
        st.setdefault("midi", {})
        st.setdefault("renders", {})
        st.setdefault("placeholders", {})
        expected = self._expected_notes(clip)
        for part in clip.parts:
            mid = clip.folder / f"{part}.mid"
            pst = st["midi"].setdefault(part, {})
            if clip.audio_only:
                clip.notes[part] = []
                clip.tempo_source[part] = "none"
                clip.midi_sha[part] = ""
                clip.midi_origin[part] = "audio_only"
                continue
            fresh = None  # --check: the notes a generated MIDI would have when it is missing or out of date on disk
            if part in expected:
                notes = expected[part]
                if not mid.exists():
                    if self.write:
                        write_midi(mid, notes, f"{cid} {part}")
                        pst["generated_sha256"] = sha256_file(mid)
                        self.log.append(f"wrote {rel(mid)}")
                    else:
                        fresh = notes
                elif sha256_file(mid) == pst.get("generated_sha256"):
                    if self.write:
                        before = sha256_file(mid)
                        write_midi(mid, notes, f"{cid} {part}")
                        pst["generated_sha256"] = sha256_file(mid)
                        if before != pst["generated_sha256"]:
                            self.log.append(f"regenerated {rel(mid)}")
                    elif notes_signature(read_midi(mid)["notes"]) != notes_signature(notes):
                        fresh = notes
                elif "generated_sha256" not in pst:
                    # first build on a checkout: adopt the file if it is what the source describes
                    probe = read_midi(mid)["notes"]
                    if notes_signature(probe) == notes_signature(notes):
                        pst["generated_sha256"] = sha256_file(mid)
            elif not mid.exists():
                raise ContentError(f"{rel(clip.folder)}: missing {part}.mid (an owner clip needs one MIDI file per part)")
            if fresh is not None:
                info = {"notes": fresh, "tempo_bpm": float(BPM), "tempo_source": "recorded_default"}
            else:
                info = read_midi(mid)
            if info["tempo_bpm"] and abs(info["tempo_bpm"] - BPM) > 0.01:
                raise ContentError(f"{rel(mid)}: tempo {info['tempo_bpm']:.2f} BPM; library clips are {BPM} BPM")
            clip.notes[part] = info["notes"]
            clip.tempo_source[part] = info["tempo_source"]
            clip.midi_sha[part] = sha256_file(mid) if fresh is None else "unwritten"
            if part not in expected:
                clip.midi_origin[part] = "owner"
            elif clip.midi_sha[part] == pst.get("generated_sha256"):
                clip.midi_origin[part] = "generated"
            else:
                clip.midi_origin[part] = "owner_edited"
            for n in info["notes"]:
                if n["tick"] >= clip.length_ticks:
                    raise ContentError(f"{rel(mid)}: a note starts at bar {n['tick'] // TICKS_PER_BAR + 1}, after the clip's {bars} bars")
        return clip

    # --- MIDI from the clip's source description ----------------------------------------------------------------------
    def _expected_notes(self, clip: Clip) -> dict[str, list[dict]]:
        src = clip.data.get("source", {"type": "owner"})
        kind = src.get("type", "owner")
        if kind in ("owner", "imported"):
            return {}
        if kind == "derived":
            return {part: self._derive(clip, part, spec) for part, spec in src["parts"].items()}
        if kind == "generated":
            return self._generate(clip, src)
        raise ContentError(f"{rel(clip.folder)}/clip.json: source.type must be owner, imported, derived or generated")

    def _derive(self, clip: Clip, part: str, specs: list[dict]) -> list[dict]:
        """Bars cut from the owner's source MIDI (never edited; its hash is checked against the integrity record)."""
        integrity = read_json(ROOT / "campaign" / "Musical_Source_Integrity.json")["after_sha256"]
        out = []
        for spec in specs:
            path = ROOT / spec["file"]
            key = spec["file"].removeprefix("campaign/")
            digest = sha256_file(path)
            if integrity.get(key) not in (None, digest):
                raise ContentError(f"{spec['file']}: hash {digest} differs from campaign/Musical_Source_Integrity.json")
            first, last = spec["bars"]
            lo, hi = (first - 1) * TICKS_PER_BAR, last * TICKS_PER_BAR
            for n in read_midi(path)["notes"]:
                if lo <= n["tick"] < hi:
                    m = dict(n)
                    m["tick"] -= lo
                    out.append(m)
        out.sort(key=lambda n: (n["tick"], n["pitch"]))
        return out

    def _generate(self, clip: Clip, src: dict) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {}
        for part, pattern in src.get("patterns", {}).items():  # drums: 16 steps per bar, x = hit, g = ghost, a = accent
            steps = pattern.replace("|", "").replace(" ", "")
            if len(steps) != 16 * clip.bars:
                raise ContentError(f"{rel(clip.folder)}/clip.json: pattern for {part} has {len(steps)} steps, needs {16 * clip.bars}")
            pitch = 36 if part == "kick" else 38
            vel = {"x": 108, "a": 120, "g": 46}
            out[part] = [{"tick": i * (PPQ // 4), "duration_ticks": 120, "pitch": pitch, "velocity": vel[c]}
                         for i, c in enumerate(steps) if c in vel]
        for part, notes in src.get("notes", {}).items():  # pitched: [position, length in beats, pitch(, velocity)]
            lst = []
            for row in notes:
                lst.append({"tick": pos_to_tick(row[0]), "duration_ticks": int(round(float(row[1]) * PPQ)),
                            "pitch": pitch_of(row[2]), "velocity": int(row[3]) if len(row) > 3 else 100})
            out[part] = sorted(lst, key=lambda n: (n["tick"], n["pitch"]))
        if "chords" in src:  # accompaniment: [chord, bars] in order, plus an optional hat pattern per bar
            lst, bar = [], 0
            for name, length in src["chords"]:
                m = re.match(r"^([A-G][#b]?)(m7|m|maj|sus2|sus4|)$", name)
                if not m:
                    raise ContentError(f"{rel(clip.folder)}/clip.json: chord '{name}' not understood")
                root = pitch_of(m.group(1) + "4")
                for b in range(int(length)):
                    for iv in CHORDS[m.group(2)]:
                        p = root + iv
                        while p > 69:
                            p -= 12
                        lst.append({"tick": (bar + b) * TICKS_PER_BAR, "duration_ticks": TICKS_PER_BAR - 240, "pitch": p, "velocity": 56})
                bar += int(length)
            hats = src.get("hats", "")
            if hats:
                steps = hats.replace("|", "").replace(" ", "")
                for b in range(clip.bars):
                    if b < int(src.get("hats_from_bar", 1)) - 1:
                        continue
                    for i, c in enumerate(steps[:16]):
                        if c in "xo":
                            lst.append({"tick": b * TICKS_PER_BAR + i * (PPQ // 4), "duration_ticks": 120,
                                        "pitch": 46 if c == "o" else 42, "velocity": 56})
            out["other"] = sorted(lst, key=lambda n: (n["tick"], n["pitch"]))
        missing = [p for p in clip.parts if p not in out]
        if missing:
            raise ContentError(f"{rel(clip.folder)}/clip.json: generated source has no data for {missing}")
        return out

    # --- renders -------------------------------------------------------------------------------------------------------
    def owner_render_path(self, clip: Clip, part: str, sound: str) -> Path:
        return clip.folder / f"{part}__{sound}.wav"

    def placeholder_path(self, clip: Clip, part: str, sound: str) -> Path:
        return clip.folder / "placeholder" / f"{part}__{sound}.wav"

    def compatible(self, clip_id: str, part: str, sound_id: str) -> bool:
        """Whether `sound_id` may play `part` of the clip: any sound of the family unless the clip declares its renders."""
        clip = self.clips[clip_id]
        snd = self.sounds.get(sound_id)
        if snd is None or snd.family != part:
            return False
        declared = clip.sounds.get(part)
        if declared is not None:
            return sound_id in declared
        return bool(snd.synth) or self.owner_render_path(clip, part, sound_id).exists()

    def bound_sound(self, clip_id: str, part: str) -> str:
        """The one sound a clip declares for a part (a mission says "bound" to mean it). Raises when there is not exactly one."""
        clip = self.clips[clip_id]
        declared = clip.sounds.get(part)
        if not declared:
            raise ContentError(f"{clip_id} declares no {part} render in its clip.json (\"sounds\"), so its {part} sound cannot be bound")
        if len(declared) > 1:
            raise ContentError(f"{clip_id} declares {len(declared)} {part} renders {declared}; offer them as a sound choice instead of binding")
        return declared[0]

    def render(self, clip_id: str, part: str, sound_id: str) -> dict:
        """The audio of one clip part played by one sound: the owner WAV if there is one (validated), otherwise the
        generated placeholder (written or refreshed now). Returns {frames (n x 2 float), placeholder, path}."""
        clip = self.clips[clip_id]
        sound = self.sounds[sound_id]
        if sound.family != part:
            raise ContentError(f"sound {sound_id} is a {sound.family} sound and cannot play the {part} part of {clip_id}")
        name = f"{part}__{sound_id}"
        st = self.state["clips"][clip_id]
        owner = self.owner_render_path(clip, part, sound_id)
        declared = clip.sounds.get(part)
        if declared is not None and sound_id not in declared:
            raise ContentError(f"{clip_id} is played only by its declared {part} renders {declared}; {sound_id} is not one of them")
        if owner.exists():
            frames = self._check_owner_render(clip, part, sound_id, owner)
            return {"frames": frames, "placeholder": False, "path": owner}
        if declared is not None:
            raise ContentError(f"{rel(owner)} is declared by {clip_id} but missing")
        if not sound.synth:
            raise ContentError(f"sound {sound_id} has no placeholder synth in content/sounds.json and {clip_id} has no {name}.wav render")
        st["renders"].pop(name, None)
        ph = self.placeholder_path(clip, part, sound_id)
        key = sha256_bytes(json.dumps([clip.midi_sha[part], sound.synth, SYNTH_SOURCE, clip.bars]).encode())
        if not ph.exists() or st["placeholders"].get(name) != key:
            if not self.write:  # --check: do not synthesise or write; the render only has to exist
                self.log.append(f"placeholder {rel(ph)} would be written")
                return {"frames": np.zeros((bars_to_frames(clip.bars + TAIL_BARS), 2), dtype=np.float32), "placeholder": True, "path": ph}
            mono = synth.render_part(part, clip.notes[part], clip.bars, sound.synth, f"{clip_id}/{name}")
            write_wav(ph, mono)
            st["placeholders"][name] = key
            self.log.append(f"placeholder {rel(ph)}")
        frames, _ = read_wav(ph)
        return {"frames": frames, "placeholder": True, "path": ph}

    def _check_owner_render(self, clip: Clip, part: str, sound_id: str, path: Path) -> np.ndarray:
        frames, fmt = read_wav(path)
        where = rel(path)
        if fmt["sample_rate"] != 48000:
            raise ContentError(f"{where}: {fmt['sample_rate']} Hz; export at 48000 Hz")
        if fmt["channels"] != 2:
            raise ContentError(f"{where}: {fmt['channels']} channel(s); export stereo (2 channels)")
        musical = bars_to_frames(clip.bars)
        longest = bars_to_frames(clip.bars + TAIL_BARS)
        if fmt["frames"] < musical - 2:
            raise ContentError(f"{where}: {fmt['frames']} frames is shorter than the clip's {clip.bars} bars ({musical} frames at 174 BPM); "
                               f"export from the clip's first bar to its end plus the release tail")
        if fmt["frames"] > longest + 2:
            raise ContentError(f"{where}: {fmt['frames']} frames is longer than {clip.bars} bars plus a one-bar tail ({longest}); trim the export")
        peak = float(np.max(np.abs(frames))) if frames.size else 0.0
        if peak < 0.001:
            raise ContentError(f"{where}: the file is silent")
        if peak >= 0.999:
            self.warnings.append(f"{where}: peaks at full scale (clipping?); leave headroom in the export")
        if frames.shape[0] > musical + 2:
            tail = frames[musical:]
            end = tail[-min(len(tail), 480):]
            if float(np.max(np.abs(end))) > 0.01:
                self.warnings.append(f"{where}: still sounding at the end of the tail; let the release finish within one bar")
        if not clip.audio_only:
            self._check_alignment(clip, part, frames, where)
        st = self.state["clips"][clip.id]["renders"]
        name = f"{part}__{sound_id}"
        wav_sha = sha256_file(path)
        prev = st.get(name)
        if not clip.audio_only and prev and prev.get("wav_sha256") == wav_sha and prev.get("midi_sha256") != clip.midi_sha[part]:
            raise ContentError(f"{where} was rendered from an earlier {part}.mid of {clip.id}; the MIDI changed since. "
                               f"Re-export the WAV from the new MIDI (or delete it to fall back to the placeholder)")
        st[name] = {"wav_sha256": wav_sha, "midi_sha256": clip.midi_sha[part], "frames": int(fmt["frames"])}
        return frames

    def _check_alignment(self, clip: Clip, part: str, frames: np.ndarray, where: str) -> None:
        """Drums: every cue note should have an audible attack within 25 ms of its MIDI time. Pitched parts: the first
        note's onset. A failure is a warning (listen at the printed checkpoints), not an error."""
        mono = np.abs(frames).mean(axis=1)
        win = 240  # 5 ms
        notes = clip.notes[part] if part in ("kick", "snare") else clip.notes[part][:1]
        late = []
        for n in notes:
            s = tick_to_sample(n["tick"])
            before = mono[max(s - 2 * win, 0):s].mean() if s > 0 else 0.0
            after = mono[s:s + 5 * win].max() if s < len(mono) else 0.0
            if after < 0.01 or after < 2.0 * before:
                late.append(n["tick"])
        if notes and len(late) > len(notes) * 0.3:
            bars = sorted({t // TICKS_PER_BAR + 1 for t in late})
            self.warnings.append(f"{where}: {len(late)} of {len(notes)} notes show no attack at their MIDI time (bars {bars[:6]}); "
                                 f"check the export starts exactly at the clip's first bar")

    def save_state(self) -> None:
        write_json(self.state_path, self.state)

    # --- the loops the game plays --------------------------------------------------------------------------------------
    def declared_sounds(self) -> set[str]:
        """Every sound some clip declares in its clip.json (the recorded sounds that only play their own clip)."""
        return {sid for c in self.clips.values() for ids in c.sounds.values() for sid in ids}

    def offered(self, clip: Clip, part: str) -> list[str]:
        """The sounds a clip part is offered with, in sounds.json order: its declared renders, or else every sound of the
        family that no clip declares and that can play it (a synth for the placeholder, or an owner render)."""
        declared = clip.sounds.get(part)
        if declared is not None:
            return list(declared)
        taken = self.declared_sounds()
        out = []
        for sid, snd in self.sounds.items():
            if snd.family != part or sid in taken:
                continue
            if snd.synth or self.owner_render_path(clip, part, sid).exists():
                out.append(sid)
        return out

    def loop_frames(self, clip: Clip, src: np.ndarray) -> np.ndarray:
        """One clip render (frames x 2, musical length plus tail) as the loop the game plays: exactly bars_to_frames(loop
        bars) frames, the render tiled or placed as the clip kind needs and its tail folded onto the loop's start."""
        bars = chart.loop_bars(clip.index_kind, clip.bars)
        if bars == 0:
            raise ContentError(f"{clip.id}: a backing is 8 or 16 bars, or longer (cut to 16); it has {clip.bars} bars")
        length = bars_to_frames(bars)
        if clip.index_kind == "backing" and clip.bars > bars:
            src = src[:length].copy()  # a long backing is cut to its first 16 bars with a 10 ms fade out
            n = min(BACKING_FADE, len(src))
            src[len(src) - n:] *= np.linspace(1.0, 0.0, n, dtype=np.float32)[:, None]
            starts = [0]
        elif clip.index_kind in ("groove", "bass"):  # a shorter groove or bass line is tiled over the 8-bar loop
            starts = [tick_to_sample(k * clip.length_ticks) for k in range(bars // clip.bars)]
        elif clip.index_kind == "fill":
            starts = [tick_to_sample((bars - clip.bars) * TICKS_PER_BAR)]
        else:
            starts = [0]
        buf = np.zeros((length + len(src), 2), dtype=np.float32)
        for at in starts:
            buf[at:at + len(src)] += src
        out = buf[:length].copy()
        tail = buf[length:]
        n = min(len(tail), length)
        out[:n] += tail[:n]  # the release tail wraps around to the start of the loop
        return out

    def loop_name(self, clip_id: str, part: str, sound: str) -> str:
        return f"loops/{clip_id}__{part}__{sound}.ogg"

    def build_loops(self, out_dir: Path, write: bool = True) -> dict[tuple[str, str, str], dict]:
        """Assemble (and with `write` encode) the loop of every clip part and offered sound. The source is the owner WAV
        or the placeholder render; an Ogg is only re-encoded when its source, or the way loops are made, changed.
        Returns {(clip, part, sound): {file, peak_db, placeholder}}. Loops no clip offers any more are removed."""
        out: dict[tuple[str, str, str], dict] = {}
        loops_state = self.state.setdefault("loops", {})
        for cid, clip in sorted(self.clips.items()):
            for part in clip.parts:
                for sid in self.offered(clip, part):
                    r = self.render(cid, part, sid)
                    name = self.loop_name(cid, part, sid)
                    entry = {"file": name, "placeholder": r["placeholder"]}
                    out[(cid, part, sid)] = entry
                    if not write:
                        continue
                    key = sha256_bytes(json.dumps([sha256_file(r["path"]), clip.kind, clip.bars, LOOP_VERSION, LOOP_QUALITY]).encode())
                    cached = loops_state.get(name)
                    ogg = out_dir / name
                    if cached and cached.get("key") == key and ogg.exists():
                        entry["peak_db"] = cached["peak_db"]
                        continue
                    frames = self.loop_frames(clip, r["frames"])
                    db = peak_db(frames)
                    entry["peak_db"] = round(db, 2) if db > -120.0 else -120.0
                    encode_ogg(frames, ogg, LOOP_QUALITY)
                    loops_state[name] = {"key": key, "peak_db": entry["peak_db"]}
                    self.encoded += 1
        if write:
            wanted = {e["file"] for e in out.values()}
            for stale in sorted(set(loops_state) - wanted):
                del loops_state[stale]
            for f in sorted((out_dir / "loops").glob("*.ogg")) if (out_dir / "loops").exists() else []:
                if f"loops/{f.name}" not in wanted:
                    f.unlink()
                    imp = f.with_suffix(".ogg.import")
                    if imp.exists():
                        imp.unlink()
        return out

    def index(self, loops: dict, defaults: dict, instruments: dict, rules: dict) -> dict:
        """songs/library/index.json (format rhythm_warfare.library.v1)."""
        placeholder_of: dict[str, bool] = {}
        for (cid, part, sid), e in loops.items():
            placeholder_of[sid] = placeholder_of.get(sid, True) and e["placeholder"]
        sounds = {}
        for sid, snd in self.sounds.items():
            ins = instruments[sid]
            sounds[sid] = {"family": snd.family, "name": snd.name, "placeholder": placeholder_of.get(sid, bool(snd.synth)),
                           "produces": ins["produces"], "blurb": ins["blurb"]}
        clips = {}
        for cid, clip in sorted(self.clips.items()):
            entry = {"kind": clip.index_kind, "name": clip.name, "key": clip.key,
                     "bars": chart.loop_bars(clip.index_kind, clip.bars), "parts": list(clip.parts), "bound": bool(clip.sounds),
                     "sounds": {}, "cues": {}, "loops": {}, "peak_db": {}}
            for part in clip.parts:
                entry["sounds"][part] = self.offered(clip, part)
                if clip.index_kind != "backing":
                    entry["cues"][part] = chart.clip_cues(clip, part, rules)
                entry["loops"][part] = {}
                entry["peak_db"][part] = {}
                for sid in entry["sounds"][part]:
                    e = loops[(cid, part, sid)]
                    entry["loops"][part][sid] = e["file"]
                    entry["peak_db"][part][sid] = e["peak_db"]
            clips[cid] = entry
        return {"format": "rhythm_warfare.library.v1", "bpm": BPM, "ticks_per_beat": PPQ, "loop_bars": chart.LOOP_BARS,
                "defaults": defaults, "sounds": sounds, "clips": clips}
