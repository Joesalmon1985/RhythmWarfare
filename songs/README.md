# Song packs

Three kinds of content live here: the loop library, the mission packs and the legacy duel packs.

## The loop library: `library/`

`library/index.json` (format `rhythm_warfare.library.v1`) lists every sound and clip the player's loadout can pick from:
for each clip its kind (groove, fill, bass, backing), the sounds it is offered with, its input cues (ticks inside one
8-bar loop: kick pad 1, snare pad 4, bass pads by pitch) and, for every part and sound, one 8-bar Ogg in
`library/loops/<clip>__<part>__<sound>.ogg` (exactly 529,655 frames at 48 kHz; a backing is 16 bars). The game plays
these loops, looped, with gain switches at phase boundaries, in every mission: music is the loadout, not the mission.
Written by `python tools/content/build.py` from `content/`; never edit by hand.

## Missions (schema 4): `m01_first_watch/` to `m10_last_light/`

| Pack | Mission | Bars | Form (D drums, B bass, 8 bars each) |
| --- | --- | --- | --- |
| `m01_first_watch` | 1 First Watch | 128 | `DDBDBDDBDBDBDDBD` |
| `m02_second_pulse` | 2 Second Pulse | 40 | `DDDDD` |
| `m03_hold_the_line` | 3 Hold the Line | 48 | `DBDBDB` |
| `m04_backbeat` | 4 Backbeat | 48 | `DDDDDD` |
| `m05_counterpoint` | 5 Counterpoint | 56 | `DBDBDBD` |
| `m06_fortress` | 6 Fortress | 56 | `DDDDDDD` |
| `m07_crossroads` | 7 Crossroads | 64 | `DBDBDBDB` |
| `m08_crossfire` | 8 Crossfire | 64 | `DDDDDDDD` |
| `m09_iron_rhythm` | 9 Iron Rhythm | 64 | `DDBDDBDD` |
| `m10_last_light` | 10 Last Light | 80 | `DDBDBDBDBD` |

Each pack is one `level.json` (schema 4): title, length, the phases from the form, the baked waves and intros, the
battlefield rules and the `base` the battlefield gives the player (production buildings, entries, defense points,
civilians). There is no audio in a pack: the loops live in `library/` and the mission only says which phases cue drums or
bass. Written by `python tools/content/build.py` from `content/missions/level_NN.json` (the old authoring, with per-mission
choices and full-length stems, is kept in `content/missions_legacy/`).

Whether a sound still plays a placeholder is in `library/index.json` (`sounds.<id>.placeholder`) and in `content/REPORT.md`.
To replace the placeholders with renders from Ableton, follow `docs/CONTENT_TO_RENDER.md`.

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
