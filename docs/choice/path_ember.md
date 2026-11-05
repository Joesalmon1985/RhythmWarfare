# Ember Road: choice briefs (visual representation of every branching scene)

Path `ember` (15 scenes E00 to E14, 145 BPM, 1 beat = 0.414 s). Scope: every scene with 2 or more hotspots (all 15; E12 and E13 are endings with one way out, designed as one-ending scenes with two manners). Source of truth for ids: `content/paths/ember/run.json`, `content/paths/ember/hotspots/{hollow,north,deeps,marsh,mountain}.json`, maps `content/story/maps/{orchard,birch_hall,deep_halls,ash_land}.json`. Coverage: 37 of 37 hotspot ids in `content/paths/ember/hotspots/*.json` appear in this file, across 15 of 15 scenes (checked by script: every id and every scene section present).

## 0. How to read this brief

**Vocabulary (used by every section).** At any time exactly one option of a scene is CURRENT; at beat 0 it is the default. All others are REST. A touch on an option's thing makes it CURRENT within one beat; the previous CURRENT drops to REST in the same beat.

| word | meaning |
| --- | --- |
| REST | the option is not current: its thing/person shows the rest state |
| CUR | the option is current: its thing/person shows the current state; the world around it agrees |
| TOUCH | the 1-beat transition played at the moment of a touch (both the new CUR and the dropped one) |
| S / F | the commit outcome: success (on_success) / failure (on_failure) |
| `swap id -> sprite` | a map thing shows another sprite (new engine op, section 5) |
| `piece id on/off` | a map piece switched (existing op) |
| `act actor: act@face (look_at, prop)` | a directed act (existing `acting` contract; new phases `rest`, `current`, `touch`) |
| `gaze` | named bystanders `look_at` the CURRENT option's anchor (cheap and universal) |

