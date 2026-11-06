# The transition spike (M2.1) and the real-driver measurements (M1.7)

6 November 2026, branch `wip/music-m2-spike`, this PC (Ryzen 7 5800X, Windows 11, Godot 4.5.1). It answers
section 7.2 of `docs/parallel-development/MUSIC_TRANSITIONS.md` and measures what M1 had measured only on the
Dummy driver. Nothing was listened to. Every figure below comes from a capture of the audio (Godot's
`AudioEffectCapture` on a bus) analysed numerically, from the engine's own counters, or from the process's
CPU time. Each figure names its driver. During every real-driver run the Master bus was muted and the
captured buses sent to a muted bus: nothing reached the speakers. A capture sits before a bus's volume and
mute, so it records the full signal (checked: a stem captured at RMS 0.17 with Master muted).

## 1. Verdict

**Build `pitch_scale` on the tail's own synchronised group, with two groups summed, the delay and the
high-pass for `echo_out`, and nothing else. But first fix how a group starts: on WASAPI a group started
mid-run lands one or two mix periods (8.0 or 18.7 ms) later than the lateness rule assumes, so the tail and
the incoming beats are 8 to 19 ms apart, a flam.** The playhead shows that error exactly on the next frame,
so M2.4 starts the incoming group early and muted, and absorbs the error before T (section 6).

- Two groups side by side: about 1.5% of one core each, 96 to 113 MB of memory each, start, pause and
  resume together (10 pause cycles moved the tail against the incoming by under 0.02 ms each).
- `pitch_scale` keeps the tail on the incoming grid: 0.15 ms of drift over the 16.7 s window, pitch as
  computed (-30 and +49 cents measured), no measured click at the rate step for -30 cents.
- Fallback: if the owner dislikes the pitch of the tail, narrow row 6 from 50 to 30 cents. Only 1.3% of the
  blend transitions the graph can produce lie above 30 cents (73.5% are within 10 cents), so the cost is
  small. Pre-rendered tails are the last resort, not the fallback.
- Ruled out: `AudioEffectPitchShift` (35 ms of added latency, more than 6% of a core); `AudioStreamInteractive`
  and `AudioStreamSynchronized` as the transition mechanism (no arbitrary start, one rate for everything);
  pre-rendered tails for now (1,939 distinct tails, 0.5 to 2.8 GB, against a problem nobody has heard yet).

## 2. Measurements

Packs from `C:\Users\joesa\rw-audio-work\packs`. "Spike" runs: `tools/music/spike/transition_spike.gd`.
"Run" runs: `tests/fixtures/track_scenes/measure_track_audio.gd` (the real `RunAudio`, `RunTrackAudio` and
`TransitionDirector`).

| What | Figure | Driver, source |
|---|---|---|
| Output latency the engine reports | 10.00 ms (the project asks for 15) | WASAPI, run and spike |
| Mix period | 10.00 ms from the main thread; the content quantum is 512 frames (10.67 ms) | WASAPI |
| Mix period | 85.33 ms | Dummy, run |
| One track group, CPU | +1.4% of one core (4 stems) | WASAPI, spike, process CPU time |
| Second group, CPU | +1.7% of one core (5 more stems, 9 Vorbis decoders in all) | WASAPI, spike |
| `pitch_scale` 0.983 on the tail, CPU | +1.0% of one core (the resampler works) | WASAPI, spike |
| `AudioEffectPitchShift` on the tail bus (fft 2048, oversampling 4), CPU | +6.0% of one core | WASAPI, spike |
| `AudioEffectHighPassFilter` and `AudioEffectDelay`, CPU | not measurable (under the 1% noise) | WASAPI, spike |
| Memory of one pack (static) | 91 to 113 MB a pack (about 1.6 times the Ogg files on disk) | WASAPI, spike and run |
| Memory with 1, 2, 3 packs held | +97.0, +205.8, +305.7 MB | WASAPI, run |
| Pack decode (worker thread) | 76 to 146 ms a pack (4 or 5 stems) | WASAPI, spike and run |
| Pack decode | 100 to 127 ms | Dummy, run |
| A group started with the clock: audio against song time | 4.04 to 4.06 ms late, every track, constant | WASAPI, capture |
| A group started mid-run (`play(from + late)`): audio against song time | 12.06 or 22.73 ms late; its playhead says 8.0 or 18.7 ms; the 4.04 ms above is the rest | WASAPI, capture and playhead |
| Same, inside one group over a scene | drift 0.000 ms per 100 s (capture), at most 0.025 ms per 100 s (playhead) | WASAPI |
| Tail against incoming beat, 175 to 172 BPM | -8.3 ms (the incoming later), steady to 0.15 ms over the window | WASAPI, capture |
| Tail against incoming beat, 172 to 177 BPM | -7.4 ms, steady to 0.2 ms | WASAPI, capture |
| Tail against incoming beat, 140 to 174 (echo) | -18.7 ms | WASAPI, capture |
| Tail drift at `pitch_scale` (rate quantisation) | 0.93 to 1.27 ms per 100 s, so 0.15 to 0.21 ms over a 16.7 s tail | WASAPI, capture |
| Pause and resume, 10 cycles mid-blend | tail minus incoming moved 0.15 ms in all over 16 s, the same as without pauses | WASAPI, capture |
| `AudioEffectPitchShift` latency | +35.2 ms against the tail without it (onset alignment) | WASAPI, capture |
| `AudioEffectPitchShift` at pitch 1.0 | no latency, waveform identical: the effect passes through | WASAPI, capture |
| Limiter in the first 4 incoming bars (sum of both groups) | peak in +4.8 to +6.9 dBFS; reduction max 7.8 to 15.8 dB, p95 3.4 to 6.1 dB | WASAPI, capture before and after |
| Tail bus after the hard floor | digital silence (echo repeats included) | WASAPI, capture |
| Offline render of one 16.5 s stem (ffmpeg 9.0.1) | rubberband 0.6 to 0.8 s; atempo 0.25 to 0.3 s | this PC, wall time |
| Tails that can occur | 1,939 distinct (track, exit lap, rate, window), 30,366 s of tail | from `track_scenes.json` and the target graph |
| Storage of all tails | lingering stems at pack quality 2.84 GB; one baked stereo mix a tail 1.78 GB; at 128 kb/s: 0.78 GB and 0.49 GB | computed |

