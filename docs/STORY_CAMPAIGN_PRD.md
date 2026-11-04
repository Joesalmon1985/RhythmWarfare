# Rhythm Warfare — Story Campaign: Night One
## Product requirements and autonomous implementation brief for Claude Code

**Status:** Approved implementation brief / build the complete first level  
**Date:** 3 November 2026  
**Source repository:** https://github.com/Joesalmon1985/RhythmWarfare  
**Engine:** Godot 4.5.1, GDScript, existing landscape-first 1280 × 720 project  
**Working mode name:** **Story Campaign**  
**First level title:** **Night One**  
**Delivery expectation:** One cohesive implementation run, a runnable first level, original in-repository artwork, deterministic tests, screenshots, documentation and a clean implementation branch. **Not merely a proposal or 16-bar demo.**

---

## 1. Product vision and non-negotiable decisions

Build a separate **Story Campaign** mode in the existing Rhythm Warfare game. The player is a DJ performing an entire drum-and-bass set in a nightclub. The screen is **a fixed 2D illustrated nightclub viewed from the DJ's position**, looking over a mixing desk towards a dance floor. The upper screen is a densely populated, layered animated tableau built from **original sprites**. The four rhythm pads are visually integrated into the **foreground DJ deck**. The supplied track plays continuously. Accurate performance energises the crowd; poor performance deflates it. A handful of authored moments have visibly different outcomes according to the player's accumulated performance. The first level has a satisfying intro, development, climax and ending, not just a mood gauge and generic repeating sprites.

**Absolutely required:**

1. Add a visible **Story Campaign** entry on the main menu. **Keep the existing Campaign, Continue, Practice, Loadout, Settings, Developer and legacy duel functional and independently selectable.** Do not turn the current Campaign into Story Campaign.
2. Deliver a **complete playable 128-bar first story level**, approximately 176.6 seconds at 174 BPM, using the existing **First Watch musical content, chart, loadout, note judgement and synchronized stem transport**. Do not shorten the soundtrack, create a different score, or require the owner to export anything else from Ableton.
3. Present the scene as a **collection of independently animating original 2D sprites over one fixed nightclub background**, not a pre-rendered video, a scrolling world, an OpenRA battle, or a static screen with a few bobbing circles.
4. The nightclub is from the **DJ's eye-line**, with a convincing mixing desk across the foreground, four interactive deck pads and a visible crowd looking toward the DJ. Camera is **fixed** for level one; no panning to other rooms and no hard scene cuts during the set. Dramatic variation comes from sprite animation, staging, props, lighting and crowd movement.
5. The game should look like a **finished stylised illustrated level**. Original source artwork and the in-game assets must be delivered. No borrowed OpenRA sprites, copied game art, stock assets, paid image/video APIs, random internet downloads, asset-license uncertainty, grey placeholder rectangles, emoji crowds, or generic circles standing in for people.
6. Preserve existing **four-button pad mechanics**, MIDI-derived note positions, falling-note readability, calibration, misses/muting behaviour, music options and global volume settings. All four pads retain touch support and D/F/J/K keyboard support.
7. A **two-bar musical sequence** currently produces one final pass/fail event (60% default threshold). Story mode uses those events to drive crowd reactions, not unit production. The **eight-bar phases** define major authored visual cues and sections of the set. Do not silently implement the older four-bar rules.
8. No server, online account, video-generation tool, external paid service, runtime network dependency or game engine replacement.
9. Work in a **new Git branch**, commit meaningful milestones, never overwrite existing user audio and do not delete existing modes. Do not auto-push to `main`.
10. Complete the implementation and verify it **in this one Claude Code session** as far as tool access allows. Do not stop after producing a design plan. If a tool is unavailable, implement a local fallback, record the limitation and continue with the rest.

## 2. Source-of-truth reconnaissance — inspect before changing code

The repository is actively evolving. **Read the actual checked-out files first** and favour the code on the working branch over historical PRDs if they disagree. The current state inspected for this brief (3 November 2026) includes:

