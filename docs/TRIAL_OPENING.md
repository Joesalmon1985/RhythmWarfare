# The Bassment

The wizard in the Warehouse runs a trial in the cellars under the club: a gamebook-style dungeon, played on the same four pads, the same clock and the same music as the run. It is an original
dungeon (63 passages in 16 zones, 10 creatures, 3 items, one victory), shown as a flat illustrated screen. **Only a death, three lost fight phrases or the victory lead back to the
Warehouse.** This file is the single document for it: launch, how it plays, the zones, how to add a passage, and how it was checked. `assets/trial/PROVENANCE.md` says what is in the
repository and where it came from.

## Launch

```
godot --path .                      # Play; in the Warehouse level a wizard stands at the left edge with a floating "Enter the Trial"
godot --path . res://src/trial/trial_play.tscn          # straight into the dungeon
RW_TRIAL_START=12 godot --path . res://src/trial/trial_play.tscn       # start at any passage (12 the eel, 13 a death, 59 the Echo, 63 the victory)
RW_TRIAL_BOT=perfect RW_TRIAL_CHOICES=d,d,1,0 godot --path . res://src/trial/trial_play.tscn   # scripted: the picks made in each window in turn
RW_TRIAL_VIRTUAL=1 RW_TRIAL_BOT=perfect RW_TRIAL_UNTIL=63 RW_STORY_QUIT=1 godot --headless --path . res://src/trial/trial_play.tscn   # the default walk to the victory, no window
godot --headless --path . -s tools/trial/validate.gd                    # check the data and print a summary (add `-- all` for every passage's links)
godot --headless --path . -s tests/run_tests.gd -- --filter trial       # the tests
```

Bots: `perfect` plays every cue, `none` plays nothing, `no_fights` plays every cue except a fight's. `RW_TRIAL_CHOICES` is the pick made in each window in turn (an index, or `d` / empty for
no pick, so the default applies). `RW_TRIAL_UNTIL=<passage>` with `RW_STORY_QUIT=1` quits when that passage is shown.

## How it plays

* **Warehouse.** The wizard (`assets/trial/art/wizard.png`) waits at the left of the stage with a floating **Enter the Trial**, only in the Warehouse level. Ignoring it changes nothing:
  the run goes on by its ordinary routes. Choosing it leaves the run for the dungeon.
* **The music game never stops.** Cues fall on the four pads the whole time, in 16-beat blocks (four bars) on the same clock, packs and judge as the run. Nothing pauses for reading
  or choosing.
* **A passage.** An illustrated scene, the passage title, two to four sentences, **floating choices**, and a footer naming the zone (and the items you carry). The only inputs are the
  choices and the pads (the system back key leaves the dungeon; it is not a game input).
* **Four bars to choose.** When a passage appears its choices float for exactly four bars, with a bar showing the time left. One choice is marked `[DEFAULT]`. Tap another to pick it (tap
  again to change your mind, up to the last beat). When the four bars end the game moves on with your pick, or with the default if you picked nothing. A choice that needs an item you do
  not hold is not shown.
* **The phrase.** A committed choice is played as the next block of cues: a drums or bass phrase of the tier its data names. Between the choices and the phrase the music and the pads carry
  on without a break.
* **A pass** moves to the choice's passage, shows its consequence line, and opens a new four-bar window at once. **A failed phrase** keeps you in the passage with the same choices; the one
  you failed reads "Try again: ..." and is now the default, so doing nothing retries it. Retry as often as you like.
