"""The one content build command.

    python tools/content/build.py              # the loop library, then every mission in content/missions/
    python tools/content/build.py level_03     # the loop library, then one mission (its level id)
    python tools/content/build.py --check      # validate only: nothing is written

Reads the loop library (content/library, content/sounds.json, data/campaign/instruments.json) and the missions
(content/missions/*.json). The library is always built, whichever missions are named: it imports the MIDI, uses the owner's
WAV renders where they exist and generated placeholders otherwise, validates everything (formats, lengths, tails, MIDI grid
and tempo, keys, chart rules of every clip and of every groove with every fill, instruments, the loadout defaults) and writes
songs/library/index.json with the 8-bar loops (songs/library/loops/*.ogg) the game plays. Each mission becomes
songs/<pack>/level.json (phases from its form, waves, intros, base). content/REPORT.md, docs/CONTENT_TO_RENDER.md and
data/campaign/library_names.json follow. It never writes an owner WAV and never overwrites a part MIDI the owner edited.
"""
from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import chart  # noqa: E402
from common import (INSTRUMENTS, LIBRARY, MISSIONS, ROOT, RULES_PATH, SONGS, TICKS_PER_BAR, ContentError, read_json, rel,  # noqa: E402
                    write_json, write_text_lf)
from library import Library  # noqa: E402
import mission as mission_mod  # noqa: E402

DEFAULTS = {"groove": "groove_half_time", "fill": "", "kick_sound": "kick_half_time", "snare_sound": "snare_backbeat",
            "bass": "bass_sub_line", "bass_sound": "bass_sub_deep", "backing": "acc_hats_driving"}
INFANTRY = {"rifle_squad", "grenadier_squad", "e1", "e2", "e3", "e4"}
VEHICLES = {"jeep", "apc", "1tnk", "2tnk", "arty", "ftrk"}


def load_instruments(lib: Library, path: Path, rules: dict) -> tuple[dict, list[str]]:
    """data/campaign/instruments.json: {sound id: {produces: [{reward, share}], blurb}} for every sound in sounds.json."""
    errors: list[str] = []
    data = read_json(path)
    rewards = rules["rewards"]
    for sid, snd in lib.sounds.items():
        ins = data.get(sid)
        if ins is None:
            errors.append(f"{rel(path)}: sound {sid} has no entry (every sound says what it produces)")
            continue
        produces, blurb = ins.get("produces"), ins.get("blurb")
        if not isinstance(produces, list) or not isinstance(blurb, str) or not blurb:
            errors.append(f"{rel(path)}: {sid} needs \"produces\" (a list) and a one-line \"blurb\"")
            continue
        for p in produces:
            r, share = p.get("reward"), p.get("share")
            if r not in rewards:
                errors.append(f"{rel(path)}: {sid} produces '{r}', which is not in data/campaign/rules.json rewards")
            elif isinstance(rewards[r], dict):
                kind = rewards[r].get("type")
                ok = (snd.family == "kick" and r in INFANTRY) or (snd.family == "snare" and kind == "build") \
                    or (snd.family == "bass" and r in VEHICLES)
                if not ok:
                    errors.append(f"{rel(path)}: a {snd.family} sound cannot produce '{r}' (kicks make infantry, snares build "
                                  f"defenses, bass sounds make vehicles)")
            if isinstance(share, bool) or not isinstance(share, int) or share < 1:
                errors.append(f"{rel(path)}: {sid} share for '{r}' must be a whole number of 1 or more")
        if snd.family == "other" and produces:
            errors.append(f"{rel(path)}: {sid} is an 'other' sound and produces nothing")
        if snd.family != "other" and not produces:
            errors.append(f"{rel(path)}: {sid} produces nothing (a kick, snare or bass sound produces at least one reward)")
    for sid in data:
        if sid not in lib.sounds:
            errors.append(f"{rel(path)}: '{sid}' is not a sound in content/sounds.json")
    return data, errors


