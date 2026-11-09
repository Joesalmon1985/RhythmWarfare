# Bedroom music POC (Unity) - rhythm layer on the Sims 2 bedsit

Branch `feature/bedroom-music-poc`. A first-person rhythm/mixing layer over the existing four-view OpenTS2 bedsit, borrowing the
RhythmWarfare design (custom loops drive 4 pads, a build into a recorded drop, 80 % success threshold, mixing mode with no
judging). The room-side game that sits on top of it (headphones, mess to tidy, the knock and the visitor) is described in [ACT_ONE.md](ACT_ONE.md). RhythmWarfare itself was **not** modified. No recordings, extracted EA assets or other large audio are in Git.

**Scope of this pass (agreed): Gatekeeper-only.** Only *Fresh - The Gatekeeper (Original Mix)* is on this PC. *Drop Dis* and *Levels* are
modelled (owner timestamps, cues, plan legs) but have no audio, so the three-track path is exercised only with **simulated tracks in
automated tests** (clearly marked), never in the real game.

## Run it

1. Prepare the local audio once (git-ignored `LocalAudio/`): `python -I Tools/music/prepare_audio.py` (needs ffmpeg; converts the
   Gatekeeper mp3 and the RhythmWarfare 174 BPM loop stems to 48 kHz stereo 16-bit WAV, no trimming).
2. Windows exe: `Builds\Windows\UnityBedsitPOC.exe -music` (or set `BEDSIT_MUSIC=1`). In the editor: open `Assets/Scenes/Bedsit.unity`,
   set `BEDSIT_MUSIC=1`, press Play. Audio folder: `BEDSIT_AUDIO_DIR`, or `LocalAudio` next to the exe / in the project root.
3. Act One: after the wake-up the player puts on headphones (about 1.5 s); the music starts then, with a 3 s lead-in. The rhythm minigame runs for
   128 beats (44 s), the recording's own run-in plays for the next 128 beats (44 s) with no minigame, and the **drop arrives about 90 s after the
   headphones go on**, with a three-knock door cue. The bedroom view controls are unchanged: left/right edge = turn, top-centre = interact (the
   door), **bottom strip = 4 pads** (or keys **D F J K**); tapping a piece of mess tidies it. `F1` toggles the diagnostics overlay, `P` pauses (timeline,
   scheduling and judging all freeze), `F2` forces the knock (developer shortcut).
4. Scripted players for demos/recordings: `-musicbot=perfect|partial|fail` (rhythm), `-tidybot=all|most|none` (tidies one item every ~3 s, answers the knock,
   saves a screenshot of the visitor), `-musicrecord=SECONDS -quit` (writes `<exe folder>\Evidence\audio\runtime_<bot>.wav/.txt`, including the Act One log), `-overlay`.

## What is built

| Requirement | Where |
|---|---|
| One shared music session for all four views; turning never restarts music/score; Scene 1 (North) start; compass-order turning; bottom keeps facing | `MusicPoc` is created once; verified by `MusicPocSceneTests` (below) |
| RHYTHM vs MIXING modes | `MusicDirector` (mode follows the plan legs); `MusicHud` shows pads only in RHYTHM |
| Custom MIDI/WAV drives 4 pads for 256 -> 128 beats before the drop; the recording runs 128 -> 0 with no minigame; 80 % threshold | `plan.json` `buildLoops`, `RhythmJudge`, `MusicDirector.RunPhase` (see "The build" below) |
| Mistake -> relevant custom stem muted/reduced, timeline never stops, restored at the *current* position with a short ramp | `Mixer.TrimTo` voices, `stemMuteLevel` 0.15 (30 ms ramp), restore after 2 hits (80 ms ramp) |
| Failure recovery (no rewind, no silence) | a failed gate repeats the last 32-beat loop (re-judged at 60 %, up to 2 repeats), then the run-in starts regardless (no soft-lock) |
| Door knock at the drop | `KnockSynth` (synthesized wooden knock) played on beats 0, 1, 2 of the drop; `MusicDirector.DropReached` unlocks the door |
| Mixing rules: one authoritative timeline, no double drops, fade outgoing over final 32 beats, no clipping, deck prep, pause sync | `Mixer` (timeline = audio clock), limiter ceiling 0.90 / max 0.98 |
| Dev overlay | `MusicOverlay` (facing, mode, song/position, beat, next anchor, incoming song/entry, accuracy vs threshold, stem state, pending plan) |
| Scripted perfect/partial/fail paths | `MusicBot.Perfect/Partial/Failing` |

### Pad -> instrument mapping (level-MIDI stems from the RhythmWarfare loop library, 174 BPM, 8 bars = 32 beats each)

| Pad | Key | Drum loops (1 and 3) | Bass loops (2 and 4) |
|---|---|---|---|
| 1 | D | kick (`groove_half_time` / `kick_half_time`) | lowest bass pitch band |
| 2 | F | - | bass pitch band 2 |
| 3 | J | - | bass pitch band 3 |
| 4 | K | snare (`snare_backbeat`) | highest bass pitch band |

Charted notes are judged (perfect 45 ms, good 90 ms) and audible in the custom layer; a hats loop plays as accompaniment but is not charted.
See `Assets/Bedsit/Music/Resources/Music/loops.json`.

### The build (256 beats, about 88 s)

Four rhythm loops, then the recording's own run-in to the drop:

