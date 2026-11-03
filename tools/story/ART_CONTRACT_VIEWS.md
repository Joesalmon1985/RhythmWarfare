# Story Campaign: extra views (a moving, Doom-style camera) for chapters 2 and 3

Read `tools/story/ART_CONTRACT.md`, `ART_CONTRACT_CHAPTERS.md`, `docs/STORY_ART.md` and the chapter's existing generator modules first.

Design change: only Night One keeps a fixed camera. Every later chapter takes the player **around the world** as the set progresses:
the camera "walks" forward into the next room (a dolly: the room swells toward its vanishing point with parallax and a head bob, the next
room resolves out of it) or turns to look a different way (a yaw: rooms slide past with parallax). Each stop is a **view**: a full
1280 x 720 design-space room drawn from the DJ's eye line, exactly like the chapter's existing room (which becomes the view `main`).
The pads stay at the bottom; each room's lower 260 px is covered by the desk strip, crowd feet are at y <= 440.

## What to deliver per chapter (additive: the existing `main` view and every current asset stay as they are)

Add `stage.views` to the chapter's `manifest.json`: a list of **three new views** (so four rooms with `main`), each:

```json
{"id": "gallery", "title": "Observation gallery",
 "layers": [{"id": "backdrop", "file": "source/views/gallery_backdrop.svg", "pos": [0,0], "size": [1280,720], "px_scale": 0.5},
            {"id": "front_frame", "file": "...", "pos": [..], "size": [..], "px_scale": 0.5, "z": "front"}],
 "anchors": { "floor_rows": [{"y":..,"scale":..} x5, front scale 1.0, feet y <= 440], "floor_polygon": [...], "floor_grid": {...},
              "light_points": [[x,y] x8], "led_screen": [x,y,w,h], "circle_centre": [x,y], "circle_radii": [rx,ry],
              "horizon_y": 130, "vanish": [x,y], "doorway": [x,y,w,h], "woofers": [[cx,cy,r], ...], "riser": [cx,floor_y,w],
              "disco_ball": [x,y], "wall_left_x": n, "wall_right_x": n },
 "pieces": [ {id, file, pos, size, px_scale, pivot?, anim, z, blend?, view-specific ids unique across the chapter} ],
 "palette_hint": "cool"}
```
- `layers` are back-to-front static layers; `z: "front"` layers (arches, rails, foreground silhouettes) draw over the crowd, default behind it.
- `anchors` follow the chapter's existing `stage.anchors` conventions; every key is optional **except** `floor_rows` (5 rows),
  `floor_polygon`, `light_points` (8), `circle_centre`, `circle_radii`, `vanish`. A missing optional key makes the runtime skip that feature
  in that room (no woofer pulses, no LED screen, no doorway). Keep the `stage.sprites` ids shared: the runtime re-uses the chapter's
  `fixture`, `woofer`, `beam`, `glow`, `spot_pool`, haze etc. for every view.
- 2 to 4 `pieces` per view for authored beats (they use the same `anim`, `z`, `blend` rules as `stage.pieces`; ids must not collide).
- The rooms must read as **different places** (architecture, props, light), not recolours, and form a believable route: the runtime moves
  `main -> A` (walk), `A -> B` (turn), `B -> C` (walk), `C -> main` (turn) among others, so each room should feel like part of one
  location with plausible neighbours. The `vanish` point is where the dolly pushes toward when walking *out of* that view (the way ahead).

Also add `stage.sprites.passage_frame` (optional but wanted): a large frame (door arch / hatch / gate) with the opening in the middle that
the camera passes through during a "step through" transition, centre pivot, authored to span the 1280 x 720 frame when scaled 2x.

## Chapters and rooms

- `mothership` (existing `main` = the dance deck): `gallery` (an observation gallery with a vast curved window onto the planet, bar and lounge
  seating, long perspective corridor feel), `reactor` (the reactor ring chamber: a glowing core, energy pylons, catwalk floor), `bridge`
  (the command bridge: banked consoles, a captain's chair on a dais, huge viewscreen showing the star field).
- `underworld` (existing `main` = the gate and arena): `court` (an obsidian court of columns and braziers leading to a throne),
  `pit` (a lava lake with bone bridges and rising flame, a stage platform out on the lake), `furnace` (the great forge: chains, anvils,
  molten channels, a huge demonic face in the wall).

## How to work

Each chapter agent works only in its own modules (`tools/story/art/mothership_stage.py` or `uw_stage.py` and new `views_*.py` files),
keeps `build_assets.py` / `check_assets.py` untouched (the runtime owner extends the checker), appends a short section to
`docs/STORY_ART.md`, extends the chapter's preview scene so each view can be rendered with the crowd rig for review, and checks real Godot
screenshots. Determinism and Night One / existing chapter files must stay byte-identical except for the manifest gaining `stage.views`
and `stage.sprites.passage_frame`.
