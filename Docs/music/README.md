# Bedroom music POC (Unity) - rhythm layer on the Sims 2 bedsit

Branch `feature/bedroom-music-poc`. A first-person rhythm/mixing layer over the existing four-view OpenTS2 bedsit, borrowing the
RhythmWarfare design (custom loops drive 4 pads, a short build into a recorded drop, 80 % success threshold, mixing mode with no
judging). RhythmWarfare itself was **not** modified. No recordings, extracted EA assets or other large audio are in Git.

**Scope of this pass (agreed): Gatekeeper-only.** Only *Fresh - The Gatekeeper (Original Mix)* is on this PC. *Drop Dis* and *Levels* are
modelled (owner timestamps, cues, plan legs) but have no audio, so the three-track path is exercised only with **simulated tracks in
automated tests** (clearly marked), never in the real game.

## Run it

1. Prepare the local audio once (git-ignored `LocalAudio/`): `python -I Tools/music/prepare_audio.py` (needs ffmpeg; converts the
   Gatekeeper mp3 and the RhythmWarfare 174 BPM loop stems to 48 kHz stereo 16-bit WAV, no trimming).
2. Windows exe: `Builds\Windows\UnityBedsitPOC.exe -music` (or set `BEDSIT_MUSIC=1`). In the editor: open `Assets/Scenes/Bedsit.unity`,
   set `BEDSIT_MUSIC=1`, press Play. Audio folder: `BEDSIT_AUDIO_DIR`, or `LocalAudio` next to the exe / in the project root.
3. Music starts 3 s after the wake-up sequence finishes (so the first ~10 s are silent by design); the first drop then arrives ~33 s later. The bedroom view controls are unchanged:
   left/right edge = turn, top-centre = interact, **bottom strip = 4 pads** (or keys **D F J K**). `F1` toggles the diagnostics
   overlay, `P` pauses (timeline, scheduling and judging all freeze).
4. Scripted players for demos/recordings: `-musicbot=perfect|partial|fail`, `-musicrecord=SECONDS -quit` (writes
   `<exe folder>\Evidence\audio\runtime_<bot>.wav/.txt`), `-overlay`.

## What is built

| Requirement | Where |
|---|---|
| One shared music session for all four views; turning never restarts music/score; Scene 1 (North) start; compass-order turning; bottom keeps facing | `MusicPoc` is created once; verified by `MusicPocSceneTests` (below) |
| RHYTHM vs MIXING modes | `MusicDirector` (mode follows the plan legs); `MusicHud` shows pads only in RHYTHM |
| Custom MIDI/WAV drives 4 pads; short build into an explicit recorded drop; 80 % threshold | `plan.json` `buildLoops`, `RhythmJudge`, `MusicDirector.RunPhase` (see "The build" below) |
| Mistake -> relevant custom stem muted/reduced, timeline never stops, restored at the *current* position with a short ramp | `Mixer.TrimTo` voices, `stemMuteLevel` 0.15 (30 ms ramp), restore after 2 hits (80 ms ramp) |
| Failure recovery (no rewind, no silence) | a failed gate repeats that 32-beat loop (re-judged at 60 %, up to 2 repeats), then the build moves on regardless (no soft-lock) |
| Mixing rules: one authoritative timeline, no double drops, fade outgoing over final 32 beats, no clipping, deck prep, pause sync | `Mixer` (timeline = audio clock), limiter ceiling 0.90 / max 0.98 |
| Dev overlay | `MusicOverlay` (facing, mode, song/position, beat, next anchor, incoming song/entry, accuracy vs threshold, stem state, pending plan) |
| Scripted perfect/partial/fail paths | `MusicBot.Perfect/Partial/Failing` |

### Pad -> instrument mapping (level-MIDI stems from the RhythmWarfare loop library, 174 BPM, 8 bars = 32 beats each)

