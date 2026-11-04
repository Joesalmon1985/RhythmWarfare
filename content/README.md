# Content: the loop library and the missions

The player has one loadout (groove, fill, kick sound, snare sound, bass line, bass sound, backing) that plays in every
mission. The game plays 8-bar loops, one per clip part and sound, looped, with gain switches at phase boundaries. A mission
no longer authors music: it defines a title, a length, the form (which 8-bar phases are drums or bass), the battlefield and
the waves. Everything is built from this folder by one command:

```
python tools/content/build.py              # library, then every mission (about 25 s from scratch, under a second when nothing changed)
python tools/content/build.py level_03     # the library, then one mission
python tools/content/build.py --check      # validate everything, write nothing
```

- `sounds.json`: every sound (id, family kick / snare / bass / other, friendly name, the placeholder synth recipe).
  What a sound produces in battle (kicks make infantry, snares build defenses, bass sounds make vehicles) and its one-line
  blurb are in `data/campaign/instruments.json`; the build refuses a sound without an entry.
- `library/<clip_id>/`: one musical clip at 174 BPM in 4/4. `clip.json` says its kind (`groove`, `fill`, `bass`,
  `accompaniment`, which the index calls `backing`), friendly name, length in bars, key (pitched clips), optional
  `cue_min_velocity` (ghost notes below it are heard but not cued) and where its MIDI came from. One MIDI file per part
  (`kick.mid`, `snare.mid`, `bass.mid`, `other.mid`) and one WAV per part and sound:
  - `library/<clip_id>/<part>__<sound_id>.wav`: **your render** (drop-in; the build only reads it),
  - `library/<clip_id>/placeholder/<part>__<sound_id>.wav`: the generated placeholder (open it in Ableton to hear what the
    file should contain; the build rewrites it, never your files).
- `missions/level_NN.json`: one mission, nothing else: `level_id`, `number`, `title`, `pack`, `bars`, `seed`, `form`
  (one letter per 8-bar phase: `D` drums, `B` bass; `bars` is 8 times its length), `battle` (`battlefield`, the waves
  file, optional `rules`), `intros` (hint lines by bar) and a `note`. `missions_legacy/` keeps the old authoring (choices,
  phases, stems), which `tools/content/export_midi.py` still reads.
- The battle side of a mission lives outside this folder: `data/campaign/waves/level_NN.json` (the `rules` block:
  `objective_hp`, `sockets_per_point`, `units_per_point`, `start_units` such as five riflemen per choke point, and
  the `waves` by bar, each with an `entry` and a `target` class `defenses`, `civilians` or `core`) and
  `data/battlefields/<id>.json` (mission 1 plays on `village_01`: houses, civilians, the barracks). The build bakes
  both into `level.json` and derives its `base` block (production buildings, entries, defense points, civilians) from the
  battlefield, so rebuild after editing them.
- `build_state.json`: written by the build (which MIDI each of your WAVs was rendered from, the generated placeholders,
  the source of every loop so an unchanged one is not re-encoded). Commit it with your WAVs.
- `REPORT.md`: written by the build: the loops table (owner or placeholder, peak), the missions table, warnings.

What the build writes: `songs/library/index.json` (sounds, clips, cues, loop files, peaks) and
`songs/library/loops/<clip>__<part>__<sound>.ogg`, `songs/mNN_*/level.json` (schema 4, no audio), `content/REPORT.md`,
`docs/CONTENT_TO_RENDER.md` and `data/campaign/library_names.json`. The index and the packs are byte-identical when
nothing changed. Godot ignores this folder (`.gdignore`); the game plays the loops in `songs/library/`.

**How a render becomes a loop.** Exactly 8 bars (529,655 frames at 48 kHz; a backing is 16 bars): a 2-bar groove is placed
at bars 1, 3, 5 and 7 and summed, a 1-bar fill sits in bar 8, an 8-bar bass line or backing is used as it is, a backing
longer than 16 bars (the generated ones, 32 to 48) is cut to its first 16 with a 10 ms fade; whatever rings past the end is
added onto the start so a tail wraps around.

**Cues and the chart.** Kick cues are pad 1, snare cues pad 4, bass cues are spread over pads 1 to 4 by pitch (lowest
left; one pitch alone uses pad 2), taps only, at least 1440 ticks apart (`data/campaign/rules.json` `chart.bass`). The build
checks every clip (same pad at least 480 ticks apart, the same thumb at least 480 between pads) and every groove together
with every fill (the groove's bars 1 to 7 and the fill's bar 8); an error names the clip or the pair. Prefer a clip's
`cue_min_velocity` or a note edit in Ableton to a looser rule.

The exact list of files to render, with export settings, is `docs/CONTENT_TO_RENDER.md`. The rules the build enforces are
`docs/PRD.md` section 15.

## Your own recordings: importing an Ableton batch

Mission 1 is built from the owner's exports in `ToAddTry1/` (kept exactly as exported; `.gdignore` keeps Godot out of
the folder and `*.asd` analysis files are git-ignored). The manifest `content/imports/first_watch.json` says which
export is which clip, part and sound; the importer files them into the library:

```
python tools/content/import_ableton.py content/imports/first_watch.json --check   # report what would be written
python tools/content/import_ableton.py content/imports/first_watch.json           # write the clips and sounds
python tools/content/build.py                                                      # build the loops from them
```

