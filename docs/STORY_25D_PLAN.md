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