def check_defaults(lib: Library, d: dict) -> list[str]:
    """The loadout's defaults exist and play together."""
    errors: list[str] = []

    def clip(cid: str, kind: str, label: str):
        c = lib.clips.get(cid)
        if c is None or c.index_kind != kind:
            errors.append(f"default {label} '{cid}' is not a {kind} clip in the library")
            return None
        return c

    g = clip(d["groove"], "groove", "groove")
    b = clip(d["bass"], "bass", "bass")
    k = clip(d["backing"], "backing", "backing")
    if d["fill"]:
        clip(d["fill"], "fill", "fill")
    for fld, part, c in (("kick_sound", "kick", g), ("snare_sound", "snare", g), ("bass_sound", "bass", b)):
        snd = lib.sounds.get(d[fld])
        if snd is None or snd.family != part:
            errors.append(f"default {fld} '{d[fld]}' is not a {part} sound")
        elif c is not None and d[fld] not in lib.offered(c, part):
            errors.append(f"default {fld} '{d[fld]}' does not play the default {c.index_kind} {c.id}")
    if k is not None and not lib.offered(k, "other"):
        errors.append(f"default backing {k.id} has no sound")
    return errors


def headroom_warnings(index: dict) -> list[str]:
    """The default loadout plays a kick, a snare, a bass and a backing together: warn when their peaks could add past 0 dBFS."""
    d = index["defaults"]
    try:
        g, b, k = index["clips"][d["groove"]], index["clips"][d["bass"]], index["clips"][d["backing"]]
        peaks = [g["peak_db"]["kick"][d["kick_sound"]], g["peak_db"]["snare"][d["snare_sound"]],
                 b["peak_db"]["bass"][d["bass_sound"]], k["peak_db"]["other"][next(iter(k["peak_db"]["other"]))]]
    except KeyError:
        return []
    total = 20 * math.log10(sum(10 ** (p / 20) for p in peaks))
    return [f"the default loadout's four loops could peak at up to {total:.1f} dBFS together (an upper bound); leave headroom in the renders"]         if total > 0.0 else []


def run(only: list[str] | None = None, check: bool = False, library: Path = LIBRARY, missions: Path = MISSIONS,
        songs: Path = SONGS, sounds: Path | None = None, state: Path | None = None, report: Path | None = None,
        instruments: Path = INSTRUMENTS, rules: Path = RULES_PATH, defaults: dict | None = None, quiet: bool = False) -> dict:
    t0 = time.time()
    defaults = dict(defaults or DEFAULTS)
    lib = Library(library, sounds or (library.parent / "sounds.json"), state or (library.parent / "build_state.json"), write=not check)
    errors: list[str] = []
    result = {"ok": False, "errors": errors, "warnings": [], "missions": [], "library": lib, "index": None}
    try:
        rule_set = chart.load_rules(rules)
        lib.load()
        ins, ins_errors = load_instruments(lib, instruments, rule_set)
    except ContentError as exc:
        errors.append(str(exc))
        return result
    errors += ins_errors
    errors += check_defaults(lib, defaults)
    chart_errors, chart_warnings = chart.check_library(lib, rule_set)
    errors += chart_errors
    loops: dict = {}
    index = None
    if not errors:
        out = songs / "library"
        try:
            loops = lib.build_loops(out, write=not check)
            if not check:
                index = lib.index(loops, defaults, ins, rule_set)
                warnings_extra = headroom_warnings(index)
                lib.warnings += warnings_extra
        except ContentError as exc:
            errors.append(str(exc))
    built = []
    for path in sorted(missions.glob("level_*.json")):
        if only and path.stem not in only:
            continue
        try:
            m = mission_mod.build(path, songs, write=not check and not errors)
        except ContentError as exc:
            errors.append(str(exc))
            continue
        errors += m.errors
        built.append(m)
        if not quiet:
            status = "FAILED" if m.errors else ("checked" if check else f"-> {rel(songs / m.pack)}")
            print(f"{m.level_id} {m.title}: {m.bars} bars, form {m.form}, {len(m.waves)} waves, {m.enemies} enemies  {status}")
    warnings = lib.warnings + chart_warnings + [w for m in built for w in m.warnings]
    if not errors:
        if not check:
            lib.save_state()
            write_json(songs / "library" / "index.json", index, depth=4)
            write_report(lib, loops, built, warnings, report or (library.parent / "REPORT.md"))
            if songs == SONGS:
                import render_list
                names = {**{s.id: s.name for s in lib.sounds.values()}, **{c.id: c.name for c in lib.clips.values()}}
                write_json(ROOT / "data" / "campaign" / "library_names.json", dict(sorted(names.items())))
                render_list.write(lib, loops)
    if not quiet:
        for line in lib.log:
            print("  " + line)
        for w in warnings:
            print("WARNING " + w)
        for e in errors:
            print("ERROR " + e)
        if index is not None:
            mb = sum((songs / "library" / e["file"]).stat().st_size for e in loops.values()) / 1e6
            print(f"library: {len(index['clips'])} clips, {len(index['sounds'])} sounds, {len(loops)} loops ({lib.encoded} encoded), {mb:.1f} MB")
        print(f"{'OK' if not errors else 'FAILED'} in {time.time() - t0:.1f} s")
    result.update({"ok": not errors, "warnings": warnings, "missions": built, "index": index, "loops": loops})
    return result


