# Story Campaign 2.5D: art direction tweaks (owner's notes, 2026-11-04)

Given after seeing Night One in the 2.5D world. References: `pixelexample/Rave.png`, `Hospital.png`, `InsaneAsylum.png`. The owner's
words: "this isn't exactly what the game should look like, but it should look more like this"; "every level and every scene feels too
familiar to the last"; "more frequent player movement and looking around"; "the figures should be doing things other than dancing at
times, appropriate to the space and mood they are in"; "have some fun with it".

This brief extends `docs/STORY_25D_PLAN.md`. It adds a work package WP9 (Sonnet) and replaces the polish brief in plan section 9
(Opus). Everything in the plan's sections 2, 7, 8 and 11 still holds (song-time determinism, headless tests, no new audio, no downloads,
the frame budget, the main campaign untouched).

## 1. What the references have that the build does not

1. **Density and grime.** Every surface is textured: dithered gradients, wear, rust, cables, trusses, pipes, tiles, blinds. Ours are
   flat tiles with uniform light.
2. **Light as mood.** Pools of warm light in cool dark rooms; haze in the beams; moonlight through blinds across a floor; a lit doorway
   at the end of a dark corridor; glowing monitors and lamps. Ours is one light level per sector.
3. **Props that tell a story.** A water bottle and a pint on the decks, an ashtray, cups held up, a heart monitor by the bed, beds
   with rails, a nurses' station, lined-up chairs, jars on shelves, a rotary phone, a radiator, a fan, a wall clock, a surgical lamp.
4. **Figures that are people.** Naturalistic proportions, varied clothes and hair, eyes closed lost in the music, drinking, pointing,
   arms up, hands on the mixer, headphones on, and a dense crowd fading into silhouettes behind.
5. **Depth.** Rooms open onto other rooms: double doors framing a lit corridor, a window onto the night, a long sightline to a desk.
6. **Tone.** The hospital is a night ward, blue with a moon in the window and a warm corridor beyond. The asylum is a grim green
   institutional lab with rust, pipes and a moon through a barred window. Both are darker and more atmospheric than our gentle
   Hospital and Ward. The rave is a warehouse: steel trusses, speaker stacks, a dense crowd, smoke.

## 2. Pillars

### A. Layout variety (every room must read as a different place at a glance)
No two rooms in the campaign share a footprint, height and sightline. Every chapter map contains at least one of each: a long
sightline (a corridor or a hall seen end to end), a tall room, a tight low room, an opening to the outside or to a big view, a level
change (stairs, riser, ramp, pit, balcony, a bed you look up from), and a room seen *through* another (a doorway or window framing it).
The place where the music is played moves too: not always a central floor facing a stage. Per chapter:
- **Night One**: a warehouse rave. Entrance tunnel under a steel stair; the main floor under trusses with a balcony above; the booth
  raised at one end behind speaker stacks; a bar alcove, low and warm; a chill-out room with sofas and a strip of bulbs; a long tiled
  corridor to the toilets; cubicles. The balcony is a good-branch stop ("the promoter takes you up to see the floor").
- **Mothership**: a curved deck with the planet in a huge window; a cramped medical bay (the probe light); a vast reactor well seen from
  a catwalk with the core far below; a long observation gallery; the bridge on a dais with a viewscreen. Ramps, not stairs.
- **Underworld**: an arena pit seen from its floor with the demon crowd on tiers above; an obsidian court with columns and a throne up
  a stair; a bone bridge over lava; the furnace, low and red, chains and anvils; a cage.
- **Hospital** (night): a private room from the bed (the player wakes looking up), a long corridor with a lit nurses' station at the
  end, the day room with a TV and chairs, the cafeteria with vending machines, a courtyard garden under the moon with a bench.
- **The Ward** (grim, institutional, green): a dormitory of iron beds, a day room with chairs lined up against the wall, a treatment room
  with a surgical lamp and a steel table (the bad branch), the art room with easels, a long corridor of locked doors with one lit
  office, a walled courtyard under a barred sky for the talent show. The fancy-dress residents stay: they are the warmth against it.

