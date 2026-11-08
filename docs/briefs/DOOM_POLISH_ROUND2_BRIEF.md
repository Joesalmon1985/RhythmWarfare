# Doom worlds, stage D polish round 2: close the distance to the paintings

Round 1 (`docs/briefs/DOOM_POLISH_BRIEF.md`, the seven steps) is merged: every scene is lit inside or near the
exposure rule, every guide is a crop where the painting allowed it, every scene doc lists what still does not match.
The lead looked at every contact sheet beside its painting on 9 November. All eight scenes are honest placeholders
still. Round 2 is the pass that makes each scene read as *its painting at a glance*: the one thing a player would
name if asked "what is this place?" must be in the reference shot and must be the painting's thing.

Read first: the round 1 brief (its rules still hold), `LEAD_RULINGS.md` 35, 36, 38, 39, your scenes' docs and sheets,
`docs/engine/GEOGRAPHY_WORLDS.md` (new: the `pitch` field), `docs/story/HEIGHTS_AND_PATHS.md` (new: `pitch` in the rail
keys; split voids).

## Two engine hooks landed for this round

1. **A steady downward pitch at the choice viewpoint.** On the scene's run node, the rail place that has
   `"choice": true` may carry `"pitch": <degrees>` (negative looks down, within ±35). The run holds it still through
   the whole choice window (ruling 35), a herald look hands back to it, the walk-off eases it out. Use it where the
   painting looks down: the Underworld's lava lake (about −14), the Lounge's sunken sofa (about −12). Re-check the
   three guides and the pads at the pitched pose (`test_doom_views`): the guides must still read ≥ 60 px apart and
   the pads must not cover their waists.
2. **`void_top` for split voids** is computed over the connected group, so a pit split into wedges hazes to the rim.
   The Mothership's haze band decals were a workaround: keep them only if they still add something beside the
   engine haze; otherwise remove them.

## Rules for this round (on top of round 1's)

- **Every shot inside the exposure rule**, not the scene's aggregate: p50 0.25–0.38 and contrast ≥ 0.40 on each of
  the eight 16:9 shots (`tools/doom/frame_check.py`). A shot that looks into a dark drop is lit by what is in the drop
  (lava, the pool, the city) not by lifting the ambient.
- **No visibly repeating tile.** A tile that repeats across a wall or floor in the reference shot gets 2–3 variants
  or a decal break every 4 m. The Underworld's stripe basalt, the Mothership's rib lattice and the Dock's lit-window
  towers are the worst cases today.
- **No flat passage decals.** A doorway the player can walk through is a lit opening with depth: a short corridor
  sector, a frame, light on a wet floor beyond. The flat blue rectangles (the Bar's Floor passage, the Lounge's Floor
  threshold, the Dock's club passage, the Underworld's cave decal and its blue striped arch tunnel) all go.
- **The room is the painting's size** where convex sectors allow it: the Warehouse and the Lounge are much larger
  than their paintings; bring walls in or fill the depth with what the painting has (rig, stacks, scaffold; coffers,
  columns) so no shot is a void around a small crowd.
- **Guides:** every procedural guide moves toward the standard (`art/reference/standard/guide_floor_sprite_standard.png`):
  a face, dithered skin and costume, a readable silhouette from the painting; say crop or procedural per guide; the
  doc calls a placeholder a placeholder. Never a ring or beacon.
- **The scene doc** ends with the lead's list below, each item ticked or carried with one line of why.

## Per scene: the lead's list (what a player would name first)

### Warehouse (agent A)
- The hall is still a huge blue void around a small crowd. Bring the far walls in, or fill the depth with the
  painting's rig, speaker stacks, scaffold and hanging lanterns so every shot has something warm within 10 m.
- Let the warm practicals win near the bar corner and the lounge wall (they read; the blue shafts should not flatten them).
- The four shots under the rule on contrast (`approach_bar_b`, `approach_stage_c`, `stay_2`, `stumble`).
- The stage guide is 64 px and the coat below the cut is blocky: a proper crop or a proper procedural sprite.

### Bar (agent A)
- The best scene so far. Keep it.
- The Floor passage is a flat blue rectangle that two holds stare at (`stay hold way`, `left to the Floor 3/4–4/4`):
  make it an arch with depth and light on wet stone, as the painting's left doorway.
- The booth is a grey locker wall with a small figure: the painting's booth window with the desk lamp.
- Channel water and gloss barely visible from the reference view; the `left` walk passes the Floor guide within 1 m.
- Booth guide procedural placeholder: improve toward the standard.

### Lounge (agent A)
- The sunken sofa pit is the painting's whole subject and is in no shot. Author `pitch` on the choice place and, if
  needed, lower the floor of the reference viewpoint or raise the pit, until the sofa ring and the table are in the
  16:9 reference shot under the pads.
- The walls are gold cubes; the painting has warm coffered panelling under a vault: coffers as decal bands, columns,
  the ceiling ribs as a sky or decal.
- The Floor threshold is a bright blue striped box: a dark cobalt glass passage with depth.
- Contrast 0.39 aggregate, 9 of 13 shots out of the rule.

### Dock (agent B)
- The skyline is a repeating lit-window tile pasted on tall walls. Replace with a silhouette skyline (the map `sky`
  or far billboards) with a few lit windows at distance; the near walls are brick and corrugated steel, not towers.
- The wet street must read as the painting's: warm sodium pools on wet tarmac with deep shadow between them, not a
  blue-grey whole. The lamps' pools should be the brightest thing in the reference shot.
