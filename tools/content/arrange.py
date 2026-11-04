"""The arrangement system: sections of loops that make a scene's or a chapter's music (docs/MUSIC_LIBRARY_PLAN.md, M3).

    python tools/content/arrange.py generate mothership --seed 7 [--bars 64] [--id mothership_7] [--use run|chapter] [--write]
    python tools/content/arrange.py validate [content/music/arrangements/x.json ...]
    python tools/content/arrange.py render <arrangement> --bars 80 --chapter mothership [--out songs/story_mothership_1] [--format wav|ogg] [--tier 3]
    python tools/content/arrange.py audition [<arrangement> ...] [--out docs/audition]

An ARRANGEMENT (content/music/arrangements/<id>.json) is data, built offline by `generate` and read by the run (RunData / RunAudio) and by `render`:

    {"schema": 1, "id": "mothership_7", "family": "lv2_alien_spaceship", "seed": 7, "bars": 64, "use": "run",
     "compatible": [],                                   # other families the arrangement draws on (only when the catalogue lists them compatible)
     "identity": {"palette": "mothership", "filters": {...}},   # one of the five chapter palettes (content/music/palettes.json), as filters
     "sections": [{"bars": 8, "role": "intro", "pack": "lv2_alien_spaceship", "mix": "intro", "fills": [8]}, ...]}

A section is 8 or 16 bars (so the music changes on 8-bar boundaries only) and plays either a `pack` (a songs/packs/<id> set: drums, bass and synth loops with
their tiered charts) or `stems` {drums, bass, synth: <library clip/sound>} (validated structurally; the run and `render` play packs only). `mix` is a recipe
name from content/music/mix_recipes.json or a gain dict {drums, bass, other}; `fills` lists the bars (1-based inside the section) that end in a fill (the
chapter render drops bass and synth for the bar's last beat; the run ignores them). With use "run" the total is a multiple of 16 bars and every 16-bar
section starts on a 16-bar line, so each scene's 64-beat phase (16 bars) is one 16-bar section or two 8-bar ones (RunData slices the phase by `slot`).

`generate` is seeded and deterministic: the seed picks the family (among those the palette's filters pass), the roles' order, the pack of each section
and the section lengths; nothing is chosen per bar. One family per arrangement, unless the catalogue (content/music/catalogue.json, M1) lists another
family compatible with it. Without a catalogue the packs under songs/packs/ are the data: family = the Beat Shaper project, id/profile/phrase from pack.json.
`validate` checks the sections tile the target length, every pack exists and passes the run's profile, and the chart the sections produce is legal
per tier (same-pad spacing and overlaps from tools/content/chart.py, density per tier, no gap over six beats in the drum chart).
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import random
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chart import check_cues, load_rules  # noqa: E402
from common import (BPM, PPQ, ROOT, SAMPLE_RATE, TICKS_PER_BAR, ContentError, bars_to_frames, read_json, read_wav,  # noqa: E402
                    write_json, write_wav)

PACKS_DIR = ROOT / "songs" / "packs"
ARR_DIR = ROOT / "content" / "music" / "arrangements"
PALETTES_PATH = ROOT / "content" / "music" / "palettes.json"
RECIPES_PATH = ROOT / "content" / "music" / "mix_recipes.json"
CATALOGUE_PATH = ROOT / "content" / "music" / "catalogue.json"
MUSIC_JSON = ROOT / "content" / "story" / "music.json"
AUDITION_DIR = ROOT / "docs" / "audition"
AUDITION_LOCAL = ROOT / "audition"

ROLES = ("intro", "build", "drop", "breakdown", "variation", "ending")
SECTION_BARS = (8, 16)
PHASE_BARS = 16
TIERS = ("1", "2", "3", "4")
VOICES = ("drums", "bass", "other")
BASE_GAP = {"drums": 1.0, "bass": 2.0}  # beats between two cues at tier 1 (beatshaper.BASE_GAP)
FULL_GAP = 0.5  # the chart rules' floor, tiers 2 to 4
MAX_GAP_BEATS = {"drums": 6.0, "bass": 12.0}  # the longest stretch without a cue; the bass lines of the packs are sparse by design (up to 10 beats)
BLOCK_BEATS = 16
CUE_SPAN_BEATS = 12.0  # the run charts cues in beats 0..12 of a 16-beat block
MIN_BASS_RECIPE = 0.5
AUDITION_BUDGET = 30 * 1024 * 1024
MID_ROLES = ("drop", "breakdown", "variation", "drop", "build", "variation", "drop", "breakdown")


# --- data ---------------------------------------------------------------------------------------------------------

def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")


def load_packs(packs_dir: Path = PACKS_DIR, catalogue: Path | None = CATALOGUE_PATH) -> dict[str, dict]:
    """pack id -> {id, family, variant, label, bpm, phrase_beats, profile, tiers, stems, loop_frames, dir}. The catalogue (when present) may name a pack's family and
    which other families are compatible with it (`compatible` is added to every pack of the family); otherwise the family is the Beat Shaper project's slug."""
    packs: dict[str, dict] = {}
    for pj in sorted(packs_dir.glob("*/pack.json")):
        p = read_json(pj)
        src = p.get("source", {})
        packs[p["id"]] = {"id": p["id"], "family": p.get("family") or slug(src.get("project", p["id"])), "variant": int(src.get("variant", 0)),
                          "label": p.get("label", p["id"]), "bpm": int(p["bpm"]), "phrase_beats": int(p["phrase_beats"]), "profile": p.get("profile", ""),
                          "tiers": p["tiers"], "stems": p["stems"], "loop_frames": int(p.get("loop_frames", 0)), "dir": pj.parent, "compatible": []}
    cat = load_catalogue(catalogue) if catalogue is not None else {}
    for pid, fam in cat.get("pack_family", {}).items():
        if pid in packs:
            packs[pid]["family"] = fam
    for p in packs.values():
        p["compatible"] = sorted(cat.get("compatible", {}).get(p["family"], []))
    return packs


