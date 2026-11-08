# Mothership scene (doom_mothership): composition and mapping to the painting

Reference: `art/reference/doom_worlds/Mothership Ringwalk Over the Void-7.png`. Map: `content/story/maps/doom_mothership.json` (MAP11 Circle of Death), APPROXIMATE and **invented from the painting**: the render trace
(`tools/doom/trace/mothership.json`: a grass basin, a ten sided ring, two black voids) does not give one violet atrium with a ring walk round a void, so `tools/doom/trace/mothership_scene.py` builds the room
(`mothership_pilot.json`) and `tools/doom/author_mothership.py` dresses it. The ring is round, so the grid is 0.125 m. Routing: ahead Underworld, left Booth, right Dock.

## What the reference shows, and where it is in the map (metres, x east, y north, atrium centre (0, 14))

| Painting | Map piece |
| --- | --- |
| Ring walkway, wide, oval flagstones, drain slots | `ring_0..15`, 3.5 m wide between radius 6 and 9.5 m, walls 5.5 m (round 2, were 9: the vault sky shows over them); viewer `ms_ref` at radius 6.9, 112.5 degrees below the centre, looking 47 degrees north of east, the run's choice hold pitched -14 |
| Pale bone ribs, sweeping arches | round 2: one tall bone ARCH decal (`ms_arch_a` / `_b`, 5.3 x 3.2 m, two ribs leaning in to a pointed crown with an amber keystone lamp) on the outer wall of every ring piece but the two hatches, 3.7 m apart; between them the wall is a low-contrast tile (`ms_wall_rib`, `_b`, `_c`: one soft rib on dusky violet, three variants, one per piece in turn); the hatch alcoves keep the close lattice, softened to half its contrast and warmed (`ms_wall_bone`) |
| Void on the left, glowing green pool below, arch legs | 15 wedge sectors `void_*` (radius 2.25 to 6 m), floor -3 m (round 2, was -9), `void: true` but `void_12`, the POOL SHORE (see the hooks); the cliffs `ms_void_cliff` (pale legs, the pool's mint dithered up their lower half), the pool `ms_floor_void` (luminous mint with swirl rings), eight pool lamps 1.5 m over it; the `ms_void_haze` bands on the cliffs (kept: the only mist, see the hooks); arch-leg pillars (`ms_pillar`) from the pool to the rim |
| Balustrade with oval openings | `kind: railing`, `blocked: true`, `ms_rail` (round 2: warm bone, a large oval opening in each panel), 0.95 m (was 1.1), on every ring/void, platform/void and bridge/void edge |
| Amber lamps along the rail's foot | `ms_rimlamp_0..15` (small glowing blocks on the ring's inner edge every 22.5 degrees), each with a warm pool `ms_lt_rim_*` |
| The vault | the map's `sky` (`ms_sky`: dark vault with pale arches over the violet haze); the ring, void, bridge and platform are open to it, the alcoves keep `ms_ceil` |
| DJ platform in the void, bridge, Booth guide | `platform` (2.25 m radius, was 3: the pool round it is wider) on the `bridge`; its props drawn in; guide `ms_guide_booth` at (0, 15.6), threshold `ms_booth_hatch` |
| Red horned drummer at the top of a stair ahead | alcove `uw_s1`, `uw_s2` (0.375 m risers), `uw_land`, `uw_hatch`; hatch decal `ms_hatch_uw` (a bone arch round a passage glowing from within, steps climbing into it); guide `ms_guide_underworld`; threshold `ms_uw_hatch` on the landing, 2 m back from the hatch |
| Green-coat Dock guide, right foreground; the lit corridor beyond | alcove `dk_a`, `dk_b`, then `dk_c` (round 2: a lower passage 3 m on, amber floor lamps) ending in the lit doorway `ms_hatch_dock` (a bone oval arch round a corridor running on, amber lamps on a wet floor, a warm far door; the grey shutter is gone); guide `ms_guide_dock`; threshold `ms_dock_in` |
| Armillary pedestal, organ pipes, hanging cable sphere, crystals, consoles, amber wall lamps | billboards and emissive decals |
| No crowd: the three guides are the only people | `homes` and `silhouettes` empty; the world's story (`content/run/doom/story_doom_mothership.json`) has an empty cast |

Void rule: nobody can enter it (every portal into it is a railing, blocked). StoryMap demands every sector reachable through portals, so ONE edge (`ring_12`|`void_12`, west, outside every guide view; `void_12` is the pool shore in round 2) stays an unrailed portal;
it is a void crossing, so the rail and `check_rail_paths` never take it.

