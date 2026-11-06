# Music transitions: design of the DJ-style transition engine

Planning document, 6 November 2026. No game code was changed in writing it. It is the brief for stage M2 of
`docs/parallel-development/ONE_PC_PLAN.md`, built on this PC (Ryzen 7 5800X, 32 GB, RTX 3060, Windows 11,
Godot 4.5.1) by the music stream, behind the seam that stage M1 installs. It fits
`INTEGRATION_CONTRACT.md` and `contract/transition_port.gd` (version 1) without changes.

Words used here: **music stream** and **narrative stream** are the two lines of work of the one-PC plan;
**M1** is the milestone that finishes track scenes and installs the seam; **M2** is this engine. **T** is the
song time of the boundary (the downbeat where the scene changes). Bars are 4 beats. "Incoming bar n" counts
bars of the incoming track's grid from T (bar 0 starts at T).

Status words, as in the rest of this folder: implemented / partial / missing, and for what is to be built
straightforward / complex / uncertain. "To verify in the spike" marks every engine fact I could not confirm
from the Godot 4.5 source or documentation.

## 1. Today, in a page

| Part | State | Facts this design relies on |
|---|---|---|
| The clock | implemented | `SongClock.audio_time()` = `transport.playback_position()` + `AudioServer.get_time_since_last_mix()` - output latency, the latency read once in `begin_countdown()`. Monotonic, frozen while paused. `judge_time()` subtracts `calibration_ms`. In the run the transport is `RunAudio.player`, a silent mono 8-bit loop of 64 beats (`RunAudio.silent_loop`) at an artificial rate (`clock_rate`: 174 BPM gives 8,700 Hz). `clock_rate`, `frames_per_beat` and `silent_loop` take an `int` BPM |
| Scene music | implemented (loop scenes) | `RunAudio` plays each phase's loop voices as separate `AudioStreamPlayer`s started on the clock with lateness compensation (`play(from)`, `from = now + time_to_next_mix - t`), gains ramped per frame |
| Transitions | partial | A scene change fades every old voice linearly over `mix.phase_fade_s` = 0.6 s **starting at** the new downbeat, while the new drums ramp in over 0.35 s. Optional bass carry for 16 beats within one music family. A path hand-off swaps the clock stream on the downbeat (`schedule_clock_swap`, `_swap_clock`, with `song_base = t - mix_period` to avoid the 88 ms jump found earlier). No crossfade curve, no beat matching, no tempo ramp, no stretching, no `pitch_scale` anywhere in `src/` |
| Limiter | missing in the run | `AudioEffectHardLimiter` exists only in the standalone track mode (`src/track/track_play.gd`, ceiling -0.3 dB) |
| Track packs | implemented, outside Git | `track.json` (`rhythm_warfare.track.v2`): `tempo.bpm` (float), `tempo.first_downbeat_s`, `tempo.confidence`, `sections[]` with roles, `voices[]` and `backing[]` (3 to 5 stems in the packs on this PC), charts. `source.tempo_detail` has `constant` and `drift_ms_max_abs`. Packs live in `C:\Users\joesa\rw-audio-work\packs`: 47 folders, 46 with `track.json`, 41 usable (5 fail validation, one is empty) |
| Track stems as one group | implemented (standalone mode) | `TrackTransport.load_pack_streams` puts all stems in one `AudioStreamSynchronized` on one player; per-stem gain by `set_sync_stream_volume`, 30 ms ramps |
| Track scenes, logic half | implemented, virtual clock only | `RunTrackPlan.compute`: entry bar E = first drop bar - 16 (`lead_in_bars`), laps of 16 bars, scene time 0 = downbeat of bar E. The engine re-grids at `_enter` (`_regrid`), emits `tempo`, `track_start`, `track_lap`, `track_last_lap`, `track_extend`, `track_wrap`, `track_end`. The choice is fixed at beat 60.5 of a departure lap (`hotspot_commit`, `track_last_lap`); the boundary is beat 64 |
| Track scenes, audio and wiring | missing (stage M1, being built now) | Nobody has heard a track scene. M1 delivers, by `docs/TRACK_SCENES_HANDOVER.md`: the group on `track_start` from `track_t`, seek on `track_wrap`, fade on `track_end` "with the door", stop on the Bassment hand-off, mutes, loading off the main thread, the limiter, a float-tempo clock (M1.4), and `TransitionDirector` in `&"cut"` mode on `src/transition/transition_port.gd` (present in this worktree as a byte copy of the contract) |
| Measurements | missing | Every timing figure so far comes from the Dummy driver (mix chunk 88.5 ms, no output latency). Nothing measured on WASAPI or on a phone |

