# Prompt for the next agent (paste everything below the line into a new session)

Intended for a Claude Sonnet 5.5 session at medium effort, started in `C:\Users\joesa\Documents\Cursor\MusicGame`.

---

You are continuing Rhythm Warfare, a Godot 4.5.1 mobile rhythm game in this folder (`main` branch of
https://github.com/Joesalmon1985/RhythmWarfare). Your job is to implement the three-level defense campaign that
the owner has designed, on the `main` branch, in reviewable stages, keeping the game playable and the tests green
at every commit.

## Read first, in this order

1. `docs/HANDOVER.md`: what exists today (two-sided duel, four stems, OpenRA simulation, 425 headless checks).
2. `docs/CAMPAIGN_PLAN.md`: the plan you are executing. It maps the owner's requirements onto the code file by
   file, lists the design calls already made, the stage order, the tests to write and the environment facts.
   Follow it; where you must diverge, say so in the commit message and in the handover.
3. `campaign/Claude_Defense_Campaign_Prompt.md`: the owner's requirements (survival win, no enemy base, three
   defense points with round-robin group assignment, instrument profiles with recipes, four unlabelled buttons,
   2/2/3 loadout caps, per-slot stems, authoring pipeline, acceptance list). These are the rules of the game.
4. `campaign/Rhythm_Game_Research_and_Refinements.md`, `campaign/Defense_Campaign_Design_and_Workflow.md`,
   `campaign/Plan/*.json`, then `campaign/First_Three/level_01/` (song.json, chart_rules.json, player_chart.json,
   waves.proposed.json, Music/*.mid).
5. `docs/PRD.md` sections 4, 8 and 9 (judgement, music behaviour, pack contract), `docs/TIMING.md`.

Do not re-ask settled decisions listed in `docs/HANDOVER.md` or in the plan's section 6 defaults. Where the owner's
campaign prompt and the old PRD disagree, the campaign prompt wins.

## Working rules

- Work on `main`. Commit at the end of every stage in `docs/CAMPAIGN_PLAN.md` section 4 with `bash tools/test.sh`
  green, then `git push origin main`. Commit messages say what changed and any divergence from the plan. End every
  commit message with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Keep the existing duel packs (`songs/level_01`, `songs/test_16`) and their tests working as a legacy mode behind
  `schema_version` 1. Do not delete the duel path.
- Never edit the MIDI files under `campaign/First_Three/*/Music/`. Their SHA-256 values are in
  `campaign/Musical_Source_Integrity.json`; the importer must verify them.
- Placeholder audio is fine and must be labelled as such in the pack manifest and the loadout screen. Real stems
  come from the owner later, one file per slot and profile.
- No one-miss failure, no direct core damage for a miss, no tighter timing windows, no random button remapping,
  no silent note moving or hold shortening. Chart problems are build errors for the author to fix.
- Godot: `tools/test.sh` runs the headless tests and refreshes the class cache. The console binary is
  `C:\Users\joesa\Downloads\Godot_v4.5.1-stable_win64.exe\Godot_v4.5.1-stable_win64_console.exe`. New
  `class_name` scripts need the `--import` pass that `test.sh` does. Annotate types on `var x := dict["k"]`.
  Write Python scripts to files rather than long quoted heredocs in Bash.
- Python 3.14 with numpy and ffmpeg is available. Install `mido==1.3.3` once (`pip install mido==1.3.3`). Run
  project scripts as `python tools/campaign/<script>.py`, not from inside `campaign/`.
- `DuelMasterBattle` under `Documents\Cursor\DuelMaster` is an asset source only. Never edit or build it.
- Report outcomes honestly: which checks ran, which passed, which you could not run (the phone run is the owner's).

## Stages and done criteria (details in `docs/CAMPAIGN_PLAN.md` section 4)

0. **Tooling and contract.** Move the three reference scripts to `tools/campaign/`, fix the validator's root path,
   rerun it from the repo and confirm the 102 pack checks pass. Write the schema 2 pack contract into
   `docs/PRD.md` (new section 14) and `songs/README.md` before coding.
1. **Rhythm feel.** `tools/campaign/build_defense_pack.py` compiles every chart from the part MIDIs and rules
   (its note lists must equal the pack's `player_chart.json` files exactly: 64 / 96 / 89, practice 80),
   synthesises placeholder stems per part, writes schema 2 `level.json` with hashes and a render manifest.
   Loader v2 (notes carry `button`, `slot_id`, `part_id`, `source_note_id`, `family`; sections carry
   `mode`; stems keyed by slot plus `other`; several charts per pack), judge keyed by `slot_id`, generic N-stream
   transport, `Session.lookahead_s` (default 2.2 s), a DRUMS / BASS cue one bar ahead, practice mode with the
   battlefield hidden (`RW_BATTLE=off`, `RW_CHART=<chart id>`). Done when all three packs play on Windows with
   aligned stems, level 2 practice and campaign charts play over identical audio under separate chart ids, and
   level 3's bass holds run across all four buttons at full length.
2. **Defense battle.** `data/battlefields/defense_01.json` (one base, `command_core` objective, three defense points
   in an arc in front of the wall opening, three entries placed by travel time, walls plus two pillboxes only),
   waves scheduled by time and spawned without producers, `src/sim/defense_ai.gd` (groups hold their point with a
   leash; wave units attack-move via their point to the objective), outcome rules (objective dead -> defeat at
   once; `duration_ticks` reached with every objective alive -> victory; same tick -> defeat), HUD with objective
   health and wave warning, `tools/autoplay.gd` and `tools/balance.sh` extended. Done when level 1 is playable
   end to end, no input loses, perfect play survives, and the harness prints objective health and wave outcomes.
3. **Instruments and production.** `data/instruments/catalogue.json` from the pack's catalogue (validated actors,
   producer tags agreeing with `build_at` in `data/openra_rules.json`), per-slot deterministic recipe counters,
   round-robin group assignment with group ids in the production log, per-slot producer gating and muting with
   gain restored in place, unavailable notes inert and excluded from accuracy. Done when a kick profile produces
   infantry and another alternates vehicles regardless of button, and the same bass slot produces its group on
   each of buttons 1-4.
4. **Campaign and loadout.** `data/campaign/campaign.json`, `src/core/campaign.gd` (atomic `user://campaign.json`,
   clears, unlocks, per-level loadouts, corrupt-file recovery), campaign level list, loadout screen (slot rows,
   locked profiles with their unlock level, unit mix text, validation of families, distinct profiles, required
   slots and 2/2/3 caps, missing-render handling), result screen with clears and unlocks, Play and Practice.
   Done when a first clear unlocks the next level and its profiles, replays never reset, practice writes nothing.
