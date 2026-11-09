# Authentic Sims 2 animation: provenance and compatibility findings

## What is used

Every animation is a Maxis `ANIM` resource (type `0xFB00791E`, group `0x1C0532FA`) from the installed game, decoded by
OpenTS2 (`AnimResourceConstBlock`, `ScenegraphAnimationAsset.CreateClipFromResource`) and applied to the Sim's ORIGINAL
skeleton (`auskel`, with its IK chains) or to an original object's own bones (door). No generic Unity animation, no procedural sway.

| Logical key | Resource name | Package (game/Base/TSData/Res/Sims3D unless noted) | Channels | Length | Used for |
|---|---|---|---|---|---|
| `pose` | `a-pose-neutral-stand_anim` | `Sims00.package` | 51 (181 curves) | 1 frame | base layer under everything |
| `idle` | `a-idle-neutral-armsSide-wtC-breatheLoop_anim` | `Sims00.package` | 51 | 3.96 s | breathing idle overlay |
| `wave` | `a-react-wave-fullBody_anim` | `Sims00.package` | 61 | 2.60 s | **east NPC, mirror reflection, corridor NPC** |
| `clap` | `a-clapSmall-loop-standing_anim` | `Sims00.package` | 51 | 1.88 s | west NPC |
| `cheer`, `greet`, `surprise`, `stretch` | `a-clapBig-loop-standing_anim`, `a-soc-greet-nod_anim`, `a-hairChange-head-surprise_anim`, `a-idle-neutral-armsSide-wtC-stretchShoulders_anim` | `Sims00.package` | 51 / 3 / 37 / 51 | 0.5-4 s | available in the library |
| door | `o-door-open-CW_anim` | `Objects00.package` (Base/TSData/Res/Objects) | 14 (hinge `r_door_rot`) | 1.05 s | north door |

Run-time provenance is also printed by `SimAnimationLibrary.DescribeAll()` and recorded in
`Evidence/animation_proof.txt` and `Evidence/evidence_log_windows_exe.txt`.

## Loading code path

`Sims2Runtime.Initialise()` -> OpenTS2 `Core.InitializeCore()` + `ContentManager.AddPackages` (Base `Sims3D`, `Catalog/Skins`,
`Materials`, `Catalog/Patterns`) -> `SimAnimationLibrary.Resolve(key)` -> `ContentManager.GetAsset<ScenegraphAnimationAsset>(ResourceKey(name,
GroupIDs.Scenegraph, TypeIDs.SCENEGRAPH_ANIM))` -> `CreateClipFromResource(Scenegraph.BoneNamesToRelativePaths, BlendNamesToRelativePaths)`
-> legacy `Animation` component on the skeleton root, plus the Animation-Rigging IK graph built by `SimCharacterComponent`.
Reference: OpenTS2 `SimAnimationTest`, `SimCharacterComponent`, `ScenegraphAnimationAsset`, `ScenegraphGMDCTest` (studied; our `AnimationProofRunner` reproduces the SimAnimationTest flow, then extends it to dressed Sims).

## Proof that the original animation changes the pose

* `Evidence/animation_proof.txt`: wave on the base Sim and a dressed Sim: maximum bone rotation change **178.6 degrees**.
* Play Mode test `OriginalSims2AnimationVisiblyChangesACharactersPose`: asserts the resource targets `auskel`, has > 20 channels and
  moves at least one bone > 30 degrees. `MirrorInteractionPlaysAnAuthenticAnimation...` does the same for the reflected player.
* Screenshots (local): `Evidence/screenshots/proof_02_wave_a.png`, `31_mirror_wave_*.png`, `51_corridor_*`.

## Compatibility findings (what had to change for OpenTS2 on Unity 6 and for dressed Sims)

1. **Dressed premade Sims were static.** Stock OpenTS2 renders a CAS outfit's clothing/hair as rigid, bone-tagged geometry and only
   the face is skinned, so animations moved the face and nothing else. Added `ScenegraphComponent.AddSkinnedShape` and a
   `skinnedParts` mode in `CreatePersonOutfit` that binds the outfit SHPEs to the skeleton as `SkinnedMeshRenderer`s. The rig can live
   in the Face or Body resource, so shapes are deferred until it is found.
2. **Rigging factory:** `SimCharacterComponent.CreateAnimatedFromOutfit` wraps an outfit and builds the IK rig on its skeleton.
3. **Euler channels with different key counts were dropped.** OpenTS2 built quaternion keys only from the X component's keys, losing
   rotations animated on Y/Z alone (the door hinge). Keys are now built on the union of all component times, with hemisphere continuity.
4. **One-frame pose clips are not evaluated** by Unity's legacy `Animation` (length 0). `CreateClipFromResource(..., minimumDuration)` holds
   single-key curves for 0.5 s; the pose is played `ClampForever`.
5. **Layering is required.** Sims 2 idles/gestures are authored over the neutral pose. Layer 0 = pose, 1 = idle, 2 = one-shots; the union of IK
   chains of pose + current clip must be active (`AdjustInverseKinematicWeightsForAnimations`), or the arms stay in T-pose.
6. **Rebuilding the animation graph during playback is unsafe**: all IK chains are registered when the Sim is created.
7. Unity 6: compressed textures must be a multiple of 4 (tiny DXT3 mips patched), shader `#include` paths, Unity audio disabled (FMOD
   device deadlock crashed the editor on this machine; audio is not used).
8. Warnings that remain and are harmless: `Bone or blend for animation channel hair_trans / t_topgrow / r_eyestretch / l_eyestretch /
   eyedirection not found` (those blend/bones are not on the OpenTS2-assembled head).
9. Mirrors: OpenTS2 cannot load mirror CRES resources (`cViewerRefNodeRecursive`); the frame is loaded as a bare SHPE and the reflection is ours.
