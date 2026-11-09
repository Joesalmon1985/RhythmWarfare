# Bedroom art pipeline - how a room is made (and how to make the next one)

Room 01 ("Kit's bedsit", a young rave-music fan's first flat) is the quality benchmark. Everything in it is data + reusable props.

```
Blender script (Art/Source/blender/<family>.py)  ->  FBX (Assets/Bedsit/Art/Models/<family>/)
      -> Bedsit/Art/Build Props  ->  prefab per prop + shared PBR materials (Assets/Bedsit/Resources/Art/Props|Materials)
      -> room definition JSON (Assets/Bedsit/Resources/Rooms/<id>.json)  ->  RoomBuilder at run time
```

## 1. Props (Blender, original work)
* `Art/Source/blender/bsk.py` is the shared helper library; `BRIEF.md` is the modelling contract (units, origin = bottom centre, front = Blender -Y,
  materials are *role names*, UVs, bevels, budgets, verification).
* Families: `textiles.py`, `paper.py`, `kitchen.py`, `furniture.py`, `electronics.py`, `club.py` (+ `exterior.py` for the shop street).
  Run one with `"C:/Program Files/Blender Foundation/Blender 4.5/blender.exe" -b -P Art/Source/blender/<family>.py`.
  Each writes FBX to `Assets/Bedsit/Art/Models/<family>/`, a `manifest_<family>.json` (dimensions, tris, roles, placement notes) and preview PNGs.
* Blender front (-Y) arrives facing +Z in Unity, Blender +X arrives as Unity -X (handedness). A prop's back is -Z in Unity.

## 2. Import (Unity editor)
* Menu **Bedsit/Art/Build Props** (`Assets/Bedsit/Editor/ArtPipeline.cs`): fixed importer settings, maps every Blender material *role* to a shared material
  (`ArtPipeline.Rules`: texture, normal map, smoothness/metal, emission, two-sided cloth shader `Bedsit/Cloth` for thin goods), writes prefabs to
  `Resources/Art/Props/<name>.prefab`. After adding materials/props run it, then force a reimport of `Assets/Bedsit/Resources/Art` if the editor shows stale (pink) materials.
* **Bedsit/Art/Render Prop Sheets** renders contact sheets of the prefabs *as Unity shows them* to `Evidence/props/`.
* Textures: `Tools/art/stage_textures.py` copies the chosen CC0 Poly Haven sets into `Assets/Bedsit/Art/Textures`.

## 3. A room = one JSON (`RoomDef`, `Assets/Bedsit/Core/Room/RoomDef.cs`)
`shell` (wall/floor/ceiling materials, skirting), `openings` (door/windows per wall with the exterior `view` they show), `furniture`, `decor`,
`cleanables` (tidy tasks), `lights` (incl. pulsing venue lights), `exteriors` (street props), `ground`, `environment`, `hideLegacy` (old Sims 2 objects to hide),
`bedPillowEye`, `wakeYaw`, `standingPitch`. Placements are `{prop, pos, euler, scale, tag, parent}`; `parent` = tag of another placement (desk-top items follow the desk).
A cleanable = `{id, action, view, messy(+messyExtra), tidy(+tidyExtra) | target, radius, height, sound}`; actions: `make`, `fold`, `stack`, `slide`, `swap`, `coil`, `zip`, `bin`.
* Authoring helper: `python -I Tools/art/make_room01.py` regenerates `room01.json` (helpers to place things against walls; yaw facing the room: N 180, S 0, E 270, W 90).
* **Another room**: copy `make_room01.py` to `make_roomNN.py`, change size/openings/furniture/props/lights/cleanables (different bed type, desk-less layout, other country's
  exteriors...), write `roomNN.json`, run the game with `-room=roomNN` (or `BEDSIT_ROOM=roomNN`). New prop = a new Blender function + export + Build Props; no C# changes.
  New exterior view = new building props + `exteriors`/`ground`/venue-light entries.

## 4. Run-time pieces
`RoomBuilder` (shell, props, lights, exteriors), `Cleanable` (messy/tidy state + animations + highlight), `SfxSynth` (synth sounds), `RoomSave` (progress file; `-loadroom` restores it),
`ActOne` (uses the room's cleanables: tidy meter, compass pips, knock/visitor logic unchanged). `-legacyroom` restores the old Sims 2 furniture + procedural clutter.

## 5. QA
`Assets/Bedsit/Tests/PlayMode/BedsitPlayModeTests.cs` > `RoomTests` (props present, no pink/missing materials, camera headings + tasks visible per view, state transitions for every action type,
save/load). Screenshots: `Evidence/screenshots/overhaul_{messy,tidy}_{North,East,South,West}.png` (+ `overhaul_sheet_*.png`), captured by an editor script that snaps each view and
`SnapToTidy`s every task (they contain Sims 2 content in the mirror/windows, so they are git-ignored).
