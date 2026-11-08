# Weather: rain in the 2.5D world (hook H10, package A9)

For the environment agents authoring the rain scenes (Booth, Dock, Balcony, the Lounge's street). The paintings (`art/reference/doom_worlds/Rainy*.png`, `Rain-Slick Rooftop Crossroads-3.png`) are the bar (ruling 36); the rain is in the one 3D world (ruling 38), not a canvas overlay.

## Data

On the map (`content/story/maps/<map>.json`):

```json
"weather": {"rain": 0.8, "wind": 10, "drips": [{"at": [4.15, -1.2], "h": 3.2}]}
```

| Key | Meaning | Checked |
|---|---|---|
| `rain` | 0..1: the share of the streaks drawn (`StoryWeather.RAIN_MAX` = 420 at 1). 0 draws no streaks and no drips. | 0..1, a number |
| `wind` | degrees of slant from vertical; positive leans the falling rain toward +x (a world direction, so the slant turns with the camera). | -60..60, a number |
| `drips` | eaves: each `{at: [x, z], h}` drops water from `h` metres above its sector's floor to the floor, `DRIPS_PER` (2) drops on their own song-time periods. | `at` in a sector, `0 < h <= 30` |

Unknown keys are errors. The map has no weather without the key (`StoryMap.weather` is `{}`).

On a sector:

| Key | Meaning |
|---|---|
| `"rain": true` | rain falls inside although the sector has a ceiling (an open yard drawn with a roof texture) |
| `"rain": false` | an open sector kept dry |
| absent | open (rain falls) when its ceiling is the sky: `ceil_tex` `"sky"` or a painted sky tile named `*_sky` (the Dock's `dk_ceil_sky`) |
| `"wet": 0..1` | the floor's gloss. Absent: the map's `rain` on a sector where rain falls, 0 elsewhere. A dry map may author `wet` (a spill): it gets the gloss and no rain. |

Queries: `StoryMap.rain_open(sid)`, `wet_of(sid)`, `has_weather()`, `StoryMap.sky_ceiling(sector)`.

The Dock (`doom_dock.json`) needs only `"weather": {...}`: its four `dk_ceil_sky` sectors are open, the two truss-roofed ones dry. Its eaves are the canopy edge (x 4, sector 1_0 against 0_0) and the blue door's lintel (x -4, 5_0 against 2_0); the shot sheet uses drips there (`tools/engine/shoot_weather_node.gd`, `DRIPS`).

## What is drawn

`StoryStage` builds a `StoryWeather` (`src/story/world/story_weather.gd`) as a child of the `StoryWorld`, beside the light show, only when `map.has_weather()`. A map without weather gets no node and no extra work: Night One's low-res frame is byte-identical to one captured before this code existed (`tests/test_weather.gd`, baseline `tests/fixtures/weather/night_one_frame.png`).

- **Rain**: one `MultiMeshInstance3D` of thin quads, all motion in its vertex shader. Each streak has a fixed world anchor (a hash of its index, the same PCG hash on the CPU in `streak_pos`). The shader wraps the anchors into a 13 x 7.5 x 13 m box centred 5.5 m ahead of the eye and 2 m below it to 5.5 m above, so the streaks stay put in the world while the camera moves and the ones that leave the box reappear on its far side. They fall at 9 m/s on song time, slanted by `wind`, 0.55 m long, widened with distance to stay at least one low-res pixel, faded in over 0.7 to 1.6 m (none smear across the lens) and out from 10 to 15 m.
- **Lighting**: a light map over the ground plane (0.5 m a texel, at most 192 a side) holds the lamps' light at eye height (the map's `light` things with the falloff the world is baked with; cones ignored; the hue kept, so a streak by a sodium lamp is orange and one in the moon's light is blue) and, in alpha, whether rain falls there. The shader reads it per vertex: a streak takes the colour of the practicals around it (a faint cool base plus the lamps' colour), times the camera sector's song-time light (it breathes with the room). A streak over a roofed sector is collapsed to nothing (no area, no fill). Additive blend, unshaded, no fog (it fades by distance instead).
- **Drips**: a second MultiMesh with the same shader in drip mode: short drops falling from each eave with gravity on song time.
- **Wet floor gloss**: one MultiMesh of floor quads, at most 24. For each map light within 22 m, the point where a mirror floor would show the lamp (between the eye and the lamp's foot: `eye + (foot - eye) x E / (E + H)`, E the eye's height over the lamp's floor, H the lamp's) is found; if that point's sector is wet and in sight, a soft band broken into ripple rows lies on the floor there, stretched toward the eye, in the lamp's colour x strength x `wet` x 0.42, with a song-time shimmer. **What it is not**: it is not a reflection. Nothing of the walls, the sprites or the people is mirrored; a lamp behind a wall can still put a band on a floor in sight; the floor is not darkened or re-coloured. It is the highlight band under the practicals that the paintings show, placed where a mirror would put it.

## Clock, pause, view

Everything is a function of song time and the camera: `StoryStage._update_world` calls `weather.update(t, lowres.camera, sector light, visible sectors)`; the node has no `_process`. A paused song holds every streak, drop and shimmer still; a restart replays the same rain. The rain is drawn inside the stage's low-res `SubViewport` (it pixelates with the world, under the crowd overlay and the hotspots), so it never reaches the pads, the note lane or the HUD; the stage clips its picture to its own rect.

Reduced effects keeps half the streaks (`REDUCED_SHARE`). `RW_STORY_HIDE=weather` hides the node (profiling).

## Cost

Measured with `tools/engine/shoot_weather.gd` on the Dock at the default 360 lines (a 640 x 231 low-res picture in a 1280 x 720 window, the 460 px stage strip), the dev PC:

| Rain | Streaks | Low-res draw calls | Primitives | weather.update CPU |
|---|---|---|---|---|
| 0 | 0 | 61 | 2470 | 3 us (nothing wet: returns at once) |
| 0.5 | 210 | 64 | 2936 | 8 to 14 us |
| 1 | 420 | 64 | 3356 | 8 us |

So: +3 draw calls (rain, drips, gloss), +2 triangles a streak, drop or band, one light-map fetch per vertex, additive fill of thin streaks over a 640 x 231 picture. The gloss bands are re-placed only when the eye moves (16 sector lookups at the Dock), otherwise only their colours change. Building the light map is a one-off when the stage is built (a rasterise per sector; the Dock: 47 x 40 texels).

Not measured: GPU time on a phone. The dev PC's low-res viewport GPU time (`viewport_get_measured_render_time_gpu`, 30 frames) moved between 0.34 and 0.72 ms from run to run with no rain-dependent trend, so it does not separate the rain's cost from noise; a desktop GPU says nothing about a mid phone's fill rate. Headless runs (the tests) have no renderer and measure nothing on the GPU. The < 1 ms budget is argued from the counts above (one 840-triangle instanced draw of thin additive quads, two tiny ones), not shown on a device.

## Files

- `src/story/world/story_map.gd`: `weather`, `_build_weather`, sector `rain` / `wet`, `rain_open`, `wet_of`, `has_weather`, `sky_ceiling`.
- `src/story/world/story_weather.gd`: the node, its shader and the CPU mirror of the streak maths.
- `src/story/story_stage.gd`: `weather` built in `attach_world`, updated in `_update_world`.
- `tests/test_weather.gd`; `tests/fixtures/weather_frame.gd`, `weather_baseline.gd` (re-run the baseline only when the world's look changes on purpose).
- `tools/engine/shoot_weather.gd` (+ `_node.gd`): the sheet. Needs the Dock's map and its art: `RW_WEATHER_MAP=<doom_dock.json>`, and `assets/story/doom_dock/` imported in the checkout.
