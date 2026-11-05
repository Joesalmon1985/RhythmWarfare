# Story Campaign art: Night One and the chapters

All artwork of the Story Campaign's first level is **original**, drawn by code in this repository. No OpenRA sprites, no stock
or downloaded assets, no external services. Regenerate everything with one command; it only touches
`assets/story/night_one/` and never the music, Ableton sources or other game art.

> **2.5D note.** The chapter sections below describe how the art was drawn for the first, painted version. The rooms' anchors, `floor_rows` and layer compositing they mention are
> no longer read (the map places everything; see the last section), and the 2D review tools they name (`shoot_chapter.sh`, `shoot_views.sh`, `shoot_hp.sh`, `shoot_mh.sh`,
> `preview_chapter/views/mh/sectioned`) were removed with the 2D rooms. Character, prop, piece and interlude art, the generators and the contracts are unchanged. Use
> `tools/story/capture.sh` and `tools/story/preview_art.tscn` (character and prop sheets) to look at things.

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
  visible behind a crowd of 30. `led_tiles` (optional, Night One only) is the lit floor's tile grid (`far_x`, `rows`, `vanishing_point`,
  `far_y`): the runtime lights single tiles in chases, ripples and sweeps on the beat; rooms without it keep a plain floor glow.
- Runtime presentation (no art needed): the pads are drawn by `src/story/story_pad_view.gd` (a PadView skin on the `pad_bezel`
  and desk art), the falling notes by `story_note_lane.gd`, the overlay cards by `story_hud.gd`, the menus by `story_style.gd`.
  Each room is split into far / mid / near / top depth groups so the moving camera has parallax (`StoryView.PARALLAX`).
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
| `brute` | broad, ram horns, tusks and nose ring, bulging deltoids under armoured pauldrons | ram horns in `hair_back`; `pauldron_l`/`pauldron_r` (joint **`torso`**, z 6: a riveted dome with two lames, gold trim and three horn spikes, drawn over the upper arm so a raised arm slides out from under it) | a leather harness with skull buckle and iron pauldrons with a skull boss, b gold chest plate and orange pauldrons with a flame sigil |
| `fiend` | tall, slick quiff, pale horns, goatee, waistcoat, jacket sleeves with shirt cuffs | `wings` (joint `torso`, swing, bat wings) | a purple jacket and bow tie, b red suit and long tie |
| `skeleton` | bone body with ribs and spine, hollow grin, party hat | party hat in `hair_front` | a red hat, b green hat and bow tie |
| `flame` | fire spirit, orange (a) or violet-blue (b) body with a hot core down every limb, flames off the shoulders and forearms, flame feet | flame hair in `hair_back` + `hair_front` (both swing) | a shorts, b scarf |
| `horned_queen` | elegant, long sweeping horns, long hair, pointed boots | `cape` (joint `torso`, swing) and a fixed `collar`, `skirt` on `hips` | a bare arms, b opera gloves |

Every demon has a tapered neck with a shadow under the jaw. The `glow_hand` position and the `glowstick` sprite (white, tintable) form a
small flame torch. Rear silhouettes `sil_a` (a brute: spiral ram horns, spiked pauldrons), `sil_b` (a fiend: swept horns, quiff, wide bat
wings), `sil_c` (an imp: big ears, little horns, spade tail) have `idle` and `up` (arms up with devil-horns hands), with orange (left) and
magenta (right) rim lights.

## The room (`stage`)

Same perspective, anchors, `floor_rows` and sprite ids as Night One. `layers`: `backdrop` (cavern ceiling with stalactites, far wall with
lava veins, lava falls on the side walls, bone columns, the fanged hellmouth at the back centre, the marquee `led_screen` hung on chains,
the closed iron `doorway` gate, a bone bar, cracked obsidian floor with glowing tiles and a summoning circle matching `circle_*`, lava
gutters along the foot of both side walls fed by the lava falls, fire-pit bowls), `riser` (bone-and-iron platform), `speaker_l/r` (infernal amp stacks with horns and skulls; their `pos`/`size` include a small
overhang), `desk_top`. Extra anchors: `floor_grid`, `wall_left_x`, `wall_right_x`, `horizon_y`, `hellmouth` [x, y, r], `fire_pits`.
Sprites: `woofer` (toothed iron ring), `fixture` (a demonic eye-lamp), `disco_ball` (an infernal brazier orb in a cage), `glowstick`
(torch), `door_open` (the gate thrown open on hellfire, iron leaves swung in, a horned arrival, an orange spill on the floor), the deck pieces, and the white lighting sprites (`glow beam spot_pool haze_a haze_b vignette`, `confetti` = ash-embers).
`spot_pool` is the chapter's own: a dimmer centre and a fainter far half than Night One's, because the runtime draws it over the crowd and the
dancer standing in a spotlight must stay lit rather than washed out.

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
| `court` | obsidian court: columns with gold bands, gothic windows, banners, a red runner to a stepped dais with the skull throne and braziers; the polished floor mirrors the columns, braziers and window light and has gold inlay bands (violet, gold, magenta) | horizon 140, floor from y 258, rows 286..438 | `court_throne_aura` (pulse, behind, add), `court_flames` (flicker, behind, add), `court_banners` (sway, behind, mix, pivot at the top), `court_seal` (pulse, behind, add) | `led_screen` (judgement tablet over the throne), `riser`, `disco_ball`, `throne`, `braziers`; no woofers |
| `pit` | lava lake, far-shore fortress and volcano, a bone causeway and two bridges, the stage platform out on the lake: basalt running-bond slabs with hot seams, a lava-lit stone curb round the rim (gaps where the causeway and bridges land) with skull lanterns, the lake glowing and bubbling against it (ember red, orange, bone) | horizon 190, chamfered platform polygon from y 266 (row 0 stays between x 330 and 950, the lake shows at the sides) | `pit_lava_glare` (pulse, behind, add), `pit_plumes_l/_r` (flicker, behind, add; rising out of the lake beyond the rim), `pit_fortress_glow` (pulse, behind, add) | `led_screen`, `doorway` (the bone gate in the left cliff: arrivals cross the left bridge), 4 `woofers` (two amp stacks on the platform), `riser`, `causeway`, `bridges` |
| `furnace` | the great forge: riveted steel hall, pipes, hazard stripes, anvils, molten channels, a glowing coal heap and a pallet of cooling ingots, a huge grinning demon face whose furnace mouth is the screen and throws a warm pool across the steel floor (steel blue, white-hot orange) | horizon 125, floor from y 264, rows 286..438 | `furnace_eyes` (pulse, behind, add), `furnace_ladle` (sway, behind, mix, pivot at the crane chain), `furnace_sparks` (flicker, behind, add), `furnace_channels` (pulse, behind, add) | `led_screen` (the mouth), 4 `woofers` (boiler hatches), `riser`, `face`, `anvils`, `channels` |

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
`crack_segment` (a straight slice to stretch or chain); both have a charred dark lip round the molten core and fade out before the texture
edges, so their glow is never cut off however they are stretched. `flame_jet` (a soft licking flame PNG with two side tongues, 80 x 180
design px, pivot at the base, animate by flip/scale), `portal_vortex`
(512 px red-black swirl, centre pivot), `embers` (4 frames of 32 px), `dark_wash` (red-black full-screen wash, 320 x 180 shown at 4x).
Anchors: `crack_origin`, `crack_end`, `portal_centre`, `flame_jets` (two floor points), and the contract's `ufo_hover`/`beam_floor`
(unused by this chapter, kept for the generic cutscene code). Draw the `blend: add` ones additively.

## Staging (`content/story/underworld.json`)

The camera moves on the block downbeats (bars 17, 33, 49, 57) and every eight-bar block has its own beat. Set pieces are switched in the room
the camera is in (a room's own pieces are ambient; switching them on at the move that enters the room lets later `piece_pulse` events flash
them without a fade-in pop), and the main room's pieces that only matter on the way back (`skull_throne`, `ember_rain`) wait for bar 57.

