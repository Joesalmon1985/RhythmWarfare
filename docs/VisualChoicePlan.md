# RhythmWarfare — Complete Visual Interaction & Rhythm Adventure Conversion

## Mission

You are the lead development agent working on:

https://github.com/Joesalmon1985/RhythmWarfare

I want you to plan and then implement a major redesign of the existing game in one autonomous development run.

**Use Fable for initial architecture and planning, Sonnet subagents for implementation, and Opus for the final graphics, animation and visual polish review.**

Your job is to coordinate this work, delegate intelligently, integrate all changes, run tests, inspect screenshots, resolve problems and deliver a complete playable result.

Do not simply produce a plan and stop. Plan first, then execute the plan automatically.

Do not ask me routine implementation questions. Make sensible decisions, document them and continue.

If the requested model aliases are unavailable, use the nearest available equivalents and record the substitution.

---

# 1. The fundamental game design

RhythmWarfare should become a combination of:

- A continuous four-button drum-and-bass rhythm game.
- A first-person, on-rails cinematic adventure.
- A visually driven branching narrative with interactive environments.

**The player has only two types of gameplay input:**

1. Four musical pads, which they must play in time with the continuing music.
2. Touching or clicking visible objects, characters, doors, destinations and environmental features to select what they want to happen.

There must be NO manual walking, joystick, WASD movement, steering, free-look requirement, inventory management or additional gameplay controls.

All movement happens automatically through the existing 2.5D world engine using authored on-rails camera animations.

Keep existing pause, settings and accessibility controls outside this simplified gameplay model.

## The central gameplay loop

1. The music plays continuously, and the player performs the rhythm pattern using four pads.
2. The game displays interesting objects, characters, locations and possible paths within the environment.
3. The player taps a visible object or destination.
4. That object immediately changes visually to confirm selection.
5. Rhythm gameplay continues without interruption.
6. At the appropriate musical boundary, the game evaluates the player's performance.
7. Good performance executes the desired action or route.
8. Poor performance produces an alternative outcome: another route, failed interaction, setback, surprising story development or, where appropriate, game over.
9. The appropriate on-rails animation plays.
10. The next section begins, presenting new visual opportunities while the music continues.

**The player chooses what they want to happen by touching the world. Their musical performance determines whether it happens. The story is communicated through what they see and hear.**

This must become the governing design principle for all existing levels.

---

# 2. Critical design restrictions

These requirements are non-negotiable.

### A. Continuous rhythm

The music must not stop for decisions, interactions, exploration or camera transitions.

Existing audio transport, MIDI timing, four-pad judgement and Beat Shaper music packs must be preserved.

Music continues during on-rails movement and cinematic sequences.

Musical transitions should be scheduled on beat/bar boundaries without restarting the clock.

The player must remain able to hit notes during animations.

### B. No written directional choices

Remove all written prompts such as:

- Go left / Go right.
- Enter the Trial.
- Choose your way.
- Continue to the next room.
- Select an option from a floating text menu.

Replace them with visible interactive elements belonging naturally to the environment.

Examples include doors opening, lamps flickering, an NPC beckoning, a ladder descending, an unusual painting, a glowing mechanism, or a crack forming in the ground.

Environmental signage can remain where artistically appropriate. Normal menus and accessibility settings may use text. But gameplay navigation must not require reading written choices.

### C. Obvious visual feedback

Every selectable object needs at least three visual states:

- Available: visibly interesting or discoverable.
- Selected: immediately and unmistakably confirms the player's touch.
- Committed: the selection resolves and its corresponding animation begins.

The player must be able to change a selection until it becomes committed.

Selection feedback must be visible while music is playing and must not obscure the four pads.

### D. Success and failure branches

A player's intended action and the actual outcome are separate concepts.

For each major choice, support success and failure outcomes.

Failure must not merely show a generic red flash and then continue identically.

It should cause a meaningful consequence where the existing narrative allows it: a different destination, altered world state, an encounter, a setback, a different character response or an alternate scene.

Avoid unwinnable states and repeated failure loops without recovery.

### E. No unnecessary new mechanics

Do not introduce movement controls, dialogue trees, inventories, complex puzzle interfaces, minigame buttons or separate control schemes.

All complexity should come from what the player can see, choose and experience.

