# Rhythm Warfare: handover for the next agent

State on 30 October 2026, after the defense campaign build and the owner's three layout requests (centred base, off-screen entries, unlock-all). Read this first, then `docs/PRD.md` (section 14 is the
rule set for the campaign; sections 1 to 13 still describe the legacy duel), `README.md` (layout and commands) and
`docs/CAMPAIGN_PLAN.md` (the plan this build followed; its divergences are listed below). Everything is committed on
`main` at https://github.com/Joesalmon1985/RhythmWarfare.

## What the game is now

A mobile rhythm game with a three-level defense campaign. You play a chart on four unlabelled buttons; every
successful note builds a **group** of OpenRA units (the recipe of the instrument equipped in that note's slot) that
walks to one of three defense points outside your base, round robin, and holds it. The base sits in the middle of the
screen; enemy waves walk on from off screen at the **left, right and top** (nothing from below, the lane is there) on a
schedule that ignores your accuracy; they walk via the defense point of their side to your **command core**. Lose the
core and the run is over at once; reach the end of the song with it alive and you win, enemies or not. There is no
enemy base. Clearing a level unlocks the next level and its instruments. Misses cost production only.

| Level | Song | Chart | Equipped by default | What it teaches |
| --- | --- | --- | --- | --- |
| 1 First Watch | 32 bars, 44.1 s | 64 taps on buttons 1 and 4 | March Kick (2 riflemen), Guard Snare (1 jeep) | steady half-time pulse |
| 2 Second Pulse | 40 bars, 55.2 s | 96 taps on buttons 1, 2, 4 (practice chart: 80) | + Armour Kick (light tank, jeep, repeating) | a third input, a second kick |
| 3 Hold the Line | 48 bars, 66.2 s | 60 drum taps + 29 bass holds, drums and bass alternating every 8 bars | + Patrol Sub (2 riflemen + 1 rocket soldier per hold) | bass holds across all four buttons |

The old two-sided duel (`songs/level_01`, `songs/test_16`, schema 1) is still in the game as "Free play" and still
passes its tests; delete it only when the owner says so.

## Layout change of 30 October 2026 (centred base, off-screen entries, unlock-all)

- **Map**: `data/maps/field_80x40.json` (80 x 40 cells) and `data/battlefields/defense_01.json`, both written by
  `python tools/campaign/build_battlefield.py` (edit the script, not the JSON). One brick compound, ring x 28 to 50,
  y 16 to 25, five-cell openings left (rows 19 to 23), right and top (columns 37 to 41), one pillbox at the end of each
  opening, factory, barracks, core, power plant and dome inside; defense points 1 left (24,21), 2 top (39,13),
  3 right (54,21); entries `left` (8,21), `top` (39,0), `right` (70,21). `view.center` (39.5, 20.5) and
  `view.max_cells` (53.4 x 20) define the window.
- **View**: `BattleView.window_rect()` picks the visible window (never larger than `max_cells`, centred on `view.center`),
  everything outside it is masked, sprites stay at native scale; a screen wider than 16:9 shows dark bars beside the
  window rather than the spawn area. The pause button moved to the top right (the top defense point is under the
  centre). The HUD wave warning says `WAVE n INCOMING FROM THE LEFT|RIGHT|TOP s`, draws an arrow at that edge and the
  route to the defense point.
- **Waves**: every level uses all three approaches (round robin spreads defenders over all three points, so one
  approach wastes two thirds of them). `tools/campaign/retime_waves.py` assigns entries and spawn ticks from contact
  times (first contact 12.6 s, last unit 2 s before the song ends); `build_defense_pack.py` prints travel times per actor
  and flags a wave that breaks either limit. Order of work after any edit: `gen_waves.py` (counts), `retime_waves.py`,
  `build_defense_pack.py <n> --waves-only`, `tools/test.sh`, `tools/balance.sh`.
- **Unlock-all** (testing): `"unlock_all": true` in `data/campaign/campaign.json` opens every playable level from the
  menu and, per level, every profile whose `available_from_level` is at or below it; clears and bests still save, the
  stored unlocks ignore the switch, the menu shows a note. **To turn it off set it to `false`** in that file (or run with
  `RW_UNLOCK_ALL=0`; `RW_UNLOCK_ALL=1` forces it on) and rebuild the exports. It is on now.
- Tests: `tests/test_defense_layout.gd` (entries outside the window on 16:9, 21:9 and 4:3, base centred, wave units walk
  in unseen, production leaves the compound, first contact after the opening bars and last arrival before the end),
  plus the unlock-all test in `tests/test_campaign.gd`. Other tests needed only the entry id changed.
- Balance after the change: `docs/BALANCE.md` (perfect and 0.85 survive, none loses on all three levels; 0.6 reported).
  Nobody has played this layout: see "Not verified" below.

## Verified and not verified

Verified (30 Oct 2026, this machine; the 29 Oct list that follows was re-run where marked):
- `bash tools/test.sh`: 1,892 headless checks, 0 failures (the old duel tests plus the schema 2 loader, importer
  regression, judge-by-slot, transport with five streams, defense simulation, catalogue, campaign save, balance guard
  rails). One expected `Parse JSON failed` line is the corrupt-save test.
- `python tools/campaign/validate_campaign.py campaign`: the pack's 102 structural checks pass.
- The importer reproduces the pack's compiled charts exactly (64 / 96 / 89 events, practice 80) and the 18 MIDI hashes
  match `campaign/Musical_Source_Integrity.json` (a test re-hashes them).
- Seeds 1 to 3 for perfect, 0.85, 0.6 and no input on all three levels (`docs/BALANCE.md`, re-run 30 Oct on the centred
  layout): perfect and 0.85 survive, no input loses; 0.6 is reported (levels 1 and 3 lose it, level 2 loses one seed).
- Screenshots of a real-window run of level 3 (30 Oct): base centred, entries off screen, units walking in from the
  left and right edges, direction arrow and text warning, pause button top right. Looked at by the agent, not by a person.
- Desktop real-window run of level 3 with perfect autoplay (re-run 30 Oct, centred layout): p95 16.67 ms (vsync-capped
  60 Hz), 0 of 3,970 frames over 33 ms, max 25.1 ms, peak 163 live units. Windows export runs the level 2 pack headless; the Android APK (42.8 MB) exports and
  signs and contains the packs and data.
- Screenshots of the playtest, battle, menu and loadout screens were looked at; nothing was played by a person.

**Not verified:** the new layout on any screen but a 1280 x 720 desktop window (wide phones show dark bars, a 4:3 tablet
shows a 20-row window with bars above and below), whether 12 s of visible walking before contact feels right, whether
the top approach (10 s, near the HUD bar) is readable, whether enemy waves are fun with three points; a phone run (touch feel, thumb gaps, frame time on the device), real stems (all audio is
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
  wave warning with direction and route), `lane_view.gd` (notes, focus cue, `lookahead_s`), `sprite_bank.gd`.
- `src/scenes/`: `main_menu` (campaign list, free play, rhythm playtest, calibration, approach slider), **`loadout`**,
  `play`, `result`, `calibration`.
- `data/`: `battlefields/defense_01.json` (centred base, 80 x 40 map `maps/field_80x40.json`; + the duel's `mvp_mirrored_01.json`), **`campaign/campaign.json`**,
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
3. The pack's `waves.proposed.json` is replaced by tuned files in `data/campaign/waves/` (scaled counts, entries
   left / right / top and spawn ticks from `retime_waves.py`, plus level rules such as `objective_hp`).
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
   on a phone. `BattleView.PIXEL_SCALE = 2` doubles the sprites (the window then shows half as many cells; revisit `view.max_cells`).
3. Levels 4 to 10, the air-service recipe (recognised by the catalogue, used by no level), second objective (`tech_core`)
   and battlefield variants with more defenses are planned in `campaign/Plan/`, not built.
4. The loadout screen is functional, not styled; no audition of an instrument's sound (renders play only in the level).
5. Duel backlog items (idle fidgets, ruins, sound effects, title art) still apply; none is campaign-critical.

## Everyday commands

```
bash tools/test.sh                                                   # 1,892 headless checks (about 35 s)
python tools/campaign/build_defense_pack.py all                      # rebuild packs + placeholder stems (about 15 s)
python tools/campaign/build_defense_pack.py all --waves-only         # after editing data/campaign/waves/*.json (prints travel times)
python tools/campaign/build_battlefield.py                           # rewrite the map and defense_01.json
python tools/campaign/gen_waves.py 2 60000 1.4 && python tools/campaign/retime_waves.py 2   # scale counts, then entries and times
RW_CHART=level_03.campaign RW_SEEDS="1 2 3" bash tools/balance.sh res://songs/hold_the_line 1.0 perfect "accuracy:0.85" none
python tools/campaign/audio_preflight.py songs/hold_the_line
RW_PACK=res://songs/hold_the_line RW_CHART=level_03.campaign RW_AUTOPLAY=perfect RW_SCENE=play <godot> --path .   # PERF line
RW_PACK=res://songs/second_pulse RW_CHART=level_02.practice RW_BATTLE=off <godot> --path .                        # rhythm only
<godot> --headless --path . --export-debug "Android" build/android/RhythmWarfare-debug.apk                        # docs/EXPORT.md
```

`<godot>` is `C:\Users\joesa\Downloads\Godot_v4.5.1-stable_win64.exe\Godot_v4.5.1-stable_win64_console.exe` on the
owner's machine. New `class_name` scripts need a `--import` before headless runs; `tools/test.sh` does that. In this
shell, long quoted Python in heredocs fails when it contains apostrophes: write scripts to files.
