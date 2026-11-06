# Start here: picking up the laptop's work (6 November 2026)

The laptop restarted at about 07:53 on 6 November 2026 and stopped three pieces of work part-way through.
This file says what exists, what is missing and what to do next on another machine. It is a status note,
not one of the planned documents; delete it when the work it describes is finished.

## This branch

`feature/laptop-handover-2026-11-06` is `main` at `86950290` with three branches merged into it. Nothing
on it has been merged into `main`.

| Merged branch | Commit | What it holds | Verified? |
|---|---|---|---|
| `feature/track-scenes` | `c1105593` | The engine half of track scenes, a track assigned to every scene, `docs/TRACK_SCENES_HANDOVER.md` | No. The full suite was about 35 of 87 test files in, with no failure reported, when the laptop restarted. |
| `wip/importer-fixes` | `fbb048d9` | Importer fixes for the seven recordings that failed | The importer's 41 unit tests pass on this branch. The re-import of the seven was not finished. |
| `feature/parallel-development-plan` | `3b39b85a` | Four of the twelve planning documents, in this folder | Not reviewed. |

The merges had no conflicts. The Godot test suite has not been run on the merged result.

## Material copied by hand, not in Git

The repository is public, so audio and the planning inputs travel outside it. The owner has copied three
folders to the new machine; ask the owner where they are, because the documents and briefs refer to them
by their laptop paths.

| Laptop path | What it is |
|---|---|
| `/home/joe/rw-audio-work/planning/` | The planning inputs. Its `READ_ME_FIRST.md` lists them: the owner's brief (`OWNER_BRIEF.md`), the lead's binding decisions (`DECISIONS.md`), five investigation reports, the brief given to each agent, and the laptop session's memory notes (`claude_memory/`), which record the owner's decisions and working preferences. |
| `/home/joe/rw-audio-work/packs/` | The imported track packs (stems, charts, previews). 46 complete packs; see the import section below for the ones not to trust. |
| `/home/joe/Projects/MusicGame/ToAddTry4/` | The 61 source recordings, needed to finish the import. Never commit these or the packs. |

## What to do next, in order

1. **Run the full Godot suite on this branch** (`tests/run_tests.gd`, headless). Track scenes is not
   verified until it passes. The owner's rule is that track scenes goes to `main` only when the full suite
   and the automated playthroughs are green.
2. **Finish the import.** `tools/audio_import/README.md` describes the tool; it needs Python with Demucs
   and was only run on Linux. Then bring the track catalogue up to date (it covers 44 recordings).
3. **Finish the planning documents** (table below), have them reviewed against `OWNER_BRIEF.md`, and ask
   the owner before anything goes to `main`.
4. **The audio and wiring half of track scenes**, from `docs/TRACK_SCENES_HANDOVER.md`.

The plan was written for two machines working at once (a Windows PC on music, the Ubuntu laptop on
narrative and interaction). The owner has since moved the work to one more powerful machine; ask the owner
whether the two-machine split still stands before writing the implementation plans and worker prompts.

## The import of the 61 recordings

State when the laptop restarted:

- 38 imported cleanly.
- 7 failed: `bad_company_uk_trace_nitrous_audio_remix`, `exile_destructive_vibrations`, `particle_pyro`,
  `su3_ject_crystal_eyes`, `moving_fusion_makosa`, `mantra_decibella_tim_reaper_stars_are_calling`,
  `paralel_in_the_clouds`. The re-import with the fixed importer had finished the first of these and was
  part-way through `su3_ject_crystal_eyes`, whose pack has no `track.json` and must be re-imported. The
  packs of the other five are the ones that failed validation. Re-import all seven with the importer on
  this branch.
- Track 46 of 61 (`InsideInfo - Victory Over Death`) was being separated and has no pack.
- 15 recordings had not been started.

The import skips recordings whose pack is already finished (`--skip-imported`), so it can be run over the
whole source folder again.

## The twelve planned documents

| Document | State |
|---|---|
| `INTEGRATION_CONTRACT.md` and `contract/transition_port.gd` (+ `.uid`) | Written by the lead session. Not reviewed. |
| `FILE_OWNERSHIP.md` | Written. Not reviewed. |
| `CURRENT_ARCHITECTURE.md` | Written (1052 lines, over the 800-line target). Not reviewed. |
| `NARRATIVE_GRAPH.md`, `graph/graph_today.json`, `graph/narrative.schema.md` | Not written. The agent was still computing route costs. |
| `INTERACTION_DESIGN.md` | Not written. The agent was still building the scene audit tables. |
| `MUSIC_TRANSITIONS.md` | Not written. The agent was still reading the track packs. |
| `WINDOWS_IMPLEMENTATION_PLAN.md` | Not started. |
| `UBUNTU_IMPLEMENTATION_PLAN.md` | Not started. |
| `MERGE_AND_TEST_PLAN.md` | Not started. |
| `WINDOWS_CLAUDE_PROMPT.md` | Not started. |
| `UBUNTU_CLAUDE_PROMPT.md` | Not started. |
| `README.md` | Not started. It must list the open decisions for the owner (section D7 of `DECISIONS.md`). |

The briefs for the three unwritten design documents are in the planning folder under `agent_briefs/` and
can be reissued once their paths are corrected for the new machine. The intended order after those three
was: the two implementation plans, the merge and test plan, the two worker prompts and the README, then
an independent review of everything against the owner's brief.

## Points raised by the finished agents and not yet acted on

From the agent that wrote `FILE_OWNERSHIP.md`, overlaps that remain after the first Windows milestone and
that the implementation plans must cover:

- Windows needs further hooks in `run_play.gd` and `run_engine.gd`.
- The music tuning keys in `run.json` sit in a file owned by Ubuntu.
- `content/paths/*/music.json` sits in a folder owned by Ubuntu.
- The baseline of `test_run_tracks_safety` against Ubuntu's routing changes.
- Door timing in `run_journey.gd` against the length of the blend.
- `transition_port.gd.uid`: both branches copy the fixed file from `contract/` (this was dealt with in
  `INTEGRATION_CONTRACT.md`).

From the agent that wrote `CURRENT_ARCHITECTURE.md`, places where the investigation reports disagreed with
the code. The document follows the code in each case:

- The choice window opens at beat 44.5 and its event is stamped 48; some reports and docs say 48 or 49.
- `max_hotspots` is used: node `ward` sets 5 (`run.json:3068`).
- There are 87 `test_*.gd` files, not 178.
- `export_presets.cfg` enables the network and wifi-state Android permissions.
- Reaching the Jesus and LOTR quests today costs 6 choices only with the Bassment back key; without it, 25.
- The integers that matter for a tempo change are in `clock_rate`, `frames_per_beat` and `silent_loop`,
  not in `_swap_clock`.
- `content/music/tracks/catalogue.json` still says `imported: 2`.
