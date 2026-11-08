# Geography worlds

A geography world is one place in a map of places (the Doom scenes: Warehouse, Bar, Balcony, Chill-out, Booth, Dock,
Mothership, Underworld). Each place is its own world on its own map; each of its routes leads to another place's world.
Cycles are the point (Floor -> Bar -> Floor). Contract: `docs/parallel-development/CONTRACTS.md` section 1 and hook H1.6.
Code: `src/run/run_data.gd` (`is_geography`, `_validate_geography_routes`), `src/run/run_journey.gd` (`threshold_of`,
`threshold_move`, `threshold_leave`), `src/run/run_play.gd` (`_update_passage`). Tests: `tests/test_geography.gd`.

## What a generator emits for a one-scene geography world

`worlds` entry: `id`, `title`, `map`, `depth`, `blurb`, `"geography": true`. `depth` still sets the tier and the home
cards. There is no depth rule between geography worlds.

The scene (a `nodes` entry):

- `id` = the world id, `world`, `scene`, `title`, `"entry": true`. `exit_scene` is optional, because the entry may be the exit.
- `next`: a stay `{to: <own id>, dir: "down", loop: true}`, and one or more routes out
  `{to: <entry scene id of another geography world>, dir: up|left|right, label}`. Directions are unique.
- `place.waypoint`: home.
- `place.rail`: `good`, `bad`, `glances`, `strolls` as for any scene. Also:
  - `arrive`: where the player steps in from another world.
  - `exits {dir: waypoint}`: one doorway per `next` direction, `down` included.
  - a choice viewpoint (a `good`/`bad` place with `"choice": true`, `hold_bars >= 3`) may author `pitch`: degrees, negative looks down, within +-35,
    default 0. The camera holds that pitch, still, through the whole choice window and lets it go with the walk-off (below). Use it where the
    viewpoint looks down at its feature (a lava lake, a sunken sofa); the facing is still the waypoint's `yaw`. Unauthored, nothing changes.
  - `routes {up|left|right: move}`: each move is `{to, via?: [waypoints], bars, hold_bars?: >= 0, style?, role?}`. `bars` must be above 0; the walk clamps it to 2..4 bars, then to the time left before the boundary. A walk-out from a tap takes more when the leg needs it (ruling 42, below).
    `to` is the threshold, normally the same waypoint as `exits[dir]`. `stumble` and `arrive` keys are allowed. `down` has no move.

All waypoints (`to`, `from`, `via`) must exist in the world's map. A `thresholds {to: waypoint}` dict on the node is
still honoured, and wins over the route move. A generator does not need to write it.

An example follows. Its waypoint names are made up for illustration; a working fixture is in `tests/fixtures/geography/run.json`.

```json
{"worlds": [{"id": "doom_bar", "title": "The Copper Bar", "map": "doom_bar", "depth": 2, "geography": true, "blurb": "..."}],
 "nodes": [{
  "id": "doom_bar", "world": "doom_bar", "scene": "bar", "title": "The Copper Bar", "entry": true, "exit_scene": true,
  "next": [
   {"to": "doom_bar", "dir": "down", "label": "Stay at the bar", "loop": true},
   {"to": "doom_booth", "dir": "up", "label": "Up to the booth"},
   {"to": "doom_warehouse", "dir": "left", "label": "Back to the floor"},
   {"to": "doom_lounge", "dir": "right", "label": "Into the chill-out"}],
  "place": {"waypoint": "bar_ref", "rail": {
   "good": [{"to": "bar_counter", "bars": 3, "hold_bars": 2}], "bad": [{"to": "bar_corner", "role": "queasy", "bars": 2}],
   "arrive": "bar_arrive",
   "exits": {"down": "bar_ref", "up": "bar_stair_top", "left": "bar_floor_door", "right": "bar_lounge_door"},
   "routes": {
    "up":    {"to": "bar_stair_top",   "via": ["bar_stair_foot"], "bars": 3, "hold_bars": 1},
    "left":  {"to": "bar_floor_door",  "via": ["bar_v_west"],     "bars": 2, "hold_bars": 1},
    "right": {"to": "bar_lounge_door", "via": ["bar_v_east"],     "bars": 2}},
   "glances": [{"by": -12, "bars": 2}], "strolls": [{"fwd": 0.8, "bars": 3}]}}}]}
```

## What the run does at the boundary

