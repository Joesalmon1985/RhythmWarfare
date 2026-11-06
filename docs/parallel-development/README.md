# Parallel development: the planning documents

This folder holds the plan for the next piece of RhythmWarfare work: track scenes that are heard, a narrative graph with quests from every location, a
densely touchable world, and DJ-style transitions between scenes. It was first planned for two machines and, on 6 November 2026, moved to one Windows PC:
one lead session (Fable), with a music stream and a narrative stream run by subagents in separate git worktrees. No game code was written for these
documents. Everything marked "proposed" in them does not exist yet.

## Reading order

| # | File | Read it for |
|---|---|---|
| 1 | `ONE_PC_PLAN.md` | The plan: stages, work packages, gates, models, risks. Binding |
| 2 | `LEAD_RULINGS.md` | Rulings 1 to 19 of the lead. Binding and later than every other document |
| 3 | `ONE_PC_PROMPT.md` | The prompt that starts the lead session |
| 4 | `INTEGRATION_CONTRACT.md` and `contract/transition_port.gd` | The one interface between the two streams (version 1), as text and as code |
| 5 | `FILE_OWNERSHIP.md` | Who may edit which file, before and after milestone M1; the scope check |
| 6 | `CURRENT_ARCHITECTURE.md` | What exists today, checked against the code |
| 7 | `NARRATIVE_GRAPH.md` and `graph/` | The graph of locations and quests, route state, the ten validation rules |
| 8 | `INTERACTION_DESIGN.md` | Choices, reactive objects, coverage targets, the scene audit |
| 9 | `MUSIC_TRANSITIONS.md` | The transition modes, the planner, the transport, the spike |