5. **Levels 2 and 3, balance, evidence.** Tune waves and recipes per level with the harness over seeds 1-3
   (perfect and 0.85 survive, no input fails, report 0.6 honestly); tables in `docs/BALANCE.md`; Windows and
   Android exports per `docs/EXPORT.md`; the desktop `PERF` line; exact phone instructions for the owner; rewrite
   `docs/HANDOVER.md`, update `README.md` and `songs/README.md`.

Write the tests listed in `docs/CAMPAIGN_PLAN.md` section 5 as you go, in the stage that introduces each behaviour.

## Things already found that you should not rediscover

- Wave entries at the map edge do not work: riflemen move about 1.3 cells per second and jeeps about 4, so the
  pack's late waves would never arrive before a 44 to 66 second song ends. Place entries 14-16 cells from the wall
  opening (or crop the map) and print travel times in the build output.
- The fortified duel base would beat the pack's waves with no player input. Level 1 starts with walls and two
  pillboxes only; later levels add defenses through battlefield variants.
- `AudioStreamSynchronized` takes up to 32 streams; the levels need 3, 4 and 5. Measure, do not assume, the
  decoding cost of five to eight Ogg streams on desktop and report it; the phone number is the owner's run.
- The stems carry a one-bar tail after `duration_ticks`. Survival resolves at `duration_ticks`, not at audio end;
  `play.gd`'s `_on_song_finished` becomes a fallback only.
- Same-thumb hold-plus-tap is a loader error; the 960 / 480 tick gaps are warnings (design targets, untested on a
  phone).
- `campaign/.gdignore` keeps Godot from importing the pack's CSV files. Keep it.

## When you finish

Leave `main` pushed with: the three playable levels with placeholder audio, the practice chart for level 2, the
campaign flow, the balance tables, the exports, updated docs and a rewritten `docs/HANDOVER.md` that states what
was verified, what was not (phone run, real stems), and every divergence from `docs/CAMPAIGN_PLAN.md`.