## 3. Answers to section 7.2

**Q1, pause and resume.** Pass. Ten cycles of 0.3 s pauses mid-blend (`stream_paused` on the clock and both
groups in one frame) left the tail-against-incoming offset where it was: it moved 0.15 ms over 16 s, which
is the rate drift that runs without pauses too. WASAPI.

**Q2, the rate step and 10, 30, 50 cents.** Numerically clean for -30 cents: against an offline
reference with smooth gains and the rate switched at T, no 2 ms frame of the tail had more energy above
6 kHz than the reference (max +0.6 dB). For +49.6 cents one frame 8 ms after T was +6.6 dB; that is inside
the 10 to 20 ms where the engine still plays at rate 1 while my reference has switched, so it is not
conclusive. The pitch is as computed: -30 cents and +49 cents measured from the spectrum. Whether 30 or 50
cents is acceptable is for the owner's ear (section 5). A ramp was not tried.

**Q3, `AudioEffectPitchShift`.** Fails both limits. +6.0% of a core (limit 3%) and +35 ms of latency
against the tail without it (limit 5 ms), which would put the tail's beats 35 ms behind the incoming. It
did restore the pitch (0 cents measured). Keep it out, on every platform.

**Q4, offline render with rubberband.** Passes on time and timing: 0.6 to 0.8 s to render 16.5 s of a
stem, pitch 0 or -1 cents, onsets within 2 ms of the grid at both ends of 12 bars. `atempo` is faster but
its onsets wander by up to 16 ms. Rubberband's "smooth" setting softened transients and drifted up to 6 ms.
Quality numbers (against the source at the same musical position, 300 Hz to 12 kHz): log-spectral distance
4.9 to 5.3 dB for rubberband, 5.2 to 5.5 for atempo, 8.0 to 8.7 for `pitch_scale` alone (which includes the
pitch change itself). Not needed unless Q2 fails by ear.

**Q5, `AudioStreamInteractive`.** Unsuitable. Read from the 4.5.1 binary's class API (no playback trial):
a transition starts "immediately", on the next beat or bar of the current clip's own tempo, or at its end;
the next clip starts at its start or at the same position. There is no start at an arbitrary track time
(bar E), and one `pitch_scale` covers both clips, so the tail cannot be rate-matched alone.
`AudioStreamSynchronized` has one start and one rate for all its streams (only per-stream volumes): right
for one group, unable to hold two tracks at two positions and two tempos.

**Q6, is `play(from)` sample-accurate.** The seek itself is: inside a group, and from one track to the next,
the audio sits where the playhead says plus a constant 4.04 ms (to 0.02 ms, six tracks), the same for every
group, so it cancels between tail and incoming and calibration absorbs it against the cues. What is not
accurate is the start time. `play()` takes effect one or two mix periods after the call, not at
`now + time_to_next_mix` as the lateness rule assumes: the group lands 8.0 or 18.7 ms late, depending on
where the call fell. The fallback the plan names ("start 1 bar earlier at -80 dB and unmute at T") is the
right shape, with one addition: measure the playhead and absorb the error while muted (section 6).

