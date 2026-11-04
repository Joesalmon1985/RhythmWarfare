# Story Campaign: 2.5D (Doom-style) rebuild, player journey, and campaign-wide playtesting

Status: plan agreed 2026-11-04, not started. Written against branch `feature/story-campaign-night-one` at `f013328`.
Work happens on a new branch `feature/story-25d` cut from there, so the finished 2D version stays intact and shippable.

Owner's brief, in their words: keep the graphics they like, but make them *2.5D, Doom style*; let the player *move around*;
in Night One the player *starts on the dance floor as a dancer; as they do well they climb onto the stage and become the DJ;
if they do poorly they start to feel ill and have to rush to the toilets to be sick*; improve the *graphics and variety of each
level*; and do *robust playtesting* that a player can progress *from level to level, start to finish, with perfect and poor play*.

Three sessions: (1) this plan, (2) a Claude Sonnet session builds it (work packages WP0 to WP8 below), (3) a Claude Opus session
does the visual polish (section 9). Hand-off prompts for both are in section 12.

## 1. What stays, what changes

Stays (and must keep working byte-for-byte in logic terms):
- All music, judgement, pads, falling notes, `StoryRun` / `Match` rhythm-only mode, `CrowdController` energy model, `StoryDirector`
  scheduling, decisions and endings, `StoryProgress` saves, chapter routes and interludes, the autoplay policies, the headless tests.
- The art itself: every SVG/PNG under `assets/story/<chapter>/` (characters, props, walls, floors, lights) and the Python generators in
  `tools/story/art/`. The 2.5D world is textured *with this art*, so the look the owner likes survives the change of projection.
- The 2D `StoryCharacter` rig and its analytic beat poses (the dancers keep dancing exactly as they do now).
- The cutscenes (`StoryInterludeFx`) stay 2D in the build phase; polish may restage them (9.6).

Changes:
- `StoryStage` / `StoryView` (the painted 1280 x 720 rooms with a faked dolly) are replaced by a real 3D world rendered Doom-style:
  low internal resolution, flat unshaded surfaces, per-sector light levels, vertical billboards, no camera pitch, beat-locked head bob.
- The camera is the player. It moves through the club on an authored rail driven by the story decisions (dancer > stage > DJ booth, or
  dancer > corridor > toilets), with free look at all times. Free walking is a stretch goal (section 4.4), off by default.
- Every chapter becomes a small connected map of 4 to 6 rooms with its own geography for the good path and the bad path.

## 2. Rendering architecture (decision: Godot 3D, not a shader raycaster)

Why 3D rather than a Wolfenstein-style raycaster in a shader: the rooms need stairs, a riser, a pit, a stage platform and door
frames that occlude; the `gl_compatibility` renderer (project.godot, mobile too) handles simple unshaded 3D well; and Opus can polish
geometry, props and light with ordinary scene tools. The Doom look comes from *how* it is rendered, not from a raycaster:

- `StoryWorld` (new, `src/story/world/`): builds the 3D scene from a map file (section 3). Floors and ceilings are polygon meshes per
  sector, walls are quads per segment, all `StandardMaterial3D` unshaded with nearest-neighbour textures and `vertex_color_use_as_albedo`
  for per-sector light. Textures are the chapter's existing SVG art rasterised to small tiles (64 or 128 px) by `build_assets.py`
  (new `textures/` output per chapter, deterministic, listed in the manifest).
- Rendered into a `SubViewport` at 480 x 270 (setting: 360p / 270p / 180p), nearest-filtered up to the stage area above the pad strip.
  Reduced-effects keeps the same resolution but disables bob, stagger and the queasy post-process.
- Light: no real lights. Each sector has a light level and a colour that are functions of song time and the stage state (palette,
  strobe, flicker, pulse, ending), applied as vertex colours each frame. Distance darkening is a fog setting on the `Environment`
  (verify in WP0 that compatibility fog works on this machine; otherwise a cheap depth-darken in the surface shader).
- Beams, spot pools, haze, LED wall, floor tiles, disco ball: additive unshaded quads or animated-texture surfaces in 3D, driven by the
  same song-time functions `StoryFx` uses now (port the maths, drop the 2D drawing).
- Crowd: the existing 2D `StoryCrowd` draws into a `CanvasLayer` *inside the same low-res SubViewport*, so dancers pixelate like the
  world. Each actor has a 3D home (sector + x,z); a pure-GDScript pinhole projector (`StoryProjector`, testable headless) gives its
  screen position and scale from the camera pose, and the crowd is sorted by distance. Occluders the camera passes through (door
  frames, pillars, the booth desk) are drawn in the overlay in front of the crowd when nearer than it. Dancers never stand inside walls
  (map validation), so wall clipping is not needed. Stretch: bake sprite sheets and move dancers to `Sprite3D` (section 10).
- Post-process on the SubViewport output: queasy wobble (sine warp, chroma split, desaturation, vignette with a slow breathing rate),
  strobe white-out, the ending fade. One shader, parameters from song time.
- `StoryStage` keeps its public surface so the director and the tests keep working: `setup`, `update(t, energy)`, `apply(action)`,
  `on_sequence`, `ending()`, `tableau()`, `is_active`, `progress`, `since`, `action_log`, `reset`. Internally it owns a `StoryWorld`,
  a `StoryPlayer` (the rail camera) and the crowd bridge. Every value is a function of song time: pause freezes, restart replays,
  frame step is irrelevant (keep the existing determinism tests green at 30, 60 and variable steps).

## 3. Map data (new, per chapter)

`content/story/maps/<chapter>.json`, validated by `StoryMap` (pure logic, no nodes), checked by tests:

