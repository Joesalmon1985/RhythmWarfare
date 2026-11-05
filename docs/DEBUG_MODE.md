# Debug / Playtest mode

For listening and playing through every scene on purpose, and writing down what you do not like so it can be traced to **one song file or one visual**. Everything here is text and
buttons for the owner; regular play is unchanged (the run still writes nothing on the screen: `docs/THREE_PATHS_AND_FACES_PLAN.md` D3, `tests/test_run_hud_silent.gd`).

## Open it

* Home screen: the **Debug / Playtest** button (beside Settings). It is in every build, nothing to switch on first.
* `RW_DEBUG=1` (desktop, scripted runs): the overlay and the feedback buttons are on for any run launched with it, including plain Play (the home button then reads "Debug / Playtest (on)").
* Debug mode ends when the home screen is shown again (the Back button of the list, Pause > Quit to home).

## The scene list

Every playable scene, grouped by run and world: **the main 174 BPM run (36 scenes, 7 worlds)**, **The Life of Jesus** (Gospel, 17), **The Mission Count** (Squadron, 14), **The Ember Road** (15);
the two-scene **Stub** test path appears only in the editor and test runs (it is excluded from exports). The chips at the top jump to a run.

* **Tap a row** to start the game AT that scene (the same machinery as `RW_RUN_START` / `RW_RUN_PATH`: `Session.run_start_node` and `run_start_path`).
* **Info** opens the scene's full identity (below) with a START HERE button and "Copy these details".
* A row reads: `scene id   Title` / `BPM  tier  Set name(s)  [pack ids, ">" where the arrangement switches]  OWNER | OWNER stand-in (temp) | PLACEHOLDER`. A leading `!` marks a scene whose
  packs or stems did not resolve (should never show).
