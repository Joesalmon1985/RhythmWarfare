# The Mission Count (`squadron`): path notes (docs/THREE_PATHS_AND_FACES_PLAN.md section 5, stage 4)

Dubstep, 140 BPM with a half-time feel, entered from the radio in the Warehouse booth (`warehouse.booth.radio` -> `path:squadron`), left by the neutral coast (`run:warehouse`, flag `keep:path_squadron_free`).
These notes are Stage 4's own file; Stage 6 merges them into `docs/HANDOVER.md`, `docs/CONTINUOUS_RUN.md`, `docs/STORY_ART.md` (the art sections below are written in its format) and `docs/MUSIC_HANDOFF.md`.

## 1. What was built

| piece | where |
| --- | --- |
| the run: 14 scenes, 4 worlds, routes, rails, cast, 4 cinematics, stage mix | `content/paths/squadron/run.json` (written by `python3 tools/paths/make_squadron.py`) |
| the owner's 14 loops, assigned one per scene (not temporary) | `content/paths/squadron/music.json`, `songs/packs/squadron_c01` .. `c14` (committed, like every pack; re-import: `python3 tools/content/import_squadron.py`) |
| hotspots with their acting (23 of them direct a person) | `content/paths/squadron/hotspots/{base,air,city,escape}.json` |
| extra walks for `walk_run.sh --path squadron` | `content/paths/squadron/walks.json` |
| three maps | `content/story/maps/{airfield,city,harbour}.json`, authored by `tools/paths/squadron_{lib,airfield,city,harbour}.py` |
| their chapter data (actors, groups, palettes; not chapters of the old campaign: `run_only`) | `content/story/{airfield,city,harbour}.json`, found by the run through each world's `story` key |
| the story tables (routes, hotspots, acting, cast, cinematics) | `tools/paths/squadron_story.py` |
| the art: textures and props, drawn in numpy | `tools/story/art/tex_squadron*.py` (brief: `tools/paths/squadron_tex_brief.json`), builder `tools/story/art/chapter_squadron.py`, `python3 tools/story/build_assets.py airfield|city|harbour` |
| the people: ten new wardrobe archetypes | `tools/story/art/wardrobe.py` (`squadron()`), `tools/story/art/people.py`, preview `tools/story/squadron_wardrobe_preview.py` |
| the booth portal's props (a radio, the bomber's shadow) | `tools/story/art/tex_night_one.py` (`thing_booth_radio`, `thing_bomber_shadow`), `content/story/maps/night_one.json` (`booth_radio`, `booth_bomber_shadow`) |
| tests | `tests/test_run_squadron.gd`, the per-path matrix in `tests/test_run_matrix.gd`, `tools/paths/check_squadron.gd` |
| proof | `docs/shots/squadron/` (`node_cNN`, `route_cNN`), `docs/shots/acting/squadron_*` |

Regenerate: `python3 tools/paths/make_squadron.py` (data), `python3 tools/story/build_assets.py airfield` (and `city`, `harbour`: textures, manifest and the baked people), `godot --headless --path . --import`.

## 2. The 14 scenes