```
{ "units_per_m": 1, "eye_height": 1.6,
  "textures": {"wall_brick": "textures/wall_brick.png", ...},
  "sectors": [ {"id": "floor", "polygon": [[x,z],...], "floor": 0, "ceiling": 3.2, "floor_tex": "...", "ceil_tex": "...",
                "light": 0.55, "tint": "#8060ff", "room": "main", "flags": ["dance_floor"]} ],
  "walls":   [ {"from": [x,z], "to": [x,z], "tex": "wall_brick", "sector": "floor", "portal": "stage"|null, "lower_tex": "...", "upper_tex": "..."} ],
  "things":  [ {"id": "woofer_l", "kind": "billboard", "sprite": "woofer", "at": [x,z], "y": 0.9, "size": 1.0, "anim": "pump"} ],
  "homes":   [ {"actor": "hero", "sector": "floor", "at": [x,z]} ],
  "waypoints": [ {"id": "floor_centre", "at": [x,z], "yaw": 0, "sector": "floor"}, {"id": "booth", "at": [..], "yaw": 180} ],
  "occluders": [ {"id": "stage_frame", "sprite": "passage_frame", "between": ["steps", "stage"]} ],
  "sky": {"tex": "sky_planet.png", "mode": "cylinder"} }
```

Validation rules (all tested): every sector polygon is simple and closed; every portal wall has a matching sector on the other side;
every waypoint, home and thing lies inside its sector; every chapter actor has a home; every `player_move` target in the chapter JSON
is a waypoint; the journey graph for each ending is connected from the start waypoint.

Authoring aid: `tools/story/preview_map.tscn` flies the map with WASD and mouse, prints the pose on a key press (paste into waypoints),
and renders it through the same low-res pipeline so what you see is what ships.

## 4. The player's journey

### 4.1 New director actions (chapter JSON, scheduled on bars like every other action)
- `player_move {to: <waypoint>, style: walk|stagger|run|climb|carried, bars}`: the camera moves along the sector graph (A* over
  portals, straight within a sector) and arrives facing the waypoint's yaw. Walk bobs on the beat (as the current dolly does), stagger
  adds a slow roll and off-beat stumbles, run is faster with a stronger bob, climb adds a rising eye height, carried (hospital) a gentle sway.
- `player_look {yaw | at: <waypoint or actor>, bars}`: turns the head; the player's free-look offset eases back to zero during it.
- `player_role {dancer | on_stage | dj | queasy | sick | recovered | out}`: drives the HUD role badge, the pad strip skin (dancer strip vs
  DJ deck), the crowd's attention target (who they face) and the post-process.
- `fx_queasy {amount 0..1, bars}`: the illness look; `sick_beat {bars}`: head down in the cubicle, music low-passed and quietened by the
  transport's existing stem gains (no new audio), a cistern flush at the end is optional and silent if no legal sound exists.

The camera never moves during a `player_move` that overlaps a dense note run: the director validates (warning at load) that every
move starts on an authored break or a bar where the chart has at most one note per beat, and moves last 2 to 4 bars.

### 4.2 Night One (the owner's spec, mapped onto the existing decisions)
| Bar | Existing decision | Good branch | Bad branch |
| --- | --- | --- | --- |
| 1 | opening | Start as a *dancer* at `floor_centre`, facing the stage where the resident DJ plays. Role badge DANCER. | same |
| 33 | first_impression | The promoter waves you over: `player_move steps (walk, 4 bars)`, `climb` onto the riser; role ON STAGE beside the DJ. | You hang back at the floor edge; `fx_queasy 0.3`; role QUEASY. |
| 57 | spotlight_circle | The DJ hands over the headphones: `player_move booth (walk, 2 bars)`, `player_look at floor`; role DJ. This is the current fixed DJ view, now in 3D. | `fx_queasy 0.6`, `player_move corridor (stagger, 4 bars)`; the toilet sign ahead. |
| 73 | big_drop | The whole floor jumps as seen from the booth. | `player_move cubicle (run, 2 bars)`, `sick_beat 4 bars`, `player_role sick`, then `recovered` and `player_move floor_edge (walk)` for the win-back beat. |
| 105 | final_push | Legendary Set: ends in the booth, crowd in a wave. | Lost the Floor: lights up, you are at the door or back in the toilets; Good Night (middle): you end on the stage edge or the floor. |
| 115 | win_back | Recovered after a bad branch: `player_move steps` or `booth` if energy allows. | Stay where you are. |

A player who recovers after the toilets can still climb at a later decision: the journey is authored per decision outcome, not fixed
by the first branch, so the existing win-back behaviour is preserved.

### 4.3 Chapters 2 to 5 (same pattern, each with a good "up" and a bad "away")
- The Mothership: the deck among aliens > good: up the ramp to the holo-dais, the bridge at the peak > bad: a dim medical bay where the
  greys examine you under a probe light (queasy = the light), beamed home from the airlock.
- The Underworld: the arena floor among demons > good: the throne steps, then the pit stage out on the lava > bad: dragged toward the
  furnace chains, the pit edge, devoured.
- The Hospital: your bed (carried in a chair) > good: the day room, the cafeteria party, the garden at the peak > bad: back to bed,
  curtains drawn, the quiet corridor.
- The Ward: the day room > good: the corridor to the courtyard, the talent-show stage > bad: the corridor the other way, the quiet room,
  lights out.

### 4.4 Free movement (stretch, default off)
Breaks of 8 bars with no notes in the chart could let the player walk with WASD, arrows or a touch stick to the next waypoint; if they
have not arrived by the bar, the rail takes over. Only after WP6 is accepted, and only if the owner wants it: it is a design change to
the music charts (breaks must exist) and to the input mapping on phones.

### 4.5 Free look (always on)
Mouse drag or touch drag on the stage area yaws the head within plus or minus 60 degrees of the rail's facing and eases back; the pad
strip ignores it. Keyboard Q/E also yaw. Not needed for play, but it is what makes "the player moves around" feel true.

## 5. Variety per chapter (what makes the levels read as different places)