**Q7, clicks from per-frame gain steps.** Not found numerically. The half-beat cut (0.17 s) at rate 1 and the
1-bar fade showed no extra high-band energy against the smooth reference during the cut; the only frames
above it (+3 to +15 dB) lie in the last 50 ms of the 1-bar fade, at 26 dB under the music's usual high-band
level, where the stepped gain is a frame behind the smooth one. The ear must still confirm.

**Q8, the limiter.** Fails the 3 dB limit with the tail at full gain. In the first 4 incoming bars the sum
peaked at +4.8 dBFS (175 to 172), +6.9 (172 to 177) and +2.7 (the echo), and the limiter reduced by up to
7.8, 14.6 and 3.2 dB (p95 3.4, 6.1, 2.6 dB). Part of it is not the blend: `amplify_crossy_badman` alone
already needs 3.2 dB. Offline, from the two captures, a tail at -3 dB lowers the sample peaks by about 1.2 dB
and a tail at -6 dB by about 2 dB.

**Q9, the clock rate.** No longer applies to track scenes: M1.4 made the clock a 48 kHz loop, and on WASAPI
a group against that clock drifted 0.000 ms per 100 s (capture, two 42 s scenes) and at most 0.025 ms per
100 s (playhead). The 8,700 Hz clock was not measured on WASAPI.

## 4. M1.7: the measured run on the real driver

`measure_track_audio.gd`, WASAPI, start `warehouse.balcony`, 105 s, every track scene left at the end of
lap 2 (`RW_MEASURE_LEAVE=2`), Master muted, the RunTrack bus captured. The run played `sub_focus_rock_it`,
then `northern_zone_faint` (from t = 44.138), then `fresh_the_gatekeeper_original_mix` (from t = 88.531).
Both changes were `cut`, as M1's planner makes every change.

| What | Figure (WASAPI) |
|---|---|
| Cue time against audio time, first scene (group started with the clock) | audio 4.06 ms late, mean = max, drift 0.000 ms per 100 s (22 windows, 42 s) |
| Cue time against audio time, second scene (started mid-run, logged lateness 24.6 ms) | audio 22.73 ms late, mean = max, drift 0.000 ms per 100 s (22 windows, 42 s) |
| Cue time against audio time, third scene (logged lateness 15.6 ms) | audio 22.71 ms late, drift 0.000 ms per 100 s (8 windows, 14 s) |
| Playhead against clock, the same three groups | 0.00, -18.68, -18.67 ms mean; drift -0.002 to -0.025 ms per 100 s |
| Pack load (worker thread) | 82 to 119 ms for 4 stems (five packs) |
| Memory, static, with 1, 2, 3 packs held | +97.0, +205.8, +305.7 MB |
| Worst frame within 0.5 s of a scene entry | 20.1 ms (t = 44.138), 16.7 ms (t = 88.531) |
| Worst frame overall | 20.1 ms (the first entry: a track start and end in one frame); median 16.7 ms (vsync), p99 16.8 ms |
| Output latency reported | 10.00 ms |
| The silence report (`RunAudio.outgoing_silent`) | fired for both changes, 0.614 and 0.623 s after T (the 0.6 s fade plus a frame); `completed` followed in the same frame, not by the director's grace timer |

Read together: the cue-to-audio offset changes from scene to scene, by the start error of section 3, Q6
(here 4 ms in the first scene, 23 ms after each change). That is a jump of up to 19 ms at a boundary that
calibration cannot remove, because it is not constant. It exists today, with `cut`, in every track scene
entered mid-run.

**The 141 ms frame.** Not reproduced, so not explained. Two runs looked for it with every frame's contents
logged (engine events, track audio entries, decodes, memory and object deltas, process time): 105 s on
WASAPI with two scene changes and three packs let go, worst frame 20.1 ms; 100 s on Dummy from `warehouse`
(the earlier setting), worst frame 11.4 ms. The candidates named in the brief did not show: packs are let go
on a worker thread now (`RunTrackAudio._release`; the 190 ms main-thread stall it fixed is a likely origin
of a figure like 141 ms if that run predates it, but I could not check which code that run had), the decodes ran on workers (no frame over
20 ms while five packs decoded), and these runs render nothing that compiles a shader or imports a texture.
The measure script now prints the eight worst frames with what happened in each, so a future occurrence
will be named.

**Not measured, and why.** The output latency the device really has (the reported 10 ms is the buffer, not
the path to the ear; it needs a microphone or a person with the calibration screen). Whether the cues feel
on the beat (a person). Underruns (none were visible in the captures, which would show gaps; a long run on
a phone is the real test). The 8,700 Hz clock on WASAPI (no longer used with track scenes on).

## 5. For the owner's ear (M2.6)

Recommended pairs, built on the fixed start (section 6):

1. `chase_status_no_problem_original_mix` to `stimpy_party_last_sounds` (balcony to chill): `blend`, -29.9
   cents. Listen for: pitch of the old synths and vocals against the new track, no flam in bars 0 to 2, the
   level at T (no jump, no pumping from the limiter).
