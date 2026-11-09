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
3. Act One: after the wake-up the player puts on headphones (about 1.5 s); **Gatekeeper starts from its first sample** about 1 s after they begin to go on. The rhythm minigame is
   **drums only** and runs over the song's first section (25.5 s); pass it and the song carries on into its next section (44 s) with no minigame; the **drop arrives about 71 s after
   the headphones start going on**, with a three-knock door cue. The bedroom view controls are unchanged: left/right edge = turn, top-centre = interact (the door),
   **bottom strip = 4 pads** (or keys **D F J K**); tapping a piece of mess tidies it. `F1` toggles the diagnostics overlay, `P` pauses (timeline, scheduling and judging all
   freeze), `F2` forces the knock (developer shortcut).
4. Scripted players for demos/recordings: `-musicbot=perfect|partial|fail` (rhythm), `-tidybot=all|most|none` (tidies one item every ~3 s, answers the knock,
   saves a screenshot of the visitor), `-musicrecord=SECONDS -quit` (writes `<exe folder>\Evidence\audio\runtime_<bot>.wav/.txt`, including the Act One log), `-overlay`.

## What is built

| Requirement | Where |
|---|---|
| One shared music session for all four views; turning never restarts music/score; Scene 1 (North) start; compass-order turning; bottom keeps facing | `MusicPoc` is created once; verified by `MusicPocSceneTests` (below) |
| RHYTHM vs MIXING modes | `MusicDirector` (mode follows the plan legs); `MusicHud` shows pads only in RHYTHM |
| The song starts at its first sample; a drums-only custom minigame runs over its first section (to `firstDrop -128 beats`); passing it (80 %) lets the song carry on into the next 128-beat section with no minigame | `plan.json` `opening`, `RhythmJudge`, `MusicDirector.RunIntro` (see "The build" below) |
| Mistake -> relevant custom stem muted/reduced, timeline never stops, restored at the *current* position with a short ramp | `Mixer.TrimTo` voices, `stemMuteLevel` 0.15 (30 ms ramp), restore after 2 hits (80 ms ramp) |
| Failure recovery | a failed gate **loops the intro section again** (the recording restarts from its first sample at the section end; custom drums never stop, 30 ms cross-cut; re-judged at 60 %, up to 2 repeats), then the run-in starts regardless (no soft-lock) |
| Door knock at the drop | `KnockSynth` (synthesized wooden knock) played on beats 0, 1, 2 of the drop; `MusicDirector.DropReached` unlocks the door |
| Mixing rules: one authoritative timeline, no double drops, fade outgoing over final 32 beats, no clipping, deck prep, pause sync | `Mixer` (timeline = audio clock), limiter ceiling 0.90 / max 0.98 |
| Dev overlay | `MusicOverlay` (facing, mode, song/position, beat, next anchor, incoming song/entry, accuracy vs threshold, stem state, pending plan) |
| Scripted perfect/partial/fail paths | `MusicBot.Perfect/Partial/Failing` |

### Pad -> instrument mapping (level-MIDI stems from the RhythmWarfare loop library, 174 BPM, 8 bars = 32 beats each)

| Pad | Key | Drums (the Act One minigame uses only these) | Bass (only in mid-song builds of a cycling plan) |
|---|---|---|---|
| 1 | D | kick (`groove_half_time` / `kick_half_time`) | lowest bass pitch band |
| 2 | F | - | bass pitch band 2 |
| 3 | J | - | bass pitch band 3 |
| 4 | K | snare (`snare_backbeat`) | highest bass pitch band |

Charted notes are judged (perfect 45 ms, good 90 ms) and audible in the custom layer; a hats loop plays as accompaniment but is not charted.
See `Assets/Bedsit/Music/Resources/Music/loops.json`.

### The build (Act One opening: 70 s from the first sample to the drop)

Gatekeeper's first drop is at 69.655 s. Its section before the 128-beat run-in is the first **25.517 s (74.0 beats)** of the file:

| Song time | Section | You play | Audio |
|---|---|---|---|
| 0 -> 25.517 s | **intro** (up to `firstDrop -128 beats`) | **drums only**: kick (pad 1) + snare (pad 4) from the minigame loops, about 42 notes; **gate 80 %** | the recording from its very first sample (0.25 s fade-in) + the custom kick/snare drums (0.7) |
| 25.517 -> 69.655 s | **run-in** (the next section, 128 beats) | nothing - the rhythm game is gone | the same recording carries on (no new entry, nothing moves); the custom drums ease out over 8 beats |
| 69.655 s | **drop** | - | three door knocks on beats 0, 1, 2; MIXING mode |

* The custom drum loops are phase-locked so a 32-beat loop boundary falls exactly on the run-in start (the loops start 22 beats into their pattern), keeping them on the same bar grid as the
  `-128 / -256` cue table.
* Fail (below 80 %): the intro section **loops again** - the recording restarts from its first sample exactly at the section end (previous pass cut over 30 ms, new pass in over 30 ms; the drums
  keep going), judged at 60 %, at most 2 repeats; after that the run-in begins anyway so nobody is stuck. Each repeat delays the drop by 25.5 s. The brief's "never rewind a playing
  recording" rule is deliberately relaxed here: the *loop* is the recovery.