| Pad | Key | Drum phases (loops 1 and 3) | Bass phases (loops 2 and 4) |
|---|---|---|---|
| 1 | D | kick (`groove_half_time` / `kick_half_time`) | lowest bass pitch band |
| 2 | F | - | bass pitch band 2 |
| 3 | J | - | bass pitch band 3 |
| 4 | K | snare (`snare_backbeat`) | highest bass pitch band |

Charted notes are judged (perfect 45 ms, good 90 ms) and audible in the custom layer; a hats loop plays as accompaniment but is not charted.
See `Assets/Bedsit/Music/Resources/Music/loops.json`.

### The build (96 beats, about 33 s)

Three 32-beat loops, then the recorded drop and MIXING mode (no judging, just look around):

| Loop | You play | Gate | Audio |
|---|---|---|---|
| 1 `drums` | kick + snare | none (warm-up) | custom drums fade in |
| 2 `bass` | bass notes on pads 1-4 | **80 %** or the bass loop repeats | custom drums + bass |
| 3 `buildup` | kick + snare again | **80 %** or the buildup is faded out and re-entered (drop held) | the recording's own 32-beat lead-in to the drop **eases in over 8 beats** under the drums; bass drops out; custom level 0.8 -> 0.6 |

* Nothing is charted in the last 4 beats before the drop; the build is judged at the end of loop 3 (4 beats early) so a failed buildup can be eased
  out before the drop would arrive.
* After the drop the custom drums fade over 2 beats and the rhythm HUD fades away (MIXING).
* Retries use the recovery threshold (60 %), at most 2 per gate; after that the build moves on anyway.
* Stems reduced by a mistake are restored at every loop boundary, so one slip never carries into the next loop.

### Sequence (`plan.json`)

L1 build (3 loops above) Gatekeeper -> first drop; L2 handover Gatekeeper second drop -> Drop Dis first drop (**fallback with Drop Dis missing: build into the
Gatekeeper second drop**); L3 build Drop Dis -> second drop; L4 handover Drop Dis ending -> Levels first drop; L5 build Levels -> second drop;
L6 repeat to Gatekeeper using a valid *future* outgoing anchor (second drop, else ending; never an anchor already reached). Legs whose song is
unavailable are skipped with a log line; nothing starts from a negative cue (invalid cues are rejected, not clamped).

## Audio inventory (verified from the files, `Docs/music/*.json`)

| Item | Result |
|---|---|
| Gatekeeper | 323.448 s, 48 kHz stereo after conversion, source peak +1.32 dBFS (over full scale -> limiter) |
| Tempo | **174.000 BPM**, derived from the audio: the two measured drop attacks (69.655 s, 202.0685 s) are 383.999 beats apart. The generic comb/autocorrelation estimator gave 162.2 BPM and is **not reliable** on this track; it is not used |
| Beat origin | 0.3447 s |
| Anchors (s) | first drop 69.655 (owner 69.68), second drop 202.0685 (owner 202.09), ending 312.4138 (owner 312.43): owner stamps are 21-26 ms late vs the measured attack |
| Key | F# major r=0.647 vs F# minor 0.593 / B major 0.581: **uncertain** (margin 0.054); not used by the game |
| Stems of the recordings | **none exist** - full stereo mixes only. Consequence: recorded-song stem effects are not possible; mistakes only affect the custom stems; the outgoing song can only fade as a whole |
| Loop stems | kick/snare/bass/hats WAV 11.034 s = exactly 32 beats at 174. MIDI-vs-WAV: kick and snare match (kick sample has a fixed +46 ms onset latency); **bass MIDI does not fully match the WAV** (up to 51 ms off, `midi_matches_audio=false`) |
| Drop Dis / Levels | file missing: owner timestamps only; BPM 174 inferred from their gaps (319.99/255.98 and 255.98/255.99 beats), not verified from audio |

Cue table (8 candidates per song, invalid ones flagged, never clamped): `Docs/music/cue_table.md` / `.json`, regenerated by
`Tools/music/make_cue_table.py`. For Gatekeeper first-drop -256/-384 are invalid (before the file start).

