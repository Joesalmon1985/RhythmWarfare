# Provenance of the Deathtrap Dungeon opening

DuelMasterBattle (https://github.com/Joesalmon1985/DuelMasterBattle, commit `1b9513dd973087281bfcedeb8a786788331697b0`, GPL-3.0, same owner) was only **read**. Nothing was
changed there. What was brought across, and where each piece came from:

## Data

| Here | From DuelMasterBattle | Notes |
| --- | --- | --- |
| `content/trial/passages.json` links for passages 1, 270, 66, 119 (`choices[].to` and `.book`) | `DD/Deathtrap_Dungeon_Verified_Backbone.json` `verified_nodes` (and `godot_project/content/dd_passages/{1,270,66,119}.json`, status BOOK_VERIFIED) | edges copied exactly; the test `tests/test_trial.gd` pins them |
| passages 56 and 293 as endpoints | the same backbone (293: edges to 137 and 382 are recorded as `next_verified` and not built); 56 appears as the target of 270 and 119 | prototype endpoints, no content of their own |
| passage text (entrance, fork, east branch, named box) | `WizardRTSHybrid/wizard_rts/data/trial/legacy_zones.json` zones `dd_entrance` and `dd_fork` (signs `dd_crystal`, `dd_table`, `dd_arrow`, `dd_prints_west`, `dd_prints_east`, `dd_east_draught`, `dd_empty_box`, pickup `aid_box`) | lightly edited and joined; `text_source` in each passage says legacy or verified-beat |
| the Giant Fly encounter | `WizardRTSHybrid/wizard_rts/data/trial/legacy_bestiary.json` `giant_fly` (description; "a loser may escape wounded", `docs/TRIAL_CANON_STATUS.md`) and the `fly_east` entity of `dd_fork` (the intro line) | **ADAPTED placement**: the legacy puts the fly on the east loop of the fork zone, and the book passage 119 is not verified to contain one; it is attached to the "push through the curtain, east" choice of 119 and labelled `"placement": "ADAPTED"` |
| the fight's rhythm, win and loss text | written here | the legacy resolves fights as Ward duels, which this game does not have |

`docs/TRIAL_CANON_STATUS.md` was read for what is book-checked: the Crystal Entrance, Footprint Fork and Footprint Galleries rows are implemented legacy content, the east loop
reconnecting (119 to 56) is implemented legacy, and the Giant Fly is implemented legacy.

## Art

| Here | From | Notes |
| --- | --- | --- |
| `assets/trial/art/wizard.png` | `godot_project/assets/pixel/portraits/wizard.png` (sha256 301cd08b81d14dbd...) | the wizard waiting in the Warehouse |
| `assets/trial/art/giant_fly_portrait_0.png`, `_1.png` | `godot_project/assets/pixel/creatures/giant_fly_portrait_{0,1}.png` | the fight; `_1` is the struck frame |
| `assets/trial/art/box.png` | `godot_project/assets/pixel/props/box.png` | currently unused; kept for the named-box scene |
| `assets/trial/scenes/*.png` | **drawn for this repo** by `tools/trial/make_scenes.py` (procedural pixel art) | placeholders for proper illustrations: replace a file with a 1280x720 PNG of the same name |

## The other 396 passages

| Here | From | Notes |
| --- | --- | --- |
| `content/trial/book_graph.json` | the owner's OCR passage pack: GlenGame (https://github.com/Joesalmon1985/Glen-s-game) branch `feature/deathtrap-full-book`, `puca_dungeon/content/deathtrap_ff/passages/*.json` (400 files, read-only), merged with the verified backbone and a hand-made spine of bridges | links, luck tests, fights and deaths only: structural facts, not text; **unverified**; see `docs/TRIAL_FULL_BOOK.md` |
| `content/trial/book_text.json` | **original** one- or two-sentence summaries written for this game from the OCR text (not copied: a script rejects any run of five words shared with the source) and zone placeholders | the pack's passage text is not reproduced anywhere in this repository |
| `assets/trial/art/{manticore,bloodbeast,poison_ivy,flying_guardian,cave_troll,throm_duel}_portrait_{0,1}.png` | DuelMasterBattle `godot_project/assets/pixel/creatures/` (same commit as above) | the other creatures use the generic monster |
| `assets/trial/art/monster_{0,1}.png`, `assets/trial/scenes/dd_*.png`, `death.png`, `victory.png` | drawn for this repo by `tools/trial/make_zone_scenes.py` | placeholders |

## Not brought across

The legacy Godot world map, the Ward duel system, the other 20 zones, Throm, the riddle and every later passage. Passage 293's onward links (137 and 382) are in the data as
`next_verified` and nowhere else.