* **Options** (for scenes started from the list): continue into the next scene when it ends (default on, as the game would; off = back to the list at the scene's end); autoplay the pads
  (the test bot, `RW_RUN_BOT=perfect`: hear a whole arrangement without playing; it is the only assist and it already existed for the tests); give the hotspot flags the scene needs (so every hotspot is on offer);
  also show the old play text (`DevText`: title cards, captions, countdown); start energy (the run's 60, full 100, low 25); **main-run arrangement**.
* The crowd leaving ends a debug run on the list, not on the retry screen. Pause > **Back to scene list** returns at any time; Pause > Restart restarts the scene you are in.
* **Progress is not touched.** A scene started from the list plays in a throwaway save (`user://playtest_run_save.json`); your real reached levels, flags and seed come back when home is shown.

### The arrangement option (read this)

Every scene of the 174 run has **three arrangements** of its music family (`content/story/music.json`: `arrangement` and two `alternates`) and the game picks one per run from a seed, so the song you hear in
the same room changes between runs. The list shows the arrangement in force: by default the one the game would pick with the current seed (stated in Info: "picked by the per-run seed N, as the game does"), or
choose "1st / 2nd / 3rd arrangement of every scene" to hear and rate each one. The overlay and the notes always record the arrangement that really played. The paths have one arrangement per scene.

## Reading the labels (the scene's Info and the overlay)

**AUDIO**
* *Source*: `OWNER'S LOOP`; `OWNER'S LOOP (stand-in, temporary)` (music.json `temporary`: the Underworld plays Lv2 / Cold Fusion loops until Lv3 Hell exists); `PLACEHOLDER (synthesised, temporary)` (the Gospel and Ember).
* *Pack* `squadron_c07 (C07)`: the pack id, its label, the loop length. Under it the three **stem files exactly as in your exports**: `Drums: Beat Shaper - C07-Drums.wav`, `Bass: ...`, `Synth: ...`
  (read from each pack's `pack.json`, `loops.<voice>.source_file`; a placeholder has none, so it names the pack's stem instead). `(STEM MISSING)` would mean the stem does not load.
* *Cues (tier n)*: the Drums and Bass **MIDI** files the cues are charted from, at the difficulty tier of the world (min(depth, 4)).
* *Sections*: a 174-run scene is two 8-bar sections (or one 16-bar) of an arrangement, each its own pack and **mix recipe**; "CHART PACK PER BLOCK" lists which pack charts each of the four blocks.
* *Music family*: scenes of one family share key and sound; the bass of the scene you leave carries into the next (`mix.carry_bass`).

**MIX IN FORCE**: the four stage gains (drums / bass / synth; stage 1 drums alone, 2 bass enters, 3 drums return, 4 bass strongest), the run level (`mix.gain_db`), the bass bus (high-pass, shelf, drive, pre / post gain),
the bass carry, the recipe bass floor, the hotspot dip. In play the overlay adds what is actually heard (the smoothed voice gains) beside the stage's target.

**VISUAL**: the art **map** (and its stage node), the **view** (the scene's home waypoint) and its sector and room, the **light preset** (the sector's sky: night / dawn / day / morning or "indoors (no sky)", the light level, tint, fog),
the set **pieces** on (and how many are off), the **cast** (the people directed in this scene), the **crowd** homed in the room, and the **hotspots on offer** (id, kind, the person who acts, where it leads), with the flags they need.

**The overlay** (in play): scene, BPM, `phase n | block k/4 | stage | beat | energy`, the pack playing right now (and `section 2/2` when the arrangement switches), the stem and MIDI file names, the mix, the visual line,
the cast and hotspot ids. The `PT` button (key `H`) hides the panel and the three buttons. `RW_DEBUG=1` or the list turns it on; no other play has it.

## Feedback: tell it what you did not like

Three big buttons on the stage, with hotkeys on a keyboard:

| Button | Key | Writes |
| --- | --- | --- |
| Don't like the MUSIC | `M` | `music_dislike` |
| Don't like the VISUALS | `V` | `visual_dislike` |
| Like it | `L` | `like` |

Each press appends one entry and shows a toast ("Saved: DON'T LIKE THE MUSIC | squadron/city | squadron_c07"). Pause also has a note field and **Save note** (`note`). An entry holds: time, run, scene id and title,
phase, block, stage, beat, BPM, energy, the packs of the scene, **the pack and the stem and MIDI file names playing at that moment**, source and `temporary`, the arrangement and tier, the visual ids (map, view, sector, light, pieces on, cast, hotspots), the verdict and your text.

## Where the notes are and how to send them back

Two files in the app's user folder (`user://`): `playtest_notes.md` (readable, one block per press) and `playtest_notes.jsonl` (one JSON object per line).

* **In the game**: list > **Notes (n)** shows them newest first with **Copy all** (the readable file to the clipboard: paste it straight into the chat) and **Copy JSON lines**. The screen prints the real folder.
* **Windows**: `%APPDATA%\Godot\app_userdata\Rhythm Warfare\`.
* **Android**: the app's private folder; on most phones `Android/data/com.joesalmon.rhythmwarfare/files/` (a build with USB debugging: `adb shell run-as com.joesalmon.rhythmwarfare cat files/playtest_notes.md`). Copy all and paste is the easy way.
* **Summary**: `python tools/run/playtest_notes_summary.py playtest_notes.jsonl` prints the songs (packs, with the stems named as your DAW files, source, scenes), your sets, the visuals (map / view) and the scenes
  ranked by dislikes, and every typed note. `--top n`, `--json`.

## Limits

* Nothing here was run on a phone: the list, overlay and notes were checked headless and in desktop screenshots (`docs/shots/debug/`); the touch sizes follow the game's (rows 76 units, feedback buttons 64 units high in the 720-unit layout).
* Starting mid-scene or with the bass already revealed is not offered; a scene starts as it always does, on drums alone.
* The Bassment (the dungeon between two scenes) is not in the list; the overlay says "THE BASSMENT" while you are in it and notes still write.
* The overlay's identity is read from the loaders; if the packs are re-laid on disk (shared stems, Ogg) it still names the owner's files because it reads `pack.json`, but the file paths it checks are the packs' own `stems`.

## Checks and tools

* `tests/test_playtest.gd`: the list holds exactly every scene of every run and path; every row's packs and stems resolve and carry the owner's names; the arrangement option; every scene starts through the debug route on the virtual clock;
  the overlay, the buttons, the hotkeys and the notes (written, read back, parsed); the throwaway save; the home button; with the mode off there is no overlay and the HUD writes nothing.
  `tools/content/test_playtest_notes_summary.py`: the summary.
* `bash tools/run/shoot_debug.sh`: the screenshots in `docs/shots/debug/` (needs a display). Screenshot hooks: `RW_DEBUG_DETAIL=<run>/<scene>` opens a scene's Info, `RW_DEBUG_SCROLL=<run id>` scrolls the list.
* Code: `src/debug/` (`playtest_mode.gd` the switch and options, `playtest_catalog.gd` the identity as data, `playtest_list.gd`, `playtest_overlay.gd`, `playtest_notes.gd`, `playtest_notes_screen.gd`); the hooks in `run_play.gd`
  (the launch options, the overlay, the pause panel), `run_data.gd` (`arrangement_override`), `dev_text.gd` and the home button in `main_menu.gd`.
