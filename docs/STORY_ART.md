# Story Campaign art: Night One and the chapters

All artwork of the Story Campaign's first level is **original**, drawn by code in this repository. No OpenRA sprites, no stock
or downloaded assets, no external services. Regenerate everything with one command; it only touches
`assets/story/night_one/` and never the music, Ableton sources or other game art.

```
python3 tools/story/build_assets.py             # full rebuild: Night One, then every chapter (mothership)
python3 tools/story/build_assets.py mothership  # only the mothership chapter (also: mothership chars|stage|interlude)
python3 tools/story/build_assets.py chars       # only the six dancers (keeps the manifest's stage section)
python3 tools/story/build_assets.py stage       # only the room, props, silhouettes and PNG effects
python3 tools/story/check_assets.py             # validate the manifest against the art contract
python3 tools/story/check_assets.py --determinism   # also rebuild twice and compare hashes
tools/story/shoot_preview.sh stage /tmp/story_art   # real Godot screenshot of the composed set (needs a display)
tools/story/shoot_preview.sh set /tmp/story_art mothership   # third argument = chapter folder under assets/story/
```

Requirements: Python 3, Pillow and NumPy (only for the few PNG effects). Godot 4.5.1 imports the SVGs natively; run
`godot --headless --path . --import` after a rebuild (the `.import` files are committed like the rest of the project).

## How it is made

| Part | Source | Why |
| --- | --- | --- |
| Characters, backdrop, speakers, riser, desk, props, silhouettes | **SVG** written by `tools/story/art/chars.py` and `stage.py`, imported by Godot at 2x | Crisp at any scale, editable in Inkscape, limbs/parts stay separate for rigging |
| Beams, glows, floor spot pools, haze, vignette, confetti | **PNG** from Pillow/NumPy in `tools/story/art/sprites.py` | Godot's SVG importer (ThorVG) has no blur or filter support, so soft light needs real alpha gradients |
| `manifest.json` | written by the same script | The one file the runtime reads: part pivots, joints, layers, anchors, sprite ids |

Outputs: `assets/story/night_one/source/*.svg` (about 200 small text files), `assets/story/night_one/processed/*.png` (7 small
textures), `assets/story/night_one/manifest.json`. Everything is deterministic, the total is about 2 MB including Godot's `.import` files.

SVGs are written at **2x** (`width/height` are twice the `viewBox`), so every manifest entry has `px_scale: 0.5`; a sprite's
design-space size is its texture size times `px_scale`. Do not hand-edit the generated SVGs unless you also stop regenerating
them: edit the Python (shapes are plain helpers in `tools/story/art/lib.py`) and rebuild.

## Style

Stylised 2D neon vector/cartoon: bold indigo outlines (`#1b1040`, never pure black), two-tone cel shading with a soft shade
gradient on the right and cyan (left) / magenta (right) rim lights that match the room's lights, a palette of indigo and navy
shadows, magenta, cyan and violet lights and a few warm amber accents. Faces carry the emotion (eyes, brows, mouth, blush,
sweat drop) together with posture, so mood never depends on hue alone.

## Characters (`archetypes`)

Six archetypes with different proportions, hair, clothes and accessories, two palette/detail variants each (`a`, `b`):

| id | read | notable |
| --- | --- | --- |
| `groover` | tall, lean | spiky hair with coloured tips, tank top with chevron print, chain, side-stripe trousers |
| `ponytail` | slim | swinging side ponytail with scrunchie, crop top, wide trousers, lashes |
| `hoodie` | broad, short | cap with badge, big hoodie with drawstrings and pocket, chunky sneakers, hood bunched behind the neck |
| `curly` | medium | big curl cloud (back and front pieces), round neon glasses, open jacket and shirt |
| `bob` | small | blunt bob that swings, sleeveless dress with collar, pleated skirt, socks, freckles |
| `punk` | tallest | mohawk with a spiked back layer, studded vest and wristbands, ripped trousers, tall boots |

