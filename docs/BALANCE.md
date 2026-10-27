# Balance evidence (acceptance A08, A12)

Method: `tools/balance.sh <pack> <enemy_fraction> <policies...>` runs `tools/autoplay.gd`, a headless harness that
drives `Match` (judgement, enemy schedule and battle simulation; no audio, no rendering) with a scripted input
policy at 60 Hz against the pack's authored enemy events. Policies: `perfect` hits every note on time;
`accuracy:<f>` hits each note with seeded probability f; `none` never presses. `enemy_fraction` keeps a seeded subset
of the authored enemy events (1.0 = the pack as authored). All runs on 27 Oct 2026, seed 1, simulation at 25 ticks/s.

## Level 01 "First Contact" (64 bars, 88.3 s, 321 player notes)

Chosen schedule: `--enemy-profile ramp --enemy-start 0.5 --enemy-end 0.9` (230 of 321 events; per section
intro 52%, build 57%, drop_1 65%, breakdown 73%, drop_2 80%, finale 88%). Baked into `songs/level_01/level.json`.

| Player policy | Outcome | Time | Player built (tanks/infantry/aircraft) | Enemy built | Peak live units P/E |
| --- | --- | ---: | --- | --- | --- |
| perfect | victory | 68.7 s | 105 / 420 / 7 | 65 / 230 / 13 | 126 / 15 |
| accuracy 0.85 | victory | 81.8 s | 109 / 460 / 12 | 85 / 315 / 24 | 129 / 15 |
| accuracy 0.70 | defeat (song end, both bases intact) | 88.3 s | 94 / 430 / 6 | 97 / 405 / 8 | 19 / 73 |
| accuracy 0.50 | defeat (song end, player factory lost) | 88.3 s | 65 / 270 / 13 | 97 / 405 / 8 | 18 / 103 |
| none | defeat (main base destroyed) | about 40 s | 0 | | |

Consistently accurate play wins before the track ends; sustained misses lose (A12). The enemy never reacts to the
player: its events are the authored list, skipped when a producer is dead or the air wing is capped (A08; see
`tests/test_match.gd` for the once-and-in-order proof).

## Alternatives measured

| Schedule | perfect | 0.85 | 0.70 | 0.50 |
| --- | --- | --- | --- | --- |
| mirror 0.85 (first draft) | stalemate | stalemate | stalemate | loss 58 s |
| mirror 0.72 | stalemate | stalemate | loss 86 s | loss 55 s |
| ramp 0.6 to 0.95 | stalemate (enemy base at 25%) | stalemate | stalemate | loss 71 s |
| ramp 0.4 to 0.85 | win 80 s | win 73 s | stalemate (factory lost) | loss 65 s |
| **ramp 0.5 to 0.9** | **win 69 s** | **win 82 s** | stalemate | stalemate (factory lost) |

Runtime subsets of the mirror schedule (`enemy_fraction`): 0.55 to 0.70 win for every accuracy from 0.6 up;
0.75 and above stalemate for everyone. The transition is sharp because both armies grind in the middle until one
side reaches a critical mass, which then rolls through; the ramp profile hands the player that mass early and
makes the enemy catch up only if the player stops producing.

## Simulation rules that shaped the result

- Units engage only what is already inside weapon range (units first, then defences, then buildings; walls only
  when stuck against them) and otherwise march straight ahead in their own row, so a wider army forms a wider
  front instead of converging on one point.
- Units keep rolling forward while shooting enemy units (fire on the move) and stand still only to siege
  buildings; without this both fronts stopped at weapon range and only the first row ever fired.
- Spawn exits are inside the wall line, so attackers must pass the gap and the turrets to reach the producers.
- Anti-air is one SAM site per base, placed deep (covers roughly the enemy half); the ZSU-23 gun's 10-cell range
  made the whole midfield a no-fly zone and was dropped from the layout (the actor and its rules remain available).

## Known tuning items

- A larger army sometimes wins later than a smaller one (ramp 0.4 to 0.85: perfect 80 s, 0.85 accuracy 73 s)
  because the crowd jams in the wall gap; a wider gap or stronger separation would smooth this.
- Air: 72 bass actions but only 5 to 24 aircraft per run; most actions find the wing busy (sorties take about
  30 s including a 16 s rearm). That is by design (no banking of sorties), but the pad count and rearm delay are
  the levers if air should matter more.
- Repair at Red Alert scale costs about 1 credit per 700 HP step, so the 5,000-credit budget never runs out in a
  song; the budget is a PRD tunable.
