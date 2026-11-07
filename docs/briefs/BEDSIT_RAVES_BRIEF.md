# Owner's brief: the bedsit opening, four raves, three activities and street racing (7 November 2026)

Verbatim from the owner, kept here so every agent and every resumed session reads the same words. The lead's
plan for it is `docs/parallel-development/LONG_RUN_PLAN.md`; the contracts are `CONTRACTS.md`.

---

We are revising RhythmWarfare's opening and adding new activities. Implement this work in parallel with the Doom II geography, rail movement and visual-polish work already requested.

Repository: https://github.com/Joesalmon1985/RhythmWarfare

This is an implementation instruction. Plan, build, integrate, visually inspect, test, commit and push the work. Continue beyond writing documentation.

## 1. Coordinate the parallel work

Inspect AGENTS.md, current handovers, active branches and the existing parallel-development ownership and integration documents.

Establish two coordinated workstreams:

**Environment stream:** Doom II map conversion, world geometry, rail traversal, environment art and visual polish.

**Gameplay stream:** bedsit navigation, four rave variants, puzzle activities, racing rules, progression and activity input modes.

Use separate worktrees and branches. Use bounded subagents where available, with clear file ownership and one integration lead.

Agree the shared interfaces first, then work against fixtures and adapters while the other stream proceeds. Define contracts for:

- Scene entry and exit.
- Theme selection.
- Rail destinations and arrival poses.
- Activity entry, results and exit.
- Input ownership and rhythm participation.
- Puzzle progression.
- Bass unlocking through the existing audio system.
- Race environment rendering and camera poses.

One owner should integrate changes to shared files such as RunPlay, the minigame host, rhythm judging and audio transitions. Do not independently rewrite these in both streams.

Respect the current music/narrative transition interface. Gameplay code should request musical changes through the agreed interface.

Keep an up-to-date ownership table, integration checklist and branch/commit handoff.

## 2. New opening: the bedsit

The player starts inside their bedroom/bedsit.

Build one coherent room viewed in four cardinal directions. Turning reveals different sides of the same room, with consistent furniture and geometry.

The four world interaction areas behave as follows:

| Area | Action |
|---|---|
| Left | Turn 90 degrees left |
| Right | Turn 90 degrees right |
| Bottom | Stay facing the same direction |
| Top/forward | Leave for the rave associated with the current facing |

Direction-to-theme mapping is fixed:

| Facing | Rave theme |
|---|---|
| North | Space |
| South | Magic and unicorns |
| East | Dinosaurs |
| West | Transport |

Start facing North. Turning wraps correctly through all four directions.

Every facing must contain a visually understandable forward threshold into its corresponding rave. Make these surreal transitions feel intentional within the bedsit.

Use objects, decoration, lighting and sound to suggest the destination before entry. Avoid dependence on written direction labels or a menu. Development overlays may show compass direction.

Bedsit navigation should allow relaxed inspection without rhythm failure forcing an unwanted departure.

These four world interaction areas are separate from the musical pad controls.

This opening supersedes the previously proposed opening route between the eight concept scenes. Preserve existing content and save compatibility; retain legacy entry points for development rather than deleting unrelated campaigns.

## 3. Four flavours of rave

Create four distinctive rave environments:

- **Space:** orbital architecture, alien clubgoers, cosmic views and luminous equipment.
- **Magic and unicorns:** enchanted dance spaces, magical creatures, iridescent materials and playful surreal details.
- **Dinosaurs:** prehistoric scale, dinosaur clubgoers, foliage, fossils and volcanic or jungle atmosphere.
- **Transport:** a rave built around vehicles, platforms, depots, machinery and movement.

Each contains the same three functional activities:

1. Fix the bass knob on stage.
2. Work in the cloakroom.
3. Serve drinks at the bar.

Each also provides access to the street-racing activity and a route back to the bedsit.

Share activity logic across themes. Supply theme-specific props, customers, animation, presentation and spatial placement through data.

Give the environments different architectural silhouettes and circulation. Shared functionality should not result in four identical rooms with swapped textures.

Coordinate with the environment stream to reuse the Doom-based geometry and art pipeline where suitable. The previous concept images remain useful material, lighting and spatial references; the new theme brief governs these four raves.

## 4. Puzzle one: restore the bass

The opening rave track is "Valley of the Shadows" by Origin Unknown, using the locally available version and existing audio-import pipeline.

Initially its bass stem is locked off.

The player must:

1. Select a visible route onto the stage.
2. Travel there on the existing rail system.
3. Interact with the DJ deck.
4. Free the stuck bass control and turn it up.