What M2 adds, in one sentence: when a scene changes, the incoming track starts on T at its own tempo and
becomes the clock's grid, while the outgoing track carries on underneath as a fading tail that is silent at
least 4 bars before the incoming first drop.

## 2. The transition model

### 2.1 One transition, lock to completed

```
outgoing grid (its own tempo)            T = boundary                    incoming grid (its own tempo)
 lap k of the outgoing scene                                            lap 1 of the incoming scene (the lead-in)
 beat 48      56     60 60.5   64 = 0                                                              E+16 = drop
 |------------|------|--|------|--------|--------|--------|-- ... ---|--------|--------|--------|---|
 bar 12       14     15 lock   bar 0    1        2        4           8        12       14       16
                        ^      ^        ^        ^                             ^                 ^
                     locked  switched                                      completed          first drop
                     (plan)  incoming starts at bar E, rate 1.0          (tail silent)    (no tail, 4 bars clear)
                             tail rate set to r

 outgoing cues  ######## (block 3 cues end by beat 60: the 4-beat rest, none survive into the blend)
 incoming cues           ######## ######## (charted from the incoming track, judged on the incoming grid)

 tail stems (outgoing track, played on at rate r = in_bpm / out_bpm)
   bass                  \__                                   (gone by incoming bar 1)
   drums, kick, tops     \_____                                (gone by bar 2)
   backing               \_____                                (gone by bar 2: it may hold bleed of kick and bass)
   other, vocals         ===========\_______________________   (hold to bar 2, fall to silence by bar W)
   tail high-pass        20 Hz ------> 250 Hz by bar 4, then held
 incoming stems          all at pack gain from T (never faded in, never stretched, never re-pitched)
```

W is the blend window in incoming bars: 12 in the normal case (16 bars of lead-in minus the 4 clear bars).
The contract's `plan.blend_beats` is 4W (48) and `plan.complete_t` is T + W bars of the incoming tempo.

Nothing audible that depends on the destination happens before `locked` (contract rule 4). Between the lock
and T (3.5 outgoing beats) the director only prepares: it attaches the incoming stems to a stopped player at
-80 dB and schedules the start.

### 2.2 Worked example with two real tracks

A real route of the main run: `warehouse.balcony` to `warehouse.chill`. Their first-choice tracks, with the
values from the packs on this PC:

| | Outgoing: `chase_status_no_problem_original_mix` | Incoming: `stimpy_party_last_sounds` |
|---|---|---|
| `tempo.bpm` | 174.9997 | 172.0000 |
| `tempo.first_downbeat_s` | 0.0166 s | 0.5787 s |
| beat, bar, lap (16 bars) | 0.342858 s, 1.371431 s, 21.94289 s | 0.348837 s, 1.395349 s, 22.32558 s |
| first drop section | bar 40 (54.874 s) | bar 31 (43.835 s) |
| entry bar E, `entry_t` | 24, 32.931 s | 15, 21.509 s |
| laps (half-way rule) | 5 | 5 |
| stems | drums, other, vocals, backing (no bass stem) | drums, bass, other, vocals, backing |
| `tempo_detail` | constant, drift 4.1 ms max | constant, drift 0.8 ms max |

The player touches the door to the chill-out room in lap 2 of the balcony and leaves at the end of it.

