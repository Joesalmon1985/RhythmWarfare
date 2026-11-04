# Provenance of the Bassment's content

The Bassment (the wizard's dungeon under the club, `docs/TRIAL_OPENING.md`) is original work. Everything in `content/trial/`, `src/trial/` and `assets/trial/` was written or drawn for
this repository, except one picture.

## What is here

| What | Where | Made by |
| --- | --- | --- |
| The passages, zones, creatures, items and phrases (63 passages, 16 zones, 10 creatures) | `content/trial/passages.json` | hand-authored text and structure for this game |
| Zone and death/victory scenes, 1280x720 | `assets/trial/scenes/*.png` | `tools/trial/make_scenes.py` (procedural pixel art, lit per pixel) |
| Creature portraits, 64x64, two frames each | `assets/trial/art/<creature>_0.png`, `_1.png` | `tools/trial/make_creatures.py` (procedural pixel art) |
| The wizard waiting in the Warehouse | `assets/trial/art/wizard.png` | the owner's own sprite (it first lived in the owner's other repository, DuelMasterBattle, `godot_project/assets/pixel/portraits/wizard.png`); kept by the owner's decision |

No downloaded asset, no audio and no text from any book or other repository is in the dungeon. Its music is the run's own packs (`content/trial/passages.json` `"music"`).

## What was removed, and why

The first version of this dungeon was structured on a published gamebook: its zone names, its creatures and characters, a three-item lock at the end, and a graph of all 400 of its
passages recovered by OCR from the owner's earlier adaptation projects, with invented bridges between them. The owner decided the game's dungeon must be original, so on 2026-11-04 all
of that was taken out of the working tree and the dungeon was re-authored from scratch:

* `content/trial/book_graph.json`, `book_text.json` and `quest_map.json` (the recovered graph, its summaries and the quest map);
* `src/trial/trial_book.gd` (the code that composed 400 passages from them) and `tools/trial/build_book.py`, `make_quest_map.py`, `make_passage_table.py` (the OCR-pack build paths);
* `docs/TRIAL_FULL_BOOK.md`, `docs/TRIAL_QUEST_MAP.md`, `docs/TRIAL_PASSAGES.md` and `docs/trial_quest_map.png`;
* the creature portraits and the crate picture copied from the other repository (`*_portrait_*`, `box.png`, `monster_*`) and the old placeholder scenes.

The git history still contains those files (older commits on the earlier branches); removing them from history is a separate decision for the owner. Passage numbers are plain numbers
assigned in order of authoring; nothing in the game or the docs presents them as taken from, or checked against, any book.
