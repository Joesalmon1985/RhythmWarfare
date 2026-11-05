# Music report: which music plays where, and why

The populate step of the music library (`docs/MUSIC_LIBRARY_PLAN.md`, M4) executing the owner's brief (`docs/MusicImportPlan.md`). What exists: the catalogue (`docs/MUSIC_CATALOGUE.md`), the packs
(`songs/packs/`), the arrangement system (`tools/content/arrange.py`), and, since this step, an arrangement behind every scene of the run and two rendered arrangements behind every chapter.
The per-scene tables are in `docs/MUSIC_HANDOFF.md` (generated); the audition WAVs are `audition/` (ignored by git, `python tools/content/arrange.py audition`, index in `docs/audition/README.md`).

## 1. How the music was chosen

**Family first.** A family is one Beat Shaper project and its variants (`lv1_warehouse`, `_v1`, `_v2`, ...): the export grouping is the strongest compatibility evidence in the catalogue, so an arrangement
plays **one family**, and only a *variation* section may borrow a pack from another family, and only when the catalogue lists the two compatible (not merely sharing a tempo). **Palette second.** Each
chapter identity is a filter on the packs (`content/music/palettes.json`: family glob, profile, density, which mix recipe each role gets), never a file name. **Seed last.** `arrange.py generate <palette> --seed N`
is deterministic: the seed picks the role order, the pack of each 8- or 16-bar section (base pack for intros and endings, the densest two for drops, the sparsest two for breakdowns, never the same pack twice
in a row) and nothing is chosen per bar. A scene plays the 16-bar window `slot` of an arrangement; its `alternates` are further seeds of the same family, and the per-run seed picks between them (same seed, same
music and same chart; `RW_RUN_SEED` overrides).

| World (scenes) | Palette | Family and why | Arrangements (bars) |
| --- | --- | --- | --- |
| Warehouse (6), Night One: energetic warehouse rave | `warehouse` | `lv1_warehouse` (+ `_v1`, `_v2`): the Lv1 set, 87 BPM x2 half-time profile, the family the Night One recording already sits in; the entry opens on the base pack | `warehouse_1..3` (96) |
| Mothership (5): futuristic electronic | `mothership` | `lv2_alien_spaceship` (`_v2`, `_v3`; `_v1` fails the chart check, a 10-beat drum gap, so it only plays as a plain pack, which no scene does now) | `mothership_1..3` (80) |
| Underworld (5): aggressive dark neurofunk | `underworld` | `cold_fusion_interface` (the four `cold_fusion*` packs, 174 BPM, the densest set in the repository at 7 to 10 cues per bar) with the `dark_drop` / `dark_breakdown` recipes (bass full, synth held back). `metaverse_ready_fusion` is the one contrasting family a variation may borrow (the catalogue lists the pair compatible). **The nearest match**, not the final answer: Lv3 Hell has no MIDI, so the scenes stay `temporary: true` | `underworld_1..3` (80) |
| Hospital (6): fragile, gradually uplifting | `hospital` | `lv4_hospital` (+ `_v1.._v3`): fragile recipes (drums 0.7, bass 0.7, synth full) for intros and breakdowns, `uplift` on drops and endings, so a world plays from fragile to uplifting | `hospital_1..3` (96) |
| Ward (6): unsettling industrial | `ward` | `lv5_asylum` (+ `_v1.._v3`): 87 BPM x2, the `harsh` and `dark_breakdown` recipes | `ward_1..3` (96) |
| Hospital, late (4) and Ward, late (4) | `hospital`, `ward` | the same families with other seeds (and 64 bars), so the late visit does not repeat the early one | `hospital_late_1..3`, `ward_late_1..3` (64) |
| Deathtrap Dungeon (the Bassment) | none | **unchanged**: `dd_part1` (ambient) is the pack the dungeon plays and `dd_part2` (fights) is named in `passages.json` as `fight_audio`/`fight_chart`. The dungeon engine (`src/trial/`) plays one pack and reads no arrangements, and `src/trial` is not the music's to change. The catalogue does not list `dd_part1` compatible with Metaverse Ready Fusion (it lists `lv1_warehouse`, `lv5_asylum`, `default_project` on a folder basis only), so no Meta section was added | none |