Each chapter map gets, and the screenshots must show: its own wall/floor/ceiling texture set and sky; 4 to 6 rooms with different
heights and footprints (long corridor, tall hall, low cubicles, open courtyard); an animated surface (the LED wall, lava, the
reactor core, the hospital window daylight, the courtyard string lights); a signature 3D set piece (the riser and booth, the holo-dais,
the pit platform over lava, the garden path, the talent-show stage); its own light rig behaviour (sweep beams, hologram rings, fire
flicker, soft daylight with dust, warm bulbs); and the existing props as billboards (woofers, braziers, easels, drip stands).
Textures come from the chapter's existing SVG art so palettes stay what they are.

## 6. HUD and input
- The pad strip (`StoryDeck`) is unchanged in semantics; it gains a *dancer* skin (a rail of four floor tiles) used while the role is
  DANCER / QUEASY / SICK, and the existing DJ deck skin when ON STAGE / DJ. Switching is a song-time cross-fade.
- Role badge next to the act title (DANCER, ON STAGE, DJ, FEELING ROUGH, OUT COLD); the result screen names the journey taken.
- Settings: Camera motion (full / reduced / none), Internal resolution (360p / 270p / 180p). Reduced effects implies reduced motion.

## 7. Work packages for the build session (Sonnet), in order; each ends with green tests and a commit

- WP0 Spike (half a day): `story_play` shows a low-res SubViewport 3D box room with one textured wall, the pads below still playable,
  frame time printed with `RW_STORY_PROFILE_FROM`. Confirms compatibility-renderer fog, nearest upscaling and the frame budget. Commit the
  numbers in the handover.
- WP1 `StoryMap` + validation + tests (pure logic), the Night One map authored (entrance, floor, steps, riser, booth, bar, corridor,
  toilets with two cubicles). `build_assets.py` gains the texture tiles output and `check_assets.py` checks them.
- WP2 `StoryWorld` builder (sectors, walls, portals, things, sky, per-sector light as vertex colour), the preview scene.
- WP3 `StoryPlayer`: the rail camera, pathing over portals, move styles, free look, song-time determinism; tests at 30/60/variable steps.
- WP4 Crowd bridge: homes in 3D, `StoryProjector`, overlay sorting and occluders; the existing crowd directives (`bring_in`, `circle_form`,
  `hero_to`, `walk_to`...) translated from design-space targets to map coordinates (the chapter JSON gains map targets; the old
  design-space numbers are dropped from the story files).
- WP5 FX port: beams, pools, haze, LED, tiles, strobe, flicker, ball, queasy post-process, ending fades; `StoryFx` 2D code deleted
  once the tests move over.
- WP6 Night One journey authored (section 4.2), dancer strip skin, role badge, settings; screenshots for each journey node.
- WP7 Chapters 2 to 5: maps, journeys, textures, set pieces (section 4.3 and 5).
- WP8 Playtesting (section 8), docs: update `STORY_CAMPAIGN_HANDOVER.md`, `STORY_ART.md`, README; regenerate `docs/shots/story`.

Rules: keep the main campaign untouched; no new audio; no downloaded assets; every visual is a function of song time; headless tests
must not need a renderer (3D nodes may exist, but logic under test lives in `StoryMap`, `StoryPlayer`, `StoryProjector`); commit per WP
with the WP name in the message.

## 8. Playtesting (robust, automated, repeated every WP)

8.1 Per-chapter policy matrix (headless, extends `tests/test_story_chapters.gd` and `tools/story/tune.gd`): for each of the five
chapters, policies perfect, accuracy 0.9 / 0.8 / 0.7 / 0.5, beginner, sloppy, none, seeds 1 to 3. Assert: the ending is in the chapter's
set; perfect gives the top ending and none the bottom ending; the *journey* (the ordered list of waypoints reached, from
`stage.action_log`) matches the authored expectation for top, middle and bottom endings; the camera is inside a valid sector at every
bar; no `player_move` overlaps a dense note run.

