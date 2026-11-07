# Owner's brief: eight explorable environments on Doom II geography (7 November 2026)

Verbatim from the owner, kept here so every agent and every resumed session reads the same words. The lead's
plan for it is `docs/parallel-development/LONG_RUN_PLAN.md`; the contracts are `CONTRACTS.md`.

---

Work in https://github.com/Joesalmon1985/RhythmWarfare.

Implement eight explorable environments using the specified Doom II maps as their geographical foundations and the eight supplied concept images as their visual targets. The player travels through these environments on guided rails while playing the existing rhythm game and selecting visible destinations.

Complete the implementation, visual refinement, verification, commits and branch push. Begin with an implementation plan, then execute it without stopping at the planning stage.

## 1. Inspect the current project

Read AGENTS.md wherever applicable, docs/PICKUP.md, docs/HANDOVER.md and the current rail, map, art and continuous-run documentation.

Fetch remote refs and identify the active integration branch from current commits and handover documents. "Latest" means the current integrated development work, not whichever branch happens to have the newest timestamp. Record the chosen base and commit.

Create an isolated worktree and branch named `feature/doom-layout-worlds`, with a unique suffix if needed. Preserve unrelated local changes.

Existing implementation areas to inspect include:

- `src/story/world/story_map.gd`
- `src/story/world/story_world.gd`
- `src/story/world/story_player.gd`
- `src/story/world/story_lowres.gd`
- `src/run/run_rail.gd`
- `src/run/run_journey.gd`
- The current hotspot, choice staging, scene generation and art generation systems.
- `content/story/maps/`
- `docs/STORY_25D_PLAN.md`
- `docs/CONTINUOUS_RUN.md`

These paths are starting points: verify them against the selected branch.

Reuse the existing engine, audio clock, rhythm judging, run state and input system. Extend the map renderer where necessary. Keep the work compatible with other ongoing story, track and minigame changes.

## 2. Establish the eight references

Find the eight supplied PNGs, inspect each, and copy them unchanged into a clearly named art-reference directory in the repository. Create a manifest connecting each reference to its scene, Doom map and implementation files.

| Location | Doom II map | Supplied reference image |
|---|---|---|
| Warehouse floor | MAP07 — Dead Simple | Cobalt Warehouse Dance Floor.png |
| Copper bar | MAP02 — Underhalls | Copper Basement Bar, Three Hidden Routes.png |
| Rainy balcony | MAP15 — Industrial Zone | Rainy industrial rooftop, three musical paths.png |
| Chill-out lounge | MAP08 — Tricks and Traps | Mustard octagonal lounge of three routes.png |
| DJ booth | MAP04 — The Focus | Rhythm Booth, Three Hidden Routes.png |
| Loading dock | MAP13 — Downtown | Rainy Rhythm Club Loading Dock.png |
| Mothership | MAP11 — Circle of Death | Mothership Ringwalk Over the Void.png |
| Underworld | MAP29 — The Living End | Three Paths Across the Basalt Abyss.png |

Original map renders for comparison:
https://ian-albert.com/games/doom_2_maps/

If a reference image is missing, identify the exact missing file. Continue independent engine and map work while obtaining it; do not invent a replacement and claim to have matched the supplied image.

## 3. Reconstruct the geography

Use actual map geometry from an owner-supplied `doom2.wad` or an equivalent verified map export wherever available.

Build a reproducible conversion process into the current StoryMap format. Preserve recognisable footprints, connectivity, relative heights, major voids, platforms, stairs, corridors and sightlines.

Handle coordinate conversion, scale, winding, sidedefs, sector adjacency and floor/ceiling heights explicitly. Decompose sectors into the convex regions required by the current renderer and pathing without introducing visible cracks or changing connectivity.

Keep the original WAD and original game textures, sprites and audio outside Git. Create project-specific replacement art.

If only map renders are available, clearly identify the reconstruction as approximate and document uncertain geometry. Do not describe a guessed layout as an exact import.

