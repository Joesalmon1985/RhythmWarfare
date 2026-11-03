# Balance evidence

The ten missions are the second part of this file ("Missions balance"). The first part is the legacy duel
(acceptance A08, A12), kept for the multiplayer mode that will build on it.

# Legacy duel (acceptance A08, A12)

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

# Missions balance (schema 3, ten missions, 31 October 2026)

This part replaces the schema 2 campaign tables of 29 and 30 October (round-robin groups, per-note recipes), which no
longer exist. Everything above this heading is the legacy duel. The rule set is `docs/PRD.md` section 15 and
`data/campaign/rules.json`; the waves are `data/campaign/waves/level_NN.json` and are baked into each pack by
`python tools/content/build.py`. **Rebuild the packs after editing a wave file**, or the harness and the game keep
playing the old waves.

## Method

```
python tools/balance_missions.py --seeds 1 2 3 --policies perfect beginner sloppy none > out.md   # every mission
python tools/balance_missions.py --missions m05 m10 --seeds 4 5 6 --policies perfect beginner     # a subset
RW_SEEDS="1 2 3" bash tools/balance.sh res://songs/m03_hold_the_line 1.0 perfect beginner         # one pack, raw lines
```

`tools/autoplay.gd` drives `Match` headless (pad judge, sequence tracker, rewards, the 25 Hz battle simulation; no audio,
no rendering) with a scripted input policy at 60 Hz. One row per mission, policy and seed. The policies:

| Policy | What it does |
| --- | --- |
| `perfect` | every cue pressed on time, every hold held to its tail |
| `beginner` | presses 85% of cues with a timing error drawn from N(+15 ms, 55 ms), lets go of 30% of holds early, adds a stray press on 12% of cues |
| `sloppy` | presses 70% of cues, N(+25 ms, 85 ms), 50% early releases, 25% strays |
| `mash` | presses every pad on every sixteenth (not in the table: it passes sequences, only as loose, see `tests/test_sequences.gd`) |
| `none` | never presses |

Seeds change the battle simulation and the input draws. A simulation pass is evidence about the waves, not about how
hard a mission feels to a person: nobody has played these missions.

## Mission 1 after the owner's first play (3 November 2026, later the same day)

The owner's six tweaks changed the sim for every mission (player units fight on the move, a defender beyond its
leash fires at what is in range but never chases) and mission 1's map and chart (96 x 48 village at zoom 0.75 with
the rally points 7 cells out, the bass charted by pitch over four pads as taps at most one per 1.5 beats, so the bass
phases have 12 or 16 cues per 8 bars instead of 15 or 23 holds). Same waves and barracks hp as the village level.
Seeds 1 to 3: perfect 3/3 with every wave destroyed, beginner 3/3, sloppy 3/3 (it was 2/3: the taps-only chart
passes more sequences), no input loses at about 1:41 (was 1:36; the longer walks delay the waves).

| Mission | Policy | Seed | Outcome | At | Sequences (sharp/steady/loose) | Built | Units | Repairs | Defenses alive | Barracks | Enemies killed | Peak units (you / enemy) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 First Watch | perfect | 1 | victory | 176.6 s | 32/32 (32/0/0) | 9 | 18 | 5 | 9 | 100% | 139 | 29 / 27 |
| 1 First Watch | perfect | 2 | victory | 176.6 s | 32/32 (32/0/0) | 9 | 18 | 5 | 9 | 100% | 139 | 25 / 28 |
| 1 First Watch | perfect | 3 | victory | 176.6 s | 32/32 (32/0/0) | 9 | 18 | 5 | 9 | 100% | 139 | 26 / 28 |
| 1 First Watch | beginner | 1 | victory | 176.6 s | 30/32 (4/24/2) | 9 | 17 | 4 | 9 | 100% | 139 | 27 / 27 |
| 1 First Watch | beginner | 2 | victory | 176.6 s | 28/32 (6/20/2) | 9 | 15 | 4 | 9 | 100% | 139 | 22 / 27 |
| 1 First Watch | beginner | 3 | victory | 176.6 s | 29/32 (6/21/2) | 9 | 15 | 5 | 9 | 100% | 139 | 26 / 28 |
| 1 First Watch | sloppy | 1 | victory | 176.6 s | 31/32 (1/12/18) | 9 | 18 | 4 | 9 | 100% | 139 | 26 / 28 |
| 1 First Watch | sloppy | 2 | victory | 176.6 s | 28/32 (0/11/17) | 9 | 16 | 3 | 9 | 100% | 139 | 26 / 28 |
| 1 First Watch | sloppy | 3 | victory | 176.6 s | 27/32 (0/12/15) | 9 | 15 | 3 | 9 | 100% | 139 | 18 / 28 |
| 1 First Watch | none | 1 | defeat | 101.0 s | 0/32 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 10 | 15 / 67 |
| 1 First Watch | none | 2 | defeat | 103.1 s | 0/32 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 11 | 15 / 73 |
| 1 First Watch | none | 3 | defeat | 101.1 s | 0/32 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 10 | 15 / 67 |

Missions 2 to 10 with the new defender behaviour (seeds 1 to 3): three late losses appeared that the 2 November
table did not have (mission 5 beginner seed 1 at 75.6 s, mission 8 perfect seed 3 at 88.1 s where the radar dome
fell 0.2 s before the end, mission 10 beginner seed 3 at 105.4 s), so their objective hp went up one notch
(mission 8 radar dome 60,000 to 70,000 and mission 5 core 90,000 to 130,000, which fixed them; mission 10 core
125,000 to 185,000 over three rounds, which only pushed its beginner seed 3 loss from 105.4 s to 108.0 s of 110.3:
that seed is overwhelmed, not worn down, so the hp stays at 185,000 and the loss is recorded as known). The rows
marked (retuned) below are the final runs; the other six missions are unchanged in outcome.

