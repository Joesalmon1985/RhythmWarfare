# Story Campaign chapters 2 and 3: art contract addendum

Read `tools/story/ART_CONTRACT.md` first and `docs/STORY_ART.md` plus `tools/story/build_assets.py` + `tools/story/art/*` (the working
Night One generator: reuse its helpers, rig builder and conventions; do not break Night One's output). Everything in the base
contract still applies (SVG source via Python, Pillow PNGs for blur/haze, original art only, `manifest.json`, 1280 x 720 design
space, desk strip authored 1280 x 260, `px_scale` 0.5 for 2x art, the rig joints/parts/faces, the same `stage.sprites` ids so the
runtime's fixtures, woofers, glows, bezels, platters, knobs and faders work unchanged, re-themed).

New chapters live in their own art folders, each with its own manifest and an `ART_BUILD` entry in the generator:

| chapter | art dir | setting | crowd |
| --- | --- | --- | --- |
| `mothership` | `assets/story/mothership/` | the alien spaceship's rave deck: a ring-shaped hangar/dance floor with a huge viewing window onto space and a planet, glowing hex floor, hanging tech pylons, a hologram dome, an alien bar | 6 alien archetypes x 2 variants |
| `underworld` | `assets/story/underworld/` | hell's nightclub: a cavern arena of cracked obsidian and lava, bone arches and chains, a skull throne stage, fire pits, a hellmouth portal at the back, a demonic mixing desk | 6 demon archetypes x 2 variants |

Run: `python3 tools/story/build_assets.py mothership` (or `underworld`, or no argument for all three chapters). Night One's
files must stay byte-identical (`check_assets.py --determinism` style check).

## Crowd archetypes (same rig contract, different anatomy)

Same joint hierarchy (`hips torso head shoulder_l/r elbow_l/r hip_l/r`), same four faces (`neutral happy cheer sad`), same part
names/joints/z ranges so the runtime's StoryCharacter animates them with no code change; the arms and legs must still be two
rotating segments (arms) and legs that rotate at the hip. Distinct silhouettes, not recolours, readable at 50 px head size. A
dancing alien or demon is a stylised friendly cartoon (this is a party): expressive faces, bold shapes, no gore.

- `mothership` ids: `grey` (big-headed classic grey, silver jumpsuit), `antenna` (tall, two antennae with glowing tips), `blob`
  (round jelly-like body, short limbs, translucent), `insect` (mantis-like, long limbs, wing-cases that swing), `cyclops` (single
  big eye, stocky), `tentacle` (octopoid headcrest with swinging tentacle-hair; two arms, two legs).
- `underworld` ids: `imp` (small, horns, tail that swings), `brute` (broad, ram horns, spiked shoulders), `fiend` (tall, bat wings
  that swing, slick hair), `skeleton` (bone body, party hat, hollow grin), `flame` (a fire-spirit with flickering flame hair that
  swings), `succubus`-style `horned_queen` (stylised, elegant, long horns, cape that swings).
- Swinging parts use `swing: true` with a `swing_pivot` exactly as in the base art.
- 2 variants each (`a`, `b`): palette and a detail differ. `glow_hand` per archetype (alien: a glowing orb/wand; demon: a small flame
  torch) using the shared `glowstick` sprite id re-themed.

Rear silhouettes: `sil_a sil_b sil_c` re-themed (`idle`, `up`); aliens: antennae/bulbous heads; demons: horned/winged outlines.

## Stage, set pieces and palette-friendly lighting

Same required `stage.layers` ids (`backdrop`, `speaker_l`, `speaker_r`, `riser`, `desk_top`; speakers become alien resonator
columns / infernal amp stacks, the riser a hovering platform / a bone-and-iron stage), same `stage.anchors` keys (`led_screen`,
`doorway` = the airlock / the gate, `floor_rows` (5, front row scale 1.0, feet y <= 440), `floor_polygon`, `floor_grid`,
`light_points` (8), `woofers` (4), `disco_ball`, `riser`, `circle_centre`, `circle_radii`, `wall_left_x`, `wall_right_x`,
`horizon_y`) and the same `stage.sprites` ids (`woofer fixture disco_ball glowstick door_open pad_bezel platter knob fader_slot
fader_cap crossfader vu_segment deck_screw desk_lip_glow glow beam spot_pool haze_a haze_b vignette confetti`), re-themed
(`disco_ball` = a glowing energy orb / an infernal brazier-ball; `fixture` = alien light-probe / demonic eye-lamp; `confetti` =
star sparks / ash-embers). Keep the lighting sprites white/neutral so the runtime tints them with its per-chapter palettes.

**New: `stage.pieces`**: a list of authored set pieces the chapter script can switch on/off/pulse by id:
`{id, file, pos:[x,y], size:[w,h], px_scale, pivot?, anim, z}` where `z` is `behind` (drawn under the crowd, over the backdrop) or
`front` (over the crowd), and `anim` is one of `none pulse flicker rotate bob sway`. Provide 6 to 8 per chapter. Suggested ids:
- mothership: `planet_window_glow` (the window's planet/aurora brightening), `hologram_dome` (translucent dome over the floor centre),
  `ring_lights` (concentric floor rings), `pylon_beams` (vertical energy columns), `warp_streaks` (streaking stars in the window),
  `saucer_flyby` (a small saucer crossing the window), `alien_banner`.
- underworld: `lava_flow` (glowing lava cracks across the floor), `fire_pits_left`/`fire_pits_right` (flame jets, `flicker`),
  `hellmouth_portal` (swirling red portal at the back centre, `rotate`), `chains_swing` (hanging chains with hooks, `sway`),
  `skull_throne` (a throne on the riser), `bone_arches`, `ember_rain`.
Pieces are drawn additive-friendly where glowing (use light colours on transparent) but remain full artwork.

## Interlude sprites (drawn over the Night One club by a scripted cutscene)

Add `manifest.interlude`: `{sprites: {id: {file, pivot, px_scale}}, anchors: {...}}` with the following art, authored to composite over the
existing Night One 1280 x 720 club view (a fixed camera):
- mothership: `ufo` (huge saucer seen from below, about 900 x 260 design px, hull with ring of lights and a glowing underside; hovers high above the
  dance floor), `tractor_beam` (a soft vertical column of light, top-centre pivot, additive, wide at the floor), `ufo_glow`
  (round underglow), `sparkle` (star twinkle), `light_flood` (white-green full-screen wash for the climax).
- underworld: `crack_glow` (a jagged glowing fissure that spans the dance floor in perspective, with a stretchable segment), `flame_jet`
  (tall flame sprite for animation by flip/scale), `portal_vortex` (a big swirling red-black vortex ring, centre pivot), `embers`
  (small ash/ember specks), `dark_wash` (red-black full-screen wash).
Place `anchors`: `ufo_hover` [x,y], `beam_floor` [x,y], `crack_origin` [x,y], `portal_centre` [x,y].

## Deliverables

`tools/story/build_assets.py mothership|underworld` writing `assets/story/<chapter>/{source,processed,manifest.json}`,
`check_assets.py` extended to validate each chapter manifest, `docs/STORY_ART.md` updated with the new chapters' provenance and
how to edit them, and `preview_art.gd/.tscn` extended (or a `preview_chapter` mode) so each chapter can be reviewed with real
screenshots. Review visually until each set reads as a finished stylised neon set.