**Slots** follow the route graph. In every world the entry scene is slot 0 (intro, then a build or breakdown, on the family's base pack: Night One's warehouse floor stays on `lv1_warehouse`), the middle scenes take the next
slots in order (builds, drops, breakdowns, variations, the occasional 16-bar section), and the exit scene takes the last slot, which always ends on a drop and an ending (palette `tail`). Scenes that are siblings in one route
window take different slots, so they play different music; they may chart different packs, which the route lock already handled (the lock compares the chart pack of block 0 of the next scene; `RunData` sets
a scene's `audio` and `chart` to its first section's pack, so nothing in the engine changed).

**Chapters.** Each chapter lists, after its own recording (Night One's `story_n1_warehouse` first; `m05`, `m07`, `m09`, `m10` for the others), two renders of an arrangement of its palette, with `bars` = the chapter's
`duration_bars` (Night One 128, Mothership 80, Underworld 64, Hospital 56, Mental hospital 64), as ogg stems under `songs/story_<chapter>_<n>/`. `StoryRun.pick_music_pack` chooses by the seed (no seed: the chapter's own
recording, as before). The director flagged dense note runs under some decisions at the default tier 3 and the tier was lowered until it stopped: Mothership 1 and 2, Underworld 2 and Hospital 2 at tier 2, Hospital 1 at tier 1.
Each chapter plays its world's family (Night One, Lv1; Mothership, Lv2; Underworld, Cold; Hospital, Lv4; Mental hospital, Lv5).

### All arrangements

| Arrangement | Palette | Family | Seed | Bars | Use | Sections | Packs played |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ch_hospital_1` | hospital | `lv4_hospital` | 21 | 56 | chapter (tier 1) | 7 | `lv4_hospital`, `lv4_hospital_v2`, `lv4_hospital_v3`, `lv4_hospital_v1` |
| `ch_hospital_2` | hospital | `lv4_hospital` | 22 | 56 | chapter (tier 2) | 7 | `lv4_hospital`, `lv4_hospital_v2`, `lv4_hospital_v1`, `lv4_hospital_v3` |
| `ch_mental_hospital_1` | ward | `lv5_asylum` | 21 | 64 | chapter (tier 3) | 8 | `lv5_asylum`, `lv5_asylum_v1`, `lv5_asylum_v3`, `lv5_asylum_v2` |
| `ch_mental_hospital_2` | ward | `lv5_asylum` | 22 | 64 | chapter (tier 3) | 8 | `lv5_asylum`, `lv5_asylum_v2`, `lv5_asylum_v3` |
| `ch_mothership_1` | mothership | `lv2_alien_spaceship` | 21 | 80 | chapter (tier 2) | 10 | `lv2_alien_spaceship`, `lv2_alien_spaceship_v3`, `lv2_alien_spaceship_v2` |
| `ch_mothership_2` | mothership | `lv2_alien_spaceship` | 22 | 80 | chapter (tier 2) | 10 | `lv2_alien_spaceship`, `lv2_alien_spaceship_v2`, `lv2_alien_spaceship_v3` |
| `ch_night_one_1` | warehouse | `lv1_warehouse` | 21 | 128 | chapter (tier 3) | 16 | `lv1_warehouse`, `lv1_warehouse_v1`, `lv1_warehouse_v2` |
| `ch_night_one_2` | warehouse | `lv1_warehouse` | 22 | 128 | chapter (tier 3) | 15 | `lv1_warehouse`, `lv1_warehouse_v1`, `lv1_warehouse_v2` |
| `ch_underworld_1` | underworld | `cold_fusion_interface` + `metaverse_ready_fusion` | 21 | 64 | chapter (tier 3) | 8 | `cold_fusion`, `cold_fusion_v3`, `cold_fusion_v1`, `meta_fusion` |
| `ch_underworld_2` | underworld | `cold_fusion_interface` | 22 | 64 | chapter (tier 2) | 8 | `cold_fusion`, `cold_fusion_v1`, `cold_fusion_v3`, `cold_fusion_v2` |
| `hospital_1` | hospital | `lv4_hospital` | 1 | 96 | run | 12 | `lv4_hospital`, `lv4_hospital_v2`, `lv4_hospital_v1`, `lv4_hospital_v3` |
| `hospital_2` | hospital | `lv4_hospital` | 2 | 96 | run | 12 | `lv4_hospital`, `lv4_hospital_v2`, `lv4_hospital_v3`, `lv4_hospital_v1` |
| `hospital_3` | hospital | `lv4_hospital` | 3 | 96 | run | 12 | `lv4_hospital`, `lv4_hospital_v2`, `lv4_hospital_v1`, `lv4_hospital_v3` |
| `hospital_late_1` | hospital | `lv4_hospital` | 1 | 64 | run | 8 | `lv4_hospital`, `lv4_hospital_v2`, `lv4_hospital_v1` |
| `hospital_late_2` | hospital | `lv4_hospital` | 2 | 64 | run | 8 | `lv4_hospital`, `lv4_hospital_v2`, `lv4_hospital_v1`, `lv4_hospital_v3` |
| `hospital_late_3` | hospital | `lv4_hospital` | 3 | 64 | run | 8 | `lv4_hospital`, `lv4_hospital_v2`, `lv4_hospital_v3`, `lv4_hospital_v1` |
| `mothership_1` | mothership | `lv2_alien_spaceship` | 1 | 80 | run | 9 | `lv2_alien_spaceship`, `lv2_alien_spaceship_v3`, `lv2_alien_spaceship_v2` |
| `mothership_2` | mothership | `lv2_alien_spaceship` | 2 | 80 | run | 10 | `lv2_alien_spaceship`, `lv2_alien_spaceship_v3`, `lv2_alien_spaceship_v2` |
| `mothership_3` | mothership | `lv2_alien_spaceship` | 8 | 80 | run | 10 | `lv2_alien_spaceship`, `lv2_alien_spaceship_v2`, `lv2_alien_spaceship_v3` |
| `underworld_1` | underworld | `cold_fusion_interface` | 1 | 80 | run | 10 | `cold_fusion`, `cold_fusion_v2`, `cold_fusion_v1`, `cold_fusion_v3` |
| `underworld_2` | underworld | `cold_fusion_interface` + `metaverse_ready_fusion` | 2 | 80 | run | 10 | `cold_fusion`, `cold_fusion_v1`, `cold_fusion_v3`, `meta_fusion`, `cold_fusion_v2` |
| `underworld_3` | underworld | `cold_fusion_interface` + `metaverse_ready_fusion` | 5 | 80 | run | 10 | `cold_fusion`, `cold_fusion_v3`, `cold_fusion_v1`, `meta_fusion`, `cold_fusion_v2` |
| `ward_1` | ward | `lv5_asylum` | 1 | 96 | run | 11 | `lv5_asylum`, `lv5_asylum_v2`, `lv5_asylum_v3`, `lv5_asylum_v1` |
| `ward_2` | ward | `lv5_asylum` | 2 | 96 | run | 12 | `lv5_asylum`, `lv5_asylum_v1`, `lv5_asylum_v2`, `lv5_asylum_v3` |
| `ward_3` | ward | `lv5_asylum` | 17 | 96 | run | 11 | `lv5_asylum`, `lv5_asylum_v3`, `lv5_asylum_v2`, `lv5_asylum_v1` |
| `ward_late_1` | ward | `lv5_asylum` | 1 | 64 | run | 7 | `lv5_asylum`, `lv5_asylum_v2`, `lv5_asylum_v3`, `lv5_asylum_v1` |
| `ward_late_2` | ward | `lv5_asylum` | 3 | 64 | run | 8 | `lv5_asylum`, `lv5_asylum_v1`, `lv5_asylum_v2` |
| `ward_late_3` | ward | `lv5_asylum` | 4 | 64 | run | 8 | `lv5_asylum`, `lv5_asylum_v3`, `lv5_asylum_v2`, `lv5_asylum_v1` |
| `warehouse_1` | warehouse | `lv1_warehouse` | 1 | 96 | run | 11 | `lv1_warehouse`, `lv1_warehouse_v1`, `lv1_warehouse_v2` |
| `warehouse_2` | warehouse | `lv1_warehouse` | 2 | 96 | run | 12 | `lv1_warehouse`, `lv1_warehouse_v2`, `lv1_warehouse_v1` |
| `warehouse_3` | warehouse | `lv1_warehouse` | 3 | 96 | run | 11 | `lv1_warehouse`, `lv1_warehouse_v1`, `lv1_warehouse_v2` |

## 2. Before and after

Measured by `python tools/content/music_metrics.py` (before = the merge of the catalogue, importers and arrangement system, `41016a9b`, which had one pack per scene).

| Metric | Before | After |
| --- | --- | --- |
| Playable music variations per scene (distinct 16-bar pack sequences across the arrangement and its alternates) | 1 in each of the 36 scenes (36 in all) | 1 to 3 per scene, 98 in all (28 scenes have 3, six have 2, two have 1: the entry scenes always open on the base pack, so they differ least) |
| Rendered versions per chapter | 1 (Mothership: 2) | 3 in every chapter (own recording and 2 arrangements) |
| Packs played by a scene, a rendered chapter or the dungeon | 17 of 26 | 21 of 26 |
| Source WAV files behind those packs, of the 123 the catalogue lists | 51 | 63 |
| Scenes on a stand-in of another family | 5 (the Underworld on Lv2 renders) | 0 (the Underworld plays Cold, labelled the nearest match) |
| `songs/` on disk | 145.9 MB | 186.2 MB (+40.3 MB: ten ogg chapter packs of 3 to 7 MB; as stereo WAV each would be about 64 MB) |

Packs no scene plays: `lv2_alien_spaceship_v1` (a 10-beat gap in its drum chart, so `arrange.py` rejects it), `meta_fusion_v1`, `dd_part1_v1..v3` (spare takes for the dungeon). The rest of the 123 WAVs are the Ableton renders
(the loop library's clips and sounds, not packs) and the Default Project and Lv3 Hell audio, which have no charts: the run charts from MIDI, so they are not given to it.

## 3. Limitations

- **Lv3 Hell has no MIDI** (the three WAVs are in `ToAddTry2/`), so the Underworld cannot play its own recording; Cold Fusion Interface is the nearest match the catalogue offers (dark, 174 BPM, dense). The Underworld scenes keep `temporary: true`.
- **Uncertain pairings.** The catalogue lists Cold Fusion Interface and Metaverse Ready Fusion as a compatible pair (equal 174 BPM profile, a shared or relative tonal centre) but most of its bass/drums combinations are flagged
  uncertain (the phrases tile, 16 against 32 beats; the Cold bass key has confidence 0). Underworld variations that borrow `meta_fusion` (`underworld_2`, `underworld_3`, `ch_underworld_1`) are the ones to listen to first
  (`audition/underworld_2.wav`, `underworld_3.wav`). No other arrangement crosses families. Pairs the catalogue marks uncertain at the pair level are never offered by the generator.
- **Library clips are not in arrangements.** Sections naming library `stems` validate, but neither the run nor `render` plays them (library clips have no tiered charts), so the Cold and Meta Ableton clips stay in the military loadout.
  The new library *sounds* (11, from `content/imports/cold_meta.json`) remain **locked**: nothing lists them in `data/campaign/campaign.json` `new_options`. That is the owner's call.
- **Dungeon.** No arrangement: the trial engine plays one pack (see the table). Switching to `dd_part2` for fights and reading arrangements needs the trial's owner.
- **Clipping.** No render clips: chapter renders peak at 0.59 to 0.73 after the limiter (ceiling 0.97). `cold_fusion_v3` is imported 7 dB lower than the others because its bass peaks above full scale in the source.
- **Route lock.** Siblings on different slots chart different packs (the same kind of `route lock applies` warnings `beatshaper.py validate` printed before); the lock holds at every world exit (the next world's entry opens on its family's base pack).
- **Fills only act in chapter renders**; the run ignores them (no runtime mixing).
- Gameplay is unchanged: cue families per block stay the gameplay's; frame numbers are unchanged (the recordings in section 5).

## 4. Importing a new folder: one command per step

```
python tools/content/catalogue.py                         # analyse every WAV/MIDI under ToAddTry1..3 -> content/music/catalogue.json, docs/MUSIC_CATALOGUE.md
python tools/content/beatshaper.py survey NewMusic        # which Beat Shaper sets are complete, at which profile
python tools/content/beatshaper.py import NewMusic --set "Lv3 Hell" --id lv3_hell   # one pack per set (variants as <id>_v1..); docs/MUSIC_IMPORT.md
python tools/content/catalogue.py                         # again: the new files get their `used_by` links and compatibility pairs
python tools/content/arrange.py generate underworld --seed 1 --bars 80 --id underworld_1 --write                       # a run arrangement: bars = 16 x the world's scenes
python tools/content/arrange.py generate underworld --seed 21 --bars 64 --use chapter --id ch_underworld_1 --write     # a chapter arrangement: bars = duration_bars
#   assign: content/story/music.json  {"id": scene, "arrangement": id, "slot": k, "alternates": [same family], "treatment": "none", "temporary": false}
python tools/content/arrange.py render ch_underworld_1 --bars 64 --chapter underworld --out songs/story_underworld_1 --format ogg --tier 3   # then list it in the chapter's music_packs
python tools/content/arrange.py validate                  # tiling, packs, tempo, chart legality, music.json names
python tools/content/beatshaper.py validate               # packs and music.json (reads arrangement entries)
python tools/content/arrange.py audition                  # audition/<id>.wav for every arrangement, index in docs/audition/README.md
python tools/content/music_handoff.py                     # docs/MUSIC_HANDOFF.md
python tools/content/music_metrics.py                     # the before/after numbers
godot --headless --path . --import                        # after any render; commit the .import sidecars
```

A new family needs a palette only when it is a new chapter identity (`content/music/palettes.json`); a new take of an existing family is picked up by the next `generate`. When Lv3 Hell has MIDI: import it, regenerate
`underworld_1..3` and `ch_underworld_1..2` (the palette already lists `lv3_*` first), render the chapters again and set the Underworld scenes' `temporary` to false.

## 5. Verification

All on the populate commits (`Music, M4 ...`), 2026-11-05, Godot 4.5.1 headless unless noted.

| Check | Result |
| --- | --- |
| `python3 -m unittest discover -s tools/content -p "test_*.py"` (catalogue, importers, arrangements: every shipped arrangement validates, 33 arrangement tests on synthetic packs) | 163 tests OK |
| `python tools/content/beatshaper.py validate`, `arrange.py validate`, `catalogue.py --check` | OK, 31 arrangements OK, up to date |
| Full Godot suite (`tests/run_tests.gd`) | 62294 checks, 0 failures (it includes the run policy matrix `test_run_matrix.gd`, the route lock `test_run_lock.gd`, `test_run_audio_sections.gd` (12) and `test_story_music_packs.gd` (4: every chapter lists two renders, the pick, load as recorded music of the whole chapter, perfect and no-input play of all ten renders)) |
| `bash tools/run/walk_run.sh` (no ignore filter) | OK, 36 of 36 scenes, all seven paths |
| `bash tools/trial/walk_trial.sh` | WALK OK |
| `bash tools/story/walk_campaign.sh` | walk-through OK, all five paths |
| Recording, Warehouse (`warehouse`, `warehouse.bar`, `warehouse.chill`: each phase has an 8-bar switch; `record_music.gd`, 70 s, perfect play; `tools/content/check_section_audio.py`) | RESULT ok: one drums voice per section, every block within 0.01 of stage gain x recipe, 99.7 to 100 % explained, a section's drums 2.9 ms from the phase's (worst of 3 switches) |
| Recording, Underworld (`underworld`, `.court`, `.pit`: Cold packs with `dark_*` recipes, switches inside every phase) | RESULT ok, same figures (worst 2.96 ms) |
| Recording, plain scenes (the pre-arrangement assignment, `RW_RUN_MUSIC`, `check_run_audio.py`) | every block fits (99.8 to 100 %), bass and synth 0.0 to 2.9 ms from the drums, delay per phase -115.2 to -106.4 ms; `RESULT CHECK` only because of the 8.8 ms phase-to-phase spread of the recorder, the same figure `docs/CONTINUOUS_RUN.md` records for the code before the music work (frame numbers unchanged) |
| Recording, two rendered chapter packs (`story_play`, `record_music.gd` 90 and 100 s, perfect play, `tools/content/check_chapter_audio.py`: every 2-bar window without a stem switch fitted as the three stems against the logged gains) | Hospital render 1 and Underworld render 1: RESULT ok, residual delay spread 0.04 and 0.01 ms (constant +16.9 and -12.4 ms over the whole chapter: no drift), gains 0.97 to 1.0 of the log, 98 to 99 % explained |
| Arrangement legality (`test_arrangements.py` plus `arrange.py validate` on all 31 files) | tiling, packs, tempo, chart legality per tier (same-pad spacing, overlaps, density floors, no gap over 6 beats in the drum chart and 12 in the bass chart), `use` rules, recipes, family rules, alternates, music.json names |

Things found while verifying: `beatshaper.py validate` and `music_handoff.py` assumed `audio`/`chart` on every scene (both now resolve an arrangement entry); two Godot tests compared against the old plain `music.json` and now carry that
baseline themselves; `check_run_audio.py` now takes `RW_RUN_MUSIC` (it ignores arrangement entries, `check_section_audio.py` is the checker for those); `check_section_audio.py` needs a `music.json` without `alternates` (or the seed that
picks the primary), because it reads the primary arrangement; `check_music.py` models an 8-bar lap, so a whole-chapter pack needs `check_chapter_audio.py`.
