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
  - `routes {up|left|right: move}`: each move is `{to, via?: [waypoints], bars, hold_bars?: >= 0, style?, role?}`. `bars` must be above 0; the walk clamps it to 2..4 bars, then to the time left before the boundary.
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
     viewpoint's hold gives way to the walk (`StoryPlayer.end_window_holds`), and the rail takes no more steps.
   - An untouched default walks from the lock at beat 61 (3 beats before the downbeat): `RunPlay._update_passage`
     calls `RunJourney.threshold_leave`.
3. From beat 62 the passage frame shuts to the doorway. On the downbeat the stage swaps to the destination's map.
4. The destination's `rail.arrival` cuts to its `rail.arrive` and walks home. The frame opens again.

The stay (`down`, nothing chosen) keeps the scene: there is no walk and no frame. Returning to a world that was
already reached is fine. The save's `reached` list grows once per world.