Rig space: origin between the feet, +x right, **+y down** (so the head is at negative y), 2x textures with `px_scale 0.5`.
`joints` lists each joint's rest position in rig space. Runtime hierarchy: `hips` > { `torso` > { `head`, `shoulder_l` > `elbow_l`,
`shoulder_r` > `elbow_r` }, `hip_l`, `hip_r` }; `l` is screen-left.

Per variant: `parts` (name, joint, z, file, `pivot` = the joint's position **in texture pixels**, `px_scale`), `faces`
(`neutral`, `happy`, `cheer`, `sad`, anchored on `head`, drawn at `face_z`) and `glow_hand` (hand position in the forearm
textures for glow sticks). Notes for the runtime:

- A sprite is placed at `-pivot * px_scale` under its joint node. For hair and hood textures the joint lies **outside** the
  texture; that is expected.
- `swing: true` parts (ponytail, bob) also carry `swing_pivot` (texture px) where the pendulum rotation applies; their normal
  `pivot` is still the head joint, used for placement.
- Rotation convention (Godot, clockwise positive): a left arm hanging down rotates **outward with positive angles**; the right
  arm with negative angles. Raising both arms straight up is about +165 (left) and -165 (right) at the shoulder.
- Upper arm and forearm outlines have no seam at the elbow in any pose; legs rotate cleanly at the hip within about +/-25 degrees.
- `tools/story/preview_art.gd` is a working reference implementation of this rig (it is independent of `src/story/`).

## The room (`stage`)

A fixed DJ's-eye view: one-point perspective with the vanishing point at (640, 130) in the 1280 x 720 design space. Far wall
x 270..1010, y 52..262; side walls with posters and neon runs; ceiling trusses; a bar with lit bottles; a doorway; a lit LED-tile
dance floor; the mixing desk across the bottom (`desk_top`, authored 1280 x 260, stretched into the pad strip).

- `layers`: `backdrop`, `riser`, `speaker_l`, `speaker_r`, `desk_top` (back to front).
- `anchors`: `led_screen` (empty dark panel for the runtime's equaliser), `doorway`, `floor_rows` (crowd feet rows and their
  perspective `scale`), `floor_polygon`, `floor_grid` (the perspective rule to paint tile ripples), `light_points` (8 moving-head
  mounts), `woofers` (4 cone positions, sprite `woofer` has `radius` 50), `disco_ball`, `riser`, `circle_centre`/`circle_radii`
  for the dance-circle ellipse. A front-row character at `scale` 1.0 is 260 px tall; about 0.8 of the row scale keeps the room
  visible behind a crowd of 30.
- `sprites`: `woofer`, `fixture` (moving head, pivot at the mount, `lens` at the lamp), `disco_ball`, `glowstick`, `door_open`
  (overlay with its own `pos`), `spot_pool`, `haze_a`, `haze_b`, `glow`, `beam` (draw additively and tint), `vignette`,
  `confetti` (4 frames of 32 px), `desk_lip_glow`, and the deck pieces `pad_bezel` (opening is `inner_ratio` of its size, so
  scale it uniformly), `platter` (optional spinning record), `knob`, `fader_slot`, `fader_cap`, `crossfader`, `vu_segment`,
  `deck_screw`.
- `silhouettes`: `sil_a`, `sil_b`, `sil_c` for the rear crowd, each with `idle` and `up` (hands raised); dark navy with a thin
  cyan/magenta rim light, pivot at the bottom centre.

## Changing things

- A character: edit its entry in `ARCH` (proportions), `VARIANTS` (palettes) or the archetype's drawing code in `chars.py`.
- The room: `build_backdrop()` and friends in `stage.py` (coordinates are design pixels; `lwall_y`, `rwall_y` and `floor_x`
  keep walls and floor on the vanishing point).
- Light effects: `sprites.py`.
- After a change run `build_assets.py`, then `shoot_preview.sh chars`, `heads`, `joints`, `stage`, `stage_low`, `sil` to look
  at it.

## Chapter `mothership` (assets/story/mothership/)

An alien ship's ring-shaped rave deck, drawn by `tools/story/art/alien_chars.py` (dancers) and `tools/story/art/mothership_stage.py`
(set, sprites, pieces, interlude). It reuses Night One's helpers (`lib.py`, `chars.skeleton`, the PNG light sprites in `sprites.py`),
the same camera and perspective, and the same manifest schema, so the runtime needs no code change for the stage. Night One's files
are untouched (`check_assets.py --determinism` hashes both folders). Run `build_assets.py mothership`; the PNGs are small (glow, beam,
spot_pool, haze, vignette, confetti shared in kind with Night One; plus the interlude PNGs).

- `archetypes` (rig contract as above, same four faces, same part names): `grey` (big cranium, huge slanted almond eyes, silver
  jumpsuit with shoulder pads), `antenna` (tall, two swinging antennae with glowing tips, `hair_front` swing), `blob` (round translucent
  jelly body, short limbs), `insect` (mantis, long thin limbs, forearm blades, mandibles, swinging feelers as `hair_front`; its wing-cases
  are the `hair_back` part with `swing: true` on joint **`torso`**, pivot at the neck), `cyclops` (one big eye, stocky, overalls), `tentacle` (head crest with five swinging tentacles `hair_back` plus two front locks
  `hair_front`). Two variants each (`a`/`b`: skin, outfit palette and one detail, such as the grey's chest emblem or the blob's spots
  versus stripes). Eyes carry the emotion (`cheer` is a squint with an open mouth, `sad` has drooping lids, brows and a sweat drop).
  `glow_hand` is the hand position in the forearm texture for the shared `glowstick` sprite (an orb wand here).
- `stage.layers`: `backdrop` (hex-plated floor, far wall with the viewing window onto space, a ringed planet and a moon, console ledge,
  airlock, alien bar, hull ribs and portholes, ceiling and hanging pylons), `riser` (hover platform), `speaker_l`/`speaker_r` (resonator
  columns, sockets for the woofers), `desk_top` (bio-tech console). `led_screen` is the dark frame hanging in front of the window
  (460, 150, 360, 58), `doorway` the airlock. Extra anchors: `window`, `planet`, `bar`.
- `stage.sprites`: the same ids as Night One, re-themed (`fixture` = light-probe orb, `disco_ball` = energy orb, `glowstick` = orb wand,
  `confetti` = star sparks, `platter` = hologram disc); light sprites stay white so the runtime tints them.
- `stage.pieces`: `planet_window_glow` (pulse, behind), `warp_streaks` (none, behind; drawn off the LED screen), `saucer_flyby` (bob,
  behind), `ring_lights` (pulse, behind), `pylon_beams` (pulse, behind), `alien_banner` (sway, behind; pivot at its top edge), `beam_home`
  (pulse, front, `blend: add`: the goodbye tractor beam onto the dance circle, cued at bar 79 when the deck has gone quiet),
  `hologram_dome` (pulse, front; a faint fill so it never washes out the dancers under it). Entry fields: `file`, `pos` (top-left, design px), `size`, `px_scale`, `pivot`
  (animation origin, texture px), `anim`, `z` (`behind` = over the backdrop and under the crowd, `front` = over the crowd). The glowing
  ones are light-on-transparent: draw them additively.
- `interlude` (for the scripted UFO scene over the **Night One** club): `sprites` `ufo` (900 x 260 design px, seen from below, pivot at
  the centre of its underside), `tractor_beam` (PNG, pivot top centre, 480 x 340 design px, stretch it to `beam_floor`), `ufo_glow`,
  `sparkle`, `light_flood` (full screen); `anchors` `ufo_hover` [640, 92], `beam_floor` [640, 372].
- Preview: `shoot_preview.sh <mode> <out> mothership` with `set` (bare room), `stage`, `chars`, `chars_b`, `heads`, `joints`, `pieces`
  (sheet of every piece), `sil`, `deck`, `interlude`, `interlude_flood` (composited over the Night One stage). `RW_WARP=1` shows
  `warp_streaks` in `stage`.

### Mothership extra views (`stage.views`, `stage.sprites.passage_frame`)

The camera tours the ship (spec: `tools/story/ART_CONTRACT_VIEWS.md`); the existing deck is the view `main`, three more rooms follow in route
order: `gallery`, `reactor`, `bridge`. Code: `tools/story/art/mothership_views.py` (the shared `Room` perspective toolkit, the gallery,
the passage frame and `build_views()`, called from `mothership_stage.build_stage()`), `views_reactor.py`, `views_bridge.py`. Output goes to
`assets/story/mothership/source/views/`; the existing files are unchanged, the manifest only gains `stage.views` and the sprite.

Each view is `{id, title, layers, anchors, pieces, palette_hint}`. `layers`: `backdrop` (full 1280 x 720 room, behind the crowd) and
`front_frame` (1280 x 480, `z: "front"`: arches, pipes or console wedges at the screen edges, over the crowd). Anchors use the main deck's
conventions (`floor_rows` with the scale derived from that room's horizon, `floor_polygon`, `floor_grid`, 8 `light_points`, `led_screen`,
`circle_centre`/`circle_radii`, `vanish`, `horizon_y`, `disco_ball`, `wall_left_x`/`wall_right_x`); optional keys are only present where the room has
the feature: `woofers` (bridge only, speaker pods at the ends of the far console bank), `riser` (bridge, the captain's dais), `doorway`
(gallery: the amber arch, where the gatherers wait; reactor: the left blast door the late arrivals use; arrivals walk out of it). The shared
`door_open` overlay is positioned for the dance deck's airlock, so `doors_open` is only cued while the camera is on the main deck. Extra descriptive anchors: `window`, `planet`, `bar`,
`core`, `chair`. Pieces use the main schema plus `blend: "add"` for the light-on-transparent ones (`pos` top-left, `pivot` in texture px).

| view | place | vanish | pieces (anim, z, blend) |
| --- | --- | --- | --- |
| `gallery` | long lounge gallery, curved window wall with the planet's night side (lit crescent, city lights) on the right, booths and tufted sofas with pillows on the left, bar and amber arched door at the end, reflected in the polished floor | (640, 150), the door | `gallery_planet_shine` (pulse, behind, add), `gallery_cruiser` (bob, behind), `gallery_holo_menu` (flicker, behind, add) |
| `reactor` | ring chamber: containment housing with the glowing core, energy pylons (shaded plating, glass coolant tubes with bubbles, hazard plinths), catwalk grating over the glowing pit, a riveted walkway with chevrons and the core's reflection, hazard ring | (640, 140), the core | `reactor_core_glow` (pulse, add), `reactor_core_ring` (rotate, add), `reactor_pylon_arcs` (flicker, add), `reactor_steam` (flicker, add: venting coolant beside the plinths); all behind |
| `bridge` | command bridge: viewscreen with a star field and planet, banked consoles, captain's chair on a dais, star-chart ring, a runway with chevrons and the viewscreen's reflection on the deck | (640, 125), the viewscreen | `bridge_warp_streaks` (pulse, add), `bridge_holo_globe` (bob, add), `bridge_alert_beacons` (flicker, add); all behind |

Staging (`content/story/mothership.json`): the camera moves on the four bass entries of the music (bars 17 step into the gallery, 33 turn
into the reactor, 49 walk onto the bridge, 65 turn back to the main deck), each room is lit with its own palette on arrival (gallery `warm` =
amber/magenta, reactor and bridge `cool` = mint/blue-violet, main finale `rave`), and every `piece_on` / `piece_pulse` cue names a piece of
the room the camera is in at that bar (a view's pieces are on while that room is shown; a `piece_on` on arrival fades one in with the
room). Decisions play where their crowd is: the translator at bar 29 in the gallery (the gatherers waiting at the arch walk in or hang
back), gravity-off and the warp jump on the bridge, the final transmission on the main deck.

`passage_frame`: an octagonal bulkhead hatch frame (door slots, hazard stripes, sign plate, neon lining) authored 640 x 360 design px
(a 1280 x 720 texture, `px_scale` 0.5, centre pivot), so a 2x scale covers the 1280 x 720 frame; the octagonal opening (`opening` = x, y, w, h in
design px of the 640 x 360 frame) is transparent, the plating reaches all four corners.

Perspective: `Room(vp, kf, t0, b0)` maps near-frame points (u, v at depth factor k) to the screen, with ribs at equal depth steps, boxes (sofas,
consoles, pylons, dais) and floor planes, so floors converge on the room's own `vanish` and the `floor_rows` scale matches. Preview:
`tools/story/shoot_views.sh <main|gallery|reactor|bridge> <stage|set|stage_low|pieces|passage> [out_dir]` (`preview_views.gd` extends
`preview_art.gd`; `stage` shows the crowd rig, beams and the view's pieces, `passage` overlays the frame at 2x).

## Provenance and licence

Every pixel comes from the code in `tools/story/` in this repository; there is no third-party content and no generated-image
service. The art is covered by the repository's own licence.

# Story Campaign art: the Underworld chapter (`underworld`)

Hell's nightclub: a friendly stylised cartoon rave of demons (no gore) in a cavern of cracked obsidian and lava. Same
conventions, helpers and rig contract as Night One (see above and `tools/story/ART_CONTRACT_CHAPTERS.md`); everything is original
and drawn by code, with the output in its own folder `assets/story/underworld/{source,processed,manifest.json}`.

```
python3 tools/story/build_assets.py underworld          # rebuild the chapter (also part of a bare `build_assets.py`)
python3 tools/story/build_assets.py underworld chars    # only the six demons (keeps the stage section of the manifest)
python3 tools/story/build_assets.py underworld stage    # only the room, pieces, silhouettes, PNG effects and interlude sprites
python3 tools/story/check_assets.py [--determinism]     # validates Night One and every chapter manifest
tools/story/shoot_chapter.sh underworld <mode> /tmp/uw  # real Godot screenshot; mode = chars chars_b heads joints close sil stage set deck pieces interlude
```

Code: `tools/story/art/chapter_underworld.py` (build target, redirects the output folder), `uw_chars.py` (demons), `uw_stage.py` (room,
pieces, Pillow textures, interlude). The deck pieces (pad bezel, platter, knobs, faders, desk top) reuse Night One's drawing code and
re-theme it by remapping the colours (indigo to wine, cyan to gold, magenta to lava) plus a few extra bone ornaments.
Preview: `tools/story/preview_chapter.gd` extends Night One's `preview_art.gd`; `RW_CHAPTER` picks the chapter, `RW_PREVIEW` the mode
(`set` shows the room without the crowd, `pieces` every `stage.pieces` entry on its own, `interlude` the cutscene sprites over
Night One's club, `close` with `RW_ARCHS=a,b,c RW_VARIANT=a|b` big rigs for joint checks).

## Demons (`archetypes`)

Same joints, part names, z ranges, four faces (`neutral happy cheer sad`) and `glow_hand` as Night One. The arms are two rotating
segments (round caps at shoulder and elbow, no seam in any pose) and the legs rotate at the hip. Variants `a`/`b` change the palette
and one detail. Extra parts are ordinary parts: swinging ones carry `swing: true` + `swing_pivot`, exactly like the Night One ponytail.

| id | read | parts beyond the base set | variant detail |
| --- | --- | --- | --- |
| `imp` | small, big head, pointed ears, cute fangs | `tail` (joint `hips`, swing, spade tip), horns in `hair_back` | a vest, b striped shirt |
| `brute` | broad, ram horns, tusks and nose ring, spiked pauldrons on the upper arms | ram horns in `hair_back` | a leather harness with skull buckle, b gold chest plate |
| `fiend` | tall, slick quiff, small horns, goatee, waistcoat | `wings` (joint `torso`, swing, bat wings) | a bow tie, b long tie |
| `skeleton` | bone body with ribs and spine, hollow grin, party hat | party hat in `hair_front` | a red hat, b green hat and bow tie |
| `flame` | fire spirit, orange (a) or violet-blue (b) body, flame feet | flame hair in `hair_back` + `hair_front` (both swing) | a shorts, b scarf |
| `horned_queen` | elegant, long sweeping horns, long hair, pointed boots | `cape` (joint `torso`, swing) and a fixed `collar`, `skirt` on `hips` | a bare arms, b opera gloves |

The `glow_hand` position and the `glowstick` sprite (white, tintable) form a small flame torch. Rear silhouettes `sil_a` (ram horns),
`sil_b` (bat wings), `sil_c` (big ears, little horns, tail) have `idle` and `up`, with orange (left) and magenta (right) rim lights.

## The room (`stage`)

Same perspective, anchors, `floor_rows` and sprite ids as Night One. `layers`: `backdrop` (cavern ceiling with stalactites, far wall with
lava veins, lava falls on the side walls, bone columns, the fanged hellmouth at the back centre, the marquee `led_screen` hung on chains,
the closed iron `doorway` gate, a bone bar, cracked obsidian floor with glowing tiles and a summoning circle matching `circle_*`, fire-pit
bowls), `riser` (bone-and-iron platform), `speaker_l/r` (infernal amp stacks with horns and skulls; their `pos`/`size` include a small
overhang), `desk_top`. Extra anchors: `floor_grid`, `wall_left_x`, `wall_right_x`, `horizon_y`, `hellmouth` [x, y, r], `fire_pits`.
Sprites: `woofer` (toothed iron ring), `fixture` (a demonic eye-lamp), `disco_ball` (an infernal brazier orb in a cage), `glowstick`
(torch), `door_open`, the deck pieces, and the white lighting sprites (`glow beam spot_pool haze_a haze_b vignette`, `confetti` = ash-embers).

`stage.pieces` (switch on/off/animate by id; `pos`/`size` are the top-left rectangle in design px, `pivot` is relative to `pos`, `blend: add`
means draw additively):

| id | file | anim | z |
| --- | --- | --- | --- |
| `lava_flow` | glowing cracks across the dance floor | `pulse` | behind |
| `fire_pits_left`, `fire_pits_right` | flame jets above the two pits | `flicker` | behind |
| `hellmouth_portal` | swirl PNG inside the hellmouth, rotates about its centre | `rotate` | behind |
| `chains_swing` | three hanging chains with hooks and a skull lantern, pivot at the top | `sway` | behind |
| `skull_throne` | the throne on the riser | `none` | behind |
| `bone_arches` | giant rib bones framing the view | `none` | front |
| `ember_rain` | falling embers (PNG) | `flicker` | front |

### Extra views (`stage.views`) and `stage.sprites.passage_frame`

For the moving (Doom-style) camera the chapter has three more rooms besides `main`, each a full 1280 x 720 room drawn from the DJ's eye
line with its own one-point perspective (see `tools/story/ART_CONTRACT_VIEWS.md`). Code: `uw_views.py` (the `Room` perspective helper,
shared bits, the passage frame, `build_views()`), `uw_view_court.py`, `uw_view_pit.py`, `uw_view_furnace.py`; `uw_stage.build_stage()`
calls `build_views()` last, so the `main` room and every older file are untouched. Output: `assets/story/underworld/source/views/*.svg`
(2x, `px_scale` 0.5). Each view entry has `layers` (`backdrop`; `front_frame` with `z: front` drawn over the crowd, 1280 x 470),
`anchors`, 4 `pieces` and a `palette_hint`.

| view | place | floor / crowd | pieces (anim, z, blend) | optional anchors |
| --- | --- | --- | --- | --- |
| `court` | obsidian court: columns with gold bands, gothic windows, banners, a red runner to a stepped dais with the skull throne and braziers (violet, gold, magenta) | horizon 140, floor from y 258, rows 286..438 | `court_throne_aura` (pulse, behind, add), `court_flames` (flicker, behind, add), `court_banners` (sway, behind, mix, pivot at the top), `court_seal` (pulse, behind, add) | `led_screen` (judgement tablet over the throne), `riser`, `disco_ball`, `throne`, `braziers`; no woofers |
| `pit` | lava lake, far-shore fortress and volcano, a bone causeway and two bridges, the stage platform out on the lake (ember red, orange, bone) | horizon 190, chamfered platform polygon from y 266 (row 0 stays between x 330 and 950, the lake shows at the sides) | `pit_lava_glare` (pulse, behind, add), `pit_plumes_l/_r` (flicker, behind, add), `pit_fortress_glow` (pulse, behind, add) | `led_screen`, 4 `woofers` (two amp stacks on the platform), `riser`, `causeway`, `bridges` |
| `furnace` | the great forge: riveted steel hall, pipes, hazard stripes, anvils, molten channels, a huge grinning demon face whose furnace mouth is the screen (steel blue, white-hot orange) | horizon 125, floor from y 264, rows 286..438 | `furnace_eyes` (pulse, behind, add), `furnace_ladle` (sway, behind, mix, pivot at the crane chain), `furnace_sparks` (flicker, behind, add), `furnace_channels` (pulse, behind, add) | `led_screen` (the mouth), 4 `woofers` (boiler hatches), `riser`, `face`, `anvils`, `channels` |

`vanish` is where the dolly pushes when walking out of that view: the throne niche, the fortress gate, the furnace mouth. Every view
also has `light_points` (8, hung from the roof or girders), `circle_centre`/`circle_radii` (a seal on the floor under the crowd),
`floor_grid`, `wall_left_x`/`wall_right_x` and `disco_ball` [640, 0]. The shared `stage.sprites` (fixture, beam, glow, woofer ...) are reused.

`stage.sprites.passage_frame`: a hell-gate arch (rock slab, bone moulding, fangs, keystone skull) authored 640 x 360 design px
(`px_scale` 0.5, centre pivot [640, 360] in texture px): scale it 2x to span 1280 x 720; the arched opening is transparent, so the camera
can scale it up past 2x and fly through.

Preview: `RW_VIEW=court|pit|furnace tools/story/shoot_chapter.sh underworld stage|set|pieces <out>` renders that room with the crowd rig
(the view's anchors override the main ones; missing optional keys switch the feature off), and `shoot_chapter.sh underworld passage`
shows the frame.

## Interlude (`interlude`)

Sprites to composite over Night One's club view (fixed camera): `crack_glow` (a fissure fanning out in perspective, pivot at its far end),
`crack_segment` (a straight slice to stretch or chain), `flame_jet` (tall flame, pivot at the base, animate by flip/scale), `portal_vortex`
(512 px red-black swirl, centre pivot), `embers` (4 frames of 32 px), `dark_wash` (red-black full-screen wash, 320 x 180 shown at 4x).
Anchors: `crack_origin`, `crack_end`, `portal_centre`, `flame_jets` (two floor points), and the contract's `ufo_hover`/`beam_floor`
(unused by this chapter, kept for the generic cutscene code). Draw the `blend: add` ones additively.
