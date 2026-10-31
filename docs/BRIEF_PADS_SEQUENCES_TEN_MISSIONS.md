# Brief: interface polish, sequence rewards and ten playable missions

Two parts. Part A is the owner's decisions and the amendments agreed on 31 October 2026 after a review of the
brief against the repository at commit `9b3f8d1`. Part B is the owner's brief, verbatim. Where A and B
disagree, A wins. Everything in B that A does not touch stands as written.

## Part A: amendments and decisions (31 October 2026)

1. **No owner audio exists yet.** Every pack in the repo is placeholder (`placeholder: true` in each
   `level.json`). Ignore B's "existing completed owner exports"; there are none. The drop-in path (B section 7) is
   for renders the owner will make after this work. The final deliverable for the owner is
   `docs/CONTENT_TO_RENDER.md`: a short document listing every MIDI and WAV file to create to replace the
   placeholders, with exact paths, file names, bar ranges, tempo, meter, sample rate, bit depth, channel count,
   release-tail rule and Ableton export settings. Keep the placeholder audio as WAV files the owner can open in
   Ableton as references for what each file should contain, alongside the Ogg the game plays.
2. **The lane view goes.** Owner decision: drop the falling-note highway entirely (`src/ui/lane_view.gd` and its
   lookahead setting). The four illuminated pads are the only play interface. The lookahead setting becomes the
   pad cue lead-in setting.
3. **Bass on pads: one pad per bass voice**, as B section 3 says. The pack's level 3 chart (one bass voice across
   four buttons with alternating-thumb overrides and a MIDI hash guard) is archived, not ported. The thumb-gap
   rules (960 / 480 ticks) and the per-button thumb-zone checks are retired with it; keep the two-touch maximum.
4. **Music architecture: a loop library at 174 BPM.** Grooves, fills, bass structures and accompaniment are
   mission-independent clips in one library with stable ids. A mission is an arrangement of library clips plus
   its own cue sequences, rewards and waves. Each rendered sound variant is a WAV for one clip; several sound
   variants share a clip's MIDI. The three existing songs (`campaign/First_Three/level_0N/Music/*.mid`) become the
   default content of missions 1 to 3, cut into library clips where their bars repeat and kept as longer clips
   where they do not. Their MIDI files are never edited; the hashes in `campaign/Musical_Source_Integrity.json`
   must still hold.
5. **Assembly is offline.** The one build command assembles the chosen clips into full-length per-slot stems per
   mission (sample-accurate placement from absolute musical time, tails mixed, no drift) and the existing
   `AudioStreamSynchronized` transport plays them unchanged. No runtime clip engine. No in-game import screen:
   the import/build command runs on the PC; in the game at most a read-only list of installed content and what is
   still placeholder.
6. **Retire the per-note production model.** The instrument catalogue recipes, the 2/2/3 loadout caps and the
   round-robin assignment of production groups to defense points are superseded by sequence rewards (B section
   4). The three defense points stay as the zones where rewarded buildings are placed (prepared sockets per
   approach) and where any rewarded mobile unit holds. Update `data/instruments/`, `data/campaign/`, the loadout
   screen, the PRD and the handover so only one rule set remains.
7. **Keep the legacy duel mode.** Owner decision: schema 1 packs (`songs/level_01`, `songs/test_16`), the mirrored
   battlefield, the Rush AI on both sides and their tests stay working; a later multiplayer mode will build on
   them. Do not delete them. They may stay in the menu under a separate developer or free-play area.
8. **Holds are forgiving.** An early release ends that hold's contribution to its sequence; it never fails the
   sequence by itself. A hold's coverage counts toward the sequence threshold; completing it to the tail counts
   as full coverage. No precision release gesture.
9. **Reward scale.** Early missions reward static defenses first (the first drum sequence reward is one pillbox,
   as B says), with the occasional infantry unit such as a rocket soldier so the player has something against
   vehicles. A good run of an early mission should end with a handful of defenses (about six to ten), not one
   per two bars; size the sequences (two to four bars) and the capacity rules accordingly, and make the
   at-capacity behaviour (repair, upgrade or an explicit alternative) visible to the player.
10. **Wave units must fight defenses.** `ignore_structures` on wave units (set in `BattleSim.spawn_wave_unit`)
    currently makes them fight only units and their objective. Rewarded defenses must be targeted and must block
    or be destroyed; no permanent stalemates. This is a stage 2 requirement, not a later revisit.
11. **Strike slow practice.** No time-stretched audio. Practice uses the same clips, cues and recognition at the
    authored tempo, with no progression rewards.