8.2 Campaign walk-through (real Godot, windowed, virtual clock): new `tools/story/walk_campaign.sh`. A new env switch
`RW_STORY_AUTO_ADVANCE=1` makes the result and interlude screens advance by themselves (results after 1 s, interludes at their end),
and `RW_STORY_TRACE=<file>` appends one line per scene (chapter, policy, ending, route, save unlocks). The script runs the real scene
chain `story_play > story_result > story_interlude > story_play ...` from a fresh `user://` (the script sets `--user-data-dir` style
isolation, never the owner's real save) for these paths, and fails on any ERROR/SCRIPT line or a wrong chain:
- perfect: Night One (legendary_set) > abduction > Mothership (galactic_headliner) > awakening > Hospital (family_celebration) > To be continued.
- none: Night One (lost_the_floor) > descent > Underworld (devoured) > sectioned > Ward (lights_out) > To be continued.
- sloppy seed 2: Night One (good_night) > Mothership, then whatever ending it reaches, through to the end.
- mixed: perfect Night One then none in the Mothership (beamed_home) > sectioned > Ward; none Night One then perfect Underworld
  (resident_dj) > awakening > Hospital.
After each run the saves show the right unlocks (`StoryProgress`), and the Story Campaign menu lists exactly the unlocked chapters.

8.3 Screenshots: `capture.sh` gains one shot per journey node per chapter (dancer view, steps, stage, booth, corridor, cubicle; the
chapter equivalents), each ending tableau, reduced motion and high contrast, 4:3 and 20:9. Reviewed by eye in WP6/WP7 and again by Opus.

8.4 Performance: `RW_STORY_PROFILE_FROM` over the busiest 16 bars of each chapter at 270p; budget 12 ms average and 20 ms 95th
percentile on this laptop's Intel HD 520; record the numbers in the handover.

8.5 Manual checklist for the owner (in the handover): notes stay readable during every camera move; no move during a dense run; the
sick beat is discreet; free look never blocks a pad; a full run on the phone export if available.

## 9. Visual polish brief (Opus session)

After WP8 is merged, in this order, each a reviewed commit with before/after screenshots in `docs/shots/story`:
9.1 Night One: texture tiles with proper tiling seams, trim textures at floor and ceiling, the riser and booth as a set piece, bar
bottles glint, the toilet corridor's cold light and tiles, a lit EXIT sign.
9.2 Light: beat-synced sector light pulses with colour from the palette, beam cones with soft edges, spot pools that stay on the hero,
the strobe only on authored bars, a proper ending fade.
9.3 Crowd in the world: shadows as flat blobs under each dancer, depth-fog on far dancers, the front row larger and partly cropped
Doom-style, occluders tested from every waypoint.
9.4 Chapters 2 to 5: each room's signature set piece polished; skies; animated surfaces; props placed with intent (not scattered).
9.5 Motion: the walk bob curve, the stagger, the climb, free-look easing; reduced-motion checked.
9.6 Optional: restage the four cutscenes in the 3D world (the UFO over the club roof, the floor cracking under the player, the ward
door opening ahead of the camera); keep them silent and deterministic.
Rules: no change to logic, maps or tests except to add checks; keep the frame budget (8.4); regenerate screenshots.

## 10. Stretch items (only after everything above is accepted)
- Baked Doom sprite sheets (frames x 3 facings per state) and `Sprite3D` dancers with real occlusion.
- Free-walk breaks (4.4). Touch stick on phones.
- A sixth chapter location authored purely in the map format to prove the pipeline (no new music; reuse a pack).

## 11. Risks and the calls already made
- Motion and reading notes: moves only on authored light bars, small bob, a motion setting. Decided.
- Compatibility renderer: fog and SubViewport cost on phones verified in WP0 before anything else is built. Decided.
- The sick scene: discreet (head down, muffled music, no visible vomit). Default; the owner can ask for more or less.
- Free movement: off in the build; rail plus free look. Default; the owner can switch it on as a stretch.
- Headless determinism with 3D: all logic in pure classes; rendering nodes only consume them. Decided.
- Tests: the existing story suite (~1,600 checks) must stay green or be ported, never deleted without a replacement.

## 12. Hand-off prompts

### 12.1 For the build session (switch with `/model sonnet`, then paste)

```
You are continuing Rhythm Warfare (Godot 4.5.1, this folder, branch feature/story-campaign-night-one, clean). Create branch
feature/story-25d from it. Execute docs/STORY_25D_PLAN.md: the 2.5D Doom-style rebuild of the Story Campaign, the player's journey
(dancer > stage > DJ, or dancer > toilets), chapter variety, and the campaign-wide playtesting. Read first: docs/STORY_25D_PLAN.md,
docs/STORY_CAMPAIGN_HANDOVER.md, docs/STORY_ART.md, src/story/story_stage.gd, src/story/story_view.gd, src/story/story_crowd.gd,
src/story/story_director.gd, content/story/night_one.json, tests/test_story_*.gd, tools/story/capture.sh. Work through WP0 to WP8 in
order; after each WP run `GODOT=~/godot/Godot_v4.5.1-stable_linux.x86_64 bash tools/test.sh` (the Python mido failure is known and
unrelated) and commit with the WP name. Keep every rule in sections 2, 7 and 8. Do not re-ask the calls in section 11. Finish by
updating docs/STORY_CAMPAIGN_HANDOVER.md with what was built, the frame-time numbers, the walk-through results and what is left,
and regenerate docs/shots/story.
```

### 12.2 For the polish session (switch with `/model opus`, then paste)

```
You are polishing Rhythm Warfare's Story Campaign (Godot 4.5.1, branch feature/story-25d). The 2.5D rebuild is done; read
docs/STORY_25D_PLAN.md section 9 (your brief), the handover docs/STORY_CAMPAIGN_HANDOVER.md, and look at every image in
docs/shots/story before changing anything. Work 9.1 to 9.5 in order (9.6 only if time), one reviewed commit each with before/after
screenshots via tools/story/capture.sh. Do not change logic, maps or tests except to add checks; keep the frame budget in 8.4; run
the full test suite before each commit.
```

## 13. Progress log

### 13.1 WP0 to WP3 (Sonnet build session, chunk 1), branch `feature/story-25d`

Built and committed (one commit per WP, WP0 and WP2 share one because the spike became the real renderer):
- WP1 `src/story/world/story_map.gd` (`StoryMap`, pure logic), `content/story/maps/night_one.json`, `tests/test_story_map.gd`; `tools/story/art/tiles.py` (16 deterministic
  64/128 px tiles per chapter, manifest section `textures` {id: {file, size, metres}}), `build_assets.py` (`... build_assets.py tiles` rebuilds only them), `check_assets.py`.
- WP0 + WP2 `src/story/world/story_lowres.gd` (SubViewport + nearest TextureRect + Camera3D), `story_world.gd` (`StoryWorld`), `tools/story/preview_map.tscn/.gd`, `tests/test_story_world.gd`.
- WP3 `story_player.gd` (`StoryPlayer`), `story_free_look.gd` (`StoryFreeLook`), `story_projector.gd` (`StoryProjector`), the five director actions in `StoryData.ACTIONS` and
  `StoryStage.apply`, the director's dense-run warning (`StoryDirector.warnings`, surfaced in `StoryRun.warnings`), `story_play.gd` wiring, `tests/test_story_player.gd`, `tests/test_story_journey.gd`.

Where things are and how they behave (read before WP4):
- A chapter uses the 3D world when `content/story/maps/<run.data.id>.json` exists and validates; `RW_STORY_2D=1` forces the old painted room. Chapters 2 to 5 have no map yet and
  still run the 2D `StoryStage` untouched (WP7 adds their maps). Night One is 3D now; the journey actions are accepted by every stage and ignored without a map.
- `StoryStage.attach_world(map, with_nodes := true)` creates `player` (`StoryPlayer`, always) and, with nodes, `lowres` + `world` as the first child (behind the 2D crowd), sets
  `world_active`, makes the stage Control take the head-turn drag (mouse drag or touch drag on the stage area; Q/E keys) and hides every 2D room layer and `StoryFx` layer of the
  views (far, near, top, fx layers). INTERIM until WP4: the 2D `StoryCrowd` is still drawn over the 3D world at its old design-space positions, NOT through `StoryProjector`, so the
  dancers do not stand in the room geometry and do not follow the camera. `stage.journey()` lists the `player_move` targets in order (for the WP8 matrix).
- Map conventions: x right, z toward the back of the club, y up (metres); yaw 0 looks toward -z, positive yaw turns left, forward = (-sin yaw, -cos yaw); waypoint yaw is in degrees.
  Sectors must be convex (rail pathing relies on it; split a hall into sectors) and may not overlap; a portal is declared once on either sector and mirrored for the other side;
  edges no wall covers get a default wall with the sector's `wall_tex`; a thing's `y` is its centre above the sector floor, `size` its height in metres; `start` names the first waypoint.
  Homes and waypoints keep 0.25 m / 0.3 m from the walls (validated). Map `textures` name files under `assets/story/<art>/`; their metres per repeat come from the art manifest.
- Night One map: entrance (z 9..13) > floor (x -7..7, z -3..9, ceiling 3.6) > steps (0.3) > riser (0.9) > booth (1.1); bar on the right (x 7..12); corridor on the left (x -13..-7)
  > toilets > cubicle_a, cubicle_b. Waypoints: floor_centre (start), floor_edge, steps, stage, booth, corridor, cubicle, cubicle_a, door. Homes: core, early and late actors on the floor
  (the old design-space x, depth mapped to metres), gatherers (g01..g08) in the entrance, peak (p01..p04) in the bar. WP4 may move them; keep them valid.
- `StoryPlayer.pose_at(t)` returns {cam: Vector3, yaw, roll, pos, sector, ground, moving, style, u, role, queasy, sick}; `role_at`, `queasy_at`, `sick_at` are the values for the HUD badge,
  the post-process (WP5) and the head-down crouch. Events may arrive out of order (decisions fire late); the chain is rebuilt on each one. `player_look` with `at` takes a waypoint or an actor
  id (a home). `reduced` drops bob, roll and sway only. The role badge, the queasy shader and sick music are still stubs (the values exist, nothing draws them): WP5/WP6.
- The director warns at load (never errors) when a `player_move` lasts outside 2 to 4 bars, starts on a dense bar (more notes than beats in that bar), or runs mostly over dense bars.
  Night One at the default loadout has at most 4 notes a bar, so nothing is dense there; no player_move is authored in `night_one.json` yet (WP6).
- `StoryWorld.light_of(sector, t, ctx)` is the one light function (ctx: bpm, palette, energy, flicker, strobe). Dance floor and stage take the palette; others keep their own tint.

Measured (this laptop, Intel HD 520, Mesa, windowed 1280x720, `--disable-vsync`, `RW_STORY_VIRTUAL=1 RW_STORY_PROFILE_FROM=105 RW_STORY_UNTIL_BAR=113`, perfect autoplay, 663 frames, bars 105 to 113 of Night One):

| Path | mean ms | p95 ms | max ms |
| --- | --- | --- | --- |
| old 2D room (`RW_STORY_2D=1`) | 16.40 | 17.76 | 74.51 (first frame) |
| 3D world, 270 lines | 14.23 | 15.28 | 72.22 |
| 3D world, 360 lines | 14.17 | 14.81 | 75.00 |
| 3D world, 180 lines | 14.07 | 14.76 | 70.83 |
| 3D world alone (preview scene, 270 lines) | 2.42 | 2.78 | 3.17 |

The frame time does not depend on the internal resolution: the cost is the CPU (2D crowd, deck, notes). The world itself is about 2.4 ms, so the 3D path is cheaper than the old 2D room
but the whole scene is still above the plan's 12 ms average (8.4); the crowd drawing is what is left to trim (WP4 or WP5, e.g. fewer redraws, no per-actor shadows). 95th percentile is within 20 ms.
Fog works on `gl_compatibility` (Environment fog on unshaded StandardMaterial3D; verified by screenshot difference with `RW_STORY_FOG=0`), so no depth-darken shader is needed.

Deviations from the plan:
- Texture tiles are drawn with Pillow in the chapter's palette and motifs (`tiles.py`), not cropped from the SVGs: the toolchain has no SVG rasteriser (ImageMagick `convert` can render them
  but is not a build dependency and would make the output machine-dependent). The tile art can still be improved by hand-editing `tiles.py`.