* Stems reduced by a mistake come back after 2 hits in a row.
* The earlier 256-beat design (4 custom loops with a bass loop, then the run-in with the recording entering at the -128 cue) is still in `plan.json` as `buildLoops` and is used for **mid-song builds of a
  cycling plan** (the second-drop build in tests); `stopAfterLegs: 1` means Act One plays only this first drop, after which the recording plays on in MIXING mode.

### Sequence (`plan.json`)

L1 opening build (above) Gatekeeper -> first drop (**the only leg played while `stopAfterLegs` = 1**); L2 handover Gatekeeper second drop -> Drop Dis first drop (**fallback with Drop Dis missing: build into the
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

**Automated** (all run in Unity play mode; 66 tests in the full suite):

* 19 `MusicEngineTests` - cue derivation matches the brief and rejects negatives; the plan file matches the test constants; perfect play (the song starts from its first sample, ONE recording voice
  never moved, one drums-only window, the run-in begins at `firstDrop -128 beats`, drop on time, no clipping, no gap); the three-knock cue on beats 0/1/2 and `DropReached` once; the knock sound's
  envelope; Act One plans only the first drop; the intro gate tolerates a few misses, and failing it loops the intro (new voice from clip 0 exactly at the section end, only the new pass keeps playing);
  two intro loops then on anyway, never silent; recovery that passes on the second pass (drop 25.5 s later); no phantom misses in mixing; mid-song second build returns to rhythm (cycling plan);
  stem mute/restore sample-identical after the restore; pause freezes then resumes identically; handover never from an already-reached anchor and invalid-entry handover rejected;
  three-track sequence + repeat (simulated tracks); pad strip geometry; offline demo renders + analysis.
* 3 `MusicPocSceneTests` in the real bedsit scene - eight turns in compass order keep the *same* session, the *same* stem voices, never reset the score or log and add no misses;
  bottom-strip pad taps do not turn; pause freezes the timeline in the running game.
* 7 `ActOneSceneTests` - see [ACT_ONE.md](ACT_ONE.md).
* **Runtime recordings from the built exe** (`-music -musicbot=... -tidybot=... -musicrecord=...`), analysed by `Tools/music/analyze_recording.py` (`Docs/music/results/`): perfect, partial, fail.
  In all three: 0 clipped samples, peak 0.98, the only silence > 250 ms is the lead-in before the music (0-8 s = wake-up + headphones + 1 s). At the start of the run-in the mix level is continuous
  (RMS 0.20 before, 0.24 after - the song just carries on) and the drop lands at the scheduled time (first onset within 3 ms) about 2.3x louder than the 1.5 s before it. Perfect: intro 42/42,
  drop and knock at 77.652 s (song started at 7.997 s). Partial: 38/42 = 90.5 %, drop 77.674 s. Fail: intro 45.2 %, looped twice (52.4 %, 40.5 %), run-in anyway, drop 25.5 s x 2 later (see the log).
  The knock's *sound* is verified in the offline render (voices at D, D+1 beat, D+2 beats; envelope test); in the exe recordings it sits under the drop and was not separately measured.

**Not verified by a human listening.** Everything above is signal analysis and logs. I have not listened to the transitions, so musical
feel (e.g. how the build layers sit under the recording, whether the fades are pleasing) is unjudged.

## Limitations / known gaps

* Drop Dis and Levels are missing: no real handover into another song has been run in the actual game. Handover logic is covered only by tests with simulated tracks (Gatekeeper audio standing in) - that proves scheduling, not musical quality. Act One stops after the first drop anyway (`stopAfterLegs: 1`).
* Recording-stem effects (muting the recorded kick etc. on a mistake) are impossible without stems; only custom stems react.
* The levels (recording 0.9, custom kick/snare 0.7 over the intro, custom drums easing out over the first 8 beats of the run-in) are my guesses from signal levels. The custom drums are un-pitched, so key clashes are not a worry in the intro, but whether they sit well over Gatekeeper's own drums is not auditioned. All of it is adjustable in `plan.json`.
* The song's first 25.5 s is not necessarily one musical section: I treated "the section before the current one" as everything before the `firstDrop -128 beats` cue (the only structural marker I have). If the track has a real intro/verse boundary inside it the minigame still covers both.
* Looping the intro on a failed gate is a hard cut/restart of the recording (30 ms cross-cut), not a beat-matched DJ loop; whether the loop point (74 beats, not a whole number of bars) sounds good is not auditioned.
* The knock is a synthesized wooden thump (no sample), mixed on top of the drop; its realism and balance against the drop have not been listened to.
* Forward destinations (North Space, East Dinosaurs, South Magic/Unicorns, West Transport) are labelled in the overlay only - **not built**; after the door opens the player stays in the room.
* Android: music/Act One code is platform-neutral but this pass was not rebuilt/run on a phone; the audio callback path (`OnAudioFilterRead` + Update pump fallback) is untested on device. `LocalAudio` is not bundled in any build.
* Pad touch input and tidy taps are tested through code paths (`RaisePad`, `TryTidyAtScreen`), not with a real finger. Input latency is uncalibrated (`InputLatencySeconds` = 0).
* One full-suite run in this iteration showed a cold-start `Bedsit did not become ready: creating characters` timeout (90 s) in the first live-content test after a recompile; it passes on rerun. It happened before any of this iteration's code ran in that test, so it is a pre-existing cold-start issue, not diagnosed.