12. **Generated music for all ten missions.** Use the generator for every mission's MIDI and placeholder WAV now;
    the owner will replace files through the drop-in path later. Spend effort on the import and replacement path
    and on readable cues, not on making generated music sound good. Demonstrate replacement with a fixture,
    including an edited-MIDI fixture, as B section 7 requires.
13. **One session, subagents where sensible.** The owner wants this done in one long session and will test at the
    end. Use subagents for independent pieces (authoring missions 4 to 10 in parallel once the contract and
    mission 1 are done, test writing, documentation), one writer per set of files, and verify their output
    before building on it.
14. **Progression.** The finished campaign ships with normal progression on by default; keep `unlock_all` in
    `data/campaign/campaign.json` and `RW_UNLOCK_ALL` as the developer switch. Migrate the existing
    `user://campaign.json` save rather than resetting it.
15. **Branch and workflow.** Work on `main`, commit at the end of each of B's five stages with
    `bash tools/test.sh` green, push after each stage. Never edit the MIDI under `campaign/First_Three/*/Music/`
    or anything under `Documents\Cursor\DuelMaster`. Rebuild the Windows and Android exports at the end per
    `docs/EXPORT.md`; the phone run is the owner's.

## Part B: the owner's brief (verbatim)

# Rhythm Warfare: interface polish, sequence rewards and ten playable missions

Implement this brief in https://github.com/Joesalmon1985/RhythmWarfare. This is an implementation request: make the changes, generate working placeholder content, test the result and update the handover. Do not stop after a design proposal or a single demonstration level.

The owner delegates the detailed unit progression, building layouts, rewards and tuning to you. Make sensible decisions and document them; do not wait for the owner to choose every unit, mission name, colour or numerical threshold.

## Establish the current state

Read the repository instructions, README, `docs/HANDOVER.md`, the relevant PRD/campaign sections, existing tests and current code before editing. Inspect the actual working tree and preserve unrelated work. Follow the established repository workflow.

When this brief was prepared, main was `9b3f8d14b1040d543a7bf816065685749686ee90`, with three playable defense missions, saved progression/loadouts, per-slot audio, a centred base and off-screen enemy entries on the left, right and top. Levels 4–10 were data-only plans. Check for newer work and build on it.

This brief supersedes earlier proposals for a player-operated phase arranger, scrolling note lanes as the primary interface, a three-bass maximum, and one production reward per successful note. Update conflicting documentation and configuration rather than leaving both rule sets active.

## 1. The intended experience

The player selects a mission by NAME, makes only the musical choices that mission requires, and plays four illuminated instrument pads while their defenses survive enemy waves until the song ends.

The mission authors the song: phase order, duration, use of selected patterns/sounds, fills, which instruments are followed, reward schedule and waves. Players discover its structure through play. There is no player timeline editor or phase-arrangement screen in this scope.

Keep the player base centred, three defensive approaches, enemy spawns outside the visible window, automatic defenders and the absence of an enemy base. Required objectives must survive to the authored musical deadline. A missed cue never directly damages the core or instantly ends the run. Keep landscape mobile play and the OpenRA visual style.

## 2. Musical choices: separate patterns from sounds

Implement these as separate concepts, with fewer choices in early missions:

- **Kick/snare grooves:** authored rhythms, such as kick on beats 1 and 3 with snare on 2 and 4, or an extra kick between beats 3 and 4. These beat numbers describe musical timing, not physical button numbers. A groove contains coordinated kick/snare parts. You may expose compatible kick/snare variants within the groove selector if useful; do not present arbitrary combinations that produce an invalid chart.
- **Kick sounds:** eventually choose two different kick sounds; different phases can use different selections.
- **Snare sounds:** eventually choose two different snare sounds, similarly used by the mission.
- **Bass structures:** eventually choose two or three phrases defining bass pitches, rhythm and note lengths.
- **Bass instruments:** eventually choose two to FOUR different synth sounds. Four supersedes the previous three-bass cap. These are choices available across the arrangement, not a requirement for four simultaneous inputs.
- **Drum fills:** eventually choose one or two fills, placed by the mission. A fill normally replaces the relevant end of a groove instead of accidentally doubling it.

A late mission can request two or three grooves, one or two fills, two or three bass structures and two to four bass voices. Early missions can fix most ingredients and ask for only a simple groove and sound. Store the requirements per mission; do not force the fully unlocked selection screen onto mission one.