---

# 3. Inspect the actual repository first

Before implementing anything, inspect:

- The current checked-out branch and working tree.
- `main` and `feature/run-on-25d`.
- The existing 2.5D Story Campaign.
- The continuous-run engine.
- The Bassment dungeon/trial system.
- All currently authored worlds, rooms, passages, routes, encounters and endings.
- Existing music packs and their assignments.
- Existing screenshots, tests and development documentation.

Important starting references:

- `docs/RUN_DUNGEON_MUSIC_PLAN.md`
- `docs/STORY_CAMPAIGN_HANDOVER.md`
- `docs/STORY_25D_PLAN.md`
- `src/story/world/`
- `src/run/`
- `src/trial/`
- `content/story/`
- `content/run/`
- `content/trial/`
- `tools/story/`

Treat the actual checked-out code as authoritative where documentation is outdated.

Identify the most complete, suitable integration base. Preserve uncommitted user work and create a dedicated implementation branch. Do not assume that `main` already contains all the newest work.

Do not push to `main` automatically.

---

# 4. Scope — ALL existing content

This is not a Warehouse-only prototype.

The redesign must cover all playable levels, locations and routes that exist in the current repository.

At minimum, inspect and account for:

## Night One / Warehouse

The dance floor, stage, DJ booth, balcony, corridor, toilets, mysterious wizard, Bassment entrance and major story transitions.

Make the nightclub feel alive and interactive.

## Mothership

The alien dance floor, gallery, reactor, bridge, helm, medical bay, examinations and alternative endings.

Players should interact with aliens, machinery and environmental features.

## Underworld

The arena, demon court, furnace, chains, throne, lava pit, cage and alternative routes.

Add environmental challenges and visually distinctive success/failure sequences.

## Hospital

The hospital bed, visitors, ward, corridor, day room, café, garden and bandstand.

Interactions should communicate the surreal mystery of the player's situation.

## The Ward

The day room, corridor, art room, dormitory, treatment room, courtyard and performance stage.

Use environmental details and character behaviour to tell the story.

## The Bassment

The current implementation contains a substantial branching adventure, including approximately 63 passages across 16 zones.

Inspect and preserve its actual branching content, secrets, items, encounters and victory/death outcomes.

Transform its written choices into physical visual interactions within the existing 2.5D engine.

Reuse authored zone environments intelligently rather than creating a separate map for every passage.

## Additional content

Inspect the actual repository for newer or alternative scenes, late-game worlds, routes and playable modes. Include all relevant currently implemented continuous-adventure content.

Do not silently omit existing levels or reduce the game's playable scope.

Preserve the military mode and original Story Chapters as separate playable modes where applicable.

---

# 5. Design a reusable interaction and cinematic system

Do not implement this through dozens of bespoke button handlers.

Develop reusable data-driven systems supporting:

### Visual hotspots

Each interactive target should define:

- Unique ID.
- World and room.
- Position in the existing environment.
- Type: object, character, exit, environmental feature, encounter or secret.
- Visible state and selection feedback.
- Availability conditions.
- Optional rhythm challenge.
- Successful outcome.
- Failure outcome.
- Corresponding camera route and animation.
- World-state changes.
- Optional repeatability.

The system must support pointer/touch hit detection against objects projected into screen space, including reasonable mobile touch targets.

Do not draw route arrows or labels as the primary navigation method.

### Choice scheduling

Allow choices to be made while playing music.

The player may change their selection before the next commitment point.

Commit the selected action at a musically safe boundary.

Support sensible visual defaults when no choice is made, without forcing players to read instructions.

### Performance-based outcomes

Use the existing rhythm performance system to determine successful and failed outcomes.

Keep failure thresholds tunable and fair.

Maintain deterministic outcomes for identical inputs.

### Cinematic execution

Use existing `StoryPlayer`, map waypoints, portal routing, movement styles, actor animation and environmental effects.

Support short interactions, longer on-rails walks, encounters and transitions between worlds.

Maintain the musical clock and pad responsiveness throughout.

### Persistent world state

Support objects that have been activated, characters who have moved, routes that have opened, secrets discovered and encounters completed.

Preserve appropriate state between scenes and revisits.

Avoid introducing a player-facing inventory interface.

---

