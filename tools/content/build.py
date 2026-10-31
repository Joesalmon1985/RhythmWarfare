"""The one content build command.

    python tools/content/build.py              # every mission in content/missions/
    python tools/content/build.py level_03     # one mission (its level id)
    python tools/content/build.py --check      # validate only: no audio written

Reads the loop library (content/library, content/sounds.json) and the missions (content/missions/*.json), imports
the MIDI, uses the owner's WAV renders where they exist and generated placeholders otherwise, validates everything
(formats, lengths, tails, MIDI grid and tempo, keys, cues, holds, sequences, thumbs, headroom), assembles every
mission's per-slot stems offline and writes songs/<pack>/level.json, its audio/ and preview/ Ogg files and
content/REPORT.md. It never writes an owner WAV and never overwrites a part MIDI the owner has edited.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import CONTENT, LIBRARY, MISSIONS, ROOT, SONGS, TICKS_PER_BAR, ContentError, rel, tick_to_seconds, write_json  # noqa: E402
from library import Library  # noqa: E402
import mission as mission_mod  # noqa: E402


def run(only: list[str] | None = None, check: bool = False, library: Path = LIBRARY, missions: Path = MISSIONS,
        songs: Path = SONGS, sounds: Path | None = None, state: Path | None = None, report: Path | None = None,
        quiet: bool = False) -> dict:
    t0 = time.time()
    lib = Library(library, sounds or (library.parent / "sounds.json"), state or (library.parent / "build_state.json"))
    errors: list[str] = []
    try:
        lib.load()
    except ContentError as exc:
        return {"ok": False, "errors": [str(exc)], "warnings": [], "missions": []}
    built = []
    for path in sorted(missions.glob("level_*.json")):
        if only and path.stem not in only:
            continue
        try:
            m = mission_mod.build(path, lib, songs, write=not check)
        except ContentError as exc:
            errors.append(str(exc))
            continue
        errors += m.errors
        built.append(m)
        if not quiet:
            st = getattr(m, "stats", {})
            status = "FAILED" if m.errors else ("checked" if check else f"-> {rel(songs / m.pack)}")
            print(f"{m.level_id} {m.title}: {len(m.sequences)} sequences, {sum(len(b['options']) for b in m.blocks)} cue lists, "
                  f"{st.get('files', 0)} stem files ({st.get('placeholder_files', 0)} placeholder), mix peak {st.get('default_mix_peak_db', '-')} dBFS  {status}")
    warnings = lib.warnings + [w for m in built for w in m.warnings]
    if not errors:
        lib.save_state()
        if not check:
            write_report(lib, built, warnings, report or (library.parent / "REPORT.md"))
            if songs == SONGS:
                names = {**{s.id: s.name for s in lib.sounds.values()}, **{c.id: c.name for c in lib.clips.values()}}
                write_json(ROOT / "data" / "campaign" / "library_names.json", dict(sorted(names.items())))
    if not quiet:
        for line in lib.log:
            print("  " + line)
        for w in warnings:
            print("WARNING " + w)
        for e in errors:
            print("ERROR " + e)
        print(f"{'OK' if not errors else 'FAILED'} in {time.time() - t0:.1f} s")
    return {"ok": not errors, "errors": errors, "warnings": warnings, "missions": built, "library": lib}


def write_report(lib: Library, built: list, warnings: list[str], path: Path) -> None:
    lines = ["# Content report", "", "Written by `python tools/content/build.py`. Do not edit; rebuild instead.", ""]
    lines += ["## Missions", "", "| Mission | Pack | Stem files | Placeholder | Owner | Default mix peak |", "| --- | --- | --- | --- | --- | --- |"]
    for m in built:
        st = getattr(m, "stats", {})
        lines.append(f"| {m.number} {m.title} | songs/{m.pack} | {st.get('files', 0)} | {st.get('placeholder_files', 0)} | "
                     f"{st.get('owner_files', 0)} | {st.get('default_mix_peak_db', '-')} dBFS |")
    lines += ["", "## Library renders in use", "", "| Clip | Part | Sound | Source |", "| --- | --- | --- | --- |"]
    used = set()
    for m in built:
        for u in m.usages.values():
            for c in u.clip_ref.options(m.choices):
                for s in u.sound_ref.options(m.choices):
                    used.add((c, u.family, s))
    for c, part, s in sorted(used):
        clip = lib.clips[c]
        owner = lib.owner_render_path(clip, part, s)
        src = f"owner `{rel(owner)}`" if owner.exists() else f"placeholder `{rel(lib.placeholder_path(clip, part, s))}`"
        lines.append(f"| {c} | {part} | {s} | {src} |")
    lines += ["", "## MIDI", "", "| Clip | Part | Origin |", "| --- | --- | --- |"]
    for cid, clip in sorted(lib.clips.items()):
        for part in clip.parts:
            lines.append(f"| {cid} | {part} | {clip.midi_origin.get(part, '?')} |")
    lines += ["", "## Listening checkpoints", "",
              "Equal lengths do not prove sync. After replacing audio, play the mission (or its practice) and listen at these",
              "song times: the first downbeat, every mode change and the last bar.", ""]
    for m in built:
        marks = [0] + [ph["start"] for ph in m.phases[1:]] + [m.duration_ticks - TICKS_PER_BAR]
        lines.append(f"- {m.number} {m.title}: " + ", ".join(f"bar {t // TICKS_PER_BAR + 1} ({tick_to_seconds(t):.1f} s)" for t in marks))
    if warnings:
        lines += ["", "## Warnings", ""] + [f"- {w}" for w in warnings]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("missions", nargs="*", help="level ids to build (default: all)")
    parser.add_argument("--check", action="store_true", help="validate only, write no audio")
    args = parser.parse_args()
    res = run(args.missions or None, args.check)
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
