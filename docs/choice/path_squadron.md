# Choice briefs: the Mission Count (`squadron`), 14 scenes C01 to C14

Designer's brief for the visual choice pass (owner verdict: touch the world, every branch must be readable from objects and people, no floating text). Documents only. Data read: `content/paths/squadron/run.json`, `hotspots/{base,air,city,escape}.json`, `content/story/maps/{airfield,city,harbour}.json`, `docs/paths/squadron.md`, the route and acting shots in `docs/shots/squadron/` and `docs/shots/acting/`.

Assumed engine (another agent builds it): at any time exactly one option of the scene is CURRENT (starts as the default), a touch on any option's thing or person makes it current within one beat, the choice can change until the commit, the staging is visible from beat 0 of the first lap and stays readable across both laps.

## 0. Reading guide

**Notation.** `act/face>look` is one directed pose (`look` = `camera`, an actor id, a thing id or a waypoint). CUR = the option is current. ALT = it is not. TOUCH = the one-beat reaction when it becomes current (at 140 BPM a beat is 0.43 s: two to four frames). RELEASE = what the option that just lost the current does in the same beat. Pixel sizes: props are 128 x 128 textures (`px_scale` 0.5, billboard `size` in metres as the map says) unless noted, wide props 256 x 128, small props 64 x 64, a head is 17 x 13 px. Art goes in `tools/story/art/tex_squadron*.py` (brief `tools/paths/squadron_tex_brief.json`, builder `chapter_squadron.py`, run `python3 tools/story/build_assets.py airfield|city|harbour`), map edits in `tools/paths/squadron_{airfield,city,harbour}.py` (they write `content/story/maps/*.json`), cast and hotspot tables in `tools/paths/squadron_story.py` (`python3 tools/paths/make_squadron.py` writes the JSON). A thing's existing sprite `thing_<name>` is treated as the ALT frame unless a section says otherwise; new state frames are spelled out per scene. Until the engine has per-thing state frames, a state is a pair of map things carrying `piece` ids switched with `pieces: {on, off}` and cast lines `piece/op` (already validated in `HotspotContract`).