# 6. Expand choices throughout the worlds

Do not merely convert two route buttons into two clickable doors.

The environments should contain a richer variety of meaningful interactions.

For every existing playable scene, audit:

- What interesting locations can be seen?
- Which characters can be approached?
- Which objects can be activated?
- Which environmental features can suggest secrets?
- Which interactions affect the music?
- Which interactions open new routes?
- What happens when rhythm performance is poor?
- Can the player encounter something unexpected?

Introduce additional options wherever practical, reusing existing art, world geometry, characters and camera routes before creating new assets.

Prefer a smaller number of genuinely different outcomes to many superficial hotspots that all do the same thing.

Ensure alternate paths eventually reconnect where sensible, avoiding an uncontrolled combinatorial explosion.

All existing main routes and endings must remain reachable.

---

# 7. Art direction and graphics

Preserve the established low-resolution 2.5D pixel-art presentation.

Use the repository's existing procedural art, sprite, texture and animation pipelines.

All new graphics must be original, stylistically consistent and appropriately integrated into the existing environments.

New artwork should make visual choices clear through environmental composition, contrast, animation, lighting, movement and recognisable silhouettes.

Do not solve everything with floating glowing rectangles.

Do not introduce unrelated asset styles, generic UI icons or inconsistent resolutions.

The visual language should be coherent across all five worlds and the Bassment.

---

# 8. Agent orchestration — plan in Fable, build in Sonnet, polish in Opus

## Stage 1 — Fable: complete architectural and implementation plan

First, use Fable as the planning and orchestration agent.

Have it inspect the actual codebase and produce:

1. A technical architecture for the new interaction system.
2. A complete inventory of existing levels, rooms, paths and choices.
3. A level-by-level conversion matrix showing what needs replacing.
4. A proposed set of new interactions and branching consequences for every world.
5. An approach for maintaining uninterrupted rhythm during choices and cinematics.
6. A concrete implementation sequence.
7. A dependency map showing which tasks can run in parallel.
8. A test and visual acceptance plan.
9. A subagent delegation plan with explicit file ownership.

Save the plan to:

`docs/VISUAL_RHYTHM_ADVENTURE_PLAN.md`

The plan must distinguish existing functionality from proposed functionality and identify technical risks.

Do not wait for my approval after producing this document. Proceed with implementation.

## Stage 2 — Sonnet: parallel implementation

Use Sonnet subagents with isolated worktrees and clearly defined responsibilities.

Suggested workstreams:

**Agent A — Core interaction engine**

Implement visual hotspots, selection states, screen-space hit testing and input routing.

**Agent B — Rhythm and narrative integration**

Implement the performance-based choice resolver, musical commitment points, outcome scheduling and continuous-audio safeguards.

**Agent C — Existing campaign conversion**

Convert Warehouse, Mothership, Underworld, Hospital and Ward. Expand their interactions, maintain existing routes and ensure each environment contains meaningful visual choices.

**Agent D — Bassment conversion**

Convert the authored passages, encounters, secrets and endings into environmental interactions and 2.5D camera journeys.

**Agent E — Validation and automated playtesting**

Develop and maintain tests covering visual selections, performance outcomes, reachability, input timing, music continuity and complete campaign walkthroughs.

Delegate further work to subagents where that genuinely improves throughput.

Avoid overlapping edits to shared files. The coordinating agent owns architecture integration, resolves conflicts and maintains the green test baseline.

Have subagents make small, meaningful commits. Integrate and test frequently rather than waiting for all worktrees to finish.

## Stage 3 — Opus: art and visual polish

Once the functional implementation is integrated, use Opus to review all scenes and screenshots.

Opus should focus on:

- Making interactive elements visually obvious without written prompts.
- Improving new pixel-art assets and their integration.
- Clear selection and commitment animations.
- Environmental lighting, contrast and atmosphere.
- Smoother and more cinematic rail journeys.
- More interesting environmental reactions to success/failure.
- Consistent visual quality across worlds.
- Making the Bassment feel integrated into the same game.
- Maintaining readability on a phone screen.

Use the existing asset generation tools to create and refine graphics. Do not assume that an Opus coding agent can directly generate finished raster artwork without a suitable image pipeline.