def load_catalogue(path: Path) -> dict:
    """Reads content/music/catalogue.json tolerantly: {"packs": [{"id", "family"}] (or a dict by id) and "compatible": {family: [family, ...]} or [[a, b], ...]}.
    Returns {} when the file is absent or has neither (the packs' own pack.json is then the data)."""
    if path is None or not Path(path).exists():
        return {}
    try:
        data = read_json(Path(path))
    except Exception:  # an unreadable catalogue never blocks the packs
        return {}
    out: dict = {"pack_family": {}, "compatible": {}}
    entries = data.get("packs", [])
    if isinstance(entries, dict):
        entries = [dict(v, id=k) for k, v in entries.items()]
    for e in entries:
        if isinstance(e, dict) and e.get("id") and e.get("family"):
            out["pack_family"][str(e["id"])] = str(e["family"])
    comp = data.get("compatible", data.get("compatibility", {}))
    if isinstance(comp, dict):
        for a, bs in comp.items():
            for b in (bs if isinstance(bs, list) else []):
                out["compatible"].setdefault(a, set()).add(b)
                out["compatible"].setdefault(b, set()).add(a)
    elif isinstance(comp, list):
        for pair in comp:
            if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                out["compatible"].setdefault(pair[0], set()).add(pair[1])
                out["compatible"].setdefault(pair[1], set()).add(pair[0])
            elif isinstance(pair, dict) and pair.get("a") and pair.get("b") and not pair.get("uncertain", False):
                out["compatible"].setdefault(pair["a"], set()).add(pair["b"])
                out["compatible"].setdefault(pair["b"], set()).add(pair["a"])
    return out


def load_palettes(path: Path = PALETTES_PATH) -> dict:
    return read_json(path)["palettes"]


def load_recipes(path: Path = RECIPES_PATH) -> dict:
    return read_json(path)["recipes"]


def recipe_gains(mix, recipes: dict) -> dict:
    """A section's mix (recipe name or gain dict) as {drums, bass, other} gains."""
    g = recipes[mix] if isinstance(mix, str) else mix
    return {v: float(g.get(v, 1.0)) for v in VOICES}


# --- charts -------------------------------------------------------------------------------------------------------

def density(pack: dict) -> float:
    """Cues per bar (drums plus bass) of the pack's densest tier."""
    t = pack["tiers"]["4"]
    bars = pack["phrase_beats"] / 4.0
    return (len(t["drums"]) + len(t["bass"])) / bars


