"""Input cues of a library clip, and the chart rules every clip (and every groove with every fill) must pass.

A mission no longer authors music: the player's loadout (groove, fill, kick sound, snare sound, bass line, bass sound,
backing) plays everywhere, as 8-bar loops. The cues of a loop are therefore a property of the clip:

    kick   every cue note -> pad 1           snare  every cue note -> pad 4
    bass   the clip's distinct pitches, ascending, spread over pads 1..4 (data/campaign/rules.json chart.bass.pads
           "pitch"), taps only, thinned to chart.bass.min_gap_ticks between consecutive cues

A groove (or a bass line) of 1, 2, 4 or 8 bars is tiled over the 8-bar loop; a fill sits in the last bar of the loop; ghost notes below the clip's
`cue_min_velocity` are not cues. Cues are [tick, duration_ticks, pad] with ticks counted from the loop's first bar.
"""
from __future__ import annotations

from common import TICKS_PER_BAR, ContentError, read_json, RULES_PATH

LOOP_BARS = 8
KICK_PAD = 1
SNARE_PAD = 4


def load_rules(path=RULES_PATH) -> dict:
    rules = read_json(path)
    bass = rules.get("chart", {}).get("bass")
    if not isinstance(bass, dict) or bass.get("pads") not in ("pitch", "slot") or not isinstance(bass.get("min_gap_ticks"), int) \
            or not isinstance(bass.get("holds"), bool):
        raise ContentError(f"{path}: chart.bass must be {{\"pads\": \"pitch\", \"min_gap_ticks\": int, \"holds\": bool}}")
    return rules