Inspect actual captured screenshots after making changes. Fix visual defects rather than only reporting them.

Opus should also remove obvious placeholder presentations and inconsistent interfaces introduced during development.

---

# 9. Acceptance criteria and automated tests

The work is complete only when the actual playable game meets these criteria.

### Controls

- Exactly four rhythm pads plus touching/clicking the environment for gameplay.
- No required manual walking or camera steering.
- No written directional-choice menus in the converted experience.
- Selections clearly change appearance.
- Selections can be changed until commitment.
- Touching the environment never accidentally triggers musical pads.

### Rhythm and timing

- Music continues throughout all navigation and scene transitions.
- Musical judgement stays synchronised.
- Pad inputs remain responsive while cinematic animations play.
- No audio restart or unintended timing drift.
- The player can fail to execute an intended action through poor musical performance.

### Story coverage

- All existing main worlds work.
- All authored major routes remain available.
- The Bassment is playable through the revised visual interaction model.
- Significant decisions have meaningful alternative outcomes.
- Secrets, encounters, endings and recovery paths remain reachable.
- World-state changes behave consistently.

### Automated testing

Use and extend the existing test tools.

Test perfect, intermediate, poor and no-input rhythm policies.

Test multiple choices, changed selections, default selections, success branches, failure branches and replay behaviour.

Check all destinations and waypoints for validity and graph reachability.

Test real scene transitions, not only the underlying pure logic.

Capture screenshots before and after selections, successful outcomes and failed outcomes.

Test with different frame rates and ensure music timing does not depend on render frame rate.

Run the full existing regression suite and fix regressions.

Where available, perform an Android export/smoke test. If device testing is not possible, clearly distinguish that from successful desktop tests.

### Completion evidence

Produce a coverage report listing every existing world, scene and major branch, with its implementation and test status.

Do not claim completion merely because the game launches or the tests compile.

---

# 10. Integration and delivery

Maintain one integration branch.

Save:

- `docs/VISUAL_RHYTHM_ADVENTURE_PLAN.md`
- `docs/VISUAL_RHYTHM_ADVENTURE_HANDOVER.md`
- A complete scene/choice coverage matrix.
- Screenshot contact sheets covering every world.
- Testing instructions and results.
- Any necessary asset generation scripts.

Document the branch name, final commit SHA, completed features, tests executed, known limitations and remaining work.

Ensure the game is launchable without special developer flags.

Leave all finished work committed on the implementation branch. Do not merge or push to `main` unless explicitly authorised.

---

# 11. Priority and autonomy rules

Work autonomously through the following priorities:

1. Preserve music synchronisation and the four-pad gameplay.
2. Build the universal visual interaction and outcome system.
3. Convert every existing playable world and major choice.
4. Convert the Bassment.
5. Expand the environments with new interactions and choices.
6. Apply Opus visual polish.
7. Complete regression tests, walkthroughs and documentation.

Use the most appropriate available Sonnet subagents for implementation, reserving Opus for tasks where its visual and architectural judgement adds value.

Do not waste the implementation run repeatedly replanning, asking for approval, or debating settled design choices.

If a feature proves unexpectedly difficult, implement the best robust solution consistent with the design, document any limitations and continue with the remaining content.

Do not sacrifice coverage of entire levels to perfect one small area.

Do not destroy, replace or unnecessarily regenerate the user's existing WAV, MIDI or music-pack assets.

Avoid unnecessary dependencies, expensive runtime graphics techniques and changes that make Android performance significantly worse.

---

# 12. Begin now

Start by:

1. Inspecting the repository, current branch, relevant feature branches and working-tree state.
2. Launching the Fable planning process.
3. Writing the complete implementation plan and coverage matrix.
4. Assigning parallel Sonnet implementation workstreams.
5. Executing those workstreams and integrating them.
6. Running automated tests and capturing visual evidence.
7. Performing the Opus visual-polish pass.
8. Testing the completed campaign and documenting the result.

**Do not stop after the planning phase. Continue into implementation and verification without requiring further input.**

The intended final result is a complete, visually interactive, on-rails rhythm adventure covering all existing content, with an extremely simple control system and a much richer set of branching experiences.

The player's only gameplay actions are to keep the beat using four pads and touch the things they want to interact with.

Everything else should happen through the world itself.

