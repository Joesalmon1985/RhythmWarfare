# Heights, voids, railings, visibility and rail paths

The renderer and rail extension for the Doom worlds (docs/briefs/DOOM_WORLDS_BRIEF.md sections 3, 4 and 7). A map converted from Doom II
(tools/doom/, another agent) is many convex pieces with floor and ceiling heights; this note says what the StoryMap JSON may now carry, what
the renderer and the rail do with it, what it costs, and what is still approximate. Branch `wip/engine-render`.

The 32 hand-made maps are the degenerate case and are drawn exactly as before: `tools/story/geometry_hash.gd` hashes every mesh the
renderer builds (vertices, UVs, vertex colours, indices, material settings) and gives the same 32 hashes before and after this work.

## What the renderer did before (and still does)

* A sector is a floor polygon and a ceiling polygon at its `floor` and `ceiling` heights (`sky` ceilings are not drawn: the sky shows).
* A solid wall is a quad from the sector's floor to its ceiling.
* A portal (a two-sided line) is open. Seen from each side, it draws a **lower part** from this side's floor up to the other side's floor
  when the other floor is higher (Doom's lower texture: the riser of a step, the face of a ledge), and an **upper part** from the other
  side's ceiling up to this side's ceiling when the other ceiling is lower (Doom's upper texture: the lip). Each face is drawn once, by the
  side it faces. Textures: the wall's `lower_tex` / `upper_tex`, else the wall's `tex`, else the sector's `wall_tex`.
* Visibility: StoryStage asks `StoryMap.visible_sectors` each time the camera moves or turns: a flood through every portal whose opening is
  in the view cone, 4 portals deep for the crowd and 7 for the geometry; sectors not reached are hidden and not lit.
* The rail (StoryPlayer) walks `StoryMap.route` (portal midpoints) and its eye follows the floors with a smooth ramp centred on each portal
  crossed (`climb` ramps over 1.6 m, the rest 0.8 m, never more than 45 % of a leg).

So steps and lips existed; this work adds their own textures, the step / drop rule, voids, railings, a clipping visibility walk for big
maps, polyline moves with holds, and the check.

## Map keys (exact JSON)

Map level (all optional):

```json
{
  "max_step": 0.5,
  "max_climb": 2.0,
  "void_drop": 3.0,
  "visibility": {"mode": "clip", "depth": 48, "far": 0}
}
```

| key | default | meaning |
|---|---|---|
| `max_step` | 0.5 | metres: a floor change across a portal up to this is a step a walker takes (stairs are runs of them); taller is a drop |
| `max_climb` | 2.0 | the limit for a move with style `climb` |
| `void_drop` | 3.0 | a sector whose floor lies this far or more below **every** neighbour and that holds no waypoint, home or spot is a void (0 turns the rule off) |
| `visibility.mode` | `flood` under 64 sectors, `clip` from 64 | which visibility walk (below) |
| `visibility.depth` | 48 | portals deep, clip mode |
| `visibility.far` | 0 (none) | metres: portals farther than this are not looked through, clip mode |

Sector (all optional):

```json
{"id": "ledge", "floor": 1.5, "ceiling": 6.0, "wall_tex": "rock",
 "step_tex": "rock_riser", "lip_tex": "trim", "drop": false, "void": false}
```

| key | meaning |
|---|---|
| `step_tex` | the riser drawn where a neighbour's lower floor meets this sector (the step up onto it, the face of the ledge) when the portal names no `lower_tex` |
| `lip_tex` | the lip drawn where a neighbour's higher ceiling meets this sector's lower one, when the portal names no `upper_tex` |
| `drop` | any floor change into or out of this sector is a drop, whatever its height (a ledge you never step off) |
| `void` | a pit: drawn far below, hazed, never stood in (see Voids) |

Wall (on a portal edge):

```json
{"sector": "bridge", "from": [-2, 1], "to": [6, 1], "portal": "pit_n", "kind": "railing", "tex": "rail", "height": 1.0}
```

| key | meaning |
|---|---|
| `kind: "railing"` | a see-through strip along the portal; the portal becomes closed to walkers (as `blocked`) but stays open to the eye |
| `tex` | the railing tile (needs an alpha channel); for a railing it is not used for the step or lip faces of the portal (those fall back to the sector's `wall_tex` as for any portal) |
| `height` | metres above the higher of the two floors (default 1.0) |

Other `kind` values are ignored here (the wall-decal kind lives on `feature/one-pc` and is not reimplemented).

Texture choice at a portal, in order: the wall's `lower_tex` / `upper_tex`; then the higher sector's `step_tex` (riser) or the
lower-ceilinged sector's `lip_tex` (lip); then, for a void's cliff only, the neighbour's `wall_tex` (its wall going on down); then the
wall's own `tex` / the sector's `wall_tex` as before.

## Steps, drops and stairs

`StoryMap.floor_change(a, b, style)` classes the walk from sector a into b: `level`, `step` (|dh| at most `max_step`, or `max_climb` for a
`climb` move), `drop` (taller, or either sector has `drop: true`) or `void` (b is a void). The renderer draws the face either way; the rule
is for the rail and the check: a move may cross a step, never a drop or a void. A stair is a run of thin sectors each a step above the last;
the eye climbs it step by step (each crossing ramps over at most 45 % of the tread).

## Voids

A sector is a void when it is marked `"void": true` or by the depth rule (`void_drop`, nobody stands in it). Each void gets `void_top`, the
lowest floor around it.

* Its floor is drawn at its own `floor` (a converter writes the real depth: the Mothership's chamber, the Underworld's basin).
* The portals around it draw their lower parts in the void's mesh from its floor up to each neighbour's floor: the neighbours' walls going
  on down as cliff faces (texture: `lower_tex`, else the neighbour's `step_tex`, else the neighbour's `wall_tex`).
* Haze by depth, baked into the vertex colours (no new pass): `haze = 0.9 x clamp((void_top - y) / (void_top - floor))`, and the colour is
  multiplied toward the fog colour (normalised to its brightest channel) at 30 % brightness. The pit's floor is dark and tinted; the cliff
  fades into it; the map's distance fog adds to that as before. The far side of a void is drawn because the visibility walk goes through
  the void's portals (a railing never stops the eye), and its cliff face is part of the void's mesh.
* The camera is never placed in a void: a waypoint, home or spot in a marked void is a map error, the depth rule never makes a void of a
  sector someone stands in (the Mothership's reactor, 4 m down, stays a room), and the check rejects any rail sample in a void.

## Railings

A `railing` wall is a cut-out strip (alpha scissor 0.5, nearest filtering, unshaded, double-sided, no blending, no depth sorting) from the
higher floor up `height` metres, in the higher sector's mesh (lit by its song-time light and its lamps like its walls). The texture is
stretched to the railing's height (v 0 to 1) and repeats along it at the tile's aspect. The portal under it is closed to walkers
(`neighbors`, `route` and the check never cross it) and open to the eye (the visibility walk ignores it). The figure cap is untouched (the
railing is geometry, not a person).

## Visibility

`visible_sectors` keeps the flood for maps under 64 sectors (every hand-made map: they draw exactly as before). From 64 sectors, or with
`visibility.mode: "clip"`, it is a portal walk that narrows the view window at every portal (the classic portal renderer's culling in the
ground plane): from the camera's sector, a portal is looked through only where its angular extent overlaps the window it is seen through,
and the next sector is walked with the overlap. A room behind a solid wall is never reached; an open hall cut into pieces is seen to its
far end (48 portals by default, not 7). Breadth first, so each sector's depth is its fewest portals; a sector already walked with a wider
window is not walked again. Portals with no opening (ceiling at or below the floor beyond) stop the eye; a portal within 0.3 m of the camera
passes the whole window. In clip mode the crowd's depth argument (4) is not used: the same window decides both.

The test is `tests/test_story_visibility.gd`.

## Rail paths

A `player_move` (and a rail place of `content/run/run.json` / `content/paths/*/run.json`) may carry:

```json
{"to": "bridge_end", "via": ["stair_top", "bridge_start"], "style": "walk", "bars": 4, "hold_bars": 1}
{"path": ["stair_top", "bridge_start", "bridge_end"], "style": "walk", "bars": 4}
{"to": "balcony_view", "role": "on_stage", "bars": 3, "choice": true, "hold_bars": 3}
```

| key | meaning |
|---|---|
| `via` | waypoint ids walked through in order before `to`: each leg is a straight line traced through the map |
| `path` | the same, `to` being the last id |
| `hold_bars` | after arriving, the camera stands still for this many bars: no bob, no drift, no glance (eased in and out over a beat) |
| `choice` | (rail places) a choice viewpoint: it must hold at least `RunRail.CHOICE_HOLD_BARS` = 3 bars, the whole choice window |

What the player does with a polyline move (StoryPlayer):

* Each leg is traced (`StoryMap.trace_segment`); the walk goes through the via points at a constant share of the eased move, the move still
  starting at its song time and lasting its bars (the song clock stays the driver: the pose is a pure function of song time; pause, restart,
  tempo handoffs and rhythm outcomes are untouched).
* Facing: from the start yaw it turns toward the way ahead over the first 20 % of the move, follows the way ahead (the direction from 2 m
  behind to 2 m ahead along the path, so a corner turns over about 4 m of walk), and turns to the arrival yaw over the last 30 %. Bob and roll
  are at 60 % on a polyline move; the pitch is untouched (the pads stay readable).
* The eye follows the floor of each piece crossed (the same ramp as before at every crossing).
* A leg that would cross a wall, a railing, a drop or a void is a data error: the player records it and walks that leg by the portal route
  instead (never through the wall); the check reports it before it ships.
* A plain move (no `via`) is exactly as before.

Choice windows (the run's block-3 window, beats 49 to 60.5): when the rail's place at the decision before the window (block 2) is a choice
viewpoint, the walk to it is shortened so it lands by beat 49, `RunJourney` gives a `player_hold` (new action: `{"bars"}`, the camera stands
still) from beat 49 to 60.5, and the window's face look, glance and stroll are left out: the viewpoint frames the choices by itself. A choice
viewpoint's own `hold_bars` (at least 3) keeps the strolls of the next blocks away too. Without `choice` the window is as before.

## The check

`tools/story/check_rail_paths.gd` (StoryRailCheck): for every run scene's rail, every move it can make (up the good rail, down and back the
bad rail with the reversed `via`, the drop from a good place to the bad rail, the arrival):

* each straight leg of a `via` move is traced: crossing only portals open to walkers, into sectors that are not voids, over steps for its
  style, through openings with room for the eye (eye height + 0.1 m);
* a plain move's portal route crosses no drop and no void for its style;
* the move is played on a StoryPlayer (no bob, no drift) and sampled 97 times: inside a walkable sector, never in a void, the eye within
  [1.4, 1.8] m above the local floor and 0.1 m under the ceiling. The local floor is the sector's floor, except across a step, where it is
  the stair line (straight from one floor to the other over the span the eye ramps over);
* every choice viewpoint holds at least 3 bars.

    godot --headless --path . -s tools/story/check_rail_paths.gd -- [run.json ...] [--node=<filter>]

## Budget figures

Measured with `tools/art/frame_time.gd` (new: no frame-time tool existed), **desktop, headless** (Godot 4.5.1, the dummy renderer and the
Dummy audio driver on the owner's Windows PC, 300 frames after 30 warm-up frames, the camera turning half a degree a frame so the visible
set is worked out every frame, as on a walk). These are CPU figures on a desktop, not phone figures. Headless the frame itself is paced
(6.9 ms whatever the work) and the dummy renderer draws nothing, so the useful numbers are the two CPU parts the work changes and the
counts a GPU would get:

* **vis**: the two portal walks StoryStage does each frame the camera moves (the crowd's and the geometry's);
* **world**: `set_visible_sectors` + `StoryWorld.update` (the song-time light of every drawn sector and billboard);
* **drawn**: mean visible sectors, their triangles, their surfaces (one draw call each) and visible billboards.

| map (pieces) | mode | vis mean / p95 ms | world mean / p95 ms | sectors | triangles | surfaces (draw calls) | billboards |
|---|---|---|---|---|---|---|---|
| mothership (25), start | none (no culling) | 0.005 / 0.008 | 0.97 / 1.29 | 25.0 | 5036 | 90.0 | 78.0 |
| mothership (25), start | flood (before, and still its default) | 0.22 / 0.38 | 0.52 / 1.02 | 12.3 | 2487 | 45.1 | 34.1 |
| mothership (25), start | clip (forced) | 0.18 / 0.26 | 0.63 / 1.01 | 10.3 | 1940 | 37.8 | 25.5 |
| underworld (21), start | none | 0.006 / 0.010 | 1.30 / 1.71 | 21.0 | 5022 | 57.0 | 120.0 |
| underworld (21), start | flood (before, and still its default) | 0.18 / 0.30 | 0.87 / 1.33 | 7.8 | 2635 | 26.7 | 64.6 |
| underworld (21), start | clip (forced) | 0.09 / 0.12 | 0.75 / 1.10 | 5.8 | 2326 | 22.9 | 59.6 |
| synthetic 5x4 (400), mid-room | none | 0.011 / 0.009 | 2.39 / 3.47 | 400 | 2320 | 1060 | 0 |
| synthetic 5x4 (400), mid-room | flood (what a converted map would get without this work) | 6.59 / 9.25 | 0.71 / 1.03 | 43.2 | 239 | 111.7 | 0 |
| synthetic 5x4 (400), mid-room | clip (its default) | 0.76 / 1.15 | 0.77 / 1.07 | 48.8 | 265 | 124.4 | 0 |
| synthetic 6x4 (576), mid-room | none | 0.005 / 0.008 | 3.54 / 4.23 | 576 | 3336 | 1524 | 0 |
| synthetic 6x4 (576), mid-room | flood | 10.59 / 13.67 | 1.12 / 1.43 | 43.2 | 239 | 111.7 | 0 |
| synthetic 6x4 (576), mid-room | clip (its default) | 0.90 / 1.39 | 1.13 / 1.57 | 52.9 | 287 | 134.9 | 0 |

The synthetic maps (`--synthetic=RxP`: R x R rooms of P x P pieces of 2 m, one door per shared side, floors stepping 0.2 m from room to room,
Mothership tiles) stand in for a converted Doom map until tools/doom/ delivers one. Reading: the flood's cost grows with the map (each
frontier sector scanned every portal of the map: 6.6 ms at 400 pieces, 10.6 at 576 on this desktop, far over a phone's budget) and its depth
limit of 7 both drops visible pieces of an open hall and keeps pieces behind walls; the clip walk stays under a millisecond here, draws what
the window shows (about 50 pieces, 125 to 135 draw calls in a room with doors), and on the hand-made maps it would draw a little less than
the flood (they keep the flood so they draw exactly as before). Without culling a 576-piece map is 1524 draw calls a frame: the culling is
what keeps a converted map inside the budget (docs/STORY_25D_PLAN.md 8.4: 12 ms mean, 20 ms p95 at 270p on the phone).

    godot --headless --audio-driver Dummy --path . -s tools/art/frame_time.gd -- --map=mothership --mode=clip
    godot --headless --audio-driver Dummy --path . -s tools/art/frame_time.gd -- --synthetic=5x4 --mode=flood

## What remains approximate

* **Visibility is worked out in the ground plane.** The clip walk narrows by the portals' plan-view extent only: a step's riser or a lip
  that hides part of an opening does not narrow it (the walk is conservative there), and a sector seen only over the top of a wall (a sky
  ceiling with a tall billboard behind a low wall) is not reached in clip mode, so such a billboard can pop in a converted map. The
  hand-made maps keep the flood and are not affected.
* In clip mode the crowd and the geometry share one walk: the crowd is drawn as deep as the geometry (the flood kept the crowd to 4 portals).
* **The void haze is a multiplier** on the vertex colours: it darkens and tints toward the fog colour, it cannot lighten toward a pale fog.
  It is linear in depth from the walkway down to the void's floor; the map's distance fog adds to it as before. No height fog, no new pass.
* The depth rule for voids is on by default only for maps of 64 pieces or more; hand-made maps opt in with `void_drop` (two Bassment
  maps have 6.5 m pits nobody stands in that would otherwise change look).
* A railing is one strip per portal edge (no posts, no thickness), drawn in the higher sector's mesh; its tile must carry alpha.
* **Polyline moves have corners**: the walk goes straight through each via point at the move's eased speed (no slowing at corners); only
  the facing is smoothed (over 2 m either side). Bob and roll are reduced on a polyline move, not removed.
* The eye's ramp at each floor change is a smoothstep over at most 0.8 m (1.6 m for `climb`), at most 45 % of either leg: a stair of narrow
  treads climbs tread by tread, quickly. The check's "local floor" across a step is the stair line over that span, a model of how a person's
  eye follows a stair, not a measurement.
* A move to a choice viewpoint decided just before the window is shortened to land by beat 49: it can be shorter than the usual 2 bars
  (a quicker walk). A held face look (the heralds' look) is not frozen by a hold; the choice window's own face look is left out at a choice
  viewpoint.
* **The existing rails fail the 0.5 m step rule in places** (`check_rail_paths.gd`, 84 scenes, 49 findings, all on the hand-made maps): the
  Warehouse stage riser and balcony stairs (0.6 to 0.8 m per step, style walk), the Underworld tiers (1.8 m, style walk) and its pit route
  that walks through the lava sectors (2.1 m down and up again: the portal route goes through the basin), the Ward courtyard stage
  (0.6 m). The maps and rails are unchanged; these are for their owners (raise `max_step` on those maps, mark the moves `climb`, or add
  steps).
* Figures are desktop, headless: no phone was measured, and headless the renderer draws nothing (GPU time is not in them); the 400 and 576
  piece maps are synthetic, not converted Doom maps (tools/doom/ is not on this branch).
* Nothing here was looked at on screen: no screenshot of a void, a railing or a polyline walk was taken (headless only).
