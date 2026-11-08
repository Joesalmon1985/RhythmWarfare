# Heralds at the quest entrances

Lead ruling 25 (6 November 2026, from the owner): every entrance to a quest from the main flow has a **herald**, a character from
that quest standing at the entrance and gesturing towards it. This page says who the heralds are, how to put one at an entrance,
and the rules they follow.

## The heralds

| Quest | Herald | From | Their touch of the quest |
| --- | --- | --- | --- |
| Dungeon (the Bassment) | the wizard of the Warehouse | `assets/story/night_one/textures/thing_wizard.png` | holds his staff, sweeps his free arm out to point, and his orb flares on the beat |
| gospel | `sh1`, the shepherd of the first night | `galilee_shore` (J00 Bethlehem, the first scene of the path) | a shepherd's crook held upright in the left hand |
| squadron | `gun`, the young Gunner | `airfield` (the Flight Line, the bomber, his last flight) | an airman's big wave over his head on beat 1, then the point on beat 2 |
| ember | `bram_o`, Bram the gardener | `orchard` (E00, the companion of the whole road) | the Ember in a small glass jar held up in his left hand, glowing |

Each person is drawn by the same renderer as the crowd (`tools/story/art/people.py`), with their own wardrobe and face from their
own chapter, so the player meets the same person again inside the quest. The owner may swap any of them by changing one line of
`HERALDS` in `tools/story/art/heralds.py`.

**The gesture** is 8 frames over 2 beats, locked to the song. On beat 1 the arm sweeps out from the chest (the Gunner waves above his head
instead). On beat 2 the point is pushed home, with the body leaning into it. The feet stay planted and there is no bounce, so it does
not read as dancing. The frames point to screen right; at run time the herald is mirrored whenever the entrance is on its left on screen.
In reduced motion the point is held still. You can see the frames in `docs/shots/art/heralds/strip_<quest>.png`: the 8 frames, the beats
marked underneath, then the mirrored point.

**The mark.** Each herald also hangs its quest's sign over the entrance. It is about 0.52 m across (about 40 px tall at 6 m in a 720 px window) and is lit by
itself, swelling on every beat. Dungeon: a violet arched door with a chevron pointing down. Gospel: a gold eight-pointed star. Squadron: green airman's wings.
Ember: an orange flame. The mark sits 1.05 m above the entrance's anchor, so it stays clear of the choice layer's lamp at 0.6 m.

**The light of the entrance.** Under the mark a pool of the quest's colour lies on the floor (1.1 m radius, flattened as the floor is seen from the eye),
brightening on the beat. An entrance with no thing of its own (a `pos` anchor, like the balcony star) gets a **gate**: a plain arched doorway in a dark stone
frame with the quest's light inside it, dithered like the rooms' own light, the mark in its crown. The frame takes the room's light; the light in it is its own.

**Depth fog.** The herald, the gate's frame, the mark and the pool fade into the room's depth fog as the people do (StoryCrowd.fog_m; lights a little less).

## Putting a herald at an entrance: one call

In the world's hotspot table (`tools/run/hotspot_tables/<world>.py`), after the entrance has been added:

```python
from heralds import herald
herald("gospel", "warehouse.balcony.star", at=(-10.05, -0.55), gate=True)
```

- `quest`: `dungeon`, `gospel`, `squadron` or `ember`.
- `entrance`: the hotspot id, or the dict that `sc()` / `add()` returned.
- `side="left"` or `"right"`: which side of the entrance the herald stands on, as the player sees the entrance from the scene's
  standpoint (`place.waypoint`). The herald stands `gap` metres (1.25 by default) to that side and 0.35 m nearer the player.