| Existing area | Relevant code / data | Required use |
| --- | --- | --- |
| Main menu | `src/scenes/main_menu.gd` | Add Story Campaign entry, do not replace legacy navigation |
| Session and settings | `src/core/session.gd` | Dedicated story launch state; preserve settings and campaign saves |
| Main rhythm play screen | `src/scenes/play.gd` | Reuse its proven transport/input/judgement patterns; do not couple story visuals to the battle view |
| Song loading | `src/core/level_loader.gd` and mission loader | Load the existing first mission with its current library/loadout resolution |
| Music | `src/audio/stem_transport.gd` and `src/core/song_clock.gd` | Synchronized musical transport; absolute music time controls all timed animation |
| Input/judgement | `src/input/pad_judge.gd`, `src/input/lane_input.gd` | Existing hit windows, holds, misses and touch rules |
| Note visuals | `src/ui/note_lane.gd`, `src/ui/pad_view.gd` | Preserve falling-note timing and pad feedback, visually skin them as DJ controls |
| Sequence outcomes | `src/core/sequence_tracker.gd` | Consume final sequence pass/fail + precision grade, exactly once |
| Match / practice logic | `src/core/match.gd` | Prefer reusing `Match.setup(level, null, false)` for judgement and stem events **if verified**; story must not display combat rewards or be marked as legacy practice |
| First mission | `content/missions/level_01.json` | 128 bars, 16 eight-bar phases, current `DDBDBDDBDBDBDDBD` form |
| Campaign content and global loadout | `data/campaign/campaign.json`, `songs/library/index.json`, `src/core/campaign.gd` | Read music selection, do not inadvertently grant existing campaign clears/unlocks |
| Owner music sources | `content/imports/first_watch.json`, `content/library/`, `ToAddTry1/` | Preserve owner WAV/MIDI provenance and current built music path |
| Test infrastructure | `tools/test.sh`, `tests/`, `tools/shoot.gd`, `tools/content/` | Extend, do not remove |

**Important current-game details:** At present the loadout is **global**, not per mission; the note cues **fall onto the pads**, not closing rings; and the mission's musical sequences are **two bars**. `StemTransport` plays looped stems via synchronized audio and may apply a per-bar gain program. Missed notes may mute an instrument until the next successful hit. Do not accidentally reset these to obsolete designs.

The first mission's existing music is the musical basis for **Night One**. Story mode must not call the legacy campaign result recorder to grant a military mission clear. A story-specific record must be kept separately.

## 3. Player experience, first launch and layout

**Main menu:** Add `Story Campaign` as a first-class option, visually aligned with existing options. Clicking it opens a small Story Campaign level screen with `Night One` (available) and a clear sense that additional chapters can come later. `Play` opens a brief title/intro card, then the same countdown and playable set. The player can pause, resume with the current countdown, restart, leave to the story menu, and see a bespoke end-of-set summary.

**Fixed camera composition:** Landscape 16:9. The club fills the stage area above the deck. The foreground mixing desk occupies the same responsive bottom area that existing pads need (standard setting presently 36% of viewport; compact 30%, large 42%). No independent set of decorative buttons covering the real hitboxes: the **four glowing deck pads themselves are the only game input controls**. They must retain adequate touch size and keyboard labels. The note lane lands precisely on their hit regions; keep a controlled dark/transparent lane overlay for legibility, without obscuring the crowd excessively. A pause control must be accessible without covering cues.

**Club scenery:** Perspective looking over the desk: dark room receding toward a far wall, truss/ceiling lights, suspended fixtures, speakers, rear booth/bar details, stage lights, floor tiles, atmospheric haze, crowd silhouettes at the back and distinctly illustrated dancers in the middle/front. Avoid text-heavy UI, cheap clip art and excessive particle noise. The booth must read as a physical mixing deck: deck housing, four luminous pads with credible labels/icons, faders or knobs, turntable/equaliser decoration and tasteful illuminated edge trims. The dance floor is the **visual focus** while the controls remain instantly readable.

**Visual art direction:** Original **stylised 2D neon vector/cartoon** with bold shapes, strong silhouettes, coherent perspective, crisp outlines and a restrained nightclub palette: indigo/navy shadows, magenta/cyan/violet lights, selected warm amber highlights. Build source assets in SVG and/or scripted vector art, then import to Godot as suitable textures; maintain editable source, transparency and sensible atlas organization. If programmatic vector assets are unconvincing, improve the illustrations, layering, lighting and staging rather than reverting to wireframe placeholders. Avoid photorealistic ambitions; pursue a consistent, intentional indie-game look.

