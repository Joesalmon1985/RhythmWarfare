# Mothership scene (doom_mothership): composition and mapping to the painting

Reference: `art/reference/doom_worlds/Mothership Ringwalk Over the Void-7.png`. Map: `content/story/maps/doom_mothership.json` (MAP11 Circle of Death), APPROXIMATE and **invented from the painting**: the render trace
(`tools/doom/trace/mothership.json`: a grass basin, a ten sided ring, two black voids) does not give one violet atrium with a ring walk round a void, so `tools/doom/trace/mothership_scene.py` builds the room
(`mothership_pilot.json`) and `tools/doom/author_mothership.py` dresses it. The ring is round, so the grid is 0.125 m. Routing: ahead Underworld, left Booth, right Dock.

## What the reference shows, and where it is in the map (metres, x east, y north, atrium centre (0, 14))

| Painting | Map piece |
| --- | --- |
| Ring walkway, wide, oval flagstones, drain slots | `ring_0..15`, 3.5 m wide between radius 6 and 9.5 m, walls 9 m; viewer `ms_ref` at 112.5 degrees below the centre, looking east-north-east |
| Pale bone rib lattice walls | the outer wall: `ms_wall_rib`, `_b`, `_c` (256 px tiles, 2 m, three variants, one per ring piece in turn); the alcoves are bone too (`_b` at the Underworld stair, `_c` at the Dock) |
| Void on the left, glowing green pool far below, arch legs | 15 wedge sectors `void_*` (radius 3 to 6 m), floor -9 m, `void: true`; the cliffs into it are `ms_void_cliff` (the ring's, bridge's and platform's `step_tex`); a `ms_void_haze` band on every wedge's cliffs (ring side and platform side, emissive); eight green pool lamps 1 m over the pool (void sectors only); pillars (`ms_pillar`) rise from it |
| Balustrade with oval openings | `kind: railing`, `blocked: true`, `ms_rail`, 1.1 m, on every ring/void, platform/void and bridge/void edge (31 pieces) |
| Amber lamps along the rail's foot | `ms_rimlamp_0..15` (small glowing blocks on the ring's inner edge every 22.5 degrees), each with a warm pool `ms_lt_rim_*` |
| The vault | the map's `sky` (`ms_sky`: dark vault with pale arches over the violet haze); the ring, void, bridge and platform are open to it, the alcoves keep `ms_ceil` |
| DJ platform in the void, bridge, Booth guide | `platform` (3 m radius) on the `bridge`; guide `ms_guide_booth` at (0, 15.8), threshold `ms_booth_hatch` |
| Red horned drummer at the top of a stair ahead | alcove `uw_s1`, `uw_s2` (0.375 m risers), `uw_land`, `uw_hatch`; hatch decal `ms_hatch_uw` (a bone arch round a passage glowing from within, steps climbing into it); guide `ms_guide_underworld`; threshold `ms_uw_hatch` on the landing, 2 m back from the hatch |
| Green-coat Dock guide, right foreground | alcove `dk_a`, `dk_b` in the outer wall; guide `ms_guide_dock`; threshold `ms_dock_in` in the alcove, 2.5 m back from the hatch |
| Armillary pedestal, organ pipes, hanging cable sphere, crystals, consoles, amber wall lamps | billboards and emissive decals |
| No crowd: the three guides are the only people | `homes` and `silhouettes` empty; the world's story (`content/run/doom/story_doom_mothership.json`) has an empty cast |

Void rule: nobody can enter it (every portal into it is a railing, blocked). StoryMap demands every sector reachable through portals, so ONE edge (`ring_12`|`void_12`, west, outside every guide view) stays an unrailed portal;
it is a void crossing, so the rail and `check_rail_paths` never take it.

Rail (`tools/run/make_doom_mothership.py`): stay loop = hub view, stair view, bridge view (each 2 bars still), then `ms_ref` (choice, 8 bars still). `rail.routes`: `up` (ring to the stair, 7 bars), `left` (ring, bridge, platform), `right` (ring, dock alcove), `stumble`, `arrive`.
One scene `doom_mothership` (geography world, depth 2), its routes straight to `doom_underworld` (up), `doom_booth` (left), `doom_dock` (right); three figure guide hotspots (no rings) and the stay hotspot.

## Stage D round 2: the five differences found at the start, and what was done

Side by side before any change (`ms_ref` against the painting):

1. The walls were a lilac tile with big dark ovals (polka dots), not the painting's thick pale ribs. Done: the oval decals are gone, the rib lattice is wired per ring piece in three variants and in the alcoves, redrawn at 256 px with three to four cells per 2 m tile, thicker warm bone ribs and deep violet openings. It reads as a lattice of streaked ribs, still finer and more regular than the painting's sweeping arches.
2. No warm practicals on the ring; the painting's amber lamps along the rail's foot carry its warm-against-cool light. Done: sixteen rim lamps with warm pools.
3. The pool's green glow was absent: its lamps stood 4 m BELOW the pool floor (a light's `y` is above its sector's floor). Done: eight pool lamps 1 m over the pool, four green rim lights under the lip, haze bands on the cliffs, `ms_void_cliff` on the cliffs. From the ring at eye height the pool is still not in view in any shot (see hooks).
4. A crowd danced on the ring; the painting has nobody but the guides. Done: empty cast.
5. The threshold holds stared at wall (the Dock hatch from 0.9 m, the Underworld hatch from 1 m, both flat red/grey shapes in dark brick alcoves). Done: both held back (2 to 2.5 m), the alcoves in bone, the Underworld hatch redrawn as a lit passage in a bone arch. The Dock hatch is still the old flat shutter decal.