### B. Movement frequency (the camera does something in every block)
At least one `player_move` or `player_look` in every eight-bar block, not only at decisions. Mix: a walk to a new spot, a slow look
sweep across the room, a turn to watch a character who is doing something, following a character through a door, stepping back as
the crowd presses in, climbing, leaning over a rail, a look up at the lights or the ceiling, a look down at the pads or a drink.
Idle looks: a slow head drift between authored moves (a function of song time, small, off in reduced motion). Decisions still choose
the branch; the blocks within a branch author the beats. The dense-run rule stays: moves start on light bars and last 2 to 4 bars.
Looks are allowed anywhere because the notes stay fixed on screen.

### C. Figures doing things (appropriate to the space and the mood)
Extend `StoryCharacter` with activity states beyond the dance set: `drink`, `toast`, `chat` (pairs face each other), `point`,
`phone` (lit face), `lean_wall`, `sit`, `lie` (a bed), `sleep`, `paint`, `pace`, `carry` (tray, drip stand, cup), `check` (a nurse at a
monitor), `stare`, `rock`, `hug`, `queue`, `wave`, `watch` (facing a target). Each sector lists its activities by mood band in the map
(`"activities": {"quiet": [...], "dancing": [...], "hype": [...]}`), the crowd picks per actor with its seeded style, and dancing is only
on `dance_floor` sectors and only when the band allows. Props in hand reuse the existing props-in-hand mechanism (cups, glow sticks,
trays, brushes, sketchbooks). Examples: at the bar people queue and drink; in the chill-out room they sit and chat and one is on a
phone; in the toilets someone leans on a sink; on the Mothership a grey examines a dancer on a table; in the court demons lounge on
the stair; in the hospital a nurse checks a monitor while the family sits and one visitor sleeps in a chair; on the Ward residents
pace, rock, paint, queue for medication, and one stares out of the barred window. Fun is wanted: an alien DJ wearing the headphones
wrong, a demon bouncer checking tickets, a patient dancing with a drip stand, a chef serving at the talent show.

### D. The pixel look (the Opus polish, section 4)
Keep the internal resolution pipeline. Textures become dense: dithered gradients, wear and grime, cables, trusses, pipes, blinds,
tiles with grout, generated procedurally (Pillow in the tiles pipeline or a Godot bake, deterministic) in the chapter's palette.
Light becomes local: per-sector vertex-colour gradients from authored light sources (a lamp thing lights the floor around it, a
doorway spills light into the dark corridor, a window throws a moonlight shape across the floor), still functions of song time.
Haze in beams. Windows with a sky, a moon, trees. A dense far crowd as layered silhouettes. Optional ordered dithering and a per-
chapter palette clamp in the post shader (a setting, off by default on reduced effects). Chapter tones: Night One warm amber and
magenta in a dark warehouse; Mothership cold cyan with the planet's glow; Underworld red and black with ember orange; Hospital
night blue with warm corridor spill; the Ward institutional green with rust, a single warm office light and flickering tubes.

### E. The figures (the owner's priority: "replicate the look of the sprites in the example art, less blocky, more individual")
The target is `pixelexample/Rave.png`: people, not mascots. What that means, concretely:
- **Proportions**: heads about 1/6.5 to 1/7 of height, real shoulders, hips and hands; no oversized heads, no stick limbs, no thick
  dark outlines (a one-pixel darker edge of the local colour at most).
