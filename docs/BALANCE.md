# Balance evidence (acceptance A08, A12)

Method: `tools/balance.sh <pack> <enemy_fraction> <policies...>` runs `tools/autoplay.gd`, a headless harness that
drives `Match` (judgement, enemy schedule, battle simulation with the Rush AI squads on both sides; no audio, no
rendering) with a scripted input policy at 60 Hz against the pack's authored enemy events. Policies: `perfect`
hits every note on time; `accuracy:<f>` hits each note with seeded probability f; `none` never presses;
`perfect_until:<s>` plays perfectly then stops. `enemy_fraction` keeps a seeded subset of the authored enemy events
(1.0 = the pack as authored). Runs on 28 Oct 2026, seed 1, simulation at 25 ticks/s, after the OpenRA behaviour
rewrite (`docs/OPENRA_BEHAVIOUR_SPEC.md`).

## Level 01 "First Contact" (64 bars, 88.3 s, 321 player notes), as authored

Schedule: `--enemy-profile ramp --enemy-start 0.35 --enemy-end 0.63` (161 of 321 events; per section intro 37%,
build 40%, drop_1 45%, breakdown 51%, drop_2 56%, finale 61%). Repair budget 500 credits per side.

| Player policy | Outcome | Time | Player built (tanks/infantry/aircraft) | Enemy built | Peak live units P/E |
| --- | --- | ---: | --- | --- | --- |
| perfect | victory | 61.9 s | 92 / 370 / 5 | 29 / 150 / 5 | 438 / 72 |
| accuracy 0.85 | victory | 69.2 s | 89 / 370 / 5 | 35 / 180 / 5 | 425 / 83 |
| accuracy 0.70 | victory | 71.1 s | 73 / 325 / 5 | 38 / 185 / 5 | 378 / 73 |
| accuracy 0.50 | defeat (song end, both bases intact) | 88.3 s | 66 / 270 / 5 | 55 / 280 / 5 | 296 / 93 |
| none | defeat (main base destroyed) | 54.0 s | 0 | 24 / 140 / 5 | 0 / 163 |

Consistently accurate play wins before the track ends; sustained misses lose (A12). The enemy never reacts to the
player: its events are the authored list, skipped when a producer is dead or the air wing is capped (A08;
`tests/test_match.gd` proves once-and-in-order application).

Siege sanity check: `perfect_until:30` against `enemy_fraction 0` (thirty seconds of production, no opposition)
destroys the enemy main base at 54 s, so the base assault itself works whenever the field is won.

## What shaped the result (all from traces with `RW_DEBUG_EVERY=12`)

- Rush AI squads of 20 to 49 idle units (`SquadSize 20 + Random(30)`) left most of both armies standing at the
  rally for the whole song; the threshold is scaled to `10 + Random(10)` for an 88-second match.
