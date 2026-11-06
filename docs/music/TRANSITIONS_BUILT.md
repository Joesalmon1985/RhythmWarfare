# DJ-style scene changes, as built (M2.4, M2.5, M2.6)

6 November 2026, branch `wip/music-m2-4`, this PC (Ryzen 7 5800X, Windows 11, Godot 4.5.1). The design is
`docs/parallel-development/MUSIC_TRANSITIONS.md`; the spike that chose the techniques is
`docs/music/TRANSITION_SPIKE.md`. Nothing here was listened to. Every figure comes from a capture of the
audio buses analysed numerically (`AudioEffectCapture`; the Master bus muted, nothing reaching the
speakers), from the engine's own counters, or from the process's CPU time, and names its driver. Other
worktrees ran Godot (tests, screenshot captures) during these measurements; CPU and frame times are
therefore noisy, and the timing figures (which come from the audio itself) are not.

## 1. What a scene change does now

Between two track scenes the director plans the change with the full decision table
(`TransitionPlanner.plan_full`, section 4.2 of the design): it supplies the outgoing track, its length, where
it is at the boundary T, its section, its stems, the incoming entry and drop bars, both sidecars and both
grid flags (`TransitionDirector._full_inputs`; the metadata is made with the scene plans, off the frame,
`RunTrackScenes.add_transition_meta`). The recipe goes to the audio with the incoming plan in it.

| Mode | What you get |
|---|---|
| every mode into a track scene | **The start fix.** The incoming group starts at the lock (about 1.2 s before T), muted, on its own slot bus. Its playhead is read against the clock every frame under `AudioServer.lock`; while it is off, the group is restarted with the lag it showed taken off, until it reads within 0.1 ms (a fallback pulls it in by `pitch_scale` if restarts run out of time). It plays at exactly rate 1.0 from two mix periods before T, is unmuted just before T, and the engine's `track_start` adopts it. |
| `blend` (within 50 cents, both grids steady) | The incoming plays from T on bar E at its own tempo and gain, never rate-changed while heard; the clock's grid becomes its grid at T (`tempo_changed` before `switched`). The outgoing group carries on as the **tail** on its own slot: `pitch_scale` = incoming / outgoing BPM from T (its bars on the incoming bars), its level -6 dB from T, bass out by incoming bar 1, drums and backing by bar 2 (bar 4 in a breakdown, an outro, or after the sidecar's `mix_out_bar`), synths and vocals held to bar 2 then out by bar W, a high-pass rising 20 to 250 Hz over 4 bars. At complete_t (T + W bars, W at most 12, at least 4 bars before the incoming drop) the hard floor stops it, its slot's effects go off and are made afresh, RunAudio reports the silence and the director emits `completed`. |
| `halftime_blend` (fixture packs only, ruling 6) | As `blend`, the tail at rho / 2 or 2 rho. No real pair of the 61 tracks uses it. |
| `echo_out` (anything else with a lead-in of 5 bars or more, or a drifting grid) | The tail at rate 1.0 through a delay of 3/4 of an outgoing beat (feedback 0.4) and a high-pass rising 200 to 2,000 Hz; rhythm and bass out in half a beat, synths in one bar; floor at T + 2 bars (1 bar for a lead-in of 5). |
| `cut` | Today's 0.6 s fade of the outgoing, with the start fix for an incoming track. Used for: an ordinary scene on either side, `no_blend`, a lead-in under 5 bars, an unready pack (after its one `not_ready` deferral, then the scene plays as an ordinary one), missing metadata (a track with no drop), every path hand-off, the Bassment (not behind the port, ruling 20). |

Also: pause and resume set every player in one `AudioServer.lock`, so the clock, the tail and the incoming
group stop and go on in the same mix chunk, and every fade is a function of song time (frozen while paused).
A second request while a blend runs is deferred `&"blending"` (conformance case 14 now runs on the real
director, staged as a 250-beat blend by the test rig). The tail is freed at its floor; the director's pins go
at the switch. One line per transition on stdout: `RUN transition id=... mode=... rate=... W=... T=...`.

## 2. How to switch it off