## 4. Complete first-level dramaturgy: 128 bars, four acts

At 174 BPM in 4/4, one bar is approximately 1.37931 s; two bars ≈ 2.759 s; eight bars ≈ 11.034 s; 128 bars ≈ **176.55 s**. **Do not quantize to integer seconds or resample music to a rough approximation.** Every visual cue derives from exact musical ticks/seconds in the loaded level, not accumulated `delta` or guessed frame counts.

**Act I — Opening the room (bars 1–32):** Small crowd, subdued lights, stage warm-up, dancers begin with mild curiosity. The first few successful sequences lead to smiles, movement, clapping and better light activity; misses make dancers pause and look uncertain. The first bass phase (bars 17–24, per the current form) triggers a conspicuous low-frequency-inspired lighting change and wave of movement regardless of outcome, with intensity depending on performance. At the Act I transition, **good path**: a group of new dancers enters and joins the floor; **bad path**: a few dancers step back or drift toward the sides. Both rejoin the same fixed room and ongoing song.

**Act II — Finding the groove (bars 33–64):** More varied dance animations, a prominent front-row character, glow-sticks, moving beams, a deliberate dance-circle moment and visibly reactive sprites. Every eight-bar block has a distinct staging event or animation change. The cumulative performance at the transition controls an authored **spotlight/dance-circle success or awkward anticlimax**. No video or room transition.

**Act III — The peak (bars 65–96):** Bigger light and haze effects, the most obvious musical drop, synchronized crowd wave and a memorable central hero dancer or group animation. Successful sequences increasingly build the crowd into coordinated jumping and hands-in-the-air moments. Misses cause a visible brief drop in energy, not instantaneous disappearance or total silence. An authored **big-drop branch** chooses an electrifying synchronized crowd moment versus a stumble from which the set can recover.

**Act IV — Closing the night (bars 97–128):** Strong visual payoff. The room grows more theatrical without changing the camera. In the final eight bars, visually anticipate the ending and ensure the ending depends on the cumulative performance, not only the final input. Resolve to **three distinct final tableaux**: `Legendary Set` (crowd roaring / raised hands / lights at full power), `Good Night` (happy dancing / warm applause) and `Lost the Floor` (subdued, mixed expressions and sparse applause). Every path finishes at the **same soundtrack endpoint**, never early-stops the set for poor performance. Preserve recoverability until near the end.

**Sixteen eight-bar visual blocks**: Implement an authored event schedule for blocks 1–16, with distinct named set pieces and staging changes. Suggested beats: doors open; first groove; first bass reveal; dancers arrive; dance circle forms; spotlight pass; group footwork; first big cheer/setback; performer on riser; bass-heavy light wave; synchronized claps; floor ripple; crowd-wide raised hands; peak rave lighting; last bass flourish; closing tableau. Use the loaded phase form to align mode-dependent actions. No random unrelated animations, no identical-looking endless loop for all sixteen blocks.

**Branching model:** At least **three explicit intermediate authored good/bad story decisions** and **three final endings**. Branches can change who stands where, the animation performed, lighting, props and the emotional read of the room. Branches **reconverge** into shared musical time. Never generate a combinatorial tree of dozens of separate levels. Every two-bar result produces immediate crowd feedback, while eight-bar blocks and the three intermediate set pieces provide narrative structure.

## 5. Crowd: actors, animation and believable reaction

Deliver a minimum of **six distinct original foreground/midground character archetypes**, not recolours of a single silhouette masquerading as distinct anatomy. Give them distinct hairstyles, outfits, shapes, proportions and dance behaviour. Multiple palette/wardrobe variants are welcome. Populate the room with about **24–36 simultaneous visible crowd instances** where performance permits, across depth bands. Rear silhouettes may be simpler and cheaper than front characters.

Each archetype must visibly support **idle/sway**, **dance**, **cheer/jump/hands up**, and **disappointed/withdrawn** behaviours; include a **transition** between states where practical. Characters should actually move arms, shoulders, bodies, heads and/or legs, not only translate the whole sprite vertically. Prefer reusable sprite rigs (`Node2D` + child shapes/textures/bones/anchors) or authored animation frames. Animate at different offsets and slightly different speeds, seeded for repeatability, to prevent every dancer from moving in lockstep. Strong hero/group synchronized moves are deliberate exceptions. Character placement must avoid overlapping the interactive pads and avoid obvious depth sorting errors.

