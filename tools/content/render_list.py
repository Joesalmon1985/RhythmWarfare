"""Writes docs/CONTENT_TO_RENDER.md: every MIDI and WAV file the owner creates to replace the placeholders.

    python tools/content/render_list.py      (also written by tools/content/build.py; the list follows the library)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import BPM, ROOT, SONGS_LIBRARY, TAIL_BARS, TICKS_PER_BAR, rel, tick_to_seconds, write_text_lf  # noqa: E402
from library import Library  # noqa: E402

KIND_TEXT = {"groove": "groove (kick and snare parts)", "fill": "fill (kick and snare parts)", "bass": "bass line",
             "backing": "backing (pad and hats on one bus)"}
KIND_ORDER = {"groove": 0, "fill": 1, "bass": 2, "backing": 3}
LOOP_TEXT = {"groove": "tiled to fill the 8-bar loop (a {bars}-bar groove repeats {n} times)",
             "fill": "placed in bar 8 of an otherwise silent 8-bar loop",
             "bass": "used as the 8-bar loop",
             "backing": "used as the {loop}-bar loop{cut}"}


def main() -> None:
    lib = Library().load()
    loops = lib.build_loops(SONGS_LIBRARY, write=False)
    write(lib, loops)


def write(lib: Library, loops: dict) -> None:
    sounds = {s.id: s.name for s in lib.sounds.values()}
    needed: dict[tuple[str, str], set[str]] = {}
    for (c, part, sid) in loops:
        needed.setdefault((c, part), set()).add(sid)
    in_place = {k: {sid for sid in v if lib.owner_render_path(lib.clips[k[0]], k[1], sid).exists()} for k, v in needed.items()}
    total_wav = sum(len(v) for v in needed.values())
    total_done = sum(len(v) for v in in_place.values())
    lines = [
        "# Content to render: every file that replaces a placeholder",
        "",
        "Written by `python tools/content/build.py` (or `python tools/content/render_list.py`) from the loop library; it follows the library.",
        f"There are **{len(lib.clips)} clips** and **{total_wav} WAV renders** below, of which "
        f"**{total_done} are your recordings already in place** (marked *in place*; the rest play generated placeholders). You never "
        "render whole songs or missions: the game plays one 8-bar loop per clip part and sound, so each clip is rendered once per "
        "sound it is offered with, and the build turns every render into its loop (`songs/library/loops/`).",
        "",
        "Batches exported from Ableton at 44.1 kHz (and MIDI longer than the clip) go through `tools/content/import_ableton.py`",
        "with a manifest like `content/imports/first_watch.json`: it converts, trims, gain-stages and files them (see",
        "`content/README.md`). Files already at 48 kHz can be dropped straight into the clip folder instead.",
        "",
        "## Export settings (every WAV)",
        "",
        "- 48,000 Hz, stereo (2 channels), 16-bit PCM WAV. No normalising, no dither needed, leave headroom (peaks below about -3 dBFS:",
        "  a kick, a snare, a bass and a backing play together).",
        f"- Tempo {BPM} BPM, 4/4, project start = bar 1. Render the clip's bars **from its bar 1**, starting exactly on the downbeat with",
        "  no pre-roll, and let the release ring: the file is the clip's musical length plus the release tail, **at most one extra bar**",
        "  (the build rejects longer files and warns when the tail is still sounding at its end). The loop folds the tail onto its",
        "  first bar, so a ringing tail is what makes the loop seam smooth.",
        "- One WAV per part and sound: render the kick part with the kick sound named in the file name, the snare part with the",
        "  snare sound, and so on. The backing is one bus (pad and hats together).",
        "- Ableton: Export Audio/Video, Rendered Track = the part's track (solo, or use the track's own export), Render Start = the clip's",
        "  first bar, Render Length = the clip's bars (+ up to one bar for the tail), Sample Rate 48000, Bit Depth 16, File Type WAV,",
        "  Normalize off, Create Analysis File off, Convert to Mono off.",
        "",
        "## How a render becomes a loop",
        "",
        "Every loop is exactly 8 bars (529,655 frames at 48 kHz) so the game can switch them on and off at any phase boundary:",
        "a 2-bar groove is placed at bars 1, 3, 5 and 7 and summed (its tail overlaps the next repetition); a 1-bar fill is placed",
        "in bar 8 of an otherwise silent loop; an 8-bar bass line or backing is the loop as it is; a backing longer than 16 bars",
        "(the generated ones are 32 to 48) is cut to its first 16 bars with a 10 ms fade. Whatever rings past the loop's end is",
        "added onto its start. The cues (what the player taps) come from the clip's MIDI: every kick note is pad 1, every snare",
        "note pad 4, bass notes spread over pads 1 to 4 by pitch (taps, at least 1440 ticks apart); ghost notes below the clip's",
        "`cue_min_velocity` are heard but not cued.",
        "",
        "## MIDI (only if you change the notes)",
        "",
        "The clip MIDI files below are the structure the cues are made from. Every one exists already (cut from your First_Three MIDI,",
        "or generated); you only export a new one when you want different notes. Export the clip as MIDI from Ableton (type 0 or 1,",
        "any PPQ; with no tempo in the file 174 BPM is assumed), save it over the file named in the table, then re-render every WAV of",
        "that part: the build refuses a WAV rendered from the earlier MIDI. The build checks the chart too: the same pad at least",
        "480 ticks apart, the same thumb (pads 1 and 2 left, 3 and 4 right) at least 480 ticks between pads, and every groove",
        "together with every fill (the groove's bars 1 to 7 and the fill's bar 8).",
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
        "tempo, meter and grid, the chart and headroom), uses your files instead of the placeholders, rebuilds the loops and the",
        "index in `songs/library/` (only the loops whose source changed are re-encoded), and lists what is still placeholder in",
        "`content/REPORT.md`. Your files are never written; delete one to go back to its placeholder. Commit your WAVs together",
        "with `content/build_state.json`.",
        "",
        "The placeholder of every file is already in place as a reference you can drag into Ableton:",
        "`content/library/<clip>/placeholder/<part>__<sound>.wav` (same length and timing your render should have). If that folder is",
        "missing on a fresh checkout, run the build once.",
        "",
        "## The files",
        "",
    ]
    for cid in sorted(lib.clips, key=lambda c: (KIND_ORDER[lib.clips[c].index_kind], c)):
        clip = lib.clips[cid]
        secs = tick_to_seconds(clip.bars * TICKS_PER_BAR)
        tail = tick_to_seconds((clip.bars + TAIL_BARS) * TICKS_PER_BAR)
        src = clip.data.get("source", {})
        if clip.audio_only:
            origin = "no MIDI (audio-only backing, never cued)"
        elif src.get("type") == "derived":
            origin = "your First_Three MIDI, " + ", ".join(sorted({f"{Path(x['file']).parts[2]} bars {x['bars'][0]}-{x['bars'][1]}"
                                                                   for p in src.get("parts", {}).values() for x in p}))
        elif src.get("type") == "generated":
            origin = "generated placeholder MIDI"
        elif src.get("type") == "imported":
            origin = f"your Ableton export (imported through `{src.get('manifest', '')}`)"
        else:
            origin = "your MIDI"
        loop_bars = 16 if clip.index_kind == "backing" and clip.bars >= 16 else 8
        loop = LOOP_TEXT[clip.index_kind].format(
            bars=clip.bars, n=8 // clip.bars if clip.bars and 8 % clip.bars == 0 else 1, loop=loop_bars,
            cut=f" (the clip's first {loop_bars} of {clip.bars} bars)" if clip.bars > loop_bars else "")
        lines.append(f"### `{cid}`: {clip.name}")
        lines.append("")
        lines.append(f"{KIND_TEXT[clip.index_kind]}, **{clip.bars} bars** ({secs:.2f} s; with the longest tail {tail:.2f} s), "
                     f"{('key ' + clip.key + ', ') if clip.key else ''}{'played only by its own recordings, ' if clip.sounds else ''}"
                     f"MIDI from {origin}. Loop: {loop}.")
        lines.append("")
        lines.append("| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for part in clip.parts:
            midi = "(none: audio only)" if clip.audio_only else f"`{rel(clip.folder / (part + '.mid'))}`"
            for sid in sorted(needed.get((cid, part), [])):
                done = sid in in_place.get((cid, part), set())
                ref = "*in place*" if done else f"`placeholder/{part}__{sid}.wav`"
                lines.append(f"| {part} | {midi} | `{rel(clip.folder / (part + '__' + sid + '.wav'))}` | {sounds[sid]} | {ref} | "
                             f"`{loops[(cid, part, sid)]['file']}` |")
        lines.append("")
    lines += ["## Sounds", "", "| Sound id | Name | Family |", "| --- | --- | --- |"]
    for sound in lib.sounds.values():
        lines.append(f"| `{sound.id}` | {sound.name} | {sound.family} |")
    lines += ["", "Adding a sound or a clip: add the sound to `content/sounds.json` and say what it produces in",
              "`data/campaign/instruments.json` (or copy `content/fixtures/example_groove/` to `content/library/<new_id>/` and edit",
              "its `clip.json`) and run the build: it adds the loops (placeholders until you drop your own WAVs in) to the index the",
              "player's loadout picks from.", ""]
    write_text_lf(ROOT / "docs" / "CONTENT_TO_RENDER.md", "\n".join(lines))
    print(f"docs/CONTENT_TO_RENDER.md: {len(lib.clips)} clips, {total_wav} WAV files ({total_done} in place)")


if __name__ == "__main__":
    main()
