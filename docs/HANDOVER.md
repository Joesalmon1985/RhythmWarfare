# Rhythm Warfare: handover for the next agent

State on 28 October 2026. Read this first, then `docs/PRD.md` (the product requirements, the authority on rules)
and `README.md` (layout and commands). Everything described here is committed on `main` at
https://github.com/Joesalmon1985/RhythmWarfare (local git only before that date).

## What the game is

A mobile rhythm game: play a 174 BPM drum and bass track on three touch lanes (kick, bass, snare) and every
successful note produces Red Alert units for your side (one light tank per kick, five riflemen per snare, a
helipad or a Longbow sortie per bass action, five pads and five aircraft at most). Both armies are run by OpenRA's
Rush AI squad logic; the player never commands units. Losing the war factory mutes the kick stem and disables its
lane, losing the barracks does the same for snare, losing the last helipad mutes bass until a bass action rebuilds
one. Destroy the enemy construction yard before the song ends to win.

## Where it stands against the PRD milestones

| Milestone | State |
| --- | --- |
| M0 music and input | Done. Four stems in one `AudioStreamSynchronized`, audio-derived monotonic clock, calibration screen, pause and resume with countdown, debug stem toggles (F3). `docs/TIMING.md`. |
| M1 ground battle | Done. 53x20 temperate map at native pixels, mirrored bases, authored enemy schedule, autonomous combat, outcomes. |
| M2 air and damage | Done. Five slots, finite ammo (8), rearm 1 per 50 ticks, bass-driven sorties with the PRD priority, pad loss and rebuild tied to the bass stem. |
| M3 complete mobile level | Mostly done. Automatic OpenRA repair, readable result screen, offline Android APK exported and verified to load the pack (28 Oct fix: exported builds check stems through `ResourceLoader`, not `FileAccess`). Owner confirmed on 28 Oct 2026 that the APK installs and runs on their phone and that timing feels right after calibration on both phone and Windows (A14, and the playable half of A09). **Not done:** the real song stems (placeholder synthesised audio is in use) and the measured phone frame-time evidence (A13). |

Acceptance evidence: A01, A02, A03, A04, A05, A06, A07, A08, A10, A11 are covered by `tests/` (425 headless
checks, `bash tools/test.sh`); A09 structurally by `tests/test_transport.gd` (device alignment still to measure);
A12 by `docs/BALANCE.md`; A13 on desktop only (p95 20.8 ms at 438 live units); A14 confirmed by the owner on the phone (the `PERF` line from a phone run is still to be captured).

## Owner decisions that are settled (do not re-ask)

- Standalone Godot 4.5.1 project; the DuelMasterBattle repository is only an asset source, never edited.
- Whole track playable; landscape; the chart is the owner's Level 01 MIDI pack (138 kicks, 111 snares, 72 bass
  actions) with no hidden production cap. The owner will supply four aligned WAV stems named `audio/01_Kick.wav`
  etc.; drop them into `songs/level_01/audio/` and change the four stem paths in `level.json` (or keep `.ogg`
  names and convert with ffmpeg). The loader accepts wav, ogg and mp3 and rejects stems whose lengths differ.
- The game must look like OpenRA (native pixel art, the real animations) and units must behave like OpenRA units
  with OpenRA's bot AI on both sides. That is implemented; keep it.
- Sandbags in player colour are correct (their pixels sit in the remappable palette range in Red Alert itself).
- Phone: the owner sideloads the APK themselves and reports back.

## How the code is organised

- `src/core/`: `level.gd` and `level_loader.gd` (song-pack contract and validation), `song_clock.gd`,
  `match.gd` (one play-through: judgement rewards -> production, enemy schedule, battle, stem mute decisions),
  `session.gd` (autoload: selected pack, calibration, env overrides `RW_PACK`, `RW_AUTOPLAY`, `RW_ENEMY_FRACTION`,
  `RW_CALIBRATION_MS`, `RW_SCENE=play`).
- `src/audio/stem_transport.gd`: one player, four substreams, 30 ms gain ramps, never stops a stem.
- `src/input/judge.gd` (pure judgement state machine) and `lane_input.gd` (touch ids and keys F, Space, J).
- `src/sim/battle_sim.gd`: the deterministic 25 Hz simulation with OpenRA rule values; `bot_ai.gd`: the Rush AI
  squad manager; `rules.gd`: data loading. Pure GDScript, no nodes, so it runs headless.
- `src/ui/`: `battle_view.gd` (sequence-driven renderer: terrain, bibs, buildings, walls by adjacency, units,
  aircraft, projectiles, muzzle flashes, explosions, deaths, craters, smoke), `sprite_bank.gd` (sequences.json,
  OpenRA facing rules, frame cache), `faction_remap.gdshader` (player-colour ramp keyed on alpha 253 pixels),
  `lane_view.gd`, `hud.gd`.
- `src/scenes/`: `main_menu`, `play` (the level screen), `calibration`, `result`.
- `assets/openra/`: 2,378 native frames plus `sequences.json` and `PROVENANCE.md`; regenerate with
  `tools/extract_openra.py` (needs the pinned OpenRA checkout and the owner's Red Alert content; paths in the
  provenance file).