Provide useful short auditions of choices. A preview of an individual choice is allowed; do not reveal the mission's complete arrangement before play. Give every mission a valid default setup, remember choices, and make the path to Play straightforward.

Use 174 BPM, 4/4 as the initial shared authoring standard, with an 87 BPM half-time feel in beginner content. Preserve long, audibly sustained bass notes. Existing completed owner exports and their source MIDI should remain available as compatible default content where possible; archive/migrate them explicitly if a new arrangement needs different notes.

Musical MIDI, audible audio, required player cues, pad assignment and production rewards are separate data. Drums may continue throughout a bass phase, but create no drum input requirements during that phase. Never require bass and drum inputs in the same bar, including hold tails. Accompaniment is never automatically charted.

## 3. Four illuminated instrument pads

Make the default playing interface four large, clear instrument pads. Remove the need to read falling notes or a scrolling highway. Keep the battlefield visible, but put successful input recognition ahead of decorative effects.

- Keep four physical positions stable and comfortable for two thumbs. Leave inactive pads visible but dim.
- Use a predictable instrument/voice assignment. In drum phases, pads represent the kick/snare voices being followed; in bass phases, they represent the bass voices being followed. Default to voice-based cues rather than making bass pitches into four piano keys. Keep the assignment stable within a phrase and avoid unnecessary reassignment between phases.
- A subtle preparatory brightening or ring can lead into a cue; the main pulse marks its musical onset. Players need anticipation, not an unexplained flash they can only react to after the beat. A very short in-play introduction can teach the pads without revealing the whole song.
- Presses provide immediate visible feedback. Bass holds stay visibly active until their authored tail and clearly show completion. Keep holds forgiving, with no need for a precision release gesture unless essential to the chosen design.
- Keep cues driven by the shared song clock, including countdown, pause/resume and calibration. Preview animations must not create a second timing authority.
- Use contrast and shapes as well as colour. Keep feedback from hiding the next cue. Instrument names/icons may sit on or beside pads when they improve recognition; do not fill them with MIDI pitches or technical identifiers.
- Maintain a maximum of two simultaneous touches and validate the work of each thumb. Four chosen synths do not imply four-finger chords. Retain keyboard support and make displayed desktop bindings agree with actual controls.
- A brief in-play transition cue may announce the incoming instrument family. It should help the player react without presenting the mission's phase roadmap.

Revisit the previous battle/rhythm screen split for this pad interface. Choose sensible mobile proportions and safe areas rather than retaining a tiny cue area merely because the old lane layout used it.

## 4. Forgiving sequences, with precision earning faster rewards

Replace per-note production in the campaign. Individual presses contribute to a clearly bounded sequence; one successfully completed sequence earns ONE production/construction action.

The starting drum-sequence reward is exactly **one pillbox**. Later missions can reward one ground unit, one building, or a repair/upgrade action. Choose the reward types and progression yourself. Keep this deliberately smaller in scale than the old per-note unit groups; do not recreate a unit-per-press system behind a renamed interface.

Define sequence boundaries in mission data and communicate progress unobtrusively. A complete one- or two-bar groove is a reasonable starting unit; beginner sequences can span two bars at 174 BPM to preserve the slower felt rhythm. Handle long bass notes deliberately. Do not silently cut a hold or place a sequence boundary through it.

Use generous cue recognition and a forgiving sequence success threshold. Do not require every note to be perfect. Choose and document initial timing windows, coverage rules, hold tolerance and precision grading, then tune them through testing.

Separate SUCCESS from PRECISION:

- Meeting the forgiving sequence threshold earns its reward after the sequence finishes.
- Better timing produces a shorter construction/deployment delay; acceptable, less accurate input produces a longer delay.
- A failed sequence earns nothing, then the next sequence starts normally. Do not wipe rewards already earned.

For example, 0.5 / 1.5 / 3 second construction delays could be initial grades, but these numbers are suggestions, not requirements. A small preparing/ready indicator should make the benefit legible. A sequence cannot reward before its future required cues have been judged.

Prevent duplicate claims, one press satisfying several cues, held pads acting as repeated taps, and mashing earning the fastest reward. Extra presses can reduce precision without making an otherwise accepted sequence fail immediately. Test these behaviours explicitly.

Do not let a denser groove or rapid fill automatically multiply army output. Define reward-bearing sequences consistently across compatible choices and balance their opportunity count. A successful long-hold sequence can earn the same single reward as a busier tap sequence.