All lighting effects and sprite reactions must remain legible and not render the crowd as flickering noise. Implement lightweight independent controls for crowd states, positions, enthusiasm, light intensity and special moments. Transitions should ease rather than snap without reason.

**Crowd energy model — initial tuning baseline, adjustable in data:**
- Scale `0..100`, begin at `45` (an interested but restrained crowd).
- Each **resolved two-bar sequence** updates once: passed `sharp` +4; `steady` +3; `loose` +2; failed −5. Clamp to range. Use current grade names from `SequenceTracker`; ensure stray presses penalize via the existing judgement, not an invented second penalty.
- Bands: `0–29 Quiet/Unimpressed`, `30–64 Dancing`, `65–84 Hype`, `85–100 Euphoric`. Apply appropriate animation weighting, crowd expression and lighting while keeping visually meaningful variation at every band.
- At **act transitions**, assess both the recent block/act success rate and cumulative energy. These decisions are explicitly authored, deterministic and documented. A simple reference rule is `energy >= 55` AND at least half of the recent 16 two-bar sequences passed; tune carefully for convincing paths.
- Endings: starting reference thresholds `energy >= 85` AND overall passed sequences ≥ 75% = Legendary; energy ≥ 40 AND passed ≥ 50% = Good Night; otherwise Lost the Floor. Thresholds are tunable and must be tested with perfect, no-input and mixed autoplayer cases.
- Retain or log the actual path decisions and energy history so results can explain what happened. Continuous energy adjustment should be reversible: recovery from a poor start must visibly work.
- Individual cue feedback (hit/miss) may cause tiny local face/deck/light reactions; the **persistent state** changes only when a sequence has resolved. Do not overreact the entire crowd to every tap.

## 6. Music and sound design — existing sound is authoritative

**Reuse the exact current game music system.** Load the built `m01_first_watch` mission via its actual current loader and player loadout. The level uses the current owner's First Watch clips and all their existing MIDI/WAV-derived gameplay logic. No newly generated music, no replacement bassline, no hard-coded rhythm chart, no audio file duplication just for Story Campaign. The existing **global Loadout** must determine the audible kick/snare/bass/backing options and therefore the cues in Story Campaign. If a selected global loadout lacks a suitable resource, rely on current library fallback and report a normal recoverable warning.

Keep `StemTransport` and `SongClock` in charge of timing. Preserve synchronized looping stems, per-bar gain programming, the mute-on-miss and restore-on-hit rules, existing perceived latency calibration, music volume and audio fade behaviour. The music must never restart on a story branch, and visual effects must not become a second timing source. Use `clock.audio_time()` for sound-synchronized decorative effects, `clock.judge_time()` for input and note display as appropriate. Cross-check any deliberate animation offset against audible beat timing.

**Effects:** Story mode should **not** play irrelevant rifle, explosion or EVA battle sounds. Add optional subtle, fully original club reactions (e.g., synthetic light clicks/claps or a soft cheer-like layer) only if they can be produced in-repo legally and mixed beneath the music. Use the existing effects-volume setting, and keep them restrained. Preserve player hit/miss haptics and feedback. Do not invent recorded human cheering if no such legal audio asset exists. A silent crowd visually is acceptable if the existing music is powerful. Do not let SFX clip or overpower owner tracks.

**Musical readability:** Keep all existing judgement windows, pad hit zones, hold behaviour, four-pad mappings (including the current bass pitch mapping), cue lead-in settings, and falling-note display. Modify their *presentation* to fit the deck, not their semantics. Tests should show that the same input trace on the original First Watch mission and Night One yields the same note/sequence judgement data before presentation-specific story logic.

## 7. Scene structure and data model

Implement a reusable, self-contained story runtime, not a single enormous `story_play.gd` with hard-coded logic. Suggested responsibilities (names can vary if architecture is cleaner):

