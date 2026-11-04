# Plan for review: the continuous run, the Deathtrap Dungeon and new music on the 2.5D game

Status: DRAFT for the owner's review, 2026-11-04. Nothing here is built yet. Written against `main` at `1a4745a2` (the 2.5D polish) and the
branches `feature/continuous-story-run` and `feature/deathtrap-opening` (both cut from `5e1250a2`, the pre-polish `main`).

## 1. What the branches hold

`feature/deathtrap-opening` contains all of `feature/continuous-story-run` plus three dungeon commits, so it is the one to integrate. A trial
merge against the current `main` is clean (no conflicts). What it brings:

| Piece | What it is | State |
| --- | --- | --- |
| **Continuous run** (`src/run/`, `content/run/run.json`, `content/story/music.json`) | The story as one endless run: 64-beat phases at 174 BPM, drums alone then bass revealed by good play, a route choice in the last block (two arrows, a marked default), crowd energy as the survival meter, seven nodes over the five worlds (Warehouse > Mothership or Underworld > Hospital or Ward > the two "late" worlds that loop). Home screen becomes Play / Start from a reached level / Settings. Old chapter saves migrate. | Built, tested headless and recorded, screenshots. Never played by hand or on a phone. |
| **Beat Shaper import** (`tools/content/beatshaper.py`, `docs/MUSIC_IMPORT.md`, `docs/MUSIC_HANDOFF.md`) | One command imports a Drums/Bass/Synth WAV+MIDI set, measures its tempo (87 or 174 BPM profiles), cuts a loop, derives kick/snare and bass-hold cues in four difficulty tiers, assigns it to a level. A hand-off sheet says what to export per level. | Built, tested. |
| **Recorded packs** (`songs/packs/`) | Lv1 Warehouse, Lv1 Warehouse (1), Lv2 Alien Spaceship, Lv2 Alien Spaceship (2). Only the Warehouse and the Mothership play their own music; the Underworld, Hospital, Ward and late levels play stand-ins with filter/distortion/reverb treatments marked temporary. | Four more exports were rejected by the importer (bass out of line, wrong drum notes). |
| **Deathtrap Dungeon** (`src/trial/`, `content/trial/`, `assets/trial/`) | A gamebook dungeon entered from a wizard in the Warehouse: all 400 passages, four bars to choose per passage with a default, every choice is a rhythm phrase on the pads, fights are harder phrases (three losses end it), luck tests, 12 deaths, victory at 400. The music never stops. | Built and tested, but presented as a flat illustrated screen with placeholder pixel pictures, not in the 2.5D world. 28 passages are book-verified, 217 come from a noisy OCR graph, 155 are invented bridges. Text is original summaries. |

What the branches **lose** against the polished `main`: the run keeps the 2.5D worlds, crowds and pads but drives only one `player_move` per
level and a role; the chapter mode's performance-driven rails (dancer > stage > balcony > booth, or corridor > cubicle), the 23 activities by
mood, the glances in every block and the three endings per chapter are not used by the run. The run also hides the chapter mode and the
military campaign from the home screen (they stay in the repo).

## 2. The design calls I need from you

1. **Which game is the front door?** The run branch replaces the chapter campaign on the home screen. My recommendation: the run is the main
   game, but it must inherit the chapters' rail journeys and activities (section 4, WP-A3), and the chapter mode stays as "Story chapters" under
   Play rather than being hidden, because its endings and cutscenes are finished work.
2. **The dungeon's look.** Today it is a flat picture with floating text. Options: (a) keep it flat but with proper illustrations; (b) bring it into
   the 2.5D engine: each zone a small Doom-style map (crystal tunnel, galleries, Throm's pit, the vaults, the mirror gallery, Igbut's door), the
   camera on rails through it, creatures as pixel figures from the wardrobe system, choices as doors or paths you look at. I recommend (b): it is
   the same engine and pipeline, and it is what makes it part of this game rather than a bolt-on. Cost: about the size of two chapters.
3. **The dungeon's music.** It plays a Warehouse stand-in through a filter. It needs its own set (or two: ambient and fight). Can you export one?
4. **Deathtrap Dungeon is Ian Livingstone's book.** The branch avoids copying its text (original summaries, structure only) and uses the owner's
   earlier adaptations. For a game you release, the structure and names (Throm, Igbut, Bloodbeast, Sukumvit, the gems and the lock) are still
   the book's. Decide now whether this stays a private homage or gets renamed into an original "death trap dungeon" with your own creatures,
   zones and ending. The engine does not care; the content files do, and renaming is cheapest before more passages are written.
5. **Which 400?** Only 28 passages are verified and 155 are invented bridges. For a playable product I recommend a curated dungeon of about
   60 to 80 passages (the 28 verified plus hand-written ones along the zone spine), each with a real scene, rather than 400 of unequal quality.
6. **Music supply.** The hand-off sheet needs 4 chart sets plus 3 optional alternate renders to replace every stand-in, plus one or two for the
   dungeon. Four earlier exports were rejected. Do you want the importer loosened (bass placement by MIDI alone when the audio detector
   disagrees) or will you re-export?

## 3. The target, in one paragraph

One game from the home screen: a continuous run through the five 2.5D worlds in which the music builds as you play well, the camera carries you
up or away on rails as it does in the chapters, the crowd behaves to the room and mood, and the route choice at the end of each phase is a
door you walk through. In the Warehouse a wizard offers the Trial: a Doom-style dungeon of its own zones and creatures, played on the same
pads with the same clock, four bars to choose at every passage, where death or victory returns you to the floor. Every level and the dungeon
play the owner's own recorded music through the one import command, with tiers of difficulty that rise with depth.