| Mission | Policy | Seed | Outcome | At | Sequences (sharp/steady/loose) | Built | Units | Repairs | Defenses alive | Core | Enemies killed | Peak units (you / enemy) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 Counterpoint (retuned) | perfect | 1 | victory | 77.2 s | 14/14 (14/0/0) | 8 | 6 | 0 | 5 | 100% | 44 | 2 / 26 |
| 5 Counterpoint (retuned) | perfect | 2 | victory | 77.2 s | 14/14 (14/0/0) | 8 | 6 | 0 | 5 | 100% | 45 | 3 / 25 |
| 5 Counterpoint (retuned) | perfect | 3 | victory | 77.2 s | 14/14 (14/0/0) | 8 | 6 | 0 | 5 | 100% | 45 | 3 / 25 |
| 5 Counterpoint (retuned) | beginner | 1 | victory | 77.2 s | 14/14 (1/13/0) | 8 | 6 | 0 | 5 | 11% | 35 | 2 / 28 |
| 5 Counterpoint (retuned) | beginner | 2 | victory | 77.2 s | 13/14 (1/11/1) | 7 | 6 | 0 | 3 | 100% | 41 | 2 / 28 |
| 5 Counterpoint (retuned) | beginner | 3 | victory | 77.2 s | 14/14 (1/13/0) | 8 | 6 | 0 | 5 | 100% | 40 | 2 / 29 |
| 5 Counterpoint (retuned) | sloppy | 1 | victory | 77.2 s | 12/14 (0/4/8) | 7 | 5 | 0 | 4 | 40% | 40 | 2 / 33 |
| 5 Counterpoint (retuned) | sloppy | 2 | victory | 77.2 s | 12/14 (0/5/7) | 7 | 5 | 0 | 5 | 100% | 40 | 2 / 29 |
| 5 Counterpoint (retuned) | sloppy | 3 | victory | 77.2 s | 11/14 (0/6/5) | 7 | 4 | 0 | 5 | 100% | 32 | 2 / 35 |
| 5 Counterpoint (retuned) | none | 1 | defeat | 37.6 s | 0/14 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 0 | 0 / 32 |
| 5 Counterpoint (retuned) | none | 2 | defeat | 37.6 s | 0/14 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 0 | 0 / 32 |
| 5 Counterpoint (retuned) | none | 3 | defeat | 37.6 s | 0/14 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 0 | 0 / 32 |
| 10 Last Light (retuned) | perfect | 1 | victory | 110.3 s | 20/20 (20/0/0) | 8 | 8 | 4 | 6 | 100% | 71 | 4 / 20 |
| 10 Last Light (retuned) | perfect | 2 | victory | 110.3 s | 20/20 (20/0/0) | 8 | 8 | 4 | 5 | 100% | 71 | 4 / 22 |
| 10 Last Light (retuned) | perfect | 3 | victory | 110.3 s | 20/20 (20/0/0) | 8 | 8 | 4 | 4 | 98% | 64 | 4 / 27 |
| 10 Last Light (retuned) | beginner | 1 | victory | 110.3 s | 20/20 (0/19/1) | 8 | 8 | 4 | 6 | 100% | 71 | 4 / 23 |
| 10 Last Light (retuned) | beginner | 2 | victory | 110.3 s | 19/20 (2/16/1) | 8 | 7 | 4 | 7 | 100% | 71 | 3 / 22 |
| 10 Last Light (retuned) | beginner | 3 | defeat | 108.0 s | 18/20 (3/15/0) | 8 | 7 | 3 | 1 | 0% | 56 | 3 / 28 |
| 10 Last Light (retuned) | sloppy | 1 | victory | 110.3 s | 16/20 (0/8/8) | 8 | 4 | 4 | 4 | 100% | 69 | 2 / 25 |
| 10 Last Light (retuned) | sloppy | 2 | victory | 110.3 s | 16/20 (0/7/9) | 8 | 4 | 4 | 1 | 49% | 56 | 2 / 25 |
| 10 Last Light (retuned) | sloppy | 3 | victory | 110.3 s | 14/20 (0/8/6) | 6 | 4 | 4 | 1 | 97% | 58 | 2 / 26 |
| 10 Last Light (retuned) | none | 1 | defeat | 70.2 s | 0/20 (0/0/0) | 0 | 0 | 0 | 2 | 0% | 29 | 0 / 33 |
| 10 Last Light (retuned) | none | 2 | defeat | 70.4 s | 0/20 (0/0/0) | 0 | 0 | 0 | 1 | 0% | 28 | 0 / 33 |
| 10 Last Light (retuned) | none | 3 | defeat | 70.2 s | 0/20 (0/0/0) | 0 | 0 | 0 | 2 | 0% | 29 | 0 / 33 |
| 8 Crossfire (retuned) | perfect | 1 | victory | 88.3 s | 16/16 (16/0/0) | 8 | 5 | 3 | 3 | 100% | 58 | 3 / 31 |
| 8 Crossfire (retuned) | perfect | 2 | victory | 88.3 s | 16/16 (16/0/0) | 8 | 5 | 3 | 2 | 100% | 66 | 4 / 32 |
| 8 Crossfire (retuned) | perfect | 3 | victory | 88.3 s | 16/16 (16/0/0) | 8 | 5 | 3 | 3 | 100% | 58 | 3 / 27 |
| 8 Crossfire (retuned) | beginner | 1 | victory | 88.3 s | 16/16 (0/16/0) | 8 | 5 | 3 | 6 | 100% | 64 | 3 / 28 |
| 8 Crossfire (retuned) | beginner | 2 | victory | 88.3 s | 15/16 (1/14/0) | 8 | 4 | 3 | 4 | 100% | 64 | 3 / 24 |
| 8 Crossfire (retuned) | beginner | 3 | victory | 88.3 s | 16/16 (2/14/0) | 8 | 5 | 2 | 4 | 100% | 64 | 4 / 25 |
| 8 Crossfire (retuned) | sloppy | 1 | victory | 88.3 s | 15/16 (0/5/10) | 7 | 5 | 2 | 5 | 100% | 61 | 4 / 25 |
| 8 Crossfire (retuned) | sloppy | 2 | victory | 88.3 s | 15/16 (0/5/10) | 7 | 5 | 3 | 4 | 100% | 59 | 4 / 26 |
| 8 Crossfire (retuned) | sloppy | 3 | victory | 88.3 s | 14/16 (0/5/9) | 6 | 5 | 3 | 4 | 100% | 63 | 4 / 22 |
| 8 Crossfire (retuned) | none | 1 | defeat | 36.0 s | 0/16 (0/0/0) | 0 | 0 | 0 | 2 | 0% | 5 | 0 / 30 |
| 8 Crossfire (retuned) | none | 2 | defeat | 36.0 s | 0/16 (0/0/0) | 0 | 0 | 0 | 2 | 0% | 5 | 0 / 30 |
| 8 Crossfire (retuned) | none | 3 | defeat | 36.0 s | 0/16 (0/0/0) | 0 | 0 | 0 | 2 | 0% | 5 | 0 / 30 |
| 10 Last Light (retuned) | perfect | 1 | victory | 110.3 s | 20/20 (20/0/0) | 8 | 8 | 4 | 6 | 100% | 71 | 4 / 20 |
| 10 Last Light (retuned) | perfect | 2 | victory | 110.3 s | 20/20 (20/0/0) | 8 | 8 | 4 | 5 | 100% | 71 | 4 / 22 |
| 10 Last Light (retuned) | perfect | 3 | victory | 110.3 s | 20/20 (20/0/0) | 8 | 8 | 4 | 4 | 98% | 64 | 4 / 27 |
| 10 Last Light (retuned) | beginner | 1 | victory | 110.3 s | 20/20 (0/19/1) | 8 | 8 | 4 | 6 | 100% | 71 | 4 / 23 |
| 10 Last Light (retuned) | beginner | 2 | victory | 110.3 s | 19/20 (2/16/1) | 8 | 7 | 4 | 7 | 100% | 71 | 3 / 22 |
| 10 Last Light (retuned) | beginner | 3 | defeat | 106.8 s | 18/20 (3/15/0) | 8 | 7 | 3 | 1 | 0% | 56 | 3 / 28 |
| 10 Last Light (retuned) | sloppy | 1 | victory | 110.3 s | 16/20 (0/8/8) | 8 | 4 | 4 | 4 | 100% | 69 | 2 / 25 |
| 10 Last Light (retuned) | sloppy | 2 | victory | 110.3 s | 16/20 (0/7/9) | 8 | 4 | 4 | 1 | 33% | 56 | 2 / 25 |
| 10 Last Light (retuned) | sloppy | 3 | victory | 110.3 s | 14/20 (0/8/6) | 6 | 4 | 4 | 1 | 96% | 58 | 2 / 26 |
| 10 Last Light (retuned) | none | 1 | defeat | 68.0 s | 0/20 (0/0/0) | 0 | 0 | 0 | 2 | 0% | 29 | 0 / 33 |
| 10 Last Light (retuned) | none | 2 | defeat | 68.2 s | 0/20 (0/0/0) | 0 | 0 | 0 | 1 | 0% | 28 | 0 / 33 |
| 10 Last Light (retuned) | none | 3 | defeat | 68.0 s | 0/20 (0/0/0) | 0 | 0 | 0 | 2 | 0% | 28 | 0 / 33 |