- `at=(x, z)` instead of `side`: an exact ground point in metres, for a tight room (the booth uses this).
- `self_thing=True, toward=T("<thing>")`: the entrance is itself the quest's person, as the Floor wizard is. Its own map billboard then plays the
  gesture, pointing at `toward`, and the mark hangs over `toward`. Only the wizard has billboard frames. Add `mark_over_self=True` to hang the mark over
  his hat instead (the chill-out wizard: he points to the way out, the Dungeon's sign is over him).
- `gate=True`: the entrance has no thing of its own (a `pos` anchor): a lit doorway in the quest's colour stands at it, its mark in the doorway's crown.

Then run `python tools/run/make_hotspots.py`. It writes a `herald` block into the entrance in `content/run/hotspots/<world>.json`,
and stops with an error when the placement breaks a rule below.

## The visibility rule: the camera brings every entrance into the picture

Nobody has to aim a camera at an entrance. Two things in `src/run/run_journey.gd` do it from the herald block alone:

1. **The heralds' look, in the opening.** At the start of every scene, for each entrance on offer from its first beat (`RunHotspots.staged`, so an entrance
   behind a flag only when the flag is set) that has a herald, the journey adds one `face` look (`RunJourney.herald_looks`): the first entrance in block 0, the
   next in block 1, the third in block 2. Each look runs from beat 0.5 to beat 15 of its block, turning in over one bar and handing back over one bar, so the
   entrance, its mark and its herald are held in the picture from about beat 4.5 to beat 11 whatever the rail does underneath (the door walk in, a stroll, the
   move at the block's decision). The points it holds are `StoryHeralds.look_points`: the entrance from 1.3 m under its mark up to the mark's top, the herald from
   the knees to the head. The block's own glance is left out so it cannot swing the entrance away. It is a look, never a move: the rail, the route and the song
   are untouched, and it is a pure function of song time like every other look.
   In a scene with more staged entrances than three looks and the window can show (five: the Floor's four gates and its wizard) each look also carries the other
   entrances' points, not kept (shared wiring step, 7 November 2026), so the group framed holds its own entrance and as many of the others as fit. The turn stops short of a wall nearer than 2.6 m in the middle of the picture
   (`StoryPlayer.herald_cap`; docs/art/CAMERA_CLEARANCE.md "The herald look") and never starts in the last beat of a door walk.
2. **The window.** From the block-2 decision the window's face look (the turn to the window's hotspots: the default exit still decides the group) frames the group
   of choices holding the most weight (`RunJourney.window_points`, the one list the run scene and the tests build): a quest entrance and its herald's spot weigh
   2 (`WINDOW_ENTRANCE_W`), a way back (a path's `<quest>.return`, a scene's `<scene>.to_hub`) 0.5 (`WINDOW_RETURN_W`), every other choice 1. So a way back never
   pulls the picture off the quest entrances, and it is framed beside them when it fits; its placement must keep it in the picture at the window (the test pins it).

An early-window entrance (the wizard: blocks 0 and 1 only) is on offer only in the opening, so its window is the opening look. Reduced motion changes nothing
in the look (it has no bob or sway; the turn is a smooth one-bar turn like the window's).

`tests/test_heralds_view.gd` checks it the way a player sees it: it plays the scripted run from the Warehouse's first beat to each herald's scene (perfect play,
the flags that put every entrance on offer), replays the journey on the real rail camera, projects the entrance and the herald into the stage strip of a
1280 x 720 window (the narrowest picture we ship; the HUD's corners left out) and wants each at least 75 % inside the picture in at least 80 % of the samples of
beats 4 to 12 and of beats 49 to 60. Today all five are at 100 %. With the look turned off (`RunJourney.look_heralds = false`) the openings fall to 0 %.
`RW_HERALD_VIEW_DEBUG=1` prints the camera and the rectangles every bar, for whoever places a new one.

**Occlusion (the wall test, shared wiring step).** A sample counts only when a ray from the eye to the entrance (its mark's top, else its middle) and one to the
herald (its head, else its chest) reach them past the map's walls, steps, lintels, floors and ceilings (the rays of `tools/art/camera_clearance_check.gd`) and the
lower half of the map's occluders (the card table and the people at it). The dancers are not seen (they move). An entrance hidden for more than a fifth of its samples
is listed in the test's `KNOWN_HIDDEN` (the findings of 7 November 2026, placement work for the location packages); a new one fails the test. A scene's way back to its
hub must be in the picture, unoccluded, for half the route window (`KNOWN_BACK_UNSEEN` lists those that are not yet).

**What it cannot guarantee.** That no dancer stands between the camera and the herald (look at the shots); that a fourth entrance in one scene is looked at (three looks a scene); that the entrance fits beside the default exit in the window (when it cannot,
the default wins and the entrance is only seen in the opening); that the mark stays clear of the HUD's corner (the bar's ember sits by it in the window); and
the camera of a run that wanders off the scripted rail (a sloppy run stands elsewhere: the look still turns to the entrance, but from further away or nearer).

## The rules

- **Not a choice.** A herald is a field of its entrance hotspot, never a hotspot of its own. So it is never selectable (the
  view only hit-tests hotspots) and never counted towards the cap of choices (rulings 1 and 16). No audit counts it (`check_hotspots.py`,
  `choice_audit`, `coverage_audit`), and it never routes anywhere. `tests/test_heralds.gd` checks that each scene's choices on show,
  its staged options and its default are the same with and without the heralds.
- **Shown with its entrance.** A herald stands while its entrance is staged, meaning on offer in this visit. That runs from the scene's first beat,
  for as long as the entrance is available. So the herald of an entrance behind a flag (the star, the ember) appears when the entrance
  does. The self herald (the Floor wizard) points the way while he is not the current choice, and beckons as before once touched.
- **Placement** (checked by `tools/run/heralds.py`):
  - inside a sector of the scene's map;
  - at least the entrance's touch radius plus 0.45 m from the entrance, so the body never covers the touch ring;
  - at least 0.75 m from every other hotspot anchor of the scene;
  - at least 1.6 m from every place the camera stands in the scene (home, the arrival, every place of the good and bad rails): nearer, head and feet do not
    both fit in the picture. (This is why the balcony's shepherd moved: he stood 1 m from the far end of the balcony.)
- **In the world like a person.** The herald is a `StoryCrowdProp` of the crowd of its room, the same mechanism as the day room's card table.
  It is projected, culled by sector and sorted by distance with the dancers, so people in front of it hide it. It is lit by the light a person standing
  there gets: the room's song-time light times the lamps around it, with the people's gain and clamps. Glowing things (the Ember, the mark) are drawn
  unlit.
- **Mirroring** is decided each frame from the camera: the gesture always points from the herald towards its entrance on screen. It
  keeps its last facing while the entrance is almost straight ahead, so it never flickers.

## What the 20 new entrances (N2.4) need from whoever places them

1. One `herald(...)` call per entrance, in the same table, after the entrance. Use the quest the entrance leads to.
2. Pick the side from the player's view of the entrance. Choose the side with open floor, away from the room's own people and other
   hotspots. If the room is tight, give `at=(x, z)`. The call refuses a herald standing inside a wall, on the entrance's ring, or on another object.
3. Add the scene to `ROUTES` in `tests/test_heralds_view.gd` (the scenes the run passes through from the Warehouse's first scene) and run it with
   `--filter heralds_view`. It must pass; if it does not, `RW_HERALD_VIEW_DEBUG=1` shows where the camera looks. Move the herald (or the entrance's object),
   not the camera.
4. Look at it. Shoot the scene with `bash tools/story/shoot_heralds.sh` after adding a line to its list (entrance name, scene, flags, a close camera
   `x:z:yaw:pitch`, the routes from the Warehouse; `RW_WINDOW=1600x720` for a 20:9 phone). Check that the herald is in the picture when the entrance is, points
   at it, and is not hidden behind a person, a pad or the HUD.
5. A new Dungeon entrance that is not the wizard himself (ruling 15) uses a standing herald: `herald("dungeon", "<id>", side=...)`. The wizard's frames
   are in the sheet like the others.
6. Do not edit the herald art for a new entrance. If a quest needs a different herald or gesture, change `tools/story/art/heralds.py` and rebuild with
   `python tools/story/build_heralds.py`, then import into Godot.

## Files

- `tools/story/art/heralds.py`, `tools/story/build_heralds.py`: the bake. Its outputs: `assets/story/heralds/heralds.png`, `heralds.json`, and `wizard_<n>[_l].png`.
- `src/story/story_heralds.gd`: the runtime (drawing, mirroring, light, the self herald).
- `src/run/hotspot_view.gd`: plays it from the choice layer. This is 9 added lines, and nothing else changed there.
- `src/run/run_journey.gd`: the heralds' look and the window's herald point (the visibility rule).
- `tools/run/heralds.py`: the `herald()` call and its placement checks.
- `tests/test_heralds.gd`, `tests/test_heralds_view.gd`, `tools/story/shoot_heralds.sh`, and the shots in `docs/shots/art/heralds/` (the close shots) and
  `docs/shots/art/entrances/` (the real camera: `before_after_play.jpg`, `phone_20x9_play.jpg`, `entrances_play.jpg`).