Each map should exist as coherent navigable geography. Author curated rail journeys through its strongest spaces; it is unnecessary to force the player through every original corridor.

Translate the architecture into these distinct environments:

- **Warehouse:** square dance arena, speaker plinths and surrounding circulation.
- **Bar:** low interconnected cellar rooms, winding passages, drainage channels and short stairs.
- **Balcony:** separate industrial building masses, rooftop ledges, bridges and exposed drops.
- **Chill-out:** octagonal hub, angled walls and branching intimate rooms.
- **Booth:** tight windowed control rooms, equipment bays and interlocking corridors.
- **Dock:** separate city blocks, street corners, loading areas and service yards.
- **Mothership:** looping raised circulation around a deep central chamber.
- **Underworld:** towering central rock mass, huge lava basin and narrow ascending cliff ledges.

Preserve their different spatial identities throughout implementation. Changing textures on one repeated room layout does not meet the brief.

## 4. Place the player inside the environments

Use the existing first-person rail camera.

For each environment author:

- An arrival route.
- A recognisable reference viewpoint that echoes its supplied image.
- A default route that keeps the player within the current scene.
- Routes toward the three visible destination choices.
- Several additional viewpoints that reveal the geography through movement.
- Recovery or failure movements compatible with the current rhythm rules.

The player should walk through doors, around corners, over bridges and along ledges. Movement must follow valid space with appropriate eye height, clearance and floor transitions.

Route travel should reveal new views rather than merely moving the camera a short distance forward and backward.

Synchronise movement to the existing song clock. Preserve pause, restart, timing, tempo handoffs and rhythm outcomes. Use gentle turns and restrained head movement, keeping the pads readable throughout.

At choice windows, arrive at a stable viewpoint where the relevant destinations can be understood and selected.

## 5. Preserve the four-area choice concept

At the main reference viewpoint:

- **Bottom/foreground:** remain in the current scene.
- **Top/ahead:** one destination.
- **Left:** another destination.
- **Right:** another destination.

These are compositional regions within a real environment. Their shapes can vary with the architecture.

Use the following routing for the eight-scene concept:

| Current scene | Ahead | Left | Right |
|---|---|---|---|
| Warehouse floor | Balcony | Bar | Chill-out |
| Bar | Booth | Floor | Chill-out |
| Balcony | Mothership | Floor | Booth |
| Chill-out | Dock | Bar | Floor |
| Booth | Mothership | Balcony | Dock |
| Dock | Mothership | Floor | Underworld |
| Mothership | Underworld | Booth | Dock |
| Underworld | Mothership | Floor | Dock |

Audit differences from the existing story graph. Implement this connected scene set behind a development feature flag or equivalent isolated configuration, preserving existing quest entrances, progression and saves. Document any proposed changes to the main story graph.

Distinguish a physical passage within an environment from a transition to another world. Place any necessary world transition at a believable threshold after the player approaches it.

Keep the four musical pads and existing touch/click choice interaction. Do not introduce manual steering or additional movement buttons.

## 6. Make choices readable through the world

Use the characters in the references as destination guides. Preserve their recognisable costumes, colours and silhouettes.

Place them at believable distances and human scale. Let them beckon, make eye contact, step aside or react to selection.

Use architectural openings, local lighting, props and glimpses of the destination to support recognition.

Remove green rings and comparable abstract selection markers from these scenes. Communicate selection through an immediate character or environmental response: a nod, a door opening, a lamp changing, or an inviting gesture.

Make idle, available, selected and committed states distinguishable without gameplay text.

Validate the projected touch targets from every supported choice viewpoint. Prevent targets from being hidden by walls, overlapping each other or conflicting with pad touches. During a choice window, avoid camera motion that moves a target away from the player's finger.

## 7. Match the supplied art through playable assets

Build the look from textured geometry, sprites, lighting and atmosphere that hold together as the camera moves.

Use the supplied image as the visual target for each scene's palette, materials, scale, depth, architectural silhouette, characters and focal lighting.

