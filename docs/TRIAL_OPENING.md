# The Bassment

The wizard in the Warehouse runs a trial in the cellars under the club: a gamebook-style dungeon, played on the same four pads, the same clock and the same music as the run. It is an original
dungeon (63 passages in 16 zones, 10 creatures, 3 items, one victory) and it is **in the 2.5D world of the rest of the game**: each zone is a small Doom-style map on the story engine, the camera
walks on rails between the passages' places, the choices are **hotspots in the room** (tap the lit exit, the creature, the rope), the creatures stand in the room, and entering and leaving are **seamless**: no scene change, no audio gap, no
clock reset. **Only a death, three lost fight phrases, the victory or the back key lead back to the Warehouse.** This file is the single document for it. `assets/trial/PROVENANCE.md` says what is
in the repository and where it came from.

## Launch

```
godot --path .                      # Play; in the Warehouse level a wizard stands at the left edge with a floating "Enter the Trial"
godot --path . res://src/trial/trial_play.tscn          # straight into the dungeon (hands over to the run scene, which hosts the dungeon)
RW_TRIAL_START=12 godot --path . res://src/trial/trial_play.tscn       # start at any passage (12 the eel, 13 a death, 59 the Echo, 63 the victory)
RW_TRIAL_BOT=perfect RW_TRIAL_CHOICES=d,d,1,0 godot --path . res://src/trial/trial_play.tscn   # scripted: the picks made in each window in turn
RW_TRIAL_BOT=perfect RW_TRIAL_TAPS="d;d;1;0" godot --path . res://src/trial/trial_play.tscn      # the same, but each pick is a finger on the hotspot's centre, through the hit test
bash tools/trial/walk_trial.sh      # scripted, headless: Warehouse > wizard > hatch > the default walk to the victory, then a walk whose picks are taps > back up into the Warehouse (isolated save)
bash tools/trial/capture.sh         # a screenshot per zone, before and after a selection, a fight, a death, the victory (needs a display) and docs/shots/trial/contact_bassment.jpg
python3 tools/trial/make_hotspots.py                                    # rewrite content/trial/hotspots.json (and the marker things of the maps) from passages.json
godot --headless --path . -s tools/trial/validate.gd                    # check the data (passages, graph, zone maps, waypoints, exits)
godot --headless --path . -s tools/trial/check_maps.gd [-- zone ...]    # check the zone maps, layouts and every hotspot's anchor one by one
godot --headless --path . -s tests/run_tests.gd -- --filter trial       # the tests
```

Bots: `perfect` plays every cue, `none` plays nothing, `no_fights` plays every cue except a fight's. `RW_TRIAL_CHOICES` is the pick made in each window in turn (an index, or `d` / empty for
no pick, so the default applies); `RW_TRIAL_TAPS` is the same list (`;` or `,` between windows) but each pick is a **tap**: a finger on the centre of that hotspot's target, through the hit test a phone uses
(it waits for the room to be lit after a zone swap and prints `TRIAL tap <aimed> -> <hit>`). `RW_TRIAL_UNTIL=<passage>` with `RW_STORY_QUIT=1` quits when that passage is shown. In the run scene: `RW_TRIAL_ENTER=1` chooses the wizard at once,
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

* **Warehouse.** The wizard (`assets/trial/art/wizard.png`) waits at the left of the stage with a floating **Enter the Trial**, only in the Warehouse level (the engine workstream turns him into a character hotspot;
  the entry and the walk back out are unchanged). Ignoring it changes nothing: the run goes on by its ordinary routes. Choosing it walks into the dungeon (see above).
* **The music game never stops.** Cues fall on the four pads the whole time, in 16-beat blocks (four bars) on the same clock, packs and judge as the run. Nothing pauses for reading
  or choosing.
* **A passage.** The camera stands in the passage's place in its zone map. Across the top is the **caption band**: the title and two to four sentences of narrative (what the place is, what is
  in it), never a choice, with the consequence of the last move or the stumble of a failed one on a line of its own. **Every choice is a hotspot in the room**, drawn as light and no words: a ring on the
  floor and a glow on the thing, and four corner ticks on the default; an exit is lit where it lies (a door, a ladder foot, a gap, the water's edge, a seam), a creature **stands in the room** and
  the fight is a tap on it, an item's place (the cracked crystal, the dark archway, a stone palm) is an object, a luck test is a feature (the pipes, the rope, the barrels, the door's grille). A hotspot behind
  the camera is a chevron at the screen edge on its side, so everything can be tapped without turning. Targets are at least 72 px across and sit only in the picture above the pads. A footer names the
  zone and the items you carry. The only inputs are the hotspots and the pads (the system back key leaves the dungeon; it is not a game input; keys 1 to 4 pick the hotspots in order on a desktop).
