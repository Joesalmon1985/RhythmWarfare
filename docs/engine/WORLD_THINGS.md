# World-staged activities: what an activity declares (contract 10, ruling 38)

For the activity agents (cloakroom, bar, bass knob, the card table's conversion). The stage draws everything; an activity only says what is there and what happens.

## The port

`setup(ctx)` receives `ctx["world"]`: a `WorldThings` (`src/contracts/world_things.gd`). In a run it is a `RunWorldPort` that also carries out every call; in a pure test keep your own `WorldThings.new()` and read its logs. Methods:

| Call | What the room does |
|---|---|
| `set_things(arr)` | replaces your dynamic things (or implement `things() -> Array`: the host reads it every frame while you are seated, and pushes `[]` when you end) |
| `people(id, state, t0, dur)` | the crowd actor `id` plays `state` from song time `t0` for `dur` s (0: until the next call) |
| `feedback(thing, kind, t)` | a tick, cross or glow mark at that thing's screen point |
| `piece_on(piece, t)`, `piece_off(piece, t)`, `piece_pulse(piece, t, bars)` | a map piece of the scene switched (a shelf glass lit) |

`make_view()` may return null, and should: there is no canvas view any more.

## Things

`{id, sprite, at: [x, z], sector, size: [w_m, h_m], frame, y?, anchor?, grid?}`

- `sprite`: a sheet `assets/story/<map art>/sprites/<sprite>.png` (or a `res://` path). Rows are states, columns frames. An unimported PNG loads too.
- `frame`: an int (row-major cell index) or `[row, col]`.
- Grid: give `grid: [cols, rows]`, or a sidecar `<sprite>.json` `{"grid": [cols, rows]}`. Without either the grid is inferred from the thing's `size` aspect (fewer rows on a tie), which is ambiguous for sheets whose rows and columns have the same cell aspect: say the grid.
- `size` is metres; the cell is stretched to it. `y` is metres above the sector floor: the bottom edge, or the centre with `anchor: "center"`.
- `at` and `frame` may change every frame; derive them from song time.
- Drawn in the crowd's overlay inside the low-res viewport, sorted with the people by distance, culled when the sector is out of sight, lit by the sector's song-time light and the lamps around it, fogged with depth. Draw no light, shadow or outline into the sheet for the room's sake; the stage lights it.
- `StoryWorld.thing_screen_point(id)` / `thing_screen_rect(id)` (low-res px) and `StoryStage.thing_screen_point` / `thing_screen_rect` (stage px) give where it is, for a dynamic thing, a map thing or a piece; use the stage rect for a `world_regions` tap target.

## People

States: `waiting`, `happy`, `impatient`, `frown`, `beckon`, `raise_glass` and the crowd's `idle`, `look`, `cheer`, `clap`, `hands_up`. A sheet without the row falls back to a named candidate (`StoryCrowd.ACTIVITY_STATES`, `CROWD_FALLBACKS`); today's Warehouse sheets lack most of them (waiting shows idle, raise_glass shows cheer). Ids: your scene's actors (`customer_0..7`, `attendant`, `bartender`, `dj`); an id the room does not cast is a warning and nothing else. Never draw a person.

## Feedback

`tick` pops and fades over one beat, `cross` shakes and fades over one beat, `glow` swells and fades over one and a half. Pixel marks, no text, in the low-res viewport at the thing's screen point. Besides the controls this is the only canvas drawing you may rely on.

## Controls

`controls()` returns 2 or 4 `{id, label: "", ...}` with one of: `draw: Callable(canvas_item, rect)` (or `(canvas_item, rect, alpha)`), `icon: "res://...png"`, `pictogram` or `shape` (+ `color: "#rrggbb"`) from `ControlPictograms.SHAPES` (same, different, circle, square, diamond, triangle, star, drop, bottle, leaf, bolt and the bar's shapes), optional `lit: false`. The pads draw them in their own slots and frames: over the beat before your seat boundary the pad glyphs cross-fade into your pictograms with a short pulse (2 controls: each pair of pads widens into one slot), and back over the beat after the strip is handed back. A label is drawn only when nothing else is given; give a pictogram.

## What not to draw

No canvas panel, card, close-up, ring, arrow, word or number over the room; no person; no light or fade of the room. State shows in your things' frames and motion, your people's states and the feedback marks.