- Sector light is applied as the `albedo_color` of each sector's own materials (one material per sector and texture, written every frame) with a baked flat shade in the vertex colour, instead of rewriting
  vertex colours: the same visual result, no mesh updates. Things are billboard quads (fixed-Y, alpha-scissor, linear filtered because the SVG sprites are 2x design size); wall and floor tiles are nearest.
- Internal resolution: one internal pixel is `window height / lines` screen pixels (270 lines gives 480 wide on a 16:9 window, a 480 x about 170 viewport for the stage strip), so the look is
  the same at every window shape. `RW_STORY_LINES=360|270|180` sets it; the Settings screen option is WP6.
- Surfaces are double sided (no culling) so wall winding can never hide a face; cost is negligible at 162 triangles for the whole Night One.
- `StoryProjector.FOV_V` is 52 degrees vertical (with the strip being about 2.8:1 this is about 110 degrees horizontal); the test compares it to a real Camera3D.
- A stage-level journey test lives in `tests/test_story_journey.gd`, the pure world tests in `tests/test_story_world.gd`.

For the next agent (WP4 to WP6): the crowd bridge should draw `StoryCrowd` inside `lowres.sub` (a CanvasLayer in the SubViewport) using `StoryProjector.project_ground(home, pose.ground ...)`
with `lowres.projector_pose(pose, free_look.offset)` and a size of `lowres.sub.size`; remember actor homes are in `map.homes` (sector + x,z) and that a home's ground height is its sector floor
(the booth is 1.1 above the floor). The stage `_fit` still scales the 2D design space to the strip; that goes away with the bridge. `tools/story/capture.sh` shots and `docs/shots/story` were NOT
regenerated in this chunk (the 2D crowd over a 3D room is interim), do that after WP4. The Python `mido` test failure is the known unrelated one.

