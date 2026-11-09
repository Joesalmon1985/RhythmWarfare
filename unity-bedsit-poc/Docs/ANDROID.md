# Android

## Status
| Item | State |
|---|---|
| Android build support (SDK, NDK, OpenJDK, Gradle 9.3.1) | installed with Unity 6000.3.28f1 |
| APK build | **succeeds**: `Builds/Android/UnityBedsitPOC.apk`, 35.9 MB, arm64-v8a, IL2CPP, minSdk 25, targetSdk 36, OpenGL ES 3, landscape, package `com.joesalmon.unitybedsitpoc` |
| Content | baked 3D room + 4 Sims inside the APK (`BAKING.md`); no Sims 2 install needed |
| Debug-signed | yes (Unity default keystore) |
| Installed / run on a phone | **NOT done**: no device was connected to this PC |
| Performance, touch feel, thermals, 20:9 layout, GPU compatibility of the OpenTS2 surface shaders on a real GPU | **NOT verified** |

## Build
Editor menu `Bedsit/Build/Android APK` (or `BuildScripts.BuildAndroid()` in batch mode with `-executeMethod`). Requires `Assets/LocalBaked`
(created by the baker on the machine that owns Sims 2). Install: `adb install -r Builds/Android/UnityBedsitPOC.apk`.

## Mobile settings applied automatically (`BedsitGame.ApplyPlatformQuality`)
30 fps target, hard shadows only, shadow distance 9 m, no MSAA, 2 pixel lights, mirror render texture 512 px high (1024 on desktop), screen kept awake,
landscape. Input: touch arrives as mouse events (Unity touch simulation); the same screen regions (left 22 %, right 22 %, top-centre) drive the three actions.

## Fixes needed to get here
OpenTS2's `CursorPlugin.dll` (x86/x64) was marked compatible with every platform and broke the Gradle step: now Windows/Editor only.
Minimum API raised to 25 (Unity 6.3 no longer supports 24).

## Likely first problems on a phone (to look at first)
1. Surface-shader cost: 79 materials use OpenTS2's Lambert + shadows shader; if slow, switch the baked materials to a simple mobile unlit/vertex-lit shader.
2. Memory: 120 meshes + 64 ASTC textures should be modest (APK 36 MB), but skinned meshes of four Sims with hair-alpha layers are the heaviest part.
3. The mirror renders the scene a second time; drop it to 384 px or render it at 15 fps if needed.
