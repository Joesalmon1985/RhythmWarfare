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

- `archetypes` (rig contract as above, same four faces, same part names): `grey` (big head, silver jumpsuit), `antenna` (tall, two
  swinging antennae with glowing tips, `hair_front` swing), `blob` (round translucent jelly body, short limbs), `insect` (mantis, long
  thin limbs, forearm blades, mandibles; its wing-cases are the `hair_back` part with `swing: true` on joint **`torso`**, pivot at the
  neck), `cyclops` (one big eye, stocky, overalls), `tentacle` (head crest with five swinging tentacles `hair_back` plus two front locks
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
  behind), `ring_lights` (pulse, behind), `pylon_beams` (pulse, behind), `alien_banner` (sway, behind; pivot at its top edge), `bar_glow`
  (flicker, behind), `hologram_dome` (pulse, front). Entry fields: `file`, `pos` (top-left, design px), `size`, `px_scale`, `pivot`
  (animation origin, texture px), `anim`, `z` (`behind` = over the backdrop and under the crowd, `front` = over the crowd). The glowing
  ones are light-on-transparent: draw them additively.
- `interlude` (for the scripted UFO scene over the **Night One** club): `sprites` `ufo` (900 x 260 design px, seen from below, pivot at
  the centre of its underside), `tractor_beam` (PNG, pivot top centre, 480 x 340 design px, stretch it to `beam_floor`), `ufo_glow`,
  `sparkle`, `light_flood` (full screen); `anchors` `ufo_hover` [640, 92], `beam_floor` [640, 372].
- Preview: `shoot_preview.sh <mode> <out> mothership` with `set` (bare room), `stage`, `chars`, `chars_b`, `heads`, `joints`, `pieces`
  (sheet of every piece), `sil`, `deck`, `interlude`, `interlude_flood` (composited over the Night One stage). `RW_WARP=1` shows
  `warp_streaks` in `stage`.

## Provenance and licence

Every pixel comes from the code in `tools/story/` in this repository; there is no third-party content and no generated-image
service. The art is covered by the repository's own licence.