def pitch_pads(pitches) -> dict:
    """Pitch -> pad: the k distinct pitches, ascending, are spread over pads 1..4 (the i-th, counting from 0, goes to
    pad [1, 2, 3, 4][i * 4 // k]); a single pitch uses pad 2."""
    ordered = sorted(set(pitches))
    k = len(ordered)
    if k == 1:
        return {ordered[0]: 2}
    return {p: [1, 2, 3, 4][i * 4 // k] for i, p in enumerate(ordered)}


def loop_bars(kind: str, bars: int) -> int:
    """The length of the loop a clip becomes: 8 bars for grooves, fills and bass lines; a backing is 8 or 16 bars
    (anything longer is cut to its first 16)."""
    if kind == "backing":
        if bars <= LOOP_BARS:
            return LOOP_BARS if bars == LOOP_BARS else 0
        return 16 if bars >= 16 else 0
    return LOOP_BARS


def clip_cues(clip, part: str, rules: dict) -> list[list[int]]:
    """The cues of one part of a clip over one loop, as [tick, duration, pad] sorted by tick."""
    if clip.audio_only or part not in clip.notes or clip.kind == "accompaniment":
        return []
    notes = clip.cue_notes(part)
    length = clip.length_ticks
    if clip.kind == "groove":
        if LOOP_BARS % clip.bars:
            raise ContentError(f"{clip.id}: a groove of {clip.bars} bars does not tile an 8-bar loop (use 1, 2, 4 or 8 bars)")
        shifts = [k * length for k in range(LOOP_BARS * TICKS_PER_BAR // length)]
    elif clip.kind == "fill":
        if clip.bars > LOOP_BARS:
            raise ContentError(f"{clip.id}: a fill is at most {LOOP_BARS} bars")
        shifts = [LOOP_BARS * TICKS_PER_BAR - length]
    else:  # bass: a line of 1, 2, 4 or 8 bars is tiled over the 8-bar loop like a groove
        if LOOP_BARS % clip.bars:
            raise ContentError(f"{clip.id}: a bass line of {clip.bars} bars does not tile an 8-bar loop (use 1, 2, 4 or 8 bars)")
        shifts = [k * length for k in range(LOOP_BARS * TICKS_PER_BAR // length)]
    cues: list[list[int]] = []
    if part in ("kick", "snare"):
        pad = KICK_PAD if part == "kick" else SNARE_PAD
        for shift in shifts:
            cues += [[n["tick"] + shift, 0, pad] for n in notes]
    else:
        chart = rules["chart"]["bass"]
        if chart["pads"] == "pitch":
            pads = pitch_pads(n["pitch"] for n in notes) if notes else {}
        else:
            pads = {n["pitch"]: 2 for n in notes}
        raw = [[n["tick"] + shift, n["duration_ticks"] if chart["holds"] and n["duration_ticks"] >= rules["chart"]["hold_min_ticks"] else 0,
                pads[n["pitch"]]] for shift in shifts for n in notes]
        gap = chart["min_gap_ticks"]
        for cue in sorted(raw, key=lambda c: (c[0], c[2])):
            if not cues or cue[0] - cues[-1][0] >= gap:
                cues.append(cue)
        return cues
    return sorted(cues, key=lambda c: (c[0], c[2]))


def where(tick: int) -> str:
    return f"bar {tick // TICKS_PER_BAR + 1} beat {(tick % TICKS_PER_BAR) // 960 + 1}"


def check_cues(cues: list[list[int]], rules: dict) -> list[str]:
    """Chart rules for cues played together: the same pad at least same_pad_min_gap_ticks apart, the other pad of the
    same thumb at least same_thumb_min_gap_ticks later, at most max_touches pads at once. Returns the problems."""
    chart = rules["chart"]
    thumb = {int(k): v for k, v in rules["thumb_of_pad"].items()}
    out: list[str] = []
    ordered = sorted(cues, key=lambda c: (c[0], c[2]))
    for p in range(1, 5):
        row = [c for c in ordered if c[2] == p]
        for x, y in zip(row, row[1:]):
            if y[0] < x[0] + x[1] or y[0] - x[0] < chart["same_pad_min_gap_ticks"]:
                out.append(f"pad {p} cues at {where(x[0])} and {where(y[0])} are {y[0] - x[0]} ticks apart "
                           f"(at least {chart['same_pad_min_gap_ticks']})")
    for th in (0, 1):
        row = [c for c in ordered if thumb[c[2]] == th]
        for x, y in zip(row, row[1:]):
            if x[2] != y[2] and y[0] - x[0] < chart["same_thumb_min_gap_ticks"]:
                out.append(f"the {'left' if th == 0 else 'right'} thumb jumps from pad {x[2]} to pad {y[2]} in {y[0] - x[0]} ticks "
                           f"at {where(x[0])} (at least {chart['same_thumb_min_gap_ticks']})")
    for c in ordered:
        held = {x[2] for x in ordered if x[0] == c[0] or (x[1] and x[0] < c[0] < x[0] + x[1])}
        if len(held) > rules["max_touches"]:
            out.append(f"more than {rules['max_touches']} touches at {where(c[0])}")
            break
    return out


def check_library(lib, rules: dict) -> tuple[list[str], list[str]]:
    """Every clip part alone, then every groove with every fill. Returns (errors, warnings); an error names the clip
    or the pair."""
    errors: list[str] = []
    warnings: list[str] = []
    cues: dict[tuple[str, str], list] = {}
    for cid, clip in sorted(lib.clips.items()):
        if clip.index_kind == "backing":
            if loop_bars("backing", clip.bars) == 0:
                errors.append(f"{cid}: a backing is 8 or 16 bars, or longer (cut to its first 16); it has {clip.bars}")
            continue
        for part in clip.parts:
            try:
                cues[(cid, part)] = clip_cues(clip, part, rules)
            except ContentError as exc:
                errors.append(str(exc))
                continue
            for msg in check_cues(cues[(cid, part)], rules):
                errors.append(f"{cid} ({part}): {msg}")
    grooves = [c for c, clip in sorted(lib.clips.items()) if clip.kind == "groove"]
    fills = [c for c, clip in sorted(lib.clips.items()) if clip.kind == "fill"]
    seam = LOOP_BARS * TICKS_PER_BAR - TICKS_PER_BAR
    for g in grooves:
        for f in fills:
            if not all((g, p) in cues for p in ("kick", "snare")) or not all((f, p) in cues for p in ("kick", "snare")):
                continue
            together = [c for p in ("kick", "snare") for c in cues[(g, p)] if c[0] < seam] + \
                       [c for p in ("kick", "snare") for c in cues[(f, p)] if c[0] >= seam]
            for msg in check_cues(together, rules):
                errors.append(f"groove {g} with fill {f}: {msg}")
    return errors, warnings