* **A fight** shows the creature, plays the harder phrase, then an outcome animation: a win spins the creature out; a loss is a lunge, a flash and a shake. **Three lost phrases in the same
  fight end the trial** (the creature's own defeat text, then the Warehouse).
* **A luck test** is one phrase with no second go: a pass goes one way, a miss the other (a setback that rejoins, or a death).
* **Items and secrets.** Three items can be found (the brass lamp, the GUEST LIST token, the silver tuning fork). Each makes a choice appear somewhere else: a shortcut past the Fungus Farm,
  a way past the bouncer without a fight, a hidden seam past the gargoyle. The footer lists what you carry.
* **Death and victory** are the only ways back: a death shows YOU DIED with one choice, "Wake in the Warehouse" (also the default, so after four bars the player is there); the victory
  does the same with daylight behind it.

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
5. New zone: add it under `"zones"` (`name`, `look`, `tier`, `scene`) and a scene file; new creature: add a function to `tools/trial/make_creatures.py` and an entry under `"encounters"`.
6. Run `godot --headless --path . -s tools/trial/validate.gd`: it lists every broken link, missing scene, phrase, item or encounter, unreachable passage, the walk by defaults, and prints the
   counts. Run `tests/test_trial.gd` for the content rules (60 to 80 passages, about ten fights, six luck tests, six deaths).

`"music"` names the pack whose recordings and chart the phrases use (`audio`, `chart`, `treatment`). `fight_audio` and `fight_chart` are a second pack id for fights; they are read and
checked (they must name packs in `content/run/run.json`) and currently equal `audio` and `chart`, because the scene plays one pack for everything. When the dungeon has its own sets (the
owner's `dd_part1` and `dd_part2`), point `audio`/`chart` at the ambient set and `fight_audio`/`fight_chart` at the fight set and wire the switch in `trial_play.gd` and `trial_engine.gd`.

## Pictures

`python tools/trial/make_scenes.py` draws the 16 zone scenes, the death and the victory (320x180 at fixed seeds, scaled 4x to 1280x720): a perspective room with textured brick and flagstone,
the lamps of the zone lighting it in dithered bands (torches, crystals, a furnace), glowing things drawn on top. `python tools/trial/make_creatures.py` draws the ten 64x64 creature portraits
(two frames each). Replace any file with a PNG of the same name and nothing else changes. Run `godot --headless --path . --import` after regenerating.

## How it is built

| Piece | File |
| --- | --- |
| data and validator | `src/trial/trial_data.gd`, `content/trial/passages.json`, `tools/trial/validate.gd` |
| rules (no nodes) | `src/trial/trial_flow.gd` |
| the clock, blocks and windows (no nodes) | `src/trial/trial_engine.gd` (uses `RunData` packs and `PadJudge`) |
| the scene | `src/trial/trial_play.gd`, `trial_play.tscn` (uses `RunAudio`, `SongClock`, `StoryPadView`, `StoryNoteLane`, `LaneInput`) |
| the wizard | `src/run/run_play.gd` `_build_gate`, flag `trial_gate` on the Warehouse in `content/run/run.json` |
| pictures | `tools/trial/make_scenes.py`, `tools/trial/make_creatures.py` |
| a recording check | `tools/trial/check_trial_audio.py` (run on a `tools/story/record_music.gd` recording of the scene) |

## Verification

Automated (`tests/test_trial.gd`, 32 tests; the whole Godot suite also passes):

* **the content**: 63 passages (60 to 80), 16 zones (12 to 17), 10 fights each with a different creature and three lives, 7 luck tests, 6 deaths plus the defeat passage, one victory, 22 side
  passages, 3 items behind 3 gated choices; titles unique; two to four sentences each; a tier per zone from 1 to 4; fights always use the harder phrase of their passage; no word of the
  book the first draft was adapted from remains in the data; the removed book files do not exist;
* **reachability and defaults**: every passage can be reached from the start; only deaths and the victory end; the default choices alone walk 30 passages from the hatch to the victory in the
  data, the flow and the engine (a perfect player who never picks reaches Daylight and leaves exactly once), and the tier never falls along the walk;
* **items**: the lamp (won from the Lampmoth) shows the dark archway and skips the Fungus Farm; the token and the fork show their choices; an unknown item or a gated default is reported by
  the validator; every passage has a default for an empty-handed player;
* **fights, luck, deaths**: every fight can be lost and then won; three lost phrases end the trial with the creature's defeat text; luck tests go either way with no retry; the final test is a
  bass hold then the Echo; death and victory lead to the Warehouse after their window (flow and scene);
* **timing and music**: the music game never stops (no more than six beats without a cue, every block carries cues); every window lasts exactly 16 beats; the commit lands on beat 12.75; a
  pick beats the default and can be changed until the window closes; a failed phrase reopens the window with the failed option as the default; the fight loses then the retry wins (engine and
  scene);
* **the scene** in a phone-sized 844x390 view: two floating choices of at least 140x40 px, one marked `[DEFAULT]`, `[CHOSEN]` replaces it on a pick, the bars-left readout, the zone footer (no
  claim about where text came from), the carried items in the footer;
* **the wizard**: "Enter the Trial" appears in the Warehouse and not elsewhere, does not touch the pads and launches the dungeon; ignoring it, the run leaves the Warehouse by its default route.

Run by script: the default walk to Daylight (`RW_TRIAL_VIRTUAL=1 RW_TRIAL_BOT=perfect RW_TRIAL_UNTIL=63`), and a run with picks that take the lamp and the dark archway.

Seen (screenshots in `docs/shots/trial/`, 1280x720 on a real window): `opening.png` the first window with the default marked, `fork.png` a choice with two bars left in the Mirror Mezzanine,
`fight.png` the Cable Eel during its phrase, `death.png` Fried, `victory.png` Daylight, `item.png` the brass lamp in the footer.

Not done: nobody has played this by hand or on a phone; the dungeon's sound is a temporary stand-in (the Warehouse recordings under the Hospital filter); the outcome animations have been looked
at in stills only; the dungeon is a flat screen (a 2.5D version is a later work package).