- `StoryCampaignData`/loader: validates chapter definitions, actor catalogue, timings, actions and branch destinations.
- `StoryDirector`: schedules visual events using the authoritative song tick; owns act transitions and authored conditional actions. No dependence on the OpenRA simulation.
- `CrowdController`: applies sequence results to score/state and coordinates crowd animation and position changes.
- `StoryStage` (Godot scene): draws fixed backdrop, crowd, decorative props, DJ deck and lighting with independent reusable nodes.
- `StoryCharacter`: reusable animated sprite actor with pose/state change and palette/depth variants.
- `StoryPlay`: hosts rhythm transport, original judge, story director, pause/resume, input, feedback and result routing. Separate scene is preferable to tightly weaving story branches into the old battle play screen.
- `StoryProgress`: new save path **`user://story_campaign.json`** containing version, best score/energy, clears and ending history, written safely without altering `user://campaign.json`.
- `StoryResult`: shows achieved ending, sequences passed, accuracy, best combo, closing crowd energy, narrative moments achieved, retry and return.

**Recommended files** (adapt where necessary):

```
content/story/night_one.json
assets/story/night_one/source/*.svg
assets/story/night_one/processed/*.png
src/story/story_director.gd
src/story/crowd_controller.gd
src/story/story_character.gd
src/story/story_stage.gd
src/story/story_progress.gd
src/scenes/story_campaign.tscn
src/scenes/story_play.tscn
src/scenes/story_result.tscn
tools/story/build_assets.py
tests/test_story_*.gd
docs/STORY_CAMPAIGN_HANDOVER.md
```

A scene-definition file should include: metadata (`id`, `level_title`, `music_pack`), bar count, exact authored eight-bar `blocks`, stage actions with tick/bar coordinates, initial crowd, actors and placements, optional per-act performance predicates, named success/failure branches, visual assets, outcome thresholds and a final ending mapping. Validate that all actors/assets/actions/branch references exist; no actions beyond bar 128; no scene progression that depends on framerate; no runaway recursive branch. Use bar/tick coordinates for authoring, never hard-coded wall-clock timers.

**Illustrative schema fragment** — this is a shape suggestion, not an instruction to omit the other 15 blocks:

```json
{
  "id": "night_one",
  "title": "Night One",
  "music_pack": "m01_first_watch",
  "duration_bars": 128,
  "initial_energy": 45,
  "blocks": [
    {
      "id": "opening_the_room",
      "start_bar": 1,
      "bars": 8,
      "events": [
        {"at_bar": 1, "action": "doors_open"},
        {"at_bar": 3, "action": "front_row_sway"},
        {"at_bar": 5, "action": "lights_low_pulse"}
      ]
    }
  ],
  "act_transitions": [
    {"at_bar": 33, "decision": "first_impression",
     "good": "new_dancers_enter", "bad": "dancers_step_back"}
  ],
  "endings": ["legendary_set", "good_night", "lost_the_floor"]
}
```

The actual content file **must contain 16 authored blocks**, at least three intermediate authored decisions, and all final outcomes. Ensure the director tolerates sequences resolving slightly after the next bar/act boundary, without wrongly predicting an unjudged result. If necessary hold a pending visual decision until the required prior sequences are final, while the song clock keeps running. No video buffering, no freezing the beat.

## 8. UX, input, pause and accessibility

- On opening Story Campaign, show Night One with a brief description and Play. Do not require the original military mission to be completed to access Story Campaign.
- A 2-second pre-play countdown may reuse the current flow. Narration/text must not block timing.
- The four pads are large, playable with both thumbs in landscape and accessible by D/F/J/K. Match the existing four-pad mapping in all musical modes; don't label instruments in a misleading way when the active family changes.
- Note lane, cues, judgement text, hold fills, bar/mode transition hints and pause UI remain visible over the decorative set. Strong lighting never hides the notes.
- Pause freezes song and all story animation at the same absolute song moment; resume uses existing count-in. Restart resets energy, crowd, event cursor and branch history. On app focus loss, use the existing sensible pause behaviour.
- Respect `high_contrast`, `reduced_effects`, calibration, cue lead-in, pad size and music/effects volume. Reduced effects stops violent flashes/strobes and reduces haze/particles while retaining readable mood changes.
- Touch input must not leak from the nightclub background into the pads; touches near the stage should not produce phantom notes. Handle 2 simultaneous touches as currently supported.
- Make happiness/sadness legible without relying exclusively on hue: expressions, posture, hand movement and stage activity must communicate status. No rapid full-screen flashing or unavoidable strobe.
- On song end, finish unresolved final note windows correctly; do not lose the final sequence because audio playback terminated first. Show a result transition after final judgements while preserving the completed song's ending.

