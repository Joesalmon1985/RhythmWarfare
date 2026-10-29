# Rhythm Warfare: handover for the next agent

State on 29 October 2026, after the defense campaign build. Read this first, then `docs/PRD.md` (section 14 is the
rule set for the campaign; sections 1 to 13 still describe the legacy duel), `README.md` (layout and commands) and
`docs/CAMPAIGN_PLAN.md` (the plan this build followed; its divergences are listed below). Everything is committed on
`main` at https://github.com/Joesalmon1985/RhythmWarfare.

## What the game is now

A mobile rhythm game with a three-level defense campaign. You play a chart on four unlabelled buttons; every
successful note builds a **group** of OpenRA units (the recipe of the instrument equipped in that note's slot) that
walks to one of three defense points in front of your base, round robin, and holds it. Enemy waves arrive from three
entries on a schedule that ignores your accuracy; they walk via a defense point to your **command core**. Lose the
core and the run is over at once; reach the end of the song with it alive and you win, enemies or not. There is no
enemy base. Clearing a level unlocks the next level and its instruments. Misses cost production only.

| Level | Song | Chart | Equipped by default | What it teaches |
| --- | --- | --- | --- | --- |
| 1 First Watch | 32 bars, 44.1 s | 64 taps on buttons 1 and 4 | March Kick (2 riflemen), Guard Snare (1 jeep) | steady half-time pulse |
| 2 Second Pulse | 40 bars, 55.2 s | 96 taps on buttons 1, 2, 4 (practice chart: 80) | + Armour Kick (light tank, jeep, repeating) | a third input, a second kick |
| 3 Hold the Line | 48 bars, 66.2 s | 60 drum taps + 29 bass holds, drums and bass alternating every 8 bars | + Patrol Sub (2 riflemen + 1 rocket soldier per hold) | bass holds across all four buttons |

The old two-sided duel (`songs/level_01`, `songs/test_16`, schema 1) is still in the game as "Free play" and still
passes its tests; delete it only when the owner says so.

## Verified and not verified

Verified (29 Oct 2026, this machine):
- `bash tools/test.sh`: 1,750 headless checks, 0 failures (the old duel tests plus the schema 2 loader, importer
  regression, judge-by-slot, transport with five streams, defense simulation, catalogue, campaign save, balance guard
  rails). One expected `Parse JSON failed` line is the corrupt-save test.
- `python tools/campaign/validate_campaign.py campaign`: the pack's 102 structural checks pass.
- The importer reproduces the pack's compiled charts exactly (64 / 96 / 89 events, practice 80) and the 18 MIDI hashes
  match `campaign/Musical_Source_Integrity.json` (a test re-hashes them).
- Seeds 1 to 3 for perfect, 0.85, 0.6 and no input on all three levels (`docs/BALANCE.md`): perfect and 0.85 survive,
  no input loses; 0.6 is reported (level 3 loses it).
- Desktop real-window run of level 3 with perfect autoplay: p95 16.67 ms (vsync-capped 60 Hz), 1 of 3,971 frames over
  33 ms, peak 176 live units. Windows export runs the level 2 pack headless; the Android APK (42.8 MB) exports and
  signs and contains the packs and data.
- Screenshots of the playtest, battle, menu and loadout screens were looked at; nothing was played by a person.

**Not verified:** a phone run (touch feel, thumb gaps, frame time on the device), real stems (all audio is
synthesised placeholder sound), any human playtest of difficulty or of the charts, alignment of stems by ear, the result
screen's look after a real clear (the logic is tested, the screen was not screenshotted after a clear), the 0.6
accuracy difficulty as the owner wants it.

## How to run the phone check (the owner's)

1. Build and install: `docs/EXPORT.md` (`--export-debug "Android" build/android/RhythmWarfare-debug.apk`, then
   `adb install -r build\android\RhythmWarfare-debug.apk`).
2. Open the app, press Calibrate once, then play **Level 3** by hand (the heaviest: five stems, bass holds, about 100
   to 180 live units). The note approach slider is under the level list (default 2.2 s).
3. Read the frame times afterwards: `adb logcat -s godot` prints a `PERF {...}` line when a run ends (p95, frames over
   33 ms, peak units, device). Report that line and whether any press felt missed on the held-thumb passages.
4. Thumb layout to judge: left thumb buttons 1 and 2, right thumb 3 and 4; the chart avoids same-thumb gaps under 960
   ticks (345 ms) and 480 ticks after a hold. These are design targets, untested on a phone.

## Replacing the placeholder audio with real stems

One WAV (or Ogg) per slot and profile, 48 kHz, same start and length for every stem of a song, rendered from bar 1
through one tail bar (level 1 ends at the start of bar 34, level 2 at 42, level 3 at 50; `Render_Checklist.csv` in each
`campaign/First_Three/level_0N/` folder names the files). Put them in `songs/<pack>/audio/` under the names already in
that pack's `level.json` (`kick_1__kick_march.ogg`, `other.ogg`, ...) or change the file names in `renders`, set
`"placeholder": false`, and run `python tools/campaign/audio_preflight.py songs/<pack>`: it checks existence, decoding,
rate, equal frames, coverage of the song plus tail, headroom, that `source_sha256` still matches the MIDI, and prints
the times to listen at (start, each focus change, the deadline). A profile with no render for a song shows as locked
for that song on the loadout screen; only renders that exist can be equipped. Do not run `build_defense_pack.py` for a
level whose audio you replaced by hand: it regenerates the placeholders (use `--waves-only` for balance changes).

## Owner decisions that are settled (do not re-ask)

- Standalone Godot 4.5.1; DuelMasterBattle is an asset source only, never edited.
- The campaign prompt's rules win over the old PRD for schema 2: survival win, no enemy base, three defense points with
  round-robin groups, slot-based recipes, four unlabelled buttons with authored placement, 2 kick / 2 snare / 3 bass
  loadout caps, per-slot stems, no one-miss failure, windows unchanged (45 / 100 ms, hold release 60 ms).
- Work on `main`, staged commits, duel path kept as legacy, no new branch.
- Look: OpenRA native pixel art with real animations and OpenRA unit behaviour; the owner sideloads the APK and reports.
- Placeholder sound is labelled as such everywhere (pack manifest, loadout screen, pack loader warning).

## How the code is organised (campaign additions in bold)

- `src/core/`: `level.gd`, `level_loader.gd` (schema 1 and dispatch), **`defense_loader.gd`** (schema 2: chart rules,
  thumb checks, render hashes, waves, `equip`), **`catalogue.gd`** (instrument profiles, recipe validation, loadout
  validation), **`campaign.gd`** (levels, saved progress, unlocks, loadouts), `match.gd` (schema 1 duel flow and the
  schema 2 defense flow: rewards -> slot -> profile -> recipe step -> group, waves by time, slot gating), `session.gd`
  (autoload: pack, chart id, loadout, `lookahead_s`, campaign, env overrides `RW_PACK`, `RW_CHART`, `RW_BATTLE=off`,
  `RW_LOOKAHEAD`, `RW_AUTOPLAY`, `RW_CALIBRATION_MS`, `RW_SCENE=play`), `song_clock.gd`.
- `src/audio/stem_transport.gd`: one player, any number of substreams (3 to 5 used, 32 allowed), gain ramps, never
  stops a stem.
- `src/input/judge.gd`: judgement over buttons, availability and rewards keyed by `slot_id`; `lane_input.gd` (keys D F J K).
- `src/sim/battle_sim.gd`: the deterministic 25 Hz OpenRA simulation. Defense mode (battlefield `mode: defense`):
  objectives, defense points, entries, `produce_group`, `spawn_wave_unit`, outcome rules. **`defense_ai.gd`** replaces
  the Rush AI there (`bot_ai.gd` is duel only). `rules.gd` loads data.
- `src/ui/`: `battle_view.gd`, `hud.gd` (duel HUD and the defense HUD: core health, time left, defenders per point,
  wave warning with route), `lane_view.gd` (notes, focus cue, `lookahead_s`), `sprite_bank.gd`.
- `src/scenes/`: `main_menu` (campaign list, free play, rhythm playtest, calibration, approach slider), **`loadout`**,
  `play`, `result`, `calibration`.
- `data/`: `battlefields/defense_01.json` (+ the duel's `mvp_mirrored_01.json`), **`campaign/campaign.json`**,
  **`campaign/waves/level_0N.json`** (tuned waves and level rules), **`instruments/catalogue.json`**, `openra_rules.json`,
  rosters, map.
- `songs/`: `first_watch`, `second_pulse`, `hold_the_line` (schema 2) plus the two duel packs.
- `tools/campaign/`: `build_defense_pack.py` (one command per level; importer, placeholder stems, level.json),
  `gen_waves.py`, `audio_preflight.py`, and the pack's reference `compile_chart.py` / `validate_campaign.py` /
  `build_campaign.py` (unchanged except `compile_chart(write=False)`). `tools/balance.sh`, `balance_report.py`,
  `autoplay.gd` (headless harness), `shoot.gd` (screenshots), `probe.gd` (duel pathing).
- `campaign/` is the owner's starter pack (source data; `.gdignore` keeps Godot out of it). Never edit the MIDI.

## Divergences from `docs/CAMPAIGN_PLAN.md` (all intentional)

1. Producer gating reads the actor's production **queue** (Infantry -> barracks, Vehicle -> war factory, Aircraft -> pad)
   because `openra_rules.json` only has `build_at` for infantry and aircraft. The catalogue's tags are validated against it.
2. The production core (recipes, groups, round robin) landed in stage 2 so level 1 was playable; stage 3 added the
   catalogue validation, loadout rules and the tests.
3. The pack's `waves.proposed.json` is replaced by tuned files in `data/campaign/waves/` (scaled counts plus level
   rules such as `objective_hp`); entries moved to 14-17 cells beyond the wall (x = 31), not the map edge.
4. The command core's hit points are a level rule (60,000, not the building's 150,000): see `docs/BALANCE.md`.
5. Enemy wave units ignore buildings other than their objective (`Ent.ignore_structures`), or they park at the
   pillboxes forever. Defenders keep the normal auto-target behaviour.
