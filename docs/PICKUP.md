# PICKUP: start here (new agent, new machine)

Written 5 November 2026 by the integrator who merged the last four feature branches into `main`. This is the single entry point. After it read `docs/HANDOVER.md` (Part A, sections A9 to A14 are the newest work), `README.md` (layout and commands) and the document each section below points to.

## 1. State of the game

Rhythm Warfare is a Godot 4.5.1 landscape phone rhythm game. Four lit pads are played in time with the music while the camera rides a rail through 2.5D worlds: the 174 BPM main run (Warehouse club, Mothership, Underworld, Hospital, Ward; 36 scenes), three branching adventures entered from the Warehouse (The Life of Jesus / `gospel`, 124 BPM, 17 scenes; The Mission Count / `squadron`, 140 BPM, 14 scenes; The Ember Road / `ember`, 145 BPM, 15 scenes), the Bassment dungeon (63 passages), the Wizard Duel (local wifi) and a Debug / Playtest list of all 82 scenes. Nothing is written during play: faces, acts and light carry the story. **Everything on `main` was built and checked by agents on a desktop with a virtual clock and a dummy audio driver. Nobody has played it by hand, on a phone, or listened to it.** The next thing that matters is the owner's phone run and ears.

| Area | Built | Machine-verified | NOT verified (needs the owner's phone / ears) |
| --- | --- | --- | --- |
| 174 run, 5 worlds, rail, hotspots, saves | yes | test suite, `walk_run.sh` | feel, difficulty, whether the pads read |
| Gospel / Squadron / Ember paths | yes (placeholder Gospel and Ember loops; Squadron on the owner's loops) | hotspot checker, walkers, tests | music quality of placeholders; story readability |
| Two laps per path scene (A12) | yes, `path.laps` 2 | tests, recordings on the dummy driver | does it drag; energy for a 55 % player |
| Audio polish: bass bus, bass carry (A10) | yes | `measure_mix.py`, recordings | everything audible (bass on a phone speaker, saturation, carry) |
| Visual polish 1 and 2 (A9, A13): faces, kneel, rails | yes | stills looked at by agents | motion, phone-size reading |
| Choice clarity (A14): current-choice engine, doors, wizard poses | engine + pilot scenes only | `tests/test_choice_clarity.gd`, strips | on a phone; most scenes are staged by defaults only; the window camera is the look pass's `face` look (A15, on `integrate/look-pass`, not yet on `main`) |
| Debug / Playtest mode (A11) | yes | tests, shots | use on a phone, notes paste-back |
| Wizard Duel (wifi) | yes | two headless processes over loopback | two real phones on a real network |
| Android debug APK | yes (section 2) | aapt2 badging + apksigner | install and run on a phone: **never done** |
| Export size / memory on a phone | pack cut to ~61 % (`docs/REPO_SIZE.md`) | `tools/export_smoke.gd` | load time, memory on a real phone |

Merge facts (this integration): origin/feature/two-laps, polish-leftovers, choice-briefs and choice-clarity were merged with `--no-ff` onto 55f6cd3f (the owner had meanwhile merged choice-clarity's PR #1 on GitHub; it was merged in again, no tree change). Conflicts were only `docs/HANDOVER.md` (A12, A13, A14 all kept), `RunPlay._scripted_select` (laps condition and several-touch strip support combined) and the generated people sheets, which were regenerated from the merged sources in a separate commit (not merged). **Full `bash tools/test.sh`: 82,082 checks, 0 failures, exit 0; Python content tests 216 OK.** `check_hotspots.py` main / gospel / squadron / ember: 0 errors (5 / 15 / 1 / 19 warnings, as before); `walk_run.sh` main 36 of 36 scenes, gospel 17 of 17, squadron 14 of 14, ember 15 of 15, all `run walk-through: OK`; `export_smoke.gd` 0 failures; `check_assets.py` OK. Nothing was switched off by data: laps (`path.laps` 2) and choice staging are both on. People-sheet bytes (pages, 55f6cd3f -> now): airfield +12.2 %, ash_land +4.2 %, bethany +4.5 %, birch_hall +2.6 %, **city +24.3 %** (over the +15 % budget: choice-clarity's beckon/plead acts), deep_halls +4.2 %, galilee_shore +13.7 %, harbour +10.3 %, hillside +4.6 %, hospital +1.0 %, jerusalem +6.7 %, mental_hospital +1.5 %, mothership +0.7 %, night_one +2.1 %, orchard +5.1 %, underworld +0.5 %. Merged-result screenshots (Warehouse floor with the wizard and a lit door, Gospel, Squadron, Ember, a Bassment passage with drawn doors) are in `docs/shots/merge/` and render sanely; under the player's own camera the Warehouse wizard is out of frame in the window (the known missing window camera, 5(a)1).

## 2. New-machine setup

Paths in older docs are the original owner's PC (`C:\Users\joesa\...`, Windows 11). **Adapt them.** Files that hard-code them (from a grep of the repository):

* `export_presets.cfg` line 65: `keystore/debug="C:/Users/joesa/AppData/Roaming/Godot/keystores/debug.keystore"`. Edit it, or blank `keystore/debug`, `keystore/debug_user`, `keystore/debug_password` to fall back to Godot's editor settings.
* `docs/EXPORT.md` (Godot binary, SDK, JDK, keystore paths and commands), `docs/REPO_SIZE.md` line 161, `docs/HANDOVER.md` ("Everyday commands"), `docs/CAMPAIGN_PLAN.md`, `docs/NEXT_AGENT_PROMPT.md`, `docs/NEXT_AGENT_PROMPT_PATHS.md` (old hand-off prompts that name the owner's checkout `C:\Users\joesa\Documents\Cursor\MusicGame`; superseded by this file).
* `tools/extract_openra.py`, `tools/extract_openra_sounds.py`, `assets/openra/PROVENANCE.md`: point at the owner's `DuelMasterBattle` checkout (only needed to re-extract OpenRA sprites/sounds; the extracted assets are committed, so ignore them).
* The scripts default the Godot path to either `$USERPROFILE/Downloads/Godot_v4.5.1-stable_win64.exe/Godot_v4.5.1-stable_win64_console.exe` (`tools/test.sh`, `tools/balance.sh`, `tools/balance_missions.py`, `tools/run/acting_gospel.py`, `tools/run/shoot_gospel.sh`, `tools/content/ogg_check.py`, and `shoot_debug.sh` / `shoot_silent.sh` when `USERPROFILE` is set) or to `$HOME/godot/Godot_v4.5.1-stable_linux.x86_64` (`tools/run/capture.sh`, `capture_path.sh`, `capture_choice.sh`, `walk_run.sh`, `frames.sh`, `tools/story/*.sh`, `tools/trial/*.sh`, `tools/paths/shoot_squadron*.sh`, `tools/duel/two_players.sh`). **Every one of them honours the `GODOT` environment variable first**, so on a new machine just `export GODOT=/path/to/Godot_..._console` (Git Bash) and nothing needs editing. Python scripts honour `PYTHON` where they call it.
* The package id `com.joesalmon.rhythmwarfare` is the owner's app id, not a path; keep it.

**Required tools**

| Tool | Version / note |
| --- | --- |
| Godot | 4.5.1 stable, the **console** binary (`..._win64_console.exe`) for headless runs |
| Godot export templates | 4.5.1.stable (`%APPDATA%\Godot\export_templates\4.5.1.stable\`) |
| JDK | 17 (the owner's was 17.0.20.1 inside `DuelMasterBattle\android-tools`; any JDK 17) |
| Android SDK | platform `android-35`, build-tools `35.0.0` (aapt2, apksigner, zipalign), platform-tools for adb |
| Debug keystore | alias `androiddebugkey`, password `android` (Godot makes one at `%APPDATA%\Godot\keystores\debug.keystore`, or `keytool -genkeypair` it); set in `export_presets.cfg` and/or Godot editor settings `export/android/*` (see `docs/EXPORT.md`) |
| Python | 3.14 (3.11+ works) with `numpy`, and `pip install mido==1.3.3` (without mido some content tests fail: known and unrelated) |
| ffmpeg | on PATH (audio conversion and the shot tools) |
| Git Bash (or any POSIX shell) | the `.sh` tools and `bash tools/test.sh`; Pillow is needed by the art builders (`pip install pillow`) |

**Build the Android debug APK** (steps of `docs/EXPORT.md`; `build/` is git-ignored; the preset `Android` is a template export, arm64-v8a only):

```
export GODOT="/path/to/Godot_v4.5.1-stable_win64_console.exe"
mkdir -p build/android
"$GODOT" --headless --path . --import
"$GODOT" --headless --path . --export-debug "Android" build/android/RhythmWarfare-debug.apk
$ANDROID_SDK/build-tools/35.0.0/aapt2 dump badging build/android/RhythmWarfare-debug.apk | head   # package, sdk 24/35
$ANDROID_SDK/build-tools/35.0.0/apksigner verify --verbose build/android/RhythmWarfare-debug.apk
adb install -r build/android/RhythmWarfare-debug.apk
```
Before the build run `"$GODOT" --headless --path . -s tools/export_smoke.gd` (checks that the exported pack holds what the game loads; see `docs/REPO_SIZE.md`). The APK built from this `main`: `build/android/RhythmWarfare-debug.apk`, 194,714,325 bytes (185.7 MiB), SHA-256 `265e91de67c3da1955b52a2dba522f0d339b0bd253314be0f1cdf50b312888f0`, package `com.joesalmon.rhythmwarfare` 0.1.0 (code 1), minSdk 24, targetSdk 35, arm64-v8a, apksigner verifies (v2, v3). Note: the manifest now carries the permissions `INTERNET`, `ACCESS_NETWORK_STATE`, `ACCESS_WIFI_STATE` (the Wizard Duel); `docs/EXPORT.md`'s "no permissions" is out of date. Never installed on a phone.

**Run the tests and walkers** (all headless, Godot console on `GODOT`):

```
bash tools/test.sh                              # whole Godot suite + Python content tests; ~15 to 20 min; exit 0 = green
bash tools/test.sh --filter run_                # a subset (Python tests skipped)
python3 tools/run/check_hotspots.py             # main run; also --path gospel|squadron|ember|stub
bash tools/run/walk_run.sh --path gospel        # real scenes on the virtual clock, every policy; also squadron, ember; no --path = main run
python3 tools/story/check_assets.py             # art checks (--determinism REWRITES processed/ and textures/ with machine-varying bytes: afterwards `git checkout` them)
godot --headless --path . -s tools/export_smoke.gd
python3 -m unittest discover -s tools/content -p "test_*.py"
```
Screenshots: `bash tools/run/capture.sh`, `capture_path.sh <path>`, `capture_choice.sh` (they need a display/GPU, not `--headless`; `docs/CONTINUOUS_RUN.md`). Run `python3 tools/shrink_shots.py` on any new `docs/shots` before committing. Annotate types on `var x := dict["k"]` (GDScript infers Variant otherwise and the parse fails).

**Regenerating art** (people sheets are generated; on a merge conflict do NOT merge them, resolve the sources, then rebuild and commit the art as its own commit):
```
python3 tools/story/build_assets.py <night_one|mothership|underworld|hospital|mental_hospital|airfield|city|harbour> people
python3 tools/story/build_ember.py people            # ash_land, birch_hall, deep_halls, orchard
python3 tools/story/build_gospel_art.py --people     # galilee_shore, hillside, bethany, jerusalem (also rewrites content/story/maps/jerusalem.json with CRLF on Windows: git checkout it)
godot --headless --path . --import
```
(`build_assets.py <unknown map> people` silently rebuilds Night One: do not pass the Ember or Gospel map names to it.) The people bake reads `staging` and the acting data, so any change to acting or staging data needs a re-bake. See `docs/FACE_POLISH.md`, `docs/STORY_ART.md`.

## 3. Files NOT in git (ask the owner)

* `NewMusic/` (untracked in the owner's checkout): the owner's Beat Shaper stems, including **`C level Music`**, the Squadron source. Needed to re-import Squadron, e.g. `python3 tools/content/beatshaper.py import --path squadron --max-error-ms 40` (`docs/MUSIC_IMPORT.md`). The **imported packs ARE committed** (`songs/packs`), so the game runs without it.
* `content/imports/` is git-ignored: where owner exports are dropped for `beatshaper.py apply` (Gospel and Ember real loops go in `content/imports/<path>/<scene>/`).
* Git-ignored and regenerable: `build/`, `.godot/`, `content/library/*/placeholder/`, `songs/*/audio/*.wav`, `midi_export/**/*.wav`, `/audition/`.
* The owner's own checkout `C:\Users\joesa\Documents\Cursor\MusicGame` (branch `feature/wizard-duel-lan`) has uncommitted state of its own (a deleted `Rhythm_Warfare_Level_01_MIDI.zip`, `NewMusic/`). Never assume it matches `main`; ask the owner before touching it.
* Local worktrees (`MusicGame-paths`, `-paths2`, `-size`, `-merge`, `-face`, `-pretest`) are local-only and may not exist on the new machine.

## 4. Branch map (origin, on 5 November 2026)

| Branch | State |
| --- | --- |
| `main` | everything below that is marked merged, plus this file |
| `feature/two-laps` | **merged** into main (A12) |
| `feature/polish-leftovers` | **merged** (A13) |
| `feature/choice-briefs` | **merged** (docs/choice) |
| `feature/choice-clarity` | **merged** (A14) |
| `feature/continuous-story-run`, `deathtrap-opening`, `face-polish`, `music-library`, `run-on-25d`, `story-25d`, `story-warehouse-music-test`, `visual-adventure`, `wizard-duel-lan` | already merged earlier (contained in main); safe to delete |
| `feature/look-pass` | merged with main on `integrate/look-pass` (HANDOVER A15: hotspot light language, edge beacons, the camera facing the window, Bassment look; conflicts and the per-piece look verdict are there); not on `main` until the owner merges that branch |

Nothing was deleted on origin. The merged branches can be deleted by the owner (`git push origin --delete <name>`) when he is happy. Worktrees are local only.

## 5. Prioritised pickup list

### (a) Choice clarity (owner's brief: every branching choice must be clear in the world)
Read `docs/CHOICE_CLARITY.md` section 0 (status and the numbered pickup list), then `docs/choice/*.md` (the per-world art/authoring briefs: `main_a_warehouse_mothership_underworld.md`, `main_b_hospital_ward.md`, `bassment.md`, `path_gospel.md`, `path_squadron.md`, `path_ember.md`). Order:
1. **Engine: the window camera (E1)**: built by the look pass as a held `face` look (`RunJourney.window_face`, `StoryPlayer.best_facing`; HANDOVER A15) once `integrate/look-pass` is merged. It frames the window's hotspot anchors (not the drawn door positions `door_at`): check on a phone, and consider framing `door_at` instead of the anchor for door options. Still needs the owner's decision (section 5(b)).
2. Then per world, lanes A to F of section 6 of the doc: set `door_at` / `sign` / `pieces` per exit, `states` per object, re-anchor the five `pos` options of the Warehouse. Author by adding `"<hotspot id>": {...}` to `tools/run/staging_data.py`, run `python3 tools/run/apply_staging.py`, re-bake people if a new act/face is named, look with `bash tools/run/capture_choice.sh`. Many defaults put a door in the middle of a room until `door_at` is set.
3. The art briefs (door skins per setting, object state pairs, a finger-post, creature frames, Bassment carriers and door-bar kits), E2 a key light on dark people, E3 a `people: [ids]` shorthand, E5 the briefs' new acts (rig + re-bake).
Tests: `tests/test_choice_clarity.gd` covers every branching scene of the four runs.

### (b) Owner decisions still open
1. **Energy balance under two laps** (`docs/HANDOVER.md` A12 section 3): a 55 % player reaches a Gospel ending 16/24 -> 7/24 and Ember 15/24 -> 11/24; players over 60 % feel no difference. Knobs: `energy.fail_loss` / `pass_gain` in `content/run/run.json` (also moves the main run), or `path.laps` back to 1. Not retuned, as asked.
2. **Do touches count before the route window?** (`run.json` `"choice": {"preselect": true}`; today touching before beat 48 does nothing.)
3. **Should the window camera turn toward the options** (item (a)1)?
4. **PERFECT / GREAT / MISS words on the pads** (keep, or remove for the silent HUD; one flag in `RunPlay._on_judge_event`).
5. **Portal discoverability gating** (the star needs `wh_saw_floor`, the ember needs `wh_vip_pass`; the radio is always there; the booth radio is an edge beacon at beats 50 to 54).
6. **Squadron's 40 ms tolerance** (C01, C02, C04, C08, C09, C12 imported at `--max-error-ms 40`; default 12) and **4-bar loops** (they repeat 8 times in a 55 s two-lap scene; 8-bar re-exports would halve it).
7. Plead vs sad beckon, drawn doors everywhere (`docs/CHOICE_CLARITY.md` section 7); the Gospel subject and ratings (A6 item 8).
8. **Optional git history rewrite** (~490 MiB of history-only blobs; commands in `docs/REPO_SIZE.md` section 4, **NOT run**). Risks: every commit hash changes, every clone and worktree and branch must be re-cut, open branches break. Do it once, only after the packs and sheets are final, and only with the owner's yes. Meanwhile: commit people sheets once per art milestone (each rebake adds ~10 MiB of history per chapter).

### (c) Real Gospel and Ember loops from the owner
Both paths still play synthesised placeholder loops. `docs/MUSIC_HANDOFF.md` holds the verbatim export prompts (17 Gospel, 15 Ember). Owner drops exports in `content/imports/<path>/<scene>/`, then `python3 tools/content/beatshaper.py --path <id> apply ...` (`docs/MUSIC_IMPORT.md`). A scene-level `bass_bus` is dropped on apply: re-measure with `python3 tools/run/measure_mix.py --run <path>` and set it again.

### (d) Unfixed visuals
From HANDOVER A9 "still looks weak" and A13 "remains weak": humanoid aliens, blobs, demons and humans have no half-size picture faces (blobs' four faces are identical at half size); the cyclops at full size untouched; `kneel`'s planted knee is large in front view, gowns hide the leg pose; `cover_face` hides the grief face by design; C12 shows a thin strip of bright coast through the quay crack and the boat is still dark; wall z-fighting of coplanar walls of adjacent rooms (no back-face culling) probably affects other maps and is not audited; many Gospel crowd scenes have directed people at 35 to 60 degrees from the rail's view; the Hospital/Ward and other main-run scenes were only looked at in a few strips. Also: after this merge the city people sheet is +24 % bytes over the 55f6cd3f baseline (the beckon/plead acts); trim if the APK size matters.

### (e) Everything needing a phone or ears: checklist
* **Phone first run**: the APK installs and starts; the pads respond at phone size; frame rate in the Ember and Hospital scenes; no stalls on scene load; the Debug / Playtest notes screen (Copy all) works.
* **Audio (A10 section 6)**: the bass carry at the Warehouse floor -> bar (seamless or muddy?); the 174 bass saturation on the phone speaker and earbuds (fuzzy on Underworld/Ward reese?); Squadron C05/C06 punch (lifted body); can the kick/snare under the drum cues still be heard (stage 2 bass 0.85)?; levels at the portals; the placeholder Gospel house and Ember psytrance bass (too loud, buzzy?).
* **Two laps (A12 section 6)**: does a minute in one room drag (Squadron: a 7 s loop eight times)?; no dropout or restart at the lap boundary (J01 / C01 / E01); four bass-cue blocks in a row in lap 2: pleasure or tiring?; do hotspots seen only after a minute get noticed?; cast lines stretched over 128 beats (stare, kneel for 24 to 32 beats): patient or frozen?; the energy for a weaker player; "Leave this path" ending the scene at the end of lap 1.
* **Visual polish (A9)**: the half-beat flash and the outcome at beat 61 before the frame closes; the 1.35 swell flare (new or a flicker?); Golgotha darkness in daylight; the crown on a finished path's portal at phone size; the brighter directed people (lit or pasted on).
* **Faces and poses (A13)**: half-size faces at the crowd's real distance; the one-knee kneel and the hands over the face in motion; the Keeper's long-shadow pool (shadow or glowing floor patch?); the Ember rails stopping four metres short of the companions.
* **Choice clarity (A14)**: open/shut doors and green/red lamps seen while playing the pads; beckon vs plead at arm's length; does staging from beat 0 help or distract; the wizard's happy/bowed frames on the dark floor; does touching a person or a door anywhere on its body select it.
* **Two phones**: Wizard Duel over a real wifi.

## 6. How to work with this owner

* The owner (Joe) is a **product owner and music producer, not a programmer** and a creative director in how he reads reports: **he wants questions before building** (use an option panel with clickable choices when you must ask), and **outcome-first, plain-English reports**: what changed for the player, what is verified, what he must listen to or look at; no diffs unless asked. Flag decisions that are his.
* The owner **stops work at a usage cap**: keep the repository always in a state a fresh agent can resume from; commit and push finished work, write the handover as you go.
* Workflow used so far: a top-level agent plans and integrates; **Sonnet subagents implement** (engine, data, tests, generators), **Opus subagents design and do graphics/art briefs**; every agent verifies with the real suite and looks at the actual screenshots (the Read tool shows images) before claiming a visual change.
* Parallel-worktree rules that worked: one git worktree and one branch per agent (`git worktree add ../MusicGame-<name> -b feature/<name> origin/main`); never touch the owner's checkout; agents `git fetch` and rebase or merge `origin/main` before pushing; **shared docs (`docs/HANDOVER.md`, `README.md`, `docs/PICKUP.md`) are edited only by the integrator** (agents write a section file or a branch-local note, to avoid conflicts); generated art (people sheets, textures, manifests, shots) is committed separately from code and rebuilt after a merge, never merged; merge with `--no-ff`, one commit per branch; push to `main` only fast-forward and only when `bash tools/test.sh` is green; never force-push or rewrite history without the owner's explicit yes.
