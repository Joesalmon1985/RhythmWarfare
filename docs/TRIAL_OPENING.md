# The Deathtrap Dungeon opening

A small gamebook-style dungeon reached from the Warehouse. Branch `feature/deathtrap-opening`, built on `feature/continuous-story-run`.

## Launch

```
godot --path .                      # Play; in the Warehouse level a wizard stands at the left edge with a floating "Enter the Trial"
godot --path . res://src/trial/trial_play.tscn          # straight into the dungeon
RW_TRIAL_BOT=no_fights RW_TRIAL_CHOICES=1,1,0 godot --path . res://src/trial/trial_play.tscn   # scripted: north, east, the fly (the bot skips fights)
RW_TRIAL_VIRTUAL=1 RW_TRIAL_BOT=perfect RW_TRIAL_CHOICES=1,1,0 RW_TRIAL_UNTIL=56 RW_STORY_QUIT=1 godot --headless --path . res://src/trial/trial_play.tscn
godot --headless --path . -s tools/trial/validate.gd                    # check the data and print the link map
godot --headless --path . -s tests/run_tests.gd -- --filter trial       # the tests
```

Bots: `perfect` plays every phrase, `none` plays nothing, `no_fights` plays every phrase except the fights. `RW_TRIAL_CHOICES` is the list of choice indexes picked in turn.

## What the player sees and does

* **Warehouse.** The wizard (`assets/trial/art/wizard.png`) waits at the left of the stage with a floating **Enter the Trial** button, only in the Warehouse level. Ignoring it changes
  nothing: the run goes on by its ordinary routes. Choosing it leaves the run for the dungeon.
* **The music game never stops.** In the dungeon cues fall on the four pads the whole time, in 16-beat blocks (four bars) on the same clock, packs and judge as the run. Nothing pauses
  for reading or choosing.
* **A passage.** A fixed illustrated scene, the passage title, a short description and **floating choices** (they bob). The only inputs are the choices and the four pads (the system
  back key leaves the dungeon; it is not a game input).
* **Four bars to choose.** When a passage appears its choices float for exactly four bars, with a bar showing the time left. One choice is marked `[DEFAULT]` (the data says which). Tap
  another to pick it (tap again elsewhere to change your mind, up to the last beat). When the four bars end the game moves on with your pick, or with the default if you picked nothing.
* **The phrase.** A committed option is played as the next block of cues (a drums or bass phrase of the tier its data names; a fight gets a harder one). Between the choices and the phrase
  the music and the pads carry on without a break.
* **A pass** moves to the option's passage and shows its consequence line with the new passage and its choices, and a new four-bar window opens at once. **A failed phrase** keeps you in
  the passage with the same choices; the one you failed reads "Try again: ..." and is now the default, so doing nothing retries it. Retry as often as you like.
* **A fight** (the Giant Fly) shows the creature, plays the harder phrase, then an outcome animation in the empty beats before the next block: a win spins the fly out of the air; a loss is
  a lunge, a sting, a flash and a shake.
* **Endpoints** (56 and 293) offer a single choice, **Return to the Warehouse**, which is also the default: leave it and after four bars a new run starts in the Warehouse.

### The timeline

```
block:        0 (ambient)            1 (phrase)             2 (ambient)             3 (phrase)
beats:   -3.25   12.75 | 16 ............ 28.75 | 32 ............ 44.75 | 48 ...
             window 1 ->|  result? <- window 2 opens at the result      -> commit ...
```

Every 16 beats, at beat 12.75 of a block (after its last cue's window has closed, with the next block's cues about to fall in), the engine ticks: after a phrase it judges it and opens a
four-bar window on the passage that results; after an ambient block it closes the window and commits the pick or the default. The first window opens in the count-in so that it too is four
bars. `src/trial/trial_engine.gd` is this, with no nodes, driven by song time.

## The passages

```
1 Crystal Entrance ── open named box ──> 270 Named Box ── continue ──> 56 (prototype endpoint)
        │
        └── continue north ──> 66 Footprint Fork ── west ──> 293 (prototype endpoint)
                                     │
                                     └── east ──> 119 Eastern Branch ── continue east [Giant Fly, ADAPTED] ──> 56
                                                        └── return and go west ──────────────────────────────> 293
```

Routes rejoin at 56 (from 270 and from 119) and at 293 (from 66 and back from 119). The links of 1, 270, 66 and 119 are the book-verified edges, pinned by `tests/test_trial.gd`;
56 and 293 are prototype endpoints. Where everything came from: `assets/trial/PROVENANCE.md`.

## Where to add the next passage

Everything about a passage lives in one place, `content/trial/passages.json`, under `"passages"`, keyed by the book's passage number:

```json
"137": {
  "title": "The Western Gallery",
  "scene": "gallery",                       // an id from "scenes" (add a picture under assets/trial/scenes/ and an entry in "scenes")
  "status": "BOOK_VERIFIED",                // or ADAPTED / LEGACY / PROTOTYPE_ENDPOINT
  "text": "A short description.",
  "text_source": "where the words came from",
  "tier": 2,                                // optional, 1 to 4: how busy the background cues are
  "choices": [
    {"label": "What the player reads", "to": 44, "book": "the book's wording of the link",
     "phrase": "junction", "consequence": "Shown with the next passage on a pass.", "default": true},
    {"label": "Another option", "to": 222, "book": "...", "phrase": "easy", "consequence": "..."}
  ]
}
```