## Mission 1, the village level (3 November 2026)

Mission 1 is now 128 bars (176.6 s), sixteen eight-bar phases DDBD BDDB DBDB DDBD, 32 four-bar sequences, on the
`village_01` battlefield: three choke points with five riflemen each from the start (`start_units`), ten houses and
ten civilians inside the wall, the barracks (60,000 hp, the only required objective) in the middle. Rewards: 9
pillboxes (three sockets open per point), 18 rifle squads and 5 grenadier squads of three (the harness counts units
and repairs where the sockets or points were full). 25 waves, 139 enemies, in four acts: bars 1 to 27 single riflemen
waves at the choke points (`target: defenses`), bars 33 to 62 two entries at once, defenses then the village
(`civilians`), bars 65 to 90 grenadiers and three jeeps for the village, bars 97 to 110 three waves of 5 riflemen and
2 grenadiers from every side for the barracks (`core`). The autoplay harness taps the suggested section every frame
(`RW_SECTION=auto`, the default on levels with civilians).

Tuning rounds, seeds 1 to 3: round 1 (barracks 20,000 hp, 150 enemies) lost both sloppy seeds and let no input live
past 1:10; round 2 (40,000 hp) still lost sloppy 2/2; round 3 (60,000 hp, waves 17 and 18 cut to 3 riflemen, the act
4 waves at 5 + 2) is kept: perfect wins 3/3 with every wave destroyed (139 killed, 0 villagers lost, at most 1 house),
beginner 3/3, sloppy 2/3 (seed 1 loses at 2:10 with 16 of 32 sequences), no input loses 3/3 at about 1:36 (the
barracks falls to act 2 alone). Missions 2 to 10 produce byte-identical harness reports to the 2 November run (the
civilian code paths are not entered, the combat rng is untouched).

| Mission | Policy | Seed | Outcome | At | Sequences (sharp/steady/loose) | Built | Units | Repairs | Defenses alive | Barracks | Enemies killed | Peak units (you / enemy) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 First Watch | perfect | 1 | victory | 176.6 s | 32/32 (32/0/0) | 9 | 18 | 5 | 9 | 100% | 139 | 23 / 23 |
| 1 First Watch | perfect | 2 | victory | 176.6 s | 32/32 (32/0/0) | 9 | 18 | 5 | 9 | 100% | 139 | 24 / 23 |
| 1 First Watch | perfect | 3 | victory | 176.6 s | 32/32 (32/0/0) | 9 | 18 | 5 | 9 | 100% | 139 | 21 / 21 |
| 1 First Watch | beginner | 1 | victory | 176.6 s | 31/32 (4/25/2) | 9 | 18 | 4 | 9 | 100% | 139 | 26 / 27 |
| 1 First Watch | beginner | 2 | victory | 176.6 s | 30/32 (4/24/2) | 9 | 17 | 4 | 9 | 100% | 139 | 28 / 21 |
| 1 First Watch | beginner | 3 | victory | 176.6 s | 29/32 (8/20/1) | 10 | 17 | 2 | 9 | 100% | 139 | 20 / 22 |
| 1 First Watch | sloppy | 1 | defeat | 130.3 s | 16/32 (0/8/8) | 7 | 9 | 0 | 7 | 0% | 65 | 18 / 47 |
| 1 First Watch | sloppy | 2 | victory | 176.6 s | 24/32 (0/9/15) | 10 | 14 | 0 | 8 | 100% | 139 | 16 / 33 |
| 1 First Watch | sloppy | 3 | victory | 176.6 s | 28/32 (1/13/14) | 9 | 15 | 4 | 9 | 100% | 139 | 17 / 21 |
| 1 First Watch | none | 1 | defeat | 97.1 s | 0/32 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 11 | 15 / 66 |
| 1 First Watch | none | 2 | defeat | 95.2 s | 0/32 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 10 | 15 / 63 |
| 1 First Watch | none | 3 | defeat | 95.6 s | 0/32 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 10 | 15 / 67 |

These rows replace the 2 November mission 1 rows below and in the raw table. "Units" counts squads as three; the
"Defenses alive" column counts pillboxes; the barracks is the "Core" column of the older tables. Known: the harness's
"Peak units (you)" includes the 15 start riflemen; the sloppy loss is a run that never retakes a choke point held by an
act 2 `defenses` wave.

## Mission 1 rebuilt on the owner's recordings (2 November 2026)

