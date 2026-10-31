# Rhythm Warfare: handover

State on 31 October 2026, after `docs/BRIEF_PADS_SEQUENCES_TEN_MISSIONS.md` (four pads, sequence rewards, ten missions,
the loop library and the owner's drop-in content path). Read this first, then `README.md` (layout and commands),
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
  prepared sockets (`data/battlefields/defense_02.json`, five per approach flanking each route outside the wall,
  `sockets_per_point` open per mission), approach with the fewest defenses first (ties: the approach most enemies are
  walking towards, else the next wave's). Units (e1 to e4, jeep, APC with its gun only, light and medium tank,
  artillery, flak truck) come out of the barracks or war factory and hold the point with the fewest defenders (at
  most 6 each); they may sortie up to 16 cells to hit an enemy shelling their point from beyond their 6-cell leash.
  At capacity a reward becomes a repair crew for the most damaged approach or, with nothing damaged, +50% health
  once for the oldest defense; the HUD says which.
- **Waves** are authored by bar per mission (`data/campaign/waves/level_NN.json`), never depend on accuracy, walk on
  from off screen at the left, top and right, attack-move via their approach's defense point to their objective and
  fight units **and defensive structures** on the way (not other buildings). Required objectives: the command core,
  plus the power plant (6, 10) or radar dome (8, 10). Survive to the end of the song to win; lose a required objective
  and the run ends.
- **Progression.** Clearing mission n unlocks mission n+1 and the options listed in its `new_options`
  (`data/campaign/campaign.json`); a mission's own defaults are always available; no accuracy threshold blocks the
  ladder. The old save (`user://campaign.json` v1) migrates to v2 on load (clears and bests kept); settings v1 keep
  calibration and the last pack, and the cue lead-in starts at its default (the old note-approach time measured
  something else).

## The ten missions (owner's view; the menus show names and locks only)

| # | Mission | Length | Phases (D drums, B bass) | New for the player | Enemies (first appearances) | Objectives |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | First Watch | 32 bars, 44 s | DDDD | kick pad 1 and snare pad 4; pillboxes; kick sound choice | e1, jeep | core |
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
  snare parts, bass lines, accompaniment), one MIDI per part, a `clip.json`. Missions 1 to 3 use clips **cut from the
  First_Three MIDI** (two-bar grooves, eight-bar bass phrases) and one long accompaniment clip per song; the source MIDI
  is never edited and its hashes are checked on every build. Missions 4 to 10 use generated clips (14 new ones).
- `content/sounds.json`: the 14 sounds (kick, snare and bass voices, ensemble) with friendly names.
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
  option once a mission lists it. Exact file list: `docs/CONTENT_TO_RENDER.md` (23 clips, 84 WAVs), rewritten by
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

**Not verified:** any phone run (touch feel, the two-thumb layout, frame time and memory with 16 Ogg streams on a
phone CPU, load time of mission 10), any listening check by ear (the build checks sample positions and headroom only;
placeholder music is generated and meant only to be readable), any human playtest of the cues, sequences or difficulty
(the beginner and sloppy policies are models), real owner renders (none exist yet), the screens on a real phone's
safe areas and DPI.

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

## How the code is organised

- `src/core/`: `mission_loader.gd` (schema 3: selection, stems, cues, sequences), `mission_rules.gd` (rules.json),
  `sequence_tracker.gd`, `match.gd` (mission flow: judge -> sequences -> rewards in the tick loop; and the duel flow),
  `campaign.gd` (ladder, unlocks, save v2 and the v1 migration), `session.gd` (settings v2, `start_mission`, env
  overrides), `level.gd`, `level_loader.gd` (schema 1 duel and dispatch; schema 2 is refused as retired), `song_clock.gd`.
- `src/input/pad_judge.gd` (missions), `judge.gd` (duel), `lane_input.gd` (touches and keys D F J K).
- `src/sim/battle_sim.gd` (deterministic 25 Hz OpenRA simulation; mission sockets, rewards, capacity, walls, prebuilt
  defenses), `defense_ai.gd` (defenders hold and sortie, waves walk via their point), `bot_ai.gd` (duel only).
- `src/ui/`: `pad_view.gd`, `battle_view.gd`, `hud.gd`, `ui_style.gd`, `settings_panel.gd`, `sprite_bank.gd`.
- `src/scenes/`: `main_menu`, `missions`, `mission_setup`, `play`, `result`, `settings`, `calibration`, `developer`.
- `tools/content/`: `build.py`, `library.py`, `mission.py`, `synth.py`, `common.py`, `render_list.py`,
  `make_fixtures.py`, `test_content.py`. `tools/autoplay.gd` (harness), `tools/balance_missions.py`, `tools/shoot.gd`.
- Retired and removed: schema 2 packs, the loadout screen, `lane_view.gd`, the instrument catalogue, the campaign wave
  generators and `audio_preflight.py`. `docs/CAMPAIGN_PLAN.md` is kept with a superseded banner.

## Exports

Rebuilt on 31 October 2026 per `docs/EXPORT.md` (`build/` is git-ignored):
- `build/android/RhythmWarfare-debug.apk`: 95.8 MB (was 42.8 MB with three missions), debug-signed, arm64-v8a, all ten
  mission packs inside. Not installed on a phone by the agent.
- `build/windows/RhythmWarfare.exe`: 202 MB with the pack embedded. Smoke test: `RW_MISSION=10 RW_SCENE=play
  RW_AUTOPLAY=perfect RhythmWarfare.console.exe --headless` plays mission 10 to the end with 16 streams, no errors.
- The APK grew because every offered combination of every mission is pre-assembled (67 MB of Ogg). If that is too
  large, trim the option pools of missions 7, 9 and 10 or lower the Ogg quality in `tools/content/common.py`.

## Known issues and backlog

1. Real stems, the phone run and a human playtest (above). Retune waves after the owner has played; the numbers are a
   harness's, and outcomes from mission 5 on are seed-sensitive.
2. Wave units of one group can stack on one exact point while grinding a target (they separate when moving).
3. A wave jeep can loiter inside the base targeting the core without doing damage (seen once while tuning mission 7).
4. The autoplay report's `reached_s` equals the spawn time for left-entry waves (a report bug, not a game bug).
5. Headroom is checked for each mission's default selection only; louder combinations (for example Heavy Kick with
   Command Saw in missions 7 and 9) may clip slightly. Owner renders change this anyway.
6. The full build re-assembles every stem (about 9 minutes); a stem cache would make owner iterations faster.
7. Mission setup on very wide screens leaves the right half of the cards area empty (functional, not pretty).
8. Duel backlog items (idle fidgets, ruins, sound effects, title art) still apply.

## Everyday commands

```
bash tools/test.sh                                          # all headless tests + content build tests (about 1 min)
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