What the importer does with each file (the originals are never modified):
- MIDI: keeps the first `bars` bars (the drum exports are 64 bars long; the clip is 8), rescales to 960 PPQ, writes
  174 BPM into the file, keeps note lengths and velocities. The export has no tempo of its own: 174 BPM is the
  project tempo, confirmed by every WAV being exactly 8 bars at 174 BPM.
- WAV: resamples 44.1 kHz to 48 kHz with the SoX resampler (no time-stretch, no dither), cuts to the clip's bars plus
  whatever tail still sounds within one bar (Other1's silent bars 9 to 14 are dropped), applies the family gain rule
  (`levels`: the largest gain that keeps the peak under `peak_db` and, when given, brings the RMS to `rms_db` so the
  recordings of one family sit at one level), then `trim_db` for the whole mix, and a short raised-cosine fade
  (`end_fade_ms`) only when the recording is cut mid-note so the loop never clicks. Nothing is normalised in place.
- `clip.json`: the clip's kind, name, bars, key, a `sounds` block (the renders it was recorded with) and `source`
  (type `imported`, the manifest, the SHA-256 of every export, the gain applied). Sounds the manifest introduces are
  merged into `sounds.json` with their friendly names.

The importer prints a report (sample rate, peak before and after, attack of the first note against the MIDI, trimmed
bars, fade) and refuses an export that does not cover the clip, a MIDI with no notes in the clip's bars, or a sound
whose family does not match the part.

## Declared renders and audio-only clips

- **Declared renders** (`"sounds": {"bass": ["bass_sub_deep", ...]}` in `clip.json`): the clip plays only its own
  recordings (the index marks it `bound`). The build never makes a placeholder for a declared render (a missing file is
  an error, not a placeholder) and never pairs the clip with a sound it does not declare. A sound without a `synth`
  recipe in `sounds.json` can only be used this way. A clip with no declaration is offered with every sound of its family
  that no clip declares (the generated kicks, snares and bass sounds), each with a placeholder until you render it.
- **Audio-only clips** (`"audio_only": true`, accompaniment only): no MIDI, nothing cued, just the recording; the index
  lists it as a backing with its one sound (`hats_driving`; the generated backings use `ensemble`).

## Adding further phrases (the owner's path)

1. Export from Ableton at 174 BPM, project start = bar 1: for a cued part (kick, snare, bass) the MIDI clip and one WAV
   per sound you want to offer, rendered from that MIDI, starting on the downbeat with no pre-roll; for a backing loop
   just the WAV. 44.1 kHz is fine (the importer converts); 48 kHz is fine too. Any length that covers the clip.
2. Put the files in a folder (one per batch, like `ToAddTry1/`) and write a manifest next to the existing one
   (`content/imports/<batch>.json`): `source_dir`, `bars`, `levels`, `trim_db`, the new `sounds` (id, family,
   friendly name) and the `clips` (id, kind, name, key, note, `parts` with the MIDI file and the `renders`
   {sound id: WAV file}; `"audio_only": true` for a backing loop with no MIDI). Ids are stable and never shown; the
   `name` fields are what the player reads.
3. `python tools/content/import_ableton.py content/imports/<batch>.json --check`, read the report, then run it
   without `--check`.
4. Say what each new sound produces in `data/campaign/instruments.json`, then `python tools/content/build.py`: the clips and
   sounds join `songs/library/index.json` with their loops, and the player's loadout can pick them (no mission file
   changes; the build refuses an unplayable chart or a missing instruments entry).
5. `bash tools/test.sh`; `docs/CONTENT_TO_RENDER.md` is refreshed by the build.

Re-running the importer is idempotent: identical inputs write identical files. Replacing an export and re-running
rewrites that clip's render; the build then notices the changed WAV through `build_state.json`.

## MIDI for missions 2 to 10 (the owner's render path)

Missions 2 to 10 arrange library clips and have no full-song MIDI, so `python tools/content/export_midi.py` (all of them, or
`level_04 level_06`) writes `midi_export/level_NN_<title>/`: a README, the default groove, bass line and backing as 8-bar
loops (`Kick_A`, `Snare_A`, `Bass_A`, `Other_Pad`, `Other_Hats`), rule-based alternatives `Kick_B/C`, `Snare_B/C`, `Bass_B/C`
(seeded from the mission, the same every run) and `Arrangement_A.mid`, a four-track reference of the whole mission. It also writes
the manifest `content/imports/level_NN.json` naming the WAVs to render from them (named after the MIDI: `Kick_A.wav`; the WAVs are
git-ignored). Render them in Ableton, then, per mission:

```
python tools/content/import_ableton.py content/imports/level_NN.json --check
python tools/content/import_ableton.py content/imports/level_NN.json
python tools/content/build.py
```

The imported clips join the library and the loadout can pick them. The exporter reads the old authoring in
`content/missions_legacy/` (`MISSIONS_LEGACY` in `tools/content/common.py`), not `content/missions/`, whose files no longer
carry choices or phases. `midi_export/README.md` has the workflow;
`tools/content/test_export.py` tests the export and runs a synthetic round trip through the importer.

## Recorded stems for a story chapter

`tools/content/import_recorded.py <manifest>` turns one recorded export set (Drums, Bass and Synth WAV with MIDI) into a chapter's own music pack, outside the loop library (`content/imports/story_warehouse.json` is the Night One example). It verifies the recordings' tempo against the MIDI, maps source beats to the 174 BPM grid, folds release tails into equal eight-bar loops and writes the cues. See `docs/STORY_CAMPAIGN_HANDOVER.md`.
