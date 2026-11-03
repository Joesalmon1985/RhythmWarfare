# Rhythm Warfare: handover

State on 3 November 2026, after `docs/BRIEF_PADS_SEQUENCES_TEN_MISSIONS.md` (four pads, sequence rewards, ten missions,
the loop library and the owner's drop-in content path), the rebuild of Mission 1 on the owner's own Ableton
recordings (`ToAddTry1/`, imported by `tools/content/import_ableton.py`) and the village version of Mission 1
(128 bars, civilians, tap-to-deploy sections, Red Alert sound effects; plan in the 3 Nov commit message). Read this first, then `README.md` (layout and commands),
`docs/PRD.md` section 15 (the mission rule set; sections 1 to 13 describe the legacy duel) and
`docs/CONTENT_TO_RENDER.md` (the owner's render list). Everything is committed on `main` at
https://github.com/Joesalmon1985/RhythmWarfare.

## What the game is now

A landscape phone rhythm defense game. Four illuminated pads play along with a 174 BPM drum and bass track; every
sequence of two to four bars you pass builds one defense or sends one unit; your Red Alert base in the middle of the
screen must keep its required buildings alive until the song ends. Ten missions, each an arrangement of a loop library
with a few musical choices of your own. Home: Continue, Campaign, Practice, Settings, and a small Developer area
(legacy duel free play, rhythm playtest, content status, unlock-all status). Normal progression is on.

## How the game plays now

- **Pads.** Four large pads at fixed positions: 1 and 2 under the left thumb, 3 and 4 under the right (keys D F J K).
  Each phase of a mission follows one family. Drum phases: the kick sound in kick slot 1 is pad 1 (slot 2: pad 2),
  the snare sound in snare slot 1 is pad 4 (slot 2: pad 3). Bass phases: one pad per bass voice, voice slots 1 to 4 on
  pads 2, 3, 1, 4, so two alternating voices sit under different thumbs. Pitches are never mapped to pads. A pad with
  nothing to play in the current phase is dim; each lit pad carries the friendly name of its sound and a shape (kick
  disc, snare diamond, bass bars) as well as its colour. At most two touches count at once.
- **Cues.** A ring closes onto the pad over the cue lead-in (setting, 0.4 to 1.2 s, default 0.7 s; it replaced the
  note approach) and the pad pulses on the beat; a hold's ring is doubled, the pad fills while you hold and flashes
  when the tail is reached. One bar before a mode change a banner names the incoming family (BASS NEXT); there is no
  roadmap. Everything is drawn from the one song clock. The lane view is gone.
- **Recognition (generous).** Perfect within 45 ms, great 90 ms, accepted 140 ms either side. One press takes the
  nearest cue of its pad; a second finger on a held pad does nothing; a press with nothing in reach is a stray.
- **Holds (forgiving).** Released within 0.15 s of the tail (or still held there) = complete; earlier = the held
  fraction counts, nothing fails. Pause ends a hold where it stands.
- **Sequences.** Missions cut each phase into sequences (four bars, two in the half-time feel; never through a hold,
  never across a mode change). A sequence passes at credit / cues >= 0.6 (taps 1 or 0, holds their coverage). A pass
  earns its **one** reward, a fail earns nothing and costs nothing already built. It resolves when its last cue is
  final, so it never rewards early and resolves the same at any frame rate.
- **Precision only sets speed.** Mean onset error of the accepted cues + 25 ms per stray per cue: sharp (<= 35 ms)
  builds in 0.5 s, steady (<= 70 ms) 1.5 s, loose 3 s. Mashing passes at best as loose. The centre of the pad strip
  shows the current sequence's progress against its threshold and what it will earn; the line under it says what was
  earned and how fast; the battlefield shows the socket being prepared with a countdown ring.
- **Rewards.** Mission 1's first drum sequence builds one pillbox. Buildings (pillbox, gun turret, flame tower) go to
  prepared sockets (`data/battlefields/defense_02.json` and `village_01.json`, five per approach flanking each route
  outside the wall, `sockets_per_point` open per mission), approach with the fewest defenses first (ties: the approach
  most enemies are walking towards, else the next wave's). Units (e1 to e4, jeep, APC with its gun only, light and
  medium tank, artillery, flak truck; squads `rifle_squad` and `grenadier_squad` are three at once) come out of the
  barracks or war factory and hold the point with the fewest defenders (at most `units_per_point`, 6 by default, 14 in
  mission 1); they may sortie up to 16 cells to hit an enemy shelling their point from beyond their 6-cell leash.
  At capacity a reward becomes a repair crew for the most damaged approach or, with nothing damaged, +50% health
  once for the oldest defense; the HUD says which.
- **Sections (tap to deploy).** A tap on the battlefield (or keys 1 2 3) makes the nearest approach by x the active
  section: a Red Alert rally flag stands at its defense point, a move flash plays, and every reward goes there while
  it has room (else the normal choice). Nothing else is drawn on the map any more: no circles, numbers, brackets,
  countdown rings or wave arrows; the top bar keeps the objective health, time, combo, defenses, enemies, villagers
  and the "WAVE n INCOMING FROM THE LEFT" line as text.
- **Civilians (mission 1).** The village map has ten houses (OpenRA `v01`..`v08`) and ten civilians (technicians
  drawn as `c1`, villagers `c2`) that wander between the houses, flee from enemies within 6 cells and die when shot;
  they never fight or repair, player units ignore them, and the result screen reports "Villagers lost x of y".
- **Sound.** `src/audio/battle_sfx.gd` plays the Red Alert effects in `assets/sfx/` (33 Ogg files extracted from the
  owner's install by `tools/extract_openra_sounds.py`) from the simulation events through `data/sfx_map.json`:
  weapon reports (M1 carbine, M60, Vulcan, grenade), kaboom and crumble on destruction, dedman screams, civilian
  cries, placbldg/build5 on pillboxes, EVA "unit ready", "enemy units approaching" (8 s before a wave), "base under
  attack", "unit lost", "mission accomplished/failed", an allied "acknowledged" on a section tap; 12 players, 8
  voices, cooldowns, EVA lines queued one deep. Effects volume in Settings; music now plays on its own "Music" bus.
- **Waves** are authored by bar per mission (`data/campaign/waves/level_NN.json`), never depend on accuracy, walk on
  from off screen at the left, top and right, attack-move via their approach's defense point to their objective and
  fight units **and defensive structures** on the way (not other buildings). A wave (or a group) may carry a
  `target` class: `defenses` (fight at the choke point and hold there), `civilians` (then the nearest house or
  villager), `core` (the objective, the default); a class falls through to the next inward one when nothing of it is
  left. A mission's level rules may add `start_units` (mission 1: five riflemen at each point) and `units_per_point`.
  Required objectives: the command core (missions 2 to 10), the barracks (mission 1), plus the power plant (6, 10) or
  radar dome (8, 10). Survive to the end of the song to win; lose a required objective and the run ends.
- **Progression.** Clearing mission n unlocks mission n+1 and the options listed in its `new_options`
  (`data/campaign/campaign.json`); a mission's own defaults are always available; no accuracy threshold blocks the
  ladder. The old save (`user://campaign.json` v1) migrates to v2 on load (clears and bests kept); settings v1 keep
  calibration and the last pack, and the cue lead-in starts at its default (the old note-approach time measured
  something else).

## The ten missions (owner's view; the menus show names and locks only)

| # | Mission | Length | Phases (D drums, B bass) | New for the player | Enemies (first appearances) | Objectives |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | First Watch | 128 bars, 177 s | DDBD BDDB DBDB DDBD | kick pad 1 and snare pad 4, then bass holds on pad 2 (drums keep playing, only one family cued at a time); drum groove, bass line, bass sound and backing track choices, all the owner's recordings; the village map (three choke points with five riflemen each, ten houses and ten civilians, the barracks in the middle), tap-to-deploy sections, pillboxes, rifle and grenadier squads; four acts: waves at the choke points, then the village, then raiders with jeeps, then the barracks | e1, e2, jeep | barracks |
| 2 | Second Pulse | 40 bars, 55 s | DDDDD | groove choice (Push / Straight), snare sound choice; turrets | e2 | core |
| 3 | Hold the Line | 48 bars, 66 s | DBDBDB | bass holds, one pad per voice; jeeps as rewards | e3, 1tnk | core |
| 4 | Backbeat | 48 bars, 66 s | DDDDDD | Two-Step groove, Snare Run fill, Siege Kick, Field Clap; flame towers, sandbags | e4, apc | core |
| 5 | Counterpoint | 56 bars, 77 s | DBDBDBD | two bass voices trading between thumbs; bass line choice | | core |
| 6 | Fortress | 56 bars, 77 s | DDDDDDD | two grooves, two kicks (pads 1 and 2); repair rewards | 2tnk, arty | core + power plant |
| 7 | Crossroads | 64 bars, 88 s | DBDBDBDB | two bass lines, three voices crossing thumbs | ftrk, v2rl | core |
| 8 | Crossfire | 64 bars, 88 s | DDDDDDDD | two snares (pads 4 and 3), fill choice | 3tnk | core + radar dome |
| 9 | Iron Rhythm | 64 bars, 88 s | DDBDDBDD | everything paired: grooves, kicks and fills in two slots | 4tnk | core |
| 10 | Last Light | 80 bars, 110 s | DDBDBDBDBD | three grooves to order, two of everything, four bass voices | all 13 ground actors | core + plant + dome |

Each mission's design notes are in its `note` field (`content/missions/level_NN.json`, `data/campaign/waves/level_NN.json`).
The coverage matrix of every ground actor and building is in `docs/BALANCE.md`, with the per-seed results.

## Content: loop library, missions, the one build command

- `content/library/<clip>/`: mission-independent clips at 174 BPM 4/4 with stable ids (grooves and fills with kick and
  snare parts, bass lines, accompaniment), one MIDI per part, a `clip.json`. **Mission 1 uses eight clips imported from
  the owner's Ableton exports** (`ToAddTry1/`, manifest `content/imports/first_watch.json`): three eight-bar grooves
  (Half-Time, Double Step, Rolling: Kick1/2/3 with Snare1), two bass lines (Sub Line from Bass1 with five recordings,
  Reese Line from Bass2 with four) and three audio-only backing loops (Driving, Busy, Offbeat Hats from Other1/2/3).
  Each declares the sounds it was recorded with (`sounds`), so it plays only its own recordings and the build never
  makes placeholders for them. Missions 2 and 3 use clips **cut from the First_Three MIDI** (two-bar grooves, eight-bar
  bass phrases) and one long accompaniment clip per song; the source MIDI is never edited and its hashes are checked on
  every build. Missions 4 to 10 use generated clips (14 new ones).
- `content/sounds.json`: 30 sounds (14 synthesised: kick, snare and bass voices, ensemble; 16 recorded by the owner)
  with friendly names. The recorded names are provisional (the hats names were inferred from the spectrum; rename in
  `sounds.json` and the clip files, then rebuild).
- `tools/content/import_ableton.py <manifest> [--check]`: files an Ableton batch into the library (44.1 to 48 kHz with
  the SoX resampler, no time-stretch; MIDI cut to the clip's bars at 960 PPQ with 174 BPM written in; WAVs cut to the
  bars plus a sounding tail of at most one bar; family gain rules, a global trim and a 10 ms end fade where a recording
  is cut mid-note; originals untouched). `content/README.md` has the manifest format and the steps for adding phrases.
- Mission features added for the owner's content: `"bound"` sound fields (the pad plays whatever the chosen clip was
  recorded with and shows that name), a `Backing track` choice (accompaniment placements with `"clip": 1`), `intros`
  (a teaching line per bar, Mission 1 has one at bar 1 and one at bar 16 when the bass starts), and dependent choices
  (`depends_on` / `with` in the pack: the Bass sound row shows only the recordings of the chosen bass line and refits
  when the line changes, in the setup screen and in `MissionLoader.fit_dependents`).
- `content/missions/level_NN.json`: choices (pools, counts, defaults), phases (which clip and sound plays where, which
  family is cued, sequence length, rewards), accompaniment, battle (battlefield, waves, rules).
- `python tools/content/build.py [level_NN ...]`: imports and validates everything, renders placeholders for every
  clip x sound a mission offers and has no owner render, assembles full-length per-slot stems offline for every offered
  combination of every usage (sample positions from absolute ticks, tails mixed, cut repetitions faded over 10 ms),
  writes `songs/mNN_*/level.json` (schema 3), `audio/` and `preview/`, `content/REPORT.md`,
  `data/campaign/library_names.json`. A full build takes about 9 minutes on this PC (stems are re-assembled every time;
  placeholders are cached). The game picks the stems that match the selection and plays them through the existing
  synchronized transport; at most 16 at once (mission 10).
- **Owner replacement**: drop `content/library/<clip>/<part>__<sound>.wav` (48 kHz stereo 16-bit, from the clip's bar 1,
  at most one bar of tail) and rebuild; edit a clip's MIDI and the build regenerates its cues and placeholders and
  refuses WAVs rendered from the old MIDI. A copied example folder (`content/fixtures/example_groove/`) becomes a new
  option once a mission lists it. Exact file list: `docs/CONTENT_TO_RENDER.md` (29 clips, 98 WAVs, 18 of them the
  owner's recordings already in place), rewritten by
  `python tools/content/render_list.py`. Proven by `tools/content/test_content.py` with the fixtures in
  `content/fixtures/` (owner WAV replaces and reverts, edited MIDI at 96 PPQ with no tempo gets new cues and makes the
  old WAV stale, bad renders rejected with their reasons).
- **Placeholder WAVs** for reference are in `content/library/<clip>/placeholder/` (133 MB, git-ignored, regenerated
  identically by the build on a fresh checkout); the game plays the Ogg stems in `songs/`.

## Verified and not verified

Verified (31 October 2026, this PC, headless unless stated):
- `bash tools/test.sh`: 1,793 GDScript checks and 9 content build tests, 0 failures. One expected
  `Parse JSON failed` line is the corrupt-save test. Covered: cue and hold recognition, generous acceptance versus
  precision speed, sequence pass/fail and one reward each, mash and duplicate presses, pause and retry determinism,
  phase continuity of the stems, socket placement and capacity, all ten missions loading with every option and
  completing (perfect wins every sequence, no input loses), progression and unlocks, save v1 migration, the legacy duel.
- The 18 First_Three MIDI hashes match `campaign/Musical_Source_Integrity.json` (checked by the build and a test).
- Seeded balance (`docs/BALANCE.md`): perfect 60 of 60 and beginner 60 of 60 wins over seeds 1 to 6, sloppy 27 of 30,
  no input 0 of 30.
- Sample-exact clip placement in the assembled stems (content test, within one sample).
- Screens looked at by the agent in real windows at 1280 x 720 and 1600 x 720: home, missions, mission setup
  (mission 1, 7 with locks, 10 with every choice), settings, play with pads and holds, pause, result. Not by a person.
- Desktop real-window run of mission 10 with perfect autoplay: see `docs/BALANCE.md` (frame time).
- Exports: see "Exports" below.

Verified (3 November 2026, the village level, this PC; see `docs/BALANCE.md` "The village level"):
- `bash tools/test.sh` green: new suites `test_village_sim.gd` (civilians, start units, target classes, squads, the
  active section), `test_civilian_art.gd`, `test_section_input.gd`, `test_battle_sfx.gd`, the rewritten mission 1
  tests (128 bars, 32 sequences, every wave destroyed by perfect play for every groove and bass line, villagers lost
  at most 4, no input loses), `tools/test_extract_openra_sounds.py` and the content tests for the village map.
- Seeded balance, seeds 1 to 3: perfect 3/3 with all 139 enemies destroyed, beginner 3/3, sloppy 2/3, no input 0/3
  (the barracks falls at about 97 s). Missions 2 to 10 produce byte-identical harness reports to before.
- Real 1280 x 720 window with perfect autoplay to VICTORY; screenshots of the village, the flag after a tap on each
  section, the move flash, the acts and the result screen with villagers. Not by a person; no sound heard by anyone.

Verified (2 November 2026, the Mission 1 rebuild, this PC):
- `bash tools/test.sh`: 2,854 GDScript checks and 20 content build tests, 0 failures. New: `tests/test_mission_one_content.gd`
  (all 81 combinations of groove x bass line x bass sound x backing load with their own stems and cues; a Sub recording
  asked for with the Reese line is swapped for the first Reese recording with a warning; defaults, 12 sequences, 6
  phases, 102 notes with every bass note a hold on pad 2, pad names from the bound sounds, both intro lines; perfect
  play wins with 12 of 12 sequences, 7 pillboxes, 5 jeeps and all 56 enemies destroyed for every groove and line; no
  input loses) and `tools/content/test_import.py` (11 tests on synthetic 44.1 kHz exports: format and length, attack
  timing against the MIDI, MIDI cut and tempo, gain, trim and fade, declarations, idempotence, pairing in the pack,
  refusals, the mode-change warning, `--check` writes nothing).
- The imported audio, by analysis (not by ear): every render is exactly 8 bars at 174 BPM (529,655 frames at 48 kHz),
  drum onsets match the MIDI within about 5 ms, the exact worst-case mix over all 81 combinations peaks at -3.03 dBFS
  and the default mix at -4.26 dBFS, the assembled stems have no clipping and no step at a loop or phase boundary
  larger than the file's own 99.9th-percentile sample step, the tail after the song end is below -43 dBFS.
- Seeded balance of the new Mission 1 (`docs/BALANCE.md`): perfect 3 of 3 wins with every wave destroyed, beginner 3
  of 3, sloppy 3 of 3, no input 0 of 3.
- Real 1280 x 720 window, `RW_MISSION=1 RW_SCENE=play RW_AUTOPLAY=perfect`: plays to VICTORY (12 of 12, holds 30 of
  30, 7 defenses, 5 units), 4 streams, 3,964 frames, average 16.7 ms, 2 frames over 33 ms (loading), 53 MB static.
  Screens looked at by the agent: mission setup with the four rows (Drum groove, Bass line, Bass sound filtered by
  the line, Backing track) before and after switching to the Reese line, the play screen in a drum phase and in a
  bass phase, the result screen. Not by a person.

**Not verified:** any phone run (touch feel, the two-thumb layout, frame time and memory with 16 Ogg streams on a
phone CPU, load time of mission 10), any listening check by ear (the build and the importer check sample positions,
lengths and headroom only; nobody has listened to the assembled Mission 1, its previews or the Red Alert effects in
the game), any human playtest of the cues, sequences, difficulty or the tap-to-deploy feel (the beginner and sloppy
policies are models; the harness taps the suggested section every frame), real owner renders for missions 2 to 10
(none exist yet; Mission 1's are real), the screens on a real phone's safe areas and DPI, the `make` animation on a
rewarded pillbox (only plays if the actor has that sequence).

## How to run the phone check (the owner's)

1. Install: `adb install -r build\android\RhythmWarfare-debug.apk` (or rebuild it first, `docs/EXPORT.md`).
2. Open the app, Settings > Calibrate once, then play mission 1 (Continue). For the heaviest case set
   `"unlock_all": true` in `data/campaign/campaign.json` and re-export, or play through, and run mission 10.
3. `adb logcat -s godot` prints a `PERF {...}` line when a run ends (p95 frame time, frames over 33 ms, peak units).
   Report that line, whether any press felt missed, whether the pads sit well under the thumbs, and the cue lead-in
   that felt right.
4. Settings has pad size, cue lead-in, high contrast, reduced effects, vibration and music volume.

## Owner decisions that are settled (do not re-ask)

From `docs/BRIEF_PADS_SEQUENCES_TEN_MISSIONS.md` Part A (31 Oct 2026): pads only (lane view dropped), one pad per bass
voice (the level 3 four-button bass chart and the thumb-gap rules are archived), a loop library at 174 BPM with
stable ids, offline assembly by one build command (no runtime clip engine, no in-game import screen), sequence rewards
replace per-note recipes, loadout caps and round robin, the legacy duel stays, holds are forgiving, early rewards are
static defenses first, wave units fight defenses, no slow practice, generated music for all ten missions, normal
progression on by default with `unlock_all` as a developer switch, the save migrates. Earlier: standalone Godot 4.5.1;
DuelMasterBattle is an asset source only; OpenRA pixel art and behaviour; work on `main`.

## Decisions made in this build (routine design details)

1. Pad mapping and windows as above (`data/campaign/rules.json` holds every number).
2. Sequence threshold 0.6; precision grades 35 / 70 ms; 25 ms per stray per cue.
3. Placeholder WAVs are not committed (133 MB); the build regenerates them deterministically.
4. Missions 1 to 3 keep their First_Three bar counts; missions 4 to 10 grow from 48 to 80 bars.
5. `fix` (service depot) is not used: the simulation has no unit-repair behaviour. `agun`/`sam` are AA-only and unused
   (no air threat). The APC is named "APC (gun only)" because it carries no troops.
6. Defenses measure range from their footprint edge in missions (flame towers could not reach riflemen otherwise);
   defenders sortie against outranging artillery and V2s. Both are mission-only, so the duel's results are unchanged.
7. Practice is the same mission with the battlefield hidden and nothing saved; the setup screen can practise one phase.
8. Mission 10's pools were trimmed to keep it at 16 streams and about 14 MB of Ogg.
9. Village level (3 Nov 2026, owner's calls): infantry only for the player, a few enemy jeeps in act 3; civilians are
   atmosphere (wander, flee, die, counted; never repair; never required); a tap sets the active section until the next
   tap (rewards before any tap are placed as before); rewards are pillboxes and rifle squads, grenadier squads from act
   3; 128 bars; the barracks is the one required objective with 60,000 hp; civilians are side-0 entities with a
   `civilian` flag (never a third side: every sim array is indexed by side); the sim uses a separate `civ_rng` for
   wandering so combat outcomes of other missions are unchanged; the autoplay harness taps sections only on levels
   with civilians (`RW_SECTION=auto|none|fixed:<i>`), because tapping the next wave's point every frame makes mission
   5 lose.

## How the code is organised

- `src/core/`: `mission_loader.gd` (schema 3: selection, stems, cues, sequences), `mission_rules.gd` (rules.json),
  `sequence_tracker.gd`, `match.gd` (mission flow: judge -> sequences -> rewards in the tick loop; and the duel flow),
  `campaign.gd` (ladder, unlocks, save v2 and the v1 migration), `session.gd` (settings v2, `start_mission`, env
  overrides), `level.gd`, `level_loader.gd` (schema 1 duel and dispatch; schema 2 is refused as retired), `song_clock.gd`.
- `src/input/pad_judge.gd` (missions), `judge.gd` (duel), `lane_input.gd` (touches and keys D F J K).
- `src/sim/battle_sim.gd` (deterministic 25 Hz OpenRA simulation; mission sockets, rewards with `count`, capacity,
  walls, prebuilt defenses, `start_units`, civilians and village buildings, wave target classes, the active section),
  `defense_ai.gd` (defenders hold and sortie, waves walk via their point then chase their class's goal, civilians
  wander and flee), `bot_ai.gd` (duel only).
- `src/ui/`: `pad_view.gd`, `battle_view.gd` (sprites only, three layers: neutral civilians, blue, red; the rally flag
  and move flash), `hud.gd` (text only), `section_picker.gd`, `ui_style.gd`, `settings_panel.gd`, `sprite_bank.gd`.
- `src/audio/`: `stem_transport.gd` (the song, on the "Music" bus), `battle_sfx.gd` (effects on the "SFX" bus from
  `data/sfx_map.json` and `assets/sfx/`).
- `tools/extract_openra.py` (sprites from the owner's OpenRA content, allow-list `NEEDED`, aliases `flagfly`),
  `tools/extract_openra_sounds.py` (AUD decoder and the sound list), `tools/campaign/build_battlefield.py`
  (`defense_01`, `defense_02`, `village_01`).
- `src/scenes/`: `main_menu`, `missions`, `mission_setup`, `play`, `result`, `settings`, `calibration`, `developer`.
- `tools/content/`: `build.py`, `library.py`, `mission.py`, `synth.py`, `common.py`, `render_list.py`,
  `make_fixtures.py`, `test_content.py`. `tools/autoplay.gd` (harness), `tools/balance_missions.py`, `tools/shoot.gd`.
- Retired and removed: schema 2 packs, the loadout screen, `lane_view.gd`, the instrument catalogue, the campaign wave
  generators and `audio_preflight.py`. `docs/CAMPAIGN_PLAN.md` is kept with a superseded banner.

## Exports

Rebuilt on 31 October 2026 per `docs/EXPORT.md` (`build/` is git-ignored):
- `build/android/RhythmWarfare-debug.apk`: 95.8 MB (was 42.8 MB with three missions), debug-signed, arm64-v8a, all ten
  mission packs inside. Not installed on a phone by the agent.
- `build/windows/RhythmWarfare.exe`: re-exported 3 November 2026 with the village level, 232 MB (the 27 MB mission 1
  pack and the sounds); `[ DONE ] savepack`. Not smoke-tested that day: Windows Application Control blocked the fresh
  exe from the agent's shell, so the owner runs it. The 31 October smoke test was `RW_MISSION=10 RW_SCENE=play
  RW_AUTOPLAY=perfect RhythmWarfare.console.exe --headless` (mission 10 to the end with 16 streams, no errors).
- The Android APK was not rebuilt on 3 November (the owner declined on 2 November); it still holds the 48-bar mission 1.
- The APK grew because every offered combination of every mission is pre-assembled (67 MB of Ogg). If that is too
  large, trim the option pools of missions 7, 9 and 10 or lower the Ogg quality in `tools/content/common.py`.

## Known issues and backlog

1. Real stems for missions 2 to 10, the phone run and a human playtest (above). Retune waves after the owner has
   played; the numbers are a harness's, and outcomes from mission 5 on are seed-sensitive.
1a. Mission 1 on the owner's recordings: the 16 sound names and 8 clip names are provisional; the Sub Line's last note
   ends on the bar line where the next drum phase's first kick is cued (bars 25 and 41, same thumb: the build warns,
   the game credits a release up to 0.15 s early, mission 3 has the same shape); the bass sound row offers nine
   recordings, shown five or four at a time by bass line; the pads are two thumbs wide apart and the bass phases use
   pad 2 only, so a phone's feel is unknown; `content/REPORT.md` reports the loudest-options bound (-1.59 dBFS, a
   10 ms block envelope) while the exact worst case is -3.03 dBFS.
2. Wave units of one group can stack on one exact point while grinding a target (they separate when moving).
3. A wave jeep can loiter inside the base targeting the core without doing damage (seen once while tuning mission 7).
4. The autoplay report's `reached_s` equals the spawn time for left-entry waves (a report bug, not a game bug).
5. Headroom is checked for each mission's default selection only; louder combinations (for example Heavy Kick with
   Command Saw in missions 7 and 9) may clip slightly. Owner renders change this anyway.
6. The full build re-assembles every stem (about 9 minutes); a stem cache would make owner iterations faster.
7. Mission setup on very wide screens leaves the right half of the cards area empty (functional, not pretty).
8. Duel backlog items (idle fidgets, ruins, title art) still apply; the duel has no sound effects (the sound layer is
   wired in the mission play scene only).
9. Village level: the top choke point's flag sits under the translucent HUD bar; a unit behind a house can draw over
   it (civilians and houses are one layer under both armies); the "defenses" waves that hold a choke point count as
   uncleared when the player never retakes it (sloppy runs); the pack is 27 MB of Ogg (18 stems x 129 bars); the
   sounds `reinfor1`, `bleep11`, `cashturn` are extracted but unused; no positional panning.

## Everyday commands

```
bash tools/test.sh                                          # all headless tests + content build tests (about 1 min)
python tools/content/import_ableton.py content/imports/first_watch.json --check   # file an Ableton batch into the library (drop --check to write)
python tools/extract_openra.py --no-map                     # sprites from the owner's OpenRA content (allow-list NEEDED in the script)
python tools/extract_openra_sounds.py --check               # Red Alert sounds to assets/sfx (drop --check to write)
python tools/campaign/build_battlefield.py                  # regenerate the maps and battlefields (defense_02 and village_01)
RW_SECTION=none <godot> --headless --path . -s tools/autoplay.gd -- res://songs/m01_first_watch perfect 1.0 1   # harness without section taps
python tools/content/build.py                               # rebuild all ten packs (about 9 min); or name missions: level_05
python tools/content/render_list.py                         # rewrite docs/CONTENT_TO_RENDER.md
python tools/balance_missions.py > out.md                   # seeded trials (about 15 min with --jobs 8)
RW_MISSION=10 RW_SCENE=play RW_AUTOPLAY=perfect <godot> --path .    # scripted run in the real play screen, prints PERF
RW_MISSION=3 RW_SCENE=play RW_PRACTICE=1 <godot> --path .           # practice run (battlefield hidden)
RW_UNLOCK_ALL=1 <godot> --path .                            # every mission and option open for one run
RW_LEAD_IN=0.9 <godot> --path .                             # cue lead-in override
<godot> --headless --path . --export-debug "Android" build/android/RhythmWarfare-debug.apk     # docs/EXPORT.md
```

`<godot>` is `C:\Users\joesa\Downloads\Godot_v4.5.1-stable_win64.exe\Godot_v4.5.1-stable_win64_console.exe` on the
owner's machine. New `class_name` scripts need a `--import` before headless runs; `tools/test.sh` does that. In
Godot 4.5 `var x := dict["k"]` is a parse error: annotate the type. In this shell, long quoted Python in heredocs
fails when it contains apostrophes: write scripts to files.
