# Recommendations: bringing this architecture into RhythmWarfare and DuelMasterBattle

Context (from `SURVEY_RW_DMB.md`): both games are **Godot** projects. RhythmWarfare already has a data-driven first-person bedsit
(4 yaws from one point, region input, hotspots, Doom-style sector maps, 2D sprite characters); DuelMasterBattle is a portrait wizard sim with
a character animation state machine and dialogue bus but no first-person content. So "reuse" means one of two things, and you should
decide which before investing more:

## Option A (recommended): Unity as a presentation/prototyping front end, designs carried across
Reuse the **architecture and data**, not the C#.
1. **Keep RW's contracts as the source of truth** (fixed N/E/S/W mapping, region fractions, `threshold_<facing>` naming, "state shown by the
   art, not rings", one tap owner). This POC already follows the region fractions (left 0-22%, right 78-100%, top-centre) and the
   "turn ends in a hard hold" rule. The Unity `InputRegions` class is a direct port of RW's `themes.json` regions and has the same tests.
2. **Port the Core assembly's seams, not the engine**: `InteractionTarget` (+ the RW hotspot JSON fields `id/anchor/kind/available/on_success`),
   `InteractionController` ("current target = f(zone, facing)"), `WorldSceneController` (zones = RW maps with fixed standpoints),
   `PlayerTransitionController` (RW's walk-to-threshold, swap, arrival pose). They are ~400 lines of engine-light logic; in Godot they become
   autoloads/nodes with the same names and events.
3. **`ICharacterActor` / `SimAnimationLibrary` pattern**: gameplay asks for logical keys (`idle`, `wave`, `clap`), a library resolves
   them with fallback candidates. This is RW's `CROWD_FALLBACKS` and DMB's priority state machine; both can sit behind the same interface, and a
   Sims-2-skeleton, sprite-sheet or Godot `AnimationPlayer` implementation is then interchangeable.
4. **Mirror**: RW has none. If wanted, in Godot use a `SubViewport` + second `Camera3D` with the same off-axis maths as
   `MirrorReflectionController` (mirror the eye through the plane, near plane = glass plane, frustum through the glass rectangle, render the
   player on a layer only the mirror camera sees). The "player is never seen" rule (RW D7) then holds everywhere except the mirror.
5. **Tests to copy** (they are the real asset): four turns = identity; turn never moves the camera; the player layer is invisible to the eye
   camera (pixel test with a marker colour); every non-mirror view has an NPC; interaction moves the rig at constant eye height; turn takes
   0.2-0.45 s. RW's headless runner and screenshot contact sheets map 1:1 onto Play Mode tests + `EvidenceRunner`.

## Option B: move RW's bedsit to Unity
Reasonable only if the Sims 2 look is the goal. Cost drivers, in order: (1) **desktop-only content** (below); (2) rewriting the content
pipeline (RW's JSON maps/hotspots would need Unity importers); (3) losing RW's 82k-check headless suite and Android flow.
The baked-content route (below) now makes it technically possible.

## Making the Sims 2 look available on a phone (decided: keep it 3D)
The owner chose to keep the characters and room as real 3D objects, not sprites. Reading a Sims 2 install at run time is impossible on a phone,
so the Unity project **bakes** the room and the Sims locally into ordinary Unity assets (meshes, ASTC textures, pre-sampled animation clips;
see `BAKING.md`). That is done and works on Windows (verified) and builds for Android (not yet run on a device).
Keep the baked output private: it derives from EA assets. For the Godot games the same baked meshes/clips could be exported (glTF) if a
3D Sims look is wanted there, but that is a separate piece of work.

## Concrete next steps (in order)
1. Decide Option A vs B with the owner (this is the one real fork).
2. Run the APK on a real phone; measure fps, memory and shader cost; if needed swap baked materials to a cheap mobile shader and lower the mirror cost.
3. (Optional) export baked meshes/clips for Godot if the 3D Sims look is wanted there.
4. Add an `InteractionTarget` state machine (idle/available/selected/committed) and art-bounds touch rects (>= 88 px at 1280x720) to match RW.
5. Add the data layer: one JSON per room (zones, standpoints, targets, NPC cast ids) with a pure validator and tests, mirroring RW's `contract_shapes`.
6. Phone pass: Android build with baked content, touch regions, 20:9 aspect, thermal/perf, and an honest "verified on device" table.

## What I would not carry over
* Unity-side dialogue menus (the brief forbids them; RW's silent acting/`cast` contract is the better model).
* OpenTS2's SimAntics/lot/UI stacks (vendored but unused).
* The procedural green cue diamond as final art: RW's rule (state shown by the art itself) suggests a lit door, a beckoning NPC, etc.