Keep the interaction short and tactile. Show the knob resisting, then responding when fixed. Communicate the task through the deck, nearby props and character reactions.

Successful repair unlocks the actual bass audio and produces an obvious audible and visual change.

Implement bass availability separately from current mix volume: ordinary rhythm-driven mixing must not bypass the puzzle lock. Once unlocked, normal mixing rules can use the bass.

Resume the bass at the current transport position with an appropriate musical ramp or boundary. Never restart it from the beginning or let it drift out of synchronisation.

Persist completion for that rave's current visit/run. Re-entering the stage must not reset it.

If suitable stems are unavailable, continue implementation with a clearly identified development fixture and report the missing audio dependency. Do not pretend a full-track volume change is isolated bass control.

## 5. Puzzle two: cloakroom same/different

This activity temporarily replaces rhythm play.

A sequence uses exactly four visually distinct symbols. On each scored trial, the player decides whether the current symbol matches the immediately preceding symbol.

Controls replace the musical pad strip:

- Large left button: SAME.
- Large right button: DIFFERENT.

Use matching and contrasting pictograms, a brief demonstration and immediate feedback. Avoid requiring written instructions during play.

Rules:

- Show the first symbol as an unscored reference.
- Score subsequent comparisons against the immediately previous symbol, including after an incorrect response.
- Generate a balanced mixture of matches and non-matches.
- Correct answers process coats quickly.
- Incorrect answers process them slowly.
- Show the coat queue, handovers and customer reactions in the world.
- Prevent repeated taps from scoring one trial multiple times.

Use a finite, configurable workload. Suggested starting default: eight coats, with correct responses taking roughly one second to process and incorrect responses roughly three seconds. These are tuning defaults.

Give completion a clear visual payoff and update the rave's cloakroom completion flag.

Allow the player to leave and return without corrupting activity state.

## 6. Puzzle three: bar recipe memory

This activity also temporarily replaces rhythm play.

Implement a working-memory drink-serving game:

1. A customer presents a pictorial drink order.
2. Briefly demonstrate its ingredient sequence.
3. Hide the demonstration.
4. The player reproduces the sequence using four large ingredient buttons in the former rhythm-pad area.
5. Animate the drink being prepared and served.

Use clear ingredient silhouettes and colours together. Keep ingredients thematically appropriate to each rave.

Begin with two ingredients and introduce three after success. Keep recipes, presentation time and workload configurable.

Correct preparation produces a quick, happy handover. Incorrect preparation produces an obvious mistake and a slower remake. Make retries understandable and keep the activity recoverable.

Suggested initial workload: four successfully served drinks to complete the bar task.

This should feel different from the cloakroom's repeated same/different judgement.

## 7. Explicit activity input and rhythm modes

Inspect the existing MinigameActivity, MinigameController and run_minigame_host implementation before extending it.

The current minigame system may assume rhythm continues during activities. Add an explicit capability or mode instead of globally changing that assumption.

Required behaviour:

| Mode | Musical pads | World/activity input | Rhythm penalties |
|---|---|---|---|
| Ordinary rave exploration | Active | World choices | Existing rules |
| Cloakroom | Replaced by same/different | Activity controls | Suspended |
| Bar | Replaced by ingredients | Activity controls | Suspended |
| Racing | Active | Four driving areas | Active; affects speed |

During cloakroom and bar play:

- Music continues through the existing transport.
- Suspend note judging and rhythm-derived energy loss.
- Suspend rhythm-triggered wobble, falling and forced route changes.
- Hold ordinary rail progression and scene-departure decisions.
- Route each input to one owner.
- Prevent an activity tap from also hitting a pad or selecting a world exit.

On exit, restore the prior interface and resume judging on a clean musical boundary with a readable lead-in. Never count notes missed while the activity owned the controls.

Preserve existing activities that intentionally retain rhythm play.

## 8. Street racing from every rave

Every rave has a visible way to enter a racing minigame.

The player becomes someone driving a car through streets. Use the existing 2.5D Doom-style renderer for the road, buildings, traffic, rivals and cockpit presentation.

Build actual movement through a course with depth and occlusion. The environment stream owns reusable geometry/rendering support; the gameplay stream owns race simulation and decisions.

Maintain rhythm play throughout the race.

Show four large driving-choice regions within the world view: top, bottom, left and right. These remain separate from the musical pads.

Use stable driving meanings:

- **Top:** continue or commit to the forward opening.
- **Bottom:** brake or drop behind.
- **Left:** move toward the available left route/lane.
- **Right:** move toward the available right route/lane.

Present timed situations where the player must identify a safe or advantageous action to avoid a collision or overtake.

Examples include a braking car ahead, an opening beside a rival, a blocked lane or a narrowing street.

Make consequences readable from traffic positions, brake lights, road geometry and vehicle motion. Do not rely on memorising arbitrary symbols.

Start with approximately four seconds per decision, configurable for difficulty. Show remaining time with a clear visual countdown; a small seconds display is acceptable.

Allow selection changes until commitment. Commit explicitly or resolve the current selection at the deadline, consistently. Give immediate selection feedback.

Ensure every generated situation has a reachable safe response. Support multiple valid responses where the road situation warrants them.

## 9. Race outcomes and presentation

Use a deterministic race model with:

- Player distance and speed.
- Rival positions and speeds.
- Driving decision outcomes.
- Rhythm performance.
- Collision and recovery states.
- Finish order and win/loss.

Good rhythm sustains acceleration and speed. Poor rhythm slows the player.

Good driving avoids penalties and enables overtaking. Bad or missed driving choices cause visible contact, braking or lost time.

Both skills must materially affect the result. Keep penalties bounded and recoverable, with a minimum travelling speed so the race can finish.

Use a finite distance-based course, initially targeting about 60–90 seconds at ordinary performance. Slower play may take longer.

Show progress through rivals, overtaking, finish-line approach and the final result. Winning means actually finishing ahead of rivals.

Animate lane changes and speed effects smoothly. Avoid intense camera shake or roll that makes the rhythm pads hard to read.

Freeze deadlines and simulation correctly on pause. Do not use wall-clock timers that keep running while paused.

After the race, return the player to the rave they entered from, preserving its theme and puzzle progress. Allow replay.

Race entry is available without requiring all three rave tasks first. Track puzzle completion and race wins separately.

## 10. Progression and integration

Use explicit state for:

- Bedsit facing direction.
- Current rave theme.
- Bass repair completion.
- Cloakroom completion.
- Bar completion.
- Race results.

Scope puzzle completion per rave theme within the run. Define what persists across saving, loading and starting a new run; follow existing save conventions and provide migration defaults.

Complete the same three activities regardless of selected flavour. The player does not have to visit all four flavours to understand or complete the opening experience.

Make completion visible through changed objects and character behaviour.

Keep scenes, themes, activity configuration and race encounters data-driven where practical.

## 11. Build and verify in parallel

Agree contracts and fixtures first. Build a complete vertical slice with the bedsit, one rave, all three activities and one race. Then populate and polish all four flavours.

Do not wait for finished art to implement gameplay. Do not call placeholder visuals finished art.

Test meaningful behaviour, including:

- Four turns return to the original bedsit view.
- Each facing enters the correct rave.
- Bottom preserves facing.
- Bass remains locked until repair and resumes in sync.
- Cloakroom comparisons remain correct after wrong answers.
- Bar sequences and retries work.
- Replacement activities generate no phantom rhythm failures.
- Input ownership is restored correctly.
- Racing keeps both pad input and driving choices active.
- Pause freezes race deadlines.
- Rhythm and driving both influence race performance.
- Every race has a reachable finish.
- Returning from activities preserves rave state.

Run existing applicable regressions. Use the project's isolated save and test-launch conventions when running multiple worktrees.

Inspect in-game stills and motion at desktop and phone viewing sizes. Check touch-target clarity, feedback, camera comfort and pad visibility.

## 12. Deliver

Push coherent commits on the gameplay feature branch and provide the environment stream with a precise integration handoff.

Deliver the integrated feature branch or draft PR, launch instructions, configuration notes, screenshots, available gameplay recordings and a concise verification report.

Document remaining dependencies and distinguish automated checks, visual inspection, listening checks and actual device testing.

Do not merge into the main integration branch without instruction.

---

## The owner's answers (7 November)

- The bedsit is the opening; the four raves are the first act; the raves borrow four Doom geographies
  (Space from the Mothership, Magic from the Chill-out lounge, Dinosaurs from the Underworld, Transport from
  the Dock); the legacy campaign stays playable from a dev entry.
- The opening track is the Chase and Status remix of "Valley of the Shadows", already imported
  (`content/music/tracks/origin_unknown_valley_of_the_shadows_chase_status_remix.json`; the pack in
  `C:\Users\joesa\rw-audio-work\packs\...`, with a bass stem).
- Art polish is required ("Make sure to do art polish").