1. To continue from **293**: add `"137"` and `"382"` (their edges are already noted there as `next_verified`), turn 293's single "Return to the Warehouse" choice into two choices to them
   (keep a way out somewhere), and drop `"endpoint": true` and the status `PROTOTYPE_ENDPOINT`.
2. `phrase` is an id from `"phrases"` (`family` drums or bass, `tier` 1 to 4), or `null` for a choice that needs no rhythm. Raise the tier for harder passages. **Exactly one choice per
   passage has `"default": true`**: it is what happens if the player has not chosen within four bars (the validator insists).
3. An **encounter** is an entry under `"encounters"` (portrait, intro, win and loss text, where it came from, `"placement": "BOOK"` or `"ADAPTED"`) named by `"encounter"` on a choice.
4. The whole quest is mapped in `content/trial/quest_map.json` (see `docs/TRIAL_QUEST_MAP.md`): find the passage there, use the edges it lists (the validator compares a
   `BOOK_VERIFIED` passage's choices with the map's verified edges) and its zone. A passage that is not yet in the map must be added to the map first.
5. Run `godot --headless --path . -s tools/trial/validate.gd`: it lists every broken link, missing scene, phrase or encounter, and prints the link map. Add the passage's verified edges to
   `VERIFIED` in `tests/test_trial.gd` if it is book-verified.

## The whole quest

`docs/TRIAL_QUEST_MAP.md` and the picture `docs/trial_quest_map.png` map the dungeon from passage 1 to the victory (400): 17 physical zones (A to K of the canonical report) in order of
play with their real exits and the flags that gate them, the three gems and the final lock, the contestants, the major encounters, and every book-verified passage (28) with its
verified edges plus the 38 passages those edges point at (marked REFERENCED: the book has 400 passages and only this macrograph is verified, so nothing past it is invented). The six
passages of the opening are the playable part, shown bright. Rebuild with `python tools/trial/make_quest_map.py build <DuelMasterBattle checkout>`.

The scene pictures are placeholders drawn by `tools/trial/make_scenes.py`; replace a file in `assets/trial/scenes/` with a 1280x720 PNG of the same name.

## Music

`content/trial/passages.json` `"music"` names the pack whose recordings and chart the phrases use (`lv1_warehouse_v1` with the Hospital's filter, marked temporary). To give the dungeon its
own: `python tools/content/beatshaper.py import <zip|folder> --set "<project>" --id trial_opening`, then set `audio` and `chart` here to `trial_opening`
(`docs/MUSIC_IMPORT.md`).

## How it is built

| Piece | File |
| --- | --- |
| data and validator | `src/trial/trial_data.gd`, `content/trial/passages.json` |
| rules (no nodes) | `src/trial/trial_flow.gd` |
| the phrase on the pads | `src/trial/trial_phrase.gd` (uses `RunData` packs and `PadJudge`) |
| the scene | `src/trial/trial_play.gd` (uses `RunAudio`, `SongClock`, `StoryPadView`, `StoryNoteLane`, `LaneInput`) |
| the wizard | `src/run/run_play.gd` `_build_gate`, flag `trial_gate` on the Warehouse in `content/run/run.json` |

## Verification

Automated (`tests/test_trial.gd`, 19 tests; the full Godot suite and the Python content tests also pass):

* the links of passages 1, 270, 66 and 119 equal the book-verified edges and the quest map's edges (the data validator compares them), 56 and 293 are prototype endpoints;
* **the music game never stops**: through the count-in, the choice windows, the phrases and the results no stretch of more than six beats is without a cue, and every block carries cues;
* **four bars and a default**: every window lasts exactly 16 beats, the first opens in the count-in, a commit lands on beat 12.75 of the block, and with no pick the marked default is taken
  (1 > 270 > 56 > out, by defaults alone, in the engine and in the scene); a pick beats the default and can be changed until the window closes; a pick after it closes is ignored;
* both entrance choices, routes that rejoin (270 and 119 meet at 56; 66 and the return from 119 meet at 293);
* a failed phrase reopens the window with the failed option as the default, a lost fight stays at the curtain and plays the losing outcome, the retry wins (engine and scene);
* the scene in a phone-sized 844x390 view: two floating choices of at least 140x40 px, one marked `[DEFAULT]`, `[CHOSEN]` replaces it on a pick, the bars-left readout, the choices step
  away during a phrase;
* the wizard's "Enter the Trial" appears in the Warehouse and not elsewhere, does not touch the pads and launches the dungeon; ignoring it, the run leaves the Warehouse by its default route;
* the quest map holds the 17 zones in order of play to the victory 400, every exit and every passage link points at something on the map, every book-verified passage is in it.

Recorded (real scene and audio, dummy driver, `tools/story/record_music.gd` + `tools/trial/check_trial_audio.py`): the dungeon starts one music group at the first beat and never restarts it;
over the six blocks recorded before the exit the drums sat at the same delay to 0.02 ms in ambient and phrase blocks alike.

Seen (screenshots in `docs/shots/trial/`, 1280x720 and 844x390): the first window with the default marked, a pick, a phrase block with the scene clear, the fork's window with two bars
left, the fight's phrase, and the lost fight returning to the same choices with "Try again" as the default.

Not done: nobody has played this by hand or on a phone; the scene illustrations are placeholders and the dungeon's sound is a temporary stand-in; the outcome animations have been looked at in
stills only; passage 119's fly is an adapted placement; the passage text is adapted legacy text and has not been re-checked against the book; the whole quest is *mapped* (the 400-passage
adjacency of the book is not verified beyond the 28 passages, see `docs/TRIAL_QUEST_MAP.md`), but only the six opening passages are playable.