- Squads that always attack-move to the closest enemy were pinned by the enemy's own production trickle next to its
  wall and never walked the last ten cells. Assault squads now attack-move at the enemy construction yard (the
  engine's rush objective) and fight what they meet within AttackScanRadius on the way.
- Several squads near one enemy mass each decided alone that they were outnumbered and fled piecemeal; the flee
  comparison now counts every friendly ground unit inside the danger circle.
- A rally point outside the wall offered the attacker a permanent target; a rally next to the exit blocked
  production. The rally is inside the base and production spawns on the nearest free cell around the exit.
- A hundred units shooting the same rifleman wasted most of their fire (overkill); targets already aimed at by many
  friends count as slightly farther away.
- At Red Alert cost scaling a repair step costs one credit, so the PRD's 5,000-credit budget repaired any building
  indefinitely (730 HP per second); 500 credits is about two full repairs of a main base.
- Anti-air: one SAM site per base, in the base centre, so helicopter squads (which avoid areas where
  `3 x SAMs >= squad size`) can strike the midfield but need four or more aircraft to hit the base.

## Earlier schedules (before the OpenRA rewrite; kept for the record)

With the first, simpler combat model the chosen schedule was ramp 0.5 to 0.9 (perfect won at 69 s). The OpenRA
behaviour model is much bloodier at the front and the enemy's production is now the pacing lever, hence the lower
ramp.

## Level 01 after the four-button, mixed-roster, fortified-base rework (28 Oct 2026)

The bases gained a brick wall line with pillboxes at the ends of an eight-cell opening, a second SAM site, a radar
dome, a service depot and a third power plant; kicks now cycle through nine vehicle types and snares produce mixed
squads (`data/rosters/openra_mvp_01.json`); wide warheads splash. Two things changed the assault:

- Crowd push. The soft separation shoved a column pressing into a wall opening back as fast as its front walked,
  so perfect play with the old schedule never reached the enemy base. A moving unit now takes only the sideways
  part of the crowd push, capped at half a step (`BattleSim._separate`).
- The chokepoint. Idle enemy units rallied in the corridor between the two walls and plugged the opening; the
  rally point is inside the inner wall again.

With those fixed the schedule was re-authored: `--enemy-profile ramp --enemy-start 0.22 --enemy-end 0.42`
(105 of 321 events; per section intro 23%, build 26%, drop_1 29%, breakdown 33%, drop_2 37%, finale 41%).
Candidates measured (perfect / 0.85 / 0.7): ramp 0.28-0.50 lost / lost / lost (perfect broke in at 83 s only after
the crowd fix); 0.25-0.45 won at 72 s / lost / lost; 0.22-0.42 won at 68 s / won at 70 s / lost. Seed 1:

| Player policy | Outcome | Time | Player built (vehicles/infantry/aircraft) | Enemy built | Peak live units P/E |
| --- | --- | ---: | --- | --- | --- |
| perfect | victory | 68.2 s | 104 / 415 / 5 | 32 / 85 / 5 (+14 replacements) | 391 / 43 |
| accuracy 0.85 | victory | 69.5 s | 89 / 375 / 5 | 32 / 85 / 5 | 322 / 43 |
| accuracy 0.70 | defeat (song end, both bases intact) | 88.3 s | 94 / 430 / 5 | 48 / 160 / 5 | 245 / 46 |
| accuracy 0.50 | defeat (song end, both bases intact) | 88.3 s | 66 / 270 / 5 | 48 / 160 / 5 | 164 / 61 |
| none | defeat (main base destroyed) | 64.9 s | 0 | 32 / 90 / 5 | 0 / 118 |

The fortified base is the point: 70% accuracy no longer wins, and the field between the walls is where the song is
decided. Outcomes between 0.7 and 0.85 are chaotic (a roster variant with less anti-air lost where the fuller one
won); when the owner's new tracks arrive, re-run this table before choosing their ramp. The air wing does fire
(ammo spent in about a third of the trace samples) but rocket soldiers and flak trucks make the Rush AI air squad
cautious, as in OpenRA.

## Known tuning items

- Peak live units reach about 440 with perfect play. Desktop (RTX 3060, 1280x720): average 17.4 ms, p95 20.8 ms,
  4 of 3,555 frames over 33 ms (the load spike), from the `PERF` line of `RW_AUTOPLAY=perfect`; the phone
  measurement (A13) is pending the device run. Per-tick simulation cost after the spatial-grid work: about 4 ms at
  peak (profile in the autoplay JSON under `profile_ms`).
- 70% accuracy still wins with 17 s to spare; raise `--enemy-end` (or both ramp ends) if the first level should
  demand more.
- Outcomes between 0.5 and 0.7 accuracy are sensitive to the squad timing (chaotic field battles); widen the
  margin with the ramp end if a gentler difficulty is wanted.
- Air: 72 bass actions, only 5 aircraft per side ever exist; most bass actions find the wing busy, by design.

# Defense campaign balance (schema 2 packs, levels 1 to 3)

Added 29 October 2026. Everything below the duel history in this file (above this section) belongs to the legacy
two-sided duel. The campaign is measured with the same headless harness:

```
RW_CHART=level_02.campaign RW_SEEDS="1 2 3" RW_WAVES=1 bash tools/balance.sh res://songs/second_pulse 1.0 perfect "accuracy:0.85" "accuracy:0.6" none
```

One line per policy and seed (with `RW_WAVES=1`, also each wave's spawn, first arrival at the wall and clear time);
`seed` offsets the simulation seed (`level.seed * 10 + seed`) and the accuracy draws. The policies are `perfect` (every
note hit exactly), `accuracy:<f>` (each note hit with that probability, seeded, misses simply not pressed) and `none`.
`tests/test_defense_balance.gd` keeps the headline guard rails (perfect survives, no input loses) in the headless suite.

## What was tuned and how

- The pack's `waves.proposed.json` assumed entries at the map edge. Entries now sit 14 to 17 cells beyond the wall
  opening (`data/battlefields/defense_01.json`); riflemen take 8.3 s from the entry to the centre defense point and
  12.2 s to the wall opening, jeeps 2.7 s and 4.0 s (the build prints this per wave: `python tools/campaign/build_defense_pack.py 1`).
- The command core keeps the OpenRA construction yard's armour but its hit points are a level setting
  (`rules.objective_hp`): 60,000 against the building's 150,000. At 150,000 the proposed waves rarely killed it within a
  44 to 66 s song, so the no-input run did not reliably lose.
- Wave sizes are the proposed waves multiplied (infantry and vehicles alike): level 1 x1.9, level 2 x2.4, level 3 x1.4
  (`python tools/campaign/gen_waves.py <level> 60000 <scale>`, then `build_defense_pack.py <level> --waves-only`). The files
  in `data/campaign/waves/` are the authoritative result and a test keeps the packs in step with them. Level 3's
  scale is lower because its song gives the player the third recipe (bass groups of two riflemen and a rocket
  soldier) and eleven waves; at x1.7 even perfect play lost.
- Enemy wave units ignore buildings other than their objective (they fight units and the core); otherwise a wave
  parks in front of the pillboxes and shoots at them forever, which no recipe of this roster can break. The
  pillboxes and walls of `defense_01` still shoot and block.
- Recipes are the catalogue's, unchanged: March Kick two riflemen, Guard Snare one jeep, Armour Kick light tank then
  jeep, Patrol Sub two riflemen and a rocket soldier. They were not rebalanced against each other: a tuned
  sidegrade set is outside the first three levels.

## Results (seeds 1 to 3, desktop headless run on 29 October 2026)

### Level 1, First Watch (32 bars, 44.1 s, command core 60,000 hp, waves = proposed x1.9)

| Policy | Seed | Outcome | Ended | Accuracy | Core left | Groups (by point 1/2/3) | Player units lost | Enemy units killed | Peak live units P/E |
| --- | ---: | --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| perfect | 1 | victory (survived) | 44.1 s | 100% | 100% | 64 (22/21/21) | 59 | 34 | 46 / 87 |
| perfect | 2 | victory (survived) | 44.1 s | 100% | 100% | 64 (22/21/21) | 68 | 29 | 44 / 94 |
| perfect | 3 | victory (survived) | 44.1 s | 100% | 100% | 64 (22/21/21) | 68 | 27 | 45 / 93 |
| accuracy:0.85 | 1 | victory (survived) | 44.1 s | 92% | 100% | 59 (20/20/19) | 68 | 29 | 42 / 89 |
| accuracy:0.85 | 2 | victory (survived) | 44.1 s | 84% | 100% | 54 (18/18/18) | 71 | 26 | 39 / 91 |
| accuracy:0.85 | 3 | victory (survived) | 44.1 s | 81% | 100% | 52 (18/17/17) | 64 | 30 | 41 / 89 |
| accuracy:0.6 | 1 | victory (survived) | 44.1 s | 56% | 14% | 36 (12/12/12) | 47 | 12 | 20 / 106 |
| accuracy:0.6 | 2 | victory (survived) | 44.1 s | 64% | 100% | 41 (14/14/13) | 57 | 21 | 24 / 96 |
| accuracy:0.6 | 3 | victory (survived) | 44.1 s | 66% | 100% | 42 (14/14/14) | 56 | 20 | 27 / 99 |
| none | 1 | defeat (core destroyed) | 39.9 s | 0% | 0% | 0 (0/0/0) | 1 | 18 | 0 / 93 |
| none | 2 | defeat (core destroyed) | 39.8 s | 0% | 0% | 0 (0/0/0) | 1 | 18 | 0 / 91 |
| none | 3 | defeat (core destroyed) | 42.9 s | 0% | 0% | 0 (0/0/0) | 1 | 19 | 0 / 98 |

### Level 2, Second Pulse (40 bars, 55.2 s, command core 60,000 hp, waves = proposed x2.4)

| Policy | Seed | Outcome | Ended | Accuracy | Core left | Groups (by point 1/2/3) | Player units lost | Enemy units killed | Peak live units P/E |
| --- | ---: | --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| perfect | 1 | victory (survived) | 55.2 s | 100% | 100% | 96 (32/32/32) | 115 | 76 | 65 / 171 |
| perfect | 2 | victory (survived) | 55.2 s | 100% | 100% | 96 (32/32/32) | 112 | 81 | 64 / 168 |
| perfect | 3 | victory (survived) | 55.2 s | 100% | 100% | 96 (32/32/32) | 115 | 79 | 67 / 167 |
| accuracy:0.85 | 1 | victory (survived) | 55.2 s | 89% | 100% | 85 (29/28/28) | 112 | 80 | 52 / 165 |
| accuracy:0.85 | 2 | victory (survived) | 55.2 s | 85% | 100% | 82 (28/27/27) | 115 | 47 | 43 / 198 |
| accuracy:0.85 | 3 | victory (survived) | 55.2 s | 81% | 100% | 78 (26/26/26) | 107 | 52 | 50 / 194 |
| accuracy:0.6 | 1 | defeat (core destroyed) | 53.2 s | 57% | 0% | 53 (18/18/17) | 78 | 20 | 23 / 226 |
| accuracy:0.6 | 2 | victory (survived) | 55.2 s | 66% | 38% | 63 (21/21/21) | 89 | 31 | 26 / 214 |
| accuracy:0.6 | 3 | victory (survived) | 55.2 s | 61% | 14% | 59 (20/20/19) | 84 | 36 | 26 / 209 |
| none | 1 | defeat (core destroyed) | 35.2 s | 0% | 0% | 0 (0/0/0) | 1 | 12 | 0 / 116 |
| none | 2 | defeat (core destroyed) | 36.1 s | 0% | 0% | 0 (0/0/0) | 1 | 14 | 0 / 118 |
| none | 3 | defeat (core destroyed) | 35.0 s | 0% | 0% | 0 (0/0/0) | 1 | 12 | 0 / 114 |

### Level 3, Hold the Line (48 bars, 66.2 s, command core 60,000 hp, waves = proposed x1.4)

| Policy | Seed | Outcome | Ended | Accuracy | Core left | Groups (by point 1/2/3) | Player units lost | Enemy units killed | Peak live units P/E |
| --- | ---: | --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| perfect | 1 | victory (survived) | 66.2 s | 100% | 100% | 89 (30/30/29) | 148 | 76 | 95 / 134 |
| perfect | 2 | victory (survived) | 66.2 s | 100% | 100% | 89 (30/30/29) | 153 | 79 | 93 / 130 |
| perfect | 3 | victory (survived) | 66.2 s | 100% | 100% | 89 (30/30/29) | 133 | 106 | 96 / 105 |
| accuracy:0.85 | 1 | victory (survived) | 66.2 s | 89% | 100% | 79 (27/26/26) | 155 | 73 | 70 / 136 |
| accuracy:0.85 | 2 | victory (survived) | 66.2 s | 85% | 100% | 76 (26/25/25) | 138 | 85 | 64 / 126 |
| accuracy:0.85 | 3 | victory (survived) | 66.2 s | 80% | 98% | 71 (24/24/23) | 141 | 59 | 58 / 152 |
| accuracy:0.6 | 1 | defeat (core destroyed) | 58.5 s | 58% | 0% | 48 (16/16/16) | 90 | 29 | 22 / 152 |
| accuracy:0.6 | 2 | defeat (core destroyed) | 61.0 s | 63% | 0% | 53 (18/18/17) | 98 | 36 | 28 / 152 |
| accuracy:0.6 | 3 | defeat (core destroyed) | 61.8 s | 62% | 0% | 52 (18/17/17) | 100 | 50 | 39 / 149 |
| none | 1 | defeat (core destroyed) | 40.8 s | 0% | 0% | 0 (0/0/0) | 1 | 16 | 0 / 90 |
| none | 2 | defeat (core destroyed) | 41.4 s | 0% | 0% | 0 (0/0/0) | 1 | 17 | 0 / 90 |
| none | 3 | defeat (core destroyed) | 40.9 s | 0% | 0% | 0 (0/0/0) | 1 | 16 | 0 / 90 |

## Reading the tables

- **Perfect and 0.85 accuracy survive every seed on all three levels**, with the command core at 100% except one
  0.85 run on level 3 (98%).
- **No input loses every seed on all three levels**, at 40 to 43 s of 44 s on level 1, about 35 s of 55 s on level 2
  and about 41 s of 66 s on level 3. Level 1 is the narrow one: with no input the first waves still need most of the
  song to reach and kill the core.
- **0.6 accuracy is reported, not tuned for**: level 1 survives all three seeds (one with the core at 14%), level 2
  survives two of three (core 38% and 14%) and loses one at 53 s, level 3 loses all three at 58 to 62 s. A player who
  misses four notes in ten is meant to feel the defense thin out; whether that is the right difficulty is the
  owner's call after a phone playtest.
- Misses cost production only (no direct core damage). The by-point column shows the round robin: the three defense
  points get equal shares of the groups (22/21/21 of 64 on level 1).
- Enemy peaks of 100 to 230 live units (the unclamped waves pile up when the defenders thin out) are the worst case for
  frame time; see the `PERF` line below.

## Desktop frame time

`RW_PACK=res://songs/hold_the_line RW_CHART=level_03.campaign RW_AUTOPLAY=perfect RW_SCENE=play`, a real window on the
development PC (RTX 3060, vsync 60 Hz), 66 s: 3,971 frames, average 16.68 ms, p95 16.67 ms, maximum 58.3 ms, one frame
over 33 ms, peak 176 live units. That is the perfect-play case; the 0.6 runs reach a higher peak (about 230 enemies on
level 2) but were measured headless only. The phone measurement (A13) is still the owner's run: see
`docs/HANDOVER.md` for the exact command.

## Not verified

No phone playthrough, no real stems (all audio is synthesised), no human playtest of the charts or of the difficulty.
The same-thumb gaps (960 / 480 ticks) are design targets that the loader only warns about; none of the three charts
triggers a warning.