1. The route window commits as usual (`RunEngine` gives `route_commit` with `same_world: false`). The departing scene's
   `exits[dir]` doorway and the chosen guide's `committed` state are unchanged.
2. The walk out is one `player_move` to the threshold along the route's `via`. It uses the move's `bars` (clamped to
   2..4), shortened so that it ends by the boundary. Its `hold_bars` is kept only if there is time left before the
   boundary. A route with no move and no threshold has no walk. The pads keep playing during the walk.
   - A tap on a guide is the decision (ruling 39). It commits at the tap's own beat: the guide goes `committed`, the
     others `declined`, and `route_commit` fires. The walk starts there (`RunEngine.tap_commit`, then
     `RunJourney.commit_walk`). A tap at beat 50 has 14 beats, enough for a 2-bar leg and a 1-bar hold. A tap made
     before the window opens commits as the window opens. Later taps in the same window are ignored. The choice
     viewpoint's hold gives way to the walk (`StoryPlayer.end_window_holds`), and the rail takes no more steps. A held `pitch`
     eases back to level over the beat after the tap.
   - **The walk-out is at a walking pace (ruling 42).** From the tap the leg is measured from the rail's place (the choice
     viewpoint) through the move's `via` to its `to`: the sum of the straight segments (`RunRail.leg_length`). It takes
     `bars = ceil(length / 3 m/s / bar length)`, clamped to 2..8 (`RunRail.walk_off_bars`; at 174 bpm a bar is 1.379 s, so
     24 m is 6 bars, 5 m is 2, 40 m is 8 at 3.6 m/s). If the authored bars (clamped 2..4) already walk the leg at 3 m/s or
     less, nothing changes: the authored bars, the hold, the shortening against the boundary, the swap on the downbeat.
     Otherwise the leg keeps its paced bars and its `hold_bars` even past the boundary: the next phase starts on time and its
     music plays while the player still walks in the world being left. The world swap waits: the passage frame shuts over the
     2 beats before the hold ends, and the swap is on the next whole beat after walk and hold (the hold runs on to it, less than
     a beat more). The destination's arrival (the cut to `rail.arrive`, the walk home) is then exactly as on a boundary, timed
     from that swap (`RunJourney.cut_t` / `swap_t`, `RunPlay` shows the new stage then and offers none of its hotspots before).
     The swap is never later than beat 32 of the next phase (`RunJourney.CUT_LATEST_BEAT`): the arrival walk (at most 3 bars)
     is over before that scene's block-2 decision (beat 44.75), which walks it to its choice viewpoint for the next window
     (beat 49), so the walk-out never collides with the next window. A commit is always before the boundary, so 8 bars always
     fit by beat 32; only the hold is cut short for a tap after beat 60. Until the arrival is over the new scene's rail takes no
     step (its log says `arriving`), block 0's glance and stroll are left out, and so is a herald's look that would start before it.
     The run prints `RUN walk-off <node> <from> -> <to>: leg <m> m, <bars> bars (<m/s> m/s, at most 3.0), hold <bars> bars, the cut
     <beats> beats after the boundary | the cut on the boundary` and keeps the entry in `RunJourney.walk_offs`.
     A leg that would need more than 8 bars at 3 m/s (about 33 m at 174 bpm) is the scene's fault: shorten it or add a hold.
     `tools/story/check_rail_paths.gd` prints every walk-out's pace (`  WALKOFF <dir> <from> -> <to>: <m> m, <bars> bars at
     <bpm> bpm, <m/s> m/s`) and flags those (`  WARN walk-off ... needs <n> bars at 3.0 m/s, more than 8 ...`). Fixture:
     `tests/fixtures/walk_pace` (one hall map, legs of 24, 5, 40 and 7 m), tests in `tests/test_geography.gd`.
   - An untouched default walks from the lock at beat 61 (3 beats before the downbeat): `RunPlay._update_passage`
     calls `RunJourney.threshold_leave`. It is no walk-out from a tap: 3 beats, the swap on the downbeat, as before.
3. From beat 62 the passage frame shuts to the doorway. On the downbeat the stage swaps to the destination's map (or,
   after a walk-out that runs on past it, as its hold ends: above).
4. The destination's `rail.arrival` cuts to its `rail.arrive` and walks home. The frame opens again.

The stay (`down`, nothing chosen) keeps the scene: there is no walk and no frame. Returning to a world that was
already reached is fine. The save's `reached` list grows once per world.
