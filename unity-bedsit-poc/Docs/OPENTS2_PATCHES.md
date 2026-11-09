# Changes to vendored OpenTS2 (MPL-2.0)

Source: https://github.com/LazyDuchess/OpenTS2 @ `bdabb07f4689ed91803a3d86dcbc8870b8832878`, copied to `Assets/ThirdParty/OpenTS2/`
(Scripts, Plugins, Shaders, Materials, Textures, the shader build pre-processor). Modified files stay under MPL-2.0 and are marked
"UnityBedsitPOC" in comments. Upstream would likely welcome the first three as fixes.

| File | Change | Why |
|---|---|---|
| `Scenes/Lot/Extensions/LotArchitectureBuildModeExtensions.cs`, `Engine/Modes/Build/BuildModeServer.cs`, `Engine/Tests/BuildModeTest.cs` | removed stray `using Codice.*`, `log4net.*`, `UnityEditor.SearchService` | IDE auto-imports; broke compile on Unity 6 and the player build |
| `Scenes/Lot/Room/RuntimeWallController.cs`, `Files/.../ScenegraphJsonDumper.cs` | `Unity.Plastic.Newtonsoft.Json` -> `Newtonsoft.Json` | Plastic SCM's bundled copy no longer exists; added `com.unity.nuget.newtonsoft-json` |
| `Shaders/**/*.shader`, `Editor/ShaderBuildPreProcessor.cs` | `#include "Assets/Shaders/..."` -> `Assets/ThirdParty/OpenTS2/Shaders/...` | files moved; without this the shaders silently rendered white |
| `Content/DBPF/Scenegraph/ScenegraphTextureAsset.cs` | tiny (2x2, 1x1) DXT3 mips decoded through a padded 4x4 block; temp textures destroyed | Unity 6 rejects compressed textures not a multiple of 4 (texture load threw) |
| `Components/SimCharacterComponent.cs` | `#if UNITY_EDITOR && OPENTS2_BONE_DEBUG` around bone gizmos | gizmos polluted the game view |
|  | `CreatePersonOutfit(..., skinnedParts)`; deferred shape binding; `CreateAnimatedFromOutfit`; `AdjustInverseKinematicWeightsForAnimations` | animatable dressed Sims (clothing deforms with the skeleton; union of IK chains) |
| `Components/ScenegraphComponent.cs` | `AddSkinnedShape`; skip subsets whose material resource is missing (warning instead of aborting the graph) | skinned outfits; some CAS heads referenced a missing material |
| `Content/DBPF/Scenegraph/ScenegraphAnimationAsset.cs` | quaternion keys on the union of X/Y/Z key times with hemisphere continuity; `minimumDuration` to hold single-frame poses | door hinge and other single-axis animated rotations were dropped; pose clips had length 0 |
| `Plugins/{x64,x86}/CursorPlugin.dll` importers | Windows/Editor only | Android build tried to package the Windows DLLs |

Not used/not compiled in our scenes (still vendored for completeness): lot/neighborhood/UI/Lua/SimAntics systems and OpenTS2's own test scenes.