| bars | room | block | beat |
| --- | --- | --- | --- |
| 1-8 | main | The gate opens | gate doors open, the floor's lava cracks ignite at 3, the first demons arrive at 5, LED and chains at 7 |
| 9-16 | main | The demons watch | the fire pits roar left (9) and right (11), sweeping beams, footwork; the hellmouth opens at 15 with a camera lean |
| 17-24 | court | Through the hellmouth | step through the hell-gate on the bass drop; the court gatherers pour in at 19 (or wait at the side on a cold floor); the throne aura flares at 21 |
| 25-32 | court | The court assembles | warm light, late demons stream in, the seal flares at 29, a push towards the throne before the walk |
| 33-40 | pit | The inferno circle | walk out onto the lava lake; the circle forms at 35, the brazier orb and cool light at 37, more demons cross the bridge at 39 |
| 41-48 | pit | The lake and the bass | the fortress flares, hero to the centre, glow torches, a light wave and haze |
| 49-56 | furnace | Into the forge | turn into the forge on the drop; peak demons, hero solo on the riser, the face's eyes flare at 53 and the channels at 55 |
| 57-64 | main | The final verdict | walk back to the main room, where the skull throne now stands on the risen stage; ember rain with the peak at 59 |

## Chapter `mental_hospital` (assets/story/mental_hospital/)

Build: `python3 tools/story/build_assets.py mental_hospital [chars|stage]` (deterministic; the single regeneration command). Hooked up through
`art/chapter_mental_hospital.py`; the art lives in `art/mh_chars.py` (crowd), `art/mh_stage.py` (shared palette, `Room` perspective class, the room shell
with its shading, a prop library, a stroke font for signs, the day room backdrop, speakers, riser, desk, manifest assembly), `art/mh_sprites.py` (re-themed
deck pieces, props, PNG lighting sprites, silhouettes, interlude), `art/mh_pieces.py` (the `main` pieces) and `art/mh_views.py` + `mh_views_corridor.py` /
`mh_views_art.py` / `mh_views_courtyard.py` (the three extra rooms and `passage_frame`). Everything is drawn by those scripts: no downloads, no outside art.

**Tone.** A kind, whimsical ward: the crowd are affectionate eccentrics in homemade fancy dress (paper crowns, towel capes, tutus, a toy parrot) and nobody is
menacing or the butt of a joke. No restraints, cells or bars anywhere: the interlude "door" is a pastel ward door with a round porthole and paper stars.
Palette: mint and lilac "fluorescent" walls at a mid pastel value (not white: the runtime draws its party light additively, so the walls keep headroom for
coloured light), honey wood, warm accents of mustard, coral, butter and peach; the lighting sprites stay white so the runtime's palettes tint them.

**Runtime lighting, tuned for pale rooms.** `beam` is a slim cone with most of its alpha in the core and a fast falloff (about 40% of Night One's), `spot_pool`
has a dim centre and a soft rim, `haze_a/_b` are thin lilac-grey drifts (a mid-tone veil adds depth instead of whitening the room) and the `vignette` is a gentle
plum. `glow` stays Night One's because the runtime also draws the dancers' contact shadows with it. The chapter's palettes are saturated (`cool` mint/violet,
`warm` amber/rose, `dusk` orange/violet for the courtyard, `rave` mint/rose/gold/violet) so additive light tints the pastel rooms rather than bleaching them.

**Authored past the frame.** Every room's `backdrop` (and `front_frame`) is drawn on a canvas 128 px wider on each side and 32 px taller than the frame
(`mh_stage.BACK_BOX`, layer `pos` (-128, -32), `size` 1536 x 752 / 1536 x 502): the moving camera pans (`camera_look` up to 120 px, far layers at parallax 0.82),
sways and turns, and the extra canvas means no black edge ever shows. Shading in `room_shell`: walls darken towards the camera, soft ambient occlusion in the
inside corners, under the ceiling line and along every wall base, a clipped floor that darkens towards the desk lip so the crowd's feet sit on it.

### Crowd (`archetypes`)

