# Draft PR: `feature/doom-layout-worlds` → `feature/one-pc` (kept separate; do not merge without the owner)

**Open it:** https://github.com/Joesalmon1985/RhythmWarfare/compare/feature/one-pc...feature/doom-layout-worlds (tick "Create as draft"). The GitHub CLI is not installed on the owner's machine, so the lead could not open it; paste this body.

## What this branch is
Eight one-scene worlds laid out on Doom II map geometry, each built from one of the owner's paintings: the Floor (`doom_warehouse`), Copper Bar (`doom_bar`), Chill-out Lounge (`doom_lounge`), DJ Booth (`doom_booth`), Loading Dock (`doom_dock`), Balcony (`doom_balcony`), Mothership (`doom_mothership`), Underworld (`doom_underworld`). One 2.5D world and one HUD (ruling 38); a stationary choice moment in each, the guide's tap is the decision and the player walks the authored leg to the threshold (rulings 35, 39); the walk-out paced at no more than 3 m/s with the world swap waiting for the doorway hold when the leg outlasts the phase boundary (rulings 42, 42b); the rail check measures the worst case from every rail place (ruling 43). Per-world music is mapped by title in `docs/doom/MUSIC.md`. Engine contracts merged from `feature/shared-contracts` e6a0383e. HEAD: see the "Where things are" table in `docs/HANDOVER.md` on `feature/one-pc`.

## How to play (PowerShell, from the `MusicGame-env` worktree)
```
& "C:\Users\joesa\Documents\Cursor\MusicGame-env\tools\dev\play_doom_worlds.cmd"
& "C:\Users\joesa\Documents\Cursor\MusicGame-env\tools\dev\play_doom_worlds.cmd" --scene doom_bar
```
Each world: a stay loop at the reference viewpoint (the near reveal, the choice place with a hold, the other reveal, the choice place again), three guides at the thresholds; tap a guide and the player walks her leg while the track plays out, the frame shuts to the doorway, the next world is shown on the boundary (or at the hold's end on a whole beat, by beat 32 of the next phase, when the leg is long). `docs/doom/LAUNCH.md` has the per-world notes, the verdicts and the carried items.

## Verified (headless, 9 November, logs `rw-audio-work/leadlogs/env_pola_*.log`)
All filters 0 failures, 0 SCRIPT ERROR: doom (views: exposure p50 0.25–0.38, contrast ≥ 0.40, guide sizes, first-window-at-the-reference tests), doom_cuts 46 (the Warehouse → Bar → Floor cut under the paced contract), choice_pitch 28, split_void 22, rail_paths 652, test_geography 299, heralds 430, camera 48, transition 17579, track 3164, weather 201, blackjack, run_, playtest, story. Rail check: 8 scenes, 0 problems, 0 walk-off warnings; the longest walk-outs are the Warehouse up leg (31.5 m, 8 bars from `wh_ref_back`) and the Lounge up leg (28.6 m, 7 bars). The counts for the final head are in RUN_LOG and HANDOVER. Two music cuts were driven headless and logged (`leadlogs/music_cut.log`).

## NOT verified
- Nothing played by a human on a screen or a phone; the phone build was never run on this branch.
- Of the 24 world-to-world cuts only the 8 in `test_doom_cuts` and the two logged music cuts have been checked at all; 16 of 24 were never looked at by eye.
- Music is mapped to worlds by title, not by listening; the owner should audition and swap (one line in `content/run/track_scenes.json` plus the MUSIC.md row).
- The lead's verdicts (ruling 36) are from contact sheets, not play.

## Reviewers' lists, verdicts and carried items (disclosed in full)
Independent reviewers (Opus) looked at every world against its painting; their lists and the lead's verdicts are in `docs/doom/LAUNCH.md` and the per-scene docs under `docs/doom/`. Summary:
- **Floor / Warehouse:** 23 of 23 shots in the exposure rule. Reads as a big club hall with the warm bar corner, the red lounge wall, the crowd and the lit rig. Carried: the room is still a vast blue hall (void floor under the lamps in the reveals; the far walls were not moved, a MAP07 re-trace is needed), the stage guide is 64 px at 16 m, the crowd sprites repeat.
- **Copper Bar:** 24 of 27. The closest to its painting (warm stone, pendants, bottle shelf, the booth window with its figure, the arched blue passage). Carried: hold_bridge and walk_ahead_1/3 at contrast 0.38–0.40, the blue passage reads flat, water gloss faint.
- **Chill-out Lounge:** 17 of 21. The sofa ring, rug and table under the pitched hold (pitch −12), coffers, the cobalt glass wall. Carried: coffers a flat tile, the glass passage a blue panel, no vault, the Dock street grey behind its guide; approach_floor dark on purpose.
- **DJ Booth:** 2 of 8 in the exposure rule (flat mid-tone tiles); needs an art pass. The Booth guide seen from the Bar is now a painting crop (71 px).
- **Loading Dock, Balcony, Mothership, Underworld:** 8 of 8 each; items ticked or carried in their scene docs.
- **Placeholders, named as such:** the crowd sprites (repeating), the Booth's tiles, the Warehouse stage guide at 64 px, the per-void "glow, no haze" engine hook (not built; the voids are split by colour only). All sprites that are not crops of a painting are placeholders by ruling 36.
- Rulings 42, 42b and 43 are the lead's and open to the owner's overrule (`docs/parallel-development/LEAD_RULINGS.md`).

## Not in this PR
`feature/bedsit-raves` (the bedsit opening and the four raves) is a separate branch and PR by plan. `main` is untouched: it moves only on the owner's word after they play `feature/one-pc`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
