# The Bassment

The wizard in the Warehouse runs a trial in the cellars under the club: a gamebook-style dungeon, played on the same four pads, the same clock and the same music as the run. It is an original
dungeon (63 passages in 16 zones, 10 creatures, 3 items, one victory) and it is **in the 2.5D world of the rest of the game**: each zone is a small Doom-style map on the story engine, the camera
walks on rails between the passages' places, the choices are lit exits in the room, the creatures stand in the room, and entering and leaving are **seamless**: no scene change, no audio gap, no
clock reset. **Only a death, three lost fight phrases, the victory or the back key lead back to the Warehouse.** This file is the single document for it. `assets/trial/PROVENANCE.md` says what is
in the repository and where it came from.

## Launch

```
godot --path .                      # Play; in the Warehouse level a wizard stands at the left edge with a floating "Enter the Trial"
godot --path . res://src/trial/trial_play.tscn          # straight into the dungeon (hands over to the run scene, which hosts the dungeon)
RW_TRIAL_START=12 godot --path . res://src/trial/trial_play.tscn       # start at any passage (12 the eel, 13 a death, 59 the Echo, 63 the victory)
RW_TRIAL_BOT=perfect RW_TRIAL_CHOICES=d,d,1,0 godot --path . res://src/trial/trial_play.tscn   # scripted: the picks made in each window in turn
bash tools/trial/walk_trial.sh      # scripted, headless: Warehouse > wizard > hatch > the default walk to the victory > back up into the Warehouse (isolated save)
bash tools/trial/capture.sh         # a screenshot per zone and docs/shots/trial/contact_bassment.jpg
godot --headless --path . -s tools/trial/validate.gd                    # check the data (passages, graph, zone maps, waypoints, exits)
godot --headless --path . -s tools/trial/check_maps.gd [-- zone ...]    # check the zone maps and layouts one by one
godot --headless --path . -s tests/run_tests.gd -- --filter trial       # the tests
```

Bots: `perfect` plays every cue, `none` plays nothing, `no_fights` plays every cue except a fight's. `RW_TRIAL_CHOICES` is the pick made in each window in turn (an index, or `d` / empty for
no pick, so the default applies). `RW_TRIAL_UNTIL=<passage>` with `RW_STORY_QUIT=1` quits when that passage is shown. In the run scene: `RW_TRIAL_ENTER=1` chooses the wizard at once,
`RW_TRIAL_LEAVE_AT=<song s>` presses the back key then, `RW_TRIAL_TRACE=1` prints every passage.

## The seamless entry and exit

`RunPlay` hosts the dungeon (`trial_scene.gd` is a child of it); the clock, `RunAudio`, the pad strip and the judge never restart.

* Choosing **Enter the Trial** (only in the Warehouse, up to beat 44 of its phase) arms the entry. The dungeon's pack is requested on a thread (`RunAudio.preload_pack`); the Service Hatch
  stage was built while the level loaded. On the **next cue-free guard** (beat 12.75 of a block) the camera is sent to the `hatch` waypoint of the Warehouse map (the staff door at the end of the
  toilet corridor, reachable from the floor) with a `player_move` that lasts until the entry.
* One block later, on the following guard, **the dungeon takes the pads**: the trial engine charts its first block, the pad strip and note lane are re-bound to its level, the run engine is
  frozen (its crowd energy is kept) and the run's rail actions stop.
* On the **downbeat** after that the passage frame has closed on the hatch (two beats earlier) and opens in the Service Hatch; `RunAudio` gets a `phase_start` for the dungeon's pack on that
  downbeat exactly as for a world swap, so the Warehouse group fades and the dungeon group enters on the same grid. From then on the trial engine owns the pads inside the run scene.
* Leaving (a death, the victory, three lost fight phrases, or the back key, which asks to leave at the next decision tick) is the same walk in reverse: the camera walks to the exit of the
  last place, the frame closes, and on the next downbeat of the dungeon's grid it opens on the Warehouse at the hatch; the Warehouse pack re-enters on that downbeat, `RunEngine.resume` begins a
  fresh phase (energy preserved, phase count carried on) and the camera walks back to the floor.

## How it plays

* **Warehouse.** The wizard (`assets/trial/art/wizard.png`) waits at the left of the stage with a floating **Enter the Trial**, only in the Warehouse level. Ignoring it changes nothing:
  the run goes on by its ordinary routes. Choosing it walks into the dungeon (see above).
* **The music game never stops.** Cues fall on the four pads the whole time, in 16-beat blocks (four bars) on the same clock, packs and judge as the run. Nothing pauses for reading
  or choosing.
