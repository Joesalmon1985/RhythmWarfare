# Rhythm Warfare: art style guide

The rules that make every world, quest and UI piece look like one game. Written for the art stream (lead ruling 26) after the audit of
6 November 2026 (`docs/art/VISUAL_AUDIT.md`). Derived from the owner's references (`pixelexample/Rave.png`, `Hospital.png`,
`InsaneAsylum.png`), `docs/STORY_25D_ART_DIRECTION.md`, and what is already best in the build: the baked people
(`tools/story/art/people.py`), the procedural pixel textures (`tools/story/art/pixeltex.py`) and the Warehouse floor.

Every rule has a check. "Script" means a check a tool makes today (`tools/art/`); "eye" means a reviewer looks at the named shot.

## 1. The look in five lines

1. Dense, hand-placed-looking pixel art: dithered gradients, wear, grime, small props. No smooth vector shapes in the picture.
2. Dark rooms with **lifted, coloured shadows** (navy, indigo, bottle green, oxblood) and **local pools of warm light**. Nothing in the
   picture is pure black except a deliberate void.
3. People are people (head 1/7 of the height, real hands and hips, individual clothes), drawn by one pipeline in every world.
4. One pixel size in the picture: the world, the people and the props share the internal pixel grid (360 lines).
5. The UI is a frame around the picture, not objects on top of it. The picture shows only things that exist in the place.

## 2. Value range (script: `tools/art/frame_check.py <raw_dir>`)

Measured on the picture only (the pad strip and the HUD cut away), averaged over a world's scenes:

| Measure | References (Rave / Hospital / Asylum) | Rule |
| --- | --- | --- |
| Luminance p5 | 0.08 / 0.09 / 0.04 | at least 0.035 |
| Luminance p50 (median) | 0.22 / 0.17 / 0.15 | 0.11 to 0.24 |
| Luminance p95 | 0.62 / 0.40 / 0.44 | 0.38 to 0.70 |
| Crushed (under 0.04) | 0 % / 0 % / 6 % | at most 10 % |
| Blown (over 0.85) | 0.1 % / 0 % / 0.2 % | at most 1.5 %, and only on light sources (lamps, screens, signs, beams) |
| Mean saturation | 0.47 / 0.58 / 0.43 | 0.35 to 0.60 |

Daylight worlds of the quests (Gospel day, Squadron airfield, Ember orchard) may run brighter: median up to 0.38, p95 up to 0.85, but the
blown rule holds and saturation stays at most 0.60.

A lit surface never goes to white: the light that falls on an albedo is capped so that `albedo x light` stays at most 0.92 per channel
(an LED floor at full beat is a light source and is exempt, but its tiles keep their colour, never a white checker).

## 3. Shared neutrals (every world uses these, tinted only by its light and fog)

| Role | Hex | Use |
| --- | --- | --- |
| Shadow ink | `#13111f` | the darkest colour of a lit room; the one-pixel darker edge of a dark sprite. Never `#000000`. |
| Deep navy | `#0b1528` | night shadow, the floor under a crowd at night |
| Bottle shadow | `#0b1519` | institutional green worlds' darkest |
| Oxblood shadow | `#2a0a08` | red worlds' darkest |
| Warm light | `#eab278` | lamp light, a lit doorway, skin highlights in warm light |
| Cool light | `#9fc4e8` | moonlight, screens, cold tubes |
| Paper / plaster | `#d8ccb4` | the lightest non-emissive surface anywhere (no pure white walls) |
| Skin ramps | `people.py` eleven tones | the same ramps in every world and quest; the world changes them only through light |

## 4. Palette per world

Fog is the map's `fog.color` (`content/story/maps/<map>.json`) and is also the darkest colour the post clamp allows.
"Key" is the ambient shadow, "mid" the main surface, "accent" the colours that may be saturated, "light" the light sources.

