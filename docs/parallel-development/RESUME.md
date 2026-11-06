# Where the planning run stopped (6 November 2026)

The planning run for the two-machine plan was interrupted when the laptop restarted at about 07:53. This
file says what exists, what is missing and how to carry on from another machine. It is a status note, not
one of the planned documents; delete it when the plan is complete.

This branch (`feature/parallel-development-plan`) was cut from `main` at `86950290`. Nothing here has been
reviewed, and nothing has been merged into `main`.

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
| `README.md` | Not started. It must list the open decisions for the owner. |

The intended order was: the three unwritten design documents, then the two implementation plans, the merge
and test plan, the two worker prompts and the README, then an independent review of everything against the
owner's brief, then commit and push to `main` as the shared baseline.

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

## Material that is not in this branch

The planning run's inputs were kept outside Git on the laptop, in `/home/joe/rw-audio-work/planning/`:
the five investigation reports (`A_music_architecture.md`, `B_narrative_inventory.md`,
`B_graph_today.json`, `C_interaction_visuals.md`, `D_architecture.md`, `E_testing_git.md`), the lead's
binding decisions (`DECISIONS.md`) and the half-built scripts of the interrupted agents (`scratch/`). The
owner's planning brief exists only in the laptop's Claude Code session history. The three unwritten design
documents cannot be finished to the same design without `DECISIONS.md` and the brief; they have to be
copied to the other machine by hand or added to this branch by the owner's decision.

## The other work in flight at the same time

- **Track scenes** (`feature/track-scenes`, pushed at `c1105593`): the engine half is done and
  `docs/TRACK_SCENES_HANDOVER.md` on that branch is the hand-over for the audio and wiring half. The full
  test suite was running on `2a32005e` when the laptop restarted and had reached about 35 of 87 test files
  with no failure reported, so the branch is not verified and was not merged into `main`.
- **Importer fixes** (`wip/importer-fixes`, pushed at `fbb048d9`): one commit that fixes negative bass note
  times, a refused folded backing and a false stem-alignment alarm, with tests. Not merged.
- **The import of the 61 recordings** (audio, never in Git; packs in `/home/joe/rw-audio-work/packs` on the
  laptop): 38 imported cleanly, 7 failed, track 46 of 61 was being separated at the restart, and 15 had
  not been started. The re-import of the 7 failures with the fixed importer had finished one track
  (`bad_company_uk_trace_nitrous_audio_remix`) and was part-way through a second
  (`su3_ject_crystal_eyes`, left without a `track.json`). The other five are `exile_destructive_vibrations`,
  `particle_pyro`, `moving_fusion_makosa`, `mantra_decibella_tim_reaper_stars_are_calling` and
  `paralel_in_the_clouds`; their packs on disk are the ones that failed validation. The batch script
  (`run_batch.sh` in `/home/joe/rw-audio-work/overnight/`) skips finished packs when started again.
- The track catalogue on `main` covers the first 44 recordings only.