def _tile(cues: list, phrase_beats: int, start_beat: int, section_beats: int) -> list[list]:
    out = []
    for k in range(section_beats // phrase_beats):
        base = (start_beat + k * phrase_beats) * PPQ
        for c in cues:
            out.append([base + int(c[0]), int(c[1]), int(c[2]), str(c[3]) if len(c) > 3 else ""])
    return out


def section_chart(pack: dict, tier: str, start_beat: int, section_beats: int, fam: str, guard: bool = True) -> list[list]:
    """The cues of one family a section plays at one tier, as [tick, duration, pad, family] from the arrangement's first tick. With `guard` the run's own rule is
    applied: only cues in beats 0..12 of every 16-beat block, a hold cut to end inside that span (RunEngine._chart_block)."""
    cues = _tile(pack["tiers"][tier][fam], pack["phrase_beats"], start_beat, section_beats)
    if not guard:
        return cues
    out = []
    for c in cues:
        in_block = (c[0] % (BLOCK_BEATS * PPQ)) / PPQ
        if in_block > CUE_SPAN_BEATS + 1e-6:
            continue
        if c[1] > 0:
            dur = min(c[1], int(round((CUE_SPAN_BEATS - in_block) * PPQ)))
            c = [c[0], dur if dur >= 480 else 0, c[2], c[3]]
        out.append(c)
    return out


def arrangement_chart(arr: dict, packs: dict, tier: str, guard: bool = True) -> dict[str, list[list]]:
    """{"drums": [...], "bass": [...]} the whole arrangement charts at `tier` (the chart of each block is the section playing then)."""
    out: dict[str, list[list]] = {"drums": [], "bass": []}
    beat = 0
    for s in arr["sections"]:
        beats = int(s["bars"]) * 4
        if "pack" in s and s["pack"] in packs:
            for fam in out:
                out[fam] += section_chart(packs[s["pack"]], tier, beat, beats, fam, guard)
        beat += beats
    return out


def chart_problems(cues: list[list], fam: str, tier: str, rules: dict, total_beats: int, unguarded: list[list]) -> list[str]:
    """Legality of one family's chart at one tier: pad spacing and overlaps (chart.check_cues), density (the tier's minimum spacing between cue times), and the
    longest stretch without a cue (measured on the unguarded timeline, seams between sections included)."""
    out = [f"tier {tier} {fam}: {m}" for m in check_cues([c[:3] for c in cues], rules)]
    times = sorted({c[0] for c in cues})
    floor = BASE_GAP[fam] if tier == "1" else FULL_GAP
    for a, b in zip(times, times[1:]):
        if (b - a) < floor * PPQ - 1e-6:
            out.append(f"tier {tier} {fam}: cues {(b - a) / PPQ:.2f} beats apart at beat {a / PPQ:.1f} (density floor {floor} beats)")
            break
    ut = sorted({c[0] for c in unguarded})
    if not ut:
        out.append(f"tier {tier} {fam}: no cues at all")
    else:
        edges = [0] + ut + [total_beats * PPQ]
        worst = max(b - a for a, b in zip(edges, edges[1:])) / PPQ
        if worst > MAX_GAP_BEATS[fam] + 1e-6:
            out.append(f"tier {tier} {fam}: a gap of {worst:.1f} beats without a cue (the limit is {MAX_GAP_BEATS[fam]:g})")
    return out


def pack_problems(pack: dict, rules: dict, bpm: int = BPM) -> list[str]:
    """Why a pack cannot be a section of an arrangement (empty = it can): the run's tempo, a phrase that tiles an 8-bar section, the three loops, four tiers, and a
    legal chart tiled over 16 bars at every tier (no gap over the limits)."""
    out: list[str] = []
    if pack["bpm"] != bpm:
        out.append(f"{pack['id']}: {pack['bpm']} BPM, the run is {bpm}")
    if pack["phrase_beats"] <= 0 or 32 % pack["phrase_beats"]:
        out.append(f"{pack['id']}: a {pack['phrase_beats']}-beat phrase does not tile an 8-bar section")
        return out
    for v in ("drums", "bass", "other"):
        if v not in pack["stems"]:
            out.append(f"{pack['id']}: no {v} loop")
    for t in TIERS:
        if t not in pack["tiers"]:
            out.append(f"{pack['id']}: no tier {t}")
    if out:
        return out
    arr = {"sections": [{"bars": 16, "pack": pack["id"]}]}
    for t in TIERS:
        guarded = arrangement_chart(arr, {pack["id"]: pack}, t, True)
        raw = arrangement_chart(arr, {pack["id"]: pack}, t, False)
        for fam in ("drums", "bass"):
            out += [f"{pack['id']}: {m}" for m in chart_problems(guarded[fam], fam, t, rules, 64, raw[fam])]
    return out


def validate_arrangement(arr: dict, packs: dict, rules: dict, palettes: dict | None = None, recipes: dict | None = None) -> list[str]:
    """Every problem of an arrangement (empty = legal)."""
    palettes = palettes if palettes is not None else load_palettes()
    recipes = recipes if recipes is not None else load_recipes()
    aid = arr.get("id", "?")
    out: list[str] = []

    def err(msg: str) -> None:
        out.append(f"{aid}: {msg}")

    for k in ("id", "family", "seed", "bars", "identity", "sections"):
        if k not in arr:
            err(f"missing '{k}'")
    if out:
        return out
    pal_id = arr["identity"].get("palette")
    pal = palettes.get(pal_id)
    if pal is None:
        err(f"identity palette '{pal_id}' is not one of {sorted(palettes)}")
    elif not any(fnmatch.fnmatch(arr["family"], g) for g in pal["filters"].get("family_glob", ["*"])):
        err(f"family '{arr['family']}' does not pass the {pal_id} palette's family filter {pal['filters'].get('family_glob')}")
    secs = arr["sections"]
    if not secs:
        err("no sections")
        return out
    total = 0
    allowed_fams = {arr["family"], *arr.get("compatible", [])}
    for i, s in enumerate(secs):
        where = f"section {i + 1}"
        if int(s.get("bars", 0)) not in SECTION_BARS:
            err(f"{where}: {s.get('bars')} bars (8 or 16: the music changes on 8-bar boundaries)")
        if s.get("role") not in ROLES:
            err(f"{where}: role '{s.get('role')}' is not one of {list(ROLES)}")
        if "pack" in s:
            p = packs.get(s["pack"])
            if p is None:
                err(f"{where}: pack '{s['pack']}' does not exist")
            else:
                if p["family"] not in allowed_fams:
                    err(f"{where}: pack {p['id']} is of family {p['family']}, the arrangement's family is {arr['family']} (compatible: {arr.get('compatible', [])})")
                bad = pack_problems(p, rules)
                out += [f"{aid}: {where}: {m}" for m in bad]
                if int(s.get("bars", 8)) * 4 % p["phrase_beats"]:
                    err(f"{where}: the {p['phrase_beats']}-beat phrase of {p['id']} does not tile {s.get('bars')} bars")
        elif isinstance(s.get("stems"), dict):
            if not s["stems"] or any(k not in ("drums", "bass", "synth") or not isinstance(v, str) or not v for k, v in s["stems"].items()):
                err(f"{where}: stems must map drums/bass/synth to a library clip or sound name")
        else:
            err(f"{where}: neither a pack nor stems")
        mix = s.get("mix")
        if isinstance(mix, str):
            if mix not in recipes:
                err(f"{where}: mix recipe '{mix}' is not in mix_recipes.json")
            elif pal is not None and mix not in set(pal["recipes"].values()):
                err(f"{where}: mix recipe '{mix}' is not one of the {pal_id} palette's (one identity per arrangement)")
        elif isinstance(mix, dict):
            if set(mix) - set(VOICES) or any(not 0.0 <= float(v) <= 1.0 for v in mix.values()):
                err(f"{where}: mix gains are drums/bass/other in 0..1")
        else:
            err(f"{where}: mix is a recipe name or gains")
        if isinstance(mix, (str, dict)) and not any("mix" in m and where in m for m in out):
            g = recipes.get(mix) if isinstance(mix, str) else mix
            if g is not None and float(g.get("bass", 1.0)) < MIN_BASS_RECIPE:
                err(f"{where}: the bass gain {g['bass']} is under {MIN_BASS_RECIPE} (the reveal must stay audible)")
        for f in s.get("fills", []):
            if not isinstance(f, int) or not 1 <= f <= int(s.get("bars", 8)):
                err(f"{where}: fill bar {f} is outside the section")
        if arr.get("use") == "run" and int(s.get("bars", 8)) == 16 and total % 16:
            err(f"{where}: a 16-bar section starts on bar {total + 1}, off the 16-bar line a scene's phase needs")
        total += int(s.get("bars", 0))
    if total != int(arr["bars"]):
        err(f"the sections add up to {total} bars, the arrangement says {arr['bars']}")
    if arr.get("use") == "run" and total % PHASE_BARS:
        err(f"use 'run': {total} bars is not a whole number of 16-bar phases")
    if any(m for m in out if "does not exist" in m):
        return out
    pk = {s["pack"]: packs[s["pack"]] for s in secs if "pack" in s and s["pack"] in packs}
    chart_arr = {"sections": [s for s in secs if "pack" in s]}
    if len(chart_arr["sections"]) == len(secs):
        for t in TIERS:
            guarded = arrangement_chart(arr, pk, t, True)
            raw = arrangement_chart(arr, pk, t, False)
            for fam in ("drums", "bass"):
                for m in chart_problems(guarded[fam], fam, t, rules, total * 4, raw[fam]):
                    err(m)
    return out


# --- generation ---------------------------------------------------------------------------------------------------

def pack_passes_filters(pack: dict, filters: dict) -> bool:
    if filters.get("profile") and pack["profile"] not in filters["profile"]:
        return False
    d = density(pack)
    return filters.get("min_density", 0.0) <= d <= filters.get("max_density", 1e9)


def candidate_families(packs: dict, pal: dict, rules: dict) -> dict[str, list[dict]]:
    """family -> its legal packs (sorted by variant), for the families that pass the palette's filters."""
    out: dict[str, list[dict]] = {}
    for p in packs.values():
        if not any(fnmatch.fnmatch(p["family"], g) for g in pal["filters"].get("family_glob", ["*"])):
            continue
        if pack_passes_filters(p, pal["filters"]) and not pack_problems(p, rules):
            out.setdefault(p["family"], []).append(p)
    for fam in out:
        out[fam].sort(key=lambda p: (p["variant"], p["id"]))
    return {k: out[k] for k in sorted(out)}


def role_plan(units: int, pal: dict, rng: random.Random) -> list[str]:
    """The role of each 8-bar unit: the palette's lead, a seeded rotation of the middle roles, the palette's tail (its last role closes the arrangement)."""
    lead, tail = list(pal.get("lead", ["intro"])), list(pal.get("tail", ["ending"]))
    if units <= len(lead) + len(tail):
        keep_tail = min(len(tail), max(1, units // 2))
        roles = lead[:units - keep_tail] + tail[len(tail) - keep_tail:]
        return roles[:units]
    off = rng.randrange(len(MID_ROLES))
    mid = [MID_ROLES[(off + i) % len(MID_ROLES)] for i in range(units - len(lead) - len(tail))]
    return lead + mid + tail


def generate(palette_id: str, seed: int, bars: int, packs: dict, rules: dict, palettes: dict | None = None, arr_id: str | None = None, use: str = "run") -> dict:
    """A deterministic arrangement of `bars` bars for a chapter palette: one family, sections of 8 or 16 bars, packs chosen per section by role."""
    palettes = palettes if palettes is not None else load_palettes()
    if palette_id not in palettes:
        raise ContentError(f"unknown palette '{palette_id}' (have {sorted(palettes)})")
    if bars % 8 or bars <= 0:
        raise ContentError(f"{bars} bars: an arrangement is a whole number of 8-bar sections")
    if use == "run" and bars % PHASE_BARS:
        raise ContentError(f"use 'run' needs a multiple of 16 bars (a scene's phase is 16 bars), got {bars}; use --use chapter for other lengths")
    pal = palettes[palette_id]
    fams = candidate_families(packs, pal, rules)
    if not fams:
        raise ContentError(f"no pack family passes the {palette_id} palette's filters {pal['filters']}")
    rng = random.Random(f"rw-arrange:{palette_id}:{seed}:{bars}")
    family = rng.choice(list(fams))
    own = fams[family]
    cross = [p for fam in sorted(packs[own[0]["id"]]["compatible"]) for p in candidate_families(packs, {"filters": {"family_glob": [fam]}}, rules).get(fam, [])]
    roles = role_plan(bars // 8, pal, rng)
    ranked = sorted(own, key=lambda p: (density(p), p["id"]))
    sections: list[dict] = []
    used_cross: set = set()
    i = 0
    prev_pack = ""
    while i < len(roles):
        role = roles[i]
        merge = (i % 2 == 0 and i + 1 < len(roles) and roles[i + 1] in (role, "drop", "variation") and role in ("drop", "variation") and rng.random() < pal.get("long_p", 0.4))
        pool = own
        if role == "drop":
            pool = ranked[-2:] if len(ranked) > 1 else ranked
        elif role == "breakdown":
            pool = ranked[:2] if len(ranked) > 1 else ranked
        elif role in ("intro", "ending"):
            pool = own[:1]
        elif role == "variation" and cross and rng.random() < 0.4:
            pool = cross
        choice = [p for p in pool if p["id"] != prev_pack] or pool
        pack = rng.choice(choice)
        if pack["family"] != family:
            used_cross.add(pack["family"])
        nbars = 16 if merge else 8
        fills: list[int] = []
        if pal.get("fills") and role in ("build", "variation"):
            fills = [nbars]
        elif pal.get("fills") and role == "drop" and merge:
            fills = [8, 16]
        sections.append({"bars": nbars, "role": role, "pack": pack["id"], "mix": pal["recipes"][role], "fills": fills})
        prev_pack = pack["id"]
        i += 2 if merge else 1
    return {"schema": 1, "id": arr_id or f"{palette_id}_{seed}", "family": family, "seed": int(seed), "bars": bars, "use": use,
            "compatible": sorted(used_cross), "identity": {"palette": palette_id, "filters": pal["filters"]}, "sections": sections}


# --- rendering ----------------------------------------------------------------------------------------------------

_LOOPS: dict = {}


def pack_loops(pack: dict) -> dict[str, np.ndarray]:
    """The three loops of a pack as stereo float32 (48 kHz, 16-bit WAV)."""
    key = str(pack["dir"])
    if key not in _LOOPS:
        loops = {}
        for v in ("drums", "bass", "other"):
            frames, fmt = read_wav(Path(pack["dir"]) / pack["stems"][v])
            if fmt["sample_rate"] != SAMPLE_RATE:
                raise ContentError(f"{pack['id']}: {v} is {fmt['sample_rate']} Hz, the chapter render needs {SAMPLE_RATE}")
            loops[v] = frames if frames.shape[1] == 2 else np.repeat(frames[:, :1], 2, axis=1)
        _LOOPS[key] = loops
    return _LOOPS[key]


def render_stems(arr: dict, packs: dict, recipes: dict, bars: int | None = None, xfade_ms: float = 10.0) -> dict[str, np.ndarray]:
    """The arrangement's sections concatenated per voice: each section's loop tiled over its bars (from loop position 0 at the section's first sample), the mix recipe
    and fills baked in, equal-power crossfades of `xfade_ms` centred on each boundary (the outgoing loop keeps playing and the incoming one starts its previous lap, whose
    end is the folded tail, so nothing is cut), then one peak limiter over the sum applied to all three voices alike."""
    bars = int(arr["bars"]) if bars is None else int(bars)
    if bars > int(arr["bars"]):
        raise ContentError(f"{arr['id']} has {arr['bars']} bars, {bars} requested")
    total = bars_to_frames(bars)
    h = int(round(xfade_ms / 1000.0 * SAMPLE_RATE / 2.0))
    out = {v: np.zeros((total, 2), dtype=np.float64) for v in VOICES}
    cum = 0
    secs = []
    for s in arr["sections"]:
        if cum >= bars:
            break
        secs.append((s, cum, min(cum + int(s["bars"]), bars)))
        cum += int(s["bars"])
    for si, (s, b0, b1) in enumerate(secs):
        if "pack" not in s:
            raise ContentError(f"{arr['id']}: section {si + 1} plays library stems, which the render does not play (packs only)")
        loops = pack_loops(packs[s["pack"]])
        a, z = bars_to_frames(b0), bars_to_frames(b1)
        n = z - a
        gains = recipe_gains(s["mix"], recipes)
        lo, hi = (0 if si == 0 else h), (0 if si == len(secs) - 1 else h)
        idx = np.arange(-lo, n + hi)
        for v in VOICES:
            loop = loops[v]
            sig = loop[np.mod(idx, len(loop))].astype(np.float64) * gains[v]
            env = np.ones(len(idx))
            if lo:
                ramp = np.sin(np.linspace(0.0, np.pi / 2.0, 2 * h, endpoint=False))
                env[:min(2 * h, len(env))] *= ramp[:len(env)]
            if hi:
                env[-2 * h:] *= np.cos(np.linspace(0.0, np.pi / 2.0, 2 * h, endpoint=False))
            sig *= env[:, None]
            if v in ("bass", "other"):  # a fill: the bar's last beat is left to the drums
                beat = int(round(SAMPLE_RATE * 60.0 / BPM))
                for f in s.get("fills", []):
                    bar_end = bars_to_frames(b0 + f) - a
                    if bar_end > n:
                        continue
                    g = np.ones(len(idx))
                    r = int(0.005 * SAMPLE_RATE)
                    lo_i, hi_i = bar_end - beat + lo, bar_end + lo
                    g[lo_i:hi_i] = 0.0
                    g[lo_i - r:lo_i] = np.linspace(1.0, 0.0, r, endpoint=False)
                    tail = g[hi_i:hi_i + r]
                    tail[:] = np.linspace(0.0, 1.0, r, endpoint=False)[:len(tail)]
                    sig *= g[:, None]
            start = a - lo
            out[v][start:start + len(idx)] += sig
    return limit(out)


def limit(stems: dict[str, np.ndarray], ceiling: float = 0.97, lookahead_ms: float = 5.0, release_ms: float = 60.0) -> dict[str, np.ndarray]:
    """One look-ahead peak limiter over the sum of the voices; the same gain curve goes on every voice so their balance is kept."""
    mix = sum(stems.values())
    peak = np.max(np.abs(mix), axis=1)
    need = np.minimum(1.0, ceiling / np.maximum(peak, 1e-9))
    if float(need.min()) >= 1.0:
        return stems
    block = 64
    nb = (len(need) + block - 1) // block
    padded = np.concatenate([need, np.ones(nb * block - len(need))])
    g = padded.reshape(nb, block).min(axis=1)
    look = max(1, int(lookahead_ms / 1000.0 * SAMPLE_RATE / block))
    rel = max(1, int(release_ms / 1000.0 * SAMPLE_RATE / block))
    # the gain at a block is the minimum over the blocks within the look-ahead before and the release after it, so it is already down when the peak arrives
    g2 = g.copy()
    for k in range(1, look + 1):
        g2[:-k] = np.minimum(g2[:-k], g[k:])
    out = g2.copy()
    for i in range(1, nb):  # a release ramp: the gain may rise by at most 1/rel per block
        out[i] = min(g2[i], out[i - 1] + 1.0 / rel)
    curve = np.interp(np.arange(len(need)), np.arange(nb) * block + block / 2.0, out)
    curve = np.minimum(curve, need)  # never above what the sample itself needs
    return {v: s * curve[:, None] for v, s in stems.items()}


def chapter_cues(arr: dict, packs: dict, tier: str, bars: int, phases: list[dict], seq_bars: int = 2) -> tuple[dict, list[str]]:
    """The chart of a rendered chapter: kick, snare and bass cues [tick, duration, pad] over the whole length, from the sections' pack tiers. A hold ends inside its
    sequence (seq_bars bars); a sequence the tier leaves without a cue of its phase's family takes the cues of tier 4 for that window; a window still empty is reported."""
    notes: list[str] = []
    fams: dict = {"drums": [], "bass": []}
    full: dict = {"drums": [], "bass": []}
    beat = 0
    for s in arr["sections"]:
        beats = int(s["bars"]) * 4
        if beat >= bars * 4:
            break
        for fam in fams:
            fams[fam] += section_chart(packs[s["pack"]], tier, beat, beats, fam, guard=False)
            full[fam] += section_chart(packs[s["pack"]], "4", beat, beats, fam, guard=False)
        beat += beats
    limit_tick = bars * TICKS_PER_BAR
    seq = seq_bars * TICKS_PER_BAR
    out: dict = {"kick": [], "snare": [], "bass": []}
    for ph in phases:
        a, b = int(ph["start_tick"]), int(ph["end_tick"])
        fam = "drums" if ph["mode"] == "drums" else "bass"
        for w in range(a, b, seq):
            hi = min(w + seq, b)
            cues = [c for c in fams[fam] if w <= c[0] < hi]
            if not cues:
                cues = [c for c in full[fam] if w <= c[0] < hi]
                if cues:
                    notes.append(f"{fam} window at bar {w // TICKS_PER_BAR + 1}: no cue at tier {tier}, took tier 4's")
                else:
                    notes.append(f"ERROR {fam} window at bar {w // TICKS_PER_BAR + 1} has no cue at any tier")
            for c in cues:
                if c[1] and c[0] + c[1] > hi:
                    c = [c[0], max(0, hi - c[0] - 240), c[2], c[3]]
                    if c[1] < 480:
                        c[1] = 0
                key = "bass" if fam == "bass" else ("kick" if c[3] == "kick" else "snare")
                out[key].append([int(c[0]), int(c[1]), int(c[2])])
    for k in out:
        out[k] = sorted({tuple(c) for c in out[k]})
        out[k] = [list(c) for c in out[k]]
    assert all(c[0] < limit_tick for k in out for c in out[k])
    return out, notes


def render_chapter(arr: dict, packs: dict, recipes: dict, chapter_id: str, out_dir: Path, bars: int, base_level: Path, tier: str = "3", fmt: str = "wav", rules: dict | None = None) -> dict:
    """Writes a mission-format pack (like songs/story_n1_warehouse): loops/{drums,bass,other}.<wav|ogg> (one stem per voice, the whole chapter long) and level.json (the
    base chapter pack's level with a `recorded_music` block whose loop is the whole chapter). Returns a summary."""
    rules = rules or load_rules()
    base = read_json(base_level)
    base_bars = int(base["duration_ticks"]) // TICKS_PER_BAR
    if base_bars != bars:
        raise ContentError(f"{base_level}: the base chapter pack has {base_bars} bars, --bars {bars}; the chapter plays {base_bars} (pass --bars {base_bars})")
    chart, notes = chapter_cues(arr, packs, tier, bars, base["phases"])
    if any(n.startswith("ERROR") for n in notes):
        raise ContentError("; ".join(n for n in notes if n.startswith("ERROR")))
    problems: list[str] = []
    for k, lst in (("drums", chart["kick"] + chart["snare"]), ("bass", chart["bass"])):
        for m in check_cues(sorted(lst), rules):
            problems.append(f"{k}: {m}")
    if problems:
        raise ContentError("the rendered chart breaks the chart rules: " + "; ".join(problems[:4]))
    stems = render_stems(arr, packs, recipes, bars)
    loops = out_dir / "loops"
    loops.mkdir(parents=True, exist_ok=True)
    files = {}
    for v in VOICES:
        frames = stems[v].astype(np.float32)
        if fmt == "ogg":
            from common import encode_ogg
            encode_ogg(frames, loops / f"{v}.ogg", quality=5.0)
            files[v] = f"loops/{v}.ogg"
        else:
            write_wav(loops / f"{v}.wav", frames)
            files[v] = f"loops/{v}.wav"
    level = dict(base)
    level["level_id"] = f"story_{chapter_id}_{arr['id']}"
    level["title"] = f"{base.get('title', chapter_id)} ({arr['id']})"
    level.pop("recorded_music", None)
    level["recorded_music"] = {
        "source": f"arrangement {arr['id']} (seed {arr['seed']}, family {arr['family']}, palette {arr['identity']['palette']})",
        "loop_bars": bars,
        "stems": {"drums": {"file": files["drums"], "mode": "drums", "families": ["kick", "snare"]},
                  "bass": {"file": files["bass"], "mode": "bass", "families": ["bass"]},
                  "other": {"file": files["other"], "mode": "always", "families": []}},
        "cues": chart,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "level.json", level, indent=1, depth=3)
    return {"dir": out_dir, "bars": bars, "tier": tier, "notes": notes, "cues": {k: len(v) for k, v in chart.items()},
            "peak": float(max(np.abs(sum(stems.values())).max(), 0.0))}


# --- audition -----------------------------------------------------------------------------------------------------

def audition_bars(arr: dict, lo_s: float = 30.0, hi_s: float = 60.0) -> int:
    """How many bars of the arrangement the audition plays: whole sections, from the start, until at least lo_s seconds and never past hi_s."""
    bar_s = 4 * 60.0 / BPM
    bars = 0
    for s in arr["sections"]:
        if bars and (bars + int(s["bars"])) * bar_s > hi_s:
            break
        bars += int(s["bars"])
        if bars * bar_s >= lo_s:
            break
    return bars


def audition(arr: dict, packs: dict, recipes: dict, path: Path) -> float:
    """Writes the audition WAV (the voices of the first sections summed at the run's last mix stage, limited): returns its length in seconds."""
    bars = audition_bars(arr)
    stems = render_stems(arr, packs, recipes, bars)
    mix = 0.45 * stems["drums"] + 1.0 * stems["bass"] + 0.6 * stems["other"]
    peak = float(np.max(np.abs(mix)))
    if peak > 0.97:
        mix *= 0.97 / peak
    write_wav(path, mix.astype(np.float32))
    return len(mix) / SAMPLE_RATE


# --- cli ----------------------------------------------------------------------------------------------------------

def arrangement_files(args_files: list[str]) -> list[Path]:
    return [Path(f) for f in args_files] if args_files else sorted(ARR_DIR.glob("*.json"))


def validate_music_json(packs: dict, arrs: dict) -> list[str]:
    """music.json entries that name an arrangement: it exists, its alternates are of the same family."""
    out: list[str] = []
    if not MUSIC_JSON.exists():
        return out
    for n in read_json(MUSIC_JSON).get("nodes", []):
        if "arrangement" not in n:
            continue
        ids = [n["arrangement"], *n.get("alternates", [])]
        for a in ids:
            if a not in arrs:
                out.append(f"music.json node {n['id']}: arrangement '{a}' does not exist")
        fams = {arrs[a]["family"] for a in ids if a in arrs}
        if len(fams) > 1:
            out.append(f"music.json node {n['id']}: its arrangement and alternates are of several families {sorted(fams)}")
    return out


def cmd_generate(args) -> int:
    packs = load_packs()
    rules = load_rules()
    palettes = load_palettes()
    recipes = load_recipes()
    made = []
    for k in range(args.count):
        seed = args.seed + k
        aid = args.id if args.id and args.count == 1 else f"{args.palette}_{seed}"
        arr = generate(args.palette, seed, args.bars, packs, rules, palettes, aid, args.use)
        problems = validate_arrangement(arr, packs, rules, palettes, recipes)
        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        made.append(arr)
        line = f"{arr['id']}: family {arr['family']}, " + " ".join(f"{s['role'][:3]}{s['bars']}:{s['pack']}" for s in arr["sections"])
        print(line)
        if args.write:
            ARR_DIR.mkdir(parents=True, exist_ok=True)
            write_json(ARR_DIR / f"{arr['id']}.json", arr, indent=1, depth=1)
    return 0


def cmd_validate(args) -> int:
    packs = load_packs()
    rules = load_rules()
    palettes = load_palettes()
    recipes = load_recipes()
    problems: list[str] = []
    arrs: dict = {}
    for f in arrangement_files(args.files):
        a = read_json(f)
        if a.get("id") != f.stem:
            problems.append(f"{f}: id '{a.get('id')}' must equal the file name")
        arrs[a.get("id", f.stem)] = a
        problems += validate_arrangement(a, packs, rules, palettes, recipes)
    problems += validate_music_json(packs, arrs)
    for p in problems:
        print("ERROR", p)
    print(f"{len(arrs)} arrangement(s): {'OK' if not problems else str(len(problems)) + ' problem(s)'}")
    return 1 if problems else 0


def cmd_render(args) -> int:
    packs = load_packs()
    recipes = load_recipes()
    path = Path(args.arrangement)
    if not path.exists():
        path = ARR_DIR / f"{args.arrangement}.json"
    arr = read_json(path)
    problems = validate_arrangement(arr, packs, load_rules())
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    chapter = json.loads((ROOT / "content" / "story" / f"{args.chapter}.json").read_text())
    first = chapter.get("music_packs", [chapter["music_pack"]])[0]
    base_level = ROOT / first.replace("res://", "") / "level.json"
    out = Path(args.out) if args.out else ROOT / "songs" / f"story_{args.chapter}_{arr['id']}"
    info = render_chapter(arr, packs, recipes, args.chapter, out, args.bars, base_level, args.tier, args.format)
    print(f"rendered {info['dir']}: {info['bars']} bars, cues {info['cues']}, peak {info['peak']:.3f}")
    for n in info["notes"]:
        print("  note:", n)
    return 0


def cmd_audition(args) -> int:
    packs = load_packs()
    recipes = load_recipes()
    files = [ARR_DIR / f"{a}.json" for a in args.arrangements] if args.arrangements else sorted(ARR_DIR.glob("*.json"))
    rows = []
    total = 0
    out_dir = Path(args.out) if args.out else AUDITION_DIR
    for f in files:
        arr = read_json(f)
        p = out_dir / f"{arr['id']}.wav"
        secs = audition(arr, packs, recipes, p)
        total += p.stat().st_size
        rows.append((arr, secs, p))
        print(f"{p}: {secs:.1f} s")
    if not args.out and total > AUDITION_BUDGET:  # too big to commit: move to the ignored folder
        AUDITION_LOCAL.mkdir(exist_ok=True)
        for _, _, p in rows:
            p.replace(AUDITION_LOCAL / p.name)
        out_dir = AUDITION_LOCAL
        print(f"{total / 1e6:.1f} MB exceeds {AUDITION_BUDGET / 1e6:.0f} MB: written to {AUDITION_LOCAL} (ignored by git)")
    write_audition_readme(rows, out_dir, total)
    return 0


def write_audition_readme(rows: list, out_dir: Path, total: int) -> None:
    here = out_dir.resolve() == AUDITION_DIR.resolve()
    where = "docs/audition/" if here else "audition/ (gitignored)"
    lines = ["# Arrangement audition previews", "",
             "One WAV per arrangement in `content/music/arrangements/`: the first sections summed at the run's last mix stage (drums 0.45, bass 1.0, synth 0.6), limited,",
             "16-bit stereo, 48 kHz, 30 to 60 s. Written by `tools/content/arrange.py audition`.", "",
             f"The WAVs are in {where} ({total / 1e6:.1f} MB in all)."]
    if not here:
        lines += ["They are over the 30 MB budget, so they are not committed. Regenerate them with:", "", "    python tools/content/arrange.py audition", ""]
    lines += ["", "| Arrangement | Palette | Family | Bars | Preview | Sections |", "| --- | --- | --- | --- | --- | --- |"]
    for arr, secs, p in rows:
        lines.append(f"| {arr['id']} | {arr['identity']['palette']} | {arr['family']} | {arr['bars']} | {secs:.0f} s | " +
                     ", ".join(f"{s['role']} {s['bars']} ({s['pack']})" for s in arr["sections"]) + " |")
    AUDITION_DIR.mkdir(parents=True, exist_ok=True)
    (AUDITION_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("palette")
    g.add_argument("--seed", type=int, default=1)
    g.add_argument("--count", type=int, default=1)
    g.add_argument("--bars", type=int, default=64)
    g.add_argument("--id")
    g.add_argument("--use", choices=["run", "chapter"], default="run")
    g.add_argument("--write", action="store_true")
    g.set_defaults(fn=cmd_generate)
    v = sub.add_parser("validate")
    v.add_argument("files", nargs="*")
    v.set_defaults(fn=cmd_validate)
    r = sub.add_parser("render")
    r.add_argument("arrangement")
    r.add_argument("--bars", type=int, required=True)
    r.add_argument("--chapter", required=True)
    r.add_argument("--out")
    r.add_argument("--tier", default="3", choices=list(TIERS))
    r.add_argument("--format", choices=["wav", "ogg"], default="wav")
    r.set_defaults(fn=cmd_render)
    a = sub.add_parser("audition")
    a.add_argument("arrangements", nargs="*")
    a.add_argument("--out")
    a.set_defaults(fn=cmd_audition)
    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except ContentError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