| World (map) | Fog | Key | Mid | Accent | Light | Mood |
| --- | --- | --- | --- | --- | --- | --- |
| Warehouse (`night_one`) | `#0a0618` | `#16080f` | `#634e60` brick, `#391c16` rust | `#c23a8a` magenta, `#2fb6c8` cyan | `#eab278` amber, `#ff4fb0` beams | warm amber and magenta in a dark warehouse (Rave.png) |
| Mothership (`mothership`) | `#06081c` | `#0b0c1e` | `#3b4d63` hull, `#4e8d8e` teal | `#7be0d0` cyan, `#b88cff` violet | `#cfefff` cold white, planet `#5a8fd8` | cold cyan with the planet's glow |
| Underworld (`underworld`) | `#2a0a08` | `#200d11` | `#572222` brick, `#8a5c57` bone | `#ff6a1a` ember, `#c02030` blood | `#ffb050` fire | red and black with ember orange |
| Hospital, Hospital late (`hospital`) | `#0c1636` | `#18293d` | `#3a4a68` wall, `#524e64` lino | `#e0b060` corridor spill, `#5fd890` monitor green | `#9fc4e8` moon, `#eab278` station lamp | a night ward, blue with a warm corridor (Hospital.png) |
| Ward, Ward late (`mental_hospital`) | `#06110c` | `#0b1519` | `#394d44` tile, `#4a6758` paint | `#a05a30` rust, fancy dress colours on people only | `#e8c070` one office lamp, `#c8e8d0` tubes | grim green institution (InsaneAsylum.png) |
| The Bassment (`bassment_*`) | per zone | `#100c10` | stone and brick of the zone | the zone's one colour | torch `#ffb050` | a dungeon under the club; each zone one accent |
| Gospel day (`galilee_shore`, `hillside`, `bethany`, `jerusalem`) | per sector | `#3a2a20` | `#c8a878` limestone, `#b08848` ochre, `#6a7a40` olive | `#5a8ab8` lake, `#ff9a60` dusk | sun `#fff0c8` | ochre, olive, limestone, silver-blue lake |
| Gospel night | per sector | `#141830` | `#4a5ab0` tint on the day ramps | `#ffc89a` oil lamp | lamp `#ffb060`, star `#fff4d0` | indigo night with oil-lamp amber |
| Squadron (`airfield`, `city`, `harbour`) | `#d8c79c` / `#7a6046` / `#0e1c34` | `#2a2418` | `#8a7a50` khaki, `#4a5030` olive drab | `#c86a2a` dust, `#2a6aa8` coast sea (the coast only) | bulb `#ffd890`, searchlight `#e8f0ff` | grainy over-exposed day, sepia city, cold blue night |
| Ember (`orchard`, `birch_hall`, `deep_halls`, `ash_land`) | per sector | `#1a1410` | `#5a6a30` grass, `#7a5a38` timber, `#c8c8d0` birch | `#ff7a20` the Ember | `#ffb050` lanterns | harvest dusk, white hall, black deeps, grey ash; the Ember the only warm light east of the ford |

The per-world `clamp_lo` of the post-process is the fog colour; nothing in that world renders darker than it (this is what lifts the
crushed blacks of section 2).

## 5. Light

- One light model everywhere: surfaces get the sector's song-time light times the lamps around them (`StoryWorld` vertex light);
  people get the same light where they stand (`story_people.gdshader`). Nothing in the picture is fullbright except emissive
  pixels (screens, lamps, signs, the Ember, lit windows), which are marked emissive and are the only pixels allowed above 0.85.
- Every room has at least one **pool** (a lamp, a doorway, a window, a screen) brighter than its surroundings by 2x, and its far wall
  falls off to the key colour. Uniform light across a room is a defect.
- The sheets are shaded from the **upper left** (`people.py`); props and tiles drawn by Python use the same direction. The world's
  lamps colour that shading; they do not re-draw it.
- Beams and haze are additive and soft; they are the only soft-edged things allowed in the picture.

## 6. Outline and edges