- **Individuality**: every actor is their own person, generated from their seed by a wardrobe system rather than picked from a few
  archetype variants. Build (height 0.9 to 1.1, slim to broad), skin tone (a wide range), hair (short, curly, braids, locs, long,
  bun, shaved, under a hat), face (eyes open or closed lost in the music, smile, grin, beard, stubble, glasses), clothes from a
  wardrobe library (t-shirt with a print, checked shirt, striped jumper, hoodie, jacket, crop top, dungarees, baggy trousers, jeans,
  skirt, dress, bucket hat, cap, beanie, headphones, bag strap, bracelet, trainers, boots), each with its own colour set in the
  chapter's palette. Chapter wardrobes: ravers; aliens with the same system (builds, skins, antennae, suits); demons (horns, hide,
  armour); hospital staff and family (scrubs, gowns, visitors' coats); the Ward's residents in fancy dress, staff in institutional
  green. No two actors in a room may share build, hair and top.
- **Shading**: cloth folds and skin shaded in two or three steps with dithering between them, a rim from the nearest light colour,
  not flat fills. Prints and stripes on clothes. Hair with strands, not a helmet.
- **Pixels**: figures are drawn so that at the internal resolution they read as hand-placed pixels, not as scaled vectors: the
  pipeline bakes each actor's rig to a sprite sheet at the internal pixel size (one pixel of the sheet is one screen pixel at the
  front row), with 3 facings, 8 to 12 frames per state, nearest-filtered, so a dancer looks like the reference's pixel people. The
  live rig stays for the cutscenes and as the bake source. The default internal resolution rises to 360 lines (640 x 360; frame
  cost was measured as independent of resolution) so the people are finer than the walls are chunky; 270 and 180 stay as settings.
- **Poses**: keep the beat-locked analytic poses but add the reference's naturalness: weight on one leg, a cup raised, a hand on a
  friend's shoulder, eyes closed with the head back, a finger pointing at the DJ, hands on the mixer with headphones on one ear.
- **Depth**: the front row large and partly cropped, the mid rows in full, the back rows as darker, bluer silhouettes with rim
  light, as the reference does.
Acceptance: a contact sheet `docs/shots/story/figures_<chapter>.jpg` of every actor at front-row size next to a crop of the
reference; the owner should see people of the same kind, original but in that spirit.

## 3. WP9 (Sonnet, after WP8): structure for A, B and C
- Rebuild the five maps to the room lists in A (reuse everything that fits; the maps are data). Validation unchanged.
- Author moves and looks in every block of every chapter (B); extend the dense-run warning to cover looks only for sanity, not to block.
  Idle head drift in `StoryPlayer`.
- Activity states in `StoryCharacter` (C), sector activities in the map schema and `StoryMap` validation, crowd selection by band, pairs
  for `chat`, targets for `watch`, props in hand; the fun beats above authored as pieces or directives.
- Light sources as things with a radius and colour; `StoryWorld` bakes per-sector vertex gradients from them (D's data hook, so Opus
  can dress rooms by placing lamps).
- The default internal resolution becomes 360 lines (settings keep 270 and 180).
- Tests: every block has a camera beat; every sector has activities for every band; no dancing off the dance floor in the quiet band;
  the matrix (plan 8.1) and the walk-through (8.2) still pass; screenshots regenerated, one per room per chapter plus the activity beats.
- Acceptance: a contact sheet per chapter in `docs/shots/story/` where a reviewer can tell every room apart at a glance; in any
  screenshot off a dance floor fewer than half the figures are dancing; between any two consecutive blocks the camera has moved or looked.

## 4. Opus polish (replaces plan section 9): look for E then D
Figures first (section 2.E), for all five chapters, before any room dressing: the wardrobe system and the per-actor generation in the
Python art pipeline, the restyled rig parts, the sprite-sheet bake, the depth treatment, the contact sheets. Then the rooms, per
chapter in this order: Night One, the Ward, the Hospital, the Underworld, the Mothership: the textures (dense, dithered, worn), the
light sources placed for mood (pools, spill, moonlight), the props that tell the story (section 1.3 and the chapter's own), the window
or opening with its sky, the far crowd silhouettes. Before/after screenshots in `docs/shots/story`, one reviewed commit per unit, the
frame budget kept (plan 8.4), no change to logic, the maps' sector graphs, journeys or tests except to add checks. The references
are the spirit, not a copy: original art only, generated by the repo's own tools.
