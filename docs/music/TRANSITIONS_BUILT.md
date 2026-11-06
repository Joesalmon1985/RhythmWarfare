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

FIGURES_GO_HERE