## 4. Work packages (Sonnet builds, Opus polishes, as before)

### WP-A Integrate the run on the polished main (branch `feature/run-on-25d`)
- A1 Merge `feature/deathtrap-opening` into a branch from `main`; run the full suite, the run recordings and the chapter walk-through; fix what the
  polish changed under the run (figure sheets, light sources, activities, settings). Keep both entry points reachable from home (call 2.1).
- A2 Music assignment check: every node plays, the Warehouse and Mothership on their own packs; the stand-ins labelled in the HUD's debug view.
- A3 **Rails and activities in the run.** Each run node gets a journey authored on the phase engine's events instead of the chapter decisions: at
  each block boundary a pass or hold moves the camera one step along the node's good rail (Warehouse: floor > steps > stage > balcony > booth) or
  back along its bad rail (floor edge > corridor > cubicle), with the queasy look and the sick beat on sustained holds; the route arrows become
  doors or paths in the room, lit when the window opens; the world swap is a walk through the door on the downbeat (the passage frame), not a
  flash. Glances and in-room walks in every block as the chapters have. Activities by mood band already follow energy, so they work unchanged.
- A4 Playtesting: the policy matrix on the run (perfect, accuracy 0.9 to 0.5, sloppy, none; seeds 1 to 3) asserting survival, depth reached and
  the rails taken; a run walk-through script through all seven nodes on the real scenes; screenshots per node and rail stop; frame numbers.

### WP-B The dungeon in 2.5D (branch `feature/dungeon-25d`)
- B1 Content decision applied (calls 2.4 and 2.5): the curated passage list, renamed or not, with a scene id per zone and a creature per fight.
- B2 Zone maps in the map format (`content/story/maps/dungeon_<zone>.json`): crystal entrance tunnel, the footprint galleries, the pit with a
  rope descent, the lower route, the trialmaster's chamber, the idol cavern, the drowned grotto, the vaults, the service tunnels, the mirror
  gallery, the lair, the grub tunnels, the troglodyte cavern, the manticore gate, Igbut's door with the three-gem lock, daylight. Each distinct
  in footprint, height and light per the art brief, with the choice points as visible exits.
- B3 `trial_play` on the 2.5D stage: the camera on rails between choice points; the four-bar window shows the choices as lit exits plus the
  floating labels (keep the labels, phones need the touch targets); a pass walks through; a fail holds at the spot; fights put the creature in the
  room as a pixel figure with win and loss poses; deaths and the victory as tableaux; return to the Warehouse by the passage frame.
- B4 Dungeon figures: creatures and the wizard through the wardrobe and sheet bake (an original bestiary if renamed); the player's hands are not
  shown (Doom shows a weapon; we show nothing or the pads).
- B5 Tests: the existing 19 trial tests ported; the four-bar window and default on the new scene; the dungeon walk-through by defaults (1 to 400
  or the curated end) on the real scene; screenshots per zone.

### WP-C Music (ongoing, each new export is one commit)
- C1 Importer hardening against the four rejected exports: a report that says exactly which bass notes failed and why; a `--trust-midi` mode that
  charts from the MIDI when the audio detector cannot place a wobbling bass (with a warning in `validate`), and `--kick`/`--snare` auto-detection
  from the most common low and mid notes.
- C2 The hand-off sheet regenerated for the run plus the dungeon (ambient and fight sets) and, if the chapters stay reachable, the chapters.
- C3 For every set you export: import, assign, validate, a scripted run on the node, a recording check, commit. Alternate renders for siblings
  where you provide them; treatments only as labelled stand-ins.
- C4 Tiers by ear: once real sets are in, a tuning pass of the four difficulty tiers (density, holds) against perfect and sloppy autoplay, so depth
  4 is hard but survivable.

### WP-D Opus polish
Dungeon zones to the art brief (dense dithered stone, torchlight pools, crystal glow, the mirror gallery's reflections, the lair's blood, daylight at
the end), the creatures, the choice-door lighting, the route windows in the five worlds, before/after sheets per zone.

### WP-E Release checks
A phone export and a by-hand play of one run and one dungeon trip on a device; memory of the sheets; calibration; the handover rewritten
around the run as the game.

## 5. Order and rough size

| Package | Depends on | Size (agent sessions) |
| --- | --- | --- |
| WP-A | your call 2.1 | 2 |
| WP-C1, C2 | nothing | 1 |
| WP-B | calls 2.2, 2.4, 2.5 | 3 |
| WP-C3, C4 | your exports | 1 per 2 to 3 sets |
| WP-D | WP-B | 1 to 2 |
| WP-E | all | 1 |

WP-A and WP-C1/C2 can start as soon as you answer 2.1; the dungeon waits on 2.2, 2.4 and 2.5.

## 6. Risks
- The run's phase engine and the chapters' director are two schedulers over the same stage; A3 must not run both. The run owns the stage in run
  mode; the director only in chapter mode.
- The dungeon's book-derived structure (2.4) is a rights question only you can settle; everything else in this plan is engine work.
- Frame time: a second scheduler and door lighting add little, but the dungeon zones are more maps with sheets; keep the 16 ms ceiling.
- Music: everything beyond the Warehouse and Mothership is a stand-in until you export; the game will sound like two songs until then.