Mission 1 is now 48 bars (66.2 s), six eight-bar phases DDBDBD, 12 four-bar sequences rewarding 7 pillboxes and
5 jeeps, over 11 waves of riflemen (3 to 6 each, two with a jeep; 54 riflemen and 2 jeeps, the last wave at bar 32).
Tuned with `tools/balance_missions.py --missions m01 --seeds 1 2 3` so that perfect play destroys every wave before the
song ends (the harness's `waves` block: every wave `cleared_s` >= 0, killed = total = 56) while beginner and sloppy play
still win and no input loses; four lighter schedules were tried first (the heaviest left 6 of 11 waves standing). The
rows below and in the raw table replace the 31 October rows for mission 1; the other nine missions are unchanged.

## Results (seeds 1 to 6 for perfect and beginner, 1 to 3 for sloppy and none; desktop headless, 31 Oct 2026)

Per mission, every run's sequences passed, defenses alive at the end (built and prebuilt) and the command core's health.

| Mission | perfect | beginner | sloppy | none |
| --- | --- | --- | --- | --- |
| 1 First Watch (rebuilt 2 Nov 2026, seeds 1 to 3) | 3/3 wins; seq 12/12 12/12 12/12; defenses 7/7/7; core 100%/100%/100%; every wave destroyed (56/56) | 3/3 wins; seq 11/12 12/12 11/12; defenses 5/6/5; core 100%/100%/100% | 3/3 wins; seq 8/12 10/12 11/12; defenses 4/5/5; core 100%/100%/100% | 0/3 wins; lost at 37.3 s, 44.5 s, 40.6 s |
| 2 Second Pulse | 6/6 wins; seq 10/10 10/10 10/10 10/10 10/10 10/10; defenses 8/8/8/8/8/8; core 100%/100%/100%/100%/100%/100% | 6/6 wins; seq 10/10 10/10 10/10 10/10 10/10 10/10; defenses 7/7/7/7/7/7; core 100%/100%/100%/100%/100%/100% | 2/3 wins; seq 9/10 10/10 5/10; defenses 6/7/3; core 100%/100%/0%; lost s3 32.6 s | 0/3 wins; lost at 28.4 s, 28.5 s, 28.5 s |
| 3 Hold the Line | 6/6 wins; seq 12/12 12/12 12/12 12/12 12/12 12/12; defenses 5/4/4/4/5/5; core 100%/100%/100%/100%/100%/100% | 6/6 wins; seq 11/12 11/12 12/12 12/12 10/12 11/12; defenses 5/5/5/4/4/5; core 100%/100%/100%/100%/100%/100% | 3/3 wins; seq 8/12 8/12 12/12; defenses 3/5/5; core 100%/100%/100% | 0/3 wins; lost at 39.0 s, 39.1 s, 39.6 s |
| 4 Backbeat | 6/6 wins; seq 12/12 12/12 12/12 12/12 12/12 12/12; defenses 7/8/8/7/7/7; core 100%/100%/100%/100%/100%/100% | 6/6 wins; seq 12/12 11/12 12/12 12/12 12/12 12/12; defenses 8/7/8/8/8/8; core 100%/100%/100%/100%/100%/100% | 3/3 wins; seq 11/12 11/12 9/12; defenses 7/5/5; core 100%/100%/100% | 0/3 wins; lost at 30.1 s, 30.1 s, 30.1 s |
| 5 Counterpoint | 6/6 wins; seq 14/14 14/14 14/14 14/14 14/14 14/14; defenses 5/5/6/5/5/5; core 28%/100%/100%/100%/100%/100% | 6/6 wins; seq 14/14 13/14 14/14 14/14 13/14 14/14; defenses 4/3/4/5/5/6; core 100%/100%/100%/100%/2%/100% | 3/3 wins; seq 12/14 12/14 11/14; defenses 4/5/5; core 10%/80%/82% | 0/3 wins; lost at 33.6 s, 33.6 s, 33.5 s |
| 6 Fortress | 6/6 wins; seq 14/14 14/14 14/14 14/14 14/14 14/14; defenses 5/4/4/6/6/5; core 100%/100%/100%/100%/100%/100% | 6/6 wins; seq 14/14 13/14 14/14 14/14 14/14 14/14; defenses 6/6/6/5/5/5; core 100%/100%/100%/100%/100%/100% | 3/3 wins; seq 13/14 12/14 11/14; defenses 6/3/1; core 100%/40%/70% | 0/3 wins; lost at 55.7 s, 54.8 s, 54.2 s |
| 7 Crossroads | 6/6 wins; seq 16/16 16/16 16/16 16/16 16/16 16/16; defenses 9/9/9/9/9/9; core 100%/100%/100%/100%/100%/100% | 6/6 wins; seq 16/16 15/16 16/16 16/16 16/16 16/16; defenses 9/9/9/9/9/9; core 100%/100%/100%/100%/100%/100% | 3/3 wins; seq 13/16 13/16 9/16; defenses 6/7/2; core 100%/100%/69% | 0/3 wins; lost at 42.6 s, 42.6 s, 41.1 s |
| 8 Crossfire | 6/6 wins; seq 16/16 16/16 16/16 16/16 16/16 16/16; defenses 6/4/7/4/3/3; core 100%/100%/100%/100%/100%/100% | 6/6 wins; seq 16/16 15/16 16/16 16/16 16/16 16/16; defenses 5/7/4/4/4/4; core 100%/100%/100%/100%/100%/100% | 3/3 wins; seq 15/16 15/16 14/16; defenses 6/4/4; core 100%/100%/100% | 0/3 wins; lost at 36.0 s, 36.0 s, 36.0 s |
| 9 Iron Rhythm | 6/6 wins; seq 16/16 16/16 16/16 16/16 16/16 16/16; defenses 5/4/6/5/5/6; core 100%/100%/100%/100%/100%/100% | 6/6 wins; seq 15/16 13/16 15/16 15/16 14/16 15/16; defenses 4/3/6/2/4/4; core 100%/92%/100%/100%/100%/100% | 2/3 wins; seq 13/16 11/16 11/16; defenses 4/2/1; core 100%/0%/93%; lost s2 86.4 s | 0/3 wins; lost at 36.4 s, 36.6 s, 36.3 s |
| 10 Last Light | 6/6 wins; seq 20/20 20/20 20/20 20/20 20/20 20/20; defenses 4/2/2/3/2/3; core 100%/32%/49%/100%/58%/74% | 6/6 wins; seq 20/20 19/20 19/20 19/20 18/20 20/20; defenses 3/2/3/3/2/4; core 32%/57%/7%/85%/18%/99% | 2/3 wins; seq 16/20 14/20 14/20; defenses 4/1/0; core 63%/0%/42%; lost s2 100.7 s | 0/3 wins; lost at 67.5 s, 67.7 s, 67.3 s |

Totals: **perfect 60 of 60 wins, beginner 60 of 60, sloppy 27 of 30, no input 0 of 30** (every no-input run loses,
between 28 and 68 s in). Sloppy loses mission 2 seed 3 (only 5 of 10 sequences passed, the left approach falls at
32.6 s), mission 9 seed 2 (86.4 s of 88.3) and mission 10 seed 2 (100.7 s of 110.3).

Reading them:

- **Missions 1 to 4 teach and forgive**: perfect and beginner keep the core at 100% and end with 5 to 8 defenses
  standing (the brief's 6 to 10 for a good early run: 6 in mission 1, 8 in mission 2; mission 3 also earns units, so
  fewer buildings). Mission 1's first drum sequence builds one pillbox.
- **Missions 5 to 10 press harder**: armour, artillery and V2 launchers wear defenses down, so 2 to 6 defenses are
  left at the end; the core takes damage in mission 10 even with perfect play (32 to 100%). Beginners still win every
  seed run, sometimes narrowly (mission 5 seed 5 ends at 2%, mission 10 seed 3 at 7%).
- **Outcomes are chaotic past mission 5**: one wave changed (mission 5's two flamethrowers to one) moved results of
  other seeds both ways. Treat single seeds as samples, not as a ranking of policies; beginner occasionally beats
  perfect because a different reward order puts a building where the next wave walks.
- **Accuracy never changes the waves**, only what gets built and how fast (sharp 0.5 s, steady 1.5 s, loose 3 s).

## What was tuned (31 October 2026)

1. Waves per mission by bar (`start_bar`), every approach used, first contact after the first sequence's reward.
   Command core hit points as a level rule (60,000 in 1 to 4, rising to 125,000 in mission 10); power plant and radar
   dome become required objectives in 6, 8 and 10, with some waves sent at them.
2. Sockets open per approach rise from 3 (mission 1) to 5 (7 to 10). Prebuilt defenses from mission 6 on compensate
   for long-range enemies arriving before the player has built much.
3. Sandbag walls beside the sockets (cover) from mission 4.
4. Simulation changes (missions only; the duel is unaffected, its tests unchanged):
   - Defenses measure range from their own footprint edge, as their attackers measure to it. Before, a flame tower
     (range 5) never fired at riflemen (range 5) grinding it from 5.6 cells.
   - **Sorties**: a defender may leave its 6-cell leash, up to 16 cells from its point, to attack an enemy that is
     shooting something of ours at that point from beyond the leash (artillery, V2 launchers). Before, they shelled a
     defense point all game unanswered.
   - The reward placement hint is the approach that most enemies are walking towards now, else the next wave's. Before,
     the first reward went to the second wave's approach and the first wave walked in unopposed.
5. After those changes: mission 5's right-hand waves carry one flamethrower instead of two, mission 10's left wave at
   bar 49 brings a medium tank instead of a second mammoth tank, and the cores of missions 5 (80,000 to 90,000) and 10
   (110,000 to 125,000) got more health. That brought beginner from 10 of 12 to 12 of 12 on those two missions over
   seeds 1 to 6.

## Coverage: every ground actor and building

Enemy counts are totals per mission (`3x2` = mission 3, two units). Rewards are sequence rewards per mission.

| Actor | As enemy (mission x count) | As reward (mission x count) | Role and limits |
| --- | --- | --- | --- |
| e1 rifleman | every mission (35 to 50) | 8x1 | the bulk of every wave |
| e2 grenadier | 2x6, 4 to 10 (7 to 10 each) | 4x2, 10x1 | splash against infantry crowds |
| e3 rocket soldier | 3x3, 5 to 10 (2 or 3 each) | 1 to 5, 8 to 10 | anti-armour; the first unit reward (mission 1) |
| e4 flamethrower | 4x8, 5 to 10 (4 to 8 each) | 7x2, 10x1 | heavy against buildings and infantry |
| jeep | every mission (1 to 7) | 3x2, 5x2, 9x1 | fast harasser |
| apc | 4x2, 5, 7 to 10 (1 or 2) | 6x2, 8x1, 10x1 | **gun only**: it carries no troops (the name says "APC (gun only)" in game) |
| 1tnk light tank | 3x2, 5 to 10 | 5x2, 9x1, 10x1 | |
| 2tnk medium tank | 6x3, 7 to 10 | 6 to 10 | |
| 3tnk heavy tank | 8x2, 9x2, 10x1 | none | enemy only |
| 4tnk mammoth tank | 9x1, 10x1 | none | enemy only; the only unit that crushes brick walls |
| arty artillery | 6x2, 8x1, 10x1 | 7x2, 8 to 10 | outranges the defenses; answered by sorties |
| v2rl V2 launcher | 7x2, 8x1, 9x2, 10x2 | none | outranges the defenses; answered by sorties |
| ftrk flak truck | 7x3, 8x1, 10x1 | 7x1, 10x1 | its flak hits ground targets in these rules |

| Building | Use |
| --- | --- |
| fact (construction yard) as **command core** | required objective in every mission; losing it ends the run |
| powr (power plant) | required objective in 6 and 10 (50,000 / 70,000 hp), otherwise scenery that can be destroyed |
| dome (radar dome) | required objective in 8 and 10 (60,000 / 70,000 hp) |
| barr (barracks), weap (war factory) | where rewarded infantry and vehicles come out; the HUD names them only when lost |
| pbox (pillbox) | reward `pillbox`; prebuilt at every approach in 6 and 10, at the top in 8 and 9 |
| gun (gun turret) | reward `turret`; prebuilt at the top in 7 to 10 |
| ftur (flame tower) | reward `flame_tower`, from mission 4 |
| brik (brick wall) | the compound ring of `defense_02.json`; enemies walk through its openings |
| sbag (sandbags) | cover beside the sockets, missions 4 to 10 (`rules.walls`) |
| repair (no building) | reward `repair`, and what any reward becomes at capacity: a repair crew for the most damaged approach, or +50% health once for the oldest defense when nothing is damaged |

Not used, on purpose: `agun` (AA gun) and `sam` (SAM site) only shoot aircraft and there is no air threat, so they
would be decorative; `hpad`, helicopters and air-service rewards are out of scope (brief, section 5); `fix` (service
depot) has art but no unit-repair behaviour in the simulation, so it is not offered rather than offered as a fake;
`tent` (allied barracks) has no art in the extracted set.

## Desktop frame time and sizes

`RW_MISSION=10 RW_SCENE=play RW_AUTOPLAY=perfect`, a real 1280 x 720 window on the development PC (RTX 3060, vsync
60 Hz), mission 10 with its 16 streams, 31 October 2026: 6,608 frames, average 16.7 ms, p95 16.67 ms, 5 frames over
33 ms (maximum 76 ms, during loading), static memory 58.8 MB. A phone has not run it.

| Mission | Bars, seconds | Phases (D drums, B bass) | Sequences | Choices (pick of pool) | Streams at once | Pack (Ogg) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 First Watch | 128, 176.6 s | DDBD BDDB DBDB DDBD | 32 | groove 1/3, bass line 1/2, bass sound 1/9 (5 or 4 fit the line), backing 1/3 | 4 | 27 MB |
| 2 Second Pulse | 40, 55.2 s | DDDDD | 10 | groove 1/2, kick 1/2, snare 1/2 | 5 | 1.2 MB |
| 3 Hold the Line | 48, 66.2 s | DBDBDB | 12 | kick 1/2, snare 1/2, bass voice 1/2 | 6 | 2.0 MB |
| 4 Backbeat | 48, 66.2 s | DDDDDD | 12 | groove 1/2, kick 1/3, snare 1/3 | 5 | 3.3 MB |
| 5 Counterpoint | 56, 77.2 s | DBDBDBD | 14 | groove 1/2, kick 1/3, snare 1/3, bass 1/2, voices 2/3 | 7 | 6.8 MB |
| 6 Fortress | 56, 77.2 s | DDDDDDD | 14 | grooves 2/3, kicks 2/4, snare 1/3 | 8 | 6.8 MB |
| 7 Crossroads | 64, 88.3 s | DBDBDBDB | 16 | groove 1/3, kick 1/4, snare 1/3, bass 2/3, voices 3/4 | 12 | 11.9 MB |
| 8 Crossfire | 64, 88.3 s | DDDDDDDD | 16 | groove 1/3, fill 1/2, kick 1/4, snares 2/4 | 6 | 8.6 MB |
| 9 Iron Rhythm | 64, 88.3 s | DDBDDBDD | 16 | grooves 2/3, fills 2/3, kicks 2/4, snare 1/4, bass 1/3, voices 2/4 | 12 | 11.6 MB |
| 10 Last Light | 80, 110.3 s | DDBDBDBDBD | 20 | grooves 3/3, fills 2/3, kicks 2/3, snares 2/3, basses 2/3, voices 4/5 | 16 | 13.9 MB |

The Ogg files of all ten packs come to 84 MB (every offered combination is pre-assembled; only the selected ones load);
mission 1 alone is 27 MB since its 18 stems run the full 129 bars.

## Not verified

No phone run (frame time, memory, touch feel, the 16-stream mission 10 on a phone CPU, the 27 MB mission 1 pack), no
real stems for missions 2 to 10, no human playtest of any mission, of the difficulty curve or of tapping sections
by hand (the harness taps the suggested section every frame, a person taps rarely), no listening check of the
assembled stems or of the battle sound effects beyond the build's sample-exact placement test. The beginner and
sloppy policies are models of mistakes, not people.

## Raw rows (seeds 1 to 3, all policies)

| Mission | Policy | Seed | Outcome | At | Sequences (sharp/steady/loose) | Built | Units | Repairs | Defenses alive | Core | Enemies killed | Peak units (you / enemy) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 First Watch | perfect | 1 | victory | 66.2 s | 12/12 (12/0/0) | 7 | 5 | 0 | 7 | 100% | 56 | 3 / 29 |
| 1 First Watch | perfect | 2 | victory | 66.2 s | 12/12 (12/0/0) | 7 | 5 | 0 | 7 | 100% | 56 | 3 / 27 |
| 1 First Watch | perfect | 3 | victory | 66.2 s | 12/12 (12/0/0) | 7 | 5 | 0 | 7 | 100% | 56 | 3 / 28 |
| 1 First Watch | beginner | 1 | victory | 66.2 s | 11/12 (1/10/0) | 6 | 5 | 0 | 5 | 100% | 55 | 3 / 28 |
| 1 First Watch | beginner | 2 | victory | 66.2 s | 12/12 (0/12/0) | 7 | 5 | 0 | 6 | 100% | 56 | 3 / 30 |
| 1 First Watch | beginner | 3 | victory | 66.2 s | 11/12 (3/8/0) | 6 | 5 | 0 | 5 | 100% | 54 | 3 / 28 |
| 1 First Watch | sloppy | 1 | victory | 66.2 s | 8/12 (0/4/4) | 5 | 3 | 0 | 4 | 100% | 52 | 2 / 33 |
| 1 First Watch | sloppy | 2 | victory | 66.2 s | 10/12 (0/2/8) | 6 | 4 | 0 | 5 | 100% | 54 | 2 / 31 |
| 1 First Watch | sloppy | 3 | victory | 66.2 s | 11/12 (0/5/6) | 6 | 5 | 0 | 5 | 100% | 50 | 3 / 32 |
| 1 First Watch | none | 1 | defeat | 37.3 s | 0/12 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 0 | 0 / 41 |
| 1 First Watch | none | 2 | defeat | 44.5 s | 0/12 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 0 | 0 / 56 |
| 1 First Watch | none | 3 | defeat | 40.6 s | 0/12 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 0 | 0 / 50 |
| 2 Second Pulse | perfect | 1 | victory | 55.2 s | 10/10 (10/0/0) | 8 | 2 | 0 | 8 | 100% | 31 | 2 / 43 |
| 2 Second Pulse | perfect | 2 | victory | 55.2 s | 10/10 (10/0/0) | 8 | 2 | 0 | 8 | 100% | 29 | 2 / 43 |
| 2 Second Pulse | perfect | 3 | victory | 55.2 s | 10/10 (10/0/0) | 8 | 2 | 0 | 8 | 100% | 29 | 2 / 43 |
| 2 Second Pulse | beginner | 1 | victory | 55.2 s | 10/10 (0/10/0) | 8 | 2 | 0 | 7 | 100% | 31 | 2 / 43 |
| 2 Second Pulse | beginner | 2 | victory | 55.2 s | 10/10 (0/9/1) | 8 | 2 | 0 | 7 | 100% | 30 | 2 / 43 |
| 2 Second Pulse | beginner | 3 | victory | 55.2 s | 10/10 (4/5/1) | 8 | 2 | 0 | 7 | 100% | 31 | 1 / 43 |
| 2 Second Pulse | sloppy | 1 | victory | 55.2 s | 9/10 (0/6/3) | 7 | 2 | 0 | 6 | 100% | 30 | 1 / 43 |
| 2 Second Pulse | sloppy | 2 | victory | 55.2 s | 10/10 (0/3/7) | 8 | 2 | 0 | 7 | 100% | 30 | 2 / 43 |
| 2 Second Pulse | sloppy | 3 | defeat | 32.6 s | 5/10 (0/1/4) | 4 | 1 | 0 | 3 | 0% | 11 | 1 / 33 |
| 2 Second Pulse | none | 1 | defeat | 28.4 s | 0/10 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 0 | 0 / 35 |
| 2 Second Pulse | none | 2 | defeat | 28.5 s | 0/10 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 0 | 0 / 35 |
| 2 Second Pulse | none | 3 | defeat | 28.5 s | 0/10 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 0 | 0 / 35 |
| 3 Hold the Line | perfect | 1 | victory | 66.2 s | 12/12 (12/0/0) | 6 | 6 | 0 | 5 | 100% | 44 | 3 / 32 |
| 3 Hold the Line | perfect | 2 | victory | 66.2 s | 12/12 (12/0/0) | 6 | 6 | 0 | 4 | 100% | 33 | 3 / 35 |
| 3 Hold the Line | perfect | 3 | victory | 66.2 s | 12/12 (12/0/0) | 6 | 6 | 0 | 4 | 100% | 34 | 3 / 34 |
| 3 Hold the Line | beginner | 1 | victory | 66.2 s | 11/12 (1/9/1) | 6 | 5 | 0 | 5 | 100% | 35 | 2 / 32 |
| 3 Hold the Line | beginner | 2 | victory | 66.2 s | 11/12 (0/11/0) | 6 | 5 | 0 | 5 | 100% | 42 | 3 / 32 |
| 3 Hold the Line | beginner | 3 | victory | 66.2 s | 12/12 (1/9/2) | 6 | 6 | 0 | 5 | 100% | 44 | 3 / 32 |
| 3 Hold the Line | sloppy | 1 | victory | 66.2 s | 8/12 (1/3/4) | 5 | 3 | 0 | 3 | 100% | 34 | 1 / 34 |
| 3 Hold the Line | sloppy | 2 | victory | 66.2 s | 8/12 (0/1/7) | 6 | 2 | 0 | 5 | 100% | 41 | 1 / 33 |
| 3 Hold the Line | sloppy | 3 | victory | 66.2 s | 12/12 (1/4/7) | 6 | 6 | 0 | 5 | 100% | 39 | 2 / 35 |
| 3 Hold the Line | none | 1 | defeat | 39.0 s | 0/12 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 0 | 0 / 41 |
| 3 Hold the Line | none | 2 | defeat | 39.1 s | 0/12 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 0 | 0 / 41 |
| 3 Hold the Line | none | 3 | defeat | 39.6 s | 0/12 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 0 | 0 / 41 |
| 4 Backbeat | perfect | 1 | victory | 66.2 s | 12/12 (12/0/0) | 8 | 4 | 0 | 7 | 100% | 49 | 2 / 46 |
| 4 Backbeat | perfect | 2 | victory | 66.2 s | 12/12 (12/0/0) | 8 | 4 | 0 | 8 | 100% | 51 | 2 / 44 |
| 4 Backbeat | perfect | 3 | victory | 66.2 s | 12/12 (12/0/0) | 8 | 4 | 0 | 8 | 100% | 48 | 2 / 45 |
| 4 Backbeat | beginner | 1 | victory | 66.2 s | 12/12 (0/12/0) | 8 | 4 | 0 | 8 | 100% | 41 | 2 / 48 |
| 4 Backbeat | beginner | 2 | victory | 66.2 s | 11/12 (0/11/0) | 8 | 3 | 0 | 7 | 100% | 41 | 2 / 46 |
| 4 Backbeat | beginner | 3 | victory | 66.2 s | 12/12 (2/10/0) | 8 | 4 | 0 | 8 | 100% | 43 | 2 / 47 |
| 4 Backbeat | sloppy | 1 | victory | 66.2 s | 11/12 (0/3/8) | 8 | 3 | 0 | 7 | 100% | 41 | 1 / 52 |
| 4 Backbeat | sloppy | 2 | victory | 66.2 s | 11/12 (0/4/7) | 7 | 4 | 0 | 5 | 100% | 25 | 2 / 52 |
| 4 Backbeat | sloppy | 3 | victory | 66.2 s | 9/12 (0/4/5) | 6 | 3 | 0 | 5 | 100% | 21 | 1 / 49 |
| 4 Backbeat | none | 1 | defeat | 30.1 s | 0/12 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 0 | 0 / 34 |
| 4 Backbeat | none | 2 | defeat | 30.1 s | 0/12 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 0 | 0 / 34 |
| 4 Backbeat | none | 3 | defeat | 30.1 s | 0/12 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 0 | 0 / 34 |
| 5 Counterpoint | perfect | 1 | victory | 77.2 s | 14/14 (14/0/0) | 8 | 6 | 0 | 5 | 28% | 38 | 2 / 27 |
| 5 Counterpoint | perfect | 2 | victory | 77.2 s | 14/14 (14/0/0) | 8 | 6 | 0 | 5 | 100% | 42 | 2 / 27 |
| 5 Counterpoint | perfect | 3 | victory | 77.2 s | 14/14 (14/0/0) | 8 | 6 | 0 | 6 | 100% | 45 | 2 / 26 |
| 5 Counterpoint | beginner | 1 | victory | 77.2 s | 14/14 (1/13/0) | 8 | 6 | 0 | 4 | 100% | 40 | 2 / 29 |
| 5 Counterpoint | beginner | 2 | victory | 77.2 s | 13/14 (1/11/1) | 7 | 6 | 0 | 3 | 100% | 39 | 2 / 29 |
| 5 Counterpoint | beginner | 3 | victory | 77.2 s | 14/14 (1/13/0) | 8 | 6 | 0 | 4 | 100% | 37 | 2 / 30 |
| 5 Counterpoint | sloppy | 1 | victory | 77.2 s | 12/14 (0/4/8) | 7 | 5 | 0 | 4 | 10% | 37 | 2 / 34 |
| 5 Counterpoint | sloppy | 2 | victory | 77.2 s | 12/14 (0/5/7) | 7 | 5 | 0 | 5 | 80% | 37 | 2 / 29 |
| 5 Counterpoint | sloppy | 3 | victory | 77.2 s | 11/14 (0/6/5) | 7 | 4 | 0 | 5 | 82% | 41 | 2 / 28 |
| 5 Counterpoint | none | 1 | defeat | 33.6 s | 0/14 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 0 | 0 / 27 |
| 5 Counterpoint | none | 2 | defeat | 33.6 s | 0/14 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 0 | 0 / 27 |
| 5 Counterpoint | none | 3 | defeat | 33.5 s | 0/14 (0/0/0) | 0 | 0 | 0 | 0 | 0% | 0 | 0 / 27 |
| 6 Fortress | perfect | 1 | victory | 77.2 s | 14/14 (14/0/0) | 8 | 4 | 2 | 5 | 100% | 40 | 3 / 33 |
| 6 Fortress | perfect | 2 | victory | 77.2 s | 14/14 (14/0/0) | 8 | 4 | 2 | 4 | 100% | 37 | 3 / 35 |
| 6 Fortress | perfect | 3 | victory | 77.2 s | 14/14 (14/0/0) | 8 | 4 | 2 | 4 | 100% | 39 | 3 / 34 |
| 6 Fortress | beginner | 1 | victory | 77.2 s | 14/14 (0/14/0) | 8 | 4 | 2 | 6 | 100% | 49 | 3 / 36 |
| 6 Fortress | beginner | 2 | victory | 77.2 s | 13/14 (0/13/0) | 7 | 4 | 2 | 6 | 100% | 46 | 3 / 34 |
| 6 Fortress | beginner | 3 | victory | 77.2 s | 14/14 (1/13/0) | 8 | 4 | 2 | 6 | 100% | 45 | 3 / 34 |
| 6 Fortress | sloppy | 1 | victory | 77.2 s | 13/14 (0/4/9) | 7 | 4 | 2 | 6 | 100% | 62 | 3 / 32 |
| 6 Fortress | sloppy | 2 | victory | 77.2 s | 12/14 (0/2/10) | 7 | 3 | 2 | 3 | 40% | 45 | 2 / 36 |
| 6 Fortress | sloppy | 3 | victory | 77.2 s | 11/14 (0/6/5) | 6 | 3 | 2 | 1 | 70% | 36 | 2 / 40 |
| 6 Fortress | none | 1 | defeat | 55.7 s | 0/14 (0/0/0) | 0 | 0 | 0 | 0 | 77% | 22 | 0 / 39 |
| 6 Fortress | none | 2 | defeat | 54.8 s | 0/14 (0/0/0) | 0 | 0 | 0 | 0 | 72% | 21 | 0 / 34 |
| 6 Fortress | none | 3 | defeat | 54.2 s | 0/14 (0/0/0) | 0 | 0 | 0 | 0 | 83% | 22 | 0 / 34 |
| 7 Crossroads | perfect | 1 | victory | 88.3 s | 16/16 (16/0/0) | 8 | 6 | 2 | 9 | 100% | 55 | 3 / 18 |
| 7 Crossroads | perfect | 2 | victory | 88.3 s | 16/16 (16/0/0) | 8 | 6 | 2 | 9 | 100% | 57 | 3 / 20 |
| 7 Crossroads | perfect | 3 | victory | 88.3 s | 16/16 (16/0/0) | 8 | 6 | 2 | 9 | 100% | 57 | 3 / 19 |
| 7 Crossroads | beginner | 1 | victory | 88.3 s | 16/16 (1/15/0) | 8 | 6 | 2 | 9 | 100% | 57 | 3 / 20 |
| 7 Crossroads | beginner | 2 | victory | 88.3 s | 15/16 (2/13/0) | 8 | 5 | 2 | 9 | 100% | 60 | 3 / 24 |
| 7 Crossroads | beginner | 3 | victory | 88.3 s | 16/16 (2/14/0) | 8 | 6 | 2 | 9 | 100% | 58 | 4 / 19 |
| 7 Crossroads | sloppy | 1 | victory | 88.3 s | 13/16 (0/8/5) | 8 | 3 | 2 | 6 | 100% | 57 | 2 / 22 |
| 7 Crossroads | sloppy | 2 | victory | 88.3 s | 13/16 (0/8/5) | 6 | 6 | 1 | 7 | 100% | 64 | 4 / 24 |
| 7 Crossroads | sloppy | 3 | victory | 88.3 s | 9/16 (0/1/8) | 5 | 3 | 1 | 2 | 69% | 41 | 2 / 29 |
| 7 Crossroads | none | 1 | defeat | 42.6 s | 0/16 (0/0/0) | 0 | 0 | 0 | 1 | 0% | 3 | 0 / 36 |
| 7 Crossroads | none | 2 | defeat | 42.6 s | 0/16 (0/0/0) | 0 | 0 | 0 | 1 | 0% | 3 | 0 / 36 |
| 7 Crossroads | none | 3 | defeat | 41.1 s | 0/16 (0/0/0) | 0 | 0 | 0 | 1 | 0% | 3 | 0 / 36 |
| 8 Crossfire | perfect | 1 | victory | 88.3 s | 16/16 (16/0/0) | 8 | 5 | 3 | 6 | 100% | 64 | 4 / 25 |
| 8 Crossfire | perfect | 2 | victory | 88.3 s | 16/16 (16/0/0) | 8 | 5 | 3 | 4 | 100% | 59 | 3 / 26 |
| 8 Crossfire | perfect | 3 | victory | 88.3 s | 16/16 (16/0/0) | 8 | 5 | 3 | 7 | 100% | 65 | 3 / 27 |
| 8 Crossfire | beginner | 1 | victory | 88.3 s | 16/16 (0/16/0) | 8 | 5 | 3 | 5 | 100% | 64 | 4 / 27 |
| 8 Crossfire | beginner | 2 | victory | 88.3 s | 15/16 (1/14/0) | 8 | 4 | 3 | 7 | 100% | 62 | 3 / 28 |
| 8 Crossfire | beginner | 3 | victory | 88.3 s | 16/16 (2/14/0) | 8 | 5 | 2 | 4 | 100% | 54 | 3 / 26 |
| 8 Crossfire | sloppy | 1 | victory | 88.3 s | 15/16 (0/5/10) | 7 | 5 | 2 | 6 | 100% | 66 | 4 / 22 |
| 8 Crossfire | sloppy | 2 | victory | 88.3 s | 15/16 (0/5/10) | 7 | 5 | 3 | 4 | 100% | 62 | 3 / 26 |
| 8 Crossfire | sloppy | 3 | victory | 88.3 s | 14/16 (0/5/9) | 6 | 5 | 3 | 4 | 100% | 59 | 3 / 25 |
| 8 Crossfire | none | 1 | defeat | 36.0 s | 0/16 (0/0/0) | 0 | 0 | 0 | 2 | 0% | 5 | 0 / 30 |
| 8 Crossfire | none | 2 | defeat | 36.0 s | 0/16 (0/0/0) | 0 | 0 | 0 | 2 | 0% | 5 | 0 / 30 |
| 8 Crossfire | none | 3 | defeat | 36.0 s | 0/16 (0/0/0) | 0 | 0 | 0 | 2 | 0% | 5 | 0 / 30 |
| 9 Iron Rhythm | perfect | 1 | victory | 88.3 s | 16/16 (16/0/0) | 8 | 5 | 3 | 5 | 100% | 61 | 3 / 28 |
| 9 Iron Rhythm | perfect | 2 | victory | 88.3 s | 16/16 (16/0/0) | 8 | 5 | 3 | 4 | 100% | 62 | 3 / 31 |
| 9 Iron Rhythm | perfect | 3 | victory | 88.3 s | 16/16 (16/0/0) | 8 | 5 | 3 | 6 | 100% | 59 | 3 / 30 |
| 9 Iron Rhythm | beginner | 1 | victory | 88.3 s | 15/16 (0/15/0) | 8 | 4 | 3 | 4 | 100% | 54 | 2 / 32 |
| 9 Iron Rhythm | beginner | 2 | victory | 88.3 s | 13/16 (0/13/0) | 7 | 3 | 3 | 3 | 92% | 48 | 2 / 33 |
| 9 Iron Rhythm | beginner | 3 | victory | 88.3 s | 15/16 (1/14/0) | 8 | 4 | 3 | 6 | 100% | 54 | 2 / 33 |
| 9 Iron Rhythm | sloppy | 1 | victory | 88.3 s | 13/16 (0/6/7) | 8 | 2 | 3 | 4 | 100% | 46 | 1 / 32 |
| 9 Iron Rhythm | sloppy | 2 | defeat | 86.4 s | 11/16 (0/2/9) | 7 | 1 | 3 | 2 | 0% | 50 | 1 / 30 |
| 9 Iron Rhythm | sloppy | 3 | victory | 88.3 s | 11/16 (1/5/5) | 5 | 4 | 2 | 1 | 93% | 58 | 2 / 26 |
| 9 Iron Rhythm | none | 1 | defeat | 36.4 s | 0/16 (0/0/0) | 0 | 0 | 0 | 2 | 0% | 5 | 0 / 30 |
| 9 Iron Rhythm | none | 2 | defeat | 36.6 s | 0/16 (0/0/0) | 0 | 0 | 0 | 2 | 0% | 5 | 0 / 30 |
| 9 Iron Rhythm | none | 3 | defeat | 36.3 s | 0/16 (0/0/0) | 0 | 0 | 0 | 2 | 0% | 5 | 0 / 30 |
| 10 Last Light | perfect | 1 | victory | 110.3 s | 20/20 (20/0/0) | 8 | 8 | 4 | 4 | 100% | 63 | 4 / 26 |
| 10 Last Light | perfect | 2 | victory | 110.3 s | 20/20 (20/0/0) | 8 | 8 | 4 | 2 | 32% | 60 | 3 / 29 |
| 10 Last Light | perfect | 3 | victory | 110.3 s | 20/20 (20/0/0) | 8 | 8 | 4 | 2 | 49% | 59 | 3 / 26 |
| 10 Last Light | beginner | 1 | victory | 110.3 s | 20/20 (0/19/1) | 8 | 8 | 4 | 3 | 32% | 68 | 3 / 29 |
| 10 Last Light | beginner | 2 | victory | 110.3 s | 19/20 (2/16/1) | 8 | 7 | 4 | 2 | 57% | 50 | 3 / 29 |
| 10 Last Light | beginner | 3 | victory | 110.3 s | 19/20 (3/16/0) | 8 | 7 | 4 | 3 | 7% | 63 | 3 / 30 |
| 10 Last Light | sloppy | 1 | victory | 110.3 s | 16/20 (0/8/8) | 8 | 4 | 4 | 4 | 63% | 67 | 2 / 24 |
| 10 Last Light | sloppy | 2 | defeat | 100.7 s | 14/20 (0/6/8) | 8 | 4 | 2 | 1 | 0% | 54 | 2 / 25 |
| 10 Last Light | sloppy | 3 | victory | 110.3 s | 14/20 (0/8/6) | 6 | 4 | 4 | 0 | 42% | 55 | 2 / 26 |
| 10 Last Light | none | 1 | defeat | 67.5 s | 0/20 (0/0/0) | 0 | 0 | 0 | 2 | 0% | 28 | 0 / 33 |
| 10 Last Light | none | 2 | defeat | 67.7 s | 0/20 (0/0/0) | 0 | 0 | 0 | 1 | 0% | 28 | 0 / 33 |
| 10 Last Light | none | 3 | defeat | 67.3 s | 0/20 (0/0/0) | 0 | 0 | 0 | 2 | 0% | 28 | 0 / 33 |