* **A passage.** The camera stands in the passage's place in its zone map, the title and two to four sentences appear over the room, the choices **float** at the right (big touch targets, keys 1
  to 4) and each is also **lit in the room as a numbered exit** (a door, a ladder foot, a gap, the water's edge, a seam) where it lies; a footer names the zone and the items you carry.
  The only inputs are the choices and the pads (the system back key leaves the dungeon; it is not a game input).
* **Four bars to choose.** When a passage appears its choices float for exactly four bars, with a bar showing the time left. One choice is marked `[DEFAULT]`. Tap another to pick it (tap
  again to change your mind, up to the last beat). When the four bars end the game moves on with your pick, or with the default if you picked nothing. A choice that needs an item you do
  not hold is not shown.
* **The phrase.** A committed choice is played as the next block of cues: a drums or bass phrase of the tier its data names. Between the choices and the phrase the music and the pads carry
  on without a break.
* **A pass** walks through the chosen exit (the head turns to it when the choice is committed), shows the consequence line and opens a new four-bar window at once; if the next passage is in
  another zone the passage frame closes on the exit and opens on the new zone on the next downbeat. **A failed phrase** keeps you where you stand with a stumble (the queasy look, a glance) and
  the same choices; the one you failed reads "Try again: ..." and is now the default, so doing nothing retries it. Retry as often as you like.
* **A fight** puts the creature in the room as a billboard figure in front of the camera (idle, attack and struck poses), plays the harder phrase, then an outcome: a win shows the struck pose and
  the creature sinks and fades; a loss is a lunge in the attack pose, a red flash and the stumble. **Three lost phrases in the same
  fight end the trial** (the creature's own defeat text, then the Warehouse).
* **A luck test** is one phrase with no second go: a pass goes one way, a miss the other (a setback that rejoins, or a death).
* **Items and secrets.** Three items can be found (the brass lamp, the GUEST LIST token, the silver tuning fork). Each makes a choice appear somewhere else: a shortcut past the Fungus Farm,
  a way past the bouncer without a fight, a hidden seam past the gargoyle. The footer lists what you carry.
* **Death and victory** are the tableaux: a death shows YOU DIED, the camera looks down and the lights go out in a slow fade, with one choice, "Wake in the Warehouse" (also the default); the
  victory is the dawn car park, a flash of daylight settling to warm light, with the same one choice. Then the walk back up the hatch.

### The timeline

```
block:        0 (ambient)            1 (phrase)             2 (ambient)             3 (phrase)
beats:   -3.25   12.75 | 16 ............ 28.75 | 32 ............ 44.75 | 48 ...
             window 1 ->|  result? <- window 2 opens at the result      -> commit ...
```

Every 16 beats, at beat 12.75 of a block, the engine ticks: after a phrase it judges it and opens a four-bar window on the passage that results; after an ambient block it closes the
window and commits the pick or the default. The first window opens in the count-in so that it too is four bars. `src/trial/trial_engine.gd` is this, with no nodes, driven by song time.

## The zones

Sixteen places in order of depth; the tier (1 to 4) is how busy the background cues are and rises with depth. The default walk crosses 13 of them in 30 passages.

| Zone | Tier | What it looks like | Passages |
| --- | --- | --- | --- |
| The Service Hatch | 1 | A rusted hatch and a ladder behind the cloakroom, chalk marks on the brick. | 1, 2, 3 |
| The Cable Run | 1 | A low tunnel hung with humming cables and spitting junction boxes. | 4 to 7 |
| Lost Property | 1 | A cramped cloakroom heaped with orphaned coats, lit by one brass lamp. | 8, 9 |
| The Flooded Boiler Room | 1 | Black water under dripping pipes, steam, and a crackling shape below. | 10 to 14 |
| The Crystal Stacks | 2 | A cavern of glowing crystal columns stacked like speaker towers. | 15 to 18 |
| The Barrel Cellar | 2 | Barrels, bones and a ruined bar under low brick arches. | 19 to 25 |
| The Fungus Farm | 2 | Terraces of luminous mushrooms around a green pool. | 26 to 29 |
| The Mirror Mezzanine | 3 | A long gallery of tall mirrors that show strangers dancing. | 30 to 34 |
| The Reverb Pit | 3 | A black shaft where every sound returns late, with a rope and a ledge. | 35 to 39 |
| The Vault of Records | 3 | Stone shelves of ancient records and a bouncer's velvet rope. | 40 to 42 |
| The Rat King's Warren | 3 | Gnawed tunnels and a throne of speaker foam. | 43 to 47 |
| The Furnace Kitchens | 4 | Red-hot ovens, swinging pots and an imp in a chef's hat. | 48 to 51 |
| The Hall of Hands | 4 | Rows of stone statues with raised palms, hushing a crowd. | 52 to 56 |
| The Resonance Door | 4 | A round iron door with a speaker grille, humming one low note. | 57, 58 |
| The Echo Chamber | 4 | A perfectly round, bare room that returns every sound as a person. | 59, 60 |
| The Dawn Stair | 4 | A spiral stair climbing to grey light, and a door with a push bar. | 61 to 63 |

```
hatch 1 ─┬─> ladder 3 ─┬─> cable run 4 ─> live junction 5 ─> cable nest 7 ───────┐   (5: dash under the sparks, a luck test, skips 7)
         └─ chalk 2 ──┘ │      └─ Lost Property 8 ─> (moth fight) lamp 9          │
                        └─> warm stairs 10 ─> boiler room 12 (eel) ─> 14 ────────┴─> Crystal Stacks 15 ─> hall 16 ─> cellar 19 ─> 20 (knight) ─> 23
  23 ─> trapdoor ─> Fungus Farm 26 ─> 28 (Mildew Mother) ─> 29 ──┐                       └ lamp: the dark corridor 24, 25 ────────────┤
                                                                 └─> Mirror Mezzanine 30 ─> 32 (twin) ─> 34 ─> Reverb Pit 35 ─> ledge 37 ─> Vault 40 (bouncer) ─> 42
  42 ─> Squeaking Stair 43 ─> Rat King 45 ─> 47 ─┐        (or the hot door ─> Furnace Kitchens 48, imp ─> 51) ─┘
  47/51 ─> Hall of Hands 52 ─> gargoyle 55 ─> Resonance Door 57 (luck, held note) ─> Echo Chamber 59 (the Echo) ─> Dawn Stair 61 ─> Last Landing 62 ─> Daylight 63
```

### Creatures and characters

Lampmoth (Lost Property), Cable Eel (boiler room), Barrel Knight (cellar), Mildew Mother (fungus farm), Mirror Twin (mezzanine), Gristle the Bouncer (vault), the Rat King (warren),
Furnace Imp (kitchens), Hushing Gargoyle (hall), the Echo (final test), and the wizard, who waits at the top.

### The final test

There is no lock to open. The **Resonance Door** wants a note *held*, not hit (a bass hold, a luck test that can be retried by failing back to it); behind it the **Echo** copies every phrase
and must be out-played in the hardest fight phrase. Standing still is the one wrong answer (passage 60, a death), as the chalk on the first wall warns. The victory is the dawn car park and the
wizard's sandwich.

## Where to add the next passage

Everything about the dungeon lives in `content/trial/passages.json`. A passage:

```json
"37": {
  "title": "The Rope Ledge",
  "zone": "pit",                            // an id from "zones" (name, one-line look, tier, scene)
  "scene": "pit",                           // an id from "scenes" (a 1280x720 file under assets/trial/scenes/)
  "kind": "normal",                         // normal | death | victory
  "tier": 3,                                // 1 to 4, equal to its zone's tier (the validator checks), rising with depth
  "text": "Two to four sentences of description.",
  "side": true, "secret": true,             // optional labels (counted by the validator): a detour that rejoins; a passage behind an item or a risk
  "grants": ["fork"],                       // optional: items picked up on entering ("items" names them)
  "choices": [
    {"label": "What the player reads", "to": 40, "phrase": "p_d3", "consequence": "Shown with the next passage on a pass.", "default": true},
    {"label": "Slide down the rope", "to": 38, "phrase": "luck_t3", "test": {"pass": 38, "fail": 39}},
    {"label": "Take the bouncer on", "to": 42, "phrase": "fight_t4", "encounter": "bouncer", "lives": 3},
    {"label": "Show the token", "to": 42, "phrase": "p_d3", "requires": "token"}
  ]
}
```

1. **Exactly one choice without a `requires` is `"default": true`**: it is what happens if nobody chooses within four bars, so the defaults alone must walk from passage 1 to the victory
   (the validator walks them and checks the tier never falls). A choice with `requires` appears only once the item is held and is never the default.
2. `phrase` is an id from `"phrases"` (`family` drums or bass, `tier` 1 to 4, a label). Every move needs one; exits (`"to": null, "exit": "warehouse"`, only on deaths and the victory) need none.
3. A **fight** names an `encounter` (an entry under `"encounters"`: name, `portrait` and `portrait_hit`, `intro`, `on_win`, `on_fail`, `on_defeat`) and `"lives": 3`, and uses a harder phrase
   (`fight_t2` to `fight_t4`). A **luck test** has `"test": {"pass", "fail"}` and its `to` is the pass passage; it cannot be retried. A **death** is `"kind": "death"` with one exit
   choice. Passage `0` is the one a lost fight leads to (keep it).
4. **Items** are under `"items"` (id to display name); `grants` gives one on entering a passage and `requires` hides a choice until it is held. The flow keeps them in `TrialFlow.flags`.
5. Every passage also needs `"map"` and `"waypoint"` and every choice `"exit_wp"` (write them in `content/trial/layout/<zone>.json` and run `python3 tools/trial/apply_layout.py`; the validator
   checks them). New zone: add it under `"zones"` (`name`, `look`, `tier`, `scene`, `map`), a scene file and a map `content/story/maps/bassment_<zone>.json`; new creature: add a function to `tools/trial/make_creatures.py` and an entry under `"encounters"`.
6. Run `godot --headless --path . -s tools/trial/validate.gd`: it lists every broken link, missing scene, phrase, item or encounter, unreachable passage, the walk by defaults, and prints the
   counts. Run `tests/test_trial.gd` for the content rules (60 to 80 passages, about ten fights, six luck tests, six deaths).

`"music"` names the pack whose recordings and chart the phrases use (`audio`, `chart`, `treatment`). `fight_audio` and `fight_chart` are a second pack id for fights; they are read and
checked (they must name packs in `content/run/run.json`) and currently equal `audio` and `chart`, because the scene plays one pack for everything. When the dungeon has its own sets (the
owner's `dd_part1` and `dd_part2`), point `audio`/`chart` at the ambient set and `fight_audio`/`fight_chart` at the fight set and wire the switch in `trial_play.gd` and `trial_engine.gd`.

## The 2.5D scene

* **Zone maps**: `content/story/maps/bassment_<zone>.json`, 2 to 4 convex sectors each, `"art": "bassment"` (the art folder `assets/story/bassment/`), lit by placed light things (torches, crystal,
  fungus glow, furnace, lamps), animated surfaces (the water swaps through four caustic frames, crystal and brass pulse), fog per zone. Each is distinct: the Service Hatch a tall ladder shaft over a
  warm landing; the Cable Run a low 15 m crawl with flickering junction boxes (eye height 1.2); Lost Property a cramped room lit by one brass lamp; the Flooded Boiler Room a sunken pool with
  moving caustics beside a rusted pipe wall; the Crystal Stacks an 11 m crystal cave with a ledge and a gap; the Barrel Cellar low arches, barrels and torch pools around a raised bar; the Fungus
  Farm terraces stepping down to a green pool; the Mirror Mezzanine a long mirrored gallery over a warm pit; the Reverb Pit a 30 m shaft with ropes; the Vault of Records shelf aisles and a velvet
  rope with a seam in the shelves; the Rat King's Warren straw tunnels branching to a bone court; the Furnace Kitchens hot tiles, stoves and a pulsing furnace; the Hall of Hands a long hall of carved
  stone hands with a gargoyle's ledge; the Resonance Door a small chamber under one huge pulsing brass door; the Echo Chamber a bare 12-sided room with one lit doorway; the Dawn Stair a stair
  that turns into daylight and an open car park under a dawn sky.
* **Passage layout**: each passage has `map` (its zone's map), `waypoint` (where the camera stands) and each choice `exit_wp` (a waypoint of that map standing at the exit that choice leads toward;
  the key `exit` is already the way out of the dungeon). `TrialData.validate` checks them against the maps (zones name valid maps, waypoints exist, exits exist and are somewhere else in the room);
  `tests/test_trial.gd` checks every waypoint and exit is reachable by the rail. `content/trial/layout/<zone>.json` is the authoring form and `python3 tools/trial/apply_layout.py` writes it in.
* **Art**: `tools/story/art/tex_bassment.py` (`main()` writes everything) draws the 86 textures of `assets/story/bassment/`: cellar-palette tiles (brick, damp brick, pipes, cables, barrels,
  crystal, fungus stone, mirror glass, iron, shelves, rock, doors, hatch, kitchen tile, hands, brass), floors, ceilings, a dawn sky strip, RGBA props (torch, crystal, mushrooms, barrel, lamp,
  furnace, doorway, ladder, rope, cables, skull, coat rack, valve, bones, stove, hand, glow, sign) and the figures `fig_<creature>_<idle|attack|struck>` (the ten creatures of
  `tools/trial/make_creatures.py` enlarged, with a lunging attack frame and the flashed struck frame) and the wizard. Deterministic. The creatures are billboards in the room (a deviation from
  the wardrobe and sheet pipeline: they need no skeleton); the player's hands are not shown.
* **Flat pictures**: `assets/trial/scenes/*.png` (`tools/trial/make_scenes.py`) are no longer shown; the data still names them and the generator is kept for the polish agent to delete or reuse.

## How it is built

| Piece | File |
| --- | --- |
| data and validator (incl. zone maps, waypoints, exits) | `src/trial/trial_data.gd`, `content/trial/passages.json`, `content/story/maps/bassment_*.json`, `tools/trial/validate.gd`, `check_maps.gd` |
| rules (no nodes) | `src/trial/trial_flow.gd` |
| the clock, blocks and windows (no nodes; `origin` is the downbeat it starts on) | `src/trial/trial_engine.gd` (uses `RunData` packs and `PadJudge`) |
| the scene (zone stages, camera, exits, figures, tableaux) | `src/trial/trial_scene.gd`, hosted by `src/run/run_play.gd` (`arm_trial`, `trial_begin_now`, `trial_leave`); `trial_play.tscn` is a launcher |
| the run side of the transitions | `RunEngine.resume`, `RunAudio` (unchanged: a `phase_start` per group), `RunPassage` |
| the wizard | `src/run/run_play.gd` `_build_gate`, flag `trial_gate` on the Warehouse in `content/run/run.json`; the `hatch` waypoint in `content/story/maps/night_one.json` |
| art | `tools/story/art/tex_bassment.py`, `tools/trial/make_creatures.py` |
| checks | `tools/trial/walk_trial.sh`, `check_trial_audio.py` (a dungeon-only recording), `check_transition_audio.py` (entry and exit), `capture.sh` |

## Verification

Automated (`tests/test_trial.gd`, 38 tests):

* **the content**: 63 passages (60 to 80), 16 zones, 10 fights each with a different creature and three lives, 7 luck tests, 6 deaths plus the defeat passage, one victory, 22 side passages,
  3 items behind 3 gated choices; **every zone's map is valid with 2 to 4 sectors and at least two lights; every passage's waypoint and every exit is a waypoint of its map, reachable by the
  rail and somewhere else in the room; a missing waypoint or exit is refused**;
* **reachability and defaults**, **items**, **fights, luck, deaths**, **timing and music** (the music game never stops; windows last exactly 16 beats; the commit is on beat 12.75; a pick beats
  the default; a failed phrase reopens the window with the failed option as the default): on the engine, as before;
* **the scene** in a phone-sized 844x390 view on the real run scene (virtual clock): a 2.5D stage with the exits lit and numbered, two floating choices of at least 140x40 px above the pads,
  the bars-left readout, the zone footer, items in the footer; defaults walk through zone swaps (a swap lands on a block's downbeat, the frame is shut before it); death and victory walk back to
  the Warehouse; three lost phrases end the trial; a fight puts the creature on the floor of its zone, it lunges when the phrase is lost and shows struck when won;
* **the wizard and the transitions**: "Enter the Trial" appears in the Warehouse only and does not touch the pads; ignoring it leaves by the default route; choosing it sends the camera to
  the hatch on the next guard, the dungeon takes the pads on the guard after, the Warehouse stays on screen until the downbeat, the Service Hatch opens on it, the dungeon's beat grid starts
  there and its first cue is on the run's grid; the back key leaves on a downbeat of that grid, the run resumes there as a fresh phase with the energy kept and the Warehouse on screen.

Run by script: `bash tools/trial/walk_trial.sh` (a virtual run from the Warehouse into the dungeon, the default walk through all 16 zones to Daylight, about 330 s of song time, back into the
Warehouse: `WALK OK`). Recorded in real time (`tools/story/record_music.gd` on the run scene with `RW_TRIAL_ENTER=1 RW_TRIAL_LEAVE_AT=30`, then `tools/trial/check_transition_audio.py`): the
numbers are in the progress note of `docs/RUN_DUNGEON_MUSIC_PLAN.md` section 7.

Seen (`docs/shots/trial/`, 1280x720 on a real window): `contact_bassment.jpg` and `zone_<zone>.png` for every zone, `entry_1` to `entry_5` (the walk to the hatch, the frame closing, the
Service Hatch opening), `fight_1_eel`, `fight_2_eel_lunges`, `death_tableau`, `victory_tableau`.

Not done: nobody has played this by hand or on a phone; the camera has no pitch control in the zone maps' authored views, so the shaft and the pit are seen across rather than looked down into;
the fight pack (`fight_audio`) is read and checked but one pack plays throughout; the creatures are enlarged portraits, not rigged figures.
