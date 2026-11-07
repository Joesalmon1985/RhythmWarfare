# Wall decals: pictures flat on a wall

Wall tiles at 96 to 160 texels per metre repeat every metre or so, so the one-off things an old big tile carried (a door, a
notice board, a sign, a window, a clock) are placed in the map instead. A map thing of kind `billboard` turns to face the camera,
which is right for a trolley or a person and wrong for a door in a wall: seen along a corridor it reads as a card standing in the
room. A **decal** is a picture that lies flat on its wall and is drawn and lit as part of that wall.

Engine: `StoryMap._build_decal` and `StoryMap._place_decals` (`src/story/world/story_map.gd`), `StoryWorld._make_decal` and
`StoryWorld._decal_light` (`src/story/world/story_world.gd`). Test: `tests/test_story_decals.gd`.

## Schema

A decal is an entry of the map's `things` with `"kind": "decal"`:

```json
{"id": "cd_s0", "kind": "decal", "sprite": "prop_ward_door_a", "at": [6.8, 2.93], "y": 0.0, "size": 2.1}
{"id": "cw_0",  "kind": "decal", "sprite": "prop_window_lit",  "at": [46.93, -5.0], "y": 1.15, "size": 1.5, "emissive": true}
{"id": "cs_c0", "kind": "decal", "sprite": "prop_wall_sign",   "at": [33.005, 1.25], "y": 2.75, "size": 0.3, "yaw": -90}
```

| Field | Meaning |
| --- | --- |
| `id` | unique among all things, lights and decals of the map |
| `sprite` | a stage sprite of the chapter's manifest, or a map texture name (as for billboards) |
| `at` | `[x, z]`: a point inside the room, at most 0.35 m (`StoryMap.DECAL_REACH`) from the wall it hangs on; it gives the position along the wall |
| `y` | the height of its **bottom edge** above the sector floor (default 0). Note: a billboard's `y` is its centre; a decal's is its bottom |
| `size` | its height in metres (default 1); the width follows the sprite's aspect, as for billboards |
| `yaw` | optional, degrees: the way the picture's face looks (0 toward -z, 90 toward -x, 180 toward +z, -90 toward +x, as `forward_of_yaw`). Overrides the wall; the decal then stands at `at` exactly |
| `emissive` | optional: the picture keeps its own colours (a lit window, a light bar, a screen); the room's song-time light still multiplies it, as for an emissive billboard |
| `sector` | optional, as for things: the sector holding `at` by default |

A decal has no `anim`, `blend`, `piece` or contact shadow.

## How it is placed and lit

- **Facing**: without `yaw`, the engine finds the nearest **solid** wall segment of the decal's sector (portals are skipped) within
  0.35 m of `at`, takes that wall's normal pointing into the sector, and drops `at` onto the wall: that point is the decal's bottom
  centre. The quad stands 6 mm (`StoryWorld.DECAL_GAP`) off the wall, so it never z-fights with it. A decal with no solid wall within
  reach and no `yaw` is a **map error** (`decal <id>: no solid wall of sector ... and no yaw`): the map does not load clean, the
  chapter tests fail. There is no fallback to a billboard.
- **A picture over a doorway** (the upper strip of a portal, where the next room's ceiling is lower) has no solid wall: give it
  a `yaw` and put `at` a few millimetres inside the room on the portal line.
- **Light**: the decal is a child of its sector's mesh (hidden and shown with it) and its material is in the sector's list, so the
  room's song-time light multiplies it exactly as it multiplies the wall. Its vertex colours are the wall's own baked light at those
  points: the wall's shade (walls running along z are darker, `WALL_SHADE_X`) in a room without lamps; in a lit room the lamps' light
  interpolated on the wall's light cells, and the quad is cut on those cells so a lamp's pool runs across it as across the wall.
  So a decal never glows unless it is `emissive`.
- **Drawing**: unshaded, nearest-filtered, alpha scissor at 0.5 (hard alpha), in the opaque pass with the walls, inside the same
  low-res picture and post; it does not turn to the camera. People, billboards, choice doors, heralds and hotspot rings in front of
  it cover it by depth. It costs one small mesh (2 to about 12 triangles) and one material, like a billboard.
- **Scenery only**: decals live in `StoryMap.decals`, not in `StoryMap.things`, and in `StoryWorld._decal_nodes`, not in
  `_thing_nodes`. So a decal is never a hotspot anchor, a crowd look target, a herald's thing, a figure-cap prop or a coverage-audit
  object, and casts no contact shadow. The camera clearance check sees walls only, so a decal does not change what it sees.

## Rules

- **Wall-mounted things are decals, free-standing things are billboards.** Doors that are scenery, boards, signs, dispensers,
  light bars, framed prints, phones, clocks, windows, maps, posters: decals. Trolleys, carts, vending machines, beds, plants,
  chairs, lamps on posts, people: billboards.
- **A thing a hotspot anchors stays a billboard** (`{"thing": id}` in `content/run/hotspots/*.json` resolves only `things`), as do
  choice doors and quest entrances: they are not scenery. Scenery doors stay visibly different from choice doors: shut, dimmer, no
  lamp, no sign of the choice set.
- **Density**: draw decals at 100 to 140 texels per metre (target 128, style guide section 7): a 2.1 m door is about 270 texels tall.
  Keep the real size over the band when they disagree (the Hospital's 64-texel clocks hang at 0.36 to 0.45 m, 142 to 178 texels per
  metre, and its phone at 164: finer than the wall, never coarser).
- Hard alpha only (0 or 255); a decal is not soft art. A glow beside a lit window is a separate `blend: "add"` billboard.
- Keep a decal inside its wall segment: it is not clipped at a corner or at a portal's edge.

## Converting a world's wall props (three steps)

1. **Pick**: list the map's billboards that hang on a wall (within about 0.35 m of a solid wall, with a `y`, or standing on the
   floor flat against a wall like a door). Drop from the list any thing a hotspot anchors (`grep '"thing"' content/run/hotspots/<world>*.json`)
   and any free-standing prop.
2. **Rewrite** each in the map (or in the generator that writes the map, then regenerate): `"kind": "decal"`, the same `id`,
   `sprite`, `at` and `size`, and `y` = the old centre `y` minus half the `size` (a billboard on the floor with no `y` has a bottom of 0).
   Drop `anim`. Keep `emissive` where the art is a light. Add a `yaw` only where there is no solid wall within reach (over a doorway).
   The ids and the billboard counts of other things do not change.
3. **Check**: `bash tools/dev/godot.sh --headless --path . -s tools/story/check_map.gd -- <map id>` loads clean (a billboard that
   hung in a doorway, as the Hospital station's clock did, now fails here: move it onto the solid wall beside it);
   `tests/test_story_decals.gd` and the world's tests pass; shoot the world's scenes with `tools/art/audit_capture.sh` and look along
   each wall: the pictures lie in the wall in perspective, at the right height, do not shimmer between two consecutive frames, and
   nothing pokes through a choice door, a herald or a hotspot ring.

## Limits

- Flat walls only: a decal is one plane. On a curved wall (a polygon of short segments) it takes the nearest segment and may stand
  off the neighbouring ones; split the picture or keep it within one segment.
- No decals on pillars or free-standing walls that are not sector walls (a column drawn as a billboard has no wall to hold one), on
  floors or on ceilings.
- The light is the wall's at the decal's points; a decal that sticks past the end of its wall segment is lit as the wall's end is.