def write_report(lib: Library, loops: dict, built: list, warnings: list[str], path: Path) -> None:
    lines = ["# Content report", "", "Written by `python tools/content/build.py`. Do not edit; rebuild instead.", ""]
    owner = sum(1 for e in loops.values() if not e["placeholder"])
    lines += ["## Library", "",
              f"{len(lib.clips)} clips, {len(lib.sounds)} sounds, {len(loops)} loops ({owner} from your recordings, "
              f"{len(loops) - owner} placeholder). The game plays these 8-bar loops (songs/library/loops) for every mission.", ""]
    lines += ["## Missions", "", "| Mission | Title | Pack | Bars | Form | Waves | Enemies |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for m in built:
        lines.append(f"| {m.number} | {m.title} | songs/{m.pack} | {m.bars} | {m.form} | {len(m.waves)} | {m.enemies} |")
    lines += ["", "## Loops", "", "| Clip | Part | Sound | Source | Peak |", "| --- | --- | --- | --- | --- |"]
    for (c, part, s), e in sorted(loops.items()):
        clip = lib.clips[c]
        src = f"placeholder `{rel(lib.placeholder_path(clip, part, s))}`" if e["placeholder"] else f"owner `{rel(lib.owner_render_path(clip, part, s))}`"
        lines.append(f"| {c} | {part} | {s} | {src} | {e['peak_db']} dBFS |")
    lines += ["", "## MIDI", "", "| Clip | Part | Origin |", "| --- | --- | --- |"]
    for cid, clip in sorted(lib.clips.items()):
        for part in clip.parts:
            origin = clip.midi_origin.get(part, "?")
            if clip.sounds.get(part):
                origin += f"; declared renders: {', '.join(clip.sounds[part])}"
            lines.append(f"| {cid} | {part} | {origin} |")
    lines += ["", "## Listening checkpoints", "",
              "Equal lengths do not prove sync. After replacing audio, play a mission and listen at its first downbeat, every",
              "mode change (bar 9 of the form's phase changes) and the last bar. The loops restart every 8 bars: the loop",
              "seam (a tail wrapping onto bar 1) is worth a listen on every new render.", ""]
    for m in built:
        marks = [0] + [ph["start_tick"] for i, ph in enumerate(m.phases[1:], 1) if m.phases[i]["mode"] != m.phases[i - 1]["mode"]]
        lines.append(f"- {m.number} {m.title}: " + ", ".join(f"bar {t // TICKS_PER_BAR + 1}" for t in marks))
    if warnings:
        lines += ["", "## Warnings", ""] + [f"- {w}" for w in warnings]
    write_text_lf(path, "\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("missions", nargs="*", help="level ids to build (default: all)")
    parser.add_argument("--check", action="store_true", help="validate only, write nothing")
    args = parser.parse_args()
    res = run(args.missions or None, args.check)
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