**Archetypes (the path's own vocabulary).**
* **Rival pullers (RP).** Two people each want you; the CUR one leans in and gestures, the ALT one sulks, turns away or busies himself. The owner's wizard pattern, played dark.
* **Mechanism state (MS).** A device shows its setting: ladder down or hauled up, pin in or out, signal arm raised or lowered, sail up or furled, latch up or down, crate lid open or nailed. Used where no person would gesture.
* **Paperwork and ink (PI).** This is a bureaucracy: the current thing has fresh red stamp ink, an open ledger, a pinned order; the other is blank, chained or dusty. Also carries the Clause tell (0.1).
* **Crowd faces the way (CF).** The idle crowd turns to the CUR option and drifts out of formation toward it.
* **Door states (DS).** Shut and padlocked against ajar with something in the gap.
* **Solemn (SO).** Gaze and posture only (C07: the crowd is pinned sad).

### 0.1 The Clause: how the joke reads without text

The Clause fires in C06 (success), C09 (success) and C11 (failure). One three-part visual contract, identical each time so the player learns it:
1. **The ghost mark.** A rust-red rubber-stamp impression (rectangle, rim of small triangular teeth, a spiral glyph, no letters) printed faintly (about 30 % alpha) on the thing that will really take effect: door B (C06), the count slate (C09), the count board (C11). New prop `thing_clause_mark`, 64 x 64, frames `ghost` and `wet`. It never sits on the thing the player touched.
2. **The smug hand.** The person who owns the stamp, chalk or brush (Clerk, Colonel's aide, Clerk) wears the new face `smug` and keeps the tool poised over the ghost-marked thing while the player's option is CUR.
3. **The overprint.** At the commit the poised tool lands on the ghost mark (it turns solid and wet) after the touched thing has resolved, and the camera turns to it. Nothing else in the path shows a ghost mark, so a mark means "that, not what you touched".

### 0.2 Two-lap rule used in every scene

Staging is a state, not a beat: a CUR or ALT pose holds the whole lap. Existing `cast` lines at fixed beats on the option actors ("cast to drop" per scene) must be removed or reduced to a non-pose layer (head turns, small idle), or they fight the state. Lap 2 adds insistence (section 4): the CUR person's cycle runs at half the beats, the ALT person droops one step further (`sulk` deepens, arms fall). One lap says "this one is happening", the second says "something is at stake".

## 1. Summary table

| scene | options (hotspot ids) | default | verdict today | archetype | effort | priority |
| --- | --- | --- | --- | --- | --- | --- |
| C01 Briefing Room | `base.cot`, `base.board` | `base.cot` | cot is 102 deg out of frame at the rail's end and reads as furniture; only the board is ringed | RP + CF (the airman at the bed) | M | P1 |
| C02 The Flight Line | `base.c02.ladder`, `base.c02.crates` | `base.c02.ladder` | ladder 76 deg off-axis at the window; crates a speck at 12 to 19 m | MS + RP | M | P1 |
| C03 The Hospital | `base.c03.hatch`, `base.c03.office_door`, `base.c03.clipboard` | `base.c03.hatch` | the office door is a bare waypoint with no prop; three targets spread 160 deg | DS + RP | L | P1 |
| C04 The Bombing Mission | `air.lever`, `air.emergency` | `air.lever` | dark nose; the box is behind the camera at the window (-75 to -155 deg); edge beacons only | MS + RP | M | P2 |
| C05 The Syndicate | `air.c05.truck`, `air.c05.ledger` | `air.c05.truck` | truck and ledger 4 to 9 m away, spread 104 deg at the window | MS + PI | M | P2 |
| C06 The Surgeon's Office (Clause) | `air.c06.door_a`, `air.c06.certificate` | `air.c06.door_a` | certificate 110 deg out of frame at g2; the Clause joke has no tell at all | PI + DS + Clause | L | P1 |
| C07 The Gunner's Last Flight | `city.jacket`, `city.medkit` | `city.jacket` | both props at the camera's knees (1.1 to 1.6 m) | SO | M | P2 |
| C08 The Old City | `city.c08.arch`, `city.c08.staff_car` | `city.c08.arch` | arch 14 to 20 m away; the MPs block whichever you touch | DS + RP | M | P2 |
| C09 The Colonel's Deal (Clause) | `city.c09.map`, `city.c09.medal` | `city.c09.map` | spread 103 deg at the window; aide and slate not part of the picture | PI + RP + Clause | L | P1 |
| C10 The Ruined City | `city.c10.hq`, `city.c10.train` | `city.c10.hq` | HQ door behind the camera (95 to 175 deg), train 15 to 19 m; spread up to 145 deg | MS + RP | M | P2 |
| C11 Endless Missions (Clause, on failure) | `escape.aircraft`, `escape.radio` | `escape.aircraft` | aircraft door behind the camera (134 deg at home); the count board is not tied to the choice | CF + PI + Clause | L | P1 |
| C12 Escape North | `escape.c12.searchlights`, `escape.c12.boat` | `escape.c12.searchlights` | boat reads as a dark hulk, the coast gap is a glitchy block | MS + RP | M | P1 |
| C13 The Neutral Coast (ending) | `escape.c13.shore`, `escape.c13.fisherman` | `escape.c13.shore` | one way out; the fisherman is a gratitude touch, not a route | ending | S | P3 |
| C14 Captured | `escape.c14.order`, `escape.c14.latch` | `escape.c14.order` | latch is ahead and fine; the order paper is 30 to 55 deg right and tiny | MS + PI + RP | M | P2 |

Coverage: 14 scenes, 29 hotspots (script check in section 5).

## 2. Scene briefs

### C01 The Briefing Room (`base`, map `airfield`, room `hut`)

**Choice.** Situation: the Colonel briefs the squadron at the board while one nervous airman would rather be in bed. Options: `base.cot` (thing `cot_empty`, exit, DEFAULT) success C03 / failure C03 (-5); `base.board` (thing `board`, exit, actor `col` directed) success C02 (+6, flag `sq_briefed`) / failure C03 (-5). Today: `docs/shots/squadron/route_c01.jpg` shows a ring on the board, the Colonel pointing at the left edge, no cot in frame (rail place g2 sees it at -102 deg, g1 at -57 deg), a purple edge beacon at the top. Blunt: a player sees one thing to press and cannot tell there is another way.

**Archetype.** Rival pullers + crowd faces the way, with the airman `a04` (already standing at the cot, home (-6.6,1.5)) as the hinge: he is either tucked up at the cot's edge or at attention at the board.

**Camera.** New rail place `c01_choice` at (-3.6,5.2) yaw 55 (this is `c01_g1` re-aimed from yaw 80); the rail ends there for both options' window and both laps. From it the cot is 5.2 m away and the board 8.1 m, 54 deg apart (both inside the 82 deg frame). `c01_g2` (-6.0,2.8) must stop facing the wall: set it to `c01_choice`.

**Option A: `base.cot` (default).**
* Affordance: the cot is no longer furniture. CUR frame `thing_cot_turned` (new, 128 x 128, size 1.3 m): blanket turned back in a triangle, dented pillow, slippers, a hot-water bottle. ALT frame is the existing `thing_cot_empty` (hospital-cornered, flat, squared pillow).
* CUR: `a04` `pat/hopeful>camera` (new act and face: pats the mattress twice, head tilted); `col` `shake_head/doubt>cot` then holds `block/doubt>cot` (arms folded, the pointer stick lowered); airmen `a01`, `a02`, `a03` `rock/bored>cot` (lounging toward the cot); `a06` `nod/hopeful>a04`.
* ALT: `a04` `salute/resolve>board` held (at attention like the others), cot in its flat state.
* TOUCH (within one beat): `a04` snaps from `salute` to `pat` in two frames, the pillow plumps (2-frame wobble of `thing_cot_turned`), `col`'s pointer drops.
* RELEASE (board loses current): the new order sheet flaps once and the pin drops it a hand lower (see board ALT).
* Commit, success and failure (both lead to C03): `a04` tucks in (`sleep/relief>camera`), the camera walks to `c01_x_up` (the cot doorway); `col` `stare/neutral>camera`. No separate failure picture: it is the same door.

**Option B: `base.board`.**
* Affordance: CUR frame `thing_board_orders` (new, 128 x 128, size 2.6 m): the old painted tally plus a fresh order sheet pinned with four pins, a red ring stamp on it, the pointer stick leaning on the frame. ALT = existing `thing_board` (tally only, a bare pin and a curled corner of an old sheet).
* CUR: `col` `point/resolve>board` (the existing available pose, face `smug` instead of `resolve` for the dark joke); `a01`, `a02`, `a03`, `a04`, `a05` `salute/resolve>board` held; `a06` `shake_head/fear>board` (the one who does not want it, kept).
* ALT: `col` `block/doubt>cot`, airmen `rock/bored>cot`.
* TOUCH: the order sheet slaps flat (2 frames), `col` `nod/smug>camera` (existing `selected` pose), airmen snap to attention on consecutive half-beats left to right (as the existing cast does).
* Commit success (C02): `col` `salute/resolve>camera` 8 beats (existing), everyone salutes, the camera walks to `c01_x_right` (the hut door `door_open_light`, bright). Failure (C03): `col` `shake_head/doubt>camera` then `stare/neutral` (existing), `a04` `pat` again, the order sheet falls off one pin, the camera goes to the cot doorway.

**Cast to drop:** `a04` salute at 48, `col` point at 0 (replaced by state), `a06` shake_head at 32 stays (it is in character for both states).

**Create.**
| item | spec | effort |
| --- | --- | --- |
| `thing_cot_turned` | cot with turned-back blanket, dented pillow, slippers, bottle; frames `settled`, `plump` (2); 128 x 128; map airfield view hut | S |
| `thing_board_orders` | board with fresh order sheet, red ring stamp (no letters), pointer stick; frames `pinned`, `slap` (2); 128 x 128 | S |
| act `pat` | hand pats a surface twice, torso leans toward it; 2 beats, 6 frames; front and side | S |
| face `hopeful` | brows raised and softened, eyes lifted, small closed smile | S |
| face `smug` | lids half down, one mouth corner up, chin up one pixel | S |
| map: `c01_choice` waypoint, `c01_g2` replaced | waypoint edit in `squadron_airfield.py` | S |

### C02 The Flight Line (`base.c02`, map `airfield`, room `line`)

**Choice.** Situation: the boy Gunner offers a ride up to the bomber, the Quartermaster offers contraband eggs from his crates. Options: `base.c02.ladder` (thing `ladder`, actor `gun`, DEFAULT) success C04 (air) / failure C04 (-5); `base.c02.crates` (thing `crates`, actor `qm`) success C05 (+6, flags `sq_egg`, `keep:path_squadron_met_quartermaster`) / failure C04 (-5). Today: `route_c02.jpg` shows the windsock and a Quartermaster at the right edge, a pad lane over the picture; the ladder is 76 deg left of the camera at g2 and out of frame, the crates are 12.6 to 19 m away.

**Archetype.** Mechanism state (ladder lowered or hauled up, crate lid open or nailed) driving two rival pullers.

**Camera and placement.** New place `c02_choice` (4.8,5.6) yaw -115. Move `crates` from (20.5,3.8) to (16.5,5.5), `qm` home from (19.2,4.6) to (17.8,6.4). Then ladder 9.7 m, crates 11.7 m, 51 deg apart, both in frame. Replace `c02_g2` with `c02_choice`.

**Option A: `base.c02.ladder` (default).**
* Affordance: CUR frame `thing_ladder` is the existing sprite read as lowered (check it reaches the ground; if not, redraw): rope ladder paid out to the dust, chocks in. ALT frame `thing_ladder_up` (new): ladder hauled up and lashed under the hatch, a bucket hung on the lowest rung.
* CUR: `gun` `beckon/cheer>camera` (new big two-arm beckon is the same `beckon` at double amplitude) leaning out of the hatch at the top of the ladder; the bomber's propeller blades spin (new 3-frame piece `thing_prop_spin`, 64 x 64, `anim bob`); `mech` `stare/doubt>gun`.
* ALT: `gun` `sad/sulk>camera` sitting on the hatch rim, chin on knees; propeller stopped.
* TOUCH: ladder unrolls (2 frames), `gun` whoops (`cheer/cheer`) for one beat then holds `beckon`.
* Commit success: `gun` `cheer/cheer>camera` 8 beats (existing), camera climbs (existing). Failure: `gun` `shake_head/doubt>camera` (existing), ladder drops anyway and he hauls you up regardless (both go to C04).

**Option B: `base.c02.crates`.**
* Affordance: CUR frame `thing_crate_stack_open` (new, size 2.1 m): top crate lid propped up on a stick, straw spilling, a nest of eggs and a tin visible; ALT = existing `thing_crate_stack` (lids nailed, a crowbar leaning, nothing visible). A twin `crates_b` stays nailed always.
* CUR: `qm` `offer/smug>camera` holding the egg (his prop), then `laugh/laugh>camera` every other beat.
* ALT: `qm` `sit/bored>camera` on the nailed lid, hat over eyes (`sleep` if `bored` is not baked yet).
* TOUCH: `qm` springs up (`laugh`), lid pops (2 frames); the Gunner's `beckon` drops to a `sulk`.
* Commit success (C05): `qm` `offer/happy>camera` 8 beats (existing); camera walks to the store door. Failure (C04, -5): `qm` `laugh/laugh>camera` then `stare/doubt` (existing), the egg in his hand is bad (a green yolk pixel tint on the `egg` prop), the ladder drops.

**Cast to drop:** `gun` wave at 0, `qm` offer at 16 and laugh at 48; keep `mech` stare at 32.

**Create.**
| item | spec | effort |
| --- | --- | --- |
| `thing_ladder_up` | ladder hauled up and lashed, bucket on rung; 128 x 128 | S |
| `thing_crate_stack_open` | open top crate, straw, eggs; frames `open`, `rustle` (2); 128 x 128 | S |
| `thing_prop_spin` | propeller disc, 3 frames, 64 x 64, placed on `bomber_nose` | S |
| face `sulk` | brows flat and down at the ends, eyes slid aside, mouth turned down, lower lip out | S |
| face `bored` | lids half down, flat mouth, no brow motion | S |
| map: `c02_choice`, move `crates` and `qm` | `squadron_airfield.py` | S |

### C03 The Hospital (`base.c03`, map `airfield`, room `tent`)

**Choice.** Situation: a field hospital where the Surgeon will find you mad and therefore fit to fly. Options: `base.c03.hatch` (thing `kitchen_hatch`, DEFAULT) success C05 / failure C05 (-5); `base.c03.office_door` (anchor waypoint `c03_x_right`, no prop) success C06 / failure C06 (-5); `base.c03.clipboard` (character `surg`, once) success C06 (+6, flags `sq_examined`, `keep:path_squadron_met_surgeon`) / failure C05 (-6). Two routes: C05 (hatch) and C06 (door and Surgeon). Today: `route_c03.jpg` shows a wall of drip bag, patients and a vertical purple beam over the scene; the office door is only a waypoint (no picture), the hatch is 46 to 84 deg left and the Surgeon is 4 m away and tiny.

**Archetype.** Door states at the far wall, the Surgeon as the pushy third. Where two options share a route (door and Surgeon both C06), the room shows one door state, and the Surgeon only adds his own pose.

**Camera and placement.** Rebuild the far wall as a stage: move `kitchen_hatch` from (9.8,-6.4) to the north wall (8.4,-9.7), add a prop thing `tent_door_office` at (1.6,-9.7) (re-anchor `base.c03.office_door` to it and move `c03_x_right` to its foot), keep `surg` at (5.6,-7.6). New place `c03_choice` (5.0,-0.6) yaw 0: door 20 deg left, Surgeon 5 deg right, hatch 20 deg right, all 9 m away. Move `c03_x_up` to the hatch front. Side cots stay and frame the view.

**Option A: `base.c03.hatch` (default, route C05).**
* Affordance: CUR frame `thing_kitchen_hatch_open` (new, size 1.8 m, transparent window): shutter rolled up, a counter, steam, and the new actor `cook` (airman `b` wardrobe plus apron and knit cap) leaning out. ALT = existing sprite redrawn shut (shutter down, bar across, no flicker).
* CUR: `cook` `offer/smug>camera` holding a mug out; the nearest patient `p01` (home (8.2,-4.6)) `laugh/laugh>hatch`; the Surgeon `write/bored>patients` (back to you).
* ALT: shutter down, `cook` absent (hidden), `p01` `sit/sad>camera`.
* TOUCH: shutter rattles up (2 frames), `cook` pops into the window; the door (if it was CUR) swings shut.
* Commit success or failure (C05): `cook` `cheer/cheer>camera`; the camera walks to the hatch (`c03_x_up`). On clipboard failure the hatch bangs open and `cook` grabs you: `surg` `shake_head/doubt` then `point/resolve>kitchen_hatch` (existing).

**Option B: `base.c03.office_door` (route C06).**
* Affordance: new `thing_door_office_ajar` (128 x 128, size 2.2 m; shared with C06): door open a hand's width, a stack of forms on a table inside, an arm in a clerk's sleeve holding a rubber stamp out of the gap. ALT = existing `thing_door_office` (shut, key in the lock, a stamp hung on a nail).
* CUR: door ajar; the Clerk's stamp hand taps the frame on every half-beat (3-frame piece).
* TOUCH: door swings ajar (2 frames), the stamp taps twice.
* Commit success or failure (C06): the door opens wide (`thing_door_office_open`), camera goes to `c03_x_right`.

**Option C: `base.c03.clipboard` (character `surg`, route C06 on success, C05 on failure, once).**
* Affordance: the Surgeon himself. CUR: `surg` `write/doubt>camera` becomes `hold_up/bored>camera` (new act: clipboard raised to you, pen over the tick box) and then turns his body toward the office door and does `sweep_arm/smug>office_door` (new act: arm sweeps toward the door); the door goes ajar (same state as option B).
* ALT (when the hatch or door is current): `surg` `turn_away/bored>patients` (profile, back half to you, writing).
* TOUCH: he turns to face you and the pen taps the clipboard (2 frames), within a beat.
* Commit success: `surg` `nod/relief>camera` (existing); failure: `shake_head/doubt` then `point/resolve>kitchen_hatch` (existing) and the hatch opens (as option A).

**Cast to drop:** `surg` write at 0 and 32, `p01` laugh at 16 and 48 (replaced by state; keep `p02` to `p04` lying).

**Create.**
| item | spec | effort |
| --- | --- | --- |
| `thing_kitchen_hatch_open` | hatch open, counter, steam, window cut-out for an actor; frames `open`, `rattle` (2); 128 x 128 | M |
| `thing_door_office_ajar`, `thing_door_office_open` | office door ajar with a clerk's hand and stamp; wide open; also used in C06; 128 x 128 each, ajar has 3 frames for the tapping stamp | M |
| thing `tent_door_office` | map thing at (1.6,-9.7) using `thing_door_office` states | S |
| actor `cook` (wardrobe) | `airman` b + `apron` accessory + `knit` hat, home (8.4,-10.3) behind the hatch, bakes `offer`, `cheer`, `shrug`, faces `smug`, `neutral` | M |
| acts `hold_up`, `sweep_arm`, `turn_away` | hold_up: both hands raise a clipboard, 2 beats 4 frames; sweep_arm: right arm sweeps to a side with a half bow, 2 beats 6 frames; turn_away: profile, head turned further, shoulders dropped, 8 beats 2 frames | M |
| map edits | move `kitchen_hatch`, add `tent_door_office`, `c03_choice`, re-anchor `base.c03.office_door` | S |

### C04 The Bombing Mission (`air`, map `airfield`, room `bomber`, night)

**Choice.** Situation: over the target in the glazed nose; drop, or abort. Options: `air.lever` (thing `release_lever`, actor `pilot`, DEFAULT) success C07 (+6, flag `sq_released`) / failure C03 (-6) through cinematic `squadron.turn_back`; `air.emergency` (thing `emergency_box`, actor `crew1`) success C03 (+3) / failure C07 (-5, flag `sq_released`). Today: `route_c04.jpg` is flak flashes and a dark nose with a purple lane over the left; at the window the camera at g2 is 1.3 m from the lever and the box is behind it (-155 deg); the box's only cue is a pulse.

**Archetype.** Mechanism state (pin in or out, glass whole or smashed) between two crew who each want you, played in fear, not cheer.

**Camera.** New place `c04_choice` (13.2,16.4) yaw 129 (the bombardier's seat, down-left): lever 3.5 m, box 3.0 m, 55 deg apart. Replace `c04_g2`. Keep the nose glass and flak as backdrop.

**Option A: `air.lever` (default).**
* Affordance: CUR frame `thing_release_lever_armed` (new): the split pin hangs out on a string, the red guard flap is up, the handle gleams. ALT = existing `thing_release_lever` shown pinned: add a split pin and a wire seal, guard flap down.
* CUR: `pilot` `point/resolve>release_lever` (existing committed pose) holding it as the pose; `gun_b` (home (10.8,16.6)) `point/resolve>nose_glass`; `crew2` `stare/fear>nose_glass`.
* ALT: `pilot` `stare/doubt>camera`, hands off.
* TOUCH: the pin is plucked and dangles (2 frames), `pilot` turns his head to you and nods once (existing `selected` pose).
* Commit success: `pilot` `stare/resolve>nose_glass` (existing), the lever rocks forward, the bay indicator needle swings (panel frame), cast lines at 61 (relief then grief) stay. Failure (turn back): the pin snaps back in place, the lever jams, `pilot` `shake_head/doubt` (existing), the cinematic stagger.

**Option B: `air.emergency`.**
* Affordance: CUR frame `thing_emergency_box_open` (new, 0.9 m): glass front smashed, hammer on a chain swinging, the red handle exposed. ALT = the existing `thing_emergency_box` with its pulse animation removed (set `anim none`: light pulses are not an affordance) and a wax seal.
* CUR: `crew1` `tug/plea>camera` (new act: hand reaches to your sleeve and pulls toward the box, body leaning that way); `crew2` `plead/plea>camera`.
* ALT: `crew1` `cover_face/fear>nose_glass`.
* TOUCH: glass shatters (2 frames), `crew1` lunges to `tug`, `pilot` face goes `doubt`.
* Commit success (C03): `crew1` `cover_face/relief>camera` 8 beats (existing), yoke tips, the horizon tilts (a rail roll of 8 deg). Failure (C07, bombs fall anyway): `crew1` `recoil/fear>camera` (existing), the lever rocks forward by itself.

**Cast to drop:** `pilot` stare at 0, `crew1` recoil at 16, `crew2` recoil at 32 (replaced by state); keep the 61-beat reactions.

**Create.**
| item | spec | effort |
| --- | --- | --- |
| `thing_release_lever_armed` | lever with pin out, guard up; frames `armed`, `rock` (2); 128 x 128 | S |
| `thing_release_lever` (restyle) | add pin and seal (pinned look) | S |
| `thing_emergency_box_open`, `thing_emergency_box` (restyle) | smashed glass with swinging hammer (2 frames); sealed, no pulse | S |
| act `tug` | reaches an arm toward the camera and tugs back twice, torso leaning away; 2 beats 8 frames; front and side | M |
| map: `c04_choice` | `squadron_airfield.py` | S |

### C05 The Syndicate (`air.c05`, map `airfield`, room `store`)

**Choice.** Situation: the Quartermaster's black-market store; the truck is about to leave. Options: `air.c05.truck` (thing `truck`, actor `drv`, DEFAULT) success C08 / failure C06 (-4); `air.c05.ledger` (thing `ledger`, actor `qm_s`) success C06 (+6, flag `sq_ledger`) / failure C08 (-6). Today: `route_c05.jpg` is dark with edge beacons; truck 4 to 10 m (bob only), ledger 21 to 51 deg off.

**Archetype.** Mechanism state for the truck, paperwork and ink for the ledger.

**Camera.** New place `c05_choice` (30.0,4.4) yaw -104 (replace `c05_g2`): truck 8.1 m, ledger 5.1 m, 55 deg apart. Keep `sign_ledgerless` on the shelves as diegetic writing.

**Option A: `air.c05.truck` (default).**
* Affordance: CUR frame `thing_truck_ready` (new, 256 x 128, size 2.8 m): tailgate down, tarp rolled back, a crate on the bed, exhaust puffs (3 frames of 32 px), brake lamps. ALT = existing `thing_truck` with tarp lashed, chocks under the wheels, no exhaust (set `anim none`).
* CUR: `drv` `beckon/smug>camera` hand out of the cab window; clerks `sc1`, `sc2` `nod/happy>truck`.
* ALT: `drv` `sleep/bored>camera` slumped on the wheel.
* TOUCH: engine coughs (exhaust frames start), `drv` snaps upright (`beckon`), `qm_s` shrugs.
* Commit success (C08): `drv` `nod/happy>camera`; the camera boards, the truck pulls out. Failure (C06, -4): `drv` `shake_head/doubt` (existing) and the truck leaves without you (slides off along x, 3 beats), `qm_s` `shrug/smug`.

**Option B: `air.c05.ledger`.**
* Affordance: CUR frame `thing_ledger_open` (new, 1.6 m): open on the counter, a pen on a chain, columns of painted squares, a coin tray with a few coins. ALT = existing `thing_ledger` closed, chained and padlocked.
* CUR: `qm_s` `offer/smug>camera` (pen held out toward you); `sc1`, `sc2` `nod/happy>camera` and lean in; `po1`, `po2` (home (30.0,4.2) and (31.4,8.0)) `stare/bored>truck`.
* ALT: `qm_s` `write/bored>ledger_back` (his own book, back half turned); `sc1`, `sc2` `turn_away/bored`.
* TOUCH: padlock clinks open and the ledger flips open (3 frames), `qm_s` spins to you, the clerks swing round on consecutive half-beats.
* Commit success (C06): `qm_s` `offer/happy` then `laugh/laugh` (existing); failure (C08): `qm_s` `block/anger` then `stamp/anger` (existing), the ledger slams shut.

**Cast to drop:** `qm_s` write at 0 and offer at 32, `sc1` and `sc2` nods at 16, 17, 48, 49.

**Create.**
| item | spec | effort |
| --- | --- | --- |
| `thing_truck_ready` | 256 x 128, tailgate down, tarp back, exhaust 3 frames; ALT frame restyle of `thing_truck` (tarp lashed, chocks) | M |
| `thing_ledger_open` | open ledger with chain and coin tray; frames `closed_padlocked`, `flip` (2), `open`; 128 x 128 | S |
| act `shrug` | palms out, shoulders up, head tilt; 2 beats 4 frames | S |
| map: `c05_choice` | `squadron_airfield.py` | S |

### C06 The Surgeon's Office (`air.c06`, map `airfield`, room `office`) THE CLAUSE (success)

**Choice.** Situation: the Surgeon pleads with the Clerk to certify him unfit to fly; the Clerk's rule says anyone sane enough to ask is sane enough to fly. Options: `air.c06.door_a` (thing `door_a`, DEFAULT) success C02 / failure C02 (-5); `air.c06.certificate` (thing `certificate`, actor `clerk`) success `squadron.double_stamp` then C09 (+5, flags `sq_stamped`, `keep:path_squadron_clause`) / failure C02 (-5). The success routes to C09, not to what a touch on a discharge certificate promises (freedom). Today: `route_c06.jpg` is the ceiling and a Surgeon in a corner; the certificate is 52 to 128 deg off-axis (not in frame at g2), door A 10 to 16 deg, door B has no role anywhere; nothing foreshadows the double stamp.

**Archetype.** Paperwork and ink + door states + the Clause tell (0.1). The Clerk is the whole show.

**Camera and placement.** Re-hang `certificate` between the two doors on the west wall at (-11.7,-5.05), size 1.2 m, y 2.0 (door A (-11.7,-3.2) and door B (-11.7,-6.9) stay; the desk `desk_clerk` (-8.4,-5.0) sits below it, `clerk` (-9.2,-5.0) behind the desk, `surg_o` (-6.8,-3.6) in front). New place `c06_choice` (-4.2,-5.0) yaw 90: door A 14 deg left, certificate dead centre, door B 14 deg right, all about 7.5 m. Replace `c06_g2`. The Clerk is then the centre of the picture, framed by his two doors.

**Desk props.** `stamp_big` (-8.0,-4.1) is the GROUNDED stamp: its face is a bomber with a bar across it, the rubber cracked, a cobweb from handle to pad (new frame `thing_stamp_big` restyled dry; 64 x 64). New `stamp_fly` (-8.6,-4.4), `thing_stamp_fly` (64 x 64): worn handle, glistening red pad, face a bomber with an arrow ahead. No words anywhere. The Clerk's own held prop (`stamp`) is the fly stamp.

**Option A: `air.c06.door_a` (default).**
* Affordance: `thing_door_office_ajar` (shared, see C03) for door A: ajar onto the glare of the flight line with a rolled flight-order tube sticking out of the gap. ALT = existing `thing_door_office` shut.
* CUR: `clerk` `stamp/neutral>orders` (new small prop `thing_orders_stack` on the desk, 64 x 64, 3 frames of stamping), a steady honest rhythm; `surg_o` `sad/grief>camera` (slumped); certificate crooked and dusty (existing `thing_certificate`).
* TOUCH: door swings ajar (2 frames), Clerk's stamp rises and thumps once; the Surgeon's head drops.
* RELEASE (certificate loses): the certificate sags to a lean.
* Commit success or failure (both C02): door opens wide, `clerk` `nod/resolve>camera` (existing failure pose), camera goes to `c06_x_up`. No trick: door A is the honest door.

**Option B: `air.c06.certificate` (the Clause).**
* Affordance: CUR frame `thing_certificate_ready` (new, 128 x 128): straight, ribbon tails fluttering, a gilt border, an empty circle waiting for a seal. ALT = existing `thing_certificate` (askew, dusty).
* CUR: `clerk` `hold_up/smug>camera` raising the certificate-sized paper to you with the fly stamp in the other hand held over **the ghost-marked door B** (not over the certificate): stamp poised toward the door. `surg_o` `plead/hopeful>clerk` (hands clasped, leaning in, new face `hopeful`). The ghost mark `thing_clause_mark` (ghost frame) on `door_b` (new map thing `door_b_mark` at (-11.65,-6.9), y 1.3).
* ALT: `clerk` `turn_away/bored>orders`, certificate askew, ghost mark still faint on door B (it is always there from beat 0: the player may never read it, but the joke is fair).
* TOUCH: the certificate straightens (2 frames), `surg_o` hops from `sad` to `plead` in one beat, `clerk` swings to face you.
* Commit success (the joke, cinematic `squadron.double_stamp`, existing walk to `c06_desk`): beat 0.5 `clerk` `stamp/laugh>camera` lowering the GROUNDED stamp on the certificate (`thing_certificate_stamped`, new: an ink circle with the barred bomber, wet); beat 2 `surg_o` brief `cheer/cheer>camera`; beat 3 the Clerk's other hand brings the fly stamp down on the certificate over the first mark (an arrow overprints the bar: `thing_certificate_stamped` frame 2) and a second thump lands on door B, where the ghost mark turns solid and wet (`thing_clause_mark` frame `wet`), door B swings open (`thing_door_office_open`) on a sepia view; the camera turns to door B (existing look_at `stamp_big` replaced by `door_b`); `clerk` `laugh/laugh>camera` 6 beats, `surg_o` `cover_face/shame>camera` 10 beats. Failure (C02, -5): the stamp never leaves its pad, `clerk` `nod/resolve>camera` (existing), the frame drops off the wall (`thing_certificate_fallen`, 128 x 128: face down on the floor, cracked glass, 2 frames) and door A opens.

**Cast to drop:** `surg_o` plead at 0 and 32 and `clerk` write/stare at 0, 16, 48 (all replaced by state).

**Create.**
| item | spec | effort |
| --- | --- | --- |
| `thing_certificate_ready`, `_stamped` (2 frames), `_fallen` (2 frames) | 128 x 128, size 1.2 m, wall-hung; stamped has the barred-bomber ring then an arrow overprint; map airfield view office | M |
| `thing_stamp_big` (restyle dry), `thing_stamp_fly` | 64 x 64 desk props, state frames `rest`, `raised` | S |
| `thing_orders_stack` | stack of forms with a stamping hand rhythm, 3 frames, 64 x 64 | S |
| `thing_clause_mark` | 64 x 64, `ghost` (30 % alpha) and `wet` (full, glistening) frames; rust red; spiral glyph; reused in C09 and C11 | S |
| `thing_door_office_open` | door B wide open on sepia street light; 128 x 128 | S |
| map: move `certificate`, add `stamp_fly`, `door_b_mark`, `c06_choice`; move `door_b`'s waypoint `c06_desk` look | `squadron_airfield.py` | S |
| acts `hold_up`, `turn_away` (see C03); faces `smug`, `hopeful` | shared | (counted once) |
| cinematic data: `look_at` `door_b` in `squadron.double_stamp`, cast lines for the second stamp at beat 3 (piece ops `door_b_mark` wet, `thing_door_office_open` on) | `squadron_story.py` | S |

### C07 The Gunner's Last Flight (`city`, map `city`, room `bomber_r`, red light)

**Choice.** Situation: the boy Gunner is dying in the red-lit cabin; take his jacket and fly on, or try the kit. Options: `city.jacket` (thing `jacket`, actor `pilot_c`, DEFAULT) success C10 / failure C10 (-5); `city.medkit` (thing `medkit`, actor `crew1c`) success C03 (+3, flag `sq_kit`) / failure C10 (-6). The crowd mood is pinned `sad`: no cheering anywhere. Today: `route_c07.jpg` (g2 is 1.1 m and 1.6 m from the two props: nose-high in the bomber's floor); both props sit at the camera's knees.

**Archetype.** Solemn: objects in hands and where people look, no gestures that read as eager.

**Camera.** New place `c07_choice` (10.8,-2.8) yaw -64: jacket 3.5 m, medkit 2.7 m, 43 deg apart, floor level props at 0.35 to 0.8 m height seen from eye height with the Gunner between them. Replace `c07_g2`.

**Option A: `city.jacket` (default).**
* Affordance: CUR: `pilot_c` holds the jacket out: new people prop `jacket` (bloodied flying jacket folded over the forearm), pose `offer/resolve>camera`; the floor `jacket` thing is switched off (piece). ALT = existing `thing_jacket_blood` folded under the Gunner's head, `pilot_c` back at his post `stare/resolve>nose_glass_r` (existing).
* CUR also: `gun_c` `lie/resolve>pilot_c` (eyes open, a small nod at the pilot); `crew2c` `cover_face/grief>camera` (existing).
* TOUCH: `pilot_c` turns from the glass to you in one beat and lifts the jacket (2 frames); `crew1c` lowers her hands from the kit.
* Commit success or failure (both C10): success `pilot_c` `stare/resolve>nose_glass_r` (existing, jacket gone); failure `pilot_c` `stare/grief>gun_c` (existing).

**Option B: `city.medkit`.**
* Affordance: CUR `thing_medkit_open` (new, 0.8 m): lid up showing the plain grey cross on its inside, a roll of bandage, a dressing half unrolled and reaching toward the Gunner. ALT = existing `thing_medkit` shut, strap fastened.
* CUR: `crew1c` `kneel/plea>gun_c` (kneeling at his side, holding a dressing: act `kneel`, prop dressing is part of the sprite); `gun_c` `lie/plea>medkit` (eyes on the kit, new look); `pilot_c` stays at the glass.
* ALT: `crew1c` `cover_face/grief>gun_c` seated (existing cast pose).
* TOUCH: the lid pops (2 frames), `crew1c` drops to a knee within a beat.
* Commit success (C03): `crew1c` `cover_face/grief>camera` 8 beats (existing), a dressing laid over the Gunner's chest (no cheer); failure (C10): `crew1c` `shake_head/grief>camera` (existing), the kit's lid closes.

**Cast to drop:** `crew1c` cover_face at 16, `pilot_c` stare at 0 (replaced by state); keep `gun_c` lie, its face switches `fear` to `neutral` at 48 as today but only when the jacket is CUR (when medkit is CUR keep `plea` to the end).

**Create.**
| item | spec | effort |
| --- | --- | --- |
| `thing_medkit_open` | open kit with grey cross on lid, bandage; 128 x 128 (size 0.8 m) | S |
| people prop `jacket` | folded jacket on forearm for `pilot_c` (and a dropped-jacket frame); in `people.py` props list | S |
| act `kneel` with prop dressing | exists; add a bandage in the hands for `crew1c` | S |
| look target `gun_c` / `medkit` | no new asset; data only | S |
| map: `c07_choice` | `squadron_city.py` | S |

### C08 The Old City (`city.c08`, map `city`, room `street`)

**Choice.** Situation: a curfew street, military police at the broken arch, a staff car at the kerb, a singer and a child. Options: `city.c08.arch` (thing `arch`, actor `mp1`, DEFAULT) success C10 / failure C10 (-5); `city.c08.staff_car` (thing `staff_car`, actor `mp2`) success C09 (+6, flag `sq_car`) / failure C10 (-5). Today: `route_c08.jpg` has the street in sepia; the arch is 14 to 20 m away (a small ruin), the car close and unreadable; the MPs block whichever you touch.

**Archetype.** Door states on the arch (barrier pole), rival pullers on the two MPs (one opens a way, one holds it).

**Camera and placement.** New place `c08_choice` (8.4,4.0) yaw -67: car 2.8 m (left), arch 14 m (right), 46 deg apart. Bring the arch group to where it reads: `mp1` to (18.6,2.8), `mp2` to (18.6,5.4), `kid_c` to (20.2,4.2) in front of the arch (the arch stays at (22.4,4.0)); `kid_c` scale 1.15. New thing `arch_pole` (barrier pole across the arch, 256 x 128 wide, at (22.0,4.0) y 1.0).

**Option A: `city.c08.arch` (default).**
* Affordance: CUR `thing_barrier_pole_up`: the red-white pole raised on its counterweight; ALT `thing_barrier_pole_down` across the arch with a lantern hung on it.
* CUR: `mp1` `stare/neutral>camera` at ease, arms at sides; `kid_c` `beckon/hopeful>camera` (big wave from the arch); `singer` `offer/happy>camera` (the hat held out toward the arch).
* ALT: pole down, `mp1` `block/anger>camera` (existing available pose), `kid_c` `sad/sulk>camera`.
* TOUCH: the pole swings up (2 frames), `mp1` drops his arms, `kid_c` jumps.
* Commit success (C10): `mp1` `nod/neutral>camera` 8 beats (existing); failure (C10, -5): `mp1` `stamp/anger>camera` then `point/resolve>street_lamp` (existing), the pole snaps down then up as the MP waves you on anyway.

**Option B: `city.c08.staff_car`.**
* Affordance: CUR `thing_staff_car_open` (new, 1.9 m): rear door swung wide, a plain dark-blue pennant standing on the wing, exhaust puff (2 frames), a white seat showing. ALT = existing `thing_staff_car` shut, dust sheet corner.
* CUR: `mp2` `sweep_arm/smug>staff_car` holding the door (new act `sweep_arm`), then `salute/resolve>camera`; `singer` `shrug/bored>camera`.
* ALT: `mp2` `block/anger>camera` (existing selected pose) at the arch side with `mp1`.
* TOUCH: door swings open (2 frames), `mp2` shifts from `block` to `sweep_arm`.
* Commit success (C09): `mp2` `salute/resolve>camera` 8 beats (existing); failure (C10, -5): `mp2` `block/anger>camera` (existing), door slams.

**Cast to drop:** `singer` laugh at 0 and offer at 16, `mp1` block at 0, `mp2` block at 32, `kid_c` beckon at 16 and 48.

**Create.**
| item | spec | effort |
| --- | --- | --- |
| `thing_barrier_pole_up` / `_down` | 256 x 128, striped pole, counterweight, lantern; map city view street | S |
| `thing_staff_car_open` | staff car with the rear door wide, pennant (plain colour, no emblem), exhaust 2 frames; restyle `thing_staff_car` windscreen at the same time (listed weak art); 128 x 128 | M |
| act `sweep_arm` | as C03 | (shared) |
| map: `c08_choice`, move MPs and kid, add `arch_pole` | `squadron_city.py` | S |

### C09 The Colonel's Deal (`city.c09`, map `city`, room `office_c`) THE CLAUSE (success)

**Choice.** Situation: the Colonel will give you a medal; the other way is the torn escape map his aide guards. Options: `city.c09.map` (thing `escape_map`, actor `aide_c`, DEFAULT) success C12 (+6, flag `sq_map`) / failure C12 (-5); `city.c09.medal` (thing `medal`, actor `col_c`) success `squadron.medal_pinned` then C11 (+5, flag `keep:path_squadron_met_colonel`) / failure C12 (-5, flag `sq_map`). Success on the medal routes to C11 (the count goes up anyway), not to the discharge a medal implies. Today: `route_c09.jpg` is good: the Colonel offering the medal case, a globe, the slate "24" in the background; but the map is 22 to 83 deg off-axis and at the window g2 the spread is 103 deg; there is no tell about the count.

**Archetype.** Paperwork and ink (the slate and the chalk) + rival pullers (Colonel against aide) + the Clause tell.

**Camera and placement.** New place `c09_choice` (8.0,10.0) yaw 165 (replace `c09_g2`): medal 2.6 m, map 7 m, 41 deg apart. Move `count_slate` from (8.8,15.6) to (6.2,15.7) (it was behind the medal case in the sight line), `aide_c` home from (4.3,13.0) to (7.6,15.0) beside it, chalk in hand. `col_c` stays at (6.6,13.9).

**Option A: `city.c09.map` (default).**
* Affordance: CUR frame `thing_map_wall_threaded` (new, 2.4 m): the torn map pinned flat, a red thread from the island pin across the sea to a drawn coast with a tiny boat; ALT = the existing `thing_map_wall` read as curled: redraw with the top-right pin out and the corner curling.
* CUR: `aide_c` `point/hopeful>escape_map` (holding the thread end), the chalk set down; `col_c` `turn_away/sulk>window_dusk` (profile to the window, the medal case shut behind him).
* ALT: `aide_c` `write/smug>count_slate` (chalk poised over the slate; this is the Clause tell, see below); `col_c` per option B.
* TOUCH: the map flaps flat and pins snap (2 frames), `aide_c` swings round and drops the chalk.
* Commit success (C12): `aide_c` `nod/relief>camera` 8 beats (existing). Failure (C12, -5): `aide_c` `shake_head/doubt>camera` (existing), the map slides off the wall into the foreground and the camera takes it.

**Option B: `city.c09.medal` (the Clause).**
* Affordance: CUR `thing_medal_case_open` (new, 1.0 m): lid up, ribbon draped over the velvet, the star medal propped; ALT = existing `thing_medal_case` shut (set `anim none`: remove the pulse).
* CUR: `col_c` `offer/smug>camera` (the medal in his hand, his other arm behind his back); `chap` `shake_head/grief>camera` (existing, kept, in the corner); `aide_c` `write/smug>count_slate` with the chalk tip touching the top of the slate; **ghost mark** `thing_clause_mark` (ghost) on `count_slate`.
* ALT: `col_c` `stare/bored>camera` arms folded, tapping a foot; case shut.
* TOUCH: lid opens (2 frames), `col_c` swings to you with the medal; the aide's chalk drops one hand to the slate.
* Commit success (C11, cinematic `squadron.medal_pinned`, existing walk to `c09_g1`): the medal is lifted toward you and the camera looks down at your chest (pin glint, `thing_medal_pin` foreground 64 x 64, 2 frames, enters from the bottom edge); in the same beat the aide wipes the slate and chalks a higher number (`count_slate` frame `up`, the ghost mark turns wet); `col_c` `laugh/laugh>camera` 8 beats, `chap` `shake_head/grief` 8 beats. Failure (C12, flag `sq_map`): `col_c` `point/anger>c09_x_up` (existing), the case slams, the map drops into your hands as in option A's failure.

**Cast to drop:** `col_c` offer at 0, `aide_c` write at 0, keep `chap` shake_head at 16 and 48 (it is the room's constant).

**Create.**
| item | spec | effort |
| --- | --- | --- |
| `thing_map_wall_threaded` and a curled restyle of `thing_map_wall` | 128 x 128, size 2.4 m; frames `flat`, `flap` | S |
| `thing_medal_case_open` | open case with ribbon and star medal; 128 x 128; remove `pulse` from `medal` | S |
| `thing_count_slate` frames | `24` (as shot), `up` (a clearly higher number, e.g. 31, fresh chalk), size 1.1 m; chalk dust | S |
| `thing_medal_pin` | foreground chest-level pin and ribbon, 64 x 64, 2 frames | S |
| `thing_clause_mark` | shared with C06 | (shared) |
| acts `turn_away`; faces `smug`, `sulk`, `hopeful` | shared | (shared) |
| map: `c09_choice`, move `count_slate` and `aide_c` | `squadron_city.py` | S |

### C10 The Ruined City (`city.c10`, map `city`, room `ruins`)

**Choice.** Situation: burnt streets, a drunk officer at headquarters' door, a night train beyond with a woman begging. Options: `city.c10.hq` (thing `hq_door`, actor `drunk`, DEFAULT, route C09 loops back) success C09 / failure C09 (-5); `city.c10.train` (thing `night_train`, actor `wom`) success C12 (+6, flag `sq_train`) / failure C09 (-6). Today: `route_c10.jpg` (g1/g2) shows the ruins and an edge beacon; the HQ door is behind the camera (95 to 175 deg), the train is 15 to 19 m away with only a pulse light.

**Archetype.** Mechanism state (a railway signal arm) + rival pullers.

**Camera and placement.** Move `hq_door` from (25.6,0.6) to (36.0,0.6) and `drunk` to (35.0,2.0); `wom` home to (34.0,5.6). Add thing `train_signal` (a semaphore signal, 128 x 128, tall, size 3.0 m) at (40.2,3.2). New place `c10_choice` (29.0,7.5) yaw -63 (replace `c10_g2`): HQ 18 deg left (9.8 m), train 18 deg right (15.7 m), the woman between them at 5 m. The fire barrel (28.0,2.4) stays at the left edge as a frame.

**Option A: `city.c10.hq` (default).**
* Affordance: CUR `thing_hq_door_open` (new, 2.4 m): door ajar, a chair kicked against it, an officer's cap and an empty bottle on the step, a slice of a warm lit room (the picture, not just a glow). ALT = existing `thing_hq_door` shut.
* CUR: `drunk` `beckon/laugh>camera` bottle raised, leaning in the doorway; survivors `surv1`, `surv2` `collapse/grief>camera` (existing).
* ALT: `drunk` `sleep/bored>hq_door` (slumped on the step), `wom` per option B.
* TOUCH: door swings ajar (2 frames), the bottle rises.
* RELEASE: the door bumps shut, `drunk` slides down the frame.
* Commit success or failure (C09): `drunk` `laugh/laugh>camera` 8 beats (existing); the camera is led to the door.

**Option B: `city.c10.train`.**
* Affordance: CUR `thing_train_signal` frame `clear` (arm lowered, green-glass lens drawn dull in the daytime sprite, a rope pulled taut) and `thing_night_train_open` (carriage doors rolled back, steam, a few silhouetted hands out of the windows, 256 x 128); ALT = signal frame `danger` (arm raised, rope slack) and the existing `thing_night_train` shut (remove its `pulse`).
* CUR: `wom` `tug/hopeful>night_train` (new act and face; holds your sleeve and pulls toward the train), `surv3` stands `stand/hopeful>night_train`.
* ALT: `wom` `plead/plea>night_train` (existing) hands clasped, sobbing, not pulling; `surv1`, `surv2` `collapse/grief` (existing).
* TOUCH: the signal arm drops with a clank (2 frames) and the doors slide (2 frames); `wom` grabs you in one beat.
* Commit success (C12): `wom` `cheer/relief>camera` (existing), the camera runs to the train. Failure (C09, -6): the arm snaps back up, `wom` `collapse/grief>camera` (existing), the doors slam, the camera is walked back to HQ.

**Cast to drop:** `wom` plead at 16 and 48, `drunk` laugh at 32, `surv1` and `surv2` collapse at 0 and 16 become the ALT state of the train.

**Create.**
| item | spec | effort |
| --- | --- | --- |
| `thing_train_signal` | semaphore signal, 128 x 128 (tall, 3.0 m), frames `danger`, `clear`, `clank` (3) | S |
| `thing_night_train_open` | open carriage doors, steam, silhouettes; 256 x 128; restyle `thing_night_train` shut | M |
| `thing_hq_door_open` | ajar door, chair, cap, bottle; 128 x 128 | S |
| act `tug` (see C04), face `hopeful` | shared | (shared) |
| map: move `hq_door`, `drunk`, `wom`; add `train_signal`, `c10_choice` | `squadron_city.py` | S |

### C11 Endless Missions (`escape`, map `harbour`, room `hut2`) THE CLAUSE (on failure)

**Choice.** Situation: the briefing hut again, the count board repainted 47; the way back to the aircraft (the loop) or the dead radio that might call someone. Options: `escape.aircraft` (thing `aircraft_door`, DEFAULT) success C02 (the loop) / failure C02 (-5); `escape.radio` (thing `radio_broken`, actor `chap_h`) success C12 (+6, flag `sq_radio`) / failure `squadron.count_raised` then C02 (-4). The Clause here is on failure: if you miss, the number goes higher and you fly again. Today: `route_c11.jpg` shows the Colonel and airmen saluting under a "47" board, a purple lane over the left; the aircraft door is behind the camera at home (+134 deg) and the radio sits low at 21 to 41 deg left; the count board is scenery, not part of the choice.

**Archetype.** Crowd faces the way + paperwork and ink + the Clause tell (the Clerk's brush).

**Placement and camera.** Re-stage the hut so the camera at `c11_home` (-1.8,4.0) yaw 90 (looking west, as already) sees everything: move `aircraft_door` from (-0.25,5.6) to the west wall (-11.75,1.3) (15 deg right of centre, size 2.4 m, an aircraft nose in the doorway), keep `count_board` (-11.6,4.0) dead centre, keep `radio_broken` (-9.2,6.9) (21 deg left, 7.4 m). Add thing `hut2_door_east` (the plain door out to the harbour, `thing_hut_door_cold`) at (-0.25,5.6), used only at the radio's commit. Re-home the airmen `h01` to `h04` to a loose file at x -8.6 to -10.4, z 2.0 to 3.4 (toward the aircraft door) so the board and radio stay clear. `c11_x_up` goes to the aircraft door front (-10.4,1.3); `c11_x_right` to the east door. Use `c11_home` as the choice place; `c11_g1`, `c11_g2` re-aim to yaw 90.

**The Clause tell.** `thing_clause_mark` (ghost) on `count_board` from beat 0; `clerk_h` (home (-10.2,5.5), activity `paint`, prop `brush`, new bucket `thing_paint_bucket` at his foot) stands under the board with the brush poised over the last digit, face `smug`, in every state. Cast lines with `if_energy_below` 40: brush on the board and the digit wet (frame `thing_count_board_wet`), so a player who is failing sees the number already being painted.

**Option A: `escape.aircraft` (default).**
* Affordance: CUR `thing_aircraft_door_run` (new, 2.4 m): the aircraft nose in the doorway with propeller turning (the `thing_prop_spin` piece from C02, 3 frames) and exhaust smoke curling in; ALT = existing `thing_aircraft_door` (propeller still, chocks).
* CUR: crowd faces the way: `h01` to `h04` `salute/resolve>aircraft_door` (the existing slowing salutes keep: `beats` 3, 6, 10, 14, the whole joke), `h05`, `h06` file after them; `col_h` `salute/smug>aircraft_door`; `chap_h` `cover_face/grief>camera` (existing).
* ALT: `h01` to `h04` stand easy `stare/hopeful>radio_broken` (arms down, a pace toward it); `col_h` `block/anger>radio_broken`; propeller still.
* TOUCH: propeller kicks over (frame advance), the airmen snap into file in a ripple of 2 beats.
* Commit success or failure (both C02): the airmen march out through the aircraft door in file; `col_h` `point/resolve>count_board` (existing), the board reads the same.

**Option B: `escape.radio` (the Clause).**
* Affordance: CUR `thing_radio_set_open` (new, 1.3 m): cover off, tubes bare, the aerial rod raised and a headset on a hook, a coil of fresh wire; ALT = existing `thing_radio_broken` (smashed, aerial snapped, dust), no flicker.
* CUR: `chap_h` `plead/hopeful>radio_broken` (hands clasped, headset in one hand); `h01` to `h04` as above (ALT of the aircraft); `col_h` `block/anger>radio_broken`; `clerk_h` brush poised (Clause tell).
* ALT: `chap_h` `cover_face/grief>camera` (existing), `clerk_h` brush resting in the bucket (relaxed).
* TOUCH: aerial extends (2 frames), `chap_h` straightens and raises the headset in one beat; the airmen turn.
* Commit success (C12): `chap_h` `nod/relief>camera` 8 beats (existing), the east door `hut2_door_east` swings open onto the blue harbour, the airmen lower their salutes and follow the camera. Failure (`squadron.count_raised`, existing walk to `c11_count`): the Clerk's brush lands: the ghost mark turns wet and solid, the digits repaint one number higher (`thing_count_board_wet`, then `thing_count_board` redrawn); `clerk_h` `write/laugh>count_board` 8 beats, `col_h` `point/resolve>count_board`, `chap_h` `cover_face/grief>camera` (existing cast of the cinematic); the camera is turned to the aircraft door (C02).

**Cast to drop:** `col_h` point at 0, `h01` to `h03` salutes at 0, 16, 32, 48 (reuse as state: keep their `beats`), `chap_h` cover_face at 16 and 48.

**Create.**
| item | spec | effort |
| --- | --- | --- |
| `thing_aircraft_door_run` | doorway with an aircraft nose, propeller 3 frames, exhaust; 128 x 128 (size 2.4 m) | M |
| `thing_radio_set_open` | repaired set with aerial raised; frames `down`, `rise` (2); 128 x 128 | S |
| `thing_count_board_wet` | count board frames `47`, `wet` (half-painted), `48+` higher; 128 x 128 | S |
| `thing_paint_bucket` | 64 x 64, brush resting / raised | S |
| `thing_hut_door_cold` | plain hut door opening onto cold blue harbour; 128 x 128 | S |
| `thing_prop_spin` | shared with C02 | (shared) |
| `thing_clause_mark` | shared | (shared) |
| map: move `aircraft_door`, add `hut2_door_east`, re-home `h01` to `h04`, re-aim `c11_g1`, `c11_g2`, move `c11_x_up`, `c11_x_right` | `squadron_harbour.py` | M |

### C12 Escape North (`escape.c12`, map `harbour`, room `quay`)

**Choice.** Situation: a fisherman's boat in the dark and a sentry under a searchlight tower. Options: `escape.c12.searchlights` (thing `search_a`, actor `sent`, DEFAULT) success C14 / failure C14 (-5); `escape.c12.boat` (thing `boat`, actor `fish`) success C13 (+8, flag `sq_boat`) / failure C14 (-6). Today: `route_c12.jpg` is a good moody quay with the sentry large, but the bright coast through its gap is a block of dither and the boat is a dark hulk; at the window the boat is 18 m away (+1 deg at home) and the light is 11 m away (-25 deg).

**Archetype.** Mechanism state (searchlight head pointing at you or away, sail hoisted or furled, lantern up or down, mooring line cast off or tied), with the sentry and fisherman as quiet rivals (stealth, not cheer). The two lights and the boat are mutually exclusive in the picture: the beam is on the boat when searchlights are CUR, away from it when the boat is CUR.

**Camera.** New place `c12_choice` (7.2,4.4) yaw -119 (replace `c12_g2`): searchlight tower 7.8 m, boat 12.9 m, 46 deg apart. Fix the neutral-coast gap (listed weak art): redraw the gap plate as a pre-filtered soft image, not a dither block, and put the fishing boat in its own pool of cold light.

**Option A: `escape.c12.searchlights` (default).**
* Affordance: CUR `thing_searchlight_aimed` (new, 3.8 m): lamp head swung round and levelled at the camera, hood glinting, a hard bright cone (additive `beam_on_camera` frame) landing on the planks at your feet; tower B (`search_b`, `beam_b`) swings its beam across the boat's deck. ALT = existing `thing_searchlight` (head pitched out to sea, beams sweeping the water).
* CUR: `sent` `point/resolve>camera` (arm up, whistle) then `stare/anger>camera`; `fish` crouches `kneel/fear>search_b` behind the nets (`nets_heap`).
* TOUCH: lamp head swings round (2 frames, 0.4 s), the beam snaps onto you, `sent` jerks up; if the boat was CUR its sail slides down a notch.
* Commit success (C14): the camera walks into the light: `sent` `point/anger>camera` 8 beats (existing). Failure (C14, -5): `sent` `stamp/anger>camera` 8 beats (existing), a stinger of whistle (cast only).

**Option B: `escape.c12.boat`.**
* Affordance: CUR `thing_fishing_boat_ready` (new, 2.8 m, 256 x 128 recommended): sail hoisted halfway, the gold lantern up on its pole and lit, oars shipped, the mooring line cast off the bollard (`bollard` at (16.0,8.6)) and trailing in the water; ALT = existing `thing_fishing_boat` redrawn tied up: sail furled on the boom, lantern down, line looped round the bollard. Raise the hull's value so it stops reading as a dark hulk.
* CUR: `fish` `beckon/fear>camera` then `hush/fear>sent` (new act: forefinger to the lips, eyes on the sentry); `sent` `turn_away/doubt>search_a` (looking out to sea); `search_b` beam swings away from the boat.
* ALT: `fish` `kneel/fear>search_b` (crouched behind the nets), sail furled.
* TOUCH: the sail snaps up a notch and the mooring line falls (2 frames), the beam jerks off the boat, `fish` bounces up to `beckon`.
* Commit success (C13): `sent` `stare/shame>camera` (existing @61, he lets you go), `fish` `nod/relief>camera` (existing); the boat casts off and the camera boards. Failure (C14, -6): `fish` `recoil/fear>camera` (existing), the beam locks on the boat, `sent` `point/resolve>camera` (existing @61).

**Cast to drop:** `fish` beckon at 0 and nod at 32, `sent` stare at 0 (all replaced by state); keep the 61-beat reactions.

**Create.**
| item | spec | effort |
| --- | --- | --- |
| `thing_searchlight_aimed` | lamp head facing camera + additive cone frame; 128 x 128 (3.8 m); frames `aimed`, `swing` (2) | M |
| `thing_fishing_boat_ready` | 256 x 128, sail half up, lantern on pole, line trailing; restyle `thing_fishing_boat` (tied, furled, lighter hull) | M |
| act `hush` | finger to lips, head turning to look aside, 2 beats 4 frames | S |
| coast gap plate redraw | `wall`/gap behind the boat, pre-filtered | S |
| map: `c12_choice` | `squadron_harbour.py` | S |

### C13 The Neutral Coast (`escape.c13`, map `harbour`, room `coast`) ENDING `free`

**Choice.** This is not a branch: the only way out is `escape.c13.shore` (thing `shore_post`, DEFAULT, success and failure both `run:warehouse` with `keep:path_squadron_free`, failure -5). `escape.c13.fisherman` (character `fish_c`, once) has no route: success +8 (flag `sq_thanks`), failure -3. Today: the exit is a wooden post 17 m away with no cue; the fisherman is the only person who beckons.

**Archetype.** Ending: the one exit is always CUR, never swaps; the person is a one-shot gratitude touch that must not take the current.

**Camera.** No change (`c13_g2` (31.0,8.0) yaw -78 has the fisherman at 5.5 m and the post 10.6 m, 6 deg apart: acceptable, they are meant to read as one picture).

**Option A: `escape.c13.shore` (default, always CUR).**
* Affordance: `thing_wooden_post_rope` (new, 1.8 m): the post at the waterline with the dinghy's painted rope coiled on it and a plain white pennant (no emblem) lifting in the wind (2 frames); `shore_boat` (34.0,3.8) dragged up beside it with an oar across the thwart; a line of footprints in the sand from the camera to the post (floor decal, 128 x 64).
* CUR (always): gulls `birds` (36.0,8.0) perch on the post; `quay_w` `wave/happy>camera` (existing cast at 16).
* TOUCH: the pennant flicks, the dinghy rocks. Commit (both): the dinghy shoves off into a turquoise swell; camera walks to the water's edge. No failure picture.

**Option B: `escape.c13.fisherman` (character, not a route).**
* Affordance: the existing `beckon` look; `fish_c` `laugh/relief>camera` always.
* TOUCH (never takes CURRENT): `nod/happy>camera`. Commit success: `cheer/cheer>camera` 8 beats (existing); failure: `shake_head/happy>camera` 6 beats (existing); he tips his hat to you (`thing` hat prop already exists) as a P3 extra.

**Create.**
| item | spec | effort |
| --- | --- | --- |
| `thing_wooden_post_rope` | 128 x 128, 2 frames pennant sway, coiled rope | S |
| decal `thing_footprints` | sand footprints toward the post, 128 x 64 | S |

### C14 Captured (`escape.c14`, map `harbour`, room `cell`)

**Choice.** Situation: a cell with a guard, the Clerk who stamps your fate, and a cellmate with an escape plan. Options: `escape.c14.order` (thing `order_paper`, actor `clerk_k`, DEFAULT) success C11 (loop) / failure C11 (-5); `escape.c14.latch` (thing `latch`, actor `mate`) success C12 (+6, flag `sq_latch`) / failure C11 (-5). Today: `route_c14.jpg` keeps the latch ahead (good) but the order paper is 30 to 55 deg right and tiny; the cellmate and guard are at 70 to 130 deg and not in frame.

**Archetype.** Mechanism state (a latch and a rope of knotted sheets) + paperwork and ink (the stamped order) + rival pullers (cellmate against Clerk).

**Camera and placement.** New place `c14_choice` (4.0,-3.2) yaw 9 (replace `c14_g2`): order 22 deg left (3.5 m), latch 22 deg right (4.5 m). Move `mate` home to (6.8,-6.6) beside the latch, `guard` home to (1.8,-5.4) beside the Clerk's table; `clerk_k` stays (3.4,-6.2).

**Option A: `escape.c14.order` (default).**
* Affordance: CUR `thing_order_stamped` (new, 1.3 m): the order sheet with a wet red ring stamp on it, the stamp lying on the pad, a pen; ALT = existing `thing_order_paper` blank, the stamp lifted and the pad closed.
* CUR: `clerk_k` `stamp/smug>order_paper` (new face) with a steady rhythm; `guard` `block/anger>camera`; `mate` `sad/sulk>camera` sitting on the bunk (knotted sheets hidden).
* ALT: `clerk_k` `write/bored>order_paper` yawning; `guard` `turn_away/bored>cell_door` (back half turned: the hole in the guarding).
* TOUCH: the stamp thumps (2 frames), `guard` squares up.
* Commit success or failure (C11): `clerk_k` `laugh/laugh>camera` 8 beats (existing); `guard` marches you out.

**Option B: `escape.c14.latch`.**
* Affordance: CUR `thing_window_latch_up` (new, 1.7 m): latch lifted, the window ajar by a finger, a sliver of cold sky; `thing_knotted_sheets` frame `hanging`: a rope of knotted blankets running from the bunk to the sill. ALT = existing `thing_window_latch` (down, bolted), `thing_knotted_sheets` frame `coil` (a bundle in the corner under the bunk).
* CUR: `mate` `beckon/hopeful>camera` then `point/resolve>latch` (existing available pose) with `hush/fear>guard`; `guard` `turn_away/bored>cell_door`.
* ALT: `mate` `sad/sulk>camera` on the bunk.
* TOUCH: the latch pops up and the rope unrolls toward the window (3 frames over one beat), `mate` bounds up.
* Commit success (C12): `mate` `cheer/relief>camera` 8 beats (existing), latch fully open, the camera climbs out (rail style `climb`). Failure (C11, -5): `mate` `shake_head/doubt>camera` (existing), the guard swings round, the rope is yanked back and the latch drops.

**Cast to drop:** `guard` block at 0, `clerk_k` write at 0 and laugh at 32, `mate` shake_head at 16 and point at 32.

**Create.**
| item | spec | effort |
| --- | --- | --- |
| `thing_window_latch_up` | open latch, ajar window; 128 x 128 | S |
| `thing_knotted_sheets` | frames `coil`, `unroll` (2), `hanging`; 128 x 128 | S |
| `thing_order_stamped` | stamped order, pad, pen; frames `blank`, `stamp`, `stamped`; 128 x 128 | S |
| map: `c14_choice`, move `mate`, `guard` | `squadron_harbour.py` | S |

## 3. New assets and expressions (roll-up)

| group | count | items |
| --- | --- | --- |
| New prop and set-piece sprites (new names, each with its state frames) | 41 | C01: `thing_cot_turned`, `thing_board_orders`. C02: `thing_ladder_up`, `thing_crate_stack_open`, `thing_prop_spin` (also C11). C03: `thing_kitchen_hatch_open`, `thing_door_office_ajar`, `thing_door_office_open` (also C06). C04: `thing_release_lever_armed`, `thing_emergency_box_open`. C05: `thing_truck_ready`, `thing_ledger_open`. C06: `thing_certificate_ready`, `thing_certificate_stamped`, `thing_certificate_fallen`, `thing_stamp_fly`, `thing_orders_stack`, `thing_clause_mark` (also C09, C11). C07: `thing_medkit_open`. C08: `thing_barrier_pole_up`, `thing_barrier_pole_down`, `thing_staff_car_open`. C09: `thing_map_wall_threaded`, `thing_medal_case_open`, `thing_medal_pin`, `thing_count_slate` (frames `24`, `up`). C10: `thing_train_signal`, `thing_night_train_open`, `thing_hq_door_open`. C11: `thing_aircraft_door_run`, `thing_radio_set_open`, `thing_count_board_wet`, `thing_paint_bucket`, `thing_hut_door_cold`. C12: `thing_searchlight_aimed`, `thing_fishing_boat_ready`. C13: `thing_wooden_post_rope`, `thing_footprints`. C14: `thing_window_latch_up`, `thing_knotted_sheets`, `thing_order_stamped` |
| Restyles of existing sprites (ALT frames) | 12 | `thing_ladder` (check it reads as lowered), `thing_release_lever` (pinned), `thing_emergency_box` (sealed, no pulse), `thing_stamp_big` (dry, cobwebbed), `thing_kitchen_hatch` (shut), `thing_map_wall` (curled), `thing_medal_case` (no pulse), `thing_staff_car` (windscreen, already weak art), `thing_night_train` (no pulse), `thing_fishing_boat` (tied, lighter hull), `thing_radio_broken` (no flicker), `thing_window_latch` |
| New faces | 4 | `hopeful` (brows lifted and softened, eyes up, small closed smile), `smug` (lids half down, one mouth corner up, chin up), `sulk` (brows flat and low at the ends, eyes slid aside, lower lip out), `bored` (lids half down, flat mouth, no brow movement); each with the species rule and an LOD 4 fallback (`hopeful` to `happy`, `smug` to `neutral`, `sulk` to `sad`, `bored` to `neutral`) |
| New acts | 7 | `tug` (arm reaches to the camera and tugs back twice, body leaning away toward the thing, 2 beats 8 frames), `turn_away` (profile, head turned further, shoulders dropped, 8 beats 2 frames), `sweep_arm` (arm sweeps to a side, half bow, 2 beats 6 frames), `hold_up` (both hands raise a clipboard, certificate or paper to the viewer, 2 beats 4 frames), `shrug` (palms out, shoulders up, 2 beats 4 frames), `pat` (hand pats a surface twice, torso leans toward it, 2 beats 6 frames), `hush` (forefinger to lips, glance aside, 2 beats 4 frames); all front and side |
| New actors and wardrobe | 1 | `cook` (`airman` b + `apron` + `knit` hat), home (8.4,-10.3) in C03 |
| New people props | 2 | `jacket` (folded over forearm; C07 `pilot_c`), `dressing` (bandage in the hands; C07 `crew1c`) |
| New map things, waypoints and moved things | 6 new things, 12 new waypoints, 19 moved | new things: `tent_door_office`, `door_b_mark`, `stamp_fly`, `arch_pole`, `train_signal`, `hut2_door_east`; waypoints: `cNN_choice` for every scene but C11 (which uses `c11_home`) and C13 (keeps `c13_g2`); moved: `kitchen_hatch`, `certificate`, `crates`, `qm`, `count_slate`, `aide_c`, `hq_door`, `drunk`, `wom`, `aircraft_door`, `mp1`, `mp2`, `kid_c`, `mate`, `guard`, `h01` to `h04` |
| Hotspots with no `acting` block today | 6 | four get one: `base.cot` (`a04`), `base.c03.hatch` (`cook`), `air.c06.door_a` (`clerk`), `escape.aircraft` (`col_h`); `base.c03.office_door` and `escape.c13.shore` have no person (state frames only) |

Effort total: 4 L scenes (C03, C06, C09, C11), 8 M, 2 S. Priority: P1 C01, C02, C03, C06, C09, C11, C12 (the first scene's teaching, the Clause, the three worst camera cases); P2 C04, C05, C07, C08, C10, C14; P3 C13.

## 4. Cross-cutting issues

**Engine needs.**
1. **State-keyed staging.** Per hotspot, poses per state: `current`, `alt`, `touched` (one beat), `released` (one beat), for the hotspot's actor and for named supporting actors; per thing a frame for `current`, `alt`, `success`, `failure`. Sketch: `"staging": {"actors": {"a04": {"current": {"act": "pat", "face": "hopeful", "look_at": "camera"}, "alt": {...}, "touched": {...}, "released": {...}}}, "things": {"cot_empty": {"current": "thing_cot_turned", "alt": "thing_cot_empty"}}}`. The existing `acting.available` maps to the default option's `current`, `selected` to `touched`.
2. **Shared route state.** C03 has two hotspots for route C06 (door and Surgeon): the room shows one "door ajar" state keyed by route, the Surgeon's extra pose keyed by hotspot.
3. **Non-route hotspots do not take CURRENT** (C13 fisherman).
4. **Choice staging visible from beat 0** of the first lap; touch accepted from the moment the window opens (the engine agent decides when). The actors' CUR and ALT poses override the scene's `cast` lines for those actors; lines at beat 61 (result reactions) still fire.
5. **Camera hold in the window.** Add a `choice` place per scene (12 new `cNN_choice` waypoints, C11 uses `c11_home`, C13 keeps `c13_g2`; positions and yaws above) that the rail holds through both laps; glances and strolls are suppressed (or limited to 8 deg) while a window is open, or the options leave the frame. Every place above keeps both options within 56 deg of each other, inside the 82 deg frame.
6. **Cinematic piece ops** inside `squadron.double_stamp`, `squadron.medal_pinned` and `squadron.count_raised`: cast lines `piece/op` at beats 2 to 3 (the second stamp, the new chalk number, the new paint). These are already valid in `validate_cast` (`CINE_CAST_LAST_BEAT` 16).
7. **Energy-conditioned lines.** C11's brush uses `if_energy_below` (valid today).
8. **Look kinds.** `pulse` and `flicker` on `medal`, `emergency_box`, `night_train`, `radio_broken`, `kitchen_hatch` and the `glow` rings are light-only cues; keep them as the engine's fallback marker for new paths, but remove the `anim` pulse and flicker from these sprites once their state frames exist, so the pose, not the light, is the signal.
9. **Insistence.** Lap 2 halves the CUR person's `beats` and deepens the ALT person's droop (one more frame of the same act). One generic rule, no per-scene data.
10. **Contract.** `HotspotContract` insists a hotspot anchored on a thing with no `acting.actor` has nobody to direct; the four exits above get actors (list in section 3). `tools/run/check_hotspots.py` wants the anchor of an exit on a thing or doorway: `base.c03.office_door` moves from a waypoint to `tent_door_office`.

**Shared pieces (build once).** `thing_clause_mark` (C06, C09, C11), `thing_door_office_ajar` and `_open` (C03, C06), `thing_prop_spin` (C02, C11), acts `tug` (C04, C10), `hold_up` (C03, C06), `turn_away` (C03, C06, C09, C12, C14), `sweep_arm` (C03, C08), `hush` (C12, C14); the four faces serve every scene.

**Rail changes (summary).** Twelve new `cNN_choice` places (C11 uses `c11_home`, C13 keeps `c13_g2`), the re-hung certificate (C06), the re-staged hut door (C11), the re-staged tent far wall (C03), the moved arch group (C08), HQ and the woman (C10), crates (C02), mate and guard (C14). All in `tools/paths/squadron_{airfield,city,harbour}.py`.

**Risks.** (1) The MP, patient and Gunner sprites are listed as weak art (the helmet reads as a plain dome; the Gunner reads as a small man): a face rig that must carry `sulk` and `hopeful` is only as good as those heads, so redraw the MP helmet and the Gunner's head first. (2) Pixel-scale of faces: all four new faces must read at 17 x 13 and at LOD 2; check with `tools/story/face_sheets.py`. (3) Props with transparent windows (the C03 hatch) depend on the actor's z-order behind the thing; the engine agent should confirm billboards can sit in front of an actor. (4) C08's arch move may cut across the portal to the ruins; check the walls in `squadron_city.py`. (5) The joke of C06, C09 and C11 depends on the ghost mark being noticed after the fact: if playtest shows nobody connects it, raise its alpha from 30 % to 50 %, do not add text.

## 5. Coverage check

Run in the worktree: `python3` over `content/paths/squadron/hotspots/*.json` and `run.json`, comparing every hotspot id with the ids named in this file in backticks. Result: see the line below (filled in by the script).

Script result: 29 hotspots in 14 scenes of 14 nodes; 14 scenes have 2+ hotspots; hotspot ids missing from this file: none; scene sections present: 14 (C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, C13, C14).




