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