6. Placeholder renders exist for **every** catalogue profile unlocked by level 3 in each active slot's family (not only
   the defaults), so the loadout screen can swap instruments; their timbres differ only by pitch and a buzzier bass.
7. Practice on the loadout screen is rhythm only (battlefield hidden, nothing saved) on the practice chart when the
   level has one (level 2) and on the campaign chart otherwise.
8. Placeholder stems are scaled (0.55) so the five-stem sum stays under full scale; `audio_preflight.py` fails a loadout
   whose stems sum above 1.0.
9. The loader, not only the importer, enforces the rules (the importer's reference compiler rejects thumb gaps; the
   loader turns those two gaps into warnings and the hold-plus-tap into an error, as planned).
10. `_on_song_finished` in `play.gd` is a fallback only: survival resolves at `duration_ticks` and nothing past the
    deadline tick is simulated.
11. Levels 4 to 10 exist as campaign data entries only (`pack: ""`, status planned).
12. Test count: the duel suite is now 1,750 checks with the new files (the earlier handover quoted 425).

## Deliberate deviations from OpenRA (duel and campaign)

Unchanged from the duel build (all commented in code): crisp attack-or-flee approximation, overkill-aware target
scoring, splash never hurts the shooter's own side, repair budget 500 credits per side, moving units slip past
stationary friends, bullets hit only if the target is still within a cell, brick walls solid except for mammoth tanks.
Campaign additions: defenders have a 6-cell leash and walk home; wave units fight units and their objective only.

