# The Ember Road (`ember`): path notes for the Stage 6 merge

Stage 5 of `docs/THREE_PATHS_AND_FACES_PLAN.md` (section 6): psytrance at 145 BPM, 15 scenes E00 to E14, entered from the small ember in a glass at the Warehouse **bar**
(`warehouse.bar.ember`, still gated on `wh_vip_pass`, the flag the stranger's VIP pass sets) and left by two endings, `quenched` and `kept`. This file is for Stage 6 (it does not edit
`HANDOVER.md`, `README.md`, `CONTINUOUS_RUN.md`, `STORY_ART.md` or `MUSIC_HANDOFF.md`); the art sections below are in `STORY_ART.md`'s format.

## What was built

| Piece | Where |
| --- | --- |
| Run data: 15 scenes, five worlds, seven cinematics, 109 cast lines, 37 hotspots | `content/paths/ember/run.json`, `hotspots/<world>.json`, authored by `tools/run/make_ember.py` (edit its tables, run it again) |
| Walks for `walk_run.sh --path ember` | `content/paths/ember/walks.json` (`kept`, `taken`, `lantern`; the default `perfect` walk is E00 to E12) |
| Music: placeholders and the owner's prompts | `content/paths/ember/music.json` (`prompt` per scene, `prompts` table, `placeholder` mix), `songs/packs/ember_e00_orchard` .. `ember_e14_taken` from `python tools/content/make_path_placeholders.py ember` |
| Four maps | `content/story/maps/{orchard,birch_hall,deep_halls,ash_land}.json`, `content/story/<map>.json` (chapter files, named by the worlds' `story` key); authored by `tools/story/ember_maps.py` |
| Art | `assets/story/<map>/` (textures, manifest, `people/` sheets) from `tools/story/build_ember.py`; drawing code `tools/story/art/ember_spec.py` (the list), `tex_ember_tiles.py`, `tex_ember_things.py`, `wardrobe_ember.py` |
| Tests | `tests/test_run_ember.gd` (data, flags, cast, pieces, hide, registry, the real scene through the bar portal, both endings, the snatched failure) |
| Proof | `docs/shots/ember/node_<scene>.jpg`, `route_<scene>.jpg` (`bash tools/run/capture_path.sh ember`), `docs/shots/acting/ember_*.jpg` (`bash tools/run/capture_path.sh ember --acting`) |

## Shared code touched (all additive; keep both sides when merging with the other paths)

* No registry change: each world of `run.json` names its chapter file in `story` (`"story": "res://content/story/<map>.json"`), the convention of the Gospel stage-3 engine commit (`RunPlay._story_entry`); the Story Campaign
  menu never sees the paths' maps.
* `src/run/run_data.gd` (path graph rules): an exit scene of a path may also lead on inside its own world (no `loop` needed; the graph check still catches cycles), may lead to any scene of its world, and a
  route to another world has no depth rule (a setback goes back).
* `src/run/hotspot_contract.gd`, `run_engine.gd`, `run_play.gd`, `story_crowd.gd`: **two new kinds of `cast` line**. `{"piece": "<id>", "op": "on|off|pulse", "at_beat": n}` switches a set piece (a map thing with
  `"piece": id`; the stage's `piece_on/off/pulse`), and `{"actor": "<id>", "hide": true, "at_beat": 0, "if_flags_all": [...]}` removes a person from the scene (`StoryCrowd.hide_actor`: Bram when you are alone, the
  Warden once he has fallen). Cinematic `cast` takes them too. Validated like every cast line (`CAST_KEYS`, `PIECE_OPS`, the map index lists pieces).
* `tools/story/art/people.py`: hat kind `hood` (`blank`: `dark` = the riders' empty hood with a red glint, `skin` = the sentinel's pale blank face). `tools/story/art/wardrobe.py`: `PATH_WARDROBES`, a
  `person` key (one look for a named person standing in several rooms), dress dispatch to `wardrobe_ember.py`. `tools/story/art/directed.py`: reads the paths' `run.json` and `hotspots/` as well as the main run's.
* `tools/run/check_hotspots.py`: in `--path` mode a route may be the success of any hotspot kind, not only an exit. `tools/run/acting_frames.py` and `contact_acting.py`: `RW_PATH_ID`, `--prefix`.
* New tools: `tools/story/check_map.gd` (a map and its chapter), `tools/run/check_path.gd` (a path's data), `tools/run/capture_path.sh` (shots of any path).

## Divergences from the plan

1. **Five worlds, not four.** The plan's `north` world lists two maps (`birch_hall`, `deep_halls`); a world has one map, so it is split: `north` (E03 Hall, E04 Pass on `birch_hall`) and `deeps` (E05 Deep Halls,
   E06 Falls on `deep_halls`). `marsh` and `mountain` share `ash_land` as the plan says (as Hospital and Hospital, late share a map). Scene ids are `hollow`, `hollow.ford`, `hollow.inn`, `north`, `north.pass`,
   `deeps`, `deeps.falls`, `marsh`, `marsh.wall`, `marsh.stair`, `marsh.plain`, `mountain`, `mountain.spring`, `mountain.keeper`, `mountain.taken` (the first scene of a world has the world's id).
2. **The default exit of a scene is an invented lit way on** where the plan lists two touches that are not exits (a hotspot's kind `exit` is the only thing that may be the default): E03 the porch door, E06 the
   landing, E07 the marsh path, E08 the crack (the plan's own), E09 the side path, E11 the way down, E12 and E13 the way back (an ending's default must set the keep flag), E14 the way out.
3. **E00 has a second touch** (the Ember in its bowl by the cot: +6 energy, flag `ember_held`) because every scene must show two to four things; the plan lists only the gate.
4. **The grandmother lies; she does not `offer`** (E00): an offering pose from a person lying on a cot does not read. She `lie`s with the `relief` face and `sleep`s at beat 44 (eyes closed); the Ember glows in
   the bowl beside her.
5. **The "mouths laugh" of the gate (E08)** is a set piece (`piece_gate_mouths`) switched on at beat 34, not an act. **Horses stamp** (E01) is a `bob` animation on the horse billboards.
6. **Alone / lost companions** are `hide` cast lines (`ember_alone` hides Bram in E05, E07, E10, E12 to E14; `ember_warden_lost` hides the Warden in E04 and E06). Bram and the Warden stop at the falls only
   as far as the data goes: the Warden is not in the marsh scenes at all (the company parts at the falls; the plan does not place him there).
7. **Taken (E14) can be entered from E06 (the rider's horn), E08 (the gate), E09 (the sentinel or the hard bells) and E10 (the tower)** as the plan's table says; its two ways out are `loop` routes (back to E10 or E08).
8. **The Birch Hall's setback and the lake's setback go to the High Pass** (E05's failure is the plan's "setback E04"): the route is a `loop` back across a world border.
9. **Music placeholders** are 8-bar WAV loops at 145 BPM in the stage 2 format (not Ogg), psytrance genre, mix bass-forward and recorded in `music.json` (`placeholder.levels_db` drums -21, bass -11, pad -28 dBFS, the sub
   at least 45 % under 90 Hz; the generator measures and refuses otherwise). Each scene plays its own pack (15 packs, about 7 MB each).
10. **The directed people are per-room instances** (`bram_f`, `bram_p`, `bram_fb` ... all `person: bram`): a crowd lives in one room, so a companion who walks with you is one actor per scene, dressed and faced
    the same by `person`.

## Flags and what they change

| flag | set by | changes |
| --- | --- | --- |
| `ember_no_vial` | the Lady's hand failed (E03) | E09 offers the hard bells (their failure is Taken) instead of the plain bells |
| `ember_warden_lost` | the lake failed (E05, `ember.warden_falls`) | the Warden is gone from E04 and E06; the horn at the falls is a rider's horn (E14) |
| `ember_alone` | Bram's boat failed (E06) | Bram is gone from E07 on |
| `keep:path_ember_quenched`, `keep:path_ember_kept` | the endings (E12, E13); E12's failure (`ember.snatched`) sets the first too | the Warehouse portal's look (Stage 6) and the home screen's endings list |

Other flags (`ember_held`, `ember_bram_lamp`, `ember_warden_met`, `ember_vial`, `ember_map`, `ember_lake_calm`, `ember_horn`, `ember_hollow_trust`, `ember_lights`, `ember_gate_open`, `ember_bells_silent`,
`ember_sentinel_asleep`, `ember_tower`, `ember_listened`, `ember_escaped`, `ember_bargain`) are set for the record and for the owner's later use.

## Music: the shopping list (15 scenes, 145 BPM, 8-bar seamless loops)

The owner's prompts are in `content/paths/ember/music.json` (`prompt` on each scene's entry and the `prompts` table), verbatim from plan 6.2. `docs/MUSIC_HANDOFF.md`'s generator does not know paths yet;
Stage 6 may add them from that table.

| scene | pack now | prompt (verbatim) |
| --- | --- | --- |
| E00 The Orchard | `ember_e00_orchard` | progressive psytrance: soft rolling kick, warm plucked arpeggios, rounded bass pulse, harvest-bell chimes, airy pads |
| E01 The Ford at Night | `ember_e01_ford` | dark psytrance: driving kick, galloping 16th bass, metallic hoof percussion, low horn drones, tense rising leads |
| E02 The Lantern Inn | `ember_e02_inn` | full-on psytrance: punchy kick, bouncing bass, tavern-fiddle synth, clapping percussion, whispering filtered lead |
| E03 The Birch Hall | `ember_e03_birch_hall` | atmospheric psytrance: deep kick, glassy arpeggios, choir-like pads, flowing bass, birch-wind textures |
| E04 The High Pass | `ember_e04_high_pass` | hypnotic psytrance: relentless kick, howling filtered noise, icy plucks, low throbbing bass, sparse hollow percussion |
| E05 The Deep Halls | `ember_e05_deep_halls` | dark progressive psytrance: cavernous kick, sub-bass drones, dripping water percussion, dissonant stabs, distant drum hits |
| E06 The Falls | `ember_e06_falls` | melodic psytrance: cascading water arpeggios, deep kick, emotional lead, flowing bass, distant choir pads |
| E07 The Reed Marsh | `ember_e07_reed_marsh` | swampy psytrance: wet kick, bubbling bass, croaking percussion, eerie whispered vocal synth, submerged pads |
| E08 The Black Wall | `ember_e08_black_wall` | industrial psytrance: hammering kick, grinding bass, iron-gate percussion, war-horn synth stabs, oppressive drones |
| E09 The Stair of Bells | `ember_e09_stair_of_bells` | minimal psytrance: tiptoe kick, muted bass pulse, tuned bell percussion, held breath pads, a single tense lead |
| E10 The Ash Plain | `ember_e10_ash_plain` | driving psytrance: marching kick, scorched bass, dry rattling percussion, ash-wind noise sweeps, a distant tolling lead |
| E11 The Throat | `ember_e11_throat` | dark psytrance: pounding kick, molten bass growls, crackling fire percussion, volcanic drones, a hypnotic whispering lead |
| E12 The Drowned Spring | `ember_e12_drowned_spring` | uplifting psytrance: clean kick, radiant arpeggios, warm bass, water-droplet percussion, a soaring resolving lead |
| E13 The Keeper | `ember_e13_keeper` | sinister psytrance: slow-burn kick, seductive warm bass, glowing pad swells, ember-crackle percussion, a lead that never resolves |
| E14 Taken | `ember_e14_taken` | oppressive psytrance: heavy kick, chained metallic percussion, low horn drones, grinding bass, cold rising sirens |

(Each prompt in the data is the full sentence "145 BPM <style> psytrance, 8-bar seamless loop. ... Separate editable MIDI tracks.")

## Art (in the format of `docs/STORY_ART.md`)

### Map `orchard` (assets/story/orchard/): the Orchard, the Ford, the Lantern Inn (world `hollow`)

Eight rectangular sectors: the orchard (open, harvest dusk), the lane, the near bank, the ford (water 30 cm down, scrolling), the far bank, the inn road, the inn (beams, hearth, back door and a window for the
rider's shadow piece) and the back yard. Surfaces drawn by `tex_ember_tiles.py` (grass, lane, ford water, bank mud, boards, flags, hedge, cottage, fence, reeds, inn panelling, door, window, beams, a starry ceiling,
`sky_dusk`), billboards by `tex_ember_things.py` (apple trees, baskets, the cot, lanterns, hearth, tables, barrels, stools, the hanging lamp, **the Ember** in its bowl, the gate, willows, black horses with a red glint, stepping
stones; pieces `river_rise`, `rider_shadow`). People (`wardrobe_ember.py`): `villager_hollow` (wool jerkin, smock, leather belt, no pointed ears, no wizard hats), `grandmother`, `bram` (broad, straw hat, dungarees, apron-coloured
gilet), `innkeeper` (round, waistcoat, ledger), `drinker`, `warden` (grey hooded cloak, belt, plain sword at the hip as a strap), `rider` (ash-grey cloak and hood, nothing inside but two red glints).

### Map `birch_hall` (assets/story/birch_hall/): the Birch Hall and the High Pass (world `north`)

A white hall (birch-trunk pillars with silver bands, banners with a leaf spray, silver lamps, a high chair, a vial on a pedestal, a table with an abstract inked chart: no real land, no writing), a porch and the snow pass
(slate, snow, pines, a cairn, the cave mouth and the ridge marker on the far wall; piece `storm`, a wall of snow switched off when the pass is calmed). People: `lady` (white robe, cape, circlet), `birch_folk` (white and silver wool,
pale sash).

### Map `deep_halls` (assets/story/deep_halls/): the Deep Halls and the Falls (world `deeps`)

A pillared dark (black-blue fluted columns, one cold hanging light), the lake (black, scrolling, the drowned thing rises as piece `drowned` at beat 46), a bridge and a ledge with the drums, the far hall, a tunnel and the top of the
falls (wet boardwalk, a boat at its landing, the Warden's horn on a rock, a starry sky, the waterfall wall scrolling).

### Map `ash_land` (assets/story/ash_land/): the marsh, the wall, the stair, the plain (world `marsh`) and the mountain (world `mountain`)

Seventeen sectors: the reed marsh (teal mist, bioluminescent lights with sad faces), the Black Wall (obsidian, a colossal gate with piece `gate_mouths`, a glowing crack, braziers, the riders), the riders' camp (tents, a stake and
chain, a fire), the stair of bells (three steps of cliff stair, three bell groups, the blind sentinel: a hood over a pale blank face), the ash plain (the Glass Mountain: a black obsidian cone with one red vent, a tower with a red light),
the throat (red vent rock, pulsing walls), the Drowned Spring (black pool, a shaft of white light as piece `shaft`, `swell` = the light swelling white at beat 48 of E12) and the Keeper's cavern (lit by the Ember on its altar alone,
`long_shadow` stretching at beat 32 of E13). People: `hollow_one` (grey species rig, wide pale eyes, barefoot, rags), `rider`, `captain` (bigger, bronze trim, a brighter glint), `sentinel`, Bram.
The Ember is the only warm light east of the ford except the braziers and the camp fire (the riders' own), and the vents.

## Verified

* `bash tools/test.sh` (see the commit message of the push for the counts): green, including `tests/test_run_ember.gd` (data, 145 BPM, the relaxed graph rules, endings and flags, acting in five states for the seven people you touch,
  hide and piece cast lines, the real scene entering through the bar portal with the tempo handoff and leaving by an ending, the snatched failure), the per-path matrix (the ember path under all four tap policies) and the Python content tests.
* `python3 tools/run/check_hotspots.py --path ember`: 0 errors, 19 warnings (all of one kind: a route whose chart pack differs from the default route's, i.e. the route lock, as in the main run). 15/15 scenes reachable, both endings
  and the way back reachable, 23 flags settable.
* `bash tools/run/walk_run.sh --path ember perfect kept taken lantern sloppy none` on the real scene (virtual clock, dummy audio): `run walk-through: OK`, 15 of 15 scenes visited. `perfect` plays E00 to the Drowned Spring
  (quenched) and back into the Warehouse; `kept` ends at the Keeper; `taken` goes through Taken (the tower's light) and back to the plain; `lantern` takes the lantern, the ridge and the horn.
* Shots looked at (Read tool): every scene at 28 beats (`docs/shots/ember/node_*.jpg`) and with the hotspot window open (`route_*.jpg`); the seven people in five states (`docs/shots/acting/ember_*.jpg`, five
  contact sheets `contact_acting_ember_<world>.jpg`). The lighting of the night scenes, the placement of the people and the three shots below were fixed after looking.
* Both endings and the setback are walked (above) and tested; the failure cinematic `ember.snatched` is tested through the real scene (`RW_RUN_BOT=blocks:1110`, `RW_RUN_SELECT=mountain.spring.pool@52`).

## Shots I am not happy with

* `route_*` shots of the dark scenes (Deep Halls, Falls, the Keeper): the people are small and dim at the default camera; the acting contact sheets show them well, the scenes themselves are moody rather than clear.
* `node_hollow_ford`: Bram and his lantern are at the edge of the picture (his hotspot is a beacon at the left); the riders and horses across the water read well.
* E12 and E13 (`node_mountain_spring`, `node_mountain_keeper`): the white shaft and the Ember read, but Bram and the Hollow One stand at the edges of a very dark cavern; the white swell (`swell`) and long shadow pieces
  are only seen late in the phase (beats 48 and 32) and were not shot.
* The Hollow One's skin reads cyan in the teal marsh (the grey species rig lit by teal light): intended gaunt grey, but the colour is the light's.

## Not verified

* Nothing was played on a phone, nothing was heard: the placeholders are synthesised numpy loops (bass-forward by measurement, never auditioned), the handoff and every scene ran on the virtual clock with the dummy audio driver.
  The owner's real loops (`content/imports/ember/<scene>/`, `beatshaper.py import --path ember`) are not in; they will need the loosening Stage 2 noted if they are 4-bar phrases.
* How the acts and faces read moving, and whether a person at beat 50 and an outcome at beat 62 are seen by someone looking at the pads (as in stage 1d): only still frames.
* The `swell`, `long_shadow`, `river_rise`, `rider_shadow`, `storm` and `drowned` pieces are shown on screen in shots only for the first two (`river_rise` in the lantern success strip, `storm` at E04's start, `gate_mouths` at E08); the
  others are validated and fired at their beats in tests but nobody looked at them.
* Frame times on a phone (the four maps were built on a desktop; the stage build of each map costs 75 to 250 ms and the prebuild runs in a cue-free guard before a portal or a world change).
* The Warehouse portal's look after an ending (Stage 6), and the home screen's section for the path (the data is there: `paths.ember`).
* `docs/MUSIC_HANDOFF.md` is not regenerated (Stage 6); the shopping list is in `content/paths/ember/music.json` and above.