* **Four bars to choose.** When a passage appears its hotspots are lit for exactly four bars; a thin bar along the bottom of the picture (no text) shows the time left. **One is brighter: the default**,
  what happens if nobody chooses. Tap another to select it (it lights gold with a second ring and the default mark moves off; tap another to change your mind, up to the last beat). When the four bars end
  the committed hotspot flashes for a beat and the game moves on with your pick, or with the default if you picked nothing. A choice that needs an item you do not hold has no hotspot.
* **The phrase.** A committed hotspot is played as the next block of cues: a drums or bass phrase of the tier its data names (`challenge`). Between the choice and the phrase the music and the pads carry
  on without a break.
* **A pass** walks through the chosen exit (the head turns to it when the choice is committed), shows the consequence line as a short caption and opens a new four-bar window at once; if the next passage is in
  another zone the passage frame closes on the exit and opens on the new zone on the next downbeat (the new room's hotspots come up when it is on screen). **A failed phrase** keeps you where you stand with a
  stumble (the queasy look, a glance) and the same hotspots; the one you failed is now the default (the bright one), so doing nothing retries it. Retry as often as you like.
* **A fight.** The creature stands in the room (a billboard figure: idle, attack and struck poses) while the window is open, as the hotspot for the fight; tapping it (or leaving it as the default) plays the
  harder phrase, then an outcome: a win shows the struck pose and the creature sinks and fades; a loss is a lunge in the attack pose, a red flash and the stumble. **Three lost phrases in the same
  fight end the trial** (the creature's own defeat text, then the Warehouse).
* **A luck test** is one phrase with no second go: a pass goes one way, a miss the other (a setback that rejoins, or a death).
* **Items and secrets.** Three items can be found (the brass lamp, the GUEST LIST token, the silver tuning fork). Each makes a hotspot appear somewhere else: a shortcut past the Fungus Farm,
  a way past the bouncer without a fight, a hidden seam past the gargoyle. The footer lists what you carry.
* **Death and victory** are the tableaux: a death shows YOU DIED, the camera looks down and the lights go out in a slow fade, with one hotspot, the way out (also the default); the
  victory is the dawn car park, a flash of daylight settling to warm light, with the same one hotspot. Then the walk back up the hatch.

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

Everything about the dungeon lives in `content/trial/passages.json`; **`content/trial/hotspots.json` is made from it** (`python3 tools/trial/make_hotspots.py`, never edited by hand: one hotspot per choice, keyed by
passage, `id` `trial.<passage>.<n>` with n the choice's index, the contract of `docs/VISUAL_RHYTHM_ADVENTURE_PLAN.md` section 2). A passage:

```json
"37": {
  "title": "The Rope Ledge",
  "zone": "pit",                            // an id from "zones" (name, one-line look, tier, scene)
  "scene": "pit",                           // an id from "scenes" (only an id now: the flat pictures were deleted; each zone is a 2.5D map)
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
6. **Hotspots.** After any change to `passages.json` run `python3 tools/trial/make_hotspots.py`. The kind comes from the choice: a fight is an `encounter` (anchored to a marker thing `hs_<creature>` that the script writes
   into the zone map where the creature stands, `TrialScene.figure_spot`; a new creature needs an entry in the script's `FIGURES` and in the scene's), a luck test is a `feature`, a choice that needs an item or whose
   place grants one is an `object`, everything else an `exit` anchored to its `exit_wp`. Features and objects name an existing thing of the map in the script's `THINGS` table (the rope, the pipes, the door) or a marker.
   `check_maps.gd` and `tests/test_trial.gd` fail when the file and the passages disagree (defaults, routes, challenge family and tier, availability, anchors that are not in the map).
7. Run `godot --headless --path . -s tools/trial/validate.gd`: it lists every broken link, missing scene, phrase, item or encounter, unreachable passage, the walk by defaults, and prints the
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
* **Flat pictures**: deleted in the bring-to-main pass. Only `assets/trial/scenes/stacks.png` remains, the Wizard Duel's backdrop (`src/duel/duel_play.gd`); `tools/trial/make_scenes.py` can still redraw it (it would redraw the others too: delete those again). The `scenes` block of `passages.json` keeps its ids and legacy `file` paths, which the data validator no longer checks.
* **Text panel and light**: the passage text is a band across the top of the view (95 % wide, 60 % opaque), not a block over a third of it; the warren, echo chamber and cellar maps have a minimum `light` of 0.8 and `ambient` of 0.75 per sector. The other zones were not changed (a visual polish of the Bassment is still due).
* **Fights**: `dd_part2` is named in `music.fight` of `passages.json`, but the scene still plays the one pack (`dd_part1`); the fight pack is not switched to.

## How it is built

| Piece | File |
| --- | --- |
| data and validator (incl. zone maps, waypoints, exits) | `src/trial/trial_data.gd`, `content/trial/passages.json`, `content/story/maps/bassment_*.json`, `tools/trial/validate.gd`, `check_maps.gd` |
| the hotspots: data, generator, which a player may see, where an anchor stands, the agreement check | `content/trial/hotspots.json`, `tools/trial/make_hotspots.py`, `src/trial/trial_hotspots.gd` |
| the lights and the taps (a thin fallback, deleted when the engine workstream's `hotspot_view` is merged) | `src/trial/trial_hotspot_fallback.gd` |
| rules (no nodes) | `src/trial/trial_flow.gd` |
| the clock, blocks and windows (no nodes; `origin` is the downbeat it starts on) | `src/trial/trial_engine.gd` (uses `RunData` packs and `PadJudge`) |
| the scene (zone stages, camera, caption band, hotspots, figures, tableaux) | `src/trial/trial_scene.gd`, hosted by `src/run/run_play.gd` (`arm_trial`, `trial_begin_now`, `trial_leave`); `trial_play.tscn` is a launcher |
| the run side of the transitions | `RunEngine.resume`, `RunAudio` (unchanged: a `phase_start` per group), `RunPassage` |
| the wizard | `src/run/run_play.gd` `_build_gate`, flag `trial_gate` on the Warehouse in `content/run/run.json`; the `hatch` waypoint in `content/story/maps/night_one.json` |
| art | `tools/story/art/tex_bassment.py`, `tools/trial/make_creatures.py` |
| checks | `tools/trial/walk_trial.sh`, `check_trial_audio.py` (a dungeon-only recording), `check_transition_audio.py` (entry and exit), `capture.sh` |

## Verification

Automated (`tests/test_trial.gd`, 42 tests):

* **the content**: 63 passages (60 to 80), 16 zones, 10 fights each with a different creature and three lives, 7 luck tests, 6 deaths plus the defeat passage, one victory, 22 side passages,
  3 items behind 3 gated choices; **every zone's map is valid with 2 to 4 sectors and at least two lights; every passage's waypoint and every exit is a waypoint of its map, reachable by the
  rail and somewhere else in the room; a missing waypoint or exit is refused**;
* **reachability and defaults**, **items**, **fights, luck, deaths**, **timing and music** (the music game never stops; windows last exactly 16 beats; the commit is on beat 12.75; a pick beats
  the default; a failed phrase reopens the window with the failed option as the default): on the engine, as before;
* **the hotspots**: the file agrees with the passages (95 hotspots, a flat list: 74 exit, 10 encounter, 7 feature, 4 object by `trial_kind`), every anchor is in its zone map, the creature marker stands where the figure does,
  an item's hotspot appears only with the item; every hotspot of every passage has a target of at least 72 px from where the camera stands and can be hit at its centre;
* **the scene** in a phone-sized 844x390 view on the real run scene (virtual clock): a 2.5D stage with the hotspots lit (the default brighter), no button and no choice written anywhere, the caption band across
  the top, a tap selecting and changing the pick (and keys 1 to 4), a tap off a target picking nothing, targets at least 72 px and never over the pads, the thin bar full at four bars, the zone footer, items in the footer; defaults walk through zone swaps (a swap lands on a block's downbeat, the frame is shut before it); death and victory walk back to
  the Warehouse; three lost phrases end the trial; a fight puts the creature on the floor of its zone, it lunges when the phrase is lost and shows struck when won;
* **the wizard and the transitions**: "Enter the Trial" appears in the Warehouse only and does not touch the pads; ignoring it leaves by the default route; choosing it sends the camera to
  the hatch on the next guard, the dungeon takes the pads on the guard after, the Warehouse stays on screen until the downbeat, the Service Hatch opens on it, the dungeon's beat grid starts
  there and its first cue is on the run's grid; the back key leaves on a downbeat of that grid, the run resumes there as a fresh phase with the energy kept and the Warehouse on screen.

Run by script: `bash tools/trial/walk_trial.sh` (a virtual run from the Warehouse into the dungeon, the default walk through all 16 zones to Daylight, about 330 s of song time, back into the
Warehouse, then the same with three of the picks made by taps through the hit test: `WALK OK`). Recorded in real time (`tools/story/record_music.gd` on the run scene with `RW_TRIAL_ENTER=1 RW_TRIAL_LEAVE_AT=30`, then `tools/trial/check_transition_audio.py`): the
numbers are in the progress note of `docs/RUN_DUNGEON_MUSIC_PLAN.md` section 7.

Seen (`docs/shots/trial/`, 1280x720 on a real window, `bash tools/trial/capture.sh`): `contact_bassment.jpg` and `zone_<zone>.png` for every zone (the hotspots lit, the default brighter),
`select_before` / `select_after` (a tap moves the gold ring), `fight_1_hotspot` (the eel stands in the room as the fight's hotspot), `fight_2_phrase`, `fight_3_win`, `death_before` / `death_tableau`,
`victory_before` / `victory_tableau`, and the older `entry_1` to `entry_5` (the walk to the hatch, the frame closing, the Service Hatch opening; not regenerated by capture.sh).

Not done: nobody has played this by hand or on a phone; the camera has no pitch control in the zone maps' authored views, so the shaft and the pit are seen across rather than looked down into;
the fight pack (`fight_audio`) is read and checked but one pack plays throughout; the creatures are enlarged portraits, not rigged figures.