| Event | Song time | Outgoing track time | Incoming track time |
|---|---|---|---|
| Lock (beat 60.5 of lap 2) | T - 1.2000 s | 75.617 s (bar 55.1) | (not playing) |
| Boundary, `switched` | T | 76.817 s (bar 56) | 21.509 s (bar 15 = E) |
| Bass and backing gone | T + 1.395 s (incoming bar 1) | 78.188 s | 22.904 s |
| Drums gone | T + 2.791 s (bar 2) | 79.560 s | 24.300 s |
| Tail silent, `completed` | T + 16.744 s (bar 12) | 93.274 s (bar 68) | 38.253 s |
| Incoming first drop | T + 22.326 s (bar 16) | | 43.835 s (bar 31) |

- Mode: tempo ratio r = 172.0000 / 174.9997 = 0.982859, a difference of 1.71%, so `blend`.
- The tail is slowed by `pitch_scale = 0.982859` from T: a pitch change of 1200 x log2(0.982859) =
  **-29.9 cents** (under a third of a semitone). In 16.744 s of playing it advances 16.457 s of its own
  audio, exactly 12 of its own bars, so its bar lines fall on the incoming bar lines.
- The tail plays bars 56 to 68 of the outgoing track, inside its first drop (bars 40 to 91). Because that is
  the loud part, the rhythm section leaves within 2 bars; the synths and vocals carry the hand-over.
- Plan sent with `locked`: `{mode: &"blend", fallback: false, outgoing_bpm: 174.9997, incoming_bpm: 172.0,
  blend_beats: 48, complete_t: T + 16.744}`.
- During the blend the incoming lead-in is the stimpy build-up (bars 15 to 31; its focus is the drums up to
  bar 24, then the synths), so the player is already playing incoming cues over the tail.

For comparison, the other ratios the catalogue produces:

| Pair (BPM) | r | Pitch of the tail | Mode |
|---|---|---|---|
| 174 to 175 | 1.00575 | +9.9 cents | blend |
| 172 to 176 | 1.02326 | +39.8 cents | blend |
| 172 to 177 | 1.02907 | +49.6 cents | blend (the widest pair in the catalogue that blends) |
| 168 to 172 | 1.02381 | +40.7 cents | blend |
| 168 to 174 | 1.03571 | +60.8 cents | echo_out |
| 140 to 174 | 1.24286 | +376 cents | echo_out |

An `echo_out` example: leaving `ternion_sound_artifice` (140.0040 BPM, squadron `base.c03`) into a 174 BPM
track. No rate matching (the tail plays at 1.0). At T the tail's drums, bass and backing fall in half an incoming
beat (0.17 s), the synths and vocals in one bar, through an echo of 3/4 of an outgoing beat (0.321 s) with
feedback 0.4; the tail bus is forced silent at T + 2 incoming bars (2.759 s), `blend_beats` 8.

### 2.3 The tempo distribution, checked

Read on this PC from the 46 packs' `track.json` and, for the 15 recordings without a pack, the catalogue's
`quick.bpm`: **58 of 61 recordings lie between 172 and 176 BPM** (28 round to 174, 21 to 175, 6 to 172, 1 to
173, 2 to 176). The three outside are 140.004 (`ternion_sound_artifice`), 168.0008
(`mantra_decibella_tim_reaper_stars_are_calling`, currently failing validation) and 176.9999
(`amplify_crossy_badman`). This agrees with the planning decision. Two consequences:

- 177 BPM is an outlier only by the 172 to 176 label. It blends with every track in the cluster (at most
  49.6 cents against 172). 168 blends with 172 and 173 and echoes out against 174 and above.
- **No pair in the catalogue is near 2:1.** The path tempos of ordinary scenes (124, 140, 145) are not near
  2:1 with 174 either. `halftime_blend` is designed and tested on synthetic fixtures but no real
  transition will use it today.

## 3. Metadata

### 3.1 What comes from the pack and is never duplicated

`tempo.bpm`, `tempo.first_downbeat_s`, `tempo.confidence`, `beats_per_bar` (4), `duration_s`, `sections[]`
(roles and bar-aligned times), `voices[]` and `backing[]` (keys and gains), `source.tempo_detail.constant`
and `.drift_ms_max_abs`. The same values are in Git in `content/music/tracks/<id>.json` (`tempo.constant`,
`tempo.drift_ms_max`, `sections`, `voices`), which is what the planner's tests read, so that the suite never
needs the packs. The sidecar never repeats any of these; it only corrects or adds.

