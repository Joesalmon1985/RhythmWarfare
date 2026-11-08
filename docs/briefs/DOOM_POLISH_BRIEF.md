# Doom worlds, stage D polish round 1: every scene against its painting

Read first: `docs/parallel-development/LEAD_RULINGS.md` 35, 36, 38, 39 (stationary choice moments, no rings; the paintings are
the bar; `art/reference/standard/guide_floor_sprite_standard.png` is the sprite standard; one world one HUD; a guide's tap is
the decision), `docs/briefs/DOOM_WORLDS_BRIEF.md`, `docs/doom/CONVERSION.md`, `docs/doom/LAUNCH.md` (the eight worlds are
now one-scene geography worlds routing straight to each other; `tests/test_doom_cuts.gd` proves a cut), each scene's doc
`docs/doom/scenes/<scene>.md` (its own "what does not match" list is your work list) and its shots in `docs/shots/doom/<scene>/`.
The style guide: `docs/art/STYLE_GUIDE.md` if present (128 texels per metre, the exposure rule p50 0.25–0.38, no flat fills,
dithered highlights, warm practicals against cool ambience).

## The work, per scene, in this order

1. **Side by side.** Reshoot the scene (`tools/doom/shoot_<scene>.py`), put the painting beside the reference viewpoint at
   16:9 and 20:9, and write down, before changing anything, the five biggest differences you can see. Fix those five first.
2. **Composition and framing** at the choice viewpoint: the painting's foreground (the Lounge's sofa and cushion, the Booth's
   desk, the Dock's bollards and pallets, the Underworld's bone chimes and gong) must be in the picture; move the reference
   viewpoint or add the foreground pieces (billboards/things at depth) so it is. The three guides must read as figures at their
   doorways at ≥ 60 px, apart, and the pads must not cover their waists at the thresholds (raise the threshold viewpoints' eye
   line or hold a step back). The threshold holds must not stare at a blank wall (the Dock, Mothership, Underworld shots):
   turn the hold's yaw into the opening, or move the hold.
3. **Exposure and light.** Every shot inside the exposure rule (`tools/doom/frame_check.py`): the Balcony, Underworld and Dock
   are under; lift with practical lamp pools and emissive decals, not a flat ambient. Warm practicals (sodium, amber, lava, LEDs)
   against cool ambience (blue, violet, moon), as the paintings do.
4. **Surfaces.** No flat tiles: brick with mortar variation, wet concrete with puddle gloss baked in, foam, basalt cracks with
   lava glow, mesh, corrugated steel, velvet, studded panels; dithered highlights; the texel density of the style guide; wall
   tiles that do not visibly repeat across a wall (vary per wall, or 2–3 variants). Use the map's `sky` for open ceilings
   (the Dock, Balcony: a storm sky; the Underworld: a red cloud sky; the Mothership: the void's haze) instead of a ceiling tile.
5. **Geometry the painting asks for** where it is cheap in convex sectors: arches/ribs as decal bands, the Lounge's pit sofa
   ends, the Mothership's side platform, the Underworld's deeper abyss (and a steady downward pitch glance at the choice
   viewpoint so the lava reads: `player_look` with `pitch` and `steady`, see `src/story/world/story_player.gd` and A8b's use),
   the Balcony's high walkway as a billboard, the Bar's barrels and bottles, the Booth's big desk as a foreground billboard.
6. **The guides.** Ruling 36. Each guide gets a 256 px-class sheet (four states idle/available/selected/committed, the existing
   stems). Where the painting shows the figure large enough (≥ 180 px tall in the painting), CROP it: `numpy` + PIL are
   available (no cv2/rembg) — build the mask by colour distance from the figure's surround plus a flood from the corners,
   clean it with a small erosion/dilation, scale with nearest-neighbour to the sheet height, derive the four states by small
   edits (a lamp-lit rim for available, a brighter rim and raised hand for selected, a turn-away for committed). Where the
   figure is too small, improve the procedural sprite toward the standard (dithered skin and sequins, a face, readable costume
   colours and silhouette from the painting). Say per guide which it is: crop or procedural. Never put a ring or beacon under
   a guide.
7. **Reshoot and compare again**; `tests` green: `--filter doom`, `doom_cuts`, `rail_paths`, `run_`, `playtest`, `story`
   (count SCRIPT ERROR lines every run; the runner prints 0 failures on a parse error); `check_rail_paths.gd` 0 problems;
   `check_doom_map.gd` per scene OK. Update each scene doc's "what matches / what does not / placeholders" to the new truth.

## Rules

Work only in your worktree and only on your scenes' files (`tools/doom/trace/<scene>_scene.py`, `author_<scene>.py`,
`art/make_<scene>_*.py`, `content/story/maps/doom_<scene>.json`, `assets/story/doom_<scene>/`, `tools/run/make_doom_<scene>.py`
for rail/viewpoint data only, `tests/test_doom_views.gd` only inside your scenes' blocks, `docs/doom/scenes/<scene>.md`,
`docs/shots/doom/<scene>/`). Never `src/`; report hooks. Never push/merge/rebase/reset; WIP checkpoints per scene. The WAD,
Doom textures/sprites/audio and renders are never committed; nor the track packs. Report per scene: the five differences you
fixed, exposure numbers before/after, each guide crop/procedural, what still does not match, test counts. Facts only.
