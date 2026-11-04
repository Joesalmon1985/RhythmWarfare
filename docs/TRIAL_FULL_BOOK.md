# The whole book: all 400 passages

Every passage number from 1 to 400 is now a playable passage of the dungeon, and only **death** (or losing a fight three times) and **the victory at 400** return the player to the
Warehouse. The first four passages are hand-authored, the rest come from the files below. This page says exactly how far each passage can be trusted.

```
godot --path . res://src/trial/trial_play.tscn                            # from passage 1
RW_TRIAL_START=169 godot --path . res://src/trial/trial_play.tscn         # start anywhere: 169 is the Cave Troll fight, 2 a death, 400 the victory
godot --headless --path . -s tools/trial/validate.gd                       # the data check and the counts (add  -- all  to list every passage)
```

## What there is and where it came from

| What | Count | Source | Trust |
| --- | --- | --- | --- |
| `BOOK_VERIFIED` | 28 | the owner's verified backbone (`content/trial/quest_map.json`), with the book-checked links; the text is the backbone's own one-line "beat" (4 of them are hand-written passages) | the links are checked against the book |
| `OCR_GRAPH` | 217 | the owner's OCR passage pack (GlenGame `feature/deathtrap-full-book`, `puca_dungeon/content/deathtrap_ff`, read-only): links, luck tests, fights, deaths; text is **an original short summary** of the OCR text | **unverified**: the OCR is noisy (page numbers and neighbouring passages bleed in, some numbers are misaligned) |
| `BRIDGED` | 155 | no usable source: the pack has only a placeholder for 161 of the 400 passages | **invented**: zone text and links that only keep the dungeon connected |
| `SYNTHETIC` | 1 | passage 0, "Defeated", where a lost fight leads | invented |

Links: 55 verified, 408 from the OCR pack, 351 bridged. **Walking** the dungeon (never taking a "side passage") reaches 180 passages; the other 220 are hung off those as side passages
("Take the side passage") so that all 400 can be played, and they are not where the book would put them. Defaults alone walk 1, 270, 56, 198, 142, 88, 258, 95, 37, 351, 240, 89, 54, 40, 98,
105, 77, 400 (17 steps; a test follows them).

The text of each passage: 28 backbone beats, 186 original summaries (checked by a script not to copy any run of five words of the OCR text; 22 that did were thrown away), 1 written for the game
(passage 56), and 185 zone placeholders ("This passage's text has not been written or verified yet" or a zone line). The full table is `docs/TRIAL_PASSAGES.md`.

Things found on the way, for a page check against the book:

* The backbone's edge **162 to 442** names a passage the 400-passage book does not have (it is probably 142 or 149); it is not built, 162 leads on to 218 by a bridge. Passage **449**
  (Throm's state list) is out of range too.
* The pack hand-wrote a demo chain (101, "Giant Rat" at 37, 399 as a death) that contradicts the verified backbone; the backbone wins and 101 is dropped.
* Passage 8 is marked a death by the pack but also holds a luck test and seven links (OCR conflation); it plays as the pack says: a death.

## How the dungeon plays

* **Spine.** The verified fragments are joined, in the legacy adaptation's zone order, by a hand-made chain of bridges (`SPINE` in `tools/trial/build_book.py`, each with its reason): 1, 66, 293, 382,
  222, 154, 22, 184, 323, 194, 52, 169, 288, 221, 60, 365, 290, 302, 379, 213, 37, 351, 240, 89, 281, 399, 192, 162, 218, 65, 269, 127, 6, 364, 31, 62, 16, 241, 400. The six orders of Igbut's
  lock all lead back to the lock except the legacy's right one (ADAPTED).
* **Zones and pictures.** A passage's zone is fixed where the quest map places it, otherwise by how far it is from the start, so the dungeon is met zone by zone in order. Each zone has its own
  illustration (`assets/trial/scenes/dd_*.png`, drawn for this repo), plus death and victory.
* **Tier.** The difficulty of a passage's cues rises with its distance from the start (tiers 1 to 4).
* **Fights** (22): the passage's combat in the pack, or the legacy's (Giant Fly 119, Cave Trolls 169, Throm 302, the Manticore 6). The fight option plays a harder phrase; a creature beats you after
  **three** lost phrases and that is the end (passage 0, then the Warehouse). Creature pictures: six from DuelMasterBattle, the rest a generic monster tinted per creature.
* **Luck tests** (14): one option, "Trust to luck": the phrase decides which way it goes, with no second go.
* **Deaths** (12): the pack's, plus passage 0. The death passage shows YOU DIED and offers one choice, "Wake in the Warehouse", which is also the default: after four bars the player is back.
* **Victory:** passage 400, then the Warehouse.
* **Not modelled:** dice, Skill, Stamina and Luck points, items, gold and flags (a passage that depends on having an item simply offers all its ways), and the book's conditions.

## Making it better

* Replace a passage by hand: add it to `content/trial/passages.json` (it wins over the book files).
* Correct the graph: fix `SPINE` or the pack, then `python tools/trial/build_book.py graph --pack <deathtrap_ff folder>` and `python tools/trial/make_passage_table.py`.
* Texts: `python tools/trial/build_book.py text --chunks <folder> --pack <deathtrap_ff folder>` assembles original descriptions (the helper chunks are not kept in the repository).
* The whole quest map and the 17 zones are in `docs/TRIAL_QUEST_MAP.md`.
