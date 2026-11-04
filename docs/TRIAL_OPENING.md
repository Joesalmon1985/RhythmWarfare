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
* **A passage.** A fixed illustrated scene, the passage title, a short description and **floating choices** (they bob). Nothing else is interactive: no movement, no menus; the only
  inputs are the choices and the four pads. (The system back key leaves the dungeon; it is not a game input.)
* **A choice** starts a short rhythm phrase on the existing pads: the music of the dungeon plays, cues fall, you play them. The phrase is a slice of a pack's chart (the same WAV/MIDI
  import, tiers and `PadJudge` as the run), started on the audio clock four beats after the choice.
* **A pass** moves to the choice's passage and shows its consequence line with the new passage and its choices. **A failed phrase** keeps you in the passage with the same choices; the
  one you failed reads "Try again: ...". Retry as often as you like.
* **A fight** (the Giant Fly) shows the creature, plays a longer, harder phrase, then an outcome animation: a win spins the fly out of the air; a loss is a lunge, a sting, a flash and a shake.
* **Endpoints** (56 and 293) offer a single choice, **Return to the Warehouse**, which starts a new run in the Warehouse.

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
  "choices": [
    {"label": "What the player reads", "to": 44, "book": "the book's wording of the link",
     "phrase": "junction", "consequence": "Shown with the next passage on a pass."}
  ]
}
```

1. To continue from **293**: add `"137"` and `"382"` (their edges are already noted there as `next_verified`), turn 293's single "Return to the Warehouse" choice into two choices to them
   (keep a way out somewhere), and drop `"endpoint": true` and the status `PROTOTYPE_ENDPOINT`.
2. `phrase` is an id from `"phrases"` (`family` drums or bass, `tier` 1 to 4, `beats` 4 to 14), or `null` for a choice that needs no rhythm. Raise the tier for harder passages.
3. An **encounter** is an entry under `"encounters"` (portrait, intro, win and loss text, where it came from, `"placement": "BOOK"` or `"ADAPTED"`) named by `"encounter"` on a choice.
4. Run `godot --headless --path . -s tools/trial/validate.gd`: it lists every broken link, missing scene, phrase or encounter, and prints the link map. Add the passage's verified edges to
   `VERIFIED` in `tests/test_trial.gd` if it is book-verified.

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

Automated (`tests/test_trial.gd`, 11 tests; the full suite and the Python content tests also pass):

* the links of passages 1, 270, 66 and 119 equal the book-verified edges, 56 and 293 are marked prototype endpoints, all six passages are reachable;
* both entrance choices (open the named box; continue north), the routes that rejoin (270 and 119 meet at 56; 66 and the return from 119 meet at 293);
* a fight: a lost phrase stays in 119, marks the choice "Try again", plays the losing outcome; the retry passes, plays the winning outcome and reaches 56 (flow and scene);
* the phrase is charted on the music's half beats, judged by `PadJudge`, a perfect player passes, an absent one fails, attempts are independent, the fight phrase has more cues;
* the scene in a phone-sized 844x390 view: two floating choices of at least 140x40 px, a picture and a description, the choices step aside during a phrase, a pass shows the consequence
  and the next choices, the endpoint's only choice leaves for the Warehouse;
* the wizard's "Enter the Trial" appears in the Warehouse and not elsewhere, does not touch the pads, launches the dungeon; ignoring it the run leaves the Warehouse by its default route.

Recorded (real scene and audio, dummy driver, `tools/story/record_music.gd` + `tools/trial/check_trial_audio.py`): across seven attempts the recorded drums matched the drum loop started at each
attempt's start time; the delay repeated in a cycle with a spread of 11.8 ms (two mixer blocks of the dummy driver) and no drift over 38 s. Each attempt's cues are on the music's
beats by construction, so a cue and its sound are never more than that start quantisation apart (the perfect window is 45 ms).

Seen (screenshots in `docs/shots/trial/`): the entrance, the eastern branch with the fly during a phrase and after a lost fight, the wizard in the Warehouse at 1280x720 and 844x390.

Not done: nobody has played this by hand or on a phone; the scene illustrations are placeholders; the dungeon's sound is a temporary stand-in; the outcome animations are scripted tweens that have
been looked at in stills only; passage 119's fly is an adapted placement, not a book fact; text for passages 1, 66, 119 and 270 is adapted legacy text and has not been re-checked against the book.