## Known issues and backlog

1. Real stems and the phone run (above). Retune `docs/BALANCE.md` after the owner has played: the wave scales are
   starting points chosen by a harness, not by a human.
2. Enemy peaks reach 100 to 230 live units on levels 2 and 3 when the defenders thin out; fine on the desktop, unmeasured
   on a phone. `BattleView.PIXEL_SCALE = 2` halves the map if sprites are too small or slow.
3. Levels 4 to 10, the air-service recipe (recognised by the catalogue, used by no level), second objective (`tech_core`)
   and battlefield variants with more defenses are planned in `campaign/Plan/`, not built.
4. The loadout screen is functional, not styled; no audition of an instrument's sound (renders play only in the level).
5. Duel backlog items (idle fidgets, ruins, sound effects, title art) still apply; none is campaign-critical.

## Everyday commands

```
bash tools/test.sh                                                   # 1,750 headless checks (about 35 s)
python tools/campaign/build_defense_pack.py all                      # rebuild packs + placeholder stems (about 15 s)
python tools/campaign/build_defense_pack.py all --waves-only         # after editing data/campaign/waves/*.json
RW_CHART=level_03.campaign RW_SEEDS="1 2 3" bash tools/balance.sh res://songs/hold_the_line 1.0 perfect "accuracy:0.85" none
python tools/campaign/audio_preflight.py songs/hold_the_line
RW_PACK=res://songs/hold_the_line RW_CHART=level_03.campaign RW_AUTOPLAY=perfect RW_SCENE=play <godot> --path .   # PERF line
RW_PACK=res://songs/second_pulse RW_CHART=level_02.practice RW_BATTLE=off <godot> --path .                        # rhythm only
<godot> --headless --path . --export-debug "Android" build/android/RhythmWarfare-debug.apk                        # docs/EXPORT.md
```

`<godot>` is `C:\Users\joesa\Downloads\Godot_v4.5.1-stable_win64.exe\Godot_v4.5.1-stable_win64_console.exe` on the
owner's machine. New `class_name` scripts need a `--import` before headless runs; `tools/test.sh` does that. In this
shell, long quoted Python in heredocs fails when it contains apostrophes: write scripts to files.