Priorities include:

- Warehouse: cobalt light, steel trusses, crowd silhouettes and speaker structures.
- Bar: copper, damp brick, low pipes and amber practical lights.
- Balcony: wet steel, rain, cyan moonlight and layered rooftop silhouettes.
- Lounge: mustard upholstery, burnt orange, plants and warm lamps.
- Booth: dense equipment, cables, red LEDs and task lighting.
- Dock: rain-soaked tarmac, brick blocks, shutters and street lighting.
- Mothership: ivory organic ribs, mint illumination and violet depth.
- Underworld: black basalt, molten orange, crimson haze and extreme vertical scale.

Use consistent pixel density and art treatment across surfaces and characters. Avoid stretching a few generic textures over every environment.

A full-screen concept image used as a static background does not satisfy the walking-world requirement.

Improve the renderer selectively where the references require it, preserving the project's mobile rendering constraints.

## 8. Implement and inspect in stages

First complete the warehouse as an end-to-end pilot: imported geography, valid rail journey, three character choices, default remain behaviour and a polished reference viewpoint.

Inspect it in the running game, correct problems, then apply the working pipeline to the remaining seven scenes. Continue through all eight.

Use bounded subagents for geometry conversion, scene authoring, art and independent review where available. Assign one owner to shared engine changes and integrate frequently.

For every scene capture:

- Its reference viewpoint.
- At least two other rail viewpoints.
- A selected-choice state.
- A short movement recording where capture tools are available.

Compare actual in-game captures against the corresponding supplied image. Refine geometry, framing, materials and lighting based on observed differences. Check the scenes at phone viewing size as well as desktop size.

## 9. Verify the result

Run the repository's applicable checks and add meaningful coverage for new geometry conversion and rail behaviour.

Verify:

- Valid sectors, portals, triangulation and heights.
- Rail segments stay in traversable space.
- No camera travel through walls, props or unsupported drops.
- All three choices and the default behaviour work.
- Correct destinations and arrival poses.
- Stable rhythm timing during movement and scene transitions.
- Correct pause, restart and recovery behaviour.
- Existing story and minigame integration.
- Visible, reachable touch targets at each choice viewpoint.

Measure rendering performance on representative heavy views. Record the device or runtime used. Keep desktop measurements distinct from tests performed on an Android device.

Retain existing music and track integration. If "Valley of the Shadows" by Origin Unknown is already available locally, use the existing importer and playback pipeline for the opening warehouse presentation. Do not block the environment work on acquiring music.

## 10. Deliver and push

Commit coherent changes and push the feature branch. Do not merge it into the integration branch.

Deliver:

- Eight reconstructed and re-themed maps.
- Eight functioning sets of rail journeys and character choices.
- The original reference images and their manifest.
- Reproducible conversion and asset-building tools.
- In-game comparison captures and available movement recordings.
- Launch instructions for the complete experience and each scene individually.
- A concise record of verification, performance and remaining limitations.
- The branch name, commit SHA and comparison or draft PR link.

Report separately what was implemented, what was visually inspected and what was actually tested. Do not claim visual parity from code review or passing headless tests alone.

---

## The owner's answers (7 November)

- `doom2.wad` supplied: `C:\Users\joesa\rw-audio-work\doom\doom2.wad` (never in Git; `RW_DOOM_WAD` names it).
- The concept images: 16 PNGs in `C:\Users\joesa\Documents\Cursor\MusicGame\Concept art` (the eight named
  above, each with a `-N` suffix in its file name, plus a second variant of each scene).
- The eight scenes are a separate set behind a flag; the four raves of the bedsit brief borrow four of the
  geographies (Space from the Mothership, Magic from the Chill-out lounge, Dinosaurs from the Underworld,
  Transport from the Dock); the existing five-location campaign stays playable from a legacy entry.
- The opening track is the Chase and Status remix of "Valley of the Shadows" (already imported).