Choose how bass sequences are rewarded: buildings, mobile defenders or a progression between them are your decision. Preserve the same sequence-based principle. Construction, queues, reward grading and enemy waves must use deterministic song/simulation time and pause together.

## 5. Ten playable missions and the ground roster

Create all TEN genuinely playable campaign missions with complete placeholder music, authored input sequences, enemy waves, functional battlefields, rewards and progression. Entries marked planned, missing audio or copies that only change the title do not count.

You decide mission names, lengths, unlock order, unit/building rewards, producer rules, objectives, difficulty and layouts. Introduce new musical decisions and combat roles gradually. Early missions should teach and forgive; later missions combine learned ideas. Keep accuracy acceptance generous and make difficulty come from patterns, coordination and battle pressure.

Audit the current rules/art and use the full eligible ground roster across the campaign. At the reviewed revision, the ground combat actors were:

`e1`, `e2`, `e3`, `e4`, `jeep`, `apc`, `1tnk`, `2tnk`, `3tnk`, `4tnk`, `arty`, `v2rl`, `ftrk`.

Cover existing ground-relevant buildings and walls as functional parts of the campaign: objectives, production, defense and support. Aircraft, helipads and air-service rewards are out of scope. Audit AA-only structures and document their treatment; do not invent an air threat just to justify them or count unused catalogue entries as meaningful content. If an actor has art but lacks an implemented ability, implement an honest supported role or state the limitation; do not imply an APC transports troops if it only has its gun.

Provide a coverage matrix listing every eligible actor/building, its first appearance and its actual role/mission use. Use it to catch omissions. Replace earlier air-themed planned unlocks with appropriate ground content.

Design building arrangements for playability. Give rewarded buildings prepared valid sockets or another reliable automatic placement system. Spread defenses sensibly around the approaches, keep routes open, and prevent overlaps or infinite stacking. Decide what happens at capacity: repairs, upgrades or an explicit alternative. Make this clear rather than silently discarding a successful sequence reward.

Ensure new defenses participate properly in combat. Revisit existing enemy `ignore_structures` behaviour where necessary; rewarded defenses must not be decorative, and structure targeting/pathing must not create permanent stalemates. Buildings, defenders, enemies and critical objectives need coherent damage/targeting rules.

Retune waves for the new reward rate. Enemy wave timing remains authored independently of the player's live accuracy. Surviving the song with the required objectives alive wins. Test beginner mistakes, not only scripted perfect inputs. Keep unit counts and effects appropriate for a phone.

## 6. Menus, options and feedback polish

Build a coherent interface in the existing game's visual style. Use consistent spacing, typography, selected/focused/disabled states, Back behaviour, readable controls and responsive layouts.

- **Home:** a clear Continue/Play route, Campaign, Practice and Settings. Put legacy/debug/testing tools in a separate unobtrusive area.
- **Missions:** names with only the minimal availability/progress indicators needed for navigation. No exposed phase timelines, enemy composition, rhythm lesson, duration or advance structural spoilers on mission cards. Do not make the player configure irrelevant choices.
- **Selection:** concise cards or equivalent controls, short auditions, clear selection counts and good defaults. Display friendly asset names. Locked/unavailable choices explain the action needed in plain language.
- **Settings:** useful volume controls, timing calibration, visual cue lead-in/readability, pad size or layout settings where practical, contrast/reduced effects and optional vibration. Save settings and provide sensible resets. The owner should not need to edit config files for normal options.
- **Pause:** Resume, restart, settings and return to mission setup; a readable resume countdown.
- **Results:** outcome, useful sequence/timing feedback, earned unlocks, Retry, Change choices and Next mission. Keep technical chart IDs and diagnostics out of the normal flow.
- **Practice:** use the same cues and recognition as the campaign, with no progression rewards. Support rehearsing a difficult sequence/section if practical. Keep slow practice, if implemented, honest about audio timing and separate from campaign scores.

Keep normal progression enabled by default in the finished campaign; preserve unlock-all as an explicit developer option rather than the standard player experience. Migrate existing saves/settings safely instead of resetting progress unnecessarily.

## 7. Drop-in WAV/MIDI content and real placeholders

Implement an actual owner-facing content workflow. The owner must be able to export WAV/MIDI from Ableton, place the files in a documented location, and import/rebuild them without changing GDScript or manually rewriting large level JSON files.

Support the distinction between:

1. A rhythmic/melodic structure, represented by musical MIDI and a chart/sequence template.
2. An instrument sound rendering that structure, represented by matching WAV audio.
3. A mission arrangement that uses these assets while independently selecting required input cues and rewards.