Tests at the end of this chunk: Godot suite 15,308 checks, 0 failures (13,274 before the build; new files `test_story_map`, `test_story_player`, `test_story_world`, `test_story_journey`);
the story subset passes (`--filter story`). The Python content tests still fail on the missing `mido` module (known, unrelated). `src/scenes/story_interlude.gd` had a pre-existing
"inferred from Variant" parse error that `test_scenes` printed (it did not fail a check); fixed with a type annotation. Asset check: `python3 tools/story/check_assets.py --determinism` is OK.

### 13.2 WP4 to WP6 (Sonnet build session, chunk 2), branch `feature/story-25d`

Commits: "tiles from the chapter art", "WP4 crowd bridge", "WP5 FX port", "WP6 Night One journey" (see `git log`).

Tiles (correction): `tools/story/bake_tiles.gd` rasterises the chapter's SVGs in headless Godot (`Image.load_svg_from_string`), crops regions (back-wall panelling, plinth, LED screen, bottle shelf, entrance doors, woofer
SVG, four cells of the LED floor, `riser.svg`) and resamples to 64 or 128 px. `tiles.py` now only holds the metres per tile and runs the bake (needs `$GODOT` or `~/godot/Godot_v4.5.1-stable_linux.x86_64`);
`build_assets.py tiles` rebuilds only them; `check_assets.py --determinism` passes. The toilet tiles have no art and are palette fills; the cubicle door is the entrance door turned teal. Documented in `docs/STORY_ART.md`.

WP4 crowd bridge (`StoryCrowd` world mode, `StoryCrowdProp`, `StoryMap.visible_sectors`, `StoryStage`):
- A chapter with a map file now gets its map in `StoryStage.setup` (headless too): `stage.map`, `stage.player` and the crowd's world mode exist without a renderer; `attach_world(map, true)` (story_play does it) adds the
  `lowres` viewport, the `StoryWorld`, the `StoryWorldFx` and moves the crowd into a `CanvasLayer` inside `lowres.sub` (the painted room `_root` is hidden). `RW_STORY_2D` is gone (Night One has no design-space numbers).
- In world mode `actors[id]["pos"]` and `["home"]` are ground coordinates (x, z metres); `a["sec"]` is the sector (re-resolved while walking, ground height = sector floor). Walks follow `StoryMap.route` (through the doors, never through a
  wall). Each frame the stage hands the crowd the pose (`set_camera`), the crowd projects every dancer (`_place_world`, inlined pinhole), culls by sector visibility (`visible_sectors`, up to two portals deep, cached while the camera is still),
  fades dancers closer than 1.3 m to the eye, sorts dancers, silhouettes and occluders together by distance (`_sort_world`, integer keys) and draws flat shadow blobs. Culled dancers keep their mood state but skip the pose and the draw.
  Dancers pose at up to 45 Hz of song time (`POSE_RATE`), position and scale every frame.
- Map additions (all validated): `spots` (door with `slots`, circle with `radii` and `open`, riser, side_l, side_r), `silhouettes` (rear row), homes may carry `side`, occluders are `{sprite (a map texture), at, width, height}` drawn over the
  crowd (Night One: two speaker stacks on the floor). The design-space numbers (x, depth, side_x, side_depth) are removed from `content/story/night_one.json`; chapters 2 to 5 keep theirs and the untouched 2D path.
  Gatherer and peak homes moved from the entrance and the bar onto the floor (the old design-space mapping), enter via the door and side spots.
- Crowd frame cost (this laptop, same profile as 13.1, bars 105 to 113, 270 lines, perfect autoplay, 663 frames): before 13.7 to 14.2 ms mean (p95 14.5 to 15.3); after 12.0 ms mean, p95 12.5 ms. What was cut: the per-dancer
  `_draw` no longer allocates a dictionary and string keys per frame (joint index array), dancers skip pose and redraw when the song-time step is under 1/45 s, culled dancers are not drawn, one integer sort instead of a lambda sort,
  inlined projection and cached portal visibility, scanlines in one call, the painted 2D layers and `redraw_fx` are skipped in world mode. Remaining cost split (measured by hiding parts): pads + notes + HUD about 6 ms
  (pad style boxes with AA 0.75 ms, deck 1.1 ms, notes 2 ms), crowd about 3.3 ms, world 2.4 ms. The next 2 ms would come from caching the static deck layer and the pad boxes.

WP5 FX port (`StoryLight` pure functions, `StoryWorldFx` nodes, `story_post.gdshader`, `StoryLowRes.apply_post`):
- `StoryLight` holds the song-time maths (beam strength and angle, strobe, bloom, mood dim, ending fade, haze, floor tiles, spots, LED value, confetti, post-process state); `StoryWorldFx` draws them in 3D as unshaded additive quads: crossed-plane
  beams from the six map fixtures, spot pools and cones, two haze bands, the LED floor as one nearest-filtered 14 x 12 texture over the floor (refreshes at 20 Hz of song time), ripples and the circle ring, disco-ball dots, woofer glow
  and a MultiMesh of confetti; the LED wall is a 32 x 32 texture swapped into the `wall_led` material (12 Hz of song time, ending words in a 3 x 5 pixel font). The strobe is a 0.3 s white flash on `bass_reveal`/`burst` only, never in reduced effects.
- Post-process on the low-res output (`story_post.gdshader`): sine warp, chroma split, desaturation and a breathing vignette from `player.queasy_at`, plus mood dim, ending fade (lost night sinks to 0.55, good 0.12, legendary none), strobe and
  bloom. Reduced effects zeroes the queasy part (no warp, split, desaturation or breathing) and the strobe.