| id | silhouette and costume | variant a | variant b | swinging parts |
| --- | --- | --- | --- | --- |
| `pirate` | stocky; striped breton shirt, red sash, tall turned-cuff boots, eye patch | tricorn hat, brown beard and moustache, patch on the left | red polka-dot bandana, gold hoop, waistcoat, toy parrot on the shoulder, patch on the right | `hat_feather` (a), bandana tails in `hair_back` (b) |
| `king` | short and round; gold paper crown, dressing gown with a tied cord, pyjama legs, fluffy slippers | plum gown, towelling collar, white beard | teal gown, paper-ermine collar, grey moustache, blue-gem crown | none (crown and gown flaps stay put) |
| `chef` | broad with a round tummy; tall pleated toque, double-breasted whites with a wrap panel, mandarin collar, neckerchief, pen in the sleeve pocket, checked trousers, clogs | classic with blue neckerchief and moustache | red trim, blue apron (`torso` + shared hips), no moustache | none |
| `superhero` | tall; domino mask, pyjama top with an emblem, wellington boots, marigold gloves | blue top, star emblem, orange towel cape | red top, lightning emblem, blue towel cape | `cape` (towel cape, `torso` joint, z -15) |
| `ballerina` | slim; leotard, layered tutu on the hips, tiara, hair bun, ribbon shoes | pink, blonde | lilac with gold sequins, dark hair | `hair_back` (the bun) |
| `orderly` | tall and calm; scrubs, chest pocket, lanyard and badge, trainers (the day room's hero dancer) | teal, round coral glasses with clear lenses, curls | lilac, short neat beard | none |

Same rig contract as Night One (joints, part z, four faces, `glow_hand`, the wand `glowstick` sits in the hand). `king` and `ballerina` carry a `skirt` part on `hips`
(gown flaps / tutu); the `pirate` has a sash tail; faces carry the eye patch, mask, moustache or glasses so every expression keeps the costume, and every face has a
faint blush. Rim lights are mint (left) and peach (right). Rear silhouettes (`sil_a` king, `sil_b` chef, `sil_c` pirate with a parrot) are soft lilac and slate
figures with mint and peach rims and a lighter head (the runtime multiplies them by a lilac tint), never black cut-outs.

### Day room (`main`) and sprites

Layers: `backdrop` (ceiling tiles with fluorescent troffer panels, the light washing the top of the far wall, mint far wall and lilac dado, the ward door, two
windows with curtains and radiators, the wall TV and a shelf of board games, left-wall windows with curtains and radiators and their light across the floor, right
wall pictures, a checkered vinyl floor with the windows mirrored in it, a round rag rug under the dance circle, two mismatched armchairs, plants, a side table and a
lit floor lamp), `riser` (a low wooden talent-show platform with bunting), `speaker_l/_r` (wooden hi-fi cabinets), `desk_top` (teal formica with sticker doodles).
Anchors as the other chapters (`led_screen` = the wall TV, `doorway` = the ward door, 5 floor rows, 4 woofers, 8 light points, `circle_centre`/`circle_radii` match
the rug). Pieces (`pos`/`size` design px, `pivot` design px relative to `pos`):

| id | anim | z | blend | pivot | what |
| --- | --- | --- | --- | --- | --- |
| `notice_board` | none | behind | mix | - | cork board with notes on the far wall |
| `mood_lamp` | pulse | behind | mix | lamp glass | lava lamp on a round side table |
| `bunting` | sway | behind | mix | top centre | three strings of paper pennants |
| `craft_table` | none | behind | mix | - | table of paint pots, paper, brushes |
| `wall_clock` | none | behind | mix | - | clock over the door |
| `paper_chains` | sway | behind | mix | top centre | swags of paper chain with stars |
| `fairy_lights` | flicker | behind | add | centre | two strings of fairy lights |
| `window_light` | pulse | behind | add | centre | sunbeams from the left windows onto the floor |

Re-themed sprites: `woofer` = radio cone, `fixture` = lilac clip-on spotlight, `disco_ball` = pastel glitter ball on paper-chain links, `glowstick` = foil star wand,
`door_open` = the ward door open onto the bright corridor (an orderly with a tea trolley arriving), `confetti` = pastel paper confetti (rectangle, punched circle,
star, streamer curl), deck pieces = Night One's drawn through a hue remap (indigo to teal, cyan to mint, magenta to coral).

### Extra views (`stage.views`) and `passage_frame`

Each view has `backdrop` + `front_frame` (z front) layers authored past the frame, the required anchors, 3 pieces and `palette_hint`.

| view | place | pieces (anim, blend) | notes |
| --- | --- | --- | --- |
| `corridor` | long corridor of honey parquet and mint walls, painted doors with paper stars and portholes, hand rails, tea and laundry trolleys, glazed garden doors at the end | `corridor_tubes` (flicker, add), `corridor_end_glow` (pulse, add), `star_garland` (sway) | `palette_hint` cool; `doorway` = the garden doors at the far end (the ward pours out of it on a good morning meeting), `disco_ball` under the garland; front frame = lowered bulkhead with paper stars and two door-frame pillars |
| `art_room` | warm peach studio: ash boards with paint splats and a rumpled drop cloth, beams and skylight, north-light window over a counter of jars, shelves with a boombox, kiln, easels, a painting gallery, a pale blue door with a palette sign | `kiln_glow` (flicker, add), `hanging_paintings` (sway), `skylight_beam` (pulse, add) | `palette_hint` warm; `doorway` = the left-wall door (late arrivals and the gatherers), `disco_ball` under the skylight, `woofers` = the boombox's two cones |
| `courtyard` | walled garden at dusk: deep blue to peach sky with stars and a moon, dusky brick and ivy, the ward building with warm lit windows, dusk paving with warm light pools, raised beds, bench, water butt, the gate (`doorway`) with a lit lantern, and a pallet stage under a hand-lettered TALENT SHOW banner | `string_lights` (flicker, add), `washing_line` (sway: bunting plus a stripy shirt, towel cape, tutu and paper crown), `fireflies` (pulse, add) | `palette_hint` dusk; `riser` = the pallet stage (the hero's solo spot, no lift); light points hang from the festoon cable; front frame = the two cable posts and foreground foliage |

`passage_frame`: a ward door frame (pastel wall panels with a lilac dado, a white timber arch, paper stars), 640 x 360 design px at px_scale 0.5, centre pivot, scale 2x to span
the frame, arch opening 300 wide with the apex at y 36 transparent.

### Staging (`content/story/mental_hospital.json`)

The camera moves on the block downbeats 17 (step through the ward door into the corridor on the bass drop), 25 (turn right into the art room), 41 (walk out into the
garden) and 57 (turn left back to the day room); each room brings its own palette (`palette_hint`). Every eight-bar block has its own beat:

| bars | room | block | beat |
| --- | --- | --- | --- |
| 1-8 | main | The day room | the ward door opens on an orderly with the tea trolley, morning sun from the windows, the mood lamp at 3, early arrivals and the craft table at 5, the TV wakes and the fairy lights come on at 7 |
| 9-16 | main | Morning meeting | cool light and a clap (or a look round), bunting and sweeping beams at 11, footwork and paper chains at 13, a lean towards the door at 15 |
| 17-24 | corridor | Down the corridor | step through on the drop; the decision: the whole ward pours out of the garden doors (or a few hang back); a wave and the star garland at 19, a look right and the end glow at 21, a follow spot sweeps and the tubes flare at 23 |
| 25-32 | art_room | Art class | turn into the warm studio with late arrivals at the door, the kiln glows at 27, crossing beams and the gatherers (or they wait at the door) at 29, a push in on the skylight beam at 31 |
| 33-40 | art_room | The easel circle | the art-class decision (a masterpiece and a spotlit cheer, or a giggling scatter), the circle forms at 35, the glitter ball under the skylight and a look left at 37, the paintings swing at 39 |
| 41-48 | courtyard | Into the garden | walk out at dusk with late arrivals, glow wands and the hero into the circle at 43, a light wave over the string lights at 45, fireflies and haze at 47 |
| 49-56 | courtyard | The talent show | the drop decision and the last arrivals with a push in, the hero's solo in front of the pallet stage at 51, rave light and the washing line at 53, a clap at 55 |
| 57-64 | main | Lights out | turn back to the day room: the hero walks to the talent-show riser, which rises at 58, the rave peak at 59, hands up, confetti and a push at 61, crossing beams and paper chains at 63 |

### Interlude (`interlude`) and the `sectioned` cutscene

Sprites: `fluoro_wash` (320 x 180 PNG at px_scale 4, cold mint-white, faint tube banding), `tunnel_vignette` (640 x 360 PNG at 2: clear centre closing to deep
teal), `cell_door` (the ward door, frame + leaf, 320 x 440 design px, pivot at the door's foot; companions `cell_door_frame` with a transparent opening,
`cell_door_leaf` with a hinge-foot pivot to scale in x, `cell_door_open` the leaf swung inward) and `flicker_tube` (a fluorescent tube, additive). Anchors:
`door_centre` (the door's foot), `door_opening`, `tube_row`.

The cutscene (`content/story/interludes.json` `sectioned`, drawn by `StoryInterludeFx._draw_sectioned`, 16 s over the room just left): the music stops and the
crowd fades (0-4 s), a soft tunnel closes in and breathes (drifting off, 1.6-5.2 s), plain cold light floods back as the tunnel opens and three tubes blink on one
after another with two gentle dips each (6-8.6 s), the ward door fades in (9.2 s), swings open onto the day room, which is the chapter's own backdrop seen through
the opening with warm light spilling out (10.6-12.2 s), and the camera walks through it until the room fills the screen (12.6-15.2 s), then a short soft
mint-white fade hands over to the chapter. Captions stay kind: "The music stops." / "Everything goes soft, and very quiet." / "Then a light. A very bright, very plain
light." / "'There you are, love. Welcome back to the ward.'" / "None of it happened. Or did it? Come and meet everyone." The ward door stands in a mint wall
with a lilac dado on a pale floor while it is small, so it never floats in the light.

Review frames at a frozen cutscene time (the live scene's clock is wall time, so slow first frames run it ahead):
`RW_T=11.4 RW_FROM=underworld|mothership|night_one godot --path . -s tools/shoot.gd -- res://tools/story/preview_sectioned.tscn <out> 12:shot:name`
(`tools/story/preview_sectioned.gd` replays the scene-side events, dim, fade_crowd and captions, up to `RW_T`, then draws the fx at that time).

### Reviewing

`tools/story/shoot_mh.sh <main|corridor|art_room|courtyard> <stage|stage_low|set|pieces|chars|chars_b|close|sil|deck|passage|interlude|interlude_flood> [out_dir]`
(on `preview_mh.gd`, which extends `preview_chapter.gd` with the chapter's own interlude sheets). `close` takes `RW_ARCHS=pirate,king,chef RW_VARIANT=b`. For the
real runtime look use the single-shot pattern of `tools/story/capture.sh` with `RW_STORY_CHAPTER=mental_hospital` (bars 3, 12, 17.6, 22, 25.9, 28, 36, 41.9, 44,
52, 57.9, 60 and the endings at 67 with the `perfect`, `sloppy` and `none` policies, plus `RW_REDUCED=1` / `RW_HIGH_CONTRAST=1`).

# Story Campaign art: the Hospital chapter (`hospital`)

You wake in a hospital bed in a sunny private room with your family around you. Same contract as the other chapters (rig, faces,
`stage.sprites` ids, 1280 x 720 design space, `stage.pieces`, `stage.views`, `passage_frame`, `interlude`), re-skinned to warm, soft, golden and teal
daylight: apricot wallpaper, a teal dado, honey floorboards, wooden furniture, paper cards and balloons. Original art drawn by the generator, no
downloads. `python3 tools/story/build_assets.py hospital` writes `assets/story/hospital/` (about 230 SVG, 13 PNG, `manifest.json`), deterministically.
Code: `tools/story/art/hp_chars.py` (visitors), `hp_stage.py` (the main room, sprites, silhouettes, interlude), `hp_props.py` (perspective `Room`, floors,
plants, bunting, balloons, the `grade` and `overscan` helpers ...), `hp_views.py` (+ `hp_view_corridor.py`, `hp_view_cafeteria.py`, `hp_view_garden.py`, the
stroke-font signs and `passage_frame`).

**Light and tone (read this before touching colours).** The runtime draws beams, floor glow, spot pools and blooms *additively* over the room, and a bright
cream room turns white under them. So the rooms are painted in mid tones and graded: `hp_props.grade()` is drawn last over every backdrop and lays a warm
shadow (`#5a2f3a`) over the near floor, the ceiling and the side edges, so the dancers stand on a mid-tone floor and the lit middle distance carries the
brightest values. The chapter has its own lighting sprites (`hp_stage.build_light_sprites`): a `beam` that is a soft shaft of sunlight with dust motes
(about 40 % of Night One's light), a dim warm `spot_pool`, and a thin warm dust `haze_a/b`; `glow` stays Night One's (the crowd's contact shadows use it).
Glow pieces (`window_sunbeams`, `corridor_lights`, `corridor_doorglow`, `cafeteria_sun`, `garden_sunrays`, `garden_spray`) are kept faint for the same reason.
The palettes in `content/story/hospital.json` are saturated (amber, coral, teal, periwinkle) rather than pastel, and each room has its own:
`ward` (corridor), `tea` (cafeteria), `golden` (garden), picked up through the views' `palette_hint` when the camera arrives.

**Overscan.** Every full-width room layer (`backdrop`, `front_frame`, in every room) is written 150 design px wider on both sides (`hp_props.overscan`,
`room_layer`): the strips beyond the frame repeat the frame's edges mirrored, through `<use>` so the files barely grow. A `camera_look`, the walker's sway or a
turn never shows the void at the screen edge. Layer `pos` is therefore `[-150, 0]` and `size` `[1580, h]`.

## Visitors (`archetypes`)

`mum` (long wavy hair that swings or a bun with a headband, floral dress + cardigan or polka-dot dress + scarf), `dad` (stubble beard, plaid shirt with rolled
sleeves, or glasses and a knitted argyle vest), `granny` (white or lilac-rinse curls with a bun, round glasses, cardigan, long skirt, brooch or pearls),
`kid` (small, big head; a girl with swinging pigtails in dungarees, or a boy in a cap and shorts; a balloon on a string tied at the shoulder is a swinging
`balloon` part on `torso`), `nurse` (scrubs, a heart ID badge, a folded nurse's cap with a bun, or a printed scrub cap), `doctor` (white coat with coat tails
part on `hips`, stethoscope, head mirror and glasses, or a curly puff with a red headband). Variants `a`/`b` differ in palette, hair and a clothing detail.
Things held in the left hand (`hp_chars.hand_prop`, drawn into the left forearm so they swing and wave with the arm): dad a brings flowers in a paper cone,
dad b a gift box with a bow, doctor a a clipboard, granny a a walking cane she waves above her head when she cheers. The right hand carries the
`glowstick` (a white heart wand). Heights: kid 203, granny 245, mum 258, dad 269, nurse 270, doctor 280. Rig, parts, `z` and faces exactly as Night One;
warm gold / coral rim lights replace the neon rims. Swinging parts (`swing: true` with `swing_pivot`): mum's hair (back), pigtails, nurse's bun, the kid's
balloon.

## The main room (`stage`)

One-point perspective, vanishing point (640, 130), far wall 270..1010 x 52..262 (same rows and scales as Night One: feet rows y 286..438). The bed stands
against the far wall (head board, patchwork quilt, pillows, teddy, heart cushion), bedside cabinets with a lamp, a door at the left of the far wall
(`doorway`), a tall sunny window on the right wall, a notice board on the left wall, the information board over the bed is the `led_screen`. Floor: honey planks
with a woven oval rug in the dance circle. Layers: `backdrop`, `riser` (a low wooden step with a striped rug), `speaker_l/r` (wooden hi-fi cabinets,
woofer cones drawn by the runtime), `desk_top` (the over-bed table: wood grain, cream pad wings, a teal mixer). Sprites: `woofer` (cream paper cone), `fixture` (brass
spotlight), `disco_ball` (a paper-star lantern on a long ribbon; pivot where the ribbon meets the lantern, so the main room hangs it low at (640, 118) in front of the
bed head and clear of the information board, the garden and cafeteria hang it from the top), `glowstick` (heart wand), `door_open` (the door thrown open, a visitor
with a balloon arriving), `pad_bezel`, `platter` (a record with a heart label), `knob`, `fader_slot/cap`, `crossfader`, `vu_segment`, `deck_screw`,
`desk_lip_glow` (warm gold), `glow`, `beam`, `spot_pool`, `haze_a/b`, a warm `vignette` and paper/petal/heart/star `confetti`. Silhouettes: a mum with a bun and a
bouquet (`sil_a`), a dad (`sil_b`), a kid with a balloon (`sil_c`), warm plum with gold and coral rims.

Pieces (`pos`/`size` top-left in design px, `pivot` relative to `pos`; `behind` = under the crowd):

| id | anim | z | blend | what |
| --- | --- | --- | --- | --- |
| `window_sunbeams` | pulse | behind | add | slanting rays from the window across the floor, dust motes |
| `fairy_lights` | flicker | front | mix | two swags of coloured bulbs across the top (clear of the lantern) |
| `balloon_bunch` | bob | behind | mix | six balloons on a gift weight, left corner, pivot at the weight |
| `cards_garland` | sway | behind | mix | thirteen get-well cards pegged on a string above the bed |
| `heart_monitor` | pulse | behind | mix | a friendly monitor with a green heart trace on the right bedside cabinet |
| `flower_vase` | sway | behind | mix | a bouquet on the left cabinet, pivot at the vase foot |
| `paper_stars` | bob | behind | mix | eight folded paper stars hanging from the ceiling either side of the lantern |

## Extra views (`stage.views`) and `stage.sprites.passage_frame`

Route: main -> corridor -> cafeteria -> garden -> main. Each view has a `backdrop` and a `front_frame` (`z: front`, 470 high) layer (both overscanned), the
required anchors (5 floor rows with front scale 1.0 and feet y <= 440, `floor_polygon`, `floor_grid`, 8 `light_points`, `circle_centre`/`circle_radii`, `vanish`,
`horizon_y`, `wall_left_x/right_x`) and the optional ones that the room has (`led_screen`, `doorway`, `disco_ball`).

| view | place | floor and footing | pieces |
| --- | --- | --- | --- |
| `corridor` (vanish 640,205, palette `ward`) | long ward corridor: teal doors with paper hearts and notice boards, a parked wheelchair and a hand-gel station on the left, tall windows with a row of waiting chairs (and a forgotten balloon) on the right, a nurses' desk, water cooler and glass doors to the garden at the far end, hanging WARD / CAFE signs in the front layer | warm caramel tiles, coral and teal way-finding lines | `corridor_banner` (sway, a GET WELL SOON banner), `corridor_lights` (pulse, add, troffer glow), `corridor_doorglow` (pulse, add) |
| `cafeteria` (vanish 640,190, palette `tea`) | family lounge: servery counter with tea urn and cakes, a coral vending machine, tea trolley, tables and chairs, windows onto the garden, a door back to the corridor, an armchair and a table in the front layer | coral and caramel chequered lino with a mint ring for the circle | `cafeteria_lamps` (sway, pendant lamps), `cafeteria_steam` (flicker, add), `cafeteria_vending` (flicker, add), `cafeteria_sun` (pulse, add) |
| `garden` (vanish 640,195, palette `golden`) | sunlit courtyard at golden hour: the ward's brick wing with a WELCOME HOME banner, a tiered fountain, benches, lantern posts, hedges, ivy walls; a pergola with vines and sunflowers in the front layer | sandstone paving with a mosaic ring, grass verges | `garden_spray` (pulse, add), `garden_sunrays` (pulse, add), `garden_bunting` (sway, front), `garden_petals` (bob) |

`passage_frame` is a papered wall with a teal dado, falling into a warm shadow round the doorway, a wooden architrave with a heart keystone, a bunting swag and
balloons, 640 x 360 design px (scale 2x), centre pivot, the arched opening (300 wide, apex y 36) transparent. The opening is cut by winding it the other way
round inside the slab path: ThorVG ignores `clip-rule` inside a `clipPath`, so an even-odd clip left the wallpaper stripes painted across the opening.

## Interlude (`interlude`) and the `awakening` cutscene

Sprites for the waking cutscene over the previous chapter's room: `eyelid_top` (pivot bottom centre = the closing edge, 1280 x 520 design px at px_scale 2: deep
plum at the outer edge warming to rosy red near the edge where daylight shines through, a soft crease, a dark lash line and long tapered lashes curling out from the
middle) and `eyelid_bottom` (pivot top centre, short sparse lashes); `white_wash` (320 x 180 at 4x, warm white); `monitor_line` (a 1024 px heartbeat trace,
kept for compatibility); `waking_view` and `waking_blur` (640 x 360 at 2x: what the opening eyes see, the family leaning in over the bed against the sunny
window with fairy-light bokeh, nearly in focus and completely out of focus). Anchors `eyelid_seam`, `monitor_line`.

`StoryInterludeFx._draw_awakening` (timeline in `content/story/interludes.json` `awakening`): it lays everything out on the screen whatever the cutscene stage's
fit. The dream room warms behind a thickening veil while faint beeps light it; the lids close in two drowsy blinks (`eyelids_close`); in the dark a phosphor ECG
sweep (`monitor`) runs left to right with a fading tail, each spike landing on a heartbeat whose rate climbs from 56 to 92 bpm as you come round (a closed-form beat
phase, shown on a BPM readout), and the light through the lids swells on every beat; the eyes flutter open (`eyelids_open`: a crack of light, shut again, open)
onto the family, overexposed and blurry, pulling into focus; then the morning floods in (`white`). Reduced effects: one smooth close and open, no flashes, a steady
glow.

## Staging (`content/story/hospital.json`)

56 bars. The camera moves on block downbeats (bars 17 step, 25 turn right, 33 walk, 49 turn left); every eight-bar block has its own beat. The crowd is
family and staff only, ten per room plus arrivals; the private room's rear crowd stands at the sides, clear of the bed.

| bars | room | block | beat |
| --- | --- | --- | --- |
| 1-8 | main | Waking up | sunbeams and the heart monitor at 1, the door opens at 3, the first visitors come in with the balloons at 5, the information board, flowers and a heart flutter at 7 |
| 9-16 | main | The family gathers | warm light, fairy lights and clapping at 9, sweeping lights and the cards garland at 11, footwork and paper stars at 13, the sun swells and the camera leans towards the door at 15 |
| 17-24 | corridor | Down the corridor | step through the door on the bass; visiting-hours decision; a wave at 19, the garden doors glow and the camera glances along the windows at 21, a spotlight sweep and more family at 23 |
| 25-32 | cafeteria | Tea and biscuits | turn into the lounge; the gatherers come in (or wait at the door) at 27, crossing lights and clapping at 29, a push towards the garden at 31 |
| 33-40 | garden | Out into the garden | walk out into the courtyard; the circle forms at 35, the lantern lights, the fountain bursts and the circle decision at 37, late arrivals at 39 |
| 41-48 | garden | Golden hour | the big-song drop decision and a push in at 41, heart wands and the hero to the centre at 43, a light wave (and the win-back) at 45, everyone else arrives at 47 |
| 49-56 | main | Going home | turn back into the room; the kid climbs the step for a solo at 51, the peak at 53, the kid steps down and hands go up (confetti at the top) at 55 |

## Preview

`tools/story/shoot_hp_run.sh <out> name:policy:bar[:ENV=V,...] ...` takes real screenshots of the running chapter (virtual clock, scripted input); `tools/story/capture.sh` is the maintained way.

## 2.5D texture tiles and the world (every chapter)

The Story Campaign plays in a 2.5D world (docs/STORY_25D_PLAN.md); the painted 1280 x 720 rooms of the first version are no longer drawn, but their SVG art is still the
source of everything the world shows:

- `assets/story/<chapter>/textures/*.png` (square 64 or 128 px; `thing_*` are RGBA billboards; `sky_*` are 256 x 64 strips that wrap once round the world; listed with their size and
  metres per repeat in the manifest section `textures`) are cropped out of the chapter's own SVGs by `tools/story/bake_tiles.gd` (headless Godot: `Image.load_svg_from_string`, crop, resample).
  The recipes are the methods `_night_one()`, `_mothership()`, `_underworld()`, `_hospital()` and `_mental_hospital()` (crops are in design space; the hospital and ward backdrops are wider
  and offset, see the notes in their recipes). Where the art has no counterpart (toilets, medical bay, treatment room, quiet rooms, the skies, the cage) the tile is a palette fill or a
  tinted copy of a crop. The metres per repeat of each tile live in `tools/story/art/tiles.py` (`SPECS`).
- `python3 tools/story/build_assets.py <chapter> tiles` rebuilds only a chapter's tiles and its manifest section (set `GODOT=` if the binary is not in `~/godot`); a full chapter build does it too.
  Run `godot --headless --path . --import` afterwards so the new PNGs get their `.import` files. `check_assets.py --determinism` checks the tiles and that a rebuild is byte-identical.
- Set pieces (the manifest `stage.pieces` and each room's `pieces` under `stage.views`) are drawn as billboard things in the world: a map thing with `"piece": "<id>"` shows that SVG
  while the chapter's `piece_on` / `piece_off` / `piece_pulse` actions say so (blend and animation follow the manifest entry).
- The manifest no longer carries what only the 2D rooms read (`stage.anchors`, each view's layers, anchors and palette hint); `build_assets.py` strips them and `check_assets.py` rejects them.
  The art files themselves (backdrops, front frames) are kept: they are the tile sources and the Story Campaign menu's thumbnails.
- Rooms, doors, heights, props and light live in `content/story/maps/<chapter>.json` (see the handover). Review the tiles of a chapter at a glance with a contact sheet of the PNGs.

### WP9 additions (layouts, lights, activities)

- New tiles (recipes in `tools/story/bake_tiles.gd`, metres in `tools/story/art/tiles.py`): `thing_chair` (hospital, ward), `thing_bench` (hospital), `thing_column` and `thing_anvil` (underworld), all RGBA billboards
  cropped or redrawn from the chapter's own art. Night One, the Mothership's medical bay and the Ward's quiet room reuse existing tiles.
- Things may use any map texture or manifest sprite as their `sprite`; lights (`"kind": "light"`) need no art and are baked into vertex colours (docs/STORY_CAMPAIGN_HANDOVER.md, "WP9 additions").
- Held props and the phone's light, the seat under a sitter, the sleeper's Zs and the drip stand are drawn with plain shapes in `StoryCharacter._draw_held`: placeholders for the polish pass.
- Dancer parts are packed into a runtime atlas (`StoryAssets.build_rig_atlas`); the SVG parts are unchanged on disk.

## The people: wardrobe and baked sprite sheets (polish, art direction 2.E)

Every actor of every chapter is drawn as an individual and baked to their own pixel sprite sheet; the SVG rigs above remain on disk as the live rig
(`RW_STORY_RIG=1` draws everyone with it, and anything without a sheet falls back to it) and their poses are the bake source.

- **Wardrobe** (`tools/story/art/wardrobe.py`): `cast_chapter(chapter, actors)` dresses each actor from a seed of chapter and id. A spec has a build (height 0.9 to 1.1,
  kids about 0.65; width slim to broad; a curve from straight to curvy), skin (eleven tones), hair (short, curly, afro, locs, braids, long, wavy, bob, bun, ponytail,
  pigtails, buzz, shaved, mohawk, spiky, quiff, perm; natural or dyed colours; a parting), face (eyes open or closed and lost in the music, stubble, beard,
  moustache, glasses or shades, freckles, blush), a top (tee, tank, crop, long sleeve, jumper, hoodie, shirt, polo, scrubs, jumpsuit, dress, gown, chef's whites,
  leotard...) with a pattern (plain, a chest print from eight motifs, stripes, vertical stripes, a band, check, dots, tie-dye, an emblem, a skeleton's ribs), an outer
  layer (open jacket or check overshirt, gilet, cardigan, coat, a long white coat, a robe with fur trim, a cape), bottoms (jeans, baggy, flares, trousers, shorts,
  skirt, dungarees, leggings, pyjamas, a tutu, a gown's bare legs), shoes, a hat (cap, cap backwards, bucket, beanie, crown, chef's hat, bandana, tricorn, scrub cap,
  headscarf, party hat) and accessories (bag strap, bracelet, watch, necklace, headphones round the neck, lanyard, stethoscope, belt, sash, scarf, bow tie, eyepatch,
  mask, harness, shoulder plates). Chapter wardrobes: the ravers (a 90s rave palette; the archetype only biases hair and hoodie); the Mothership's species keep their
  archetype (grey, antenna, blob, insect, cyclops, tentacle: head shape, eyes, antennae, wing cases, tentacles) in space suits; the Underworld's demons (horns small,
  big, ram or long, bat wings, tails, pointed ears, bare chests with harness or plates, skeletons with ribs, flame hair, queens with capes and crowns); the
  Hospital's mums, dads, grannies and kids in visitors' clothes, nurses in scrubs, doctors in white coats, and a patient in a gown (anyone with the drip or lying);
  the Ward's residents in homemade fancy dress (pirate, king, chef, superhero, ballerina) and staff in institutional green. Ravers who came along (`art: night_one`)
  keep the raver wardrobe. **Rule**: no two actors in one room share build, hair and top (`look_key`); a clash re-rolls deterministically; `check_assets.py` checks it.
- **Pixel rig** (`tools/story/art/people.py`): a skeleton with the head about a seventh of the height, real shoulders, hips, hands and feet, posed by the live rig's
  limb angles, rasterised straight into pixels at the sheet size (numpy; no vector scaling). Each part is shaded as a rounded form in three steps (dark, mid, lit,
  light from the upper left) with an ordered dither between them, a one-pixel darker edge of the local colour on the silhouette (never black), a one-pixel shadow
  where a part overlaps another, folds on cloth, strands in the hair, curls in curly hair. Three facings: front, a three-quarter turn (the runtime mirrors it for the
  other side) and back (the back of the head, the back print). Props are drawn in the hand: a plastic pint (amber with a head), a water bottle, a mug, a tray of
  glasses, a phone (its screen emissive), a clipboard, tickets, a brush, a sketchbook, a drip stand with its bag and line, headphones over the ears for a DJ and,
  for the Mothership's DJ, worn the wrong way (one cup on the forehead, one under the chin, the band across the face). Sitters get a seat, the lying a bed sheet.
- **Poses**: `tools/story/dump_poses.gd` (headless Godot) samples `StoryCharacter.sample` over one cycle of every state (`StoryCharacter.SHEET_CYCLES`: beats and frames
  per state, 4 to 16 frames; the dance once per personal style) into `assets/story/people_poses.json`. So the sheets and the live rig share one set of poses.
- **Sheets** (`tools/story/art/people_sheets.py`, `python3 tools/story/build_assets.py <chapter> people`): for each actor the states the runtime can show them in
  (computed as `StoryCrowd.pick_activity` picks, plus the dance set on dancing sectors, the walk, the look, the hero's five dance styles), each in the facings it
  needs (the walk in all three, the paired activities from the side, the targeted ones from the side and the back) and three levels of detail drawn at their own
  sizes (full: a build-1.0 adult stands 112 pixels; half; quarter). Identical frames are stored once. Output in `assets/story/<chapter>/people/`: `page_<n>.png`
  (2048 square, 8-bit: a pixel is material << 2 | shade step, +128 on the rim, 0 transparent), `palette.png` (one row of 32 materials x 4 steps per actor) and
  `people.json` (the frame table and per actor `{row, style, height, look, states: {state: [beats, frames, front, side, back]}}`). Sizes: Night One 43 actors in
  3.4 MB on disk; the other chapters 116 to 118 actors in 9 to 10 MB (16 to 19 pages, about 60 to 70 MB of 8-bit texture in memory while the chapter plays).
  Building a chapter takes one to three minutes on four cores.
- **Runtime**: `StoryPeople` (src/story/story_people.gd) loads a chapter's sheets once (pages as R8 textures: the compatibility renderer does not hand an imported
  L8 texture's value to a shader as is). `StoryCharacter` draws one frame of its sheet (`sheet_pick`, `sheet_frame`: the state's cycle shifted by the person's own
  phase, whole beats for the kick-locked states) with the live sample's bounce, jump, sway and squash applied, nearest-filtered; the glow stick, the sleeper's Zs and
  the phone's glow are a child node. `StoryCrowd` sets the facing from where the person walks or looks (a partner, a target, the crowd for a DJ: seen from the booth
  the DJ shows their back) and feeds `src/story/story_people.gdshader`: the palette colour lit by the light the person stands in (the sector's song-time light times
  the lamps around them, `StoryWorld.figure_light`), faded towards the chapter's fog with distance (from 5.5 m, full at 17 m) with a rim of the room's light, so the
  back rows read as darker, bluer silhouettes.
- **Review**: `python3 tools/story/figure_sheets.py [chapter]` writes `docs/shots/story/figures_<chapter>.jpg` (every actor at front-row size, unlit, beside a crop of
  pixelexample/Rave.png at the same pixel scale). `check_assets.py` checks every actor has a sheet with its states, frames inside pages, a palette row, a sensible
  height and the room rule.
- **Changing a look**: edit the chapter's function in `wardrobe.py` (or `people.py` for drawing), then `python3 tools/story/build_assets.py <chapter> people` and
  `godot --headless --path . --import`. Changing a pose in `StoryCharacter.sample` or a cycle in `SHEET_CYCLES`: rerun `dump_poses.gd` first.

## Acting: fourteen faces and fifteen directed acts (docs/THREE_PATHS_AND_FACES_PLAN.md 2.1 and 2.2, stage 1a)

- **Faces** (`people.FACES`, `StoryCharacter.FACES`): the crowd's `neutral`, `happy`, `cheer`, `sad` and ten acted ones, `fear`, `anger`, `plea`, `doubt`, `relief`, `awe`, `grief`, `laugh`,
  `resolve`, `shame`. They are drawn on the person's own face traits (`Painter.act_eye`, `act_brow`, `act_mouth`, `act_cheeks`; `act_small` at the half level of detail, where an eye is one
  pixel and the brows' slant, the eye's height and the mouth's shape carry the feeling). The species keep their vocabulary: a skeleton's jaw drops (fear, awe, laugh), clenches (anger) or
  hangs (grief) while its sockets widen or narrow; a grey's eyes go wide with catch lights or narrow to slits; the cyclops's one eye is lidded or ringed with white and its brow slants; an insect's
  compound eyes grow, slant or sag and its mandibles open, clamp or droop; a blob's round eyes and wide mouth do the same; a brute's anger bares its teeth. The quarter-size head has only the
  four old faces: `people.LOD4_FALLBACK` maps each acted face to the nearest (fear, anger, plea, grief, shame to sad; doubt, resolve to neutral; relief to happy; awe, laugh to cheer).
  The four old faces are drawn exactly as before. Hair or a hat brim that covers the brows hides them (as before); the eyes and the mouth carry the face for those people.
- **Acts** (`StoryCharacter.ACTS`): `beckon`, `nod`, `shake_head`, `recoil`, `bow`, `kneel`, `offer`, `plead`, `collapse`, `salute`, `block`, `cover_face`, `stamp`, `laugh`, `write`; each a state with a
  pose in `sample()`, a cycle in `SHEET_CYCLES` and a default face in `FACE_OF`. They start on the bar (bar-locked like the flair moves). The pixel rig is 2D, so a forward bend is the pose key
  `fwd` (0 to 1): the three-quarter view leans into the turn, the front and back views shorten the trunk and sink the head; hands raised to the face are the forearm folded up from a hanging arm
  (since visual polish 2, docs/HANDOVER.md A13, `Body._hands_to_face` puts both hands over the face for the front and three-quarter views and `Body._one_knee_down` gives `kneel` its one-knee-down legs). `point`, `stare` and the other
  old states take a face parameter too and keep their own default faces; `look_at` on `point` is the existing `toward` (stage 1b resolves a target id into it: `StoryCrowd.look_point`, see `docs/CONTINUOUS_RUN.md` "Acting in the run").
- **Which people are baked in which acts** (`tools/story/art/directed.py`): only the directed people, never the whole crowd, and since stage 1d **exactly what the story uses**: the list is derived from the `acting` blocks of
  `content/run/hotspots/*.json` and the `cast` lines of scenes and cinematics in `content/run/run.json` (both authored in `tools/run/acting_data.py`, see `docs/CONTINUOUS_RUN.md` "Acting in the run"). `content/story/directed_actors.json`
  is the hand-kept extras file and ships empty (stage 1a's proof actors with every act and face are gone; entries may be `act`, `act@face` or `act@face:front+side`). A face other than the act's own
  default is a separate frame set named `act@face` in `people.json` (`beckon@plea`); `StoryCharacter.face_override` picks it in `sheet_pick`. Frames are shared through the usual dedupe.
  `check_assets.py` fails when a directed person lacks an act, a face or a facing, when a state names an unknown face, or when `people_poses.json` and `people.py` disagree about the faces and acts;
  `tests/test_story_acts.gd` fails when anything directed is not baked or anything undirected is.
- **Proof**: `python3 tools/story/face_sheets.py acting` writes `docs/shots/faces/<chapter>_acting.jpg`: each directed person's faces (front, three-quarter, half size) cropped from the
  built sheets, then their acts (the middle frame of each cycle, front and three-quarter). The committed images are stage 1a's (the proof actors that wore every one of the fourteen faces and fifteen acts, since removed
  from the sheets); with the stage 1d data the sheet shows only the faces each directed person really wears, about 30 people per chapter (3 MB a chapter, so it is not regenerated into the repo). The stage 1d proof is
  `docs/shots/acting/` (`bash tools/run/capture.sh --acting`).
- **Rebuild**: edit poses in `StoryCharacter.sample`, rerun `godot --headless --path . -s tools/story/dump_poses.gd`, then the five `build_assets.py <chapter> people` commands, as in `docs/FACE_POLISH.md`.

## The pixel look of the rooms (polish, art direction 2.D)

- `tools/story/art/pixeltex.py`: tileable procedural textures drawn in numpy at tile size and quantised to a chapter palette ramp with 8x8 ordered dithering (bricks
  and mortar, glazed tiles and grout, grime and drips, rust, riveted panels, trusses, pipes, cables, blinds, planks, checker, lava). Each chapter's
  `tools/story/art/tex_<chapter>.py` composes them; `tiles.build` writes its tiles after the Godot bake (an id the bake also makes is replaced; a new id is added).
- The post-process has an optional ordered dither and a palette clamp from the chapter's fog colour (the "Story pixel dithering" setting, on by default, off with
  reduced effects).

# Story art: the maps of the three paths (`gospel`, `squadron`, `ember`; stages 3 to 5 of docs/THREE_PATHS_AND_FACES_PLAN.md)

Eleven maps in all (the plan counted twelve: the Mission Count's night bomber is a room of its `airfield` map, not a map of its own). All of it is original and drawn by code, seeded and byte-identical on a rebuild; no
downloaded or published art, no text anywhere (the only glyphs are the painted digits of the Mission Count's boards), no emblem of any real force or book. None of them has an SVG rig: a path map is `assets/story/<map>/`
with `manifest.json` (`textures`, `people`, `borrow_sprites: true` where the path uses Night One's light and deck sprites), `textures/*.png` (surfaces as 64 px tiles, props as 128 px billboards, a few wide props
256 x 128, skies 256 x 64) and `people/` (the baked sheets). The map is `content/story/maps/<map>.json` and its chapter data (actors, groups, palettes; `run_only`, so these are **not** chapters of the Story chapters
menu) is `content/story/<map>.json`; a path's run.json names it per world with `"story": "res://content/story/<map>.json"` (`RunPlay._story_entry`). Where the engine needed new map features they are listed in
`docs/CONTINUOUS_RUN.md` "Paths": set pieces (a thing with `"piece": id`), sector `sky` and `fog`, the cast lines `piece` and `hide`.

| Path | Map (world) | Built by | Rooms (views) |
| --- | --- | --- | --- |
| gospel | `galilee_shore` (`jordan`), `hillside` (`galilee`), `bethany` (`road`), `jerusalem` (`jerusalem`) | `python3 tools/story/build_gospel_art.py --people` (`gospel_maps.py`, `gospel_tex.py`, `gospel_things_a.py`, `gospel_things_b.py`, `wardrobe.gospel()`) | 17 views |
| squadron | `airfield` (`base`, `air`), `city` (`city`), `harbour` (`escape`) | `python3 tools/story/build_assets.py airfield\|city\|harbour` (maps: `tools/paths/squadron_{lib,airfield,city,harbour}.py`; textures `tex_squadron*.py`, `chapter_squadron.py`) | 4 + 4 + 4 rooms |
| ember | `orchard` (`hollow`), `birch_hall` (`north`), `deep_halls` (`deeps`), `ash_land` (`marsh`, `mountain`) | `python3 tools/story/build_ember.py` (`ember_maps.py`, `art/ember_spec.py`, `tex_ember_tiles.py`, `tex_ember_things.py`, `wardrobe_ember.py`) | 8 + 4 + 4 + 17 sectors |

Run `godot --headless --path . --import` after any rebuild. `tools/story/check_assets.py` checks the three Squadron worlds only (`PATH_CHAPTERS`); the Gospel's four maps are checked by `tests/test_gospel.gd` and `tools/content/test_gospel.py`, the Ember's four by `tests/test_run_ember.gd` and
`godot --headless -s tools/story/check_map.gd` (a map and its chapter). This gap (the Gospel and Ember maps are not in `check_assets.py`) is on the backlog in `docs/HANDOVER.md`.

## The Gospel maps

Views side by side 18 m apart behind a spine road with a portal in each view's back wall (the rail walks from any room to any other through it). A world has one map (the engine rule), so the plan's "galilee_shore day"
is `hillside`'s lakeshore. Palette: ochre, olive, limestone, the lake silver-blue; night indigo with oil-lamp amber (`TOD` in `gospel_maps.py`: light 0.34 and tint `#4a5ab0` at night, `#ffc89a` at dawn).

### Map `galilee_shore` (assets/story/galilee_shore/): the world `jordan`
`bank_night` (J00): a night road in `floor_dust`, a thatched stable lit from inside (`thing_stable`, a lamp light), the star over it (the piece `star`, additive), a campfire (`flicker`), sheep, a far hill town, the stars of
`sky_night`; `bank_dawn` (J01): a sand bank and a river band (`floor_water`, scrolled, 0.4 m lower, an open step between), reeds, palms, the Baptist standing in the water, the dove (the piece `dove`), a far town (Nazareth's
rooftops) as the exit; `rocks` (J02): the wilderness, boulders (`thing_rock_a/b/c`), the tempter, a basket of bread on a rock, the village fires far off; `workshop` (J03): a clay yard, a limestone house with a door, the bench,
planks, the cart with nets.

### Map `hillside` (assets/story/hillside/): the world `galilee`
`lakeshore` (J04): shingle shore, two boats, nets drying on poles, a fish rack, a lake band with boats far out; `street` (J05): a cobbled Capernaum street between limestone houses, the family, the child on a mat, the caravan far
down the road; `slope` (J06): a grassy slope with the crowd seated, the disciples standing, a far hill, a lake band; `storm` (J07): a shore at night under `sky_storm`, a boat with the disciples before it, the beacon fire, the
pieces `storm_cloud`, `rain`, `lightning`.

### Map `bethany` (assets/story/bethany/): the world `road`
`courtyard` (J08): clay court between mud-brick walls, the laid table (`thing_table_meal`), stools, the donkey, the sisters and the disciples; `hill_dusk` (J09): a hillside at dusk (`sky_dusk`, `#ff9a60`), baskets empty
(`thing_basket`) and the full ones as pieces, the crowd seated, a lantern; `gate` (J10): a paved road to the city gate (`thing_citygate`, `wall_city`), four palms, the steps, the olive tree, the waving crowd and the priests at the gate.

### Map `jerusalem` (assets/story/jerusalem/): the world `jerusalem`
`temple` (J11): flagstones, colonnades (`wall_columns`), the portico far off, three money-changers' tables (`t1_up`..`t3_up`) and the same tables overturned (`t1_over`..`t3_over`) as pieces; `grove` (J12): olive trees on dark
soil at night, torches far off; `praetorium` (J13): pale walls with the red band, the dais with the seat, the bowl and jug, braziers; `hill` (J14): bare rock under `sky_dusk`, three plain crosses (`thing_cross`), the sky
pieces `dark1`..`dark3` (bruised gradients, alpha 0.35 / 0.6 / 0.82); `tomb` (J15): a garden of cypress and flowers, the rock tomb (`thing_tomb`), the stone closed and rolled (`stone_closed`, `stone_rolled`), `sky_morning`;
`road` (J16): a paved road in the morning, the city hazy behind, sheep.

### The Gospel people (`wardrobe.gospel`)
Archetypes by `wear`: `fisher` (bare-armed, bandana, bare feet, belt), `villager` and `woman`/`sister`/`mother` (long tunics in undyed wool or dye, stripes, headscarves), `disciple` (twelve recurring robes with sashes and
cloaks: `d01`..`d12` have the same look in every map, `wardrobe.dress` seeds a disciple from "gospel/dNN"), `priest` (white, blue sash, turban), `soldier` (plain lamellar-pattern cuirass, shoulder plates, plumeless helmet,
boots, no emblem), `merchant` (striped, gilet, turban), `child`, `elder` (grey, cloaked), `governor` (white with one red band), `tempter` (tall, dust-coloured, hooded), `baptist` (camel-hair tunic, long hair and beard), plus
`shepherd`, `carpenter`, `gardener`. New hats `helmet` and `turban` in `people.py`. Sheets: galilee_shore 19 people, hillside 35, bethany 29, jerusalem 47 (130 in all). The live Night One rig stands in only as a fallback:
the actors name a Night One archetype so that `StoryCrowd` creates them.

## The Squadron maps

Grainy, over-exposed Mediterranean daylight outside, warm bulbs inside, sepia and noir in the city, a cold blue night at the harbour; the neutral coast is the only saturated place of the path. No insignia (the Colonel's
ribbons are colour bars, the military police have blank white armbands, the cross on the tent is a plain grey cross). Textures 64 px tiles, props 128 px billboards, six wide props 256 x 128, a 256 x 64 sky.

### Map `airfield` (worlds `base` and `air`, scenes C01 to C06)
Bleached khaki, olive drab, orange dust, a white-blue sky, fog `#d8c79c`; the bomber green-black lit by instrument lamps. Six rooms (rectangles, metres, x east / z south): `hut` (-12..0, 0..8, view `main`: the mission board
with a painted tally, the empty cot at the north doorway, stove, maps table, hanging bulbs, the east door onto the line), `line` (0..26, 0..14: sandbag berm, orange dust, the invented twin-engine bomber nose with its ladder,
crates, windsock, jeep, the tent flap and the hangar front), `tent` (0..10, -10..0: cots, drip stands, the kitchen hatch), `office` (-12..0, -10..0: the desk with a huge stamp, a framed certificate, two doors, filing
cabinets), `bomber` (10..14, 14..22: the glazed nose at night with flak flashes, the release lever, the emergency box, instrument panel; ambient 0.9 so the crew read), `store` (26..38, 0..12: the Quartermaster's ledger, the
truck, crates and shelves of tins). No pieces; things with `anim` (`flicker` stove, hatch and flak, `sway` lamps and windsock, `pulse` emergency box, `bob` truck). Palettes `khaki`, `glare`, `instrument`. 36 people.

### Map `city` (world `city`, scenes C07 to C10)
Sepia and noir without neon (fog `#7a6046`): `bomber_r` (-4, the bomber again under red alarm lamps, view `main`), `street` (0..24, 0..8: stucco shopfronts, cobbles, the staff car, the broken arch at the far end, washing
lines, cafe table), `office_c` (2..12, 8..16: dark panelling, the Colonel's desk, the medal case, the torn map, globe, the tally slate), `ruins` (24..46, 0..10: blackened brick under a fire-lit sky, the burnt car, the fire
barrel, headquarters' door and, far off, the night train with its lamp). Palettes `red`, `sepia`, `fire`. 20 people.

### Map `harbour` (world `escape`, scenes C11 to C14)
A cold blue night cut by white searchlight beams (fog `#0e1c34`): `hut2` (the briefing hut again, the count board reading 47 in fresh paint, the smashed radio, the aircraft in the door), `quay` (0..22, 0..12: wet planks, the
fishing boat with one gold lantern, two searchlight towers with additive beams, nets, bollard), `cell` (0..10, -8..0: tally scratches, the barred window with its latch and a shaft of moonlight, the order on the table), and
the **neutral coast** `coast` (22..44, 0..14, ceiling 4.5): golden sand, turquoise sea, cobalt sky, bright umbrella pines, gulls, a blue-and-white boat, seen from the quay only through a narrow gap behind the boat. Palettes
`khaki`, `searchlight`, `bright`, `cold`. 21 people.

### The Squadron people (`wardrobe.squadron()`)
`airman` (a plain, b ground crew in overalls, c pilot in a leather jacket with goggles), `officer` (a colonel: broad, peaked cap, 4 x 3 ribbon bars, b aide with glasses, c chaplain with a dark collar band), `clerk` (0.82 high,
round glasses, garters, bow tie; holds a `stamp`), `surgeon` (long stained white coat, stethoscope, mask down, stubble), `quartermaster` (broad, apron, moustache; an `egg`), `gunner` (a boy: 0.7 high, oversized jacket, flying
cap), `mp` (white helmet, belt, cross strap and blank armband), `civilian_city` (a man, b woman, c child, d street singer), `fisherman` (a yellow oilskin, b dark oilskin with sou'wester, c jersey and beard), `patient` (striped
pyjamas; a head bandage, b sling, c plaster on a leg). Recurring people (the Colonel, the aide, the chaplain, the Clerk, the Surgeon, the Quartermaster, the Gunner, the pilot, the crew) are one person in every map (`same_as`,
`fixed`: seeded by who they are). New in `people.py`: hats `peaked sidecap flightcap mphelm flatcap knit fisher fedora eyeshade surgcap`, tops `uniform pyjamas`, outers `waistcoat oilskin`, accessories `ribbons webbing armband
garters bandage sling apron braces collarband maskdown rag chain`, props `stamp egg medal hat`. The five old chapters are pixel-identical (511 specs and 7,965 frames hashed before and after). The booth portal's props (a
radio, the bomber's shadow) are Night One's own procedural props (`tex_night_one.py` `thing_booth_radio`, `thing_bomber_shadow`; `content/story/maps/night_one.json` `booth_radio`, `booth_bomber_shadow`). Preview:
`tools/story/squadron_wardrobe_preview.py`.

## The Ember maps

### Map `orchard` (assets/story/orchard/): the Orchard, the Ford, the Lantern Inn (world `hollow`)
Eight rectangular sectors: the orchard (open, harvest dusk), the lane, the near bank, the ford (water 30 cm down, scrolling), the far bank, the inn road, the inn (beams, hearth, back door and a window for the rider's shadow
piece) and the back yard. Surfaces by `tex_ember_tiles.py` (grass, lane, ford water, bank mud, boards, flags, hedge, cottage, fence, reeds, inn panelling, door, window, beams, a starry ceiling, `sky_dusk`), billboards by
`tex_ember_things.py` (apple trees, baskets, the cot, lanterns, hearth, tables, barrels, stools, the hanging lamp, **the Ember** in its bowl, the gate, willows, black horses with a red glint, stepping stones; pieces
`river_rise`, `rider_shadow`). People (`wardrobe_ember.py`): `villager_hollow` (wool jerkin, smock, leather belt, no pointed ears, no wizard hats), `grandmother`, `bram` (broad, straw hat, dungarees, apron-coloured gilet),
`innkeeper` (round, waistcoat, ledger), `drinker`, `warden` (grey hooded cloak, belt, plain sword at the hip as a strap), `rider` (ash-grey cloak and hood, nothing inside but two red glints).

### Map `birch_hall` (assets/story/birch_hall/): the Birch Hall and the High Pass (world `north`)
A white hall (birch-trunk pillars with silver bands, banners with a leaf spray, silver lamps, a high chair, a vial on a pedestal, a table with an abstract inked chart: no real land, no writing), a porch and the snow pass
(slate, snow, pines, a cairn, the cave mouth and the ridge marker on the far wall; piece `storm`, a wall of snow switched off when the pass is calmed). People: `lady` (white robe, cape, circlet), `birch_folk` (white and
silver wool, pale sash).

### Map `deep_halls` (assets/story/deep_halls/): the Deep Halls and the Falls (world `deeps`)
A pillared dark (black-blue fluted columns, one cold hanging light), the lake (black, scrolling, the drowned thing rises as piece `drowned` at beat 46), a bridge and a ledge with the drums, the far hall, a tunnel and the top of
the falls (wet boardwalk, a boat at its landing, the Warden's horn on a rock, a starry sky, the waterfall wall scrolling).

### Map `ash_land` (assets/story/ash_land/): the marsh, the wall, the stair, the plain (world `marsh`) and the mountain (world `mountain`)
Seventeen sectors: the reed marsh (teal mist, bioluminescent lights with sad faces), the Black Wall (obsidian, a colossal gate with piece `gate_mouths`, a glowing crack, braziers, the riders), the riders' camp (tents, a stake
and chain, a fire), the stair of bells (three steps of cliff stair, three bell groups, the blind sentinel: a hood over a pale blank face), the ash plain (the Glass Mountain: a black obsidian cone with one red vent, a tower with
a red light), the throat (red vent rock, pulsing walls), the Drowned Spring (black pool, a shaft of white light as piece `shaft`, `swell` = the light swelling white at beat 48 of E12) and the Keeper's cavern (lit by the Ember on
its altar alone, `long_shadow` stretching at beat 32 of E13). People: `hollow_one` (grey species rig, wide pale eyes, barefoot, rags), `rider`, `captain` (bigger, bronze trim, a brighter glint), `sentinel`, Bram. The Ember is
the only warm light east of the ford except the braziers and the camp fire (the riders' own), and the vents.

### The Ember people (`wardrobe_ember.py`)
`wardrobe.PATH_WARDROBES` dispatches a path's dress to its own file; a `person` key gives one look to a named person who stands in several rooms (`bram_f`, `bram_p`, `bram_fb` ... are per-room instances of `person: bram`: a crowd
lives in one room, so a companion who walks with you is one actor per scene). New in `people.py`: the hat kind `hood` (`blank`: `dark` = the riders' empty hood with a red glint, `skin` = the sentinel's pale blank face).

## Wardrobe archetypes of the paths, in one table

| Path | Wears (`wear`) |
| --- | --- |
| gospel | `fisher villager woman sister mother disciple priest soldier merchant child elder governor tempter baptist shepherd carpenter gardener` |
| squadron | `airman officer clerk surgeon quartermaster gunner mp civilian_city fisherman patient` |
| ember | `villager_hollow grandmother bram innkeeper drinker warden rider lady birch_folk hollow_one captain sentinel` |

Sheet budget: the path maps' people sheets are 0.2 to 1.6 MB a map (the Underworld's are 9 MB); the five old chapters' sheets grew 3.2 % in all with the acting data (stage 1d).
