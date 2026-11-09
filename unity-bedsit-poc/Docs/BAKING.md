# Baked content: how the 3D Sims 2 room and characters get onto a phone

Decision (owner, 9 Nov): **no sprites.** Characters stay real 3D skinned models; the game rules stay as simple as they are
(three actions, four views, one door). The only obstacle to a phone was that the content was read from a desktop Sims 2
install at run time. The fix is a one-off, local conversion.

## What the baker does (`Bedsit/Bake/Bake live content to local assets (Play mode)`)
Run with the game playing from the live Sims 2 install (Editor, `config.json` present). It writes ordinary Unity assets to
`Assets/LocalBaked/` (**git-ignored**: they are derived from EA assets):

| Thing | Becomes |
|---|---|
| each of the 4 Sims | prefab `Resources/Baked/Actor_<id>.prefab`: plain `SkinnedMeshRenderer`s + the original skeleton (138 bones); no OpenTS2, no Animation Rigging, no IK |
| original animations (idle, wave, clap, cheer, greet, surprise) | `Clips/*.anim`: legacy clips **sampled frame by frame (30 fps) from the original Sims 2 animations** while OpenTS2 plays them, so IK is already resolved into plain bone rotations (+ root/pelvis position) |
| the room, furniture, garden | one prefab `Resources/Baked/World.prefab` (120 meshes, 79 materials; the door keeps its original `o-door-open-CW_anim` clip, 1.05 s) |
| textures (64) | PNG + importer settings: DXT on Windows, **ASTC 6x6 at <= 512 px on Android** |

At run time `BedsitContent` picks the source: baked when `Assets/LocalBaked` exists and no `config.json` is found (always on a phone),
otherwise live. `BEDSIT_CONTENT=live|baked` overrides. The gameplay code is identical for both.

## Results
* 37 / 37 Play Mode tests pass: 23 against live content, 14 repeating the first-person/interaction tests with baked content forced,
  including the pixel tests (player body visible only in the mirror; NPC in every non-mirror view).
* Windows exe (116 MB) built from baked content and run **without any Sims 2 install or `config.json`**: full evidence flow, no errors.
* Android APK (35.9 MB, arm64-v8a, minSdk 25) built with the same content. **Not run on a phone** (no device attached).

## Re-baking / changing the cast
Edit the Sim ids in `BedsitGame` (premade Pleasantview Sims, `N001_User000NN`), play in the Editor, run the menu item. Baked actors only
contain the bones/clips baked from the player's Sim (all adult Sims share one skeleton); child/elder Sims would need their own bake.

## Limits (be aware)
* Face blend shapes are not animated in baked clips (the live path does not animate them either: the rig lacks those channels).
* Baked animations are fixed-rate samples (30 fps); the live path is the exact original keyframes.
* Baked output is an EA-derived asset: do not publish it; the repository ignores it.