`RW_RUN_TRANSITIONS=cut` on the command line: every scene change is a cut (the start fix stays: it is not a
mode). `RW_RUN_TRANSITIONS=full` forces every mode on. Without either, the game plans every mode when track
scenes are on (`TransitionPlanner.DEFAULT_ON = true`, `game_default()`); under the test runner it is off unless
a test asks (`TransitionDirector.modes_override`). Narrowing blends to 30 cents is `MAX_CENTS`; the tail level
is `TAIL_GAIN_DB`; both in `src/music/transition_planner.gd`.

## 3. Hearing a pair (M2.6)

From PowerShell in the checkout (it calls Git's bash by its full path, like `play_tracks.cmd`):

```
tools\dev\hear_transition.cmd --list
tools\dev\hear_transition.cmd --pair 1            # chase_status_no_problem_original_mix -> stimpy_party_last_sounds, blend -29.9 cents
tools\dev\hear_transition.cmd --pair 1 --cut      # the same change as a plain cut, to compare
tools\dev\hear_transition.cmd <track A> <track B>
```

It plays the last lap (16 bars) of A's scene as the game plays it, then the change into B's scene through the
real director and audio, then 20 bars of B (past its first drop), with sound, and prints the mode chosen and
why. The recommended pairs: 1. chase_status to stimpy (blend, -29.9 cents); 2. ternion_sound_artifice to
acuna_go_back (echo_out, 140 to 174); 3. chase_status to mampi_swift_soldiers (cut: Soldiers' first drop is at
bar 0); 4. unglued_telefonik to amplify_crossy_badman (blend at +49.6 cents, the widest). I ran it muted only,
to check that it works: I cannot hear, and nothing below describes how anything sounds.

## 4. Figures

Every timing figure is cue time against the audio itself (a 0.5 s window of the captured bus cross-correlated
against the pack's stems, 1 to 8 kHz). About 4.04 ms is common to every group (the audio sits that much behind
its playhead on this engine; calibration absorbs a constant), so what matters is that it is the same everywhere.

### 4.1 The start fix (WASAPI, muted, `measure_track_audio.gd`, warehouse.balcony, two cut changes at lap 2)

| Scene | Before | After |
|---|---|---|
| first (started with the clock) | 4.06 ms | 4.06 ms |
| second (entered at t = 44.1) | 22.73 ms | 4.04 ms |
| third (t = 88.5) | 12.04 ms | 4.04 ms |

The 19 ms jump at a scene entered mid-run is gone. A first version corrected the muted group by `pitch_scale`
only: its playhead read 0.00 ms but its audio sat 3.37 and 2.51 ms (WASAPI): the resampler's buffer phase moves
with the rate and the playhead cannot see it. Restarts at rate 1.0 replaced it. Every prepared start since landed
by restarts (typically 1 to 3) with 0.000 to 0.017 ms left on the playhead and rate 1.0 throughout.
Bar-0 entries (no audio before the entry): probe then real start at T, WASAPI, loadstar_dr_karg 4.063 ms and
mampi_swift_soldiers 4.063 ms (playhead -0.015 and -0.014 ms). Before the probe existed, loadstar's unprepared
start measured 1.38 ms (WASAPI), which was luck: the old rule lands 8 or 18.7 ms off.

The return from the Bassment (no lock; the dungeon names its exit downbeat ahead, `trial_exit`): measured
through the real run scene (`measure_run_play.gd`) but **on the Dummy driver**, because WASAPI would not open on
this PC for those runs (`init_output_device` error, the engine fell back to Dummy; it had opened all day before).
Seven returns over two runs: every one prepared, its 88 ms Dummy landing error (one Dummy chunk) corrected to
under 0.02 ms, cue against audio 4.04 to 4.06 ms, the same as the first scene. Not measured on WASAPI.

### 4.2 Blends and echo-outs (WASAPI, muted, `tools/music/transition_pair.gd` + `analyse_transition_pair.py`)

| Pair | Mode | Incoming cue vs audio | Tail vs incoming beat | Tail last above -60 dBFS | Limiter p95 / max, first 4 bars |
|---|---|---|---|---|---|
| chase_status 175 -> stimpy 172 | blend -29.9 cents | 4.042 ms | +0.10 ms mean, 0.18 max | 4.06 bars before the drop | 2.59 / 10.1 dB |
| unglued 172 -> amplify 177 | blend +49.6 cents | 4.042 ms | +0.10 mean, 0.21 max | 4.04 bars | 3.12 / 14.6 dB |
| ternion 140 -> acuna 174 | echo_out | 4.063 ms | -0.04 mean, 0.04 max | 14.0 bars (floor at 2) | 2.16 / 4.6 dB |
| floodlight 174 -> loadstar 172 | blend -20 cents (probe start) | 4.063 ms | -0.12 mean, 0.17 max | 4.14 bars | 1.87 / 5.8 dB |

(tail at -6 dB). The spike measured -8.3 and -7.4 ms between tail and incoming beats before the start fix; now
0.04 to 0.21 ms. After the floor the tail bus carries nothing: its capture stops (the bus goes inactive), i.e.
silence, echo repeats included. The tail's own track time follows its rate to 0.1 to 0.2 ms over 16.7 s.

### 4.3 Headroom (WASAPI, the three spike pairs, limiter on RunTrack, first 4 incoming bars, p95 / max reduction)

| Tail level | chase -> stimpy | unglued -> amplify | ternion -> acuna |
|---|---|---|---|
| 0 dB | 4.24 / 9.2 dB | 3.66 / 14.1 | 3.83 / 6.9 |
| -3 dB | 3.19 / 10.2 | 3.40 / 13.6 | 2.85 / 5.5 |
| **-6 dB (chosen)** | 2.59 / 10.1 | 3.12 / 14.6 | 2.16 / 4.6 |
| the incoming alone (a cut) | 2.36 / 11.2 | 3.27 / 15.3 | 3.02 / 5.7 |

The maxima are the incoming tracks' own (a cut has them too; `amplify_crossy_badman` alone reaches 15 dB): no
tail level removes them. The cheapest fix that takes the blend's extra load away is the tail level: at -6 dB the
p95 reduction is within 0.3 dB of the incoming track alone. A per-pack loudness trim would also lower the tracks'
own limiting, but it changes every scene's level, not the transition; it is left to the owner (section 6).

### 4.4 Ten changes in a row on real packs (`measure_track_audio.gd`, warehouse.balcony, every scene left at lap 2)

Two runs of 470 s, ten changes each (3 echo-outs, 7 blends: balcony, chill, exit, mothership, gallery, bridge,
exit, hospital, corridor, dayroom, garden).

| Run | Driver | Cue against audio, the eleven groups | Drift | Prepared starts |
|---|---|---|---|---|
| before the probe start | WASAPI | 4.021 to 4.063 ms for ten; loadstar (entry bar 0, not prepared then) 1.375 ms | under 0.01 ms per 100 s | 9 of 10, each landed by restarts, residual under 0.02 ms |
| after the probe start | **Dummy** (WASAPI would not open, see 4.1) | 4.018 to 4.063 ms for all eleven, loadstar 4.042 | under 0.01 ms per 100 s | 10 of 10, residual under 0.02 ms; each had landed 88 ms off (one Dummy chunk) |

No trend over the ten. Worst frame within 0.5 s of an entry: 16.8 to 17.2 ms (WASAPI run; the Dummy run 29.9 to
31.5 ms, its frames are 15.6 / 31 ms by the Dummy driver's pacing, the same away from entries).

### 4.5 CPU, memory, frames (WASAPI; other worktrees were running Godot, so CPU is noisy)

- Process CPU: the outgoing alone 9 to 11% of a core; during a blend 11 to 14%; about +3% for the tail's group,
  its resampler and the high-pass (`pair_cpu.py`, process CPU time). Echo-out runs ranged 9.7 to 15.6%: noise.
- Memory: the incoming pack is decoded before the lock, so a blend adds no allocation at T; two packs in memory
  are about +206 MB static (M1.7's figure), private memory 440 to 500 MB in these runs with the captures.
- Worst frame within 0.5 s of T: 16.7 to 17.3 ms (vsync 16.7) in every pair and every scene entry of the ten-change
  run. Worst frames anywhere were 35 to 574 ms with nothing of ours in them (the frame log names no event):
  other processes.

### 4.6 On the virtual clock (Dummy driver, the suite)

`tests/test_transition_*.gd` on synthetic fixture packs through the whole engine (`blend_rig.gd`): the order of
the signals, the tail's rate, level, fades by kind and high-pass, the floor at complete_t and 4 bars before the
drop, `song_time()` monotonic, echo-out, short lead-ins, a drifting grid, every failure path, pause, memory, ten
transitions with WASAPI-like landing lags (every one corrected under 0.1 ms, every cue exactly on its group's
audio, no trend), and the judge: the same grades with transitions as with cuts at 0, +-30 and +-70 ms.

## 5. The walk with transitions on

`tools/run/walk_run.sh perfect_a` (virtual clock, Dummy driver, real packs, `GODOT` = the wrapper), modes on by
the game's default: **OK** twice (before and after the Bassment and probe work), 0 ERROR or SCRIPT lines, every
track scene at its planned number of laps. 19 scene changes each: the first walk 15 blend and 4 echo_out, the
second 12 blend and 7 echo_out (the scenes' track picks differed between the two runs), no cut and no fallback.
The modes come from the `RUN transition` lines, e.g. `warehouse->warehouse.bar mode=blend ... rate=0.999981 W=12`.

## 6. What only a person can judge

- The pitch of the tail: up to 50 cents (`unglued -> amplify`, +49.6). If it sounds sharp, `MAX_CENTS = 30` (1.3%
  of blends become echoes).
- The level at T: the tail steps to -6 dB under the incoming downbeat; whether that is a drop or pumping.
- The stepped per-frame gains (no click found numerically in the spike) and the echo's tail-off.
- Whether the incoming's few ms of its own lead-in before T (unmuted one mix period early) is ever noticed.
- A per-pack loudness trim for the tracks that drive the limiter on their own.

## 7. Known limits

- A scene change with no lock at all (the pause menu's leave on a lap that is not a departure lap; a lock later
  than 0.15 s before T) still starts the incoming group by the old lateness rule, 8 to 19 ms off on WASAPI. A
  track's wrap (a hold past the plan: `track_wrap` seeks the playing group) has the same error. Both are rare.
- The Bassment: its entry and return stay outside the port (ruling 20): a cut through the engine. The return is
  aligned through `trial_exit`, a one-line hook in `src/trial/trial_scene.gd`.
- A path hand-off is always a cut.
- `halftime_blend` is tested on fixture packs only: no real pair uses it.
- The silence report waits for every fading track group; a group faded for another reason in the same window
  (the Bassment taking the run) delays `completed` until its 0.6 s fade is over.

## 8. Android

- Decoders: a blend runs both groups (8 to 10 Vorbis decoders with today's packs). The `light` setting of the
  design (tail rhythm stopped at T) is not built; `RW_RUN_TRANSITIONS=cut` is the switch if a phone cannot.
- Memory: two packs held during a blend, about 210 MB at today's encoding; three with a requested next
  destination. Re-encoding for the phone (ruling 24) lowers this in proportion.
- The start fix measures and restarts whatever the device's mix period is, so it does not depend on WASAPI's
  10 ms; the probe for bar-0 entries assumes a start lands with a repeatable lag, to be checked on the phone.
- The output device can disappear (headphones, a call): WASAPI failed to open on this PC late in this work; the
  engine fell back to the Dummy driver and the music went on silently.

## 9. Files

`src/run/run_track_audio.gd` (slots, the prepared start, the probe, tails, the floor), `src/run/run_audio.gd`
(`prepare_transition`, `trial_exit`, locked pause), `src/transition/transition_director.gd` (`_full_inputs`,
`modes_override`, the RUN line), `src/music/transition_planner.gd` (`game_default`, `TAIL_GAIN_DB`),
`src/run/run_track_scenes.gd` (`add_transition_meta`), `src/track/track_transport.gd` (`set_tail_gain`),
`src/trial/trial_scene.gd` (one line). Tools: `tools/music/transition_pair.gd`, `analyse_transition_pair.py`,
`pair_cpu.py`, `tools/dev/hear_transition.sh` / `.cmd`, `tests/fixtures/track_scenes/measure_run_play.gd`.
Captures and logs: `C:\Users\joesa\rw-audio-work\m2\`, outside Git.
