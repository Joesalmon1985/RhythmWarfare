# Draft PR: `feature/bedsit-raves` → `feature/one-pc` (kept separate; do not merge without the owner)

**Open it:** https://github.com/Joesalmon1985/RhythmWarfare/compare/feature/one-pc...feature/bedsit-raves (tick "Create as draft"). The GitHub CLI is not installed on the owner's machine, so the lead could not open it; paste this body.

## What this branch is
The run's opening before the Warehouse: the player's bedsit (one room, four facings), four raves behind its thresholds (Space, Magic and unicorns, Dinosaurs, Transport), each with three activities (fix the bass knob, the cloakroom, the bar), a street race per rave, the card table, and the way out to the Warehouse once ANY ONE rave's three activities are done (ruling 41). Head `b815ab45` (9 November 2026); 106 commits over `feature/one-pc`; engine contracts merged from `feature/shared-contracts` e6a0383e (hold pitch, walk pace 42/42b, observe-once, rail check worst case 43, the herald-look fix at a claimed frame).

## How to play (PowerShell, from the `MusicGame-play` worktree)
```
& "C:\Users\joesa\Documents\Cursor\MusicGame-play\tools\dev\play_bedsit.cmd"
& "C:\Users\joesa\Documents\Cursor\MusicGame-play\tools\dev\play_bedsit.cmd" --rave space
& "C:\Users\joesa\Documents\Cursor\MusicGame-play\tools\dev\play_bedsit.cmd" --race magic
```
Tap the left or right fifth of the screen to turn, the top to go through the facing's threshold, the bottom to stay. Shortest path to the Warehouse: face north, top → Space, do the knob, the cloakroom and the bar, take the hatch home, tap left (now facing west), tap the middle of the door. `docs/bedsit/LAUNCH.md` "Playing it" has the full tap-by-tap path.

## Verified (headless, 9 November, logs `rw-audio-work/leadlogs/play_c2_*.log`)
All 23 filters 0 failures, 0 SCRIPT ERROR: blackjack 10622, bedsit 425 (incl. `test_bedsit_play` 177: turns, picks, all four raves and home, the way out), space_rave 446, magic_rave 563, dinos_rave 559, transport_rave 559, race 3616 (incl. `test_race_themes` 2011), run_matrix 1945, cloakroom 3062, bar 398, activity_modes 149, minigame 251, weather 201, test_geography 299, choice_pitch 28, heralds 430, camera 48, story_player 2868, rail_paths 652, transition 17579, run_ 17414, playtest 3569, story 53147. A virtual run drove bedsit → Magic rave → home by touch with the facing saved.

## NOT verified
- Nothing played by a human on a screen or a phone. Only the Magic path was driven end to end; the way-out test sets the three activity flags directly rather than playing the activities.
- No listening by ear.

## Placeholders and known limits (from the independent review, the agents' reports and the lead)
- **Art:** the Magic, Dinosaur and Transport rave art and all three new races are PLACEHOLDERS and say so in their manifests (`placeholder: true`): not drawn from a painting, Space's cell size (160×104 vehicles, 448×56 dash) not the 256 px standard (ruling 36), recoloured Space props (the Dinos truck and Transport bus are the Space van). No race engine or contact sounds. The Dinos bonnet is a flat band.
- **The way out and the Transport threshold share one door** (middle vs top region) in the west facing; documented; the owner may want a separate exit object.
- Bar customers are the same `antenna` body in each rave, dressed per theme. `build_transport_rave.py` still writes dark control colours; the lift to legibility is in drawing (`ControlPictograms.legible`).
- The bedsit's floor is out of frame (the held pitch is not used there).
- Race rules and numbers are Space's for all four themes; finish times are the same for the same play.
- The fourth rave's hangar race nodes are real scenes but were looked at only on contact sheets (`docs/shots/bedsit/<theme>/race_contact.jpg`).
- Rulings 40 (card table keeps `replace`), 41 (any one rave opens the way out), 42/42b (walk pace, deferred swap) and 43 (rail check worst case) are in force; 41–43 are the lead's and open to the owner's overrule.

## Not in this PR
`feature/doom-layout-worlds` (the eight Doom worlds) is a separate branch and PR by plan. `main` is untouched: it moves only on the owner's word after they play `feature/one-pc`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