### 3.2 The sidecar `content/music/transitions/<track id>.json`

Text, in Git, owned by the music stream. One per track; a missing file means "use the pack as it is".

```json
{
  "format": "rhythm_warfare.transition.v1",
  "track": "stimpy_party_last_sounds",
  "first_drop_s": 43.80,
  "second_drop_s": null,
  "downbeat_offset_beats": 0,
  "intro_start_s": null,
  "outro_start_s": null,
  "mix_in_bar": null,
  "mix_out_bar": null,
  "no_blend": false,
  "linger": null,
  "checked": "2026-11-12",
  "note": ""
}
```

| Field | Type, unit | Default | Meaning and validation |
|---|---|---|---|
| `format` | string | required | exactly `rhythm_warfare.transition.v1` |
| `track` | string | required | equals the file name and a catalogue id |
| `first_drop_s` | number, s from the start of the audio, or null | null: the first `drop` section of the pack | The owner's first drop. 1.0 <= value <= `duration_s` - 16 bars. Snapped (3.3). Replaces the first drop section's start in `RunTrackPlan`, so a corrected drop also moves the scene's entry bar E |
| `second_drop_s` | number or null | null: the second `drop` section | Same rules; must be > `first_drop_s` + 16 bars. Used by `entry: "drop2"` |
| `downbeat_offset_beats` | integer, -3 to 3 | 0 | Corrects the pack's bar phase: the effective first downbeat is `first_downbeat_s + k x beat` (plus 4 beats if that is negative). Set when the snap says the grid is a whole number of beats out (3.3) |
| `intro_start_s` | number or null | null | Where the track's own mix-in intro begins. Informational; checked to be before the first drop |
| `outro_start_s` | number or null | null | Where the track starts winding down. Its snapped bar is the default of `mix_out_bar` |
| `mix_in_bar` | integer bar or null | null: first drop bar - `lead_in_bars` | Entry bar E for every scene that plays this track. Must lie between first drop bar - 16 and first drop bar - 6. Order of precedence: `start_bar` in `track_scenes.json`, then `mix_in_bar`, then the drop rule |
| `mix_out_bar` | integer bar or null | null | From this bar on the track is in its outro: a tail starting at or after it uses the long recipe (drums leave over 4 bars instead of 2). Without it, the pack's section roles decide (a tail starting in a `breakdown` or `outro` section uses the long recipe) |
| `no_blend` | bool | false | Never overlap this track with another: every transition into or out of it is `cut` |
| `linger` | list of voice keys or null | null: `other`, `vocals` | Which stems may linger after incoming bar 2. Every key must be a voice of the pack |
| `checked` | date string or null | null | Set by the sheet tool when the owner has looked at the track |
| `note` | string | "" | Free text |

Unknown keys are errors, in the style of `RunTrackScenes._check_entry`. Errors are sentences naming the file
and the field. An invalid sidecar is ignored as a whole (warning), and the track plays from its pack.

### 3.3 Snapping a manual drop to the grid

A drop time alone is not a grid: the grid is `first_downbeat_s`, `bpm` and 4 beats a bar from the pack. The
owner's time is snapped to the nearest bar line of that grid, and the distance says how far the two agree.

```
fd'   = first_downbeat_s + downbeat_offset_beats * beat
bar_f = (first_drop_s - fd') / bar           (fractional bar)
bar   = round(bar_f)                         (the snapped drop bar, used everywhere)
e     = first_drop_s - (fd' + bar * bar)     (snap error, seconds); e_b = e / beat (beats, -2 < e_b <= 2)
```

| Snap error | Verdict | Effect |
|---|---|---|
| \|e_b\| <= 0.25 beat (<= 87 ms at 172) | agrees | none |
| within 0.25 of +-1, +-2 beats | bar phase suspect: "the grid looks k beats out" | warning; the tool proposes `downbeat_offset_beats: k`; the owner confirms |
| otherwise | grid suspect (wrong tempo, drifting tempo, or a typo) | error; the track's grid is not trusted for beat matching (`grid_ok` false, 3.5) until fixed |

