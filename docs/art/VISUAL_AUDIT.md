# Visual audit (art stream, 6 November 2026)

The owner asked for "a big visual polish so the graphics look seamless, and none of the artwork is jarring with other images"
(lead ruling 26). This is the audit: what the game looks like today, judged by eye against `pixelexample/` and
`docs/STORY_25D_ART_DIRECTION.md`, the ranked fix list, and the work packages that carry it out in parallel. The rules the fixes
must meet are in `docs/art/STYLE_GUIDE.md`. Nothing in the game was changed by this audit.

## 1. What was captured

All shots are real Godot frames of the run on the virtual clock, perfect play, default exits, 1280 x 720 unless said
(branch `wip/art-audit`, cut from `feature/one-pc`, 6 November 2026).

| What | Count | How | Where |
| --- | --- | --- | --- |
| Every scene of the main run (36 scenes, 7 worlds) | 216 frames | `tools/art/audit_capture.sh` (new): one launch per scene, 6 frames: beat 24, beat 40, beat 54 (hotspot window), the last 0.25 s of the scene, 0.3 s and 3 s into the next scene | `world_<world>.jpg`, `joins_main.jpg` |
| Every scene of the three paths (Gospel 17, Squadron 14, Ember 15) | 276 frames | the same; the last lap of a two-lap scene | `world_gospel_*`, `world_squadron_*`, `world_ember_*`, `joins_<path>.jpg` |
| Quest entrances and the passage into each path | 18 frames | `tools/art/audit_extra.sh portals` (RW_RUN_PORTAL, flags set) | `entrances.jpg` |
| A hotspot in each state, a door walk | 8 frames | `audit_extra.sh states` (the recipes of `tools/run/capture.sh`) | `ui.jpg` |
| The passage between worlds | 14 frames | `audit_extra.sh passage`: Warehouse exit to Mothership from -2 s to +6 s; Underworld exit to Ward | `passage.jpg` |
| Main menu and Story chapters menu | 2 | `audit_extra.sh home` | `ui.jpg` |
| 20:9 phone shape (1600 x 720) | 12 (6 scenes) | `audit_extra.sh wide` | `wide_20x9.jpg` |
| The Bassment, every zone (16) | 32 | `audit_extra.sh bassment` (RW_TRIAL_DIRECT) | `bassment.jpg` |
| Every texture of every map (721 PNGs, 17 maps) | 17 sheets | `tools/art/texture_sheet.py` (new) | `textures/textures_<map>.jpg`, `textures/texture_check.txt` |

All under `docs/shots/art/audit/`; 31 single frames that the findings cite are in `docs/shots/art/audit/frames/`.

Not captured: the Bassment fight sequence (the scripted fight launch wrote no frames; the creatures are seen standing in their zones
instead, e.g. `bassment.jpg` vaults, kitchens, echo), the wizard's walk into the Bassment hatch, the Story chapters' own play
(`story_play.tscn`; the run is the game now), and the 844 x 390 phone layout (only 20:9 at 720 lines was asked for).

Windows notes: the Linux capture scripts were not used as they are (`tools/run/capture.sh` passes a `/tmp/...` path to the Windows
Godot and lets Godot write into the real `user://` folder, the shared save). `tools/art/audit_capture.sh` and `audit_extra.sh` do the same
work with `APPDATA` pointed at a temp folder, `cygpath -m` paths, and `tools/dev/godot.sh` for the one-at-a-time lock; a `python3` shim
directory on `PATH` stood in for `python3`. The captures took about two hours, most of it waiting for other worktrees' Godot runs.

## 2. Measurements

`tools/art/frame_check.py` (picture only, pad strip and HUD cut; `frame_check.txt`):

| Picture | Median luminance | Crushed (under 0.04) | Note |
| --- | --- | --- | --- |
| References (Rave, Hospital, Asylum) | 0.22, 0.17, 0.15 | 0 %, 0 %, 6 % | dark but lifted, coloured shadows |
| Warehouse, Mothership, Underworld, Ward, Ward late | 0.07 to 0.08 | 10 % to 33 % | half as bright as the references, a third of the picture black |
| Hospital, Hospital late | 0.14, 0.15 | 0 % | in range: the closest world to its reference |
| Gospel (4 worlds) | 0.35 to 0.43 | 0 % | daylight; 5x the Warehouse's median |
| Squadron base, air, city, escape | 0.39, 0.34, 0.18, 0.18 | 0 % to 4 % | sepia haze, low contrast in the air |
| Ember hollow, north, deeps, marsh, mountain | 0.14, 0.57, 0.07, 0.09, 0.07 | 0 % to 31 % | from blown white (north, 6 % over 0.85) to near black |

