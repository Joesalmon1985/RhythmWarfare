# Bedroom music POC (Unity) - rhythm layer on the Sims 2 bedsit

Branch `feature/bedroom-music-poc`. A first-person rhythm/mixing layer over the existing four-view OpenTS2 bedsit, borrowing the
RhythmWarfare design (custom loops drive 4 pads, 128-beat build into a recorded drop, 80 % success threshold, mixing mode with no
judging). RhythmWarfare itself was **not** modified. No recordings, extracted EA assets or other large audio are in Git.

**Scope of this pass (agreed): Gatekeeper-only.** Only *Fresh - The Gatekeeper (Original Mix)* is on this PC. *Drop Dis* and *Levels* are
modelled (owner timestamps, cues, plan legs) but have no audio, so the three-track path is exercised only with **simulated tracks in
automated tests** (clearly marked), never in the real game.

## Run it

1. Prepare the local audio once (git-ignored `LocalAudio/`): `python -I Tools/music/prepare_audio.py` (needs ffmpeg; converts the
   Gatekeeper mp3 and the RhythmWarfare 174 BPM loop stems to 48 kHz stereo 16-bit WAV, no trimming).
2. Windows exe: `Builds\Windows\UnityBedsitPOC.exe -music` (or set `BEDSIT_MUSIC=1`). In the editor: open `Assets/Scenes/Bedsit.unity`,
   set `BEDSIT_MUSIC=1`, press Play. Audio folder: `BEDSIT_AUDIO_DIR`, or `LocalAudio` next to the exe / in the project root.
3. Music starts 3 s after the wake-up sequence finishes (so the first ~10 s are silent by design). The bedroom view controls are unchanged:
   left/right edge = turn, top-centre = interact, **bottom strip = 4 pads** (or keys **D F J K**). `F1` toggles the diagnostics
   overlay, `P` pauses (timeline, scheduling and judging all freeze).
4. Scripted players for demos/recordings: `-musicbot=perfect|partial|fail`, `-musicrecord=SECONDS -quit` (writes
   `<exe folder>\Evidence\audio\runtime_<bot>.wav/.txt`), `-overlay`.

## What is built

| Requirement | Where |
|---|---|
| One shared music session for all four views; turning never restarts music/score; Scene 1 (North) start; compass-order turning; bottom keeps facing | `MusicPoc` is created once; verified by `MusicPocSceneTests` (below) |
| RHYTHM vs MIXING modes | `MusicDirector` (mode follows the plan legs); `MusicHud` shows pads only in RHYTHM |
| Custom MIDI/WAV drives 4 pads; 128-beat build to an explicit recorded drop; 80 % threshold | `plan.json` settings, `RhythmJudge`, `MusicDirector` |
| Mistake -> relevant custom stem muted/reduced, timeline never stops, restored at the *current* position with a short ramp | `Mixer.TrimTo` voices, `stemMuteLevel` 0.15 (30 ms ramp), restore after 2 hits (80 ms ramp) |
| Failure recovery (no rewind, no silence) | up to 3 scheduled 32-beat custom phrases, each re-judged at 60 %, then the drop plays regardless (no soft-lock) |
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

Build = four 32-beat phases drums / bass / drums / bass (128 beats). Charted notes are judged (perfect 45 ms, good 90 ms) and audible in the
custom layer; a hats loop is available but uncharted. See `Assets/Bedsit/Music/Resources/Music/loops.json`.

### Sequence (`plan.json`)

L1 build Gatekeeper -> first drop; L2 handover Gatekeeper second drop -> Drop Dis first drop (**fallback with Drop Dis missing: build into the
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

**Automated** (all run in Unity play mode; 54 tests in the full suite):

* 14 `MusicEngineTests` - cue derivation matches the brief and rejects negatives, perfect/partial/fail paths, no phantom misses in mixing,
  stem mute/restore in sync, recovery without rewind or silence, recovery reaches another valid attempt, handover never scheduled from an
  already-reached anchor, invalid-entry handover rejected, three-track sequence + repeat (simulated tracks), pause freezes then resumes
  identically, pad strip geometry, offline demo renders + analysis.
* 3 `MusicPocSceneTests` in the real bedsit scene - eight turns in compass order keep the *same* session, the *same* stem voices, never reset
  the score or log and add no misses; bottom-strip pad taps do not turn; pause freezes the timeline in the running game.
* **Runtime recordings from the built exe** (`-music -musicbot=... -musicrecord=...`), analysed by `Tools/music/analyze_recording.py`
  (`Docs/music/results/`): perfect (215 s), partial (110 s), fail (110 s). In all three: 0 clipped samples, peak 0.98, the only silence
  > 250 ms is the intro (0-9.9 s = wake-up + 3 s start delay); the first drop lands at the scheduled 54.029 s (loud onset within 1 ms, RMS x7.7-13
  over the build); the perfect run also lands the second drop at 186.442 s. Partial: 6 misses, 88.3 % -> pass. Fail: 46.7 %, then
  three recoveries (55.6 / 50.0 / 44.4 %), attempts exhausted, drop plays anyway.
* Not flaky-free: in one full-suite run `FirstPersonTests.StartingCameraIsFirstPerson` timed out once during cold content load
  ("creating characters", 90 s); it passed on rerun (3.5 s) and the 53 others passed. Not caused by the music code.

**Not verified by a human listening.** Everything above is signal analysis and logs. I have not listened to the transitions, so musical
feel (e.g. how the build layers sit under the recording, whether the fades are pleasing) is unjudged.

## Limitations / known gaps

* Drop Dis and Levels are missing: no real handover into another song has been run in the actual game. Handover logic is covered only by tests with simulated tracks (Gatekeeper audio standing in) - that proves scheduling, not musical quality.
* Recording-stem effects (muting the recorded kick etc. on a mistake) are impossible without stems; only custom stems react.
* While a build runs the recording is silent (builds are *custom* layers into the recorded drop); the 4-beat recorded-fade-in at the end of a build was not auditioned.
* Gatekeeper-only play ends the first loop of the plan at the second drop, then restarts the song at the ending anchor (`REPEAT`); this repeat leg was seen in the log of the 215 s recording but not played to its end.
* Forward destinations (North Space, East Dinosaurs, South Magic/Unicorns, West Transport) are labelled in the overlay only - **not built**.
* Android: music code is platform-neutral but this POC pass was not rebuilt/run on a phone; the audio callback path (`OnAudioFilterRead` + Update pump fallback) is untested on device. `LocalAudio` is not bundled in any build.
* Pad touch input is tested through `RaisePad`/region maths, not with a real finger. Input latency is uncalibrated (`InputLatencySeconds` = 0).