Example: the owner types 43.80 s for stimpy. bar_f = (43.80 - 0.5787) / 1.395349 = 30.975, bar 31,
e = -34.5 ms = -0.10 beat: agrees. Had the owner typed 44.18 s (one beat late), e_b = +0.99: phase suspect.
This matters because the packs' bar phase is the weakest part of the import (`downbeat_confidence` is about
0.4 even on well-behaved tracks such as "Go Back").

### 3.4 The sheet of first-drop times and its tool

The owner corrects a generated sheet rather than typing 61 values.

`tools/audio_import/drop_sheet.py` (music stream; Python, numpy, ffmpeg; no Godot):

- `drop_sheet.py make [--audition]` writes `content/music/transitions/drop_sheet.csv` (metadata only, in Git;
  opens in Excel). One row per catalogue recording, the doubtful ones first:

| Column | Filled by | Example |
|---|---|---|
| `track`, `artist`, `title` | tool | `stimpy_party_last_sounds`, Stimpy, Party Last Sounds |
| `bpm`, `first_downbeat_s`, `beat_ms` | tool, from the pack | 172.0000, 0.5787, 348.8 |
| `detected_drop_s`, `detected_drop_bar`, `detected_drop_mmss` | tool, first `drop` section | 43.835, 31, 0:43.835 |
| `second_drop_s` | tool | 177.788 |
| `rough_drop_s` | tool, catalogue `quick.first_drop_s` (an independent rough look) | 44.6 |
| `flags` | tool | `no pack`, `rough disagrees by 8+ bars`, `tempo not constant`, `drop before bar 16` |
| `audition` | tool | path of the audition file, outside Git |
| `owner_drop` | **owner** | blank or `ok` = accept; `43.80`; `0:43.8`; `bar 31`; `+1 beat` |
| `owner_offset_beats` | **owner** (rare) | blank or -3 to 3 |
| `owner_note` | **owner** | free text |

- `--audition` renders, for each pack, 4 bars before to 4 bars after the detected drop, mixed from the stems,
  with a click on every downbeat of the pack's grid and a louder click on the drop bar, to
  `C:\Users\joesa\rw-audio-work\cache\drop_audition\<id>.wav`. Outside every repository; never committed.
  Listening to one file answers both questions: is the drop right, and is the grid on the beat.
- `drop_sheet.py apply` reads the corrected sheet, writes or updates the sidecars (a blank owner cell never
  overwrites a value), sets `checked`, and prints each track's snap error and verdict. Rows marked `no pack`
  are kept for later.
- Tests: `tools/audio_import/test_drop_sheet.py` on synthetic track.json files (parsing of every accepted
  form, snapping, the three verdicts, no overwrite by blanks).

### 3.5 Missing data and tempos that are not constant

| Case | Behaviour |
|---|---|
| No sidecar | Pack values only: drop = first `drop` section; no markers; `no_blend` false |
| A field missing or null | Its default (table 3.2) |
| No `drop` section and no `first_drop_s` | `RunTrackPlan`'s existing rule (loudest section); the 4-bar guarantee is measured from that bar |
| Pack missing or refused | The scene is ordinary (M1's rule); any transition into it is `cut` |
| `grid_ok` false | Beat matching off: `blend` and `halftime_blend` become `echo_out` (no rhythmic overlap). The chart is unaffected (cues are charted from track seconds) |

`grid_ok` is true when `drift_ms_max_abs` <= 20 ms and the sidecar's snap verdict is not "grid suspect".
On the packs of this PC four tracks fail the drift test: `freestylers_pendulum_sirreal_painkiller_noisia_remix`
(251 ms), `teddy_killerz_teddy_killerz_night_train_t3ggcfz1vs` (258 ms), `fresh_the_gatekeeper_original_mix`
(163 ms), `northern_zone_faint` (37 ms). `annix_kingdom` is marked not constant but drifts 14.8 ms at most and
keeps `grid_ok`. No per-bar beat map exists for drifting tracks and none is designed here: echoing out is the
robust answer, and the cue chart already follows the audio.