2. `ternion_sound_artifice` (140) to `acuna_go_back` (174): `echo_out`. Listen for: the echo trailing off in
   2 bars, no flam, no click in the half-beat cut.
3. A cut into `mampi_swift_soldiers_gyrhlx7pafa` (first drop at bar 0): `cut`, the 0.6 s fade.

Also, as a quick extra if time allows, `unglued_telefonik` to `amplify_crossy_badman` (+49.6 cents, the
widest blend): if the old track sounds sharp there, narrow row 6 to 30 cents (1.3% of blends become echoes).
To judge by ear: 30 and 50 cents; any click at T; the limiter's pumping in the first bars; the stepped fades.

## 6. What M2.4 needs before it starts

1. **The start of a group (the seam, `RunTrackAudio.run_item` "start" and `_start`; `RunAudio.prepare_transition`).**
   The lateness rule `late = now + time_to_next_mix - t` is wrong by one or two mix periods on WASAPI. The
   group's playhead, read against the clock under `AudioServer.lock()` on the next frame, shows the error to
   0.01 ms. So: at the lock (T - 3.5 outgoing beats, about 1.2 s), start the incoming group muted at
   `entry_t - (T - now)`; on the next frames measure (playhead - clock) - (entry_t - T); absorb it with a
   small `pitch_scale` on the still-muted group (20 ms over 0.5 s is 4%; nobody hears a muted group), back to
   1.0 before T; unmute at T. The engine's `track_start` then finds the group started and only records it.
   For this `prepare_transition(boundary_t, recipe)` needs the incoming plan in the recipe (dir, entry_t,
   beat_s), and `_start` must accept an already running group. The same correction would also remove the
   18 ms jump of today's `cut` scene entries (section 4); it belongs to M2.4 since `run_audio.gd` and the track
   audio are the music stream's.
2. **The tail's gain at T.** Q8: start the tail bus at -3 dB (a step at T, under the incoming downbeat) and
   let the owner judge the pumping. A recipe field (`tail_gain_db`), not a planner row.
3. **The planner's table stays as written**, row 6 at 50 cents, until the owner has listened. No change to
   the decision table is needed by these figures. If the ear says no to 50 cents, it is one constant (30).
4. **Gains as functions of song time, applied every frame**, as designed: the stepped staircase showed no
   measurable click. The effects (high-pass, delay) created once and switched with
   `AudioServer.set_bus_effect_enabled`, as the spike did; the hard floor (player stop and effects off at
   `complete_t`) gave digital silence on the tail bus, echo repeats included.
5. **Keep the capture method** for M2.5's measurements: `analyse_track_capture.py` measures cue against audio
   from the audio itself; the playhead alone misses the constant 4 ms but sees the start error exactly.

## 7. Android risks

- **Decoders.** A blend runs 8 to 10 Vorbis decoders (today's packs: 4 or 5 stems a group); about 3% of one
  desktop core here. A phone core is several times slower; the `light` setting (tail rhythm stopped at T, 2 or
  3 tail decoders) stays the safe default until measured on the device.
- **Memory.** 91 to 113 MB a pack in memory at today's encoding, about 1.6 times the file size. Two packs in
  a blend are about 210 MB; three about 310 MB. Re-encoding for the phone (ruling 24) at a lower bitrate
  lowers this in proportion to the file size; no preload during a blend on a phone.
- **Start error.** The one-or-two-period start error was measured on WASAPI's 10 ms periods. Android's
  periods differ and may be longer; the playhead correction of section 6 works for any period, which is
  the reason to build it rather than a constant offset.
- **Build size.** The packs' stems are 4.12 GB at about 468 kb/s a stereo stem. At 128 kb/s that is about
  1.1 GB in the APK. Pre-rendered tails would add 0.49 GB more (one baked mix a tail at 128 kb/s), about
  +43%. Another reason not to build them.
- **PitchShift.** Ruled out on the PC already; never on a phone.

## 8. Files

Kept (measurement tools):
- `tests/fixtures/track_scenes/measure_track_audio.gd`: now drives the run with the director wired as
  RunPlay does, logs the worst frames with their contents, holds extra packs for memory figures, mutes the
  speakers and captures the RunTrack bus on request (options in its header).
- `tests/fixtures/track_scenes/analyse_track_capture.py`: cue time against the audio itself, from that
  capture.

Throwaway, under `tools/music/spike/` (README there): `transition_spike.gd` (the experiments),
`make_experiments.py` (their list), `analyse_spike.py` (alignment, clicks, limiter, PitchShift),
`offline_tails.py` (pairs, storage, renders), `cpu_sampler.py` (process CPU time), `probe.gd` (the capture
and class API check). Captures, renders and logs are in `C:\Users\joesa\rw-audio-work\spike\`, outside Git.
No game code was changed.