`tools/art/texture_sheet.py` (`textures/texture_check.txt`): **225 of 721** surface textures are under 48 texels per metre (16 to 43;
the screen shows about 123 pixels per metre at 3 m), and 18 are resampled vector crops (hundreds of colours, smooth ramps:
`underworld` wall_face, wall_throne, wall_hellmouth, wall_fortress, wall_shelf, wall_speaker, floor_orange, wall_court; `mothership`
wall_arch, wall_door, floor_lounge, thing_core, wall_speaker; `night_one` thing_wizard; `hospital` floor_wood; `deep_halls` sky_falls;
`bassment` fig_wizard_idle, fig_wizard_attack). Every map has LOWDENS textures; the worst are ceilings and skies at 16 to 21 px/m.

## 3. Findings, worst first

Shot names are files in `docs/shots/art/audit/frames/` unless a sheet is named. "Owner's taste" is yes only for a real style choice.

### F1. Two pixel sizes in one picture: near people and near walls are magnified 2x to 8x
- **Where**: every world; worst in warehouse.bar, warehouse.balcony, underworld.court, hospital.cafeteria, ward.courtyard, squadron
  base and air, every Ember box room.
- **Shots**: `warehouse_bar__a24.jpg` (the striped dancer's pixels are 6 screen px, the bottles behind are 2), `underworld_court__mid.jpg`,
  `ember__mountain_taken__a24.jpg` (ceiling texels the size of a fingernail), `underworld__a24.jpg` (brick at 32 px per texel).
- **What is wrong**: the world is 360 lines, but walls and ceilings are 16 to 48 texels per metre and people come to 1.0 m from the
  eye with a 112-pixel sheet, so the same frame mixes 1x, 3x and 8x pixels. This is the single thing that most makes the game look
  assembled from parts.
- **Made by**: tile size and metres in `tools/story/art/tiles.py` SPECS, `tools/story/bake_tiles.gd` (the five old chapters),
  `tools/story/art/tex_<chapter>.py`, `gospel_tex.py`, `tex_squadron*.py`, `tex_ember_tiles.py`, `tex_bassment.py`; people: the
  sheet sizes in `tools/story/art/people_sheets.py` and the near fade `NEAR_FADE = (1.0, 1.8)` in `src/story/story_crowd.gd`.
- **Fix**: (a) every surface redrawn or re-tiled at 96 to 160 px/m (target 128): procedural tiles get a bigger size per metre,
  baked crops are replaced by procedural ids (no `bake_tiles.gd` change is needed: a procedural id replaces a baked one).
  (b) people: never draw a person above 1.25x their sheet (cull or fade from 4.5 m for the crowd, or add a double-size level for the
  cast who come close). (c) a rule in `texture_sheet.py` that fails the build on LOWDENS.
- **Size**: large (spread over every world package). **Owner's taste**: no.

### F2. Vector cut-outs in a pixel world: rear silhouettes, banners and old 2D crops
- **Where**: mothership.reactor and .bridge (black blob silhouettes in the front row), underworld (vector demon banner, furnace face,
  throne wall), underworld.pit (magenta-rimmed silhouettes), hospital.corridor and .garden (purple and pink seated blobs), ward and
  ward_late (lilac crown shapes in front of the camera), warehouse.balcony.
- **Shots**: `mothership_reactor__a24.jpg`, `underworld_court__mid.jpg` (a 400 px cartoon demon with yellow eyes), `ward_late__win.jpg`,
  `hospital_corridor__mid.jpg`.
- **What is wrong**: the first 2D version's style (smooth SVG shapes, thick indigo outlines, flat fills) survives as the rear crowd and
  as wall art, and the rear crowd stands close enough to the camera to fill a quarter of the picture.
- **Made by**: silhouettes `sil_*` in the chapter manifests from `tools/story/art/stage.py`, `alien_chars.py`, `uw_chars.py`,
  `hp_chars.py`, `mh_chars.py` (drawn by `StoryCrowd` as `StoryCrowdProp`); set pieces from `uw_view_court.py`, `uw_view_furnace.py`,
  `mothership_views.py`, `mh_pieces.py`; baked SVG crops in `bake_tiles.gd`; positions in `content/story/maps/<chapter>.json` (`silhouettes`).
- **Fix**: rear rows become people (the quarter level of detail tinted to the fog with a rim, as the shader already does for far
  dancers) and are never closer than 8 m; pieces and crops are rasterised at their pixel size and quantised with `pixeltex.py`.
- **Size**: medium per world. **Owner's taste**: no.

### F3. The one shared door is everywhere, and its lit inside fills the screen with a beige checker
- **Where**: every world, every path, every Bassment zone (the doors are the choices). Close-ups: warehouse.booth (mid), hospital
  (win), hospital_late.exit, ward.courtyard, the passage windows.
- **Shots**: `warehouse_booth__mid.jpg` (62 % of the picture is the door's cream dither), `hospital__win.jpg`, `bassment_hatch__win.jpg`,
  `gospel__galilee__a24.jpg`, `ember__hollow__a24.jpg`; sheet `bassment.jpg`.
- **What is wrong**: `door_0..3.png` is one suburban wooden door, 48 x 96 pixels for a 2 m door (24 px/m), the same on a spaceship, in
  hell, in Galilee and in the dungeon. Open, its inside is a flat cream dither, which up close is a giant beige checkerboard.
- **Made by**: `tools/run/make_choice_art.py` -> `assets/run/choice/door_*.png`, `spill.png`; drawn by `src/run/choice_props.gd`
  and `hotspot_view.gd` (run stream).
- **Fix**: one door set per world (warehouse fire door, airlock, iron gate, ward door, night-ward double doors, Galilee house door,
  hut door, inn door, dungeon door) at 128 px/m, and an open state whose inside is a light gradient in the destination tint, not a
  flat fill. Needs a per-world lookup in `choice_props.gd` (a run-stream file: ask the lead).
- **Size**: medium (drawing) plus a small engine change. **Owner's taste**: no (the per-world look follows the style guide).

### F4. The picture is twice as dark as the references, with crushed blacks
- **Where**: Warehouse, Mothership, Underworld, Ward, Ward late, Ember deeps and mountain (median 0.07 to 0.09, 10 % to 33 % black).
- **Shots**: `mothership_gallery__mid.jpg`, `ward_dorm__mid.jpg`; table in section 2.
- **What is wrong**: the references are dark but every shadow is a colour (navy, indigo, bottle green); here a third of the
  Mothership is black, the Ward dormitory is an empty dark box, and the Warehouse's walls vanish. The bright Hospital (0.14) sits
  between worlds of 0.07, so the run pumps from murky to clear and back.
- **Made by**: the post clamp in `src/story/world/story_lowres.gd` / `story_post.gdshader` (`clamp_lo` is black), sector light
  levels and lamps in `content/story/maps/<chapter>.json`, fog colours, `src/story/world/story_light.gd`.
- **Fix**: clamp the low end to the world's fog colour (style guide section 4), raise the ambient floor so p5 is at least 0.035, and add
  at least one pool of light per room; check with `frame_check.py`.
- **Size**: medium (one shared change, then per-world light tuning). **Owner's taste**: no (the references settle it).

### F5. The camera stares into walls from a few centimetres
- **Where**: warehouse.balcony (mid, end), warehouse.chill (mid, end), mothership.gallery (mid, end), underworld (a24),
  hospital_late.quiet (a24, mid, end), hospital.cafeteria (mid), gospel jordan.baptism -> next (nx0), ember marsh.wall.
- **Shots**: `warehouse_balcony__mid.jpg` (the whole picture is brick), `mothership_gallery__mid.jpg`, `hospital_late_quiet__a24.jpg`;
  sheets `world_warehouse.jpg`, `joins_main.jpg`.
- **What is wrong**: a glance or a stroll on the rail turns the camera to a wall at arm's length; with F1 the frame becomes a mosaic of
  six or eight blocks.
- **Made by**: the rail places, glances and strolls in `content/run/run.json` and `content/paths/*/run.json` (`place.rail`), against the
  geometry in `content/story/maps/*.json`. Not an art file: run stream.
- **Fix**: a headless check that samples each scene's camera pose every beat and fails when the nearest surface along the view is
  under 2.5 m (proposed `tools/art/camera_clearance.gd`); the run stream moves the failing glances.
- **Size**: small to write the check, medium to fix the rails. **Owner's taste**: no.

### F6. The falling notes and holds are opaque UI panels over the picture
- **Where**: every scene.
- **Shots**: any frame; `gospel__jordan_baptism__win.jpg`, `ward_late__win.jpg`, `squadron__base__a24.jpg`.
- **What is wrong**: a tap note is a 100 x 60 px rounded tile with a bright rim and a dark body; a hold is a full-width translucent
  lavender column up to the top of the picture. Over the pixel world they are the brightest, smoothest, biggest shapes on screen and
  cover faces and doors.
- **Made by**: `src/story/story_note_lane.gd` (on `NoteLane`), colours from `story_style.gd`.
- **Fix**: draw notes as light (a glowing shape with a mostly transparent body above the strike line), holds as a lit core one third of
  the pad wide; keep the hit geometry unchanged.
- **Size**: small to medium. **Owner's taste**: yes (how much the notes may cover the picture is a game-feel choice).

### F7. Open-air scenes are boxes: the sky is a ceiling with perspective, stars and moons are big squares
- **Where**: every Gospel exterior, squadron base.c02 and escape.c13 (the coast), hospital.garden and hospital_late, ward.courtyard,
  Ember orchard, north.pass, marsh.
- **Shots**: `gospel__galilee__a24.jpg`, `gospel__jordan_baptism__win.jpg` (a purple slab across the top), `squadron__escape_c13__a24.jpg`
  (a cartoon sky on a ceiling), `hospital__mid.jpg` / sheet `world_hospital.jpg` garden (a blocky moon).
- **What is wrong**: the sky is a 256 x 64 strip on a ceiling plane, so it converges like a roof and ends in a hard edge at the wall
  tops; stars are 8-pixel squares; the hills are flat walls.
- **Made by**: sky textures `sky_*` (`gospel_tex.py`, `tex_squadron*.py`, `tex_ember_tiles.py`, `bake_tiles.gd` `_sky`), sector `sky`
  drawing in `src/story/world/story_world.gd` / `story_map.gd`, map heights in `gospel_maps.py`, `tools/paths/squadron_*.py`, `ember_maps.py`.
- **Fix**: draw `sky` sectors as a backdrop at infinity (a camera-locked cylinder or a screen-space strip that turns with yaw), skies at
  1024 px or more, stars 1 to 2 px, the moon drawn, far hills as layered billboards.
- **Size**: medium (engine) plus small per world. **Owner's taste**: no.

### F8. Near people become translucent smears
- **Where**: hospital.cafeteria, hospital.dayroom, the passage into the Mothership, ward_late.exit, squadron air.
- **Shots**: `hospital_cafeteria__a24.jpg`, `passage_wh_ms__6_0.jpg`.
- **What is wrong**: a dancer passing between 1.0 and 1.8 m fades by alpha while magnified 3x, so a ghostly giant blurs a quarter of
  the frame.
- **Made by**: `NEAR_FADE` in `src/story/story_crowd.gd`.
- **Fix**: with F1(b): cull at the 1.25x size limit instead of fading a giant; if a fade is kept, fade to the fog colour, not to transparent.
- **Size**: small. **Owner's taste**: no.

### F9. The pad strip changes look by role and by world; quests wear the Warehouse's neon desk
- **Where**: all; most visible in Gospel, Squadron, Ember and the Bassment.
- **Shots**: `gospel__jordan_baptism__win.jpg`, `squadron__base__a24.jpg`, `ember__hollow__a24.jpg`; sheet `joins_main.jpg` (the strip
  swaps between the plain rail and the ornate desk inside a scene).
- **What is wrong**: the bottom 36 % of the screen is a neon purple club desk under a Galilean shore and a 1940s airfield; within a scene
  the strip cuts between the plain "dancer rail" and the ornate DJ deck as the role changes; the Underworld alone has its own copper desk.
- **Made by**: `src/story/story_deck.gd`, `story_pad_view.gd`, deck sprites in the chapter manifests (`borrow_sprites: true` in the path maps).
- **Fix**: one deck skin per world family (club, ship, hell, hospital, ward, Galilee, airfield, Ember, Bassment) built from the
  shared neutrals and the world accent; cross-fade the rail/deck change over a beat. Or one neutral strip everywhere (question 2).
- **Size**: medium. **Owner's taste**: yes.

### F10. The quest entrances do not read, and there is no herald yet
- **Where**: warehouse.balcony (Gospel's star), warehouse.booth (Squadron's radio), warehouse.bar (Ember's glass).
- **Shots**: `portal_gospel__lit.jpg`, `portal_squadron__lit.jpg`; sheet `entrances.jpg`.
- **What is wrong**: the Gospel entrance is a lamp in a dark corner; the Squadron radio is a small box under a smeared magenta
  "bomber shadow" that reads as a stain; the Ember glass is a few pixels on a table. Ruling 25 asks for a herald at each.
- **Made by**: `tools/story/art/tex_night_one.py` (`thing_booth_radio`, `thing_bomber_shadow`), Night One map things, hotspot rows
  in `tools/run/hotspot_tables/` (warehouse).
- **Fix**: redraw the three entrance objects to style guide section 12 (real objects, 0.8 m or more, the quest colour as emitted
  light), and build the herald (section 12) with an attach point.
- **Size**: medium. **Owner's taste**: no (the guide fixes the look; the choice of motif per quest is in question 4).

### F11. Traffic-sign lamps and a barrier X float in every world
- **Where**: every scene with a choice.
- **Shots**: `underworld_court__mid.jpg` sheet row (`world_underworld.jpg` court a24: a red no-entry sign at head height),
  `gospel__galilee__a24.jpg` (the red X of `bars.png` in Capernaum), `ember__hollow__a24.jpg`.
- **What is wrong**: the green chevron disc, the red no-entry square, a road signpost and a red-and-white barrier are road furniture
  of today, drawn flat, floating over doors in hell and in Galilee.
- **Made by**: `make_choice_art.py` -> `lamp_go.png`, `lamp_stop.png`, `sign_go.png`, `sign_stop.png`, `bars.png`.
- **Fix**: the lamp is a lamp of the world (a bulb cage, a torch, an oil lamp, a ship's status light) lit green or red; the barrier is
  the world's own (planks, chains, a rope); per-world sets with the doors (F3).
- **Size**: small to medium. **Owner's taste**: no.

### F12. The Bassment's creatures and the wizard are drawn in another style
- **Where**: Bassment cloakroom (moth), vaults, kitchens, echo; the wizard on the Warehouse floor and in the Bassment.
- **Shots**: `bassment_vaults__win.jpg`; sheet `bassment.jpg`; `assets/run/choice/wizard_*.png`.
- **What is wrong**: the creatures are big, flat, low-detail sprites (two shades, no dither, cartoon faces) at about 30 px/m; the wizard has
  a yellow and magenta halo outline. Next to the baked people they look like another game.
- **Made by**: `tools/trial/make_creatures.py` (`fig_*`), the Bassment textures `tex_bassment.py` (fig_wizard_*), `make_choice_art.py` (wizard).
- **Fix**: draw creatures with the `people.py` painter (three steps, dither, a darker edge, 128 px/m) or at least to section 6 and 7 of the guide;
  the wizard through the people pipeline with a robe and hat wardrobe, no halo.
- **Size**: medium. **Owner's taste**: no.

### F13. Two menu languages, and chapter thumbnails of rooms that no longer exist
- **Where**: main menu, Story chapters.
- **Shots**: `home_screen.jpg`; sheet `ui.jpg`.
- **What is wrong**: the main menu is flat grey and gold programmer UI with the engine version in the corner; the chapters menu is the
  neon `StoryStyle`. The chapter thumbnails are the first version's vector rooms, not the 2.5D worlds.
- **Made by**: `src/scenes/main_menu.*` (UiStyle), `src/story/story_chapters.gd` and `story_style.gd`, thumbnails from the old backdrops.
- **Fix**: one style (StoryStyle extended) for every menu, a title screen with a real frame of the game behind it, thumbnails captured
  from the run.
- **Size**: medium. **Owner's taste**: yes (the title screen).

### F14. Squadron is behind a sepia veil; Ember north is blown white; the orchard is garish
- **Where**: squadron base, air, city; ember north (birch hall, pass); ember hollow (orchard).
- **Shots**: `squadron__base__a24.jpg`, `ember__north__a24.jpg`, `ember__hollow__a24.jpg`; sheets `world_squadron_*.jpg`, `world_ember_*.jpg`.
- **What is wrong**: Squadron's fog and grain wash the people to the same khaki as the walls (contrast p95-p5 0.35 in the bomber); the
  birch hall is 6 % blown and has no shadows at all; the orchard's grass and apples are the most saturated thing in the game.
- **Made by**: fog and palettes in `tools/paths/squadron_*.py`, `chapter_squadron.py`, `tex_squadron*.py`; `ember_maps.py`,
  `tex_ember_tiles.py`, `tex_ember_things.py`, sector lights.
- **Fix**: tune to sections 2 and 4 of the guide (Squadron's sepia from the palette, not from fog over the people; the birch hall white
  at 0.8, with blue shadows; the orchard grass two steps less saturated).
- **Size**: small to medium. **Owner's taste**: no.

### F15. Speaker cones drawn as flat targets on hospital and ward walls
- **Where**: hospital.corridor, ward.courtyard, ward.corridor, ward_late.exit.
- **Shots**: `hospital_corridor__mid.jpg`; sheet `world_ward.jpg`.
- **What is wrong**: concentric orange and grey discs (the woofer sprite) hang in mid-air beside the purple silhouettes; they read as
  dartboards and come from the club.
- **Made by**: the chapter manifest sprite `woofer` (`hp_stage.py`, `mh_sprites.py`) placed by the map / `StoryStage`.
- **Fix**: draw the bandstand's speakers as world props (a PA cabinet on a stand) in the world's palette, or remove them where no
  stage is.
- **Size**: small. **Owner's taste**: no.

### F16. The passage window starts on a magnified wall or the beige door
- **Where**: every world change (warehouse.exit, mothership.exit, underworld.exit, hospital.exit, ward.exit, a path's last scene).
- **Shots**: `passage_wh_ms__0_75.jpg`; sheets `passage.jpg`, `joins_main.jpg` (nx0 column of the exits).
- **What is wrong**: the black mat and the opening window are a good idea, but the window's first frames show the new world's camera
  inside a door frame (beige checker, F3) or a wall at 1 m (F1, F5), so the first image of a new world is a blur of blocks.
- **Made by**: the arrival pose of the new world's first scene (`place.waypoint`, `rail.arrive` in run.json) and F3's door art; the
  frame itself is the transition code (`src/transition/`, not art).
- **Fix**: after F3 and F1 it improves on its own; the run stream starts arrivals 2 m back from the door.
- **Size**: small. **Owner's taste**: no.

### F17. Empty rooms
- **Where**: ward.dorm, ward_late.dorm (no people, no beds visible in the frames), mothership.gallery (mid), ember deeps.
- **Shots**: `ward_dorm__mid.jpg`; sheet `world_ward_late.jpg`.
- **What is wrong**: the art direction promises iron beds and residents; the frames show a dark green box.
- **Made by**: `content/story/maps/mental_hospital.json` (things, lights, homes), `content/story/mental_hospital.json` (actors).
- **Fix**: place beds (a `thing_bed_iron` in `tex_mental_hospital.py`), sleepers and a lamp; see F4.
- **Size**: small to medium. **Owner's taste**: no.

### F18. HUD details
- **Where**: every scene.
- **Shots**: any frame.
- **What is wrong**: judgement words (PERFECT, HELD, HOLD, MISS) are drawn under and over the falling notes and overlap one another;
  the energy and block bars top left are flat bars of another style from the pads; the HUD vanishes during a passage and pops back.
- **Made by**: `src/run/run_hud.gd` (run stream), `src/story/story_pad_view.gd`, `story_hud.gd`.
- **Fix**: one label row above the strip with a short fade; bars in the strip's frame style; the HUD fades with the passage.
- **Size**: small. **Owner's taste**: no.

### What is already good and must be kept
- **The baked people** (`docs/shots/story/figures_*.jpg`; every world sheet): naturalistic proportions, individual wardrobes, dither
  shading, no black outlines, the same hand in every world and quest. They are the standard the rest must meet.
- **The Warehouse floor** (`warehouse__mid.jpg`, `ui.jpg` states): LED checker floor, trusses, speaker stacks, coloured beams, a dense
  crowd: the closest frame to `Rave.png`.
- **The Hospital corridor** (`hospital__mid.jpg`): night blue, ceiling tiles, doors, warm lamps, a drip stand: close to `Hospital.png`
  and in the reference's value range.
- **The Underworld pit** (`underworld_pit__mid.jpg`): lava floor, red and purple beams, a strong single mood.
- **Gospel's props and Jerusalem** (`gospel__jerusalem__a24.jpg`, `textures/textures_galilee_shore.jpg`): clean pixel props in one hand.
- **Hotspot light** drawn inside the low-res pass (pools, rings, ripples pixelate with the world).
- **The 20:9 layout** (`wide_20x9.jpg`): the picture widens, nothing breaks.
- **The passage idea** (black mat, a window that opens on the new world): keep it, fix what the window shows (F16).

## 4. Work packages

Rules for all: work on a `wip/art-<package>` branch from `wip/art-audit`; commit one reviewed unit at a time; before/after shots with
`tools/art/audit_capture.sh` (`RW_SHOTS=<regex>`) into `docs/shots/art/<package>/`; run `tools/shrink_shots.py` before committing;
`tools/test.sh` green at the end; never regenerate another package's files. The people sheets are regenerated only by A2 (ruling 26).
Paths in "Owns" are the only files the package edits.

| Package | Findings | Owns (only these files) | Order | Acceptance | Model |
| --- | --- | --- | --- | --- | --- |
| **A1 Shared stage look** | F4 (shared part), F7 (engine part), F8, F1(b) runtime cap | `src/story/world/story_lowres.gd`, `story_post.gdshader`, `story_world.gd`, `story_map.gd` (sky only), `story_light.gd`, `src/story/story_crowd.gd`, `story_people.gd`, `story_people.gdshader`, `tools/art/*` checks | **Start at once.** First commit: clamp to fog and the figure cap (others tune after it) | `frame_check.py`: no world DARK or BLOWN on unchanged maps beyond the guide; no person above 1.25x sheet (a debug counter in a headless test over every scene); sky sectors drawn at infinity in `gospel__galilee`, `hospital_garden`; `tests/test_story_*` green | Opus |
| **A2 People** | F1(b) sheet side, F12 wizard, F10 herald body | `tools/story/art/people.py`, `people_sheets.py`, `wardrobe*.py`, `directed.py`, `content/story/directed_actors.json`, `assets/story/*/people/**` | Start at once on the wizard and herald wardrobe; re-bake **once**, after A1's cap is decided | `figure_sheets.py` sheets per chapter; `check_assets.py`; `tests/test_story_acts.gd` green | Opus |
| **A3 UI** | F6, F9, F13, F18 (story parts) | `src/story/story_note_lane.gd`, `story_pad_view.gd`, `story_deck.gd`, `story_hud.gd`, `story_style.gd`, `story_chapters.gd`; deck sprites only as new files `assets/run/deck/**`; `src/scenes/main_menu.*` and `src/run/run_hud.gd` only with the lead's approval (not art files under ruling 26) | Start at once; F6 and F9 wait for the owner's answers (questions 1, 2) | before/after `ui.jpg`, a frame per world family with the new strip; `tests/test_note_lane.gd`, `test_pad_judge.gd` green | Sonnet (Opus for the deck drawings) |
| **A4 Choice art** | F3, F11, F12 (wizard sprite until A2 replaces it) | `tools/run/make_choice_art.py`, `assets/run/choice/**` | Start at once (draw); the per-world lookup in `src/run/choice_props.gd` is a run-stream change: hand it to the lead | a sheet of every door set and lamp; `world_*` win shots with the new doors; `tests/test_choice_clarity.gd` green | Opus |
| **W1 Warehouse** | F1(a), F2, F10 objects | `tools/story/art/tex_night_one.py`, `stage.py`, `sprites.py`, `chars.py` (silhouettes only), `content/story/maps/night_one.json`, `content/story/night_one.json`, `assets/story/night_one/{textures,source,processed}/**`, manifest | After A1's first commit for light; textures at once | `texture_sheet.py night_one`: 0 LOWDENS, 0 MANYCOL; before/after `world_warehouse.jpg`; `check_assets.py` | Opus |
| **W2 Mothership** | F1(a), F2, F4 tuning | `tex_mothership.py`, `alien_chars.py` (silhouettes), `mothership_stage.py`, `mothership_views.py`, `views_bridge.py`, `views_reactor.py`, `content/story/maps/mothership.json`, `content/story/mothership.json`, `assets/story/mothership/**` except people | as W1 | as W1 for `mothership` | Opus |
| **W3 Underworld** | F1(a), F2 (banners, crops), F4 tuning | `tex_underworld.py`, `uw_*.py`, `chapter_underworld.py`, `content/story/maps/underworld.json`, `content/story/underworld.json`, `assets/story/underworld/**` except people | as W1 | as W1 for `underworld` | Opus |
| **W4 Hospital** (both hospital worlds) | F1(a), F2, F15, F7 garden sky | `tex_hospital.py`, `hp_*.py`, `chapter_hospital.py`, `content/story/maps/hospital.json`, `content/story/hospital.json`, `assets/story/hospital/**` except people | as W1 | as W1 for `hospital` | Sonnet (the textures are already pixel art; mostly density) |
| **W5 Ward** (both ward worlds) | F1(a), F2 (crowns), F4, F15, F17 | `tex_mental_hospital.py`, `mh_*.py`, `chapter_mental_hospital.py`, `content/story/maps/mental_hospital.json`, `content/story/mental_hospital.json`, `assets/story/mental_hospital/**` except people | as W1 | as W1 for `mental_hospital`; `ward_dorm` shows beds and people | Opus |
| **W6 Gospel** | F1(a), F7 skies and hills | `gospel_tex.py`, `gospel_things_a.py`, `gospel_things_b.py`, `gospel_maps.py`, `build_gospel_art.py`, `content/story/maps/{galilee_shore,hillside,bethany,jerusalem}.json`, `content/story/` same four, `assets/story/` same four except people | after A1's sky change | as W1 for the four maps; `tests/test_gospel.gd` green | Sonnet |
| **W7 Squadron** | F1(a), F7 (airfield, coast skies), F14 | `tex_squadron*.py`, `chapter_squadron.py`, `chapter_airfield.py`, `chapter_city.py`, `chapter_harbour.py`, `tools/paths/squadron_*.py`, maps and chapters `airfield`, `city`, `harbour`, `assets/story/{airfield,city,harbour}/**` except people | after A1 | as W1 for the three maps; median 0.18 to 0.38 per world, contrast p95-p5 above 0.4 | Sonnet |
| **W8 Ember** | F1(a) (worst ceilings), F7, F14 | `tex_ember_tiles.py`, `tex_ember_things.py`, `ember_spec.py`, `ember_maps.py`, `build_ember.py`, maps and chapters `orchard`, `birch_hall`, `deep_halls`, `ash_land`, their `assets/story/**` except people | after A1 | as W1 for the four maps; `tests/test_run_ember.gd` green | Opus (the most box-like rooms) |
| **W9 Bassment** | F1(a), F12 creatures | `tools/story/art/tex_bassment.py`, `tools/trial/make_creatures.py`, `tools/trial/make_scenes.py` (art fields only), `content/story/maps/bassment_*.json`, `assets/story/bassment/**`, `assets/trial/**` | at once | `bassment.jpg` before/after; `tools/trial/validate.gd` green | Opus |
| **A5 Camera clearance** (check only) | F5, F16 | `tools/art/camera_clearance.gd` (new) | at once | a list of failing scene poses handed to the run stream; the fixes are theirs | Sonnet |

**Start at once, in parallel**: A1, A2 (wizard and herald wardrobe, no re-bake yet), A3 (except F6 and F9), A4, A5, W9, and the
texture-density part of W1 to W5 (procedural tiles do not depend on A1). **After A1's first commit** (fog clamp, figure cap, sky at
infinity): the light tuning in W1 to W5, and all of W6, W7, W8. **Last**: A2's single re-bake of the people sheets, then the herald
placed on the three existing entrances (ruling 25), then a full `audit_capture.sh all` pass compared with this audit.

Shared-file warnings: `tools/story/bake_tiles.gd` and `tools/story/art/tiles.py` are shared by the five old chapters; no package edits them
(a procedural id in `tex_<chapter>.py` replaces a baked tile, and its metres come with it). `tools/story/build_assets.py` is not edited;
each world runs it for its own chapter only (`build_assets.py <chapter> tiles|stage`). `content/story/**` is not named in ruling 26;
the lead should confirm that the world packages own their map and chapter JSON.

## 5. Questions of taste for the owner

1. **Falling notes over the picture (F6).** Today they are solid tiles and full-height columns. Recommendation: draw them as light
   (a glowing outline and a faint body), holds as a thin lit core, so the picture stays readable; the timing stays exactly the same.
2. **The pad strip per world (F9).** A deck skin per world family (club desk, ship console, hell's copper, a wooden board for Galilee,
   an instrument panel for the Squadron, a carved board for the Ember) or one neutral dark strip everywhere? Recommendation: per world
   family, because the strip is a third of the screen and should belong to the place.
3. **The title screen (F13).** Recommendation: the main menu over a live, slowly moving frame of the Warehouse floor, in the neon
   style of the chapters menu; the engine version line removed.
4. **Quest entrance motifs (F10, ruling 25).** Recommendation: Gospel, a star projected on the balcony wall with a robed herald holding
   an oil lamp; Squadron, the radio redrawn as a 1940s field set on a crate with a pilot herald in a flying cap; Ember, a glowing ember in
   a glass on the bar with a hooded warden herald. Each emits its quest colour.
