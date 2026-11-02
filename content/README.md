# Content: the loop library and the missions

Everything the ten missions play is built from this folder by one command:

```
python tools/content/build.py            # all missions (about a minute); --check validates without writing audio
```

- `sounds.json`: every sound a mission can offer (id, family kick / snare / bass / other, friendly name).
- `library/<clip_id>/`: one musical clip at 174 BPM in 4/4. `clip.json` says its kind (`groove`, `fill`, `bass`,
  `accompaniment`), friendly name, length in bars, key (pitched clips) and where its MIDI came from. One MIDI file per
  part (`kick.mid`, `snare.mid`, `bass.mid`, `other.mid`) and one WAV per part and sound:
  - `library/<clip_id>/<part>__<sound_id>.wav`: **your render** (drop-in; the build only reads it),
  - `library/<clip_id>/placeholder/<part>__<sound_id>.wav`: the generated placeholder (open it in Ableton to hear what the
    file should contain; the build rewrites it, never your files).
- `missions/level_NN.json`: one mission: its choices, phases (which clip and sound plays where, which family is cued),
  sequences and rewards, accompaniment and battle data.
- `build_state.json`: written by the build (which MIDI each of your WAVs was rendered from). Commit it with your WAVs.
- `REPORT.md`: written by the build: what is still placeholder, warnings, listening checkpoints.

The exact list of files to render, with bar ranges and export settings, is `docs/CONTENT_TO_RENDER.md`. The rules the
build enforces are `docs/PRD.md` section 15. Godot ignores this folder (`.gdignore`); the game plays the Ogg stems the
build writes into `songs/`.

## Your own recordings: importing an Ableton batch

Mission 1 is built from the owner's exports in `ToAddTry1/` (kept exactly as exported; `.gdignore` keeps Godot out of
the folder and `*.asd` analysis files are git-ignored). The manifest `content/imports/first_watch.json` says which
export is which clip, part and sound; the importer files them into the library:

```
python tools/content/import_ableton.py content/imports/first_watch.json --check   # report what would be written
python tools/content/import_ableton.py content/imports/first_watch.json           # write the clips and sounds
python tools/content/build.py level_01                                            # build the mission from them
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

## Declared renders, audio-only clips, bound sounds, dependent choices

- **Declared renders** (`"sounds": {"bass": ["bass_sub_deep", ...]}` in `clip.json`): the clip plays only its own
  recordings. The build never makes a placeholder for a declared render (a missing file is an error, not a
  placeholder) and never pairs the clip with a sound it does not declare. A sound without a `synth` recipe in
  `sounds.json` can only be used this way.
- **Audio-only clips** (`"audio_only": true`, accompaniment only): no MIDI, nothing cued, just the recording. The
  build checks its length and headroom and plays it as a stem.
- **Bound sounds**: a phase can say `"kick_sound": "bound"` (any sound field) instead of a choice slot or a fixed id:
  the sound is whatever the chosen clip declares for that part. The pad label shows that sound's name (Mission 1's
  pads read "Half-Time Kick" and "Backbeat Snare" for the Half-Time groove).
- **Backing track choice**: a choice of kind `accompaniment` plus placements with `"clip": 1` (a slot of that choice)
  instead of a fixed clip id.
- **Dependent choices**: when the options of a sound choice (for example `bass_voice`) are declared renders of the
  clips of another choice (`bass`), the build writes `depends_on` and, per option, `with` (the clips the option plays)
  into the pack. The setup screen shows only the options that fit the chosen clip and swaps an option that no longer
  fits for that clip's default (or its first fitting recording), saying so; `MissionLoader.fit_dependents` does the
  same for a saved selection. The build refuses a mission whose default pairing does not fit, whose option plays none
  of the offered clips, or whose declared render is missing.

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
4. Offer the clips in a mission: add the clip ids to the pools in `content/missions/level_NN.json` (and the sound ids
   to the sound choice's pool; the build works out which recording fits which clip), set the defaults, add the ids to
   that mission's `new_options` in `data/campaign/campaign.json` so the unlock screen names them, then
   `python tools/content/build.py level_NN`. The build refuses invalid pairings and reports the loudest combination.
5. `bash tools/test.sh` (the mission tests load every combination), `python tools/balance_missions.py --missions mNN`
   if the arrangement changed, and `python tools/content/render_list.py` to refresh `docs/CONTENT_TO_RENDER.md`.

Re-running the importer is idempotent: identical inputs write identical files. Replacing an export and re-running
rewrites that clip's render; the build then notices the changed WAV through `build_state.json`.