Node id = the run's scene id. Worlds: `base` (depth 1), `air` (2), `city` (3), `escape` (4). Routes, first = default; `loop` marks a route that goes back (a validation device: the plan's absurd loop is C11 -> C02).
Every route is taken by exactly one exit hotspot (the checker's rule); the touches of the plan's table are those hotspots, plus one door where the table has only one touch.

| scene | node | map room | default | other | touches (hotspot: success / failure) |
| --- | --- | --- | --- | --- | --- |
| C01 Briefing Room | `base` | airfield hut | C03 | C02 | cot (exit): C03 / C03; mission board: C02 / C03 |
| C02 The Flight Line | `base.c02` | line | C04 | C05 | ladder: C04 / C04; crates: C05 / C04 |
| C03 The Hospital | `base.c03` | tent | C05 | C06 | hatch: C05 / C05; office door: C06 / C06; the Surgeon's clipboard (character): C06 / C05 |
| C04 The Bombing Mission | `air` | bomber (night) | C07 | C03 | release lever: C07 / **C03 turn_back (-6)**; emergency controls: C03 / C07 |
| C05 The Syndicate | `air.c05` | store | C08 | C06 | truck: C08 / C06; ledger: C06 / C08 |
| C06 The Surgeon's Office | `air.c06` | office | C02 | C09 | door A: C02; **certificate: `squadron.double_stamp` -> C09 / C02** |
| C07 The Gunner's Last Flight | `city` | bomber (red) | C10 | C03 | jacket: C10; medical kit: C03 / C10 |
| C08 The Old City | `city.c08` | street | C10 | C09 | arch: C10; staff car: C09 / C10 |
| C09 The Colonel's Deal | `city.c09` | colonel's office | C12 | C11 | map: C12; **medal: `squadron.medal_pinned` -> C11 / C12** |
| C10 The Ruined City | `city.c10` | ruins | C09 (loop) | C12 | headquarters: C09; night train: C12 / C09 |
| C11 Endless Missions | `escape` | briefing hut | C02 (loop) | C12 | aircraft: C02; **broken radio: C12 / `squadron.count_raised` -> C02** |
| C12 Escape North | `escape.c12` | harbour | C14 | C13 | searchlights: C14; boat: C13 / C14 |
| C13 The Neutral Coast (ending `free`) | `escape.c13` | coast | run:warehouse | | shore: `keep:path_squadron_free`; the fisherman (character) |
| C14 Captured | `escape.c14` | cell | C11 (loop) | C12 (loop) | stamped order: C11; window latch: C12 / C11 |

**The Clause** exactly as written: a success that carries a cinematic and a route that is not the obvious one, only in C06 (the certificate's rhythm succeeds, the stamp slams, the camera turns to door B, a second stamp lands the other way, the Clerk laughs and the Surgeon is ashamed: C09) and C09 (the medal is pinned and the count goes up anyway: C11); C11 is the plan's third, a failure (the Clerk paints the number higher). `tests/test_run_squadron.gd` checks it is nowhere else.
**The loop** C11 -> C02 -> ... is the absurd ending; its way out is the radio (C11 success -> C12 -> C13); the cell (C14) sends you back to C11 or out through the latch to C12. The default routes of a player who never touches anything run round it for ever (C01, C03, C05, C08, C10, C09, C12, C14, C11, C02, C04, C07, C10 ...): the crowd leaving is that player's ending.
**Flags**: `keep:path_squadron_free` (the ending), `keep:path_squadron_clause` (the certificate), `keep:path_squadron_met_surgeon`, `_met_quartermaster`, `_met_colonel`; per-run flags `sq_briefed`, `sq_egg`, `sq_examined`, `sq_released`, `sq_ledger`, `sq_stamped`, `sq_kit`, `sq_car`, `sq_map`, `sq_medal`, `sq_train`, `sq_radio`, `sq_boat`, `sq_latch`, `sq_thanks` (the cast lines of C04 and C12 read `sq_released` / `sq_boat` at beat 61 for the reactions to the result).
**Cast and acting**: every scene has 3 to 7 cast lines (blocks 0, 16, 32, 48; reactions to a result at beats 61 to 62), the four cinematics carry acted cast, 23 hotspots direct a person (the two `character` hotspots, C03's clipboard and C13's fisherman, in all five states; the rest name the person who stands at their thing). C07's crowd is pinned `sad`: its sector offers only `stand sit rock stare` in every energy band and its cast has no cheering. C11's airmen `salute` slower each block (the line's `beats` 3, 6, 10, 14).

## 3. Divergences from the plan (and why)

1. **Worlds and maps.** A world has one map (`RunData`), so `air` (C04 to C06) is on the **airfield** map (the bomber's nose at night is a room of it, lit by instrument lamps and flak), not on `airfield` night plus `city`; `base` and `air` share the stage like Hospital and Hospital, late. The city map has its own bomber room (red light). Four maps in the plan = three map files here (the airfield night view is the bomber room).
2. **Graph rules.** Scenes entered from another world are `entry` scenes (several per world), `exit_scene` scenes may route in their own world only with `loop: true` (a validator device, so C05 -> C06, C07 -> C10 and C11 -> C12 carry it), and the depth rule of exit scenes (one level deeper) is lifted for a path (`RunData`), because C04, C07, C06 and C11 lead back to easier worlds.
3. **Kinds.** The plan's `object` touches whose success route is a route of the scene are `exit` hotspots here (look `glow`/`pulse`/`flicker`): `tools/run/check_hotspots.py` wants one exit hotspot per route anchored on a thing or a doorway, and `HotspotContract` insists the default is an exit. Only the two people (C03's Surgeon, C13's fisherman) stay `character`.
4. **Stage mix** (path's own `stages` in run.json): drums alone, then drums 0.7 + bass 1.0 (no synth), then drums back 1.0 + bass 0.9 + synth 0.5, then drums 0.55 + bass 1.0 + synth 0.7. See section 4.
5. **Names.** Wardrobe wears are `airman officer clerk surgeon quartermaster gunner mp civilian_city fisherman patient` as asked; recurring people (the Colonel, the aide, the chaplain, the Clerk, the Surgeon, the Quartermaster, the Gunner, the pilot, the crew) are one person in every map (`same_as`, `fixed`: seeded by who they are, never re-rolled), so the Colonel is the same man in the hut, the office and the C11 hut. Directed `prop`s `stamp`, `egg`, `medal` (and a held `hat`) were added.
6. **Stand-ins.** No placeholder music: every scene plays the owner's loop. The loops are 16 beats (4 bars), not the plan's 8 bars (see 4).
7. **The booth portal** gained a visible radio and the bomber's shadow on the booth wall (Night One's own procedural props), so the pulse has something to point at.

## 4. Music

All 14 sets of `NewMusic/C level Music` (copied, git-ignored, to `content/imports/squadron/C01..C14`) are imported as `squadron_c01` .. `c14` by `tools/content/import_squadron.py` (`python3 tools/content/import_squadron.py [--only C06,C07] [--check]`; about 11 s). Nothing was stretched, retimed or edited; the source folder is untouched. The packs are committed like every pack of this repo (`songs/packs/*/loops/*.wav` are tracked; `content/imports/` is the ignored drop folder), in a commit of their own (about 53 MB).

**Timing.** All 14 fit 140 BPM. `--max-error-ms 40` is used for all of them; it was *required* for C01, C02, C04, C08, C09, C12 (their kick or snare hits sit 31 to 38 ms from the MIDI notes: refused at the default 12 ms), C03, C05 and C10 verify loosely, C06, C07, C11, C13 and C14 strictly. Bass timing is `audio_checked` everywhere. C09, C11 and C14 have no snare note (kicks only).
MUSIC_HANDOFF data: `docs/paths/squadron_music_report.json` has per scene the worst error, the gains, the peaks and the command line used.

**Gains.** Per scene, the strongest bass that does not clip: the bass stem peak stays at or below -0.3 dBFS and the loudest of the four stage sums (1/0/0, 0.7/1.0/0, 1.0/0.9/0.5, 0.55/1.0/0.7) at or below -0.5 dBFS, measured on the written 16-bit loops; where the sum binds, drums then synth were lowered (drums never below -6 dB), the bass last. The importer has no limiter and refuses a stem at 0.999 or above.

| scene | drums dB | bass dB | synth dB | bass peak-limited max dB | worst stage-sum peak dBFS | bass vs drums RMS, stage 3 / 2 (dB) | bass under 90 Hz | timing needed 40 ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | -4 | +11.5 | +12 | +11.8 | -0.52 | +14.3 / +8.2 | 42% | yes |
| C02 | -3.5 | +11 | +12 | +11.8 | -0.50 | +15.1 / +9.0 | 62% | yes |
| C03 | -3.5 | +9.5 | +14 | +11.0 | -0.56 | +13.7 / +7.6 | 21% | no (loose) |
| C04 | -2.5 | +11.5 | +10 | +12.3 | -0.52 | +14.4 / +8.3 | 60% | yes |
| C05 | +0 | -2 | +9.5 | -1.1 | -0.62 | +2.0 / -4.1 | 31% | no (loose) |
| C06 | -1 | -1 | +9 | -0.5 | -0.53 | +5.0 / -1.1 | 27% | no (strict) |
| C07 | -3 | +12.5 | +11 | +13.5 | -0.61 | +21.0 / +14.9 | 79% | no (strict) |
| C08 | -5 | +12 | +8 | +12.7 | -0.50 | +18.6 / +12.4 | 83% | yes |
| C09 | -1 | +6.5 | +12.5 | +7.3 | -0.50 | +8.4 / +2.3 | 18% | yes |
| C10 | -4.5 | +12.5 | +13.5 | +13.1 | -0.58 | +20.9 / +14.7 | 70% | no (loose) |
| C11 | -4 | +6.5 | +10 | +7.0 | -0.51 | +16.5 / +10.4 | 8% | no (strict) |
| C12 | +0 | +10 | +10.5 | +10.6 | -0.95 | +12.4 / +6.3 | 55% | yes |
| C13 | -6 | +11 | +10.5 | +12.6 | -0.50 | +22.2 / +16.1 | 81% | no (strict) |
| C14 | +0 | +11 | +14 | +11.5 | -0.52 | +14.4 / +8.3 | 79% | no (strict) |

The bass is clearly present in all 14 (bass RMS above drums RMS at stage 3 everywhere), with a solid sub (over half of its energy under 90 Hz) in C02, C04, C07, C08, C10, C12, C13 and C14. **Thin or weak, for the owner's ears**: C05 and C06 (the bass is a short loud transient on a quiet body, peak-limited: its RMS is 23 to 25 dBFS and at stage 2 it sits below the drums; the C05 source bass already peaks above full scale), and C03, C05, C06, C09 and C11 are mid-heavy (sub share 8 to 31%). A re-export of those with the transient tamed, or a game-side limiter, would give more; nothing was edited. Drums are 4 dB or more lower than the sources in C01, C08, C10, C11 and C13 (C13 at the -6 floor).

**How a phase uses a 4-bar loop.** A phase is 64 beats = the 16-beat loop four times, and the four 16-beat blocks are exactly the four laps, so every lap brings a new layer: lap 1 drums alone; lap 2 the bass enters at full gain over drums at 0.7 (no synth yet); lap 3 the drums come back to 1.0 with the bass at 0.9 and the synth at 0.5; lap 4 the bass at full with drums 0.55 and synth 0.7, the strongest block (the choice window). A missed block holds its stage for a lap (the existing advance-or-hold rule). The bass is at full or nearly full gain for three laps of four, and every new scene starts on drums alone again. These are the path's own `stages` in `run.json` (data only, no engine change). Nothing is static: the loop is the same four bars but the arrangement over it changes every 27.4 s / 4 = 6.9 s.

## 5. Art (STORY_ART format)

The three art worlds have no SVG rigs: `assets/story/<map>/` holds `manifest.json` (`textures`, `people`, `borrow_sprites: true`: `StoryAssets.sprite` falls back to Night One's light and deck sprites), `textures/*.png` (surfaces 64 px tiles, props 128 px billboards, six wide props 256 x 128, a 256 x 64 sky) and `people/` (the baked sheets: airfield 36 people, city 20, harbour 21). Everything is drawn by the code named above; no downloaded or published art; no text anywhere (the only glyphs are painted digits on the mission-count boards); no insignia (the Colonel's ribbons are colour bars, the military police have blank white armbands, the cross on the tent is a plain grey cross).

### Map `airfield` (worlds `base` and `air`, scenes C01 to C06)

Grainy, over-exposed Mediterranean daylight outside (bleached khaki, olive drab, orange dust, a white-blue sky, fog `#d8c79c`), warm bulbs inside, the bomber green-black lit by instrument lamps. Six rooms (rectangles, metres, x east / z south):
`hut` (-12..0, 0..8, view `main`: the mission board with a painted tally, the empty cot at the north doorway, stove, maps table, hanging bulbs, the east door onto the line), `line` (0..26, 0..14: sandbag berm, orange dust, the invented twin-engine bomber nose with its ladder, crates, windsock, jeep, the tent flap and the hangar front), `tent` (0..10, -10..0: cots, drip stands, the kitchen hatch), `office` (-12..0, -10..0: the desk with a huge stamp, a framed certificate, two doors, filing cabinets), `bomber` (10..14, 14..22: the glazed nose at night with flak flashes, the release lever, the emergency box, instrument panel; ambient 0.9 so the crew read), `store` (26..38, 0..12: the Quartermaster's ledger, the truck, crates and shelves of tins).
Pieces: none of the manifest kind; things with `anim` (`flicker` stove, hatch and flak, `sway` lamps and windsock, `pulse` emergency box, `bob` truck). Palettes: `khaki`, `glare`, `instrument`.

### Map `city` (world `city`, scenes C07 to C10)

Sepia and noir without neon (fog `#7a6046`): `bomber_r` (-4 bomber again under red alarm lamps, view `main`), `street` (0..24, 0..8: stucco shopfronts, cobbles, the staff car, the broken arch at the far end, washing lines, cafe table), `office_c` (2..12, 8..16: dark panelling, the Colonel's desk, the medal case, the torn map, globe, the tally slate), `ruins` (24..46, 0..10: blackened brick under a fire-lit sky, the burnt car, the fire barrel, headquarters' door and, far off, the night train with its lamp). Palettes `red`, `sepia`, `fire`.

### Map `harbour` (world `escape`, scenes C11 to C14)

A cold blue night cut by white searchlight beams (fog `#0e1c34`): `hut2` (the briefing hut again, the count board reading 47 in fresh paint, the smashed radio, the aircraft in the door), `quay` (0..22, 0..12: wet planks, the fishing boat with one gold lantern, two searchlight towers with additive beams, nets, bollard), `cell` (0..10, -8..0: tally scratches, the barred window with its latch and a shaft of moonlight, the order on the table), and the **neutral coast** `coast` (22..44, 0..14, ceiling 4.5), the only saturated place of the path: golden sand, turquoise sea, cobalt sky, bright umbrella pines, gulls, a blue-and-white boat. It is seen from the quay only through a narrow gap behind the boat. Palettes `khaki`, `searchlight`, `bright`, `cold`.

### The people: wardrobe

`airman` (a plain, b ground crew in overalls, c pilot in a leather jacket with goggles), `officer` (a colonel: broad, peaked cap, 4 x 3 ribbon bars, b aide with glasses, c chaplain with a dark collar band), `clerk` (0.82 high, round glasses, garters, bow tie; holds a `stamp`), `surgeon` (long stained white coat, stethoscope, mask down, stubble), `quartermaster` (broad, apron, moustache; an `egg`), `gunner` (a boy: 0.7 high, oversized jacket, flying cap), `mp` (white helmet, belt, cross strap and blank armband), `civilian_city` (a man, b woman, c child, d street singer), `fisherman` (a yellow oilskin, b dark oilskin with sou'wester, c jersey and beard), `patient` (striped pyjamas; a head bandage, b sling, c plaster on a leg). New in `people.py`: hats `peaked sidecap flightcap mphelm flatcap knit fisher fedora eyeshade surgcap`, tops `uniform pyjamas`, outers `waistcoat oilskin`, accessories `ribbons webbing armband garters bandage sling apron braces collarband maskdown rag chain`, props `stamp egg medal hat`. The five existing chapters are pixel-identical (the agent hashed 511 specs and 7,965 frames before and after).

## 6. Proof

* **Tests**: `bash tools/test.sh` green on the rebased tree (with the Gospel path): **73,111 checks, 0 failures**, and the 181 Python content tests OK; `tests/test_run_squadron.gd` alone is 322 checks, the per-path matrix (`--filter run_matrix`) 1,061 (it runs the Mission Count under every tap policy and four skills). The suite before the stage was 71,389 (Stage 1d).
* **Checks**: `python3 tools/run/check_hotspots.py --path squadron`: 0 errors (29 hotspots, 14 of 14 scenes reached, 27 routes taken, the ending left by `run:warehouse`; one warning: the Surgeon's clipboard leads to a scene on another chart pack, the route lock decides it like the Warehouse's); `python3 tools/story/check_assets.py`: OK for the three new art worlds (textures at their stated sizes, every actor baked with every act and face the data directs); `beatshaper.py --path squadron validate`: OK (route-lock warnings only); `godot --headless -s tools/paths/check_squadron.gd`: the run and the three maps load with 0 errors.
* **Walks** (`bash tools/run/walk_run.sh --path squadron`, real scenes on the virtual clock, throwaway save): `perfect` (C01 C02 C05 C06 C09 C11 C12 C13 and back into the Warehouse, taking the Clause twice), `loop` (the default routes of a player who touches nothing: 12 scenes, round the loop), `clause`, `sloppy`, `none`: `scenes of the path visited: 14 of 14`, `run walk-through: OK`. The booth portal itself: `RW_RUN_PORTAL=warehouse.booth.radio RW_RUN_START=warehouse.booth` entered the path at 174 -> 140 BPM, played the eight scenes of `perfect` and left at 140 -> 174 BPM into the Warehouse (the log lines `RUN entered path squadron ...` and `RUN left the path ...`); each stage was built in a cue-free guard (airfield 191 ms, city 127 ms, harbour 146 ms), none at the handoff.
* **Shots** (look at them): `docs/shots/squadron/node_cNN.jpg` (a few seconds in) and `route_cNN.jpg` (the hotspot window open, beat 56) for all 14 scenes (`bash tools/paths/shoot_squadron.sh`; the real run scene on the virtual clock, the camera where the rail has put it); `docs/shots/acting/squadron_<hotspot>.jpg` and `contact_acting_squadron_<world>.jpg`: 23 hotspots in five states (`bash tools/paths/shoot_squadron_acting.sh`).
* **Shots I am not happy with**: `route_cNN` where the rail's wandering camera is looking at a wall or the ceiling at beat 56 (C03, C04, C05, C06 above all: the hotspots then show as the edge beacons, which are touchable but not pretty); the quay (`node_c12`, `route_c12`, the acting strips of the sentry and the boat) shows the bright neutral coast through its gap as a glitchy block of dither, and the fishing boat reads as a dark hulk; the flight line's sandbag berm is very loud orange; the bomber rooms are dark by design but C04's lever is hard to find from the home camera; in the acting strips of the exits that change world (`success` and `failure` panels) the passage frame is already closing over the picture, as in Stage 1d.
* **Weak art** (the artists' own list): `thing_tent_flap` (a cross on a white sheet could be read as a flag: check it in game), `thing_truck` (the cab is two boxes), `thing_staff_car` (rough windscreen), `thing_medkit`, `wall_hangar` and `wall_stucco`; gunner (reads as a small person in a helmet more than a boy), the mp's helmet (a plain white dome), the patient's head bandage (a turban), the ribbons and officer stripes (small).


## 7. Not verified

* Nobody listened to anything: no live audio, no phone. The bass gains and the stage mix come from measurements of the written loops, not from ears.
* The shots are desktop frames on the virtual clock; how acts and faces read moving on a phone, and whether a reaction at beat 61 is seen by a player watching the pads, is not known.
* The weaker pictures are listed in section 6.
