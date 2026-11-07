# Mothership scene (doom_mothership): composition and mapping to the painting

Reference: `art/reference/doom_worlds/Mothership Ringwalk Over the Void-7.png`. Map: `content/story/maps/doom_mothership.json` (MAP11 Circle of Death), APPROXIMATE and **invented from the painting**: the render trace
(`tools/doom/trace/mothership.json`: a grass basin, a ten sided ring, two black voids) does not give one violet atrium with a ring walk round a void, so `tools/doom/trace/mothership_scene.py` builds the room
(`mothership_pilot.json`) and `tools/doom/author_mothership.py` dresses it. The ring is round, so the grid is 0.125 m (not the Booth's 0.25 m: the arcs break convexity on it). Routing: ahead Underworld, left Booth, right Dock.

## What the reference shows, and where it is in the map (metres, x east, y north, atrium centre (0, 14))

| Painting | Map piece |
| --- | --- |
| Ring walkway, wide, oval flagstones, drain slots | `ring_0..15`, 3.5 m wide between radius 6 and 9.5 m, 9 m vault; viewer `ms_ref` at 112.5 degrees below the centre, looking east-north-east |
| Void on the left, glowing green pool far below | 15 wedge sectors `void_*` (radius 3 to 6 m), floor -9 m, marked `void: true`; green lights at -4 m; pillars (`ms_pillar`) rise from it |
| Balustrade with oval openings | `kind: railing`, `blocked: true`, tex `ms_rail`, 1.1 m, on every ring/void, platform/void and bridge/void edge (31 pieces) |
| DJ platform in the void, bridge, Booth guide | `platform` (3 m radius) on the tapering `bridge`; guide `ms_guide_booth` at (0, 15.8), threshold `ms_booth_hatch` |
| Red horned guide at the top of a stair ahead | alcove `uw_s1`, `uw_s2` (0.375 m risers), `uw_land`, `uw_hatch`; guide `ms_guide_underworld`, threshold `ms_uw_hatch` |
| Green-coat dock guide, right foreground | alcove `dk_a`, `dk_b` in the outer wall; guide `ms_guide_dock`, threshold `ms_dock_in` |
| Armillary pedestal, organ pipes, hanging cable sphere, crystals, consoles, amber wall lamps | billboards and emissive decals |

Void rule: nobody can enter it (every portal into it is a railing, blocked). StoryMap demands every sector be reachable through portals, so ONE edge (`ring_12`|`void_12`, west, outside every guide view) stays an unrailed portal;
it is a void crossing (`floor_change` kind void), so the rail and `check_rail_paths` never take it.

Rail (`tools/run/make_doom_mothership.py`): stay loop = hub view (ring south, platform across the railing), stair view, bridge view (each 2 bars still), then `ms_ref` (choice, 8 bars). Moves are capped at 4 bars, so the loop goes
there and back along the south-east ring and over the bridge, never round the whole ring. `rail.routes`: `up` (ring to the stair, 7 bars), `left` (ring, bridge, platform), `right` (ring, dock hatch), `stumble`, `arrive`.
Node `doom_mothership` plus stand-ins `.underworld/.booth/.dock` and exit scene `.return`; three figure guide hotspots and the stay hotspot.

## Shots (docs/shots/doom/mothership/)

`contact.jpg`, `walk_strip.jpg`, `walk_*.txt`, `guides_sheet.png`. Regenerate: `python3 tools/doom/shoot_mothership.py`. Guides at `ms_ref` (16:9): Booth 142 px, Dock 105 px, Underworld 62 px (60 required).

**Matches the painting:** the curved ring with the void on the left, the three guides (platform far left, stair ahead, hatch right), railings you see through, violet palette, hanging sphere and crystals, a lit stair with a red hatch.
**Does not:** the walls are a lilac tile with big dark ovals that reads as polka dots, not organic ribs; the pool floor is barely visible from the ring (no depth fade, see hooks); no free-standing arches, no mosaic floor gloss, no pedestal in the pool as geometry; the ring's outer wall is faceted (16 flat chords); the bridge tapers; the platform is a hub, not the painting's side platform; the dock and Underworld hatches are flat decals in tiny alcoves, close-up shots of them are blank wall; frame_check: ref p50 0.36 ok, `hold_stair`, `route_ahead`, `route_left`, `route_right` off target.

## Placeholders and hooks

Placeholders: every texture, prop, decal and the guides (Dock guide is the Lounge's character redrawn), the stand-in destinations, the music (Warehouse arrangements). Hooks: (1) the void depth haze needs `void_top` to be the highest neighbouring floor, or an authored value: a void split into
wedges has deep neighbours, so `void_top` equals its own floor and the haze is off; (2) a way to mark a sector as an unreachable void so the reachability check is not needed.
