# Heralds at the quest entrances

Lead ruling 25 (6 November 2026, from the owner): every entrance to a quest from the main flow has a **herald**, a character from
that quest standing at the entrance and gesturing towards it. This page says who the heralds are, how to put one at an entrance,
and the rules they follow.

## The four heralds

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

**The mark.** Each herald also hangs its quest's sign over the entrance. It is about 0.42 m across and is lit by itself, swelling on every
beat. Dungeon: a violet arched door with a chevron pointing down. Gospel: a gold eight-pointed star. Squadron: green airman's wings.
Ember: an orange flame. The mark sits 1.05 m above the entrance's anchor, so it stays clear of the choice layer's lamp at 0.6 m.

## Putting a herald at an entrance: one call

In the world's hotspot table (`tools/run/hotspot_tables/<world>.py`), after the entrance has been added:

```python
from heralds import herald
herald("gospel", "warehouse.balcony.star", side="left")
```

- `quest`: `dungeon`, `gospel`, `squadron` or `ember`.
- `entrance`: the hotspot id, or the dict that `sc()` / `add()` returned.
- `side="left"` or `"right"`: which side of the entrance the herald stands on, as the player sees the entrance from the scene's
  standpoint (`place.waypoint`). The herald stands `gap` metres (1.25 by default) to that side and 0.35 m nearer the player.
- `at=(x, z)` instead of `side`: an exact ground point in metres, for a tight room (the booth uses this).
- `self_thing=True, toward=T("<thing>")`: the entrance is itself the quest's person, as the Floor wizard is. Its own map billboard then plays the
  gesture, pointing at `toward`. Only the wizard has billboard frames.

Then run `python tools/run/make_hotspots.py`. It writes a `herald` block into the entrance in `content/run/hotspots/<world>.json`,
and stops with an error when the placement breaks a rule below.

## The rules

- **Not a choice.** A herald is a field of its entrance hotspot, never a hotspot of its own. So it is never selectable (the
  view only hit-tests hotspots) and never counted towards the cap of choices (rulings 1 and 16). No audit counts it (`check_hotspots.py`,
  `choice_audit`, `coverage_audit`), and it never routes anywhere. `tests/test_heralds.gd` checks that each scene's choices on show,
  its staged options and its default are the same with and without the heralds.
- **Shown with its entrance.** A herald stands while its entrance is staged, meaning on offer in this visit. That runs from the scene's first beat,
  for as long as the entrance is available. So the herald of an entrance behind a flag (the star, the ember) appears when the entrance
  does. The self herald stops once another option has been taken.
- **Placement** (checked by `tools/run/heralds.py`):
  - inside a sector of the scene's map;
  - at least the entrance's touch radius plus 0.45 m from the entrance, so the body never covers the touch ring;
  - at least 0.75 m from every other hotspot anchor of the scene.
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
3. Look at it. Shoot the scene with `bash tools/story/shoot_heralds.sh` after adding a line to its list (entrance name, scene, flags, a close camera
   `x:z:yaw:pitch`). Check that the herald is in the picture when the entrance is, points at it, and is not hidden behind a person or a pad.
4. A new Dungeon entrance that is not the wizard himself (ruling 15) uses a standing herald: `herald("dungeon", "<id>", side=...)`. The wizard's frames
   are in the sheet like the others.
5. Do not edit the herald art for a new entrance. If a quest needs a different herald or gesture, change `tools/story/art/heralds.py` and rebuild with
   `python tools/story/build_heralds.py`, then import into Godot.

## Files

- `tools/story/art/heralds.py`, `tools/story/build_heralds.py`: the bake. Its outputs: `assets/story/heralds/heralds.png`, `heralds.json`, and `wizard_<n>[_l].png`.
- `src/story/story_heralds.gd`: the runtime (drawing, mirroring, light, the self herald).
- `src/run/hotspot_view.gd`: plays it from the choice layer. This is 9 added lines, and nothing else changed there.
- `tools/run/heralds.py`: the `herald()` call and its placement checks.
- `tests/test_heralds.gd`, `tools/story/shoot_heralds.sh`, and the shots in `docs/shots/art/heralds/`.