## Exposure

`tools/doom/frame_check.py` (16:9 shots, world band), before and after this round:

| shot | before p50 / p95-p5 | after p50 / p95-p5 |
| --- | --- | --- |
| ref | 0.32 / 0.63 | 0.34 / 0.68 |
| hold_hub | 0.33 / 0.63 | 0.34 / 0.67 |
| hold_stair | 0.26 / 0.75 | 0.28 / 0.73 |
| hold_bridge | 0.29 / 0.68 | 0.28 / 0.70 |
| route_ahead | 0.21 / 0.46 (off) | 0.26 / 0.61 |
| route_left | 0.35 / 0.72 | 0.33 / 0.73 |
| route_right | 0.24 / 0.19 (off) | 0.30 / 0.64 |
| arrive | 0.33 / 0.64 | 0.33 / 0.66 |
| all eight | 0.27 / 0.67 | 0.30 / 0.69 |

Every shot is inside the rule (p50 0.25 to 0.38, p95 - p5 over 0.40). The painting measures p50 0.32, p95 - p5 0.52.

## The guides (ruling 36)

| guide | source | at `ms_ref` (16:9, figure box height) |
| --- | --- | --- |
| Dock (right, bald, green coat, yellow armband) | CROP from this painting (about 335 px tall there), `make_underworld_guides.crop_frames(DOCK_FIG)`: the same sprite the Underworld uses | 105 px |
| Booth (left, the DJ: teal hair, headphones, orange jacket) | PROCEDURAL placeholder: about 110 px in the painting above her desk (under 180 px); make_guides' figure, headphones, finished with warm and cool rims and dithered sequins on the jacket | 142 px |
| Underworld (ahead, red horned drummer, brass drum) | PROCEDURAL placeholder: about 110 px in the painting; horns and drum, rims and sequins on the robe | 62 px |

`tools/doom/art/make_mothership_guides.py`; sheet `docs/shots/doom/mothership/guides_sheet.png`. States: available a lamp-lit rim, selected a brighter rim (the crop also raises the hand), committed turned away. No ring or beacon.

## Shots (docs/shots/doom/mothership/)

`contact.jpg` (the painting beside `ms_ref`, every viewpoint at 16:9 | 20:9), `walk_strip.jpg`, `walk_up.txt`, `walk_left.txt`, `walk_right.txt`, `guides_sheet.png`. Regenerate: `python3 tools/doom/shoot_mothership.py` (needs a window).

**Matches the painting:** the curved ring with the balustrade and the void on the left; the three guides (platform far left, stair ahead, hatch right); pale rib walls in place of the polka dots; amber lamps at the rail's foot against the cool violet; a lit stair alcove with the Underworld hatch glowing; the hanging sphere, crystals and armillary; no crowd.

**Does not match:** the ribs are a flat tiled lattice, finer and more regular than the painting's sweeping three-dimensional arches, and the walls rise straight to 9 m, so the vault sky is not in any shot; the green pool, the painting's main light, is not seen from the ring (the camera cannot pitch down; the haze bands and pool lamps are below the eye's view); the floor has no oval flagstones or drain slots and no wet gloss; the ring's outer wall is faceted (16 chords); the platform is a hub at the centre, not the painting's side platform; the Dock hatch is a flat grey shutter; the Dock guide is mid-ground (105 px), not the painting's large foreground figure; the Underworld guide is small (62 px, the minimum is 60); the Booth and Underworld guides are procedural.

## Placeholders and hooks

Placeholders: every texture, prop and decal (`tools/doom/art/make_mothership_art.py`), the Booth and Underworld guides (procedural), the music (Warehouse arrangements). The Dock guide is cut from the owner's painting.
Hooks (engine, not changed here): (1) the void's depth haze needs `void_top` to be the highest neighbouring floor, or an authored value: StoryMap takes the LOWEST neighbouring floor, and a void split into wedges has wedge neighbours as deep as itself, so `void_top` equals its own floor and the haze is off (the `ms_void_haze` decals stand in); (2) the run's choice hold carries no pitch (`RunJourney.window_face`'s `player_look` has `face` and no pitch), so the choice viewpoint cannot look down at the pool; (3) a way to mark a sector as an unreachable void so the reachability check does not need one open edge.

Regenerate: `python -I tools/doom/trace/mothership_scene.py; python -I tools/doom/convert.py --scene mothership --trace tools/doom/trace/mothership_pilot.json; python -I tools/doom/art/make_mothership_art.py; python -I tools/doom/art/make_mothership_guides.py; python -I tools/doom/author_mothership.py`, then `--import`.