Rail (`tools/run/make_doom_mothership.py`): stay loop = hub view (2 bars, 1 still), then `ms_ref` (choice, 8 bars still, `pitch` -14). Round 2: one reveal, not three (the rail steps one place per passed block, so with four places the choice place is not reached by the window: see the Underworld's doc); the stair and bridge views stay as waypoints and shots. `rail.routes`: `up` (ring to the stair, 7 bars), `left` (ring, bridge, platform), `right` (ring, dock alcove), `stumble`, `arrive`.
One scene `doom_mothership` (geography world, depth 2), its routes straight to `doom_underworld` (up), `doom_booth` (left), `doom_dock` (right); three figure guide hotspots (no rings) and the stay hotspot.

## Stage D round 1 (polish brief 1): the five differences found at the start, and what was done

Side by side before any change (`ms_ref` against the painting):

1. The walls were a lilac tile with big dark ovals (polka dots), not the painting's thick pale ribs. Done: the oval decals are gone, the rib lattice is wired per ring piece in three variants and in the alcoves, redrawn at 256 px with three to four cells per 2 m tile, thicker warm bone ribs and deep violet openings. It reads as a lattice of streaked ribs, still finer and more regular than the painting's sweeping arches.
2. No warm practicals on the ring; the painting's amber lamps along the rail's foot carry its warm-against-cool light. Done: sixteen rim lamps with warm pools.
3. The pool's green glow was absent: its lamps stood 4 m BELOW the pool floor (a light's `y` is above its sector's floor). Done: eight pool lamps 1 m over the pool, four green rim lights under the lip, haze bands on the cliffs, `ms_void_cliff` on the cliffs. From the ring at eye height the pool is still not in view in any shot (see hooks).
4. A crowd danced on the ring; the painting has nobody but the guides. Done: empty cast.
5. The threshold holds stared at wall (the Dock hatch from 0.9 m, the Underworld hatch from 1 m, both flat red/grey shapes in dark brick alcoves). Done: both held back (2 to 2.5 m), the alcoves in bone, the Underworld hatch redrawn as a lit passage in a bone arch. The Dock hatch is still the old flat shutter decal.

## Exposure (stage D polish round 2)

`tools/doom/frame_check.py` per 16:9 shot (world band), p50 / p95 - p5. Before = this branch at the start of round 2; after = the final shots. The lamps' gain is 1.9 (was 2.4): with
the lower walls and the arches the scene read too bright (`route_left` 0.43).

| shot | before | after | rule |
| --- | --- | --- | --- |
| ref (the run's choice hold, pitch -14) | 0.34 / 0.68 | 0.31 / 0.55 | ok |
| hold_hub (the stay loop's reveal) | 0.34 / 0.67 | 0.31 / 0.53 | ok |
| hold_stair (a view) | 0.28 / 0.73 | 0.26 / 0.57 | ok |
| hold_bridge (a view) | 0.28 / 0.70 | 0.30 / 0.55 | ok |
| route_ahead | 0.26 / 0.61 | 0.30 / 0.49 | ok |
| route_left | 0.33 / 0.73 | 0.37 / 0.68 | ok |
| route_right | 0.30 / 0.64 | 0.31 / 0.44 | ok |
| arrive | 0.33 / 0.67 | 0.30 / 0.52 | ok |
| all eight | 0.30 / 0.69 | 0.30 / 0.56 | 8 of 8 in the rule (8 of 8 before) |

The guide-state captures (not in the eight): selected 0.34 / 0.57, committed 0.29 / 0.61. The painting measures p50 0.32, p95 - p5 0.52.

## The guides (ruling 36)

| guide | source | at `ms_ref`, the pitched choice hold (16:9, figure box height, `test_doom_views`) |
| --- | --- | --- |
| Dock (right, bald, green coat, yellow armband) | CROP from this painting (about 335 px tall there), `make_underworld_guides.crop_frames(DOCK_FIG)` | 146 px |
| Booth (left, the DJ: teal hair, headphones, orange jacket) | PROCEDURAL placeholder (about 110 px in this painting above her desk) | 140 px |
| Underworld (ahead, red horned drummer) | round 2: CROP from `Three Visitors in the Basalt Underworld-6.png` (seated at his two drums, about 330 px tall there; `UW_DRUM_FIG` in `make_mothership_guides.py`, a traced outline; a few grey pixels of the rock remain by the sticks and under the drums) | 74 px (was 62: the view turned toward him) |

`docs/shots/doom/mothership/guides_sheet.png`. States: available a lamp-lit rim, selected a brighter rim and the hand (the sticks) raised, committed turned away. No ring or beacon.

## Shots (docs/shots/doom/mothership/)

`contact.jpg`: the painting beside `ref` (the run's choice hold: `ms_ref` pitched -14), every viewpoint at 16:9 | 20:9, and the guide-state pair (`selected`: the run's own camera
just after the Underworld guide is tapped at beat 50 of the window; `committed`: the first frame of the walk-off). `walk_strip.jpg`, `walk_up/left/right.txt`, `guides_sheet.png`.
Regenerate: `python3 tools/doom/shoot_mothership.py` (needs a window).

Walk legs (lengths from the map's waypoints): up 18.0 m, left 10.3 m, right 11.4 m.

**Matches the painting:** the ring walk curving away with the balustrade and the void on the left; the walls read as tall bone arches over a soft wall, the vault's dark arched sky
above the ring; the pool's mint light on the arch legs and cliffs below the parapet (lower left of the reference shot); the three guides (the DJ on the platform left, the drummer
at the top of the stair ahead, the Dock guide at his hatch right); amber lamps at the rail's foot against the violet; the dock hatch opens on a lit corridor.

**Does not match:** the pool shows only in the lower left corner and through the parapet's ovals, not as the wide glowing lake the painting looks down on (the platform still stands in
the middle of the void; the painting's platform is to the side); the arches are flat decals, not the painting's sweeping three-dimensional ribs, and the ring wall is faceted (16
chords); the floor's ovals are a texture with no wet gloss; the Booth guide is procedural; the drummer is a seated crop (the painting shows him standing with a drum); the hanging orb is
a billboard over the platform.

## The lead's list (round 2)

- [x] The rib lattice shouts: the lattice is gone from the ring walls; one large bone arch decal per piece (3.7 m apart, two variants) over a low-contrast tile (three variants); the alcoves' lattice at half contrast.
- [x] The green pool and the vault in no shot: walls 5.5 m (vault sky above the ring in every ring shot), the pool 3 m down, the platform smaller, the parapet 0.95 m with large openings, `ms_ref` 0.85 m nearer the rim and `pitch` -14: the pool's glow is in the lower left of the reference shot (a corner, not a lake: see above).
- [x] The engine haze over the pool (`void_top` over the connected group): it is on, and it turns the pool dark violet (a multiplier toward 30 % of the fog), the opposite of the painting's glowing pool. The scene opts out with the pool shore (hooks); the haze band decals are KEPT (with the engine haze off they are the pool's only mist; the final set was not reshot without them).
- [x] The right hatch, a flat grey shutter: now a lit passage (`dk_c`) ending in a lit doorway.
- [x] The Underworld guide 62 px and procedural: cropped, 74 px.
- [ ] The Booth guide procedural: carried (about 110 px in the painting; no larger view of her in the Mothership paintings).
- [x] Added: the stay loop is one reveal and the choice viewpoint (so the window is held at `ms_ref`); selected and committed captures in the contact sheet; convert.py's `trim` (Night One's brass truss) was the texture of every cliff into the void, now cleared so the cliffs are `ms_void_cliff`.

## Placeholders and hooks

Placeholders: every texture, prop and decal (`tools/doom/art/make_mothership_art.py`), the Booth guide (procedural), the music (Warehouse arrangements). The Dock and Underworld guides are cut from the owner's paintings.

Hooks and engine notes (engine not changed here): (1) `pitch` works (the choice hold looks down -14); after a tap the camera turns to the tapped guide and walks off at once. (2) The
split-void `void_top` haze darkens a glowing pool: the scene opts out with the POOL SHORE (`void_12`, the wedge behind every guide view, at the pool's level and not a void: the
group's lowest rim floor is then the pool itself, so the haze is zero); a per-void "glow, no haze" key would say this directly. (3) A way to mark a sector as an unreachable void so
the reachability check does not need one open edge (as round 1).

Regenerate: `python -I tools/doom/trace/mothership_scene.py; python -I tools/doom/convert.py --scene mothership --trace tools/doom/trace/mothership_pilot.json; python -I tools/doom/art/make_mothership_art.py; python -I tools/doom/art/make_mothership_guides.py; python -I tools/doom/author_mothership.py; python tools/run/make_doom.py`, then `--import`.