- Sick beat audio: `StemTransport.set_duck(amount)` (default 0, so the military campaign is untouched) quietens the mix and drops the non-low stems (kick, bass, drums stay at 0.45) through the existing per-stem gains; story_play feeds it `player.sick_at`.
- Deleted from `StoryFx`: the LED floor tile code (`led_tiles` anchor, Night One only). Still needed by chapters 2 to 5 until WP7 and therefore kept: everything else in `StoryFx` (beams, spots, haze, LED screen, woofers, ball, door, pieces,
  confetti, riser column) and the whole 2D `StoryCrowd` design-space path, `StoryView` layers, the camera moves (`move_to`) and `StoryCameraOverlay`.

WP6 Night One journey:
- `content/story/night_one.json`: decision outcomes carry journey actions (dicts with an optional `after_bars` offset the director adds to the decision time), `endings[x].journey` stages the tableau (legendary: booth and DJ; good night: the steps;
  lost: the door and OUT COLD), bar 1 sets the dancer role. Places: perfect `steps, stage, booth, booth`; none and sloppy seed 2 `floor_edge, corridor, cubicle, floor_edge` then `door` (lost) or `steps` (good night).
  Deviations: the run to the cubicle lasts 4 bars (the plan said 2; from the booth it is 28 m), `final_push` good has no move (the ending stages the booth), `player_look at floor_centre` stands for "look at the floor".
- `StoryJourney` (pure) turns the director log into places, roles and the result line ("Dancer > On stage > DJ", in `StoryRun.summary()["journey"]`, shown on the result screen). Role badge chip in `StoryHud` (DANCER, ON STAGE, DJ, FEELING ROUGH, OUT COLD).
  Pad strip: `StoryDeck` draws the dancer's floor-tile rail (LED floor cells under each pad) and the DJ deck, cross-faded over 1.5 s of song time by `StoryPlayer.deck_mix_at`.
- Settings: Story camera motion (full / reduced / none: none cuts to the end of a move half way through) and Story internal resolution (360p / 270p / 180p, `Session.story_lines`; `RW_STORY_LINES` still overrides); reduced effects imply at least reduced motion
  (`Session.effective_story_motion`). `RW_STORY_MOTION=0..2` for screenshots.
- Tests: `test_story_crowd_world`, `test_story_fx_world`, `test_story_night_one_journey` (journey under perfect, none, sloppy seed 2 at 30, 60 and variable steps; camera inside a room at every bar; no dense-run warning on load).

Screenshots (docs/shots/story, regenerated for Night One: 01 to 27 and the new `j01` to `j18` journey shots, JPEG; chapters 2 to 5 untouched): looked at by eye. Fixed on the way: the camera on the stage faced the back wall (waypoint `stage` now yaw 180, facing
the floor), the DJ in the booth saw no crowd (the visible-sector walk stopped two portals out, the floor is three away: now four), the good night ended facing the LED wall (new waypoint `stage_edge`, facing the floor) and the lost night faced the street door
(`door` now faces the club), the ending words on the LED wall were cut by the wall segments (the wall texture is 48 x 32 and the words sit in its first 32 columns), dancers passing the eye filled the screen (fade now between 1.0 and 1.8 m). What is still plain
and is the polish session's to improve: the corridor and the cubicles are dark and bare (no toilet sign, no cistern or bowl sprite, the sick beat is a head-down view of a tiled wall), the stage woofers frame the booth view heavily, the entrance has no door sprite,
the near dancers' faces are large when they pass, the LED pattern is chunky at 48 x 32.

