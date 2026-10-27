# Exporting Rhythm Warfare

Godot **4.5.1.stable**, export presets in `export_presets.cfg` (repo root).
Output goes to `build/` which is git-ignored.

| Preset            | Platform        | Output                                  | Notes                                               |
|-------------------|-----------------|-----------------------------------------|-----------------------------------------------------|
| `Android`         | Android         | `build/android/RhythmWarfare-debug.apk` | Template export (no gradle), APK, arm64-v8a only    |
| `Windows Desktop` | Windows x86_64  | `build/windows/RhythmWarfare.exe`       | PCK embedded in the exe, plus `.console.exe` helper |

## Prerequisites (all verified present on this machine)

| What                     | Where                                                                                      |
|--------------------------|--------------------------------------------------------------------------------------------|
| Godot console binary     | `C:\Users\joesa\Downloads\Godot_v4.5.1-stable_win64.exe\Godot_v4.5.1-stable_win64_console.exe` |
| Export templates         | `%APPDATA%\Godot\export_templates\4.5.1.stable\`                                           |
| Editor settings          | `%APPDATA%\Godot\editor_settings-4.5.tres`                                                 |
| Android SDK              | `%LOCALAPPDATA%\Android\Sdk` (platforms: `android-35`; build-tools: `35.0.0`)              |
| JDK 17                   | `%LOCALAPPDATA%\DuelMasterBattle\android-tools\jdk\jdk-17.0.20.1+1`                        |
| Debug keystore           | `%APPDATA%\Godot\keystores\debug.keystore` (alias `androiddebugkey`, password `android`)   |

The SDK, JDK and debug-keystore locations are configured in the editor settings
file under `export/android/*`:

```
export/android/debug_keystore = "C:/Users/joesa/AppData/Roaming/Godot/keystores/debug.keystore"
export/android/debug_keystore_pass = "android"
export/android/java_sdk_path = "C:/Users/joesa/AppData/Local/DuelMasterBattle/android-tools/jdk/jdk-17.0.20.1+1"
export/android/android_sdk_path = "C:/Users/joesa/AppData/Local/Android/Sdk"
```

The `Android` preset also pins the debug keystore explicitly
(`keystore/debug`, `keystore/debug_user`, `keystore/debug_password`) so the
headless export does not depend on the editor-settings fallback. On a different
machine, edit those three lines (or blank them to fall back to the editor
settings).

## Commands

Run everything from the project root. Run `--import` once (and again after
pulling new assets) so the `.godot/imported` cache exists before exporting.

PowerShell:

```powershell
$godot = "C:\Users\joesa\Downloads\Godot_v4.5.1-stable_win64.exe\Godot_v4.5.1-stable_win64_console.exe"
New-Item -ItemType Directory -Force build\android, build\windows | Out-Null

& $godot --headless --path . --import
& $godot --headless --path . --export-debug "Android"         build/android/RhythmWarfare-debug.apk
& $godot --headless --path . --export-debug "Windows Desktop" build/windows/RhythmWarfare.exe
```

Git Bash:

```bash
GODOT="C:/Users/joesa/Downloads/Godot_v4.5.1-stable_win64.exe/Godot_v4.5.1-stable_win64_console.exe"
mkdir -p build/android build/windows
"$GODOT" --headless --path . --import
"$GODOT" --headless --path . --export-debug "Android"         build/android/RhythmWarfare-debug.apk
"$GODOT" --headless --path . --export-debug "Windows Desktop" build/windows/RhythmWarfare.exe
```

A successful run ends with `[ DONE ] export` (Android) / `[ DONE ] savepack`
(Windows) and exit code 0. The Android export prints
`Signing debug APK...` / `Signed` / `Verifying APK...` just before `DONE`.

For a release build use `--export-release` instead; the Android preset has no
release keystore configured yet (`keystore/release*` are blank), so fill those
in first or Godot will refuse to sign.

## Install on a phone

Enable USB debugging on the phone, connect it, then:

```
%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe install -r build\android\RhythmWarfare-debug.apk
```

Useful follow-ups:

```
%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe shell am start -n com.joesalmon.rhythmwarfare/com.godot.game.GodotApp
%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe logcat -s godot
```

## Quick verification

```powershell
# Windows: should print the Godot banner and exit 0 after 3 s
.\build\windows\RhythmWarfare.exe --headless --quit-after 3; $LASTEXITCODE

# Android: package / sdk / permissions / orientation
$aapt = "$env:LOCALAPPDATA\Android\Sdk\build-tools\35.0.0\aapt2.exe"
& $aapt dump badging build\android\RhythmWarfare-debug.apk | Select-String "^package|sdkVersion|native-code|application-label:"
& $aapt dump permissions build\android\RhythmWarfare-debug.apk   # expect only the "package:" line
```

Expected APK facts (as of the first export): ~29 MiB, `lib/arm64-v8a/libgodot_android.so`
+ `libc++_shared.so`, game data as loose files under `assets/` (template exports
do not use a `.pck`), minSdk 24, targetSdk 35, `screenOrientation=sensorLandscape`,
**no** `<uses-permission>` entries (offline game). The only `android.permission.DUMP`
string in the manifest is the `android:permission` guard on AndroidX's
`ProfileInstallReceiver` (standard in every AndroidX app; it restricts callers,
it does not grant the app anything).

## What the presets set and why

**Android**
- `gradle_build/use_gradle_build=false`, `gradle_build/export_format=0` (APK): plain
  template export; no Android Studio / gradle project is generated.
- `architectures/arm64-v8a=true` only; armeabi-v7a / x86 / x86_64 off.
- `package/unique_name="com.joesalmon.rhythmwarfare"`, `package/name="Rhythm Warfare"`,
  `version/code=1`, `version/name="0.1.0"`. Bump `version/code` for every
  installable update.
- `screen/immersive_mode=true` (hides nav/status bars), `screen/edge_to_edge=false`.
- Orientation is **not** a preset key in Godot 4: it comes from
  `display/window/handheld/orientation=4` (sensor landscape) in `project.godot`.
- Keep-screen-on is also a project setting
  (`display/window/energy_saving/keep_screen_on`, default `true`, unchanged) and
  needs no `WAKE_LOCK` permission.
- `permissions/internet=false` and every other `permissions/*` is `false`;
  `permissions/custom_permissions` is empty. `user_data_backup/allow=false`.
- `launcher_icons/*` left blank, so Godot rasterises `res://icon.svg` for all
  mipmap densities (including adaptive foreground/background/monochrome).
- Min/target SDK: in template mode these are baked into the 4.5.1 template
  (24 / 35) and match the installed `android-35` platform; the
  `gradle_build/min_sdk` / `target_sdk` fields only apply to gradle builds.

**Windows Desktop**
- `binary_format/embed_pck=true`, `binary_format/architecture="x86_64"`.
- `debug/export_console_wrapper=1` (debug only) also writes `RhythmWarfare.console.exe`,
  which shows a console with engine output; the plain exe is the one to ship.
- `application/modify_resources=false` because `rcedit` is not configured in the
  editor settings. The exe therefore keeps the stock Godot icon/version info. To
  brand it, install rcedit, set `export/windows/rcedit` in the editor settings,
  set `modify_resources=true` and `application/icon` to an `.ico`.
- `codesign/enable=false`.

## Changes made for this setup

- Created `export_presets.cfg` (new file; none existed).
- Created `build/android/` and `build/windows/` (ignored by git via `build/`).
- Nothing under `src/`, `songs/`, `data/`, `assets/`, `tests/`, `project.godot` or the
  editor settings was modified. No SDK packages had to be installed: build-tools
  35.0.0 (apksigner, zipalign, aapt2) and platform android-35 were already present.