## Verification

**Automated** (all run in Unity play mode; 55 tests in the full suite, 55 passed):

* 15 `MusicEngineTests` - cue derivation matches the brief and rejects negatives; perfect play (3 windows, first loop ungated, the recording's
  buildup enters exactly 32 beats before the drop, drop lands at the planned time, no clipping, no gap); warm-up loop not gated while a failed
  bass loop repeats and holds the buildup back; failure path (recovery loops, drop held, attempts exhausted -> drop anyway, never silent);
  recovery that passes on the second try; no phantom misses in mixing; second build returns to rhythm without counting old notes; stem
  mute/restore sample-identical after the restore; pause freezes then resumes identically; handover never from an already-reached anchor and
  invalid-entry handover rejected; three-track sequence + repeat (simulated tracks); pad strip geometry; offline demo renders + analysis.
* 3 `MusicPocSceneTests` in the real bedsit scene - eight turns in compass order keep the *same* session, the *same* stem voices, never reset
  the score or log and add no misses; bottom-strip pad taps do not turn; pause freezes the timeline in the running game.
* **Runtime recordings from the built exe** (`-music -musicbot=... -musicrecord=...`), analysed by `Tools/music/analyze_recording.py`
  (`Docs/music/results/`): perfect (125 s), partial (70 s), fail (110 s). In all three: 0 clipped samples, peak 0.98, the only silence
  > 250 ms is the intro (0-10 s = wake-up + 3 s start delay). The recording's buildup rises gradually after it enters (mix RMS
  0.07 -> 0.10 -> 0.16 -> 0.20 -> 0.28 over its first 5 s) and the drop then lands at the scheduled time (first onset within 4 ms) with the mix
  about 2.2x louder than the 1.5 s before it (the previous design jumped ~8x from near-silence). Perfect: drop at 43.079 s. Partial: 3 stem
  reductions, all gates passed (87.5 % on the buildup). Fail: bass loop repeated twice (50 % / 16.7 % / 58.3 %), buildup failed (43.8 %) and
  re-entered twice (56.3 %, 56.3 %), then the drop played anyway at 87.217 s.

**Not verified by a human listening.** Everything above is signal analysis and logs. I have not listened to the transitions, so musical
feel (e.g. how the build layers sit under the recording, whether the fades are pleasing) is unjudged.

## Limitations / known gaps

* Drop Dis and Levels are missing: no real handover into another song has been run in the actual game. Handover logic is covered only by tests with simulated tracks (Gatekeeper audio standing in) - that proves scheduling, not musical quality.
* Recording-stem effects (muting the recorded kick etc. on a mistake) are impossible without stems; only custom stems react.
* The levels in the buildup (recording 0.9 with an 8-beat ease-in, custom 0.6, bass removed) are my guesses from signal levels. Gatekeeper is F# major (uncertain) and the custom loops are F minor, so the two may clash harmonically while they overlap; not auditioned. All of it is adjustable in `plan.json`.
* A failed buildup is eased out over its last ~4 beats and the buildup restarts from its own beginning (a fresh entry, not a rewind of the playing track); it was not auditioned either.
* Gatekeeper-only play ends the first loop of the plan at the second drop, then restarts the song at the ending anchor (`REPEAT`); this repeat leg was seen in the log of the 215 s recording but not played to its end.
* Forward destinations (North Space, East Dinosaurs, South Magic/Unicorns, West Transport) are labelled in the overlay only - **not built**.
* Android: music code is platform-neutral but this POC pass was not rebuilt/run on a phone; the audio callback path (`OnAudioFilterRead` + Update pump fallback) is untested on device. `LocalAudio` is not bundled in any build.
* Pad touch input is tested through `RaisePad`/region maths, not with a real finger. Input latency is uncalibrated (`InputLatencySeconds` = 0).