`graph/` holds `graph_today.json` (today's route graph), `narrative.schema.md` (format `rhythm_warfare.narrative.v1`), `overlay_proposed.json`,
`narrative_graph_target.json` and `validation_report.md` (the ten rules checked on paper).

## State of each document (6 November 2026)

All were reviewed on 6 November 2026 by a reviewer who had not written them: against the owner's brief, `LEAD_RULINGS.md`, each other and the code.

| Document | State | What remains open |
|---|---|---|
| `ONE_PC_PLAN.md` | Written by the lead. Reviewed: only the entrance count (N2.4, X5) changed to 20, by ruling 15 | Its M2.3 and M2.6 still say "within 3%" and "blend, half-time and echo-out"; rulings 5 and 6 are later and say 50 cents and "blend, echo-out and cut" |
| `LEAD_RULINGS.md`, `ONE_PC_PROMPT.md` | Read, not changed | |
| `INTEGRATION_CONTRACT.md`, `contract/` | Re-worded for one PC. A dated section "Clarifications (6 November 2026)" adds rulings 9 to 14; it narrows version 1 and changes no rule. `contract/` untouched | The Bassment return and the wizard entrance are outside the port until a later piece |
| `FILE_OWNERSHIP.md` | Re-worded. Staging brought into line with the plan: the music stream owns `run_hotspots.gd` and `run_journey.gd` for M1 only; `check_scope.sh` uses `SIDE=music\|narrative` | None known |
| `CURRENT_ARCHITECTURE.md` | Re-worded; facts re-checked (line counts, 44.5 and 48, `ward` `max_hotspots` 5, 88 test files, catalogue `imported` 44). 922 lines against a target of 800: the rest would cost facts | The coverage figures are a model until `tools/run/coverage_audit.gd` (N1.5) measures |
| `NARRATIVE_GRAPH.md`, `graph/` | Corrected for ruling 15: 20 new entrances, a cellar hatch on the Floor, the wizard an extra way in. Overlay, target graph and paper report regenerated | Starting the Bassment from a port request is unsolved (spike at N2.2); the 17 extra entrances use a rotating quest |
| `INTERACTION_DESIGN.md` | Corrected for rulings 1, 15, 16: 20 entrances, 163 choice objects, hubs up to 10 | Per-scene figures are the model; 14 assumptions (A1 to A14) use their defaults |
| `MUSIC_TRANSITIONS.md` | Corrected for rulings 6, 12, 14: listening pairs are a blend, an echo-out and a cut | The one-day spike (M2.1) answers nine questions; nothing is measured on a real driver |

## The owner's decisions of 6 November 2026

From `ONE_PC_PLAN.md` section 2: the master plan is written first, and the three design documents are the first stage of the work; one lead session with the two
streams as subagents on `wip/` branches, the music stream owning the run files until track wiring is done and the narrative stream after, and Godot runs queued one at
a time; the import of the 61 recordings is finished on this PC on the RTX 3060; the plan lives on `feature/one-pc-plan`, and `main` is not touched until the suite is
green and the owner says so.

From section 9, the owner approved every default:

| # | Decision | Answer |
|---|---|---|
| 1 | Move the packs, recordings and planning inputs out of the checkout to `C:\Users\joesa\rw-audio-work\` | Yes |
| 2 | Objects that react to a tap but lead nowhere count toward the 50% | Yes |
| 3 | One run reaching all five locations; an ending | Keep today's routes, add hub-to-hub links between the paired locations, no ending yet |
| 4 | Public names of the Catch-22 and LOTR quests | Keep the original names |
| 5 | The wizard's mid-scene entrance to the Bassment | Stays as it is for now |
| 6 | Scene lengths and the every-fourth-bar rest | Decided by ear after M1 |
| 7 | Commit the planning inputs to the public repository | No; the documents restate what they need |

## For the owner to confirm

These are working defaults chosen by the lead or the documents, not yet the owner's words.

1. **An ungated Dungeon entrance in every hub, the Floor included** (ruling 15). The Floor gets a cellar hatch through the port; the wizard stays as an extra, rhythm-gated way in. This makes 20 new entrances, not 16 or 19.
2. **The seven extra path routes** (ruling 17): five `restart` routes from the quest endings and two second routes (`gospel/jordan` to `jordan.nazareth`, `ember/hollow` to `hollow.inn`). They were invented only to give three choices in every path scene.
3. **The second test route in the walkable order** (ruling 18). Your example order (Mental Hospital before Alien Spaceship) cannot be walked because the mainline is one-way; it is tested as Alien Spaceship, LOTR, Alien Spaceship, Mental Hospital, Catch-22, Mental Hospital.
4. **The smallest touch target, 88 px** (ruling 3). It is 48 dp only up to 440 dpi. Whether to raise it to 96 px is decided after the phone test (X4).
5. **Hubs may hold up to 10 objects** (ruling 16); the cap of 8 counts choices only (ruling 1).
6. **The 41 Bassment passages with fewer than three choices** stay a declared exception for a later piece (ruling 19). Whether the Bassment saves its items and passage (`NARRATIVE_GRAPH.md` 8.2, item 6).
7. **The 17 extra quest entrances on non-hub scenes** use a rotating choice of quest, so that those scenes reach three choices (`NARRATIVE_GRAPH.md` 8.2, item 4).
8. **The mainline stays one-way** (`NARRATIVE_GRAPH.md` 8.2, item 2): no route back to the Warehouse, and none from the Hospital Ward and Mental Hospital pair back to the Alien Spaceship and Hell pair. With the new pair links one run can visit all five locations.
9. **Interaction assumptions A1 to A14** (`INTERACTION_DESIGN.md` 11.2), for example that tapping the selected object again keeps it selected.
10. **Licences.** The owner stated on 6 November 2026 that they hold the rights to include the 61 tracks, so the Android build carries them (ruling 24); the audio still stays out of Git. The Jesus quest, and the Catch-22 and LOTR shapes, need someone qualified before any release (`ONE_PC_PLAN.md` section 9).

## Not done by these documents

The Godot suite, the walkers and the phone were not run for them. Nothing here was heard or played. `ONE_PC_PLAN.md` section 8 says where the owner plays and listens.