Frame time, final (same profile as above; this window had another Godot process using about 70 percent of a core, so absolute numbers run about 1 ms high; the WP4 commit measured 12.0 ms in a quiet window and 13.0 in this one): WP4 13.0, WP5 13.1 to 13.9,
final 14.4 mean, p95 15.0 to 16.7 at 270 lines (180 and 360 lines are the same: the cost is CPU). The final is higher than WP4 mainly because the authored journey puts the camera in the booth at bars 105 to 113, which sees the whole floor crowd (about 25 dancers on screen instead
of about 13); the FX update costs about 0.7 ms, the post-process 0.2 ms (and it is off while nothing needs it). So the plan's 12 ms average is not met at the busiest booth view on this laptop (about 13.5 in a quiet window); the next 1.5 ms would come from caching the static deck layer
and the pad boxes (about 1.8 ms together) or baking the dancers to sprite sheets (the plan's stretch). 95th percentile stays under 20 ms.

For the next agent (WP7 to WP8):
- A new chapter needs `content/story/maps/<chapter>.json` (map conventions in 13.1 and above), its actors without design-space x and depth (the map's homes place them), `spots` (door with `slots`, circle, riser, side_l, side_r), `silhouettes`, waypoints with a
  yaw that faces what the player should see, and textures baked by `bake_tiles.gd` (add a `_<chapter>()` recipe dictionary and the `textures` ids in `tiles.py`). Chapter JSON journeys use the same dict actions with `after_bars`; endings take `journey`.
- The 2D `StoryCrowd` design-space path stays for chapters without a map; `StoryStage.attach_world` is what turns on world mode, and `RW_STORY_2D` no longer exists. `StoryLight` and `StoryWorldFx` look for `fixture` and `woofer` things and the `dance_floor` flag on a sector, and an
  LED wall by the map texture name `wall_led`; name the equivalents the same way or extend `StoryWorldFx.build`.
- Sectors must be convex, and the crowd walks `StoryMap.route`; keep homes at least a metre from every waypoint (tested) and spots inside their sectors (validated).
- `tools/test.sh` takes a few minutes; a mid-run edit of a content file can produce failures that do not reproduce (it happened once): rerun before debugging.
- The capture script is slow (about two minutes a shot to a late bar); four `capture.sh` runs in parallel with different `RW_SHOTS` filters work on four cores. Do not use `pkill -f capture.sh` from a command that contains that string.

### 13.3 WP7 and WP8 (Sonnet build session, chunk 3), branch `feature/story-25d`

Commits: "WP7 mothership" (the multi-room engine and the first chapter), "WP7 prep" (Night One toilet sign, trace and walk tooling, matrix), the three chapter commits (underworld, hospital, mental_hospital; authored by forks of
this session in worktrees and cherry-picked), "WP7 cleanup" (2D code deleted), "WP8 playtesting" (this section, screenshots, docs).

Engine changes for chapters with several rooms (all in `src/story/`):
- One `StoryCrowd` per room (`stage.crowds`, actors' `view` = room id). `stage.current_view` is the room the player last walked into (`player_move` to a waypoint in a room that has a crowd; the medical bay, the quiet corridor and the cage have none and
  leave it where it was). The old `move_to` / `camera_look` / `camera_push` actions are gone from `StoryData.ACTIONS`; the room's palette comes from the map (`rooms`).
- `StoryMap`: `rooms`, `fog`, `animated`, `room_of`, `room_spot` (`"<room>.<name>"` then the plain name), `crowd_rooms(chapter_raw)`; `StoryCrowd.attach_map` takes its door, circle, riser and side spots from its own room.
- `StoryWorld`: things with `piece` (set pieces of the art) and `blend`, animated surfaces (`StoryLight.surface_anim`: scroll, pulse, flicker, swap; `bright` lets lava and reactor glass ignore their sector's light), per-map fog, `MIN_GAIN` 0.5 so no sector reads black, one light colour per
  sector per frame shared with the things in it. `StoryWorldFx` follows the crowd room (its dance floor sector gets the LED tiles, haze, rings, confetti).
- `player_look {by}`: a glance (sin squared envelope over its bars) added to the rail's yaw in `StoryPlayer.pose_at`; it never interrupts a move. Every eight-bar block of every chapter has two glances (art direction 2.B, first pass: glances only; walks within rooms are WP9).
- Scripted chains: `StoryTrace`, `RW_STORY_AUTO_ADVANCE`, `RW_STORY_TRACE`, `RW_STORY_POLICIES`, `RW_STORY_RECORD`; `tools/story/walk_campaign.sh`.
- Interludes play in the world: the stage builds the club in its ending tableau (the ending applied at t0 = -10 so the camera is already there), the cutscene art draws over it scaled from its 1280 x 720 design space.
- Deleted: `StoryView`, `StoryFx`, `StoryFxLayer`, `StoryCameraOverlay`, the dolly, the 2D crowd placement and drawing, the riser lift, `StoryAssets` anchors and floor rows, the 2D preview scenes and review scripts. Manifests lost `stage.anchors`, each view's layers, anchors and palette hint.
  Tests ported: `test_story_camera` rewritten (rooms, crowds, palettes, glances, determinism), chapters (crowd-room route by skill), polish, journey, stage; nothing deleted without a replacement.

Deviations and calls:
- The journey is driven by decisions only (plus the Mothership's bar-17 walk to the gallery): the old unconditional room tour could not stay, because a bad-branch player must not be dragged back to the show. So a room's crowd is where the player is.
- Fixed Night One: the toilet corridor has a lit sign (`thing_sign_wc`, baked from an inline SVG, plus a flickering glow), fog 0.024.
- Underworld and Ward bad branches end in the cage and the quiet room: no walk back (win_back is four bars after the sick beat).
- Performance is above the plan's budget in every chapter (handover Numbers).
- Pieces are billboards with scissor or blend; soft glows are plain at the moment.

Screenshots (docs/shots/story, 104 JPEGs): Night One 01 to 27 and j01 to j18 regenerated; `m_*` (Mothership 12), `u_*` (Underworld 10), `h_*` (Hospital 9), `w_*` (Ward 9): one per journey node and ending tableau; interludes and ui. Looked at by eye. Fixed on the way:
the Underworld `pit_edge` faced a wall (now yaw -45 over the deck), the shot bars of the bad Hospital branch. What is still plain: the Mothership sky planet is a blocky pink silhouette through the glass roof; the Hospital and Ward day rooms are lit purple by the
dance-floor palette rather than night blue and institutional green; the Ward quiet room (the last view of Lights Out) and the Mothership medical bay are bare tiled boxes; near dancers (a garden edge, the Mothership deck start) fill the screen; the Underworld lava reads as orange brick; the pit skyline is only the sky strip.

For the polish and WP9 agents:
- Rooms are data: `content/story/maps/<chapter>.json`. WP9 rebuilds them to art-direction 2.A; keep one `dance_floor` sector per crowd room, eight door slots per crowd room, homes 1 m from every waypoint, sectors convex, and run `tests/test_story_map.gd` and `test_story_matrix.gd`.
- The generator scripts used for WP7 maps lived in the build session's scratch folder and are not in the repo: the JSON is the source.
- A thing's `y` is relative to its sector's floor; sectors below the floor (the Mothership well at -2.5, the arena at -1.2) work, the crowd stands on its sector's floor.
- `tools/story/capture.sh` shot names carry the chapter prefix (`m_`, `u_`, `h_`, `w_`) and the bar of the journey node; if a journey changes, move the bars (use `tune.gd` for the places and `StoryDirector.bar_time` maths: decision bar plus `after_bars`).

Manual checklist for the owner (things only a person can judge): play each chapter once well and once badly and watch the journey (the badge: DANCER, ON STAGE, DJ, FEELING ROUGH, OUT COLD); notes stay readable during every move and glance (glances happen on any bar, moves only on light bars);
the sick beat is discreet; free look (drag, Q/E) never blocks a pad; the interludes still read over the 3D club (UFO over the floor, the crack, the eyelids, the ward door); the chapter tones (night ward, grim green) are what you want before the polish; the Settings screen's camera
motion and internal resolution options; a phone export if one is available; whether the Underworld and Ward bad branches should have a walk back; whether the frame times (14 to 19 ms on the Intel HD 520) are acceptable.