| Beats before the drop | You play | Audio |
|---|---|---|
| 256 -> 224 `drums` | kick + snare | custom drums fade in |
| 224 -> 192 `bass` | bass notes on pads 1-4 | + bass |
| 192 -> 160 `drums2` | kick + snare | |
| 160 -> 128 `bass2` | bass | the **whole minigame (all 4 loops together)** is judged at the end: **80 %** to pass |
| **128 -> 0 `runin`** | **nothing: the rhythm game disappears** | the recording enters at its own `firstDrop - 128 beats` cue (25.517 s in the file) and eases in over 8 beats while the custom layer eases out over 8 beats; you just look around / tidy |
| 0 | - | **drop**, three door knocks on beats 0, 1, 2, MIXING mode |

* Gatekeeper's `firstDrop - 256` cue would be before the start of the file (-18.6 s), so the minigame uses the custom layer only; the recording enters at the -128 cue.
* A failed gate repeats the last (bass) loop as a recovery attempt at 60 % (at most 2); the custom loops never stop and the recording has not entered yet, so there is
  no silence and nothing is rewound. After the attempts the run-in starts anyway, so the drop is late by 32 beats per repeat. This is judged only once, at the
  end of loop 4, never during the run-in.
* Stems reduced by a mistake are restored at every loop boundary, so one slip never carries into the next loop.
* `stopAfterLegs: 1` in `plan.json`: Act One plays only this first drop; the recording then plays on in MIXING mode. (The later legs below still exist and are tested with simulated tracks.)

### Sequence (`plan.json`)

L1 build (above) Gatekeeper -> first drop (**the only leg played while `stopAfterLegs` = 1**); L2 handover Gatekeeper second drop -> Drop Dis first drop (**fallback with Drop Dis missing: build into the
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

**Automated** (all run in Unity play mode; 65 tests in the full suite):

* 18 `MusicEngineTests` - cue derivation matches the brief and rejects negatives; perfect play (4 judged loops, the recording enters at the `-128` cue, drop at the planned
  time, no clipping, no gap); the three-knock cue on beats 0/1/2 and `DropReached` raised once; the knock sound's envelope; Act One plans only the first drop; the aggregate
  gate tolerates a few early misses but a whole missed loop repeats the bass loop and holds the recording back; failure path (recovery loops, exhausted -> run-in anyway, never
  silent); recovery that passes on the second try; no phantom misses in mixing; second build returns to rhythm (cycling plan); stem mute/restore sample-identical after the restore;
  pause freezes then resumes identically; handover never from an already-reached anchor and invalid-entry handover rejected; three-track sequence + repeat (simulated tracks);
  pad strip geometry; offline demo renders + analysis.
* 3 `MusicPocSceneTests` in the real bedsit scene - eight turns in compass order keep the *same* session, the *same* stem voices, never reset the score or log and add no misses;
  bottom-strip pad taps do not turn; pause freezes the timeline in the running game.
* 7 `ActOneSceneTests` - see [ACT_ONE.md](ACT_ONE.md).
* **Runtime recordings from the built exe** (`-music -musicbot=... -tidybot=... -musicrecord=...`), analysed by `Tools/music/analyze_recording.py`
  (`Docs/music/results/`): perfect (135 s), partial (135 s), fail (150 s). In all three: 0 clipped samples, peak 0.98, the only silence > 250 ms is the intro (0-10 s = wake-up +
  headphones + 3 s lead-in). The recording's run-in rises gradually after it enters (mix RMS 0.07 -> 0.12 -> 0.20 over the first 2 s, ~0.2-0.27 after) and the drop lands at the
  scheduled time (first onset within 3 ms) about 2.3x louder than the 1.5 s before it. Perfect: all gates passed, drop at 98.295 s, knock logged at 98.295 s. Partial: 53/60 = 88.3 %,
  drop at 98.316 s. Fail: aggregate 28/60 = 46.7 %, bass loop repeated twice (50 %, 58.3 % - both under 60 %), run-in started anyway, drop at 120.363 s (22 s later) with the knock at the drop.
  The knock's *sound* is verified in the offline render (voices at D, D+1 beat, D+2 beats; envelope test); in the exe recordings it is sitting under the drop, not separately measured.

**Not verified by a human listening.** Everything above is signal analysis and logs. I have not listened to the transitions, so musical
feel (e.g. how the build layers sit under the recording, whether the fades are pleasing) is unjudged.

## Limitations / known gaps

* Drop Dis and Levels are missing: no real handover into another song has been run in the actual game. Handover logic is covered only by tests with simulated tracks (Gatekeeper audio standing in) - that proves scheduling, not musical quality. Act One stops after the first drop anyway (`stopAfterLegs: 1`).
* Recording-stem effects (muting the recorded kick etc. on a mistake) are impossible without stems; only custom stems react.
* The levels at the hand-over (recording 0.9 with an 8-beat ease-in, custom layer easing out over 8 beats) are my guesses from signal levels. Gatekeeper is F# major (uncertain) and the custom loops are F minor, so the two may clash harmonically during the 8-beat overlap; not auditioned. All of it is adjustable in `plan.json`.
* The knock is a synthesized wooden thump (no sample), mixed on top of the drop; its realism and balance against the drop have not been listened to.
* Forward destinations (North Space, East Dinosaurs, South Magic/Unicorns, West Transport) are labelled in the overlay only - **not built**; after the door opens the player stays in the room.
* Android: music/Act One code is platform-neutral but this pass was not rebuilt/run on a phone; the audio callback path (`OnAudioFilterRead` + Update pump fallback) is untested on device. `LocalAudio` is not bundled in any build.
* Pad touch input and tidy taps are tested through code paths (`RaisePad`, `TryTidyAtScreen`), not with a real finger. Input latency is uncalibrated (`InputLatencySeconds` = 0).
* One full-suite run in this iteration showed a cold-start `Bedsit did not become ready: creating characters` timeout (90 s) in the first live-content test after a recompile; it passes on rerun. It happened before any of this iteration's code ran in that test, so it is a pre-existing cold-start issue, not diagnosed.