- The club passage (`hold_door`, `route_left`) is a flat blue LED corridor: a dark brick arch with a violet-lit door.
- `route_ahead` p50 0.22, `route_left` contrast 0.27, `arrive` and `hold_door` just under.
- The street is straight; the painting's curves left (cheap if a second sector bends the far end).

### Balcony (agent B)
- The weakest scene. The drop and the city must dominate the reference view: lower the parapets, bring the moon into
  frame, let the wet deck reflect the city; the brick box must open on three sides.
- The pink equaliser shapes on the wall at `hold_stair` go.
- `hold_bridge` and `route_ahead` at p50 0.17: the drop needs its own light (the city below, the searchlights).
- The dish and lace dome are the old flat placeholders; the Mothership guide is 85 px; the moon is hidden behind the
  towers at the reference view.

### Booth (agent B)
- The desk reads now; keep it, but it is a camera-facing cut-out that looms on the aisle walk: anchor it (a fixed
  yaw billboard, or two billboards at the desk's ends).
- The Mothership chamber beyond the hatch (`route_ahead`) is a garish violet box with crystal spires: tone it to the
  painting's violet doorway (dark, one violet light, the figure).
- The window wall is a mesh with a flat rainy city: the painting's window shows the balcony and the skyline with
  rain on the glass; the steel leaf of the dock door is not drawn; the shutter street is crude.
- Contrast 0.36 aggregate, `hold_window` and `route_left` at p50 0.20–0.21.

### Underworld (agent C)
- The scene is lilac corridors; the painting is near-black basalt over a lava LAKE under a red sky. Author `pitch`
  (about −14) on the choice place and turn the reference viewpoint so it looks ACROSS the abyss: the lake and the
  far cliffs must fill the lower half of the reference shot, the red sky the upper third.
- The basalt goes near-black with lava rim light from below (emissive at the cliff feet, as round 1 began); the
  vertical-stripe tile visibly repeats: variants or breaks.
- The blue tunnel decal (`hold_cave`) and the blue striped arch tunnel (`route_left`) are flat and off-palette: a
  dark tunnel mouth with one lantern, a path lit by lava.
- `hold_ledge`, `route_left`, `route_right` sit on the rule's lower edge (0.25); the Mothership guide is procedural
  and 82 px; the round 1 flat lift on the basalt tiles comes out.

### Mothership (agent C)
- The rib lattice shouts: white on violet, repeating everywhere. The painting's bone is soft cream with warm amber
  practicals: lower the lattice contrast, make the ribs read as a few sweeping arches (large decal bands at 4–6 m
  intervals) not a fine mesh, 2–3 variants.
- The green pool and the vault are in no shot. Open the ring's inner parapet (lower it, or a step down at the
  reference viewpoint) so the pool's glow is in the lower part of the reference shot; the vault sky must show above
  the ring (the walls rise straight to 9 m: cut them or lower them).
- With `void_top` fixed, check the engine haze over the pool and remove the band decals if they no longer help.
- The right hatch (`route_right`) is a flat grey shutter: the painting's lit doorway.
- The Underworld guide is 62 px (the edge) and procedural; the Booth guide procedural.

## Procedure (per scene, in order)
1. Merge nothing; the lead merged env (with the engine hooks) into your branch before you started. `--import` first.
2. Reference shot beside the painting; the lead's list above is your work list; add what you see.
3. Do the list; reshoot after each item that moves the camera or a wall; `frame_check` every shot.
4. `--filter doom`, `doom_cuts`, `rail_paths`, `run_`, `playtest`, `story`, `choice_pitch` (if you authored `pitch`),
   `check_rail_paths.gd`; count SCRIPT ERROR lines; `make_doom.py` + `--import` if you touched a generator.
5. Scene doc: the lead's list ticked or carried; measured p50/contrast per shot; crop vs procedural per guide;
   refreshed `docs/shots/doom/<scene>/`.

## Additions from the independent review of the branch (9 November)

- **Dock** `route_ahead` holds on an empty dark street with no opening and no guide: turn the hold into the lit far
  end (a doorway, the fourth lamp's pool, a figure) per round 1 step 2.
- **Balcony** 0 of 8 shots in the rule; at the reference view the Mothership guide (72 px) cannot be picked out by
  eye: light her, or move her nearer.
- **Lounge** guides are 66–86 px at 6 m: the smallest in any scene; bring the thresholds nearer or the guides forward.
- **Every scene:** add a **selected** and a **committed** guide-state capture to the shot set (brief §8 of
  `DOOM_WORLDS_BRIEF.md`): the shoot script taps the guide at beat 50 and shoots the hold and the first walk frame.
- **Warehouse, Bar, Booth** blocks of `test_doom_views.gd` lack the wall-sightline check the other five have: add it.
- **Walk legs:** ruling 42 (walk-outs at ≤ 3 m/s, 2..8 bars) lands in the engine this round. Legs longer than
  about 33 m must be shortened or given a hold: wh up 28.3 m, uw right 22.7 m, lg up 21.8 m, dk up 17.7 m are fine
  but will now take 5–7 bars; check each walk strip still reads and no hold stares at a wall on the longer walk.
- **Docs:** `docs/doom/LAUNCH.md` sends the pilot to other worktrees (`MusicGame-envwh`, `MusicGame-env-chill`) and
  its "Known limits (7 November)" are stale: the lead rewrites it after round 2; scene docs must not claim a match the
  sheet does not show (the Mothership's "void and ribs match", the Balcony's "moon and city match" were both wrong).