- No black outlines. A sprite's silhouette is a one-pixel edge one step darker than its local colour (as `people.py` draws it).
- No coloured halo outlines (the wizard's yellow and magenta rim in `assets/run/choice/wizard_*.png` breaks this rule).
- No anti-aliased fringe on a cut-out: alpha is 0 or 255 on every billboard (`thing_*`, pieces, silhouettes), except glows and beams.
  Script: count pixels with 0 < alpha < 255 in `thing_*` textures (must be 0 outside `*_glow`, `*_beam`, `*_star`, `piece_*` light pieces).
- No smooth vector shapes in the picture. SVG art that reaches the world (set pieces, the old 2D backdrops cropped into tiles, the rear
  silhouettes) is rasterised at its final pixel size and quantised to the world's ramp with the 8x8 ordered dither of `pixeltex.py`.

## 7. Pixel density and scaling (script: `tools/art/texture_sheet.py`, column px/m and flags LOWDENS, MANYCOL)

The picture is rendered at 360 lines (640 x 360 at 16:9) and scaled up with nearest filtering. At distance d metres one metre covers
about 369 / d internal pixels (vertical FOV 52 degrees).

| Thing | Texels per metre | Why |
| --- | --- | --- |
| Walls, floors, ceilings | 96 to 160 (target 128) | one texel is about one internal pixel at 3 m, the usual distance |
| Billboard props (`thing_*`) | 96 to 160 | the same grain as the wall behind them |
| Skies | the strip wraps the horizon once: at least 1024 px wide (256 now) | stars and the moon are 1 to 4 internal pixels, not squares of 8 |
| People | the full sheet (112 px for a 1.8 m adult = 62 px/m) is drawn at most 1.25x | above that the person must use a bigger level or not come that close |

- Surfaces under 48 px/m are defects (they read as magnified blocks next to the fine people). Today 225 of 721 textures fail.
- A texture made by cropping an SVG and resampling (many colours, smooth ramps) is a defect: redraw it with `pixeltex.py`.
- Final image scale: integer where the window allows (720 -> 2x, 1080 -> 3x, 1440 -> 4x). Non-integer phones (390 px tall) accept
  uneven pixels; nothing may be bilinear-filtered.
- Mixed pixel sizes inside one frame (a person drawn at 3 internal pixels per sheet pixel beside a wall at 1) are the most visible
  defect class of the build: the camera rule is that no person and no prop comes closer than the distance at which it reaches 1.25x.

## 8. Shadows

- Every standing person and every floor prop has a contact shadow: an ellipse 1.1 x 0.35 of its footprint, the floor's key colour at
  55 % alpha, a one-pixel dithered edge. Hanging, flying and wall-mounted things have none.
- Shadows follow the room's main light only when the room has one strong source (a lamp over a table); otherwise straight down.
- Eye check: no figure in a frame floats (feet on the floor line, shadow under them).

## 9. People (characters, heralds, crowds)

- One pipeline: `wardrobe.py` / `wardrobe_ember.py` -> `people.py` -> `people_sheets.py`, drawn by `StoryCharacter` with
  `story_people.gdshader`. Every person in the picture (crowd, cast, herald, wizard, fight creature with a body) comes from it.
- Proportions: head 1/6.5 to 1/7 of the height; shoulders, hips and hands; no oversized heads; kids about 0.65 high.
- Shading: three steps plus ordered dither, light from the upper left, a one-pixel darker edge, a rim of the room's light.
- Faces: the fourteen faces of `people.FACES`; eyes and mouth must stay visible at the front-row size (hair may not cover the whole face).
- The rear crowd is people too: far rows are the quarter level of detail tinted to the fog with a rim, not vector silhouettes.
  A rear-row silhouette may never be closer than 8 m to the camera.
- No two people in a room share build, hair and top (`look_key`, `check_assets.py`).

## 10. Props and set pieces

- Drawn in Python with `pixeltex.py` primitives at 128 px/m, quantised to the world's ramp, lit from the upper left in three steps,
  a one-pixel darker edge, a contact shadow if it stands on the floor.
- Real sizes: a door 2.0 x 0.9 m, a table 0.75 m high, a chair seat 0.45 m. A prop at the wrong scale is a defect.
- A prop belongs to its world: the same object (a door, a speaker, a lamp) is redrawn per world in that world's materials. No prop of
  one world appears in another unless the story brings it there (the Squadron radio in the booth is such a case and is drawn in the
  Warehouse's palette).

## 11. UI on the picture

- The picture region shows only the world and the hotspot light (`HotspotView`, drawn inside the low-res pass so it pixelates with the world).
- No traffic-sign iconography in the world (the green chevron lamp, the red no-entry sign of `assets/run/choice/`): the lamps of a
  door are lamps of that world (a bulb over the door, a lit exit sign where the place has one).
- The pad strip, the HUD bars and the falling notes are UI: one font (the theme's), one corner radius (10 px), the `StoryStyle`
  colours. The strip may carry the world's deck skin; a world without its own deck uses a neutral deck in `#13111f` and the shared neutrals,
  never another world's neon desk.
- Falling notes over the picture are drawn as light, not as panels: a tap note is the pad's shape glowing in the family colour with a
  transparent body (at most 35 % alpha over the picture above the strike line); a hold is a lit core one third of the pad wide, not a
  full-width translucent column. (Whether to change this is a question of taste for the owner; see the audit.)

## 12. New objects (for N2.4 to N2.6 and the herald, ruling 25)

All four are things of the place first, markers second. They are drawn to sections 4 to 10 in the **host world's** materials and
light; only their accent says where they lead.

| Object | Must look like | Accent | Size and placement | Check |
| --- | --- | --- | --- | --- |
| **Quest entrance** | a real object of the host place that the quest could enter through (a radio, a glass with a glowing ember, a projected star on the wall), not the shared door | the quest colour (Gospel `#fff0c8`, Squadron `#ffd25a`, Ember `#ff7a20`) as a light the object emits and a pool on the floor | at least 0.8 m wide; 88 px or more on screen at the usual camera distance; never behind a person | eye: at a glance in the `win` shot of its scene; script: coverage audit min px |
| **Herald** | a person of the quest (its wardrobe), baked through the people pipeline, lit by the host room's light; one motif of the quest carried visibly (a lantern, a flying cap, a robe and a staff) | none on the body; the motif may be emissive in the quest colour | stands 0.6 to 1.5 m from the entrance, three-quarter view, the act `beckon` or `point` toward it on the beat; same scale as the crowd | eye: herald and entrance read as one group in the `win` shot; `test_story_acts` bakes the act |
| **Return object** | one motif per quest (Gospel a lamp of oil, Squadron the mission board's chalk tally, Ember the lantern), drawn in the quest's style | the destination's world colour (the mainline key light) | as the entrance | eye: one return object per quest looks the same in every scene it appears |
| **Reactive prop** | an existing prop of the place (speaker stack, light rig, a patient's drip stand) | none at rest; the shared hint gleam on the beat | its real size; it must have a visible reaction (two or more frames or a code reaction) | eye: no reactive prop has a marker a choice does not have |

None of them has text, arrows, a halo outline or a floating icon.

## 13. Checks in one place

| Check | Tool | Status |
| --- | --- | --- |
| Texel density, resampled crops | `python tools/art/texture_sheet.py <out>` (LOWDENS, MANYCOL) | written, run in the audit |
| Value range, crushed and blown, saturation per world | `python tools/art/frame_check.py <raw_dir>` | written, run in the audit |
| Alpha fringe on billboards | proposed: extend `texture_sheet.py` with the share of 0 < alpha < 255 pixels | not written |
| Figure scale cap (no person drawn above 1.25x its sheet) | proposed: a debug counter in `StoryCrowd` read by a headless test over every scene's rail | not written (src/story) |
| Contact shadow present | proposed: `check_assets.py` reads each map's things and people homes and requires a shadow flag | not written |
| One look per room | `check_assets.py` `look_key` | exists |
