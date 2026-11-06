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

## 4. The planner

### 4.1 What it is

`TransitionPlanner.plan(out, inc, meta, ready) -> Dictionary`, a static pure function in
`src/music/transition_planner.gd` (no nodes, no disk, no clock). The director calls it at the lock point and
sends the public part as `plan` with `locked`; the private part (the recipe) goes to the audio class.

| Input | Content |
|---|---|
| `out` | The outgoing scene: kind (`track`, `ordinary`, `trial`, `none` at the run's start), its track plan (`RunTrackPlan` fields), the outgoing track time at T, the section role at that time |
| `inc` | The incoming scene: kind, its track plan (E, `entry_t`, laps), the incoming drop bar the plan used |
| `meta` | Both sidecars as read (or `{}`), plus `grid_ok` of each track (3.5) |
| `ready` | Whether the incoming pack's stems are decoded or still loading; whether this request was deferred once |

Output: `{mode, fallback, outgoing_bpm, incoming_bpm, blend_beats, complete_t}` (the contract's Plan, no
other keys) and, kept apart, the recipe `{rate, window_bars, stems: {key: [start_bar, end_bar, curve]},
highpass, echo, drop_t, deadline_t}`.

### 4.2 Decision table (first matching row wins)

Definitions: rho = incoming BPM / outgoing BPM; c(x) = 1200 x log2(x) in cents; L = incoming bars from T to
the incoming drop (16 with the default lead-in); R = outgoing bars left in the audio after T.

| # | Condition | Mode | fallback | W (incoming bars) |
|---|---|---|---|---|
| 1 | Incoming is a track scene, its pack is still loading, request not yet deferred | defer once (`&"not_ready"`) | | |
| 2 | Incoming pack still not ready after the deferral, or its load failed | `cut`; the incoming scene plays as an ordinary scene | true | |
| 3 | Either side is not a track (ordinary, trial, run start) | `cut` | false | |
| 4 | `no_blend` on either track | `cut` | false | |
| 5 | L < 5 or R < 1 | `cut` | false | |
| 6 | \|c(rho)\| <= 50 and `grid_ok` on both | `blend` | false | min(12, L - 4, R - 1); at most 4 for the same track on both sides |
| 7 | \|c(rho / 2)\| <= 50 or \|c(2 rho)\| <= 50, and `grid_ok` on both | `halftime_blend` | false | as row 6 |
| 8 | anything else (L >= 5 here) | `echo_out` | false | 2 if L >= 6, else 1 |

If row 6 or 7 gives W < 2, the mode becomes `echo_out` with W = 1. 50 cents is 2.93% (rho between 0.9715
and 1.0293).

`blend_beats` = 4W (0 for `cut`); `complete_t` = T + W x incoming bar (`cut`: T + `mix.phase_fade_s`).
The incoming drop is at `drop_t` = T + L x incoming bar, and `deadline_t` = `drop_t` - 4 incoming bars. By
construction `complete_t` <= `deadline_t` in every row.

### 4.3 Stem kinds and their fades

Stems are grouped by key: **bass** (`bass`); **rhythm** (`drums`, `kick`, `tops`, and `backing`, which in a
pack without a bass stem carries the kick and bass bleed); **linger** (`other`, `vocals`, or the sidecar's
`linger`). An unknown key counts as rhythm (the safe side). Curve `cos` is g = cos(pi/2 x) for x from 0 to
1 over the span (equal power); a gain under -60 dB is set to silence. Gains are functions of song time,
never of accumulated frame deltas, so a pause freezes them.

| Mode | bass | rhythm | linger | tail rate | tail bus | incoming |
|---|---|---|---|---|---|---|
| `blend` | cos over bars 0 to 1 | cos over 0 to 2 (long recipe: 0 to 4) | 1.0 to bar 2, then cos over 2 to W | rho from T | high-pass 20 to 250 Hz over bars 0 to 4, exponential | pack gains from T |
| `halftime_blend` | as `blend` | as `blend` | as `blend` | rho / 2 or 2 rho, whichever is within 50 cents of 1 | as `blend` | pack gains |
| `echo_out` | cos over 0 to 0.125 (half a beat) | cos over 0 to 0.125 | cos over 0 to 1 | 1.0 | echo on at T: delay 3/4 of an outgoing beat, feedback 0.4, wet -6 dB; high-pass 200 to 2,000 Hz over 0 to W | pack gains |
| `cut` | every stem linear to 0 over 0.6 s from T (today's fade) | | | 1.0 | none | pack gains |

At `complete_t`, whatever the curves say, the tail's player goes to -80 dB and stops, the tail bus effects
are switched off and the audio class reports silence. That hard floor is **the rule that guarantees silence
before the drop**: the window is sized so that the floor lands at least 4 incoming bars before `drop_t`, and
nothing of the tail outlives it (echo repeats included: the bus is muted with the player).

The long recipe applies when the tail starts at or after `mix_out_bar`, or inside a `breakdown` or `outro`
section of the outgoing pack: those passages are made to be mixed, so the rhythm may stay twice as long.

### 4.4 Pseudo-code

```gdscript
static func plan(out: Dictionary, inc: Dictionary, meta: Dictionary, ready: Dictionary) -> Dictionary:
	var T: float = out["boundary_t"]
	if inc["kind"] == &"track" and not ready["incoming"]:
		if not ready["deferred_once"] and ready["loading"]:
			return {"defer": &"not_ready"}                    # row 1
		return _cut(out, inc, T, true)                       # row 2: the scene plays as an ordinary one
	if out["kind"] != &"track" or inc["kind"] != &"track":
		return _cut(out, inc, T, false)                      # row 3
	if meta["out"].get("no_blend", false) or meta["in"].get("no_blend", false):
		return _cut(out, inc, T, false)                      # row 4
	var bar_in: float = 240.0 / inc["bpm"]
	var L: int = inc["drop_bar"] - inc["entry_bar"]
	var R: float = (out["duration_s"] - out["track_t_at_T"]) / (240.0 / out["bpm"])
	if L < 5 or R < 1.0:
		return _cut(out, inc, T, false)                      # row 5
	var rho: float = inc["bpm"] / out["bpm"]
	var grid: bool = meta["out_grid_ok"] and meta["in_grid_ok"]
	var mode := &"echo_out"
	var rate := 1.0
	var W := 2 if L >= 6 else 1                              # row 8
	if grid and absf(_cents(rho)) <= 50.0:
		mode = &"blend"; rate = rho                          # row 6
	elif grid and (absf(_cents(rho / 2.0)) <= 50.0 or absf(_cents(rho * 2.0)) <= 50.0):
		mode = &"halftime_blend"; rate = rho / 2.0 if rho > 1.5 else rho * 2.0   # row 7
	if mode != &"echo_out":
		W = mini(12, mini(L - 4, int(floor(R)) - 1))
		if out["track"] == inc["track"]:
			W = mini(W, 4)
		if W < 2:
			mode = &"echo_out"; rate = 1.0; W = 1
	var complete_t := T + W * bar_in
	assert(complete_t <= T + (L - 4) * bar_in + 1e-6)       # the silence rule
	return {"mode": mode, "fallback": false, "outgoing_bpm": out["bpm"], "incoming_bpm": inc["bpm"],
		"blend_beats": 4 * W, "complete_t": complete_t, "recipe": _recipe(mode, W, rate, out, inc, meta)}
```

The director strips `recipe` before emitting `locked`, so the Plan has exactly the contract's keys.

### 4.5 The cases

| Case | What happens |
|---|---|
| Same track on both sides (a route between two scenes that pick one recording) | The incoming restarts the track at its bar E, at least one lap before where the outgoing is. rho = 1, so `blend` with W at most 4: two copies of one song for longer sound like a mistake. The two groups are separate players on the same files |
| An ordinary scene on one side (no pack, or a pack not ready) | `cut`, exactly today's 0.6 s fade. Ordinary scenes are now only fallbacks; blending loop scenes is a later refinement, not in M2 |
| The Bassment | Its entrance by the wizard is not behind the port in this phase: M1 stops the track group on the trial hand-off and M2 keeps that. Returning (`RunEngine.resume`) is `cut` (row 3: the outgoing music is the trial's loops). When the entrance moves behind the port later, it is row 3 as well |
| A minigame hold | No lock happens while `engine.hold` is set; a pending request is deferred with `&"held"` at each lock point (this does not use up the single `&"not_ready"` deferral). A minigame started during a blend (the card table is touchable in every block) changes nothing: the tail's fades run on song time |
| A scene left on its first departure lap | Safe by construction: the previous tail is silent by incoming bar 12 (beat 48 of lap 1), and the earliest next lock is beat 60.5 of lap `doors_from_lap` (>= 1). So contract rule 14 (`&"blending"`) is a guard that today's data never triggers; a test proves it with `doors_from_lap` 1 |
| The destination changes at the last moment | Replacing before the lock is free (contract rule 1). The planner runs at the lock with the request as it stands, so a late pick is planned with its own readiness. Loading starts on `request()`, so a pick made 2 s before the lock may not be ready: row 1 (one more lap), then row 2 |
| `on_miss` taken at the lock | Planned like any destination. Its pack is preloaded only if the memory budget allows (always on the PC, not on a phone: section 9); otherwise row 2 |
| A path hand-off (main run to a path or back) | Same rows. The tail lives on its own player, so the clock swap and the new `RunEngine` of `RunPlay._path_swap` do not touch it (M1 must keep it so) |
| A short lead-in (`entry: "start"`, a `start_bar` override, a drop before bar 16: `mampi_swift_soldiers_gyrhlx7pafa` has its first drop at bar 0, `sub_focus_rock_it` at bar 15) | W shrinks with L; under 5 bars, `cut` |
| A tail that would run out of audio (a hold kept the scene near the end of its track) | W is capped at R - 1 bars; under 1 bar, `cut` |

## 5. The transport

### 5.1 Two groups, two slots, one sum

```
 slot A: AudioStreamPlayer + AudioStreamSynchronized (3 to 7 stems) -> RunTrackA [HighPass, Delay: off] --\
 slot B: AudioStreamPlayer + AudioStreamSynchronized (3 to 7 stems) -> RunTrackB [HighPass, Delay: off] ---> RunMix -> Music [HardLimiter, -0.3 dB] -> Master
 loop voices of ordinary scenes, unchanged: RunDrumsA/B, RunBassA/B, RunBassToneA/B ---------------------/
 clock: RunAudio.player (silent) -> Music
```

- A scene's track group takes the free slot and keeps it for the whole scene. At T the outgoing slot becomes
  the tail; nothing is rerouted (changing the bus of a playing player is avoided). The slots alternate, as
  `RunAudio.BUS_PAIRS` do for loop scenes.
- The effects are created once with the buses, disabled, and switched with
  `AudioServer.set_bus_effect_enabled`; no effect is added or removed while music plays.
- Per-stem gain: `AudioStreamSynchronized.set_sync_stream_volume(i, db)` every frame. The 4.5 source applies
  it as one constant per mix chunk (no interpolation inside a chunk), so a fade is a staircase of about 60
  steps a second: under 1 dB a step for fades of a bar or more, up to 6 dB for the half-beat cut of
  `echo_out` (to verify in the spike that it does not click).
- The limiter (M1 adds it) sits after the sum. Two full tracks in the first bar of a blend can reach +6 dB
  over one; the rhythm leaves within 2 bars. The spike measures how hard the limiter works.

### 5.2 Rate matching for small ratios

`AudioStreamPlayer.pitch_scale` changes speed and pitch together (resampling). In the 4.5 source
`AudioStreamPlaybackSynchronized::mix` passes one rate scale to every substream, so one assignment on the
tail's player keeps its stems locked together. The step is made at T in the same `_process` pass that
starts the incoming group (a scheduled item fires when `item.t <= now + time_to_next_mix`), so both land
in the same mix chunk. Placing it one chunk wrong costs about 10 ms x 3% = 0.3 ms.

The step from 1.0 to rho is heard as a pitch step of up to 50 cents on held notes. It falls on the incoming
downbeat, which masks it. A ramp over the last outgoing bar was considered and left out of M2: it moves the
tail's bar line off the incoming downbeat unless compensated. It is spike question Q2.

### 5.3 Starting and aligning

- The incoming group: at `locked` (T - 3.5 outgoing beats, 1.20 s at 175 BPM) the director attaches the
  decoded streams to the free slot's player at -80 dB and schedules `{t: T, kind: "track_in"}`. At T it
  calls `play(entry_t + lateness)` with `lateness = max(now + time_to_next_mix - T, 0)`, the pattern of
  `RunAudio._start_voice`, and sets the pack gains. The engine's `track_start` at T then finds the group
  already started and only records it (idempotent by scene and phase).
- The tail: the outgoing group, already playing. At T its rate is set (5.2) and its fades begin.
- Alignment: the tail's beat sits off the incoming beat by (start lag of the outgoing group) - (start lag of
  the incoming group) + (clock rate error over the outgoing scene, 6.4). Each start lag is under one mix
  chunk; both are logged. An optional phase nudge (absorb the measured offset by a small rate change over
  the first incoming bar: 10 ms over 1.4 s is 0.7%, 12 cents) is off by default; the spike decides.
- Seeking: the tail never seeks. The incoming seeks once, at its start, to `entry_t`. Whether a Vorbis start
  inside a file is sample-accurate in 4.5 is to verify in the spike (Q6). `track_wrap` stays M1's.

### 5.4 Memory and voices

| Item | Figure |
|---|---|
| One pack in memory | 50 to 97 MB: Vorbis q10 packets are kept compressed and decoded in the mixer (`AudioStreamOggVorbis`; to confirm by measurement) |
| During a blend | 2 packs (tail and incoming): up to about 200 MB |
| With a requested next destination | 3 packs. Loading for the next destination waits for `completed` (the tail freed) unless the budget allows it (9) |
| Vorbis decoders | 3 to 5 per group in today's packs (6 voices + backing at the format's limit): 10 in a blend today, 14 at most |
| Other players | the clock and one-shot effects; no loop voices play in a track scene |

### 5.5 Pause and focus loss

`RunPlay._notification` pauses on `NOTIFICATION_APPLICATION_FOCUS_OUT` and `NOTIFICATION_APPLICATION_PAUSED`;
`SongClock.pause` freezes song time and `RunAudio.pause` sets `stream_paused` on every player. M2 adds both
slots to that. Because every fade, the rate step and the floor are functions of song time, a pause in the
middle of a blend freezes it where it was, and the resume restarts both groups in the same frame. That they
resume in the same mix chunk is spike question Q1. A lost audio device (headphones out, a call on Android)
arrives as the same notifications; nothing else is done.

## 6. The clock

### 6.1 Where `song_time()` comes from

| When | Source of song time | Grid (beat, origin) | What sounds |
|---|---|---|---|
| Before T | the silent clock, through `SongClock.audio_time()` | outgoing: its `beat_s`, origin its scene's first downbeat | outgoing group at rate 1 |
| T to `complete_t` | the same silent clock, untouched | incoming: `_regrid(T, bpm_in)`, engine `tempo` event, port `tempo_changed` | incoming group at rate 1, tail at rate rho |
| After | the same silent clock | incoming | incoming group |

The clock is never handed from one music stream to another. The "transfer of the authoritative clock" is a
change of grid at T, which already exists (`RunEngine._regrid`): `grid_beat0` keeps counting beats,
`level.song_offset_ms` keeps ticks continuous, song time does not jump. The tail is never a source of time.

### 6.2 Float tempos

The engine's grid is already a float (`beat_s = 60 / bpm`). Only the clock stream is tied to an integer BPM
(`clock_rate(bpm: int)`). Recommended to M1 (its M1.4): make the clock **tempo-free**, one silent loop at
the project mix rate (48,000 Hz, `driver/mix_rate=48000`) of a fixed length (for example 2^20 frames,
21.85 s), never swapped. Nothing reads the clock loop's length except wrap counting in
`StemTransport.playback_position()`, so it need not be a whole number of beats. If M1 keeps a per-tempo
clock, M2 needs only that it is not swapped at a track-scene boundary inside one engine.

### 6.3 What the judge sees

`judge_time()` = song time - `calibration_ms`. After T the only cues are the incoming chart's, placed by
`_chart_track_block` at lap downbeat + (cue track time - lap track time); the tail has no cues and its
stems never mute. No outgoing cue lives into the blend: cues end by beat 12 of a block (beat 60 of the lap),
the accept window closes 140 ms later, and the boundary is 4 beats after beat 60. A cue inside a blend is
judged on the incoming grid with the same windows as anywhere else (perfect 45 ms, great 90 ms, accept
140 ms). Mutes work on the incoming group from T exactly as in mid-scene.

### 6.4 Drift accounting

| Source | Size | Accumulates over transitions? |
|---|---|---|
| Start lag of a group | under one mix chunk (about 10 ms expected on WASAPI; 88.5 ms chunks on the Dummy driver) | no: each scene's group starts fresh against the clock |
| Clock rate error | The 8,700 Hz clock is resampled with a fixed-point step truncated to 1/65,536 (`AudioStreamPlaybackResampled::mix` in the 4.5 source): 8700 / 48000 x 65536 = 11,878.4, truncated to 11,878, so the clock runs 3.4e-5 slow: 3.0 ms over an 88 s scene, 6.0 ms over 176 s. Zero with a 48 kHz clock. To confirm by measurement (Q9) | within one scene only: a fresh group start resets it |
| Tail rate quantisation | under 1/65,536 relative: 0.3 ms over a 17 s tail | no |
| Track tempo not constant | up to 258 ms between the fitted grid and the audio (`teddy_killerz`) | cues follow the audio; such tails are not beat-matched (`grid_ok` false) |

Tolerance asserted: at every boundary, and over ten consecutive transitions, |cue time - audio time of the
same event| <= one mix chunk, with no trend (slope under 0.5 ms per transition). On a virtual clock the
accounting is exact (1e-6 s).

### 6.5 Latency and calibration

Both groups go out through the same buses and device, so they share one output latency. `output_latency`
stays cached at the countdown (`SongClock.begin_countdown`); M2 does not refresh it during a blend.
Calibration is unchanged. An effect with internal latency on a tail bus would delay the tail against the
incoming track; that is why a real-time pitch shifter is not in the base design (7).