**Standard person-option grammar (owner's rule).** REST: the person still makes the same gesture, smaller, with a sad / pleading face (`plea`, `sad`, `grief`). CUR: the same gesture, bigger, with a glad face (`happy`, `relief`, `tender`). TOUCH: nod or flare, one beat. Previously-current person: `sad` for one beat, then REST. Hostile or deceptive people (riders, captain, Hollow One) use the same grammar but their glad face is `smug` or `relief` and their REST is `sulk` or `plea`, so the player learns "they want me to choose them" without reading intent.

**Standard object-option grammar.** Physical state first (open / shut, barred / unbarred, lantern lit / out, rope taut / slack, cloth flying toward / limp, sail-like parts up / furled), light second. Where the scene has a person who cares (Bram, the Warden, the Hollow One), they stand, point or look at the CUR option (`gaze`).

**Standard laps rule (two laps per scene).** CUR / REST are STATE, not beats: they persist until a touch changes them, so lap 1 and lap 2 read identically. Story `cast` lines stay beat-driven; the engine plays them on lap 1 only (lap 2 repeats only the last block, beats 48 to 63, so the final choice is never silent). Tease: at beat 20 to 23 of lap 1 every non-default PERSON option performs its REST gesture twice at full amplitude, and every non-default OBJECT option does one visible physical move (cloth flaps toward it, a lamp flares, a door shifts) then settles. That is the first-time teach: "that one wants to be picked". Touches are accepted from lap 1 beat 0; if the engine only opens touches on lap 2, run the tease on lap 2 beats 0 to 7 instead.

**Colour is never the only cue.** Every CUR/REST pair below differs in silhouette (open vs shut, raised vs lowered arm, taut vs slack, lit lantern hung vs hung out) as well as in light.

**Camera facts used below.** The game view is a wide, short strip (about 1280 x 460 px of the 720 p screen) with a narrow horizontal field of view: an object more than about 20 degrees off the heading is off screen (measured from `docs/shots/ember/route_*.jpg`: the cave 17 degrees left of the heading sits 120 px from the screen edge). "View check" lines use the map coordinates and the waypoint yaw (rel angle = bearing to the thing + waypoint yaw, forward = -y at yaw 0) and must stay within +-20 degrees from the window camera. The window camera is the end of the good rail (perfect play); a missed block slides it onto the bad rail (+-40 to 80 degrees), so the options also have to read in the "queasy" sway: keep REST/CUR states legible by silhouette, not just position.

**Build notes for the implementer.** Things and pieces: add the entry to `tools/story/art/ember_spec.py` (THINGS table, 128 x 128 RGBA hard-alpha billboard standing on the bottom edge, size in metres given in each entry, pieces may be 256 x 128), draw in `tools/story/art/tex_ember_things.py` (the pixeltex helpers), place in `tools/story/ember_maps.py` (`m.thing(id, sprite, x, z, size=, anim=, piece=)`), rebuild with `python tools/story/build_ember.py`. People: new acts and faces in `src/story/story_character.gd` (ACTS, FACES, FACE_OF, SHEET_CYCLES) and `tools/story/art/people.py` / `people_sheets.py`; every `act@face` is baked only for the actors the data names (`tools/run/acting_data.py`, `tools/run/make_ember.py` regenerates `run.json` and `hotspots/*.json`). Hand props: add to `StoryCharacter.PROPS` and the prop drawing in `people.py`. Art scale: people are about 112 px tall at the front row (head 17 x 13); a prop reads at 8 to 14 px; a face change must read at the full head size and at LOD 2.

## 1. Summary table (all 15 branching scenes)

Verdict today = what the player gets now (blunt). Effort S (up to 3 sprites, no new act) / M (4 to 8 sprites or one new act) / L (more, or several new acts). Priority P1 (real branch, unreadable now), P2, P3 (endings, cosmetic).

| scene | options (hotspot ids) | default | verdict today | archetype chosen | effort | prio |
| --- | --- | --- | --- | --- | --- | --- |
| E00 Orchard (`hollow`) | `hollow.gate`, `hollow.ember_bowl` | gate | weak: bowl is 38 deg off screen; tapping it changes no picture | mechanism (gate) + dying grandmother's hand | S | P2 |
| E01 Ford (`hollow.ford`) | `hollow.ford.crossing`, `hollow.ford.lantern` | crossing | partial: the crossing is a ring at the camera's feet; Bram only nods | world state (river level) + companion beckon | M | P1 |
| E02 Inn (`hollow.inn`) | `hollow.inn.back_door`, `hollow.inn.hooded_man` | back door | unreadable: both options 50 to 107 deg off screen, only edge beacons | door barred / open + seated vs standing Warden | M | P1 |
| E03 Birch Hall (`north`) | `north.porch`, `north.ladys_hand`, `north.map_table` | porch | weak: porch and Lady stack on one line; table off screen | three advocates; doors, vial cover, map roll | L | P1 |
| E04 High Pass (`north.pass`) | `north.pass.cave_mouth`, `north.pass.ridge_path` | cave | weak: two edge beacons on a snow wall | wayfinding cairn (cloth flies toward the way) + companions | M | P1 |
| E05 Deep Halls (`deeps`) | `deeps.bridge`, `deeps.lake` | bridge | unreadable: both 20+ m away; the lake hotspot is a piece that is hidden until beat 46 | physical barrier (chain) + drum and water | M | P1 |
| E06 Falls (`deeps.falls`) | `deeps.falls.landing`, `deeps.falls.boat`, `deeps.falls.horn`, `deeps.falls.riders_horn` (horn pair exclusive by flag) | landing | unreadable: landing and horn behind the camera, boat at the edge | boat cast off / moored, jetty rope, horn raised, startled birds | L | P1 |
| E07 Reed Marsh (`marsh`) | `marsh.path`, `marsh.hollow_one`, `marsh.lights` | path | partial: the Hollow One reads, the lights are dim dots, the path 17 m away | tempters (hand, smiling lights) vs lit causeway | M | P1 |
| E08 Black Wall (`marsh.wall`) | `marsh.wall.crack`, `marsh.wall.gate` | crack | weak: gate reads, crack 62 deg off screen | gate bar / mouths vs choked or open crack + terrified guide | M | P1 |
| E09 Stair of Bells (`marsh.stair`) | `marsh.stair.side_path`, `marsh.stair.bells` or `marsh.stair.bells_hard`, `marsh.stair.sentinel` | side path | unreadable: camera ends beyond the bells and sentinel; all three behind it | the listening guard (head turns, staff) + bells muffled or loud | L | P1 |
| E10 Ash Plain (`marsh.plain`) | `marsh.plain.road`, `marsh.plain.tower` | road | weak: tower 49 deg off screen; its success is a trap with no cue | road lamps vs signal tower and saluting riders | M | P1 |
| E11 Throat (`mountain`) | `mountain.way_down`, `mountain.whisper` | way down | unreadable: the whisper vent is behind the camera (129 deg); the story's key fork | slab over the stair vs breathing arch; the Hollow One in the way | L | P1 |
| E12 Drowned Spring (`mountain.spring`) | `mountain.spring.way_back`, `mountain.spring.pool` | way back | cosmetic: same ending, both ahead | ending gesture (rim vs stones) | S | P3 |
| E13 Keeper (`mountain.keeper`) | `mountain.keeper.way_back`, `mountain.keeper.ember` | way back | cosmetic: same ending, both ahead | ending gesture (steps vs the lifted Ember) | S | P3 |
| E14 Taken (`mountain.taken`) | `mountain.taken.camp_out`, `mountain.taken.stake`, `mountain.taken.captain` | camp out | unreadable: stake and exit behind the camera (90 to 100 deg) | chain slack / taut, guards turn their backs, captain's open hand | M | P2 |

Worst three today: E09, E06, E11.

---

## 2. Scenes

### E00 The Orchard (`hollow`, map `orchard`)

**Story.** Gran lies dying on a cot in the orchard and leaves you the Ember; the village stands round, Bram weeps. The way on is the gate.
**Choice.** (Not a route fork: both options go on to the Ford; the second is the act of taking the Ember.)

| option | anchor | kind | S | F | default |
| --- | --- | --- | --- | --- | --- |
| `hollow.gate` | waypoint `orchard_gate` (re-anchor to thing `gate`) | exit | -> `hollow.ford` | -> `hollow.ford`, energy -5 | yes |
| `hollow.ember_bowl` | thing `ember_bowl` | object | stay in scene, flag `ember_held`, energy +6 | energy -3 | no (repeatable) |

**Today.** A gate ring at 8 m and an Ember in a bowl 38 deg off screen at the window; neither tap changes the picture, so the first choice in the game teaches nothing.
**Idea.** The first lesson of the whole game: "the thing you touch wakes, the other settles." Gate leaves swing wide (go) or half-shut; Gran lifts the Ember toward you (take it).
**View check** (camera `orchard_mid` (0,9.5), yaw 0; good rail ends here, drop `orchard_near`): gate 0 deg / 8 m; bowl 14 deg / 5 m after moving it to (1.1,5.1); cot 3 deg. Move `ember_bowl` and `lt_ember_o` to (1.1,5.1) / (1.1,4.9).

- `hollow.gate` (CUR from beat 0).
  Affordance: the gate at the lane end, with `lamp_o` lit beside it.
  REST: `swap gate -> thing_gate` (half open, as now); `vo1` hat on, arms folded.
  CUR: `swap gate -> thing_gate_wide` (both leaves back, lane visible and lit amber); `act vo1: nod@relief (look_at camera)` loop, hat in hand.
  TOUCH: leaves swing wide in two frames on the beat; `vo1` straightens and nods.
  S: camera walks through (existing). F: leaves stick, stagger through (existing).
- `hollow.ember_bowl`.
  Affordance: Ember pulsing on the kick (existing anim `pulse`), Gran's open hand lying beside the bowl.
  REST: `thing_ember` low in its bowl; `act gran: lie@relief (look_at camera)`.
  CUR: `piece_gran_hand_bowl` on (her hand lifts the bowl 0.3 m toward the camera); `piece_ember_flare` on, pulses on every kick and throws 6 sparks; `act gran: lie@tender (look_at camera)`; `act vo0..vo3: stare (look_at gran)`; gate swaps back to half.
  TOUCH: flare burst on the beat, hand lifts; the gate leaves swing half-shut. Tapping the gate reverses both.
  S: the flare stays as a warm rim on the cot as the camera leaves (`ember_held`). F: flare gutters, hand drops, `act bram_o: cover_face@grief` (existing).
- Story cast stays: Gran sleeps at 44, villagers bow at 52 to 53 (they override the gaze).
**Laps.** Standard. Tease: beat 20, Gran's hand lifts the bowl once and sets it down.
**Create.**
- [T] `thing_gate_wide` (map orchard, id `gate` swap target, size 2.0 m, one frame): leaves swung fully back, a lit lane behind.
- [P] `piece_gran_hand_bowl` (map orchard, 0.7 m, 2 frames: hand rising): a pale hand with the iron bowl and Ember lifted on its palm.
- [P] `piece_ember_flare` (shared by E00, E10, E13; 128 x 128, 3 frames: halo swell, sparks): a soft dithered orange bloom with 6 sparks.
- [F] `tender` (see section 3).
- Exists: `thing_gate`, `thing_ember`, `thing_cot`, Gran acts `lie`, `sleep`.
**Effort S, P2.**

---

### E01 The Ford at Night (`hollow.ford`, map `orchard`)

**Story.** Black river, three ash-grey riders with horses watching from the far bank; Bram stands on your bank with a lantern and pleads you to follow him upstream.

| option | anchor | kind | S | F | default |
| --- | --- | --- | --- | --- | --- |
| `hollow.ford.crossing` | waypoint `ford_cross` (re-anchor to new thing `ford_stones`) | exit | -> `hollow.inn` | -> `hollow.inn`, energy -5 | yes |
| `hollow.ford.lantern` | actor `bram_f` | character | -> `north`, flag `ember_bram_lamp`, cinematic `ember.river_rises` | -> `hollow.inn`, energy -8, cinematic `ember.bram_falls` | no |

**Today.** The crossing ring sits at the camera's feet (1 m) and is invisible; Bram is 4 m away at the left edge and only nods when touched. Nothing tells the player that Bram's way is upstream and the crossing is toward the riders.
**Idea: the river level is the choice.** CUR crossing: low silver water, the stones stand out of it, the horses stamp (you wade toward the riders). CUR Bram: Bram's lantern is raised high and the river swells over the stones at the crossing while the horses shy (his way shuts the ford behind you). The player sees "Bram's smile = the river rises between me and the riders".
**View check** (camera `ford_mid` (0,-23.4), yaw 0; trim the good rail to end here): Bram (move home to (-1.4,-28.6)) -15 deg / 5 m; `ford_stones` at (1.6,-30.4) +13 deg / 7 m; horses 2 deg / 13 m; `river_swell` 0 deg / 6 m.

- `hollow.ford.crossing` (CUR from beat 0).
  Affordance: a diagonal line of flat stones (`ford_stones`) from your bank to the riders' bank, water flat and silver.
  REST: `piece_river_swell` on (a low swell with foam crests rolling over the stones; stones awash); the lantern on `stake_l` dims.
  CUR: `piece_river_swell` off; stones stand clear of the water; `horse0..horse2` bob (existing); `act rd_f0..rd_f2: stare@anger (look_at camera)` (existing cast); `act bram_f: plead@plea` with the `lantern` prop held low at his chest, `look_at camera`.
  TOUCH: the swell recedes in one beat (foam line slides off), Bram's lantern drops, his face goes `plea`.
  S: wade across (existing). F: stagger (existing).
- `hollow.ford.lantern`.
  Affordance: Bram, lantern raised, beckoning.
  REST: as above (`plead@plea`, lantern low): he looks at you with a sad face.
  CUR: `act bram_f: beckon@happy` with the `lantern` raised overhead (`hold_up`); `piece_river_swell` on; `swap horse1 -> thing_horse_far_rear` (rears), `act rd_f0..rd_f2: recoil@fear (look_at river_swell)`; the stones are submerged.
  TOUCH: Bram's arm snaps up (`nod@relief` for one beat, then `beckon@happy`); the swell climbs the stones; horses rear. Previously-current crossing: the stones vanish under the swell.
  S: existing `river_rises` plus `act bram_f: cheer@relief`. F: `collapse@grief` (existing); his lantern prop is dropped with him and the swell stays low (the cold has reached him).
- Story cast (beat 0 to 63): riders stare at 0, stamp at 32 (horses bob); Bram's `plead` at 16 and 40 is REMOVED from the cast (it is now the REST state, shown continuously); `cover_face@fear` at 48 if energy below 35 stays but does not apply while Bram is CUR.
**Create.**
- [T] `thing_ford_stones` (map orchard, id `ford_stones`, 3.0 m wide, 1 frame): five flat stones in a diagonal, wet shine, water curling round them.
- [P] `piece_river_swell` (map orchard, id `river_swell`, 256 x 128, size 5.0 m, 2 frames: foam crest shifts): a low rolling swell with silver foam, translucent. (The existing `piece_river_rise` stays the commit wall.)
- [T] `thing_horse_far_rear` (swap target for `horse1`, 2.8 m, 1 frame): the horse reared, forelegs up, red glint.
- [R] `lantern` (hand prop; low and raised variants; also used in E06).
- [A] `hold_up` (see section 3).
- Exists: `thing_rock_ford`, `thing_horse_far`, `thing_lantern_stake`, `plead@plea`, `nod@relief`, `cheer@relief`, `collapse@grief`, riders' `stare@anger`, `stamp@anger`.
**Effort M, P1.**

---

### E02 The Lantern Inn (`hollow.inn`, map `orchard`)

**Story.** A warm common room, drinkers laughing, the innkeeper writing in a ledger; a hooded man (the Warden) sits by the fire and will beckon you. A rider's shadow crosses the window at beat 48 and the room freezes.

| option | anchor | kind | S | F | default |
| --- | --- | --- | --- | --- | --- |
| `hollow.inn.back_door` | waypoint `inn_back` (re-anchor to thing `door_back`, moved) | exit | -> `north` | -> `north`, energy -5 | yes |
| `hollow.inn.hooded_man` | actor `warden_i` | character | -> `north.pass`, flag `ember_warden_met` | -> `north`, energy -4 | no |

**Today.** From the window camera the back door is 107 deg and the Warden 49 deg off screen: the player sees a hearth and a wall of mugs and two edge beacons.
**Idea: the draught and the bar.** CUR back door: the door is ajar and the room's flames lean toward it (a draught), the innkeeper ushers you out with a sweep of the arm, the Warden sits hunched over the fire with his back to you. CUR Warden: the back door is shut and barred, the draught stops, the Warden stands, throws back his hood and beckons while the drinkers all turn to him.
**View check** (camera `inn_c` (20,-28.6), yaw 180, good rail ends here: drop `inn_mid`/`inn_near`): door moved to (17.4,-17.8) on the north wall left of the hearth, rel 14 deg / 11 m; Warden home moved to (22.4,-21.0), rel -18 deg / 8 m; hearth -6 deg.

- `hollow.inn.back_door` (CUR from beat 0).
  Affordance: a small low door ajar in the north wall, cold blue night in the gap.
  REST: `swap door_back -> piece_door_barred` shown as a piece over it (closed, a heavy oak bar across); lamps `lamp_i0`, `lamp_i1` anim `none`.
  CUR: `thing_door_back` ajar; `anim lamp_i0, lamp_i1: sway` (the draught); `act innkeeper: sweep_arm@neutral (look_at door_back)`; `act warden_i: sit@resolve (look_at hearth)` hood up, back to the room.
  TOUCH: the bar lifts off with a clack on the beat, the door swings ajar, the lamps start to sway; the Warden sinks back to `sit`.
  S: existing walk. F: stagger out (existing).
- `hollow.inn.hooded_man`.
  Affordance: the man in the grey cloak by the fire, a travel pack at his feet.
  REST: `act warden_i: sit@resolve` (seated, hood up, pack at his feet). The existing `beckon@resolve` is shown on a small scale at the tease only.
  CUR: `piece_door_barred` on (the way out is shut); lamps still; `act warden_i: beckon@resolve (look_at camera)` standing (`rise` first), pack on his shoulder (prop `pack`), hood down; `act dk0..dk3: look (look_at warden_i)` (drinkers turn to him); `act innkeeper: stare@doubt (look_at warden_i)` (existing).
  TOUCH: he rises (`rise`, 1 beat), the bar drops with a thud on the kick; the draught stops.
  S: `beckon@resolve` (existing). F: `shake_head@doubt` then `sit` again (existing plus `sit`); you leave by the back door.
- Story cast kept: laughs (0 to 45), rider's shadow at 48 to 60 and the room's `recoil@fear` at 50 (they override gaze for 12 beats; the Warden does not react, he is the only calm person).
**Create.**
- [P] `piece_door_barred` (map orchard, 2.3 m, 1 frame): the back door closed, an oak bar in iron brackets.
- [A] `rise`, `sweep_arm` (section 3). [R] `pack`.
- [N] none new (actors `warden_i`, `innkeeper`, `dk0..3` exist; moved door and `warden_i` home are data edits in `tools/story/ember_maps.py`).
- Exists: `thing_door_back`, `thing_hanging_lamp` (anim `sway` is an existing mode), `sit`, `beckon@resolve`, `shake_head@doubt`, `stare@doubt`, `look`.
**Effort M, P1.**

---

### E03 The Birch Hall (`north`, map `birch_hall`)

**Story.** A white hall; the Lady on her dais offers a vial; birch folk bow; the Warden at the map table. Flags: Lady's hand S sets `ember_vial`, F sets `ember_no_vial` (E09 gets harder).

| option | anchor | kind | S | F | default |
| --- | --- | --- | --- | --- | --- |
| `north.porch` | waypoint `hall_far` (re-anchor to thing `porch_door`, the placed `thing_door_far`) | exit | -> `north.pass` | -> `north.pass`, energy -5 | yes |
| `north.ladys_hand` | actor `lady` | character | -> `deeps`, flag `ember_vial` | -> `north.pass`, flag `ember_no_vial`, energy -6 | no |
| `north.map_table` | thing `table_map` | object | -> `north.pass`, flag `ember_map` | -> `deeps`, energy -4 | no |

**Today.** The porch door and the Lady are on the same line (the Lady in front of it); the table is 54 deg off screen. Only the Lady reads, and she offers from beat 4 whatever you pick.
**Idea: three advocates, one room.** The hall itself shows which way is current: CUR porch = the great doors open and snow drifts in, birch folk face the doors; CUR Lady = she steps forward holding the vial, doors close, folk bow to her; CUR table = the hide unrolls, the Warden's finger is on it, folk lean toward it.
**View check** (camera `hall_mid` (0,15.5), yaw 0; good rail ends here, drop `hall_dais`): porch door placed at (-2.4,1.0) -9 deg / 15 m; Lady (0,3.6) 0 deg / 12 m; table moved to (1.8,8.0) +13 deg / 8 m; `warden_h` moved to (0.6,7.4) +4 deg. Camera at 15 m: size the porch door 3.4 m.

- `north.porch` (CUR from beat 0).
  Affordance: tall pale double doors at the hall's end, blue-white light and a thread of snow blowing in.
  REST: `swap porch_door -> thing_door_far_shut` (closed, silver bands, one thin line of light); `piece_snow_drift` off.
  CUR: `thing_door_far` (ajar, light); `piece_snow_drift` on (snow across the floor); banners `banner0/1` anim `sway`; `act bf0..bf4: look (look_at porch_door)`; `act lady: stare@grief (look_at camera)`; `swap vial -> thing_vial_stand_covered`.
  TOUCH: the doors swing ajar on the beat and a puff of snow runs in.
  S/F: existing walk through.
- `north.ladys_hand`.
  Affordance: the Lady in white, arms out with a glowing vial.
  REST: `act lady: offer@grief` with prop `vial` (arms out, sad face), vial stand covered by a glass bell (`thing_vial_stand_covered`).
  CUR: `act lady: offer@tender` (prop `vial` raised, glowing) ; `swap vial -> thing_vial_stand_empty`; `lamp_h0, lamp_h1` brighten (existing lights); `act bf0..bf4: bow@relief (look_at lady)` once, then `look`; porch doors swap to shut.
  TOUCH: the glass bell lifts off the pedestal and the vial is in her hand in one beat; her face softens.
  S: `nod@relief` (existing). F: `shake_head@fear`, the vial is drawn back and the bell drops over the empty pedestal (existing acts plus the swap) and the hall `look`s away; flag `ember_no_vial`.
- `north.map_table`.
  Affordance: the long table, a rolled hide with a ribbon; the Warden stands beside it.
  REST: `swap table_map -> thing_table_map_rolled`; `act warden_h: stare@resolve (look_at porch_door)`.
  CUR: `thing_table_map` (hide unrolled, a faint ink river line); `act warden_h: point@resolve (look_at table_map)` (existing); `act bf0..bf4: look (look_at table_map)`.
  TOUCH: the hide unrolls with a flap on the beat; the Warden's hand lands on it.
  S: existing; F: the hide curls shut again by itself (`swap` back), the Warden `shake_head@doubt`.
- Existing story cast kept except `lady offer@awe` at 4 to 20 (it becomes the REST/CUR state) and `lady stare@grief` at 24 (now only while the porch is CUR). The cast bows at 40 to 42 become one-off at beat 40 and are overridden by gaze.
- Flag shown without text: `ember_no_vial` keeps the pedestal under its glass bell for the rest of the scene on a repeat visit, and is shown in E09 (the muffled vs loud bells).
**Create.**
- [T] `thing_door_far_shut` (map birch_hall, 3.4 m): closed pale doors, silver bands, thin light line. Place the existing `thing_door_far` as `porch_door`.
- [T] `thing_vial_stand_covered` (1.2 m): pedestal with the vial under a glass bell. [T] `thing_vial_stand_empty`: pedestal, bare.
- [T] `thing_table_map_rolled` (1.5 m): the hide rolled with a ribbon.
- [P] `piece_snow_drift` (256 x 128 low, 2 frames): a fan of snow across the floor.
- [R] `vial`. [F] `tender`. [A] none new.
- Exists: `thing_table_map`, `thing_vial_stand`, `offer@awe`, `bow`, `point`, `stare`, `shake_head`.
**Effort L, P1.**

---

### E04 The High Pass (`north.pass`, map `birch_hall`)

**Story.** Snow pass; Bram huddles from the wind, the Warden beckons; a storm wall (piece `storm`) calms if you take the cave. If the Warden is lost (flag `ember_warden_lost`, a setback from E05) he is gone.

| option | anchor | kind | S | F | default |
| --- | --- | --- | --- | --- | --- |
| `north.pass.cave_mouth` | thing `cave` | exit | -> `deeps`, cinematic `ember.pass_calm` | -> `deeps`, energy -5 | yes |
| `north.pass.ridge_path` | thing `ridge` | exit | -> `deeps.falls` | -> `deeps`, energy -6 | no |

**Today.** The cave and the ridge marker are 22 and 23 deg off the heading at the window: two small beacons on a grey snow wall.
**Idea: the way-cairn with its cloth.** A cairn at the fork carries a red cloth that streams toward the current way; the Warden points to it; Bram turns away from the ridge. When the Warden is gone, his grey cloak lies in the snow at the cairn's foot and the cloth is the only guide.
**View check** (camera `pass_far` (0,-15.2), yaw 0, existing top of rail): `cairn` moved to (0,-21.5) 0 deg / 6 m; `cave` moved to (-5.0,-31.3) -17 deg / 17 m; `ridge` moved to (5.2,-30.6) +19 deg / 16 m; `warden_p` to (1.0,-18.6).

- `north.pass.cave_mouth` (CUR from beat 0).
  Affordance: the cave mouth hung with icicles, a hung lantern.
  REST: `thing_cave_mouth` (dark, no lantern); handline slack.
  CUR: `swap cave -> thing_cave_mouth_lit` (a lantern hung on a hook at the mouth, lit, icicles dripping); `swap cairn -> thing_cairn_cloth_l` (cloth streams left); `act warden_p: point@resolve (look_at cave)`; `act bram_p: nod@relief (look_at cave)`; the storm piece stays on (it calms only on success).
  TOUCH: the cloth flips on the beat with a snap; the lantern flares.
  S: existing `pass_calm` (storm off, `nod@relief`). F: slide on the bad rail, `plead@plea` (existing).
- `north.pass.ridge_path`.
  Affordance: the leaning marker post at the ridge with its strip of cloth; a rope handline running up.
  REST: `swap ridge -> thing_ridge_marker_limp` (cloth hangs, rope slack in the snow).
  CUR: `thing_ridge_marker` (cloth snapping toward the ridge, rope taut); `swap cairn -> thing_cairn_cloth_r`; `act warden_p: point@resolve (look_at ridge)`; `act bram_p: recoil@fear (look_at storm)` and `shake_head@plea` toward the camera (he does not want the ridge: the player reads "risky").
  TOUCH: the cloth cracks across to the right on the beat, the rope tightens.
  S: the walk along the ridge (existing). F: slide (existing).
- Flag consequence (`ember_warden_lost`): `warden_p` hidden (existing); `piece_warden_cloak_snow` on at beat 0 (a grey cloak half-buried at the cairn's foot); `act bram_p` keeps the gaze and the `plead@plea` face toward the camera at REST.
- Story cast kept: storm on from 0, off at 56 if energy above 50; Bram's `recoil` at 0 and `cover_face@fear` at 44 if energy below 40 (this one does not apply to the option actors in the last block).
**Create.**
- [T] `thing_cairn_cloth_l`, [T] `thing_cairn_cloth_r` (map birch_hall, id `cairn`, 1.8 m, 2 frames each: the red cloth flaps).
- [T] `thing_cave_mouth_lit` (4.0 m): the existing cave mouth with a hung lantern lit.
- [T] `thing_ridge_marker_limp` (3.0 m): the leaning post, cloth limp, rope in the snow.
- [P] `piece_warden_cloak_snow` (0.9 m): a grey ranger's cloak in the snow.
- Exists: `thing_cairn` (red cloth), `thing_ridge_marker`, `thing_cave_mouth`, `piece_storm_snow`, acts `point`, `recoil`, `plead`, `nod`.
**Effort M, P1.**

---

### E05 The Deep Halls (`deeps`, map `deep_halls`)

**Story.** A pillared dark, a black lake, a stone bridge, a great drum pulsing from the ledge; at beat 46 the drowned thing rises. Companions stare in awe; the Warden braces to block it.

| option | anchor | kind | S | F | default |
| --- | --- | --- | --- | --- | --- |
| `deeps.bridge` | waypoint `bridge_wp` (re-anchor to new thing `bridge_head`) | exit | -> `deeps.falls` | -> `deeps.falls`, energy -5 | yes |
| `deeps.lake` | thing `drowned` (re-anchor to new always-visible thing `lake_swirl`) | encounter | -> `deeps.falls`, flag `ember_lake_calm` | -> `north.pass`, flag `ember_warden_lost`, energy -8, cinematic `ember.warden_falls` | no |

**Today.** The bridge hotspot sits 20 m away and the lake's anchor is a piece that is switched off until beat 46 (nothing to tap in lap 1). Both options are tiny at the window.
**Idea: the chain and the drum.** CUR bridge: the chain across the bridge head is down, the head lantern lit, the drum is still and the lake flat. CUR lake: the chain is slung across the bridge head (shut), the drum skin flares on every kick, rings spread on the lake over a pale hump, and the Warden steps to the water's edge and plants himself (`block`) while Bram shrinks behind him. The player reads "I am calling the thing out".
**View check** (camera `halls_edge` (0,18.8), yaw 0, existing): `bridge_head` at (0,0.4) 0 deg / 18 m (size 5 m); `lake_swirl` at (-3.6,-3.0) -9 deg / 22 m (size 6 m); drum +15 deg / 25 m. Companions stand 4 to 5 m ahead of the camera and are the foreground cue (their size carries the read).

- `deeps.bridge` (CUR from beat 0).
  Affordance: the bridge head with a hung lantern and a chain that lies slack on the stones.
  REST: `swap bridge_head -> thing_bridge_head_chained` (chain slung across the entrance at knee height, lantern out).
  CUR: `thing_bridge_head_open` (chain dropped, lantern lit); `anim drum: none` with `swap drum -> thing_drum` (calm skin); `swap lake_swirl -> thing_lake_swirl_calm`; `act warden_d: point@resolve (look_at bridge_head)`; `act bram_d: stare@awe (look_at bridge_head)`.
  TOUCH: the chain drops with a clatter on the beat and the lantern catches.
  S: existing walk; F: stagger across (existing).
- `deeps.lake`.
  Affordance: faint rings and a pale hump just under the water, the drum answering.
  REST: `thing_lake_swirl_calm` (a single faint ring); drum calm.
  CUR: `swap lake_swirl -> thing_lake_swirl_rings` (three expanding rings, a pale hump); `swap drum -> thing_drum_struck` and `anim drum: pulse` (skin lit, dust motes, hard on every kick); bridge chained; `act warden_d: block@resolve (look_at lake_swirl)`; `act bram_d: recoil@fear (look_at lake_swirl)`.
  TOUCH: the drum thumps and a ring spreads on the beat; the Warden's arms fold.
  S: the thing sinks (`piece drowned off`) and the Warden `bow@resolve`. F: existing `ember.warden_falls` (collapse, `cover_face@fear`).
- Story cast kept: the thing rises at beat 46 whatever you pick (the menace), the Warden `block` at 48 (now equals the CUR lake state); with `ember_alone` Bram is hidden.
- Flag consequence (`ember_warden_lost`, if you return here): `warden_d` hidden, `piece_warden_cloak_rail` on (his grey cloak snagged on the bridge chain).
**Create.**
- [T] `thing_bridge_head_open`, [T] `thing_bridge_head_chained` (map deep_halls, id `bridge_head`, 5.0 m).
- [T] `thing_lake_swirl_calm`, [T] `thing_lake_swirl_rings` (id `lake_swirl`, 6.0 m, the rings frame has 3 sub-frames).
- [T] `thing_drum_struck` (2.0 m): the drum with a lit skin and dust motes.
- [P] `piece_warden_cloak_rail` (1.2 m).
- Exists: `thing_drum` (anim pulse), `piece_drowned_thing`, `block`, `recoil`, `stare@awe`, `bow`.
**Effort M, P1.**

---

### E06 The Falls (`deeps.falls`, map `deep_halls`)

**Story.** The top of a waterfall at night; a boat at the landing, Bram beside it, the Warden by his horn on a rock. The company offers to come. Flags decide the horn: with `ember_warden_lost` the horn is a rider's horn and the Warden is gone.

| option | anchor | kind | S | F | default |
| --- | --- | --- | --- | --- | --- |
| `deeps.falls.landing` | waypoint `boat_wp` (re-anchor to new thing `jetty`) | exit | -> `marsh` | -> `marsh`, energy -5 | yes |
| `deeps.falls.boat` | actor `bram_fb` | character | -> `marsh`, flag `ember_bram_boat` | -> `marsh.wall`, flag `ember_alone`, energy -6 | no |
| `deeps.falls.horn` (needs not `ember_warden_lost`) | thing `horn` | object | -> `marsh.wall`, flag `ember_horn` | -> `marsh`, energy -4 | no |
| `deeps.falls.riders_horn` (needs `ember_warden_lost`) | thing `horn` | object | -> `mountain.taken`, flag `ember_horn_riders` | -> `marsh`, energy -6 | no |

**Today.** From the window the landing is 46 deg and the horn 70 deg off screen; Bram is -22 deg at the edge; four options (three live) are all beacons.
**Idea: three things on one shore.** Left: the boat (Bram at the oars); centre: the jetty (rope and steps down to the water); right: the Warden with his horn. CUR boat: the boat is cast off and drifting out, Bram standing with oars up, smiling; CUR jetty: the boat is moored, the jetty rope taut with its lantern lit, Bram sits waiting; CUR horn: the Warden has lifted the horn to his lips and a flock of birds rises off the lip rail.
**View check** (camera `falls_in` (0,-41.8), yaw 0; trim the good rail to hold here): boat and Bram moved to (-2.8,-50.8), -17 deg / 9 m; `jetty` at (0.2,-53.0), +1 deg / 11 m; `horn` moved to (2.7,-50.0), +17 deg / 9 m; `warden_f` (2.2,-52.2) +11 deg.

- `deeps.falls.landing` (CUR from beat 0).
  Affordance: a plank jetty with a rope rail and a lantern at its end.
  REST: `thing_jetty_dim` (rope slack, lantern out).
  CUR: `swap jetty -> thing_jetty_lit` (rope taut, lantern lit); `swap boat -> thing_boat` (moored, bobbing); `act bram_fb: sit@plea (look_at camera)` with the `oar` prop shipped; `act warden_f: point@resolve (look_at jetty)`.
  TOUCH: the rope snaps taut on the beat, the lantern lights.
  S/F: existing walk down (F staggers).
- `deeps.falls.boat`.
  Affordance: Bram in the boat, an oar in his hand.
  REST: `sit@plea` as above (sad face).
  CUR: `swap boat -> thing_boat_adrift` (rope cast off and coiled aboard, the boat angled out into the current, prow lantern lit); `act bram_fb: beckon@happy` standing with the `oar` raised; jetty swaps to dim.
  TOUCH: the boat swings out on the beat; Bram stands.
  S: `cheer@relief` (existing). F: `cover_face@grief` (existing) and the boat drifts away empty; Bram is gone from E07 on (hat afloat in E07, flag `ember_alone`).
- `deeps.falls.horn` (Warden alive).
  Affordance: the grey horn on its rock beside the Warden's cloak; a flock of dark birds perched on the lip rail.
  REST: `thing_horn` (as now), `piece_birds_perch` on.
  CUR: `swap horn -> thing_horn_rock_empty` (cloak on the rock, no horn); `act warden_f: hold_up@resolve (prop horn)` (horn to his lips); `piece_birds_perch off`, `piece_birds_rise on` (the flock lifts); `act bram_fb: look (look_at warden_f)`.
  TOUCH: he lifts the horn on the beat; the birds jump.
  S: the horn sounds, the flock goes, a far answering horn; F: he lowers it, no answer, birds settle (`piece_birds_perch on`).
- `deeps.falls.riders_horn` (Warden lost).
  Affordance: a black bone horn with a red band on the bare rock, hoofprints in the wet; the Warden's place is empty.
  REST: `thing_horn_rider` (dull).
  CUR: `swap horn -> thing_horn_rider_lit` (band glowing red); `piece_riders_far on` (three tiny riders on the far lip appear); `piece_birds_rise on` (black birds leave); `act bram_fb: recoil@fear (look_at horn)`.
  TOUCH: the red band flares on the beat and the riders' silhouettes appear.
  S: -> taken (the horn is answered: the riders arrive); F: the horn is silent, the silhouettes fade (-> marsh).
- Story cast kept: offers at 6 to 20 become the REST state (the company stands ready); Bram's `nod` at 36 and the Warden's `point` at 40 are the CUR states; `fear` at 52 if energy below 40 stays.
**Create.**
- [T] `thing_jetty_dim`, [T] `thing_jetty_lit` (map deep_halls, id `jetty`, 3.0 m).
- [T] `thing_boat_adrift` (2.6 m): the boat cast off angled out. (Existing `thing_boat` is the moored one.)
- [T] `thing_horn_rock_empty` (1.2 m): the rock and cloak without the horn.
- [T] `thing_horn_rider` and [T] `thing_horn_rider_lit` (1.2 m): the black horn, dull and glowing red.
- [P] `piece_birds_perch`, [P] `piece_birds_rise` (256 x 128, 3 frames), [P] `piece_riders_far` (256 x 128).
- [R] `oar`, `horn`. [A] `hold_up`, `sit@plea` (existing act `sit` with `plea`).
- Exists: `thing_boat`, `thing_horn`, `thing_rope_post`, `cheer@relief`, `cover_face@grief`, `offer`, `nod@resolve`, `point`.
**Effort L, P1.**

---

### E07 The Reed Marsh (`marsh`, map `ash_land`)

**Story.** Teal mist, lights under the reeds with sad almost-faces; the Hollow One beckons with a plea and, at beat 52, laughs behind your back. Bram stares in fear at the lights (absent if `ember_alone`).

| option | anchor | kind | S | F | default |
| --- | --- | --- | --- | --- | --- |
| `marsh.path` | waypoint `marsh_path` (re-anchor to new thing `causeway_post`) | exit | -> `marsh.wall` | -> `marsh.wall`, energy -5 | yes |
| `marsh.hollow_one` | actor `ho_m` | character | -> `marsh.stair`, flag `ember_hollow_trust` | -> `marsh.wall`, energy -6 | no |
| `marsh.lights` | thing `mlight1` | feature | -> `marsh.wall`, flag `ember_lights` | -> `marsh.stair`, energy -4 | no |

**Today.** The Hollow One is the only legible option; the lights are dim dots, the path is a ring 17 m away.
**Idea: two tempters and a plain road.** The causeway has a hung marker lantern and a rope rail; the Hollow One is a gaunt hand reaching; the lights are drowned faces. CUR tempter: he smiles (`relief`) and holds out a hand; or the lights draw into a line and their faces soften. CUR causeway: both tempters droop: his hand falls and he looks at his feet, the lights scatter and dim.
**View check** (camera `marsh_fwd` (0,18.6), yaw 0, existing): causeway post 0 deg / 17 m (size 3.0 m); `ho_m` moved to (1.6,13.2) +17 deg / 6 m; the light line centred at (-3.0,8.0) -16 deg / 11 m; `bram_m` moved to (-1.2,14.4) -16 deg / 4 m.

- `marsh.path` (CUR from beat 0).
  Affordance: a plank causeway with a hung lantern on its first post and reeds bent along it.
  REST: `thing_causeway_post_dark` (lantern out, rope slack).
  CUR: `swap causeway_post -> thing_causeway_post` (lantern lit, rope taut); `swap mlight0..mlight5 -> thing_marsh_light` scattered, `anim bob`; `act ho_m: plead@plea (look_at camera)`, hands clasped, shrunken; `act bram_m: nod@relief (look_at causeway_post)`.
  TOUCH: the lantern flares on the beat; the lights drift outward; the Hollow One's hands fall.
  S/F: existing (F staggers).
- `marsh.hollow_one`.
  Affordance: a grey gaunt figure with an outstretched hand and wide pale eyes.
  REST: `plead@plea` (as above).
  CUR: `act ho_m: beckon@relief (look_at camera)` (a thin, wrong smile), arm out at full length; `act bram_m: stare@doubt (look_at ho_m)`; causeway swaps dark.
  TOUCH: his arm straightens on the beat and the face goes `relief`.
  S: `beckon@happy` (existing). F: `shake_head@anger` (existing).
  Cast kept: `laugh@anger` at 52 facing away (reveals the lie) overrides.
- `marsh.lights`.
  Affordance: six lights bobbing at random, faces sad.
  REST: `thing_marsh_light` scatter, faces grief.
  CUR: `swap mlight0..mlight5 -> thing_marsh_light_calm` (eyes closed, a soft smile) and `piece_light_trail on` (a line of lights over the water leading off to the right); `act bram_m: recoil@fear (look_at mlight1)`; the Hollow One at REST.
  TOUCH: the lights snap into a line on the beat and their faces soften.
  S: -> wall; F: the line breaks, the faces turn to `grief` again.
- Flag consequence (`ember_alone`): `bram_m` hidden (existing) and `piece_hat_float` on (his straw hat afloat beside the causeway).
**Create.**
- [T] `thing_causeway_post`, [T] `thing_causeway_post_dark` (map ash_land, 3.0 m).
- [T] `thing_marsh_light_calm` (0.9 m, 2 frames bob).
- [P] `piece_light_trail` (256 x 128): a row of calm lights over water.
- [P] `piece_hat_float` (0.5 m): a straw hat afloat.
- Exists: `plead@plea`, `beckon@plea`, `beckon@happy`, `shake_head@anger`, `laugh@anger`, `thing_marsh_light`.
**Effort M, P1.**

---

### E08 The Black Wall (`marsh.wall`, map `ash_land`)

**Story.** A wall of black stone, a colossal gate guarded by three riders who `block`; the Hollow One points at a crack. At beat 34 the gate's mouths laugh.

| option | anchor | kind | S | F | default |
| --- | --- | --- | --- | --- | --- |
| `marsh.wall.crack` | thing `crack` (moved) | exit | -> `marsh.stair` | -> `marsh.stair`, energy -5 | yes |
| `marsh.wall.gate` | thing `gate_black` | encounter | -> `marsh.plain`, flag `ember_gate_open` | -> `mountain.taken`, energy -8, cinematic `ember.riders_seize` | no |

**Today.** The gate is 6 m ahead and reads; the crack sits 62 deg off screen at the window (an edge beacon).
**Idea: the guide's reaction decides it.** CUR crack: the Hollow One crouches at the slit beckoning low, ash trickles heavily and a thread of light shows; the gate is shut and silent. CUR gate: the gate's bar lifts a hand's width, the mouths grin and laugh, the riders stamp, the crack is choked with rubble and the Hollow One recoils shaking his head.
**View check** (camera `wall_c` (0,-4.2), yaw 0; the good rail holds here instead of walking to the gate): gate 0 deg / 19 m; `crack` moved to (4.6,-23.4) +13 deg / 20 m (size 3.6 m); `ho_w` moved to (3.4,-20.0) +12 deg / 16 m. The riders stand at 15 to 21 m ahead of the camera, so the gate is the largest picture.

- `marsh.wall.crack` (CUR from beat 0).
  Affordance: a tall narrow crack with ash falling and a warm thread of light.
  REST: `swap crack -> thing_wall_crack_choked` (rubble heaps in the slit, no trickle).
  CUR: `thing_wall_crack` (existing, with trickle and light); `piece_gate_mouths off`; `act ho_w: crouch_beckon@relief (look_at camera)` at the crack's foot; `act rd_w0..rd_w2: block@anger (look_at gate_black)` (they watch the gate, not you).
  TOUCH: ash pours on the beat, the rubble slides off.
  S/F: existing walk.
- `marsh.wall.gate`.
  Affordance: the colossal gate, a bar across its doors, the riders in front.
  REST: gate shut; riders `block@anger (look_at camera)` as cast.
  CUR: `piece_gate_bar_lift on` (the bar slides up a hand's width, a gap of red light); `piece_gate_mouths on` (laughing); `act rd_w0, rd_w2: stamp@anger`; `swap crack -> thing_wall_crack_choked`; `act ho_w: recoil@fear (look_at gate_black)` then `shake_head@plea` toward the camera.
  TOUCH: the bar jerks up and the mouths open on the beat; the guide flinches.
  S: the riders `block` -> part (existing `block`, then the walk); F: existing `riders_seize` (laugh, stamp) -> taken.
- Story cast: `piece gate_mouths on at 34` becomes `pulse` (the mouths only pulse in time; their steady state follows the CUR); `ho_w point@doubt (look_at crack)` at 16 is the CUR crack state; `ho_w stare@doubt` at 46 remains.
**Create.**
- [T] `thing_wall_crack_choked` (map ash_land, id `crack`, 3.6 m).
- [P] `piece_gate_bar_lift` (128 x 128): the gate's bar raised with a gap of light.
- [A] `crouch_beckon`.
- Exists: `thing_wall_crack`, `thing_gate_black`, `piece_gate_mouths`, riders `block@anger`, `stamp@anger`, `ho_w` acts `point@doubt`, `stare@doubt`, `shake_head`.
**Effort M, P1.**

---

### E09 The Stair of Bells (`marsh.stair`, map `ash_land`)

**Story.** A cliff stair hung with three bell groups and guarded by a blind sentinel (a hood over a pale blank face) who listens; the Hollow One covers his face in shame. Flag `ember_no_vial` (E03) replaces the plain bells option with the hard one.

| option | anchor | kind | S | F | default |
| --- | --- | --- | --- | --- | --- |
| `marsh.stair.side_path` | waypoint `stair_side` (re-anchor to new thing `stair_gap`) | exit | -> `marsh.plain` | -> `marsh.plain`, energy -5 | yes |
| `marsh.stair.bells` (needs not `ember_no_vial`) | thing `bells` | feature | -> `marsh.plain`, flag `ember_bells_silent` | -> `marsh.plain`, energy -6 | no |
| `marsh.stair.bells_hard` (needs `ember_no_vial`) | thing `bells` | feature | -> `marsh.plain`, flag `ember_bells_silent` | -> `mountain.taken`, energy -8, cinematic `ember.riders_seize` | no |
| `marsh.stair.sentinel` | actor `sentinel` | encounter | -> `mountain`, flag `ember_sentinel_asleep`, cinematic `ember.sentinel_sleeps` | -> `mountain.taken`, energy -8, cinematic `ember.riders_seize` | no |

**Today.** The good rail ends at `stair_up` (18,-53), past the bells and the sentinel, so all three options are behind the camera at the window (the side path 159 deg). The player sees a dark stair and edge beacons.
**Idea: the guard's ear.** A blind guard is a gift: his head and staff are the pointer. CUR side path: he faces the bells (they sway softly, drawing his ear) and the staff stands upright; a hung lantern marks the gap in the balustrade. CUR bells: he turns his head up to the bells, his hand cupped (`listen`); the bells are wrapped / frosted (vial) or loud and thrashing (no vial). CUR sentinel: he lowers his staff and faces the camera, listening at you, the Hollow One backs off.
**View check** (new waypoint `stair_choice` (18.5,-33.0), yaw 0, stair sector `al_stair_a`; the good rail ends here, trim `stair_mid` and `stair_up`): sentinel moved to (16.4,-47.0) -9 deg / 14 m; bells (18,-50.5) -2 deg / 18 m; `stair_gap` at (22.4,-45.0) +18 deg / 13 m. Sizes: sentinel 2.0 m; bells 4.6 m; gap 3.0 m.

- `marsh.stair.side_path` (CUR from beat 0).
  Affordance: a gap in the stair's balustrade with a rope rail and a hung lantern, a ledge beyond.
  REST: `thing_stair_gap_dark` (no lantern, rope slack).
  CUR: `swap stair_gap -> thing_stair_gap_lit`; `act sentinel: listen@neutral (look_at bells)`, staff upright (prop `staff`); bells `anim sway` (soft); `act ho_b: cover_face@shame` (cast).
  TOUCH: the lantern lights on the beat; the sentinel's head turns toward the bells.
  S/F: existing walk (F staggers).
- `marsh.stair.bells` (vial) / `marsh.stair.bells_hard` (no vial).
  Affordance: the bell row on its beam, ropes hanging.
  REST (vial): `thing_bell_row` as now, swaying; (no vial) `swap bells -> thing_bell_row_hard` (bright clappers, thick thrashing ropes, drawn sound arcs).
  CUR (vial): `swap bells -> thing_bell_row_muffled` (white cloth wraps round the clappers, frost on the bronze, still); `act sentinel: listen@neutral (look_at bells)`, head tilted up; (no vial) the hard bells keep swinging and the ropes tighten under an invisible hand (`anim bells: pulse`), `act ho_b: shush@shame` (finger to his lips); `act sentinel: listen (look_at bells)`.
  TOUCH: the wraps drop over the clappers on the beat (vial) or the ropes snap taut (no vial); the sentinel's head swings up.
  S: bells silent, the walk up; F (vial): they chime once and the sentinel's head snaps to you (-> plain); F (no vial): the full ring, the sentinel `stamp`s (-> taken).
- `marsh.stair.sentinel`.
  Affordance: the hooded blind guard standing across the stair, staff held crosswise.
  REST: `act sentinel: block@neutral` with the staff crosswise.
  CUR: `act sentinel: listen@neutral (look_at camera)` with the staff lowered to the stone; bells `anim none`; `act ho_b: recoil@shame (look_at sentinel)`.
  TOUCH: the staff comes down with a clack on the beat; his head turns to you.
  S: `bow@neutral`, then `sleep` (existing); F: `stamp@anger` (existing).
- Story cast kept: `sentinel stare` 0 to 40 is replaced by the REST/CUR states; `ho_b cover_face@shame` at 24 and the 52 `stare@shame` stay.
- Flag consequences shown without text: `ember_no_vial` = the loud bells (REST sprite above); `ember_sentinel_asleep` on a revisit = `act sentinel: sleep` and the staff down.
**Create.**
- [T] `thing_bell_row_hard`, [T] `thing_bell_row_muffled` (map ash_land, id `bells`, 4.6 m).
- [T] `thing_stair_gap_dark`, [T] `thing_stair_gap_lit` (id `stair_gap`, 3.0 m).
- [A] `listen`, `shush`. [R] `staff`.
- Move home of `sentinel` to (16.4,-47.0); new waypoint `stair_choice` in `ember_maps.py` and `run.json` `place`.
- Exists: `thing_bell_row` (anim sway), `thing_bell`, `block`, `bow`, `sleep`, `stamp`, `cover_face@shame`.
**Effort L, P1.**

---

### E10 The Ash Plain (`marsh.plain`, map `ash_land`)

**Story.** A grey plain under a red sky, the Glass Mountain ahead; riders cross in the distance; the Hollow One pleads for the Ember; Bram (if present) offers water.

| option | anchor | kind | S | F | default |
| --- | --- | --- | --- | --- | --- |
| `marsh.plain.road` | waypoint `road_wp` (re-anchor to new thing `road_post0`) | exit | -> `mountain` | -> `mountain`, energy -5 | yes |
| `marsh.plain.tower` | thing `tower` (moved) | feature | -> `mountain.taken` (a trap), flag `ember_tower` | -> `mountain`, energy -4 | no |

**Today.** The tower is 49 deg off screen; its success sends the player to the riders' camp with no cue that it is a trap.
**Idea: lamps and a salute.** The road to the mountain is marked by three cold lamp posts; the tower is the riders' signal beacon with a lookout. CUR road: the lamps are lit, Bram offers water, the Hollow One tugs at your sleeve toward the road, the Mountain's vent flares. CUR tower: the lamps go out, the tower's beam sweeps the plain, the lookout and the distant riders stop and salute it, the Hollow One kneels and Bram recoils. The player reads "the riders' place".
**View check** (camera `plain_far` (-2,-49.5), yaw 0, existing): `road_post0` (-1,-60.0) near the road end; the road centre 3 deg / 19 m; `tower` moved to (-6.4,-64.5) -16 deg / 16 m (size 8 m); `ho_pl` -17 deg / 5 m (move to (-1.0,-54.0), -7 deg).

- `marsh.plain.road` (CUR from beat 0).
  Affordance: three low posts leading away toward the Mountain.
  REST: `thing_road_post_dark` (lamps out).
  CUR: `swap road_post0, road_post1, road_post2 -> thing_road_post_lit`; `act bram_pl: offer@relief` with prop `water_skin` (existing cast made state); `act ho_pl: tug@relief (look_at road_post0)`; `piece_ember_flare` small on the vent `vent_p`.
  TOUCH: the posts light one after another on the three beats; Bram's arm lifts.
  S/F: existing walk.
- `marsh.plain.tower`.
  Affordance: the dark tower and its single pale-red light.
  REST: `thing_tower_light` as now (steady, pulse); `rd_tw` (lookout) `stare@anger (look_at camera)`.
  CUR: `piece_tower_beam on` (a sweeping beam of red-white across the plain); `swap road_post0..2 -> thing_road_post_dark`; `act rd_tw: salute@resolve (look_at camera)`; `act rd_pl0..rd_pl2: salute@resolve (look_at tower)`; `act ho_pl: kneel@plea (look_at camera)`; `act bram_pl: recoil@fear (look_at tower)`.
  TOUCH: the beam swings across the screen on the beat; the lookout snaps to a salute.
  S: you walk up to the riders (existing; -> taken); F: the beam goes out and the riders drop their salutes, `stare@anger`.
- Story cast: riders `stare@anger` 0 to 28 stay; `ho_pl plead` at 16 and 42 and `bram_pl offer` at 24 are the REST/CUR states.
- Flag consequences: `ember_alone`: `bram_pl` hidden, `piece_skin_hung` on (his water skin hung on a dead tree at the road side). `ember_tower` only matters in E14.
**Create.**
- [T] `thing_road_post_dark`, [T] `thing_road_post_lit` (map ash_land, ids `road_post0..2` at (-1,-60), (-1.6,-64), (-0.6,-68), 1.8 m).
- [P] `piece_tower_beam` (256 x 128, 2 frames sweep). [P] `piece_skin_hung` (0.6 m).
- [N] `rd_tw`: a rider instance (existing `rider` wardrobe) at the tower foot (-6.4,-63.6) in sector `al_plain`.
- [R] `water_skin`. [A] `tug`. [F] none new.
- Exists: `thing_tower_light`, `thing_vent_glow`, `piece_ember_flare` (E00), `salute`, `kneel`, `recoil`, `offer@relief`.
**Effort M, P1.**

---

### E11 The Throat (`mountain`, map `ash_land`)

**Story.** A red-lit tunnel, walls pulsing with the bass (the Ember's whisper). The Hollow One follows with an angry stare. The scene is the story's real fork: down to the water (to quench) or listen to the whisper (to keep). Whisper S leads to E13 (kept); F leads down to the spring.

| option | anchor | kind | S | F | default |
| --- | --- | --- | --- | --- | --- |
| `mountain.way_down` | waypoint `down_wp` (re-anchor to new thing `stair_slab`) | exit | -> `mountain.spring` | -> `mountain.spring`, energy -5 | yes |
| `mountain.whisper` | thing `vent1` (re-anchor to new thing `keeper_arch`) | feature | -> `mountain.keeper`, flag `ember_listened` | -> `mountain.spring`, energy -6 | no |

**Today.** The window camera ends at `throat_low`, past the vent: the whisper vent is 129 deg behind it. The player sees red walls and a ring at the far end.
**Idea: a slab and a breathing arch, and a body in the way.** CUR down: a slab is rolled aside from the head of a cut stair that breathes cold blue mist and dripping water; the Hollow One stands in front of it with folded arms and a furious face. CUR whisper: the slab sits across the stair (only a blue gap), the arch in the right wall flares and draws the ash toward it, the Hollow One steps aside, beckons toward it with a smug face. The player reads the tug between cold and warm, no letters.
**View check** (camera `throat_c` (0,-76.0), yaw 0, existing arrival; the rail holds here, trim `throat_low`): `stair_slab` (0,-94.6) 0 deg / 19 m (size 3.4 m); `keeper_arch` moved to (3.4,-88.0) +17 deg / 12 m (inside the 8 m wide tunnel; size 3.0 m); `ho_t` moved to the fork at (1.2,-91.0), +5 deg / 15 m.

- `mountain.way_down` (CUR from beat 0).
  Affordance: a stair cut down at the tunnel's end, cold mist and a drip.
  REST: `thing_throat_stair_slab` (a basalt slab lies across the stair head, a thin blue gap).
  CUR: `swap stair_slab -> thing_throat_stair_open` (slab rolled aside, steps into blue mist, a drip falling in time); `keeper_arch` swaps dull; `act ho_t: block@anger (look_at stair_slab)` standing at the stair head, arms folded; `anim vent0, vent2: pulse` continues (the whisper does not stop).
  TOUCH: the slab grinds aside on the beat; the Hollow One steps into the way.
  S/F: existing walk (F staggers).
- `mountain.whisper`.
  Affordance: an archway in the right wall breathing red, ash drifting into it.
  REST: `thing_keeper_arch_dull` (dim, no draw).
  CUR: `swap keeper_arch -> thing_keeper_arch_flare` (mouth open, white-orange rim); `piece_ash_draw on` (ash sweeps into it); `swap stair_slab -> thing_throat_stair_slab`; `act ho_t: beckon@smug (look_at keeper_arch)`.
  TOUCH: the arch flares on the kick, the ash is drawn, the slab drops across the stair; the Hollow One turns from the stair.
  S: -> keeper; F: the flare gutters, he turns back, `stare@anger` (-> spring).
- Story cast: `ho_t stare@anger` 0 to 56 is replaced by the REST/CUR states (REST uses `sulk` toward the camera when the arch is not current, face described in section 3).
**Create.**
- [T] `thing_throat_stair_slab`, [T] `thing_throat_stair_open` (map ash_land, id `stair_slab`, 3.4 m).
- [T] `thing_keeper_arch_dull`, [T] `thing_keeper_arch_flare` (id `keeper_arch`, 3.0 m).
- [P] `piece_ash_draw` (128 x 128, 3 frames).
- [F] `smug`, `sulk`.
- Exists: `block@anger`, `beckon`, `stare@anger`, `thing_vent_glow` (pulse).
**Effort L, P1.**

---

### E12 The Drowned Spring (`mountain.spring`, ending `quenched`, map `ash_land`)

**Story.** A black pool under a shaft of white light. Both options end at the Warehouse with `keep:path_ember_quenched`; they differ in how the Ember reaches the water. Note: not a branch; do not give either option a visual that implies another ending.

| option | anchor | kind | S | F | default |
| --- | --- | --- | --- | --- | --- |
| `mountain.spring.way_back` | waypoint `pool_wp` (re-anchor to new thing `pool_rim`) | exit | -> `run:warehouse`, flag `keep:path_ember_quenched` | same, energy -5 | yes |
| `mountain.spring.pool` | thing `pool_stones` | feature | -> `run:warehouse`, same flag | same flag, cinematic `ember.snatched` | no |

**Today.** Both ahead and in view (16 m and 9 m); nothing distinguishes them.
**Idea.** Rim: you set the Ember down at the edge; stones: you wade to the lit ring of stones in the shaft. CUR rim: the shaft is narrow, the Hollow One at the rim pleads with open hands, Bram stands by. CUR stones: the shaft widens onto the ring, a slow whirl turns in the pool, the Hollow One kneels at the stones; Bram watches the stones.
**View check** (camera `spring_c` (0,-100.5), yaw 0, existing): `pool_rim` (0,-109.4) 0 deg / 9 m; `pool_stones` 0 deg / 16 m; both centred, in depth; keep them apart by offsetting `pool_rim` to (-1.6,-109.4) (-10 deg).

- `mountain.spring.way_back` (CUR from beat 0).
  REST: `thing_pool_rim` (a worn stone lip, dull).
  CUR: `piece_light_shaft` narrow (existing); `act ho_s: plead@plea (look_at pool_rim)` at the rim; `act bram_s: stare@relief (look_at pool_rim)`.
  TOUCH: ripples run to the rim on the beat.
  S/F: existing.
- `mountain.spring.pool`.
  REST: `thing_pool_stones` (existing).
  CUR: `swap pool_stones -> thing_pool_stones_lit` (the white of the shaft on the ring); `piece_pool_whirl on` (slow rings turning inward); `act ho_s: kneel@plea (look_at pool_stones)`; `act bram_s: stare@awe (look_at pool_stones)`.
  TOUCH: the whirl starts on the beat; the Hollow One drops to his knees.
  S: existing; F: `ember.snatched` (existing).
- Story cast: `ho_s plead`, `recoil` at 28, `bram_s cheer` at 40, `swell` at 48 are kept as the ending's story.
**Create.**
- [T] `thing_pool_rim` (map ash_land, 2.4 m), [T] `thing_pool_stones_lit` (3.0 m).
- [P] `piece_pool_whirl` (256 x 128, 3 frames).
- Exists: `plead@plea`, `kneel`, `piece_light_shaft`, `piece_white_swell`, `stare@awe`.
**Effort S, P3.**

---

### E13 The Keeper (`mountain.keeper`, ending `kept`, map `ash_land`)

**Story.** The cavern lit by the Ember alone on its altar; Bram recoils; the Hollow One laughs and bows; the camera's own shadow lengthens (beat 32). Both options end at the Warehouse with `keep:path_ember_kept`. Not a branch: the second option is how you take the Ember.

| option | anchor | kind | S | F | default |
| --- | --- | --- | --- | --- | --- |
| `mountain.keeper.way_back` | waypoint `ember_wp` (re-anchor to new thing `altar_steps`) | exit | -> `run:warehouse`, flag `keep:path_ember_kept` | same, energy -5 | yes |
| `mountain.keeper.ember` | thing `altar` | feature | -> `run:warehouse`, same flag | same flag, energy -4 | no |

**Today.** Both ahead, in view at the window camera; indistinguishable.
**Idea.** Steps: you walk up to it; the Ember: your hand takes it (it floats up toward the camera, the shadow of the camera stretches). CUR steps: the Ember sits on the altar, Bram backs away, the Hollow One bows. CUR Ember: the Ember rises off the stone toward the lens, flare, the long shadow on, the Hollow One laughs.
**View check** (camera `keep_mid` (24.4,-99.0), yaw 0, existing): `altar` +3 deg / 13 m; `altar_steps` placed at (25.0,-108.0) +3 deg / 9 m.

- `mountain.keeper.way_back` (CUR from beat 0).
  REST: `thing_altar_steps` (three worn steps).
  CUR: `thing_ember_altar` as now (resting); `act bram_k: recoil@fear (look_at altar)`; `act ho_k: bow@smug (look_at camera)`.
  TOUCH: a spark leaps on the beat.
  S/F: existing.
- `mountain.keeper.ember`.
  REST: as above.
  CUR: `piece_ember_lift on` (the Ember floats 0.5 m above the stone toward the camera, flare); `piece_long_shadow on` (the camera's shadow, existing piece) in lap 1 as soon as touched; `act ho_k: laugh@laugh (look_at camera)`.
  TOUCH: the Ember lifts on the beat; the cavern's shadows swing.
  S/F: existing.
- Story cast kept (Bram `recoil` 0 to 40, Hollow One `laugh` at 16, `bow` at 40, shadow at 32 on).
**Create.**
- [T] `thing_altar_steps` (map ash_land, 2.4 m). [P] `piece_ember_lift` (128 x 128, 2 frames).
- Uses `piece_ember_flare` (E00).
- Exists: `thing_ember_altar`, `piece_long_shadow`, `recoil@fear`, `laugh@laugh`, `bow`.
**Effort S, P3.**

---

### E14 Taken (`mountain.taken`, setback, map `ash_land`)

**Story.** The riders' camp: tents, a stake with a chain, a fire; riders laugh and stamp; the captain offers your life for the Ember; Bram (if present) pleads.

| option | anchor | kind | S | F | default |
| --- | --- | --- | --- | --- | --- |
| `mountain.taken.camp_out` | waypoint `stake_wp` (re-anchor to new thing `camp_gap`) | exit | -> `marsh.plain` | -> `marsh.plain`, energy -5 | yes |
| `mountain.taken.stake` | thing `stake` | object | -> `marsh.plain`, flag `ember_escaped` | -> `marsh.wall`, energy -6 | no |
| `mountain.taken.captain` | actor `captain` | encounter | -> `marsh.wall`, flag `ember_bargain` | -> `marsh.plain`, energy -10 | no |

**Today.** The camera faces the captain (+2 deg), but the stake and the exit are at 90 to 100 deg: behind the camera.
**Idea: the chain, the gap and the open hand.** CUR camp out: the chain across the gap between two tents is dropped and the plain shows beyond; the guards face the captain, the stake chain is taut. CUR stake: the stake leans in the ash with its chain slack and the shackle open, two guards turn their backs. CUR captain: he steps up with his hand open, palm up, the riders arrange in a semicircle facing you and laugh.
**View check** (camera `camp_in` (-15.4,-12.0), yaw 90, existing arrival; the rail holds here): captain (-26.0,-12.4) +2 deg / 11 m; `stake` moved to (-23.4,-14.2) +17 deg / 9 m; `camp_gap` placed at (-23.2,-9.8) -17 deg / 8 m. Riders `rd_c0..2` stand around the captain.

- `mountain.taken.camp_out` (CUR from beat 0).
  Affordance: a gap between two tents with a post at each side, a chain across it.
  REST: `thing_camp_gap_closed` (chain slung across the gap, a rider's boot on it).
  CUR: `swap camp_gap -> thing_camp_gap_open` (chain on the ground, the plain's grey beyond); `act captain: stare@resolve (look_at camera)`; `act rd_c0, rd_c1: laugh@laugh (look_at captain)`.
  TOUCH: the chain drops with a clank on the beat.
  S/F: existing walk.
- `mountain.taken.stake`.
  Affordance: the chained stake at the camp edge.
  REST: `thing_stake` (taut chain, shackle closed).
  CUR: `swap stake -> thing_stake_loose` (leaning, earth crumbling, chain slack, shackle open); `act rd_c0, rd_c1: turn_away@neutral` (backs to you, watching the fire).
  TOUCH: the stake lurches on the beat; two guards turn.
  S: `ember_escaped` (existing). F: the guards snap round, `stamp@anger` (existing `stamp`).
- `mountain.taken.captain`.
  Affordance: the captain with his hand out.
  REST: `act captain: stare@resolve (look_at camera)`.
  CUR: `act captain: offer@smug` (palm up, one step toward you; a brighter glint); `act rd_c0..rd_c2: laugh@laugh`; `act bram_c: plead@plea` if present.
  TOUCH: he steps forward on the beat.
  S: `bow@resolve` (existing); F: `laugh@laugh` (existing).
- Story cast kept: riders laugh 0 to 20, stamp at 22 to 24; captain `offer` at 16 is now the CUR state; Bram's `plead` at 8 stays.
**Create.**
- [T] `thing_camp_gap_closed`, [T] `thing_camp_gap_open` (map ash_land, id `camp_gap`, 3.0 m).
- [T] `thing_stake_loose` (2.4 m).
- [A] `turn_away`. [F] `smug`.
- Exists: `thing_stake`, `thing_tent`, `stare@resolve`, `offer@resolve`, `laugh@laugh`, `stamp@anger`, `plead@plea`.
**Effort M, P2.**

---

## 3. New acts, faces and props (shared definitions)

At the game's pixel rig (head 17 x 13, body about 112 px, hands 3 to 5 px). Each is baked only for the actors that use it.

Faces:
- `tender`: brows relaxed and up at the inner ends, eyes closed in two soft crescents, mouth a small closed smile, one cheek pixel. Used: Gran (E00), Lady (E03).
- `smug`: one brow up and one flat, lids half-lowered, one mouth corner up two pixels. Used: Hollow One (E11, E13), captain (E14).
- `sulk`: brows down and in, eyes cut sideways, lower lip pushed out. Used: Hollow One REST when not chosen (E11).
Acts (cycle in beats, frames):
- `hold_up` (2, 4): one arm raised overhead holding a prop (lantern, horn, vial), weight on the back foot.
- `sweep_arm` (2, 6): one arm swept toward the `look_at` target, torso half-turned, a small bow of the head ("this way").
- `rise` (2, 6): from `sit`, stand; ends in the idle stance.
- `turn_away` (4, 4): back to the camera, head down, shoulders sagging (rejected). Riders' version: turn their back, glint dimmed.
- `tug` (2, 6): one hand reaching toward the camera as if pulling a sleeve, body leaning back.
- `crouch_beckon` (2, 6): squat, the `beckon` arm low at ground level.
- `shush` (2, 4): finger to the lips, the other hand flat.
- `listen` (4, 4): a hand cupped at the ear, head tilted toward `look_at`.
Props (hand props, `StoryCharacter.PROPS`): `lantern`, `vial`, `oar`, `horn`, `pack`, `staff`, `water_skin`.
Rider glints: the faceless rider's "face" is its glint: map `anger` = two wide bright glints, `laugh` = two squeezed crescents, `fear` = glints off, `resolve` = steady dim glints. No new rider face is needed.

## 4. New assets and expressions: roll-up

Counts (unique names; each thing is one 128 x 128 sprite, a few have a 2 to 3 frame loop noted in the entry; each piece 128 x 128 or 256 x 128):

| scene | new things (sprites) | new pieces (first use) |
| --- | --- | --- |
| E00 | 1 | 2 |
| E01 | 2 | 1 |
| E02 | 0 | 1 |
| E03 | 4 | 1 |
| E04 | 4 | 1 |
| E05 | 5 | 1 |
| E06 | 6 | 3 |
| E07 | 3 | 2 |
| E08 | 1 | 1 |
| E09 | 4 | 0 |
| E10 | 2 | 2 |
| E11 | 4 | 1 |
| E12 | 2 | 1 |
| E13 | 1 | 1 |
| E14 | 3 | 0 |
| total | 42 | 18 |

| kind | count | names |
| --- | --- | --- |
| New things (state sprites, swap targets, new placed props) | 42 | listed per scene under Create |
| New pieces | 18 | `piece_gran_hand_bowl`, `piece_ember_flare`, `piece_river_swell`, `piece_door_barred`, `piece_snow_drift`, `piece_warden_cloak_snow`, `piece_warden_cloak_rail`, `piece_birds_perch`, `piece_birds_rise`, `piece_riders_far`, `piece_light_trail`, `piece_hat_float`, `piece_gate_bar_lift`, `piece_tower_beam`, `piece_skin_hung`, `piece_ash_draw`, `piece_pool_whirl`, `piece_ember_lift` |
| New faces | 3 | `tender`, `smug`, `sulk` |
| New acts | 8 | `hold_up`, `sweep_arm`, `rise`, `turn_away`, `tug`, `crouch_beckon`, `shush`, `listen` |
| New hand props | 7 | `lantern`, `vial`, `oar`, `horn`, `pack`, `staff`, `water_skin` |
| New wardrobe archetypes | 0 | all people are existing archetypes (`bram`, `warden`, `lady`, `hollow_one`, `rider`, `captain`, `sentinel`, `birch_folk`, `villager_hollow`, `innkeeper`, `drinker`, `grandmother`) |
| New actor instances | 1 | `rd_tw` (a rider, the tower lookout, E10) |
| New map waypoints | 1 | `stair_choice` (E09) |
| New engine ops | 1 | `swap` (thing sprite swap) plus the `state` / `rest` / `current` / `touch` / `gaze` acting phases (section 5) |
| Re-anchored hotspots | 14 | section 5 point 5 |

Total new art images: 60 sprites (frames included in each), 3 faces, 8 acts, 7 props. Priority split: P1 scenes E01 to E11 (11 scenes), P2 E00 and E14, P3 E12 and E13. A minimum useful first drop (the four P1 scenes with the worst reads) is E09, E06, E11, E02.

## 5. Cross-cutting issues

**Engine needs.**
1. **Current-state ops** on each hotspot: `state.rest` and `state.current` blocks that carry `swap` (thing -> sprite), `piece on/off`, `anim` (mode per thing), `act` (per actor, with `prop`), plus `touch` (1 beat) and `gaze` (list of actors that look at the current option's anchor). One new `acting` phase pair (`rest`, `current`, `touch`) next to the existing `available`, `selected`, `committed`, `success`, `failure`. The default option's `current` block runs from beat 0.
2. **`swap`** (thing sprite swap) is the only genuinely new stage op; everything else exists (`piece_on/off`, anim, `StoryCrowd.direct`, `hide`). It is cheaper and clearer than doubling every prop as two pieces.
3. **Priority** inside the crowd: touch reaction > CUR/REST state > beat `cast` > ambient. Option actors must not have beat `cast` lines in beats 48 to 63 (those are removed here); non-option actors keep their story beats.
4. **Cast on laps**: story cast plays on lap 1; lap 2 plays only beats 48 to 63 (or the engine repeats nothing and the state rule carries the picture). State-driven rest/current visuals never depend on the lap.
5. **Anchors**: 14 exit hotspots are anchored on a waypoint at or past the camera (invisible). Re-anchor them to visible things (listed per scene); the door walk still uses `rail.exits`. `deeps.lake` must not anchor on a piece that is off until beat 46.
6. **Hit areas**: make the hit test cover the whole thing sprite or actor (props included); options 16 to 25 m away (E05) rely on `min_px` 72, so size those things 5 to 6 m.
7. **Edge beacons and rings**: with all options in view the orange discs on the screen edge and the selected ring are redundant; keep only a 1-beat ring flash on a touch and hide the beacons for in-view anchors (they are "things of light" and compete with the diegetic cues).
8. **Window camera glances**: `rail.glances` and `strolls` yaw the camera by +-12 to 35 degrees; stop them from beat 49 (or limit to +-6 degrees), else the options leave the 20-degree view.
9. **Bad rail**: on a missed block the camera sways to +-40 to 80 degrees; the options still read by silhouette at the edge, but keep the narrow-view check on the good rail and accept the beacon on the bad rail.

**Rail and placement changes (summary).**

| scene | window camera | trim / hold | moved things |
| --- | --- | --- | --- |
| E00 | `orchard_mid` | drop `orchard_near` | `ember_bowl` (1.1,5.1) |
| E01 | `ford_mid` | drop `ford_edge` | `bram_f` (-1.4,-28.6); new `ford_stones` (1.6,-30.4), `river_swell` (0,-29.2) |
| E02 | `inn_c` | drop `inn_mid`, `inn_near` | `door_back` (17.4,-17.8); `warden_i` (22.4,-21.0) |
| E03 | `hall_mid` | drop `hall_dais` | `table_map` (1.8,8.0); `warden_h` (0.6,7.4); place `porch_door` (-2.4,1.0) |
| E04 | `pass_far` | none | `cairn` (0,-21.5); `cave` (-5.0,-31.3); `ridge` (5.2,-30.6); `warden_p` (1.0,-18.6) |
| E05 | `halls_edge` | none | new `bridge_head` (0,0.4), `lake_swirl` (-3.6,-3.0) |
| E06 | `falls_in` | hold, drop `falls_mid`, `falls_lip_wp` | `boat`, `bram_fb` (-2.8,-50.8); `horn` (2.7,-50.0); new `jetty` (0.2,-53.0) |
| E07 | `marsh_fwd` | none | `ho_m` (1.6,13.2); `bram_m` (-1.2,14.4); lights centred (-3.0,8.0); new `causeway_post` (0,1.6) |
| E08 | `wall_c` | hold, drop `wall_mid`, `wall_gate_wp` | `crack` (4.6,-23.4); `ho_w` (3.4,-20.0) |
| E09 | new `stair_choice` (18.5,-33.0) | drop `stair_mid`, `stair_up` | `sentinel` (16.4,-47.0); new `stair_gap` (22.4,-45.0) |
| E10 | `plain_far` | none | `tower` (-6.4,-64.5); `ho_pl` (-1.0,-54.0); new `road_post0..2` |
| E11 | `throat_c` | hold, drop `throat_mid`, `throat_low` | new `keeper_arch` (3.4,-88.0), `stair_slab` (0,-94.6); `ho_t` (1.2,-91.0) |
| E12 | `spring_c` | none | new `pool_rim` (-1.6,-109.4) |
| E13 | `keep_mid` | none | new `altar_steps` (25.0,-108.0) |
| E14 | `camp_in` | hold, drop `camp_mid`, `camp_near` | `stake` (-23.4,-14.2); new `camp_gap` (-23.2,-9.8) |

**Flags shown without text.** `ember_warden_lost`: his grey cloak lies in the snow (E04), snagged on the bridge chain (E05), the horn becomes the black rider's horn and the Warden is gone (E06). `ember_alone`: Bram is gone and his straw hat floats at the causeway (E07), his water skin hangs unused on a dead tree (E10). `ember_no_vial`: the Lady's pedestal stays under its glass bell (E03) and the bells at E09 are loud and thrashing instead of frosted. `ember_vial`: frosted, muffled bells. `ember_sentinel_asleep`: the guard sleeps, staff down, on a revisit (E09). Persistent endings `keep:path_ember_quenched/kept` stay with the Warehouse portal (Stage 6).

**Shared pieces.** `piece_ember_flare` (E00, E10, E13), `lantern` and `hold_up` (E01, E06), `smug` (E11, E13, E14), `tender` (E00, E03), `turn_away` (E14 riders; also usable as Bram's REST in E01), the cloak pieces (three variants).

**Sheet budget.** New `act@face` combos per directed actor: Bram (`beckon@happy` and `plead@plea` with the lantern, `hold_up@happy`, `sit@plea` and `beckon@happy` with the oar, `stare@doubt`), the Hollow One (`tug@relief`, `crouch_beckon@relief`, `kneel@plea`, `block@anger`, `beckon@smug`, `beckon@relief`, `shush@shame`, `sulk` stare), the Warden (`rise`, `sit@resolve`, `hold_up@resolve` with the horn, `block@resolve`), the Lady (`offer@grief`, `offer@tender`), the sentinel (`listen`, `block`), the captain (`offer@smug`), the four villagers and the drinkers (`look`), riders (`salute@resolve`, `turn_away`, `recoil@fear`). Expect roughly +10 to 15 % on the `ash_land` and `orchard` sheets; check against `check_assets.py` and report before/after bytes as in `docs/FACE_POLISH.md`.

**Risk and proof.** Nothing here has been seen moving; the owner should judge from the `docs/shots/ember/route_<scene>.jpg` regeneration and the acting contact sheets (`bash tools/run/capture_path.sh ember --acting`) with five states per option (REST, CUR, TOUCH, S, F), and from a touch test: tap each option in each scene and confirm the picture changes within one beat (0.41 s) and that tapping the default again restores it.
