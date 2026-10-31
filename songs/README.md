# Song packs

Two kinds of pack live here.

## Missions (schema 3): `m01_first_watch/` to `m10_*`

Written by `python tools/content/build.py` from `content/` (the loop library and the mission files); never edit them by
hand. Each holds `level.json` (schema 3, `docs/PRD.md` section 15), `audio/sNN__<clip>__<sound>.ogg` (one full-length
stem per offered clip and sound combination of each usage, 48 kHz stereo Ogg Vorbis, one bar of release tail after the
song) and `preview/<choice>__<option>.ogg` (four-bar auditions for the mission setup screen). The game loads the stems
that match the player's selection and plays them through the one synchronized transport.

Whether a pack still uses placeholder audio is in its `level.json` (`placeholder`, `content`) and in
`content/REPORT.md`. To replace the placeholders with renders from Ableton, follow `docs/CONTENT_TO_RENDER.md`.

## Legacy duel packs (schema 1): `level_01/`, `test_16/`

The two-sided duel of October 2026, kept working for a later multiplayer mode ("Free play" in the developer area).

A schema 1 pack is one folder: `level.json` plus an `audio/` directory holding four aligned stems.
The full contract is PRD section 9 (`docs/PRD.md`); the essentials:

- `level.json` (`schema_version` 1): `bpm` 174, `time_signature` [4, 4], `ticks_per_beat` 960,
  `song_offset_ms`, `duration_ticks` (bars x 3840, bar 1 = tick 0), `seed`, `stems` (relative
  paths for `kick`, `snare`, `bass`, `other`; wav, ogg or mp3), `battlefield`, `roster`, `rules`,
  `sections` (contiguous, covering tick 0 to `duration_ticks`), `notes` (`id`, `tick`, `lane`
  kick/snare/bass, `button` 1-4, `type` tap/hold, bass holds carry `duration_ticks`) and `enemy_events`
  (`id`, `tick`, `action`).
- Buttons: the game shows four unlabelled buttons. Kick notes are button 1 and snare notes button 4 (a
  `button` on them must say so, or be left out); bass notes carry any button 1-4, so a bass line can run
  across all four. A bass note with no `button` goes to buttons 2 and 3 alternately. One button never holds
  two notes at one tick or a note inside a hold.
- `event_seconds = song_offset_ms / 1000 + tick * 60 / (bpm * ticks_per_beat)`.
- Every stem starts at the same timeline point (bar 1 at sample 0), has the same sample rate and
  the same length. Nothing starts at or after `duration_ticks`; holds end inside the song; a lane
  never overlaps itself; a kick and a snare never share a tick.

## Packs

| Pack | What it is | Chart |
| --- | --- | --- |
| `level_01/` | The real first level, "First Contact": 64 bars, built from the owner's MIDI pack `Rhythm_Warfare_Level_01_MIDI.zip` | 138 kick taps, 111 snare taps, 38 bass holds, 34 bass taps (321 events), exactly the pack's `Player_Chart_Fragment.json` |
| `test_16/` | A 16-bar pack for the automated tests, cut from the owner's 174 BPM clip library (global bars 513-528) with `--all-hits` | 60 notes: every hit the chord rules allow |

Both are produced by `tools/make_song_pack.py`.

**All audio in these packs is synthesised placeholder sound** (numpy sine/noise kick, snare and
sub, plus hats, risers and a quiet chord pad on the "other" stem). It exists so the game can be
built and tested against correctly aligned stems. For `level_01` the owner's Ableton exports
(`audio/01_Kick.wav`, `02_Snare.wav`, `03_Bass.wav`, `04_Other.wav`, as named in the pack's
manifest) drop in by replacing the Ogg files and changing the extensions in `level.json`; the chart
does not change because the MIDI, not the audio, is its source.

### level_01 rules (from the MIDI pack's manifest)

- Kick and snare: every positive-velocity note-on in `01_Kick.mid` / `02_Snare.mid` is one tap.
  Lanes come from the files, not the MIDI channel; note lengths, velocity and pitch are ignored.
- Bass: every note-on in `03_Bass.mid` is one event; its length (note-off minus note-on) is a
  tap below 480 ticks and otherwise a hold with that `duration_ticks`. Its `button` comes from the
  note's pitch: the distinct bass pitches of the song are spread low-to-high over buttons 1 to 4. A
  bass note that would share button 1 or 4 with a kick or snare within 240 ticks (or anywhere inside
  its hold) moves to the inner button beside it; Level 01 runs bass under its drums, so almost all of
  its bass sits on buttons 2 and 3. Charts that keep bass phrases and drum phrases apart (the owner's
  plan for the next tracks) get the full four-button spread.
- Sections come from the MIDI section markers and are checked against the fragment.
- No density caps, no subsetting. The tool refuses to write the pack if the generated notes differ
  from `Player_Chart_Fragment.json` in any way.
- Enemy schedule: the authored level uses `--enemy-profile ramp --enemy-start 0.22 --enemy-end 0.42`
  (a seeded subset of the player's notes whose share climbs per section from 23% to 41%; 105 of 321
  events; re-authored on 28 Oct 2026 for the fortified bases and the mixed roster). `--enemy-profile mirror --enemy-accuracy f` keeps a flat fraction instead. The choice and
  the measured outcomes are in `docs/BALANCE.md`.

## Regenerating

The zips are downloaded data: extract each into its own fresh, empty folder outside the project
and run the tool with `python -I` (ffmpeg and ffprobe on PATH; numpy is the only package needed).

```bash
# level_01 from the owner's MIDI pack
mkdir -p /tmp/level01
python -I -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" \
    ~/Downloads/Rhythm_Warfare_Level_01_MIDI.zip /tmp/level01
python -I tools/make_song_pack.py --midi-pack /tmp/level01 --out songs/level_01 \
    --level-id level_01 --title "First Contact" --seed 27

# test_16 from the 174 BPM clip library
mkdir -p /tmp/clips
python -I -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" \
    ~/Downloads/Three_Movements_174BPM_MIDI_Clips_and_Assembly_Guide.zip /tmp/clips
python -I tools/make_song_pack.py --library /tmp/clips/Three_Movements_174BPM_Clip_Library \
    --out songs/test_16 --bars 513-528 --seed 7 --level-id test_16 --title "Test: 16 bars" --all-hits
```

If the zip extracts to a nested folder, point `--midi-pack` at the folder that holds
`Authoring_Manifest.json` and `--library` at the one that holds `01_Assembly_Placements.csv`.

Output is deterministic for the same inputs, arguments and seed. Other options: `--enemy-profile`,
`--enemy-accuracy`, `--enemy-start`, `--enemy-end`, `--sample-rate` (default 48000), `--keep-wav`
(keep the intermediate WAVs next to the Ogg files), and for the clip-library mode `--kicks-per-bar`,
`--snares-per-bar`, `--bass-per-bar` (maximum average charted notes per bar) or `--all-hits`.
Run `--help` for the full list.