## 9. Performance, exports and asset pipeline

Use the existing Godot 4.5.1 **GL Compatibility** renderer; no new plugins, 3D renderer or runtime image downloads. Target a smooth **60 FPS** on desktop and reasonable mobile performance (30 FPS minimum on a representative Android device, if available), with the existing audio/input feel unchanged. Use reused textures, sprite batching where feasible, simple shaders and bounded particle counts. Provide a lower FX profile tied to existing reduced-effects settings. Do not redraw every texture every frame or introduce high allocation per note.

The owner should be able to rerun one local generation script to regenerate *only original story art* without touching Ableton sources or existing assets. Prefer generated transparent PNGs from maintained SVG source; if external converters are unavailable, use an in-repo Python/Pillow fallback or native Godot procedural drawing. Add provenance and a short explanation of how to modify the sprites and background. Avoid enormous uncompressed images and duplicate textures. Only add screenshots and small sample assets necessary for review; do not commit giant generated captures.

Existing music import/build commands and the old campaign packs must continue to run. No requirement to rewrite the global loadout editor; it should work unmodified and the story level should honour its current selection.

## 10. Automated verification and acceptance tests

**Must test programmatically, not simply visually assert correctness:**

1. **Mode isolation:** `Story Campaign` appears on main menu; old Campaign, Continue, Practice, Loadout, Developer/duel and Settings still navigate correctly. Story completion never changes existing campaign clear/unlocks/last-played or overwrites `user://campaign.json`.
2. **Load and content:** Night One loads the **entire 128-bar existing mission** with the same chart/cues and actual current loadout-selected stems. No missing art, music, script class or data errors. Change global loadout → story hears/plays the corresponding options.
3. **Timing:** Test both a normal run and a simulated fast-forward/step harness. Actions, final sequence outcomes, branches and energy are deterministic at 30/60/variable frame steps. No cumulative desynchronization; beat-triggered visuals use the single song time.
4. **Best/worst/mixed outcomes:** `RW_AUTOPLAY=perfect` (or an equivalent deterministic input harness) must achieve the strongest ending and a visibly ecstatic crowd; `RW_AUTOPLAY=none` must reach the weak ending after **the full song**, with a subdued crowd; mixed seeded inputs should support the middle ending and recover from misses. No early level termination for poor performance.
5. **Sequence fidelity:** Sequence results match the existing judge: default **two-bar** subdivisions, correct finality, 60% threshold, no duplicate triggers, correct stray/hold treatment, no actions fired before judgement.
6. **Stage activity:** Every eight-bar block has at least one verifiable authored visual action. All **six original character archetypes** have all four emotion/action states, animated limbs/poses and valid imported assets. The on-screen stage is never blank after entering/restarting.
7. **Branch visibility:** At least three intermediate branches produce distinguishable on-screen actions and log the chosen branch, without changing soundtrack duration or requiring a second musical transport.
8. **Pause/resume/restart:** Music, note cues, dancers and timed light effects all pause and resume without rescheduling already executed events; replay starts with the correct energy and actor positions.
9. **Accessibility and responsive layout:** Inspect/screenshot standard, compact and large pad sizes. All pads remain within viewport, nothing critical obscured at 1280 × 720 and a narrower mobile landscape aspect. Reduced-effects and high-contrast configurations remain usable.
10. **Saves:** Save/read story results safely in `user://story_campaign.json` with a known version; corrupted saves fail gracefully and cannot corrupt military campaign progress.
11. **Audio:** No Red Alert battle sound leakage; no multiple simultaneous music streams; no music restarting after branch; no louder-than-music crowd SFX; miss mute and hit restore still work.
12. **Regression:** Run existing `tools/test.sh` and content build tests, adapt only tests that are actually invalidated by intentional presentation changes, never silently delete or skip failures.

**Visual inspection:** Export at least **five screenshots** in a local review folder: opening / act II normal dancing / high-energy peak / low-energy crowd / each visually distinct ending (six or more images if necessary). Ensure real Godot scene screenshots, not mockups presented as gameplay. Save a reproducible capture command. A simple time-lapse or GIF from automated screenshots is optional, not at the expense of completing the level.

