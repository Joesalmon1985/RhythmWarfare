"""Writes docs/CONTENT_TO_RENDER.md: every MIDI and WAV file the owner creates to replace the placeholders.

    python tools/content/render_list.py      (after tools/content/build.py; the list follows the library and missions)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import BPM, MISSIONS, ROOT, TAIL_BARS, TICKS_PER_BAR, rel, tick_to_seconds  # noqa: E402
from library import Library  # noqa: E402
import mission as mission_mod  # noqa: E402

KIND_TEXT = {"groove": "groove (kick and snare parts)", "fill": "fill (kick and snare parts)", "bass": "bass line", "accompaniment": "accompaniment (pad and hats on one bus)"}


def main() -> None:
    lib = Library().load()
    missions = []
    for path in sorted(MISSIONS.glob("level_*.json")):
        m = mission_mod.Mission(path, lib)
        m.parse()
        m.arrange()
        missions.append(m)
    needed: dict[tuple[str, str], set[str]] = {}
    used_in: dict[str, set[int]] = {}
    for m in missions:
        for u in m.usages.values():
            for c in u.clip_ref.options(m.choices):
                used_in.setdefault(c, set()).add(m.number)
                for s in u.sound_ref.options(m.choices):
                    needed.setdefault((c, u.family), set()).add(s)
    sounds = {s.id: s.name for s in lib.sounds.values()}
    total_wav = sum(len(v) for v in needed.values())
    lines = [
        "# Content to render: every file that replaces a placeholder",
        "",
        "Written by `python tools/content/render_list.py` from the loop library and the ten missions; rerun it after changing either.",
        f"Everything in the game is placeholder sound today. There are **{len([c for c in lib.clips if c in used_in])} clips** and "
        f"**{total_wav} WAV renders** below. You never render whole songs: each clip is rendered once per sound it is offered with, "
        "and the build assembles the missions from those pieces.",
        "",
        "## Export settings (every WAV)",
        "",
        "- 48,000 Hz, stereo (2 channels), 16-bit PCM WAV. No normalising, no dither needed, leave headroom (peaks below about -3 dBFS:",
        "  up to five stems play together).",
        f"- Tempo {BPM} BPM, 4/4, project start = bar 1. Render the clip's bars **from its bar 1**, starting exactly on the downbeat with",
        "  no pre-roll, and let the release ring: the file is the clip's musical length plus the release tail, **at most one extra bar**",
        "  (the build rejects longer files and warns when the tail is still sounding at its end).",
        "- One WAV per part and sound: render the kick part with the kick sound named in the file name, the snare part with the",
        "  snare sound, and so on. The accompaniment is one bus (pad and hats together).",
        "- Ableton: Export Audio/Video, Rendered Track = the part's track (solo, or use the track's own export), Render Start = the clip's",
        "  first bar, Render Length = the clip's bars (+ up to one bar for the tail), Sample Rate 48000, Bit Depth 16, File Type WAV,",
        "  Normalize off, Create Analysis File off, Convert to Mono off.",
        "",
        "## MIDI (only if you change the notes)",
        "",
        "The clip MIDI files below are the structure the cues are made from. Every one exists already (cut from your First_Three MIDI,",
        "or generated); you only export a new one when you want different notes. Export the clip as MIDI from Ableton (type 0 or 1,",
        "any PPQ; with no tempo in the file 174 BPM is assumed), save it over the file named in the table, then re-render every WAV of",
        "that part: the build refuses a WAV rendered from the earlier MIDI. Note lengths count (bass notes of an eighth or longer are",
        "holds) and a hold must end inside its four-bar sequence.",
        "",
        "## Where the files go and the one command",
        "",
        "Put each WAV in the clip's folder under the name given (`content/library/<clip>/<part>__<sound>.wav`) and run, from the",
        "project folder:",
        "",
        "```",
        "python tools/content/build.py",
        "```",
        "",
        "It checks every file (rate, channels, bit depth, length, tail, silence, alignment of the attacks to the MIDI, the MIDI's",
        "tempo, meter and grid, cues, holds and headroom), uses your files instead of the placeholders, rebuilds the game's stems and",
        "previews in `songs/`, and lists what is still placeholder in `content/REPORT.md` with the times to listen at. Your files are",
        "never written; delete one to go back to its placeholder. Commit your WAVs together with `content/build_state.json`. Then",
        "rebuild the exports (`docs/EXPORT.md`).",
        "",
        "The placeholder of every file is already in place as a reference you can drag into Ableton:",
        "`content/library/<clip>/placeholder/<part>__<sound>.wav` (same length and timing your render should have). If that folder is",
        "missing on a fresh checkout, run the build once.",
        "",
        "## The files",
        "",
    ]
    for cid in sorted(used_in, key=lambda c: (min(used_in[c]), c)):
        clip = lib.clips[cid]
        secs = tick_to_seconds(clip.bars * TICKS_PER_BAR)
        tail = tick_to_seconds((clip.bars + TAIL_BARS) * TICKS_PER_BAR)
        src = clip.data.get("source", {})
        origin = "your First_Three MIDI, " + ", ".join(sorted({f"{Path(x['file']).parts[2]} bars {x['bars'][0]}-{x['bars'][1]}" for p in src.get("parts", {}).values() for x in p})) \
            if src.get("type") == "derived" else ("generated placeholder MIDI" if src.get("type") == "generated" else "your MIDI")
        lines.append(f"### `{cid}`: {clip.name}")
        lines.append("")
        lines.append(f"{KIND_TEXT[clip.kind]}, **{clip.bars} bars** ({secs:.2f} s; with the longest tail {tail:.2f} s), "
                     f"{('key ' + clip.key + ', ') if clip.key else ''}used in mission{'s' if len(used_in[cid]) > 1 else ''} "
                     f"{', '.join(str(n) for n in sorted(used_in[cid]))}. MIDI from {origin}.")
        lines.append("")
        lines.append("| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |")
        lines.append("| --- | --- | --- | --- | --- |")
        for part in clip.parts:
            for s in sorted(needed.get((cid, part), [])):
                lines.append(f"| {part} | `{rel(clip.folder / (part + '.mid'))}` | `{rel(clip.folder / (part + '__' + s + '.wav'))}` | {sounds[s]} | "
                             f"`placeholder/{part}__{s}.wav` |")
        lines.append("")
    lines += ["## Sounds", "", "| Sound id | Name | Family |", "| --- | --- | --- |"]
    for s in lib.sounds.values():
        lines.append(f"| `{s.id}` | {s.name} | {s.family} |")
    lines += ["", "Adding a sound or a clip: add the sound to `content/sounds.json` (or copy `content/fixtures/example_groove/` to",
              "`content/library/<new_id>/` and edit its `clip.json`), offer it in a mission's choices (`content/missions/level_NN.json`)",
              "and run the build: it lists the renders it still needs as placeholders.", ""]
    (ROOT / "docs" / "CONTENT_TO_RENDER.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"docs/CONTENT_TO_RENDER.md: {len(used_in)} clips, {total_wav} WAV files")


if __name__ == "__main__":
    main()