Provide a simple folder convention and example asset pack. Use stable IDs and minimal metadata to distinguish groove parts, fills, bass structures, sound variants and accompaniment. Several rendered sound variants can share the same source MIDI. Changing a preset requires a new WAV; changing source notes/timing/duration requires regenerating affected arrangement/chart data and matching audio.

A rendered WAV cannot be played through a newly selected Omnisphere/Pigments preset inside Godot. Every offered structure/sound combination needs its own compatible render, or a clearly supported rendering method. Never offer a selectable combination whose sound is missing. Do not require the owner to render every possible complete-song combination.

Build the missing assembly step. The current transport loads complete synchronized stems; arbitrary clips are not already a drop-in feature. Assemble or cache the selected compatible clips into a gapless arrangement using the existing single-clock design. Choose a practical implementation and measure memory/loading costs on mobile. Choices are made before the run, so a live clip-launching system is unnecessary.

Preserve support for existing full-length per-slot stems, or provide a safe documented migration. Keep source MIDI and owner recordings intact. Never overwrite real supplied audio when rebuilding placeholders; make placeholder generation explicit and reversible.

Generate actual non-silent placeholder WAVs and matching MIDI for every required mission/choice, with recognizable kick, snare, sustained bass and accompaniment. They should sound musically coherent enough to test phases, holds, fills and mixes. Label placeholder status in authoring/import information and a concise player-facing notice; do not fill every menu with development prose.

Use canonical 48 kHz, stereo, 16-bit PCM WAV game inputs initially. Keep tempo/meter, musical length, release tails and source provenance explicit. Support common Ableton type 0/1 PPQ MIDI exports; if tempo is absent, use an explicitly recorded import/default tempo rather than guessing from the audio. Preserve full MIDI note durations and starting silence.

For clips, distinguish musical duration from release-tail duration. Align placements to absolute musical timing and sample frames without accumulating rounding drift. Mix tails where appropriate; do not append an extra silent/tail bar every time a clip repeats. Holds may not leak across a drums/bass input-mode boundary.

Validate asset existence, MIDI compatibility, tempo/meter, declared pitch/harmonic compatibility, audio format and frame coverage, source versions, cue conflicts, sequence boundaries, holds and mixed-output headroom. Reject incompatible combinations with helpful messages. Equal file lengths alone do not prove musical sync: provide audition/listening checkpoints and state what was actually checked.

The owner workflow should be as simple as: copy an example asset folder, replace its WAV/MIDI, provide the few required labels/fields, run ONE documented import/build command or use a small import screen, then audition/use it. Demonstrate this with a replacement fixture, including an edited MIDI fixture; do not merely write instructions for an importer that has not been built.

## 8. Work order and completion evidence

Implement in coherent stages, keeping the project runnable:

1. Define/update the content contracts, mission choice requirements, instrument-pad assignment and sequence rewards.
2. Finish the new four-pad interaction and sequence-to-pillbox loop in one mission, with placeholder audio and polished navigation.
3. Implement the real WAV/MIDI import/assembly path and verify replacing assets.
4. Build all ten missions, progressive choices, unit/building coverage and balance.
5. Complete UI/options, migration, regression checks, exports and handover.

Continue through all stages. Keep progress updates concise. Resolve routine design details yourself and record the decisions.

Run appropriate existing and new tests. In particular verify cue/hold recognition, generous acceptance versus precise reward speed, sequence pass/fail and one-time rewards, spam/duplicate prevention, pause/retry determinism, audio/phase continuity, valid building placement/capacity, all ten missions loading/completing, progression/unlocks, save migration and content replacement.

Use several seeds and perfect, plausible imperfect and no-input trials to tune the battle. Do not imply a simulation pass establishes human difficulty. Inspect the actual menu, selection, pad play, hold, pause and result screens at phone-like landscape sizes. Produce desktop/Android builds using the repository's established export workflow where the environment supports it; explicitly report anything unavailable.

Update the README/handover and provide:

- A brief explanation of the chosen pad mapping, sequence success/precision rules and reward progression.
- A ten-mission table and actual unit/building coverage matrix for the owner, separate from spoiler-free player menus.
- Exact drop-in paths, example filenames/metadata, Ableton export requirements and the one import/build command.
- Tests, balance and performance evidence, plus honest limits on phone testing and listening checks.
- Known remaining issues and build/run instructions.

The finished result must be a polished, playable ten-mission campaign with generated placeholder content and a working replacement path for the owner's WAV/MIDI exports—not just a future plan.