**Document any untested Android specifics.** If an Android toolchain is present, perform a debug export/smoke test. If unavailable, report that honestly; do not claim on-device verification.

## 11. Delivery sequence for one long Claude Code run

**Do all phases, without stopping for the owner to approve each phase.** Only ask a question if blocked by an unavoidable destructive/security-sensitive action; otherwise choose a reasonable default, document it and continue.

**Phase 0 — Safety and reconnaissance:** Check Git status and current branch; preserve uncommitted changes. If working tree is dirty, do not overwrite owner changes or stash without care; choose a safe branch/worktree. Read actual code paths. Record the starting commit SHA. Create feature branch (suggested `feature/story-campaign-night-one`). Write an initial short implementation checklist, then proceed to code.

**Phase 1 — Skeleton:** Add story entry/navigation, story-specific session/result routing, story save isolation, new story play scene and a data-driven scene loader. Get a first 128-bar run to play with working note judgement and no battle simulation.

**Phase 2 — Original art and animation:** Author source nightclub background and real sprites, integrate generated assets, stage composition, six varied character rigs, 24–36 character instances, deck and 4 functional pad surfaces, responsive layouts and light/haze/speaker/equaliser decorations.

**Phase 3 — Music-driven response:** Wire two-bar sequence events into energy and crowd pose states; test best/mixed/no-input performance, mute/restore, pause/restart and change of global loadout. Avoid changing core judge semantics.

**Phase 4 — Full level staging:** Author all 16 eight-bar blocks across four acts, three intermediate authored good/bad branches, distinctive peak moments and three complete endings. Fix visual monotony and weak feedback, not just data completeness.

**Phase 5 — Polish:** Motion easing, light timing, readable deck/note visuals, mood expressions, responsive control placement, SFX balance if added, reduced FX and high contrast. Improve original art until the stage reads as a nightclub full of dancers at screenshots, not a developer debug scene.

**Phase 6 — Verify and deliver:** Headless tests + render smoke test + visual screenshots + existing regression tests. Fix discovered issues. Update README and create `docs/STORY_CAMPAIGN_HANDOVER.md`: files created, architecture, runtime commands, how to tweak art/mood/story JSON, tests run and results, test limitations and known remaining problems. Update existing documentation only where navigation requires it; do not rewrite military campaign PRDs wholesale. Commit coherent milestones and final branch. Print final branch/commit SHA, changed file summary and exact commands to launch and test.

Claude may use independent subagents **only** for safely partitioned, nonoverlapping tasks such as asset illustration, JSON story authoring and tests. Own integration centrally; ensure every generated file is reviewed and all tests pass before signing off. Do not leave conflicting/unfinished subagent edits.

## 12. Definition of done — no premature sign-off

The job is **not done** if it only adds a menu button, empty scene, wireframe sprites, placeholder mood text, a 16-bar demo, standalone screenshots unrelated to the running game, or a proposed architecture. It **is done** when a player can select `Story Campaign → Night One`, perform the whole existing First Watch musical set from the DJ's position with the four deck pads, watch an original animated crowd in a visually finished fixed nightclub respond throughout **all 128 bars**, experience meaningful authored performance-dependent moments, reach one of three clear final tableaux, view a story-specific result, retry, and return without damaging the legacy game — with regression tests and actual screenshots.

**Priority if constrained:** (1) old game intact, (2) whole song + exact controls and audio, (3) playable and visually attractive animated nightclub, (4) continuous crowd feedback, (5) full authored branch/ending coverage, (6) accessibility/performance polish and documentation. Do not compromise (1)–(3) to chase minor optional flourishes.

---

## 13. Final execution instruction to Claude Code

Implement this PRD against the checked-out repository in a single uninterrupted coding run to the extent the available session and tools allow. Make design decisions without bouncing routine questions back to the owner. Inspect and adapt to the repo's actual current architecture. Use entirely original artwork; never modify existing owner audio. Write real code and tests, perform actual checks, save screenshots, and make meaningful commits on a dedicated branch. **The deliverable is a complete animated first story level, not another PRD.** When finished, report exactly what works, what was actually tested, what remains unverified, and how to launch it.