- `data/`: `openra_rules.json` (actors, weapons, locomotors, repair at commit e7e9e4ad), `rosters/`,
  `battlefields/mvp_mirrored_01.json` (building layout, exits, rally, air hold points), `maps/strip_53x20.json`.
- `songs/level_01/` (the level), `songs/test_16/` (for tests); `tools/make_song_pack.py` builds packs from the
  MIDI pack and synthesises placeholder stems; `songs/README.md` has the exact commands.
- `tools/`: `test.sh`, `balance.sh` and `autoplay.gd` (headless scripted matches with `RW_DEBUG_EVERY` traces and a
  per-phase profile), `shoot.gd` (scripted screenshots), `extract_openra.py`, `import_openra_assets.py` (the first,
  now superseded, importer; kept for provenance).
- `docs/`: `PRD.md`, `TIMING.md`, `BALANCE.md`, `OPENRA_BEHAVIOUR_SPEC.md` (engine-sourced spec the sim follows),
  `EXPORT.md`, `shots/` (verification screenshots).

## Deviations from OpenRA that are deliberate (all commented in code)

- Squads form at 10 + Random(10) idle units (Rush AI: 20 + Random(30)); assault squads attack-move at the enemy
  construction yard and fight what they meet within 12 cells (the engine chases the closest enemy, which a
  music-driven production trickle keeps supplying next to its own wall); the flee comparison counts every friendly
  unit in the 10-cell danger circle; targets already aimed at by many friends count as slightly farther (overkill);
  a unit whose target left range re-scans and prefers something already in range; the air squad's approach test
  uses the intended semantics (the source comparison is inverted); the fuzzy attack-or-flee logic is a crisp
  approximation (spec section 1.6).
- Repair budget 500 credits per side (the PRD's 5,000 at Red Alert cost scaling repaired indefinitely).
- Moving units slip past stationary friends (soft separation) so rear ranks reach the fight.
- Bullets damage their target only if it is still within a cell of the aim point; missiles home.

## Input and timing notes

- Lane touches and keys are read in `_input` (before the GUI), because the screen-sized Controls of the level
  would otherwise consume them; those Controls use `MOUSE_FILTER_IGNORE`, and the pause button still receives
  its clicks. Fixed 28 Oct after the owner reported no presses registering on phone and Windows.
- Every Perfect or Good shows its offset in milliseconds (positive = late). A consistent offset is device latency:
  run the calibration screen (menu) or set it by hand; the sign convention is in `docs/TIMING.md`.
- Judgement windows are the PRD's: Perfect 45 ms, Good 100 ms, hold release tolerance 60 ms.

## Known issues and polish backlog

1. Real stems: replace the synthesised placeholder audio when the owner's WAVs arrive; re-check alignment with the
   loader (it rejects a length mismatch above 5 ms) and listen for muting artefacts.
2. Phone evidence: run `RW_AUTOPLAY=perfect` on the device (the `PERF` line prints p95 frame time and peak units;
   `adb logcat -s godot`), confirm 60 FPS with about 440 live units, and the two-thumb touch feel. The sprites are
   drawn at 1:1; `BattleView.PIXEL_SCALE = 2` halves the map if they are too small on a phone.
3. Balance feel: 70% accuracy still wins with 17 s to spare; raise the ramp ends in `songs/README.md`'s command if
   the first level should be harder. Outcomes between 50% and 70% are sensitive to squad timing.
4. Presentation polish: idle infantry fidgets (`idle1`/`idle2`), prone sprites when hit, vehicle husks and the
   falling helicopter husk, building `dead` ruins for every building (only fact and powr have ruin art), scorch
   marks for napalm, camera shake, sound effects (none yet: no unit, weapon or UI sounds), lane note skins, a
   proper title screen and result screen art.
5. Dead buildings are drawn as their damaged frame darkened; OpenRA leaves rubble and craters only.
6. Tanks path straight through sandbag lines (crushing), which is OpenRA-correct but makes walls weak; consider
   brick walls (`brik`, not crushable) if the owner wants the base to hold longer.
7. The HUD is functional, not styled; the lanes and buttons are flat rectangles.
8. Gun and SAM `idle` sequences are intentionally empty frames (the turret sprite is the whole visible building),
   so the two empty PNGs `gunmake-0000.png` and `hpadmake-0000.png` must stay.
9. `tests/test_battle.gd::test_a06` depends on the air squad finding a target; if air behaviour changes, update it.
10. The repository holds 17 MB of extracted frames; they are the owner's own Red Alert content and must not be
    redistributed beyond this project (see `assets/openra/PROVENANCE.md`).

## Everyday commands

```
bash tools/test.sh                                         # 425 headless checks
bash tools/balance.sh res://songs/level_01 1.0 perfect "accuracy:0.85" none
RW_PACK=res://songs/level_01 RW_AUTOPLAY=perfect <godot> --path .          # scripted run, prints PERF at the end
<godot> --path . -s tools/shoot.gd -- res://src/scenes/play.tscn docs/shots 3000:shot:name
<godot> --headless --path . --export-debug "Android" build/android/RhythmWarfare-debug.apk   # docs/EXPORT.md
```

`<godot>` is `C:\Users\joesa\Downloads\Godot_v4.5.1-stable_win64.exe\Godot_v4.5.1-stable_win64_console.exe` on the
owner's machine. New `class_name` scripts need a `--import` before headless runs; `tools/test.sh` does that.
