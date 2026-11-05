# Gospel path: choice briefs (visual representation of every branching point)

Path `gospel`, 17 scenes J00 to J16, 43 hotspots, 124 BPM. Written 5 Nov 2026 by a game designer; documents only, no code or art. Source data: `content/paths/gospel/run.json`, `content/paths/gospel/hotspots/{jordan,galilee,road,jerusalem}.json`, maps `content/story/maps/{galilee_shore,hillside,bethany,jerusalem}.json`, shots `docs/shots/gospel/`, `docs/shots/acting/gospel_*`, notes `docs/paths/gospel.md`.
Owner verdict being answered: the game is a walking sim behind the music game; every branch must be readable in the world (people, props), with the default obvious from beat 0, a first-time player able to tell what a press does, no floating text, and not only "things of light".

Assumed engine (another agent builds it): at any moment exactly one option of the scene is CURRENT (starts as the default); a touch on any option's thing makes it current within one beat (0.48 s at 124 BPM); changeable until the commit; the commit resolves success or failure by the last block, as today. Two laps per scene are assumed (staging plays twice; commit at the decision beat 60.5 of lap 2). Every state below is **state-driven, not beat-timed**, so it is identical in both laps.

## Conventions used by every entry

* **Vocabulary.** CUR = this option is current. IDLE = not current. TOUCH = the one-beat reaction when the player touches it. RELEASE = what the previously current option does when another is touched. OK / FAIL = commit outcome visuals (success / failure of the last block).
* **The grammar (identical in every scene, so a player learns it once in J00 and J01).** An option is always a *thing that is already doing something* (an idle loop), never a dead object. IDLE keeps its invitation, small and sad: a person still gestures at the camera at half amplitude with a `sad`/`sulk`/`doubt` face; a prop keeps its idle loop. CUR is the same invitation at full amplitude: the person steps one pace toward the camera, leans in, face `hopeful` or `happy`; the prop changes shape (opened, loaded, lifted, unfurled). Bystanders `look_at: "@current"`: every head in the room turns to what will happen. The selection ring stays as a small secondary hit hint, never the only cue.
* **Not colour alone.** Posture, gaze, held props, open or shut, loaded or empty, animals. No red/green door pairs in this path: they do not fit a first-century setting and the story tone (grief, trial, tomb) forbids a game-show reading. No signboards are proposed (none would exist here); no floating text anywhere.
* **Success vs failure at commit (rule).** On OK the chosen option's people get `cheer`/`relief`/`awe` and the thing completes (loaded, opened, lifted); on FAIL the same people show `shake_head`/`shrug@sulk`/`collapse` and the thing falters, and the route shown is the failure route. Where the data's failure route equals the success route (all exits, which only add a `stagger` cinematic) the FAIL beat is a distinct stumble and a flat reaction from the same people (Cross-cutting E8).
* **Insistence in lap 2.** Same states; invitation loops run about 25 % faster and each CUR person stands one more pace forward. Option-actor `cast` lines in run.json (listed per scene as "cast conflict") must not overwrite a CUR/IDLE pose (Cross-cutting E5).
* **Pixel scale.** 1 sprite pixel = 1 low-res pixel (the world renders 360 lines at full height; `thing_*` sprites run about 35 px per metre of `size`: palm 176 px = 5 m, boat 96 px = 2.6 m; an adult is 112 px in the full-detail sheet and about 56 px at mid distance). New sprites go in `assets/story/<map>/textures/thing_<name>[_<state>].png`, are drawn in `tools/story/art/gospel_things_b.py` (a new `gospel_things_c.py` if it gets long), registered as map things with `"piece": "<view>.<name>_<state>"` in `tools/story/art/gospel_maps.py`, and listed in the manifest `stage.pieces` by `tools/story/build_gospel_art.py`. State sets use piece ids `<view>.<name>_idle|_cur|_ok|_fail`; the engine shows the one that matches the option's state.
* **People.** Acts and faces named `act@face` are baked per actor by `tools/story/art/directed.py` from the data, so every `act@face` named here is a bake request (listed as `BAKE`). New actors are added as `homes` in the map json with an archetype of `wardrobe.gospel()`. The hero (the camera) is never drawn.
* **Stay original.** Nothing from a published work other than the Gospel text; soldiers keep the plain unmarked cuirass.

## Summary table (all 17 scenes)

Verdict today: UNREADABLE = the choice cannot be told from the picture; WEAK = parts readable; ONE-WAY = not a real branch (note only). Effort S/M/L; priority P1 (fix first) to P3.

| scene | options (default first) | default | verdict today | archetype | effort | pri |
| --- | --- | --- | --- | --- | --- | --- |
| J00 `jordan` Bethlehem | `jordan.road`, `jordan.shepherd` (no route) | road | ONE-WAY; the side touch has no visible effect | A7 single way + tutorial touch | S | P2 |
| J01 `jordan.baptism` | `jordan.baptism.nazareth`, `jordan.baptism.dove` | Nazareth | UNREADABLE (dove is a glow, the town far scenery) | A3 bird as pointer + A2 two tracks | M | P1 |
| J02 `jordan.wilderness` | `jordan.wilderness.path`, `jordan.wilderness.fires` | path | UNREADABLE (empty floor and a 14 m fire; tempter acts the same both ways) | A2 trail vs camp + antagonist reaction | M | P2 |
| J03 `jordan.nazareth` | `jordan.nazareth.road`, `.neighbour`, `.cart` | road | WEAK (neighbour pleads at beat 16 only) | A1 beckon + A5 work | M | P2 |
| J04 `galilee` | `galilee.mount`, `galilee.fishermen`, `galilee.boat` | mount | WEAK (fishermen readable; boat 35 px; road empty) | A5 work + A1 | L | P1 |
| J05 `galilee.capernaum` | `galilee.capernaum.mount`, `.family`, `.caravan` | mount | WEAK (family and caravan on one line of sight; failure looks like success) | A1 emotive + A5 | L | P1 |
| J06 `galilee.mount` | `galilee.mount.loaves`, `.crowd`, `.boat` | loaves | WEAK (crowd and exit co-linear; boat 35 px) | A4 crowd lean + A5 boat | M | P2 |
| J07 `galilee.storm` | `galilee.storm.loaves`, `.south`, `.beacon` | loaves | UNREADABLE (beacon at -57 degrees is off screen; the acting disciple stands 55 degrees from it) | A6 weather + boat as compass | L | P1 |
| J08 `road` Bethany | `road.loaves`, `road.table`, `road.donkey` | loaves | WEAK (donkey at +50 degrees; exit behind the table) | A1 hosts + A3 animal | M | P2 |
| J09 `road.loaves` | `road.loaves.entry`, `.baskets`, `.lantern` | entry | WEAK (baskets do not read as a button) | A5 baskets + A1 | M | P2 |
| J10 `road.entry` | `road.entry.steps`, `road.entry.grove` | steps | UNREADABLE (both exits left of centre; the gate in the middle is neither) | A4 crowd + A2 gate/lane | M | P2 |
| J11 `jerusalem` Temple | `jerusalem.garden`, `.tables`, `.guards` | garden | WEAK (guards behind the tables on one line; only 1 of 3 tables answers) | A2 veil + A5 + A1 | M | P2 |
| J12 `jerusalem.gethsemane` | `jerusalem.gethsemane.trial`, `.sleepers`, `.shadowed` | trial | UNREADABLE (default and sleepers co-linear; guards arrive on the escape side; near black) | A6 posture only | M | P1 |
| J13 `jerusalem.trial` | `jerusalem.trial.passage`, `jerusalem.trial.gate` | passage | UNREADABLE (two empty-floor exits, no actor) | A2 barred/open + A1 | M | P1 |
| J14 `jerusalem.golgotha` | `jerusalem.golgotha.hill`, `.women` (no route) | hill | ONE-WAY | A7 solemn | S | P3 |
| J15 `jerusalem.tomb` (ending) | `jerusalem.tomb.home`, `.stone` (both `run:warehouse`) | home | ONE-WAY | A7 ending flavour | S | P3 |
| J16 `jerusalem.road` (ending) | `jerusalem.road.home`, `.followers` (both `run:warehouse`) | home | ONE-WAY | A7 ending companions | S | P3 |

Archetypes: A1 people beckon (current = happy; the others still beckon but sad); A2 two ways with a physical state (open/shut, up/down); A3 an animal or bird points; A4 a crowd leans or moves palms; A5 work in progress (a sail, a loaded cart, uncovered baskets); A6 weather/night, posture only; A7 one way (ending or side touch).

## Shared kit (defined once, referenced by code)

New **faces** (pixel rig: head 17 x 13 px full size; at half detail one pixel per eye, so brows, eye height and mouth shape carry it). Each is one new entry in `StoryCharacter.FACES`, baked per actor that names it:
* **F1 `hopeful`**: brows raised with the inner ends up (a 2 px slant), eyes one pixel higher and wide, gaze at the camera, closed 3 px up-curved mouth. Reads as "please come" without the open mouth of `plea`.
* **F2 `smug`**: one brow up one pixel, upper lids lowered (eyes 1 px tall), a 3 px smile with one corner a pixel higher. The tempter, the money-changers, a pleased guard.
* **F3 `sulk`**: brows level and low, pupils shifted to the lower corner (looks away, not at the camera), flat 3 px mouth with the ends down 1 px, head lowered 2 px. The sad invitation of IDLE options and the rejected after a commit.

New **acts** (poses of the rig; each frames in `front` and `side`, `turn_away` also `back`):
* **A1 `sweep_arm`**: one arm extends, palm up, sweeping about 60 degrees over 2 beats toward the target, then holds; 4 frames. "The way is this."
* **A2 `turn_away`**: shoulders and head turn about 120 degrees from the camera, arms drop; 3 frames. Used after a commit for the option that lost.
* **A3 `reach`**: both arms forward and low, hands open, torso leaning 8 degrees, 3 frames (the open version of `plead`).
* **A4 `hold_up`**: one arm raised overhead carrying the held prop; 3 frames.
* **A5 `shrug`**: shoulders up 2 px, forearms out, palms up; 3 frames front only.
* **A6 `wash`**: both hands over a bowl at waist height, rubbing; a 2-frame loop in `side`.

New **held props** (hand slot in `people.py` `held`, drawn in the hand pixel; 5 to 20 px):
* **H1 `loaf`** (12 x 8, round flat bread), **H2 `lantern`** (8 x 12 clay lamp on a handle, lit frame), **H3 `crook`** (4 x 52 shepherd's staff), **H4 `palm_frond`** (20 x 24), **H5 `net`** (16 x 14 net bundle that drapes), **H6 `torch`** (6 x 20 with a 2-frame flame), **H7 `lamb`** (14 x 12), **H8 `bowl`** (10 x 6 with water).

Shared **props** (each built once, placed in several views): **P-boat `boat_moored_idle|_cur`** (96 x 64 px, a small fishing boat; `idle` sail furled along the boom, oars shipped; `cur` sail raised and filled, one oar out), used in J04 and J06; **P-donkey `donkey_idle|_cur`** (96 x 80, same size as `thing_donkey`; `idle` head down, hind leg cocked, pack on the ground; `cur` loaded, saddled, ears forward, lead rope taut), used in J03 and J08.

---

## J00 `jordan`: Bethlehem, the star (map galilee_shore, view `bank_night`)

**Situation.** Night road, shepherds kneel before a stable under the star; the camera arrives, then leaves by the road. A single-way scene (the contract forces a second harmless hotspot).

| option | hotspot id | anchor today | success | failure | default |
| --- | --- | --- | --- | --- | --- |
| road | `jordan.road` (exit) | waypoint `bank_night.door_up`, 0 degrees, 11.2 m (empty floor) | `jordan.baptism` | `jordan.baptism` + `gospel.stagger_jordan_road`, -5 | yes |
| shepherd | `jordan.shepherd` (character, actor `sh2`) | -15 degrees, 7.7 m | no route; flag `gospel_shepherds`, +6 | -4 | no |

**Today.** The road is an unmarked patch of floor; the shepherd kneels and bows from the cast and shows only a ring when touched. Nothing tells the player that touching a person is the game's verb. Not a real branch.

**Archetype.** A7, and the **tutorial touch**: the first time in the run a player touches a person and sees the person answer.

**Design.**
* Road (default, CUR from beat 0): a worn track with hoof prints running to the gap; `sheep4` (+7 degrees) and `sheep3` face along it (flip them to face the track). A line of three small stones laid as a path edge (existing `thing_rock_a`, re-placed). No state change needed: it is current until the shepherd is touched.
* Shepherd IDLE: `kneel@awe` toward the stable (side view), crook lying on the ground; plus a small invitation loop: every 8 beats `sh2` turns his head to the camera and back (`look`, existing).
* Shepherd TOUCH (one beat): `sh2` stands (the `kneel` to stand takes the first beat), face `hopeful`, `look_at: camera`. CUR: `hold_up@hopeful` with the **H7 lamb** aloft, crook (**H3**) in the other hand, one pace toward the camera. RELEASE (road touched again): `bow@awe` back to `kneel@awe` over 3 beats, lamb set down.
* Commit OK (shepherd current): `cheer@happy` lamb overhead, `sh1`/`sh3` rise and `wave@happy`, `sh2` walks 4 steps along the road ahead of the camera. FAIL: `shrug@sulk`, lamb lowered. Road OK or FAIL: the three shepherds stay kneeling; FAIL adds the existing stagger only.
* Payoff (optional, P3): the honoured shepherd returns as `sp1` at J16 (`bow@awe`) conditional on `gospel_shepherds`.

**Placement and camera.** Both in view at the home yaw (0 and -15 degrees). Nothing to move.

**Create.**
* NEW held `crook` H3, NEW held `lamb` H7 (shared kit).
* NEW face `hopeful` F1, NEW face `sulk` F3, NEW act `hold_up` A4, NEW act `shrug` A5 (shared kit).
* BAKE `sh2`: `kneel@awe` (exists), `hold_up@hopeful`, `cheer@happy`, `shrug@sulk`, `bow@awe`; BAKE `sh1`,`sh3`: `wave@happy`.
* Cast conflict: `sh1`/`sh3` kneel lines are fine (they are not option actors); `sh2` has none. No removals.
* EXISTS: stable, sheep, star piece, shepherds.

**Effort S, priority P2** (tutorial value).

---

## J01 `jordan.baptism`: Baptism in the Jordan (map galilee_shore, view `bank_dawn`)

**Situation.** Dawn at the river. The Baptist stands in the water; a dove descends. Choice: follow the call into the wilderness, or return to the quiet life in Nazareth.

| option | hotspot id | anchor today | success | failure | default |
| --- | --- | --- | --- | --- | --- |
| Nazareth | `jordan.baptism.nazareth` (exit) | thing `bank_dawn.town`, +22 degrees, 14.2 m | `jordan.nazareth` | `jordan.nazareth` + stagger, -5 | yes |
| wilderness | `jordan.baptism.dove` (feature, actor `b1` the Baptist) | thing `bank_dawn.dove`, 0 degrees, 9.6 m (additive light piece); flag `gospel_baptised`, +6 | `jordan.wilderness` | `jordan.nazareth`, -4 | no |

**Today.** The dove is a bright additive sprite above the water; the town a 4.6 m backdrop strip at the edge of the view. Two things of light, no visible "ways". The Baptist points at `door_right` (nothing is there) at beat 32.

**Archetype.** A3 (the dove is the pointer) with A2 (two physical tracks leave the bank).

**Design.**
* Re-stage the bank with two tracks: the **wild track** (a footpath of pale stones climbing between rocks to a bare ridge) at -28 degrees / 9 m, and the **cart track** with a **milestone post** at +20 degrees / 6 m leading to the town. One dove, two places: it is the compass.
* Wilderness CUR: the dove is **in the air** over the river at -12 degrees (2-frame wing beat, a loose circle), the Baptist `point@resolve` along the wild track then `beckon@awe`; pilgrims `v2`,`v3` `look_at @current`, `awe`; Nazareth-side `v1_bank_dawn`,`v5` `beckon@sad` at half amplitude.
* Wilderness IDLE (Nazareth current): the dove **perches on the post** by the cart track (wings folded, head turned to the town); the Baptist `bow@happy` toward the camera, hands open (a blessing for the way home); `v2`,`v3` `beckon@sad` toward the wild track at half amplitude; town chimney **smoke thick and rising** (`town_smoke_cur`), vs thin (`town_smoke_idle`) when wilderness is current.
* Nazareth CUR: as the IDLE-wilderness description; `v1_bank_dawn`,`v5` `beckon@hopeful` full amplitude, a small cart (reuse `thing_cart` from the workshop map) stands waiting on the cart track.
* TOUCH (one beat): the dove takes off or lands (2 beats of wing frames, the first beat already changes pose), smoke changes, the previously current side drops to `beckon@sad`.
* Commit wilderness OK: the dove climbs and flies off along the wild track, the Baptist `bow@awe` then `point@resolve`, `v2`,`v3` `cheer@happy`, `v1_bank_dawn`,`v5` `turn_away@sulk`. FAIL (route to Nazareth): the dove wavers, drops to the post, the Baptist `shake_head@doubt`. Nazareth OK: the dove stays, `v1_bank_dawn`,`v5` `cheer@happy`, the Baptist `bow@happy`. FAIL: the dove startles off over the town, `v1_bank_dawn` `shrug@sulk`.
* The existing `cast` cheer/doubt lines (v1, v2, v3) may stay as ambient only when they match CUR; the b1 `point` line at beat 32 must not fire when Nazareth is current.

**Placement and camera.** All within +-30 degrees, 6 to 9 m (the route window holds the head within 8 degrees of the home yaw). Replace the `bank_dawn.dove` additive piece (0 degrees, 9.6 m) by the two dove pieces; multi-anchor hotspots (Cross-cutting E3): wilderness = [`b1`, `dove_air`, `dove_perch`, `wild_track`], Nazareth = [`town`, `post`, `cart_track`]. Re-home `v1_bank_dawn` to +18 degrees / 5.5 m and `v5` to +26 degrees / 6 m; `v2`,`v3` stay at -19 and +23 degrees (move `v3` to -24 degrees / 5 m).

**Create.**
* NEW prop `wild_track` 128 x 64, 1 frame, galilee_shore/bank_dawn (pale stones up between two rocks to a ridge, tinted by dawn).
* NEW prop `post` 20 x 44, 1 frame, bank_dawn (a milestone post with a mooring ring).
* NEW prop `dove_perch` 24 x 20, 1 frame, bank_dawn (replaces the glow dove at rest).
* NEW prop `dove_air` 28 x 22, 2 frames, bank_dawn (wing beat, pixel loop of 6 beats' travel to be moved by the engine).
* NEW prop `town_smoke` 24 x 48, 2 state frames (`idle` thin, `cur` thick; 3 animation frames each), bank_dawn.
* NEW act `sweep_arm` A1 (Baptist).
* BAKE `b1`: `bow@happy`, `beckon@awe`, `shake_head@doubt`, `sweep_arm@happy` (kept `point@resolve`); BAKE `v1_bank_dawn`,`v5`: `beckon@hopeful`,`beckon@sad`,`cheer@happy`,`shrug@sulk`; BAKE `v2`,`v3`: `beckon@sad`,`awe`,`cheer@happy`,`turn_away@sulk`.
* EXISTS: reeds, palms, river band, `town`, `thing_cart` (needs a copy into `assets/story/galilee_shore/textures/`).

**Effort M, priority P1** (first true branch: it teaches the grammar).

---

## J02 `jordan.wilderness`: Temptation (map galilee_shore, view `rocks`)

**Situation.** The wilderness; a tall dust-coloured figure offers bread. Choice: the hard path on through the rocks, or the village fires (warmth, the soft way).

| option | hotspot id | anchor today | success | failure | default |
| --- | --- | --- | --- | --- | --- |
| path | `jordan.wilderness.path` (exit, acting `t1`) | waypoint `rocks.door_up`, 0 degrees, 11.2 m (empty floor) | `galilee` | `galilee` + stagger, -5 | yes |
| fires | `jordan.wilderness.fires` (exit, acting `t1`) | thing `rocks.fires`, -27 degrees, 14.1 m | `galilee.capernaum` | `galilee.capernaum` + stagger, -5 | no |

**Today.** Neither exit is visible: one is bare floor, the other two 0.9 m fire sprites at 14 m. The tempter (+17 degrees) gives the same acting block to both. Both failures are identical (stagger to the same place).

**Archetype.** A2 (trail vs camp) with the antagonist as the live indicator.

**Design.**
* Path: a **cairn trail** of three stacked-stone cairns climbing the gap between `rockC` (-14 degrees) and `rockD` (+16 degrees), each carrying a strip of cloth on a stick. IDLE: the cloth hangs limp. CUR: the cloth stands out streaming up the trail and a scrap of dust blows along it. The tempter CUR(path): `recoil@anger`, then `turn_away@sulk`, the bread basket covered with his cloak (`bread_covered`).
* Fires: a **camp** moved to -30 degrees / 8 m: a lean-to of cloth on poles and two campers `camper1`,`camper2` (villager archetype). IDLE: fire low, one camper `sleep`, the other `sit@sulk`. CUR: fire high with a leaning smoke column, both campers `wave@happy` and `beckon@hopeful`; the tempter CUR(fires): `offer@smug` with **H1 loaf** held out, one pace toward the camera, basket open (`bread_open`, steam 2 frames).
* TOUCH: the cloth snaps taut (path) or the camp stirs and the loaf comes up (fires), within the first beat; the other side relaxes (RELEASE: cloth drops, campers `beckon@sad`).
* Commit path OK: the tempter `recoil@anger` backing off, dust; FAIL: the camera stumbles, the tempter `laugh@smug`. Fires OK: the campers `cheer@happy`, the tempter `laugh@smug` (he is pleased); FAIL: stumble, campers `shrug@sulk`, the tempter `laugh@smug`.
* Cast conflict: all `t1` cast lines (stare, offer, laugh, shake_head) are replaced by the state poses; keep a `laugh@smug` at beat 32 only `if_energy_below 50`.

**Placement and camera.** Move `rocks.fires` and `rocks.fires2` to -30 degrees / 8 m (a camp, not a far light); cairns at 0 degrees / 8 to 11 m in the gap; the tempter stays at +17 degrees / 8.4 m (re-home to +14 degrees so he reads between the two options). All inside +-35 degrees.

**Create.**
* NEW prop `cairn` 20 x 36, 2 state frames (`idle` limp cloth, `cur` streaming), rocks (3 placements).
* NEW prop `camp` 80 x 56, 2 state frames (`idle` low fire, `cur` high fire with smoke), rocks.
* NEW prop `bread_basket` 24 x 20, 2 frames (`covered` cloak over, `open` with a loaf and steam), replaces `thing_basket_full` at `rocks.bread`.
* NEW actor `camper1`,`camper2` (villager, seated near the camp).
* NEW face `smug` F2, NEW face `sulk` F3, NEW act `turn_away` A2, NEW held `loaf` H1.
* BAKE `t1`: `recoil@anger`, `turn_away@sulk`, `offer@smug`, `laugh@smug`; BAKE campers: `wave@happy`, `beckon@hopeful`, `beckon@sad`, `sit@sulk`, `sleep`, `shrug@sulk`, `cheer@happy`.
* EXISTS: rocks, bush, fires sprites (`thing_fire`), village far, tempter archetype.

**Effort M, priority P2.**

---

## J03 `jordan.nazareth`: the workshop (map galilee_shore, view `workshop`)

**Situation.** The carpenter's yard. A neighbour comes to ask for help (Capernaum); nets lie on the cart (the lake); the yard gate leads on. Road and cart both lead to Galilee; the neighbour to Capernaum.

| option | hotspot id | anchor today | success | failure | default |
| --- | --- | --- | --- | --- | --- |
| road | `jordan.nazareth.road` (exit) | waypoint `workshop.door_up`, 0 degrees, 11.6 m (empty) | `galilee` | `galilee` + stagger, -5 | yes |
| neighbour | `jordan.nazareth.neighbour` (character `n1`) | +14 degrees, 10.9 m | `galilee.capernaum`, +5 | `galilee`, -4 | no |
| cart | `jordan.nazareth.cart` (object) | thing `workshop.cart`, +31 degrees, 9.6 m | `galilee`, +5 | `galilee.capernaum`, -4 | no |

**Today.** Neighbour pleads only at beat 16 (cast), cart a static sprite, road nothing. Three targets at 0, +14 and +31 degrees are in view, but nothing differs between current and idle.

**Archetype.** A1 (neighbour) with A5 (the cart is being loaded) and a gate for the road.

**Design.**
* Road: a **yard gate** (`workshop.gate`): IDLE both leaves half closed with a rope loop over the post; CUR both leaves swung wide, the track beyond clear.
* Neighbour: at the yard fence, re-homed to +10 degrees / 7 m. IDLE `beckon@sad` half amplitude, hands low. CUR `beckon@hopeful` full amplitude then `sweep_arm@hopeful` toward the right-hand side (south, Capernaum), one pace in, holding a **H1 loaf** wrapped in cloth (a gift for the sick). TOUCH: the face lights within one beat. RELEASE: back to `beckon@sad`.
* Cart: **P-donkey** hitched. IDLE (`cart_idle`): shafts propped on a stool, nets spilling, no donkey (`donkey_idle` stands unhitched beside it, head down). CUR (`cart_cur`): nets lashed, shafts level, `donkey_cur` between them, ears forward, the carpenter `c1` at -15 degrees `nod@happy` tightening a strap (instead of `write`).
* Carpenter `c1` `look_at @current` while IDLE; `nod@happy` only if cart or road is CUR; `bow@doubt` toward the neighbour if the neighbour is CUR (he sees the need).
* Commit OK neighbour: `n1` `cheer@happy`, bows; `c1` `bow`; FAIL: `n1` `turn_away@sulk`, loaf lowered. Cart OK: the donkey steps off, `c1` `wave@happy`; FAIL: the strap slips, nets fall, `c1` `shrug@sulk`. Road OK: gate wide, `c1` `nod`; FAIL: the gate swings back (stagger beat).
* Cast conflict: `n1` plead at beat 16 and `c1` write/nod are replaced by state poses; `v1_workshop` `watch` (beat 48) is replaced by `look_at @current`.

**Placement and camera.** Gate at 0 degrees / 9 m (the existing door_up waypoint moves into the gate opening), neighbour +10 degrees, cart +31 degrees (ok, the right edge of view). All reachable inside the window glance (8 degrees).

**Create.**
* NEW prop `gate` 112 x 80, 2 state frames (`idle` half shut, `cur` wide), workshop.
* NEW prop `cart` 128 x 96 (the canvas of `thing_cart`), 2 state frames (`idle` propped, `cur` lashed and hitched), replaces `thing_cart`.
* NEW prop `donkey` (shared P-donkey `donkey_idle|_cur`).
* NEW face `hopeful` F1, `sulk` F3; NEW act `sweep_arm` A1; NEW held `loaf` H1; NEW act `shrug` A5.
* BAKE `n1`: `beckon@sad`, `beckon@hopeful`, `sweep_arm@hopeful`, `cheer@happy`, `turn_away@sulk`; BAKE `c1`: `nod@happy`, `bow@doubt`, `wave@happy`, `shrug@sulk`.
* EXISTS: bench, planks, house, olive, jars.

**Effort M, priority P2.**

---

## J04 `galilee`: calling the fishermen (map hillside, view `lakeshore`)

**Situation.** Dawn work on the shore. Choice: call the brothers at their nets, send the boat out on the lake, or take the shore track up to the hillside.

| option | hotspot id | anchor today | success | failure | default |
| --- | --- | --- | --- | --- | --- |
| hillside track | `galilee.mount` (exit) | waypoint `lakeshore.door_up`, 0 degrees, 11.2 m (empty) | `galilee.mount` | `galilee.mount` + stagger, -5 | yes |
| fishermen | `galilee.fishermen` (character `f1_lakeshore`) | -29 degrees, 5.3 m; flag `gospel_called`, +8 | `galilee.mount` | `galilee.storm`, -4 | no |
| boat | `galilee.boat` (object) | thing `lakeshore.boat_far`, +16 degrees, 11 m (1.0 m sprite, 35 px) | `galilee.storm`, +5 | `galilee.mount`, -4 | no |

**Today.** The brothers are readable (close, `stare`) but look the same touched or not; the boat is a speck; the road is bare floor. Fail routes are a surprise (the fishermen's failure sends you to a storm) with nothing to foreshadow it.

**Archetype.** A5 work in progress: each option's work is visibly *paused* (CUR) or *continuing* (IDLE).

**Design.**
* Fishermen IDLE: `f1_lakeshore`, `f2` mending the net, backs three-quarter to the camera, `beckon@sad` over the shoulder at half amplitude, net taut on its poles (`nets1`, existing). CUR: they drop the net (**H5** falls, `nets_dropped` shows the net slumped in the shallows), face the camera, `reach@hopeful` and `nod@hopeful`, one pace in; `f3`,`f4` `look_at @current`, stop working.
* Boat: the moored boat (**P-boat**) re-placed at +34 degrees / 6.5 m beside a small jetty of poles, with a boatman `bt1` (fisher). IDLE: sail furled, the boatman `sit@sulk` with an oar across his knees. CUR: sail raised and full, the boatman stands, `wave@hopeful` high over his head, the boat's rope slack (cast off). TOUCH: the sail runs up within the first beat.
* Hillside track (default, CUR from beat 0): a **child** `k1_lakeshore` re-homed to the track mouth (+8 degrees / 6 m) with a pair of **stone steps** and a shepherd's cairn marking the track (`track_steps` static). CUR: `k1` `wave@happy` and runs two paces up the track; IDLE: `k1` `sit@sulk` at the track mouth skimming a stone, `beckon@sad` once per 8 beats.
* RELEASE for the previously current: net rehung and the brothers return to work; sail furls over 2 beats.
* Commit fishermen OK: nets dropped, `f1`,`f2`,`f4` `cheer@happy` then `walk` toward and behind the camera (existing cast beat 61 `cheer`); FAIL (storm): `f1` `shake_head@doubt`, back to the net, the distant sky (the `hillside` sky) darkens one step. Boat OK: sail fills, boatman `cheer@happy`, the sky edge darkens (foreshadows the storm); FAIL: sail drops, `shrug@sulk`. Track OK: `k1` runs up the track; FAIL: `k1` trips (stagger).
* Cast conflict: `f1_lakeshore` and `f2` `stare@neutral`/`awe` cast (beats 0 to 48) and the `f2`,`f4` cheer at beat 61 stay only where they match the state; remove the unconditional stare lines.

**Placement and camera.** Fishermen -29 degrees / 5.3 m (good), track 0 / +8 degrees, boat +34 degrees: all inside +-40 degrees. The 1.0 m `boat_far` sprite is retired.

**Create.**
* NEW prop `boat_moored` (shared P-boat) 96 x 64, 2 state frames, lakeshore + slope.
* NEW prop `jetty` 64 x 24, 1 frame, lakeshore.
* NEW prop `nets_dropped` 96 x 48, 1 frame (net slumped in the shallows), lakeshore (shown while the fishermen option is CUR or OK).
* NEW prop `track_steps` 96 x 64, 1 frame, lakeshore.
* NEW actor `bt1` (fisher) in the boat; re-home `k1_lakeshore`.
* NEW act `reach` A3, `turn_away` A2 (after commit), NEW face `hopeful` F1, `sulk` F3, NEW held `net` H5, NEW act `shrug` A5.
* BAKE `f1_lakeshore`,`f2`: `beckon@sad`, `reach@hopeful`, `nod@hopeful`, `cheer@happy`, `shake_head@doubt`, `check@doubt`, `turn_away@sulk`; `bt1`: `sit@sulk`, `wave@hopeful`, `cheer@happy`, `shrug@sulk`; `k1_lakeshore`: `sit@sulk`, `wave@happy`, `beckon@sad`.
* EXISTS: boats, nets, rack, palm, waves.

**Effort L, priority P1.**

---

## J05 `galilee.capernaum`: the sick child (map hillside, view `street`)

**Situation.** A Capernaum street. Parents plead beside a child on a mat; a caravan is leaving south; the street runs up toward the hillside. The emotional centre of the first half.

| option | hotspot id | anchor today | success | failure | default |
| --- | --- | --- | --- | --- | --- |
| road to the hill | `galilee.capernaum.mount` (exit) | waypoint `street.door_up`, 0 degrees, 11.2 m | `galilee.mount` | `galilee.mount` + stagger, -5 | yes |
| family | `galilee.capernaum.family` (character `p2`) | -4 degrees, 6.4 m; flag `gospel_healed`, +10 | `galilee.mount` | `galilee.mount` + `gospel.led_out`, -8 | no |
| caravan | `galilee.capernaum.caravan` (exit) | thing `street.caravan`, +4 degrees, 12.8 m | `road` | `road` + stagger, -5 | no |

**Today.** Family (-4 degrees, 6.4 m) and caravan (+4 degrees, 12.8 m) sit on the same line of sight, so the caravan is partly hidden by the family and the nearest-centre rule is a coin toss. The family's `available`, `committed` and `failure` panels are nearly identical (see `docs/shots/acting/gospel_galilee_capernaum_family.jpg`).

**Archetype.** A1 (the owner's literal model: the family beckons happily when current, still beckons but sad otherwise), with A5 for the caravan.

**Design.**
* Family IDLE: `p1` (mother) kneeling by the mat `plead@plea` hands together, `p2` (father) standing `beckon@sad` small gesture; the child `k1_street` `lie` facing the wall (back to the camera); the elder `e1` (+23 degrees) `shake_head@doubt` arms folded. CUR: `p2` `beckon@hopeful` full arm then `reach@hopeful`, one pace out of the doorway; `p1` looks up to the camera, `reach@hopeful` with the child's hand in hers; the child turns its head to the camera (`lie@plea`); `e1` `look_at p2`, arms drop.
* Caravan: moved to a side lane at +36 degrees / 10 m with a driver `dr1` (merchant archetype). IDLE (`caravan_idle`): donkeys kneeling, loads off, the driver `sit@sulk`. CUR (`caravan_cur`): donkeys standing in line, loaded, lead rope taut, a puff of dust, the driver `wave@happy` and `beckon@hopeful`.
* Road (default): the street continues to a **flight of stone steps** at 0 degrees (`street_steps`, 96 x 64) with three pilgrims `v1`,`v2`,`v3` (re-homed in a loose line on the steps) walking up. IDLE: they stand `chat`; CUR: `v3` `beckon@happy`, the others `walk` (back facing) two paces up and `look_at` the steps.
* TOUCH: faces change within one beat; bystanders `look_at @current`.
* Commit family OK: the child sits up (existing `gospel_healed` cast: `k1_street` `sit@happy`), `p1` `collapse@relief` then `cheer@happy`, `p2` `bow@relief`. FAIL: the elder steps in front of the camera `shake_head@doubt` and leads it away (`gospel.led_out`), `p1` `cover_face@grief`, `p2` `turn_away@grief`, the child stays lying with its back turned. Caravan OK: the donkeys walk on, `dr1` `cheer@happy`; FAIL: a donkey balks (stagger), `dr1` `shrug@sulk`. Road OK: the pilgrims walk up; FAIL: the camera trips on the first step.
* Cast conflict: `p1` and `p2` plead lines at beats 0, 32 and the `e1` line at beat 48 are replaced by the poses above; `p1` `collapse@relief` at 61 stays.

**Placement and camera.** Family -4 degrees left unchanged but the caravan leaves the line of sight (+36 degrees); steps at 0 degrees / 11 m. All within +-40 degrees. Hit target sizes: family 6.4 m (large), caravan 10 m (wide sprite 224 px, fine).

**Create.**
* NEW prop `caravan` 224 x 96, 2 state frames (`idle` kneeling, `cur` standing and loaded, dust loop), street (replaces `thing_caravan`).
* NEW prop `street_steps` 96 x 64, 1 frame, street.
* NEW actor `dr1` (merchant archetype), re-home `v1`,`v2`,`v3`.
* NEW face `hopeful` F1, `sulk` F3; NEW act `reach` A3, `turn_away` A2.
* BAKE `p1`: `plead@plea`, `reach@hopeful`, `collapse@relief`, `cheer@happy`, `cover_face@grief`; `p2`: `beckon@sad`, `beckon@hopeful`, `reach@hopeful`, `bow@relief`, `turn_away@grief`; `k1_street`: `lie@plea`, `lie` (back), `sit@happy`; `e1`: `shake_head@doubt`, `stare@neutral`; `dr1`: `sit@sulk`, `wave@happy`, `beckon@hopeful`, `cheer@happy`, `shrug@sulk`; `v1`..`v3`: `chat`, `beckon@happy`, `walk` (back).
* EXISTS: houses, caravan sprite (to be replaced), jars, mat, bench, `led_out` cinematic.

**Effort L, priority P1.**

---

## J06 `galilee.mount`: the sermon (map hillside, view `slope`)

**Situation.** A seated crowd on the slope, disciples standing, a boat on the lake. Choice: stay with the crowd (then on to the loaves), the boat to the lake (storm), or the hill crest on.

| option | hotspot id | anchor today | success | failure | default |
| --- | --- | --- | --- | --- | --- |
| hill crest | `galilee.mount.loaves` (exit) | waypoint `slope.door_up`, 0 degrees, 11.2 m | `road.loaves` | `road.loaves` + stagger, -5 | yes |
| crowd | `galilee.mount.crowd` (feature, actor `c4`) | +3 degrees, 7 m; flag `gospel_mount_heard`, +8 | `road.loaves` | `galilee.storm`, -4 | no |
| boat | `galilee.mount.boat` (object) | thing `slope.boat_far`, +20 degrees, 11.7 m | `galilee.storm`, +5 | `road.loaves`, -4 | no |

**Today.** Crowd and crest share the centre line; the boat is a 35 px speck; the three seated people who matter are lost among eight. `d02_slope` points at the boat at beat 48 whatever is touched.

**Archetype.** A4 (the crowd leans) with A5 (the boat) and the disciples as the three "pulls".

**Design.**
* Crowd IDLE: seated `sit@neutral`, a few turned to look at the lake; `c4` `beckon@sad` at half amplitude from the front row. CUR: everyone `sit@hopeful`, leaning in (a 2 px forward offset), `c4` stands and `beckon@hopeful`, a mother beside him `hold_up` her child to the camera; the heckler `h1` keeps `laugh@smug`.
* Boat: the moored boat (**P-boat**, shared with J04) at +32 degrees / 6 m near the foot of the slope with `bt2`. IDLE: sail furled, boatman `sit@sulk`. CUR: sail raised and full, boatman `wave@hopeful`; the crowd's front row turns heads to the water (they `look_at @current`); `d02_slope`,`d03_slope` (re-homed at +24 and +28 degrees, by the boat) `beckon@hopeful`, `point@resolve` at it.
* Hill crest (default): `d01_slope` at -20 degrees (re-homed) beside a worn path of three flat stones climbing the left of the slope (`crest_path`, static). CUR: `d01` `sweep_arm@happy` toward the crest; IDLE: `d01` `look@neutral`, `beckon@sad`.
* Commit crowd OK: the crowd `cheer@awe` with arms raised, `h1` `cover_face@shame` (existing flag line at beat 61); FAIL: the crowd rises and `shrug@sulk`, drifting toward the shore, `c4` `turn_away`. Boat OK: sail full, the boat pushes off; FAIL: sail slumps, the oar drops. Crest OK: `d01` leads off; FAIL: `d01` stumbles (stagger).
* Cast conflict: `d02_slope` `point@resolve` at the boat (beat 48) only `if_current boat`; crowd `sit@awe` lines are the baseline for CUR/IDLE; `h1` laugh stays.

**Placement and camera.** Crowd 7 m at +3 degrees, crest path -20 degrees, boat +32 degrees; all inside +-35 degrees. Hit target for the crowd is the whole seated group (E3 multi-anchor: `c1`..`c8`).

**Create.**
* NEW prop `boat_moored` (shared P-boat; second placement).
* NEW prop `crest_path` 128 x 48, 1 frame, slope.
* NEW actor `bt2` (fisher, boatman); re-home `d01_slope`,`d02_slope`,`d03_slope`.
* NEW face `hopeful` F1, `sulk` F3; NEW act `sweep_arm` A1, `hold_up` A4, `shrug` A5, `turn_away` A2.
* BAKE crowd `c1`..`c8`: `sit@hopeful`, `sit@neutral`, `cheer@awe`, `shrug@sulk`; `c4`: `beckon@sad`, `beckon@hopeful`, `turn_away@sulk`; mother (`c5`): `hold_up@hopeful`; `d01_slope`: `sweep_arm@happy`, `beckon@sad`, `look@neutral`; `d02_slope`,`d03_slope`: `beckon@hopeful`, `point@resolve`; `bt2`: `sit@sulk`, `wave@hopeful`.
* EXISTS: hill, rocks, flowers, olive, waves.

**Effort M, priority P2.**

---

## J07 `galilee.storm`: the storm on the lake (map hillside, view `storm`)

**Situation.** Night, rain and lightning. The disciples are afraid in the boat. Choice: ride it out in the boat (the way on), run for the southern road, or go to the shore beacon and calm it.

| option | hotspot id | anchor today | success | failure | default |
| --- | --- | --- | --- | --- | --- |
| stay in the boat | `galilee.storm.loaves` (exit) | waypoint `storm.door_up`, 0 degrees, 11.2 m (empty water) | `road.loaves` | `road.loaves` + stagger, -5 | yes |
| southern road | `galilee.storm.south` (exit) | waypoint `storm.door_right`, +32 degrees, 11.6 m | `road` | `road` + stagger, -5 | no |
| beacon | `galilee.storm.beacon` (feature, acting `d03_storm`) | thing `storm.beacon`, **-57 degrees** (off screen), 7.4 m; flag `gospel_calm`; pieces off storm | `road.loaves` | `road`, -6 | no |

**Today.** The beacon is outside the 108 degree horizontal view at the home yaw, and its acting disciple `d03_storm` stands at -2 degrees: touch the fire you cannot see, watch somebody else react. The default is empty water. The shot is dark with six similar disciples.

**Archetype.** A6 (weather and night) with the **boat as a compass**: the one large sprite in the scene points at the current option.

**Design.**
* The boat (`storm.boat`, 0 degrees / 9.4 m) is the default's body (re-anchor: default = [`storm.boat`, `door_up`]) and shows the current option:
  * `boat_ride` (default CUR): bow to the lake, sail reefed to the mast, a lantern steady at the stern, the hull level. Disciples `d01_storm`,`d05` `plead@fear` small; `d03_storm` at the stern `reach@hopeful` toward the camera ("come").
  * `boat_to_beacon` (beacon CUR): hull turned 25 degrees toward the left bank, a rope trailing to the shore, bow lamp towards the beacon.
  * `boat_beached` (south CUR): keel run up on the shingle at the right, the mast leaning, the sail down; the disciples stepping out.
  * In IDLE terms the boat's three poses are the three options; the non-current ones are not drawn.
* Beacon (moved to -34 degrees / 8 m, with `f1_storm` re-homed beside it): IDLE (`beacon_idle`): embers and a low flame, `f1_storm` crouched with a cloak over his head (`cover_face@fear`), `d07` (-31 degrees) `beckon@sad`. CUR (`beacon_cur`): the fire roars with a 2 frame spark loop; `f1_storm` stands, swinging **H6 torch** in arcs, `wave@hopeful`; `d07` `beckon@hopeful`.
* South road (`storm.door_right`, +32 degrees): a **roadside post with a clay lamp** (`roadpost_idle`: lamp blown out, a cloth flapping; `roadpost_cur`: lamp steady) with `d08` (+31 degrees) beside it. IDLE `beckon@sad` pointing left-down; CUR `sweep_arm@hopeful` along the road, two paces forward, face `hopeful`.
* TOUCH: the boat swings to its new pose over one beat (a 2 frame turn), the sound/`rain` unchanged; others `look_at @current`.
* Commit beacon OK: existing: the storm pieces go off on the downbeat, `d03_storm` `stare@relief` then `awe`, `d04_storm` `awe`, the boat rights itself (`boat_ride` calm variant = `boat_calm`, a lit stern lamp). FAIL: `boat_beached`-like wreck at the south shingle, `d03_storm` `collapse@grief`. South OK: the disciples run down the road; FAIL: the lamp goes out, they stumble. Boat OK: the lantern holds, `d01`,`d05` `relief`; FAIL: the boat lurches, `d01` `collapse@fear`.
* Cast conflict: all six disciples' cast (`recoil`, `plead`) are baseline fear for IDLE; the CUR poses override; the beat 61 `d04`/`d02` relief lines stay (they follow `gospel_calm`).

**Placement and camera.** Beacon -57 to -34 degrees / 8 m; `d07` -31 degrees, `d08` +31 degrees stay; the boat stays central. The 8 degree window glance never reveals the beacon at -57 degrees: the move is mandatory.

**Create.**
* NEW prop `boat_state` 192 x 96 (the canvas of `thing_boat`), 4 frames: `ride`, `to_beacon`, `beached`, `calm` (storm view only; replaces `thing_boat`).
* NEW prop `beacon` 64 x 80, 2 state frames (`idle` embers, `cur` big flame with sparks, 2 animation frames), storm.
* NEW prop `roadpost` 24 x 56, 2 state frames (`idle` lamp out, `cur` lamp lit), storm.
* NEW held `torch` H6; NEW face `hopeful` F1, `sulk` F3; NEW act `reach` A3, `sweep_arm` A1.
* BAKE `d03_storm`: `reach@hopeful`, `plead@fear`, `collapse@grief`; `d07`: `beckon@sad`, `beckon@hopeful`; `d08`: `beckon@sad`, `sweep_arm@hopeful`; `f1_storm`: `cover_face@fear`, `wave@hopeful`; `d01_storm`,`d05`: `plead@fear`, `relief`, `collapse@fear`.
* EXISTS: rain, cloud, lightning pieces, waves, rocks, palm.

**Effort L, priority P1.**

---

## J08 `road` Bethany: the shared table (map bethany, view `courtyard`)

**Situation.** A courtyard supper; the sisters offer bread, the traitor `d12` looks away; a donkey waits at the gate.

| option | hotspot id | anchor today | success | failure | default |
| --- | --- | --- | --- | --- | --- |
| courtyard arch | `road.loaves` (exit) | waypoint `courtyard.door_up`, 0 degrees, 11.2 m (behind the table) | `road.loaves` | `road.loaves` + stagger, -5 | yes |
| table | `road.table` (character `s1`) | -7 degrees, 9.3 m; flag `gospel_table`, +8 | `road.loaves` | `road.entry`, -4 | no |
| donkey | `road.donkey` (object) | thing `courtyard.donkey`, **+50 degrees** (edge), 8.4 m | `road.entry`, +5 | `road.loaves`, -4 | no |

**Today.** The exit is hidden behind the table; the donkey is at the very edge; the sisters offer bread throughout (cast) so touching changes nothing.

**Archetype.** A1 (hosts) plus A3 (the donkey points to the gate).

**Design.**
* Table: IDLE (`table_idle`): a cloth and a jug only, stools pushed in; `s1` `offer@sad` half arm with an empty hand, `s2` `write@doubt` (existing). CUR (`table_cur`): bread, cups and a spare stool pulled out facing the camera; `s1` `offer@happy` full arm with **H1 loaf**, `s2` `sweep_arm@happy` to the spare stool; the disciples at the table (`d03`,`d04`) `look_at camera`, `happy`. `d12` `shame` stays as the unease (he looks toward the donkey: `look_at courtyard.donkey`).
* Donkey (moved to +34 degrees / 7 m): **P-donkey**. IDLE: dozing, unloaded. CUR: loaded and saddled, ears forward; `d02_courtyard` (+20 degrees) holds the rope `beckon@hopeful` leaning toward the gate side; IDLE `d02` `sit@sulk` on a stool.
* Arch (default): a **courtyard gate** with two leaves (`courtyard.gate`) at 0 degrees / 11 m, framed above the table. IDLE: leaves ajar, a bar leaning; CUR: leaves wide, the road beyond visible, `d01_courtyard` (-20 degrees) `sweep_arm@happy` toward it.
* TOUCH/RELEASE as in the grammar (`@current` gazes: the sisters look at whichever is current).
* Commit table OK: `s1` `cheer@happy`, the table fills, `d12` `shame` deepens (`cover_face@shame`); FAIL: `s1` `shrug@sulk`, the loaf withdrawn, the table cleared. Donkey OK: the donkey tugs forward, `d02` `cheer`; FAIL: it balks, `d02` `shrug@sulk`. Arch OK: gate wide; FAIL: gate bangs (stagger).
* Cast conflict: `s1` offer (beats 0 and 48), `s2` stare/write, `d12` stare lines: keep `d12`; replace `s1`,`s2` with the state poses.

**Placement and camera.** Table 0 degrees, `s1` -7 degrees; donkey from +50 to +34 degrees (rail change: move `courtyard.donkey` and the `courtyard.door_right` waypoint with it); gate 0 degrees behind the table (raise it 0.4 m so it clears the table's silhouette).

**Create.**
* NEW prop `table` 128 x 72 (the canvas of `thing_table_meal`), 2 state frames (`idle`, `cur`), courtyard (replaces `thing_table_meal`).
* NEW prop `courtyard_gate` 120 x 90, 2 state frames (`idle` ajar, `cur` wide), courtyard.
* NEW prop `donkey` (shared P-donkey).
* NEW face `hopeful` F1, `sulk` F3; NEW act `sweep_arm` A1, `shrug` A5; NEW held `loaf` H1.
* BAKE `s1`: `offer@sad`, `offer@happy`, `cheer@happy`, `shrug@sulk`; `s2`: `sweep_arm@happy`, `write@doubt`; `d02_courtyard`: `beckon@hopeful`, `sit@sulk`, `cheer@happy`; `d01_courtyard`: `sweep_arm@happy`, `look`; `d12`: `cover_face@shame`.
* EXISTS: stools, olive, jars, house.

**Effort M, priority P2.**

---

## J09 `road.loaves`: the hungry crowd (map bethany, view `hill_dusk`)

**Situation.** Dusk on a hillside; a hungry seated crowd; three empty baskets; a traveller with a lantern passes.

| option | hotspot id | anchor today | success | failure | default |
| --- | --- | --- | --- | --- | --- |
| road on | `road.loaves.entry` (exit) | waypoint `hill_dusk.door_up`, 0 degrees, 11.2 m | `road.entry` | `road.entry` + stagger, -5 | yes |
| baskets | `road.loaves.baskets` (object) | thing `hill_dusk.basket2`, 0 degrees, 6.6 m (only the middle basket); flag `gospel_fed`; pieces on `full1`..`full3` | `road.entry`, +9 | `road` (loop to Bethany), flag `gospel_hungry`, -5 | no |
| lantern | `road.loaves.lantern` (character `tr1`) | +34 degrees, 9.7 m | `road`, +4 | `road.entry`, -4 | no |

**Today.** Dusk, dark; the three baskets read as scenery; only basket 2 is a target; the lantern is a light plus a small figure. The failure of the baskets (hungry crowd, loop back) is the biggest branch consequence in this world, and nothing foreshadows it.

**Archetype.** A5 (uncover the baskets) with A1 (the traveller).

**Design.**
* Baskets IDLE: three baskets **tied shut with cloth** (`basket_covered`), the crowd `plead@plea` hands out, a child `c8` `sad`. CUR: the cloths thrown back (`basket_cur`: open, a few loaves and two fish visible), a boy `c3` stands `hold_up` **H1 loaf**, the crowd `plead@hopeful` leaning in. Any of the three baskets answers (E3 multi-anchor).
* Lantern: `tr1` with **H2 lantern**. IDLE: lantern lowered, the traveller `sit@sulk` on the rock, `beckon@sad` once per 8 beats. CUR: lantern raised, he stands `beckon@hopeful`, one pace out, a lit lantern swinging toward the left lane (back to Bethany).
* Road on (default): two pilgrims `d01_hill_dusk`,`d02_hill_dusk` (-8, +9 degrees) at the crest. CUR: both `beckon@happy` toward the crest, a line of three more lamps on the road (static lit frames); IDLE: they sit `sit@neutral` and `look_at @current`.
* TOUCH/RELEASE: cloths flip over in one beat; the lantern raises or drops.
* Commit baskets OK (existing): the full baskets (`full1`..`full3`) appear, `c3` `cheer@happy`, `c6` `laugh`, the crowd `cheer`; FAIL: baskets stay empty, `c4` `shake_head@sad`, `c8` `sad`, the crowd `turn_away@sulk`, drifting. Lantern OK: `tr1` leads off; FAIL: he shrugs (`shrug@sulk`), puts out the lantern. Road OK: the pilgrims lead on; FAIL: they stumble.
* Cast conflict: `c2`,`c5`,`c1`,`c7` plead lines stay as the IDLE baseline; the flag-based beat 61 lines stay.

**Placement and camera.** Baskets 6.6 m, -22/0/+22 degrees; lantern +34 degrees; pilgrims +-9 degrees. All fine. The scene is dark: give CUR persons a 1 px warm rim (E9).

**Create.**
* NEW prop `basket_covered` 32 x 28, 1 frame (3 placements), hill_dusk.
* NEW prop `basket_open` 32 x 28, 1 frame (loaves and fish; 3 placements), hill_dusk.
* NEW prop `crest_lamps` 64 x 32, 1 frame (three small lit lamps on stakes), hill_dusk.
* NEW face `hopeful` F1, `sulk` F3; NEW act `hold_up` A4, `shrug` A5, `turn_away` A2; NEW held `loaf` H1, `lantern` H2.
* BAKE `tr1`: `sit@sulk`, `beckon@sad`, `beckon@hopeful`, `shrug@sulk`; `c3`: `hold_up@hopeful`, `cheer@happy`; crowd `c1`,`c2`,`c4`..`c8`: `plead@plea`, `plead@hopeful`, `turn_away@sulk`; `d01_hill_dusk`,`d02_hill_dusk`: `sit@neutral`, `beckon@happy`.
* EXISTS: `thing_basket`, `thing_basket_full`, lantern, olive, hill.

**Effort M, priority P2.**

---

## J10 `road.entry`: the city gate (map bethany, view `gate`)

**Situation.** Palm-waving crowds at the city gate; priests stand in the way; an olive lane leads off. Choice: enter the city by the Temple steps, or turn aside to the olive grove.

| option | hotspot id | anchor today | success | failure | default |
| --- | --- | --- | --- | --- | --- |
| Temple steps | `road.entry.steps` (exit) | waypoint `gate.door_up`, **-30 degrees**, 10.7 m | `jerusalem` | `jerusalem` + stagger, -5 | yes |
| grove | `road.entry.grove` (exit) | waypoint `gate.door_left`, **-42 degrees**, 9.6 m | `jerusalem.gethsemane` | `jerusalem.gethsemane` + stagger, -5 | no |

**Today.** Both exits are on the left; the great gate (0 degrees, the picture's centre) is neither. The crowd waves and the priests block whatever is touched; the child offers a palm regardless.

**Archetype.** A4 (the crowd's palms) with A2 (gate leaves, a lane gate).

**Design.**
* Move the grove: `gate.door_left` moves to the **right** (+32 degrees / 11 m, where `olive` already stands) so the choice is split left (steps) and right (grove) around the gate; the central gate is then the backdrop of the steps option.
* Steps CUR (default from beat 0): the city gate leaves wide (`gate_open`), the crowd (`cr1`..`cr8`) `wave@cheer` palms (**H4**) toward the gate, the child `k1` `offer@happy` a palm to the camera, `pr1`,`pr2` `block@anger` in the doorway. IDLE: gate leaves half drawn (`gate_half`), palms lowered at half amplitude, the crowd `look_at @current`, `k1` `beckon@sad`.
* Grove: a **lane gate** (`grove_gate`, a wattle hurdle) under the olive at +32 degrees. IDLE: shut with a rope loop, `d01_gate` (a disciple) `sit@sulk` on the wall beside it. CUR: the hurdle swung open, `d01_gate` standing at it, `beckon@hopeful`, one pace out; the crowd's front row turns toward it, palms drooping; `pr1`,`pr2` `stamp@anger` (displeased).
* TOUCH/RELEASE: within one beat; the previously current gate half-closes or the hurdle shuts.
* Commit steps OK: palms thrown down on the road (`cheer@cheer`), `k1` `cheer@happy`; FAIL: palms drop, the gate leaves swing to, `pr1` `stamp@anger`. Grove OK: `d01_gate` leads off, `k1` `wave@sad`; FAIL: the hurdle jams (stagger), `d01_gate` `shrug@sulk`.
* Cast conflict: `pr1`,`pr2` `block` lines (0 and 48), `k1` offer (16), `cr2`,`cr5` cheer lines: reduce to CUR/IDLE as above.

**Placement and camera.** Steps -30 degrees (anchor the hotspot on `thing_stairs` and `gate`, E3), grove +32 degrees. Window glance up to 8 degrees keeps both in view.

**Create.**
* NEW prop `citygate` 256 x 192 (the canvas of `thing_citygate`), 2 state frames (`open`, `half`), gate (replaces `thing_citygate`).
* NEW prop `grove_gate` 56 x 56, 2 state frames (`idle` shut, `cur` open), gate.
* NEW prop `olive_lane` 96 x 80, 1 frame (a track under an olive tree), gate.
* NEW actor `d01_gate` (disciple robe).
* NEW face `hopeful` F1, `sulk` F3; NEW act `shrug` A5; NEW held `palm_frond` H4.
* BAKE `cr1`..`cr8`: `wave@cheer` (with H4), `wave@sad`, `cheer@cheer`; `k1`: `offer@happy`, `beckon@sad`, `cheer@happy`, `wave@sad`; `pr1`,`pr2`: `block@anger`, `stamp@anger`; `d01_gate`: `sit@sulk`, `beckon@hopeful`, `shrug@sulk`.
* EXISTS: palms, stairs, olive, jar, citygate sprite (to be replaced).

**Effort M, priority P2.**

---

## J11 `jerusalem` Temple (map jerusalem, view `temple`)

**Situation.** The temple court: three money-changers' tables, a colonnade, guards. Choice: leave quietly by the garden, overturn the tables, or let the guards come.

| option | hotspot id | anchor today | success | failure | default |
| --- | --- | --- | --- | --- | --- |
| garden | `jerusalem.garden` (exit) | waypoint `temple.door_up`, -29 degrees, 10.7 m | `jerusalem.gethsemane` | `jerusalem.gethsemane` + stagger, -5 | yes |
| tables | `jerusalem.tables` (object) | thing `temple.t2_up` (middle only), 0 degrees, 8.6 m; flag `gospel_tables`; pieces switch the three tables to overturned | `jerusalem.gethsemane`, +6 | `jerusalem.trial` + `gospel.walked_out`, -6 | no |
| guards | `jerusalem.guards` (encounter, actor `g1_temple`) | -9 degrees, 12.2 m (behind the tables) | `jerusalem.trial`, +3 | `jerusalem.gethsemane`, -4 | no |

**Today.** Garden is empty floor at the left; the guards stand behind table 2 on one line of sight (12 m, 40 px); only table 2 answers although there are three. The merchants write and laugh regardless.

**Archetype.** A2 (a veil or curtain drawn or tied back) with A5 (the tables) and A1 (the guards, severe not happy).

**Design.**
* Garden: the colonnade opening at -29 degrees gets a **hanging curtain** (`veil_idle` drawn closed; `veil_cur` tied back, a green fig tree and a bench beyond). A disciple `d09_temple` stands at it (IDLE `beckon@sad`; CUR `beckon@hopeful`, a pace forward).
* Tables: IDLE: merchants `mc1`..`mc3` `write@neutral` / `laugh@smug`, coin stacks steady, a **cage of doves** on each table (`dove_cage`). CUR: the tables tremble (`table_coins_shake`, 2 shake frames), the dove cages rattle, merchants `block@fear` hands flat on their tables, coin jar tipping; priests `pr1`,`pr2` `stamp@anger` and `look_at @current`. All three tables answer (E3).
* Guards: re-home `g1_temple`,`g2_temple` to +30 degrees / 8 m by the `spears` rack. IDLE: spears upright, `stare@neutral`. CUR: `g1` steps forward, spear lowered diagonally, `point@resolve`, face `resolve`, `g2` `block@anger`. They are severe, not friendly (no hopeful face).
* Commit garden OK: the veil swings, doves fly through; FAIL: the veil falls closed (stagger). Tables OK (existing): tables flip to `t*_over`, coins scatter, doves flee, merchants `recoil@fear`, priests `stamp@anger`; FAIL: the guards seize the camera's arm (`walked_out`): `g1` `block`, merchants `laugh@smug`. Guards OK: `g1` leads, `g2` falls in; FAIL: they `shake_head@doubt` and turn back.
* Cast conflict: `mc1`..`mc3` write/laugh and `g1_temple` stare (beat 48) are the IDLE baseline; the beat 61 flag lines stay.

**Placement and camera.** Garden -29 degrees (ok), tables 0 degrees, guards moved to +30 degrees. Camera glance clamp is fine.

**Create.**
* NEW prop `veil` 96 x 120, 2 state frames (`idle` closed, `cur` tied back), temple.
* NEW prop `dove_cage` 24 x 28, 2 animation frames (rattle), temple (3 placements on the tables).
* NEW prop `table_coins_shake` 112 x 72 (the canvas of `thing_table_coins`), 2 frames, temple (CUR frame of the three tables).
* NEW actor `d09_temple` (disciple robe); re-home `g1_temple`,`g2_temple`.
* NEW face `smug` F2, `hopeful` F1, `sulk` F3; NEW act `shrug` A5.
* BAKE `d09_temple`: `beckon@sad`, `beckon@hopeful`; `mc1`..`mc3`: `write@neutral`, `laugh@smug`, `block@fear`, `recoil@fear`; `g1_temple`: `stare@neutral`, `point@resolve`, `shake_head@doubt`; `g2_temple`: `block@anger`, `shake_head@doubt`; `pr1`,`pr2`: `stamp@anger`.
* EXISTS: tables up and over, columns, jar, brazier, spears rack.

**Effort M, priority P2.**

---

## J12 `jerusalem.gethsemane`: the garden at night (map jerusalem, view `grove`)

**Situation.** Olive trees at night; three disciples asleep; the traitor and guards arrive with torches at beat 48. Choice: wait and face it, wake the sleepers, or slip away. Somber: no cheerful faces here.

| option | hotspot id | anchor today | success | failure | default |
| --- | --- | --- | --- | --- | --- |
| face it (toward the torches) | `jerusalem.gethsemane.trial` (exit) | waypoint `grove.door_up`, 0 degrees, 11.2 m (empty dark) | `jerusalem.trial` | `jerusalem.trial` + stagger, -5 | yes |
| wake the sleepers | `jerusalem.gethsemane.sleepers` (character `d10`) | 0 degrees, 7.2 m (same line as the default); +3 | `jerusalem.trial` | `jerusalem.road`, -4 | no |
| the shadowed path | `jerusalem.gethsemane.shadowed` (exit) | waypoint `grove.door_right`, +32 degrees, 11.6 m (where the torches and guards arrive) | `jerusalem.road` | `jerusalem.road` + stagger, -5 | no |

**Today.** Near black with white rim glows; the default and the sleepers share the centre; the arrival of the guards happens on the side of the "escape" path, so the escape path *is* where the danger comes from; the three sleepers and the 3 guards are 12 px.

**Archetype.** A6, posture only: restraint, weariness and distance carry the choice; no gestures of delight.

**Design.**
* Rail change (mandatory): the **shadowed path** moves to the *left* (`grove.door_left`, -32 degrees, a dark lane between `olive1` and `olive3`); the **default (face it)** moves to the torch side (re-anchor `jerusalem.gethsemane.trial` to `grove.door_right`; swap the `exits` keys and `next` dirs in run.json: `up`/`left`). So: left = flee, centre = the sleepers, right = the torches.
* Face it (default CUR): the torches stand on a track at +30 degrees (`torches_cur`, two bright flames); `d12` (the traitor) waits at the track mouth `stare@resolve` toward the camera, `g1_grove`..`g3` at 12 m `block@anger`, spears lowered; the disciples' heads and cloak hoods turn toward the torch side. IDLE: torches small and far (`torches_idle`), `d12` `look` away, the guards not yet visible (group `late`, brought in by cast).
* Sleepers: IDLE (not current): `sleep` with the `Z` marks, cloaks over the heads. CUR: `d10` rolls and `sit@shame`, hand to the forehead, then `reach@shame` toward the camera; `d09` and `d11` `sit@grief` stirring; the Z marks gone. TOUCH: `d10` stirs within one beat (a head lift).
* Shadowed path: IDLE: a wattle **hurdle** (`hurdle_idle`) drawn across the left lane, a cloak hung on it; CUR: the hurdle dragged aside (`hurdle_cur`), the lane open, a bare olive branch swaying (2 frames); no person beckons (the garden is empty on that side): the camera hears only the quiet. `d11` (re-homed at -26 degrees) `look_at @current`, `shame`.
* Commit face it OK: `d12` `bow@shame`, the guards close, `g1_grove` `block@anger`; FAIL: stagger, the torches flare. Sleepers OK: `d10` stands, `d09`,`d11` rise `sit` to `kneel@shame`; FAIL: `d10` falls back asleep (`sleep`), the guards loom. Shadowed OK: the hurdle slides, the lane opens; FAIL: the hurdle drops (stagger), `g3` `stare@neutral` looks the other way.
* Cast conflict: `d11`,`d12`,`g1_grove`,`g2_grove`,`g3` lines at 32 to 56 are story and stay, but `d12` `point` at 56 only if face-it is CUR.
* Two laps: lap 1 shows the sleepers and quiet torches; lap 2 the arrival: both laps still show the current option via the lane, the sleepers' posture and the torches' size.

**Placement and camera.** Left lane -32 degrees, sleepers 0 degrees at 7 m, torches +30 degrees at 12 to 14 m: all within +-35 degrees. Raise ambient light slightly (a moon plane from the existing `lt_moon`): the moon must light the sleepers at 7 m so poses read.

**Create.**
* NEW prop `hurdle` 72 x 48, 2 state frames (`idle` across, `cur` dragged aside), grove.
* NEW prop `torches` 40 x 64, 2 state frames (`idle` small, `cur` two torches, flame loop), grove.
* NEW prop `olive_branch_sway` 48 x 64, 2 animation frames, grove.
* NEW face none needed beyond the existing `shame`, `grief`, `resolve`; NEW act `reach` A3.
* BAKE `d10`: `sleep`, `sit@shame`, `reach@shame`, `kneel@shame`; `d09`,`d11`: `sleep`, `sit@grief`, `kneel@shame`; `d12`: `stare@resolve`, `bow@shame`, `look`; `g1_grove`,`g2_grove`,`g3`: `block@anger`, `stare@neutral`.
* EXISTS: trees, rocks, torch sprites, moon light.

**Effort M, priority P1.**

---

## J13 `jerusalem.trial`: before the governor (map jerusalem, view `praetorium`)

**Situation.** The governor on his dais with a bowl and jug; guards at the passage; a crowd stamping. Choice: take the guarded passage (the road to the hill), or the open side gate (the road beyond).

| option | hotspot id | anchor today | success | failure | default |
| --- | --- | --- | --- | --- | --- |
| guarded passage | `jerusalem.trial.passage` (exit) | waypoint `praetorium.door_up`, -7 degrees, 12.7 m (behind the governor) | `jerusalem.golgotha` | `jerusalem.golgotha` + stagger, -5 | yes |
| open side gate | `jerusalem.trial.gate` (exit) | waypoint `praetorium.door_right`, +34 degrees, 11.5 m | `jerusalem.road` | `jerusalem.road` + stagger, -5 | no |

**Today.** Both exits are bare floor and no actor is attached; the governor at 0 degrees stands between and in front of the first. The crowd stamps and the governor washes (cast) with no relation to the choice.

**Archetype.** A2 (barred vs open) with the governor as the pivot (not an option) and A1 reversed (one guard looks away).

**Design.**
* Move the passage left: an **arch** at -32 degrees (`passage_arch`) with two guards flanking it; the side gate at +34 degrees with `g2_praetorium` and the scribe `sc2` beside it. The governor at 0 degrees is the centre piece, the pivot.
* Passage CUR (default): the guards `g1_praetorium` and a second `g3_praetorium` step into a **lane** (spears angled outward), the arch's **bar lifted** (`passage_arch_cur`, the bar leaning on the wall), the governor turns to the passage and `wash@resolve` (**H8 bowl**), the crowd `stamp@anger` facing it. IDLE: the **crossed spears** and the bar down across the arch (`passage_arch_idle`), the guards `block@anger`.
* Gate CUR: the gate leaf **swung ajar** (`gate_leaf_cur`) and the bar leaning; `g2_praetorium` `turn_away@sulk` (looks at the ceiling: he does not see), `sc2` `sweep_arm@hopeful` toward the gate (a restrained, not joyful, gesture; face `resolve`); the crowd's heads turn toward it, murmuring (`look_at @current`). IDLE: the leaf shut and barred with a rope; `g2` `block@anger`; `sc2` `write@neutral`.
* The woman `w1_praetorium` (-44 degrees) `cover_face@grief` throughout; her gaze when the gate is CUR: `look` toward the gate.
* TOUCH: the bars flip within one beat; the previously current side's bar drops.
* Commit passage OK: the governor `wash@resolve` held, then `offer` the bowl, the crowd `stamp@anger`; the lane closes behind the camera; FAIL: stagger, the spears cross. Gate OK: the leaf opens fully, `sc2` `bow@resolve`; `g2` still looks away; FAIL: the leaf bangs shut (stagger), `g2` `block@anger`.
* Cast conflict: governor lines (write, shake_head, offer) are the story; keep them, but `gov` `wash@resolve` at 32 only if the passage is CUR (else `write@doubt`).

**Placement and camera.** Arch -32 degrees (re-anchor `door_up`, rail waypoint), gate +34 degrees, governor 0 degrees / 11.2 m. The scribes and women all within +-45 degrees.

**Create.**
* NEW prop `passage_arch` 112 x 112, 2 state frames (`idle` bar down with crossed spears, `cur` bar lifted, lane), praetorium.
* NEW prop `gate_leaf` 72 x 96, 2 state frames (`idle` barred with a rope, `cur` ajar), praetorium.
* NEW actor `g3_praetorium` (soldier); re-home `g1_praetorium`,`g2_praetorium`,`sc2`.
* NEW act `wash` A6, `turn_away` A2, `sweep_arm` A1; NEW held `bowl` H8; NEW face `sulk` F3.
* BAKE `gov`: `wash@resolve`, `write@doubt`, `offer@resolve`; `g1_praetorium`,`g3_praetorium`: `block@anger`, `point@resolve`; `g2_praetorium`: `turn_away@sulk`, `block@anger`; `sc2`: `sweep_arm@resolve`, `bow@resolve`, `write@neutral`; `w1_praetorium`: `cover_face@grief`, `look`.
* EXISTS: dais, bowl set, benches, braziers, pillars, spears.

**Effort M, priority P1.**

---

## J14 `jerusalem.golgotha` (map jerusalem, view `hill`), single way

**Situation.** Rails scene, one road (the hill) to the next scene; the staging (sky darkening block by block, a witness kneels on a passed block, a soldier laughs on a missed one) is the rhythm's consequence. The second hotspot has no route.

| option | hotspot id | anchor today | success | failure | default |
| --- | --- | --- | --- | --- | --- |
| the hill | `jerusalem.golgotha.hill` (exit) | waypoint `hill.door_up`, 0 degrees, 10.2 m | `jerusalem.tomb` | `jerusalem.tomb` + stagger, -5 | yes |
| the women | `jerusalem.golgotha.women` (character `w1_hill`) | -33 degrees, 6.7 m; flag `gospel_stayed`, +6 | no route | -3 | no |

**Today.** Not a branch. The women are readable as grieving, but touching them shows only a ring.

**Archetype.** A7, solemn. No beckoning with happy faces and no bright feedback: this is the one scene where "current" is expressed by attention, not invitation.

**Design.**
* The hill (default, always the way on): the path of bare stones up to the crosses; no state change.
* Women IDLE: `w1_hill`,`w2_hill` `cover_face@grief`, `w3_hill` `kneel@grief`, heads down. CUR: `w1_hill` lowers her hands and `reach@grief` toward the camera, `w2_hill` turns her face to it (`stare@grief`), `w3_hill` `kneel@grief` raises her head; one pace in; no smile ever. RELEASE: hands back to the face.
* Commit OK: they take one step closer and `kneel@grief` together; FAIL: `turn_away@grief`.
* Cast conflict: women's cast (`cover_face`/`kneel`) is the IDLE baseline; the staging lines (`x1`..`x3`, `s1`..`s3`) are untouched.

**Placement and camera.** Women -33 degrees / 6.7 m ok. Nothing moves.

**Create.**
* NEW act `reach` A3, `turn_away` A2.
* BAKE `w1_hill`: `reach@grief`, `turn_away@grief`; `w2_hill`: `stare@grief`, `kneel@grief`; `w3_hill`: `kneel@grief`.
* EXISTS: crosses, sky pieces, women, soldiers.

**Effort S, priority P3.**

---

## J15 `jerusalem.tomb` (map jerusalem, view `tomb`), ending: single way out

**Situation.** Ending `tomb`: both hotspots lead back to the Warehouse (`run:warehouse`, flag `keep:path_gospel_tomb`); the difference is only energy.

| option | hotspot id | anchor today | success | failure | default |
| --- | --- | --- | --- | --- | --- |
| the garden way | `jerusalem.tomb.home` (exit) | waypoint `tomb.door_up`, 0 degrees, 8.0 m | `run:warehouse`, flag | same, -3 | yes |
| the rolled stone | `jerusalem.tomb.stone` (feature, actor `gd1`) | thing `tomb.stone_rolled`, +13 degrees, 10.3 m | `run:warehouse`, +8 | same, -3 | no |

**Today.** The stone rolls at block 0 and the women go through grief, fear, awe, cheer; the gardener points at the way (beat 48). The touch is a ring on a stone.

**Archetype.** A7 ending: the second touch is a flavour look.

**Design.**
* The garden way (default): a path through the cypresses to the dawn; the gardener `gd1` `point@resolve` along it (existing, at beat 48); IDLE only `look`.
* The stone CUR: `w1_tomb`,`w2_tomb` kneel at the mouth `kneel@awe`, and the tomb's interior shows **folded linen cloths** (`tomb_linen`, a piece, 1 frame); `gd1` `bow@awe`. IDLE: the women `stare@grief` from the path, the mouth dark.
* Commit OK: the women `cheer@happy`, `gd1` `sweep_arm@happy` toward the way; FAIL: `gd1` `shrug@sulk`; the route is the same.
* Cast conflict: the existing grief, fear, awe, cheer script for `w1_tomb`..`w3_tomb` stays; CUR only adds the kneel/linen.

**Placement and camera.** Stone +13 degrees, door 0 degrees: fine.

**Create.**
* NEW prop `tomb_linen` 32 x 24, 1 frame (folded cloth in the doorway of `thing_tomb`), tomb.
* NEW act `sweep_arm` A1, `shrug` A5; NEW face `sulk` F3.
* BAKE `gd1`: `bow@awe`, `sweep_arm@happy`, `shrug@sulk`; `w1_tomb`,`w2_tomb`: `kneel@awe`.
* EXISTS: tomb, stone pieces, cypress, flowers.

**Effort S, priority P3.**

---

## J16 `jerusalem.road` (map jerusalem, view `road`), ending: single way out

**Situation.** Ending `road`: both hotspots lead back to the Warehouse (flag `keep:path_gospel_road`); the followers touch is a flavour touch (flag `gospel_followed`, +6).

| option | hotspot id | anchor today | success | failure | default |
| --- | --- | --- | --- | --- | --- |
| the road | `jerusalem.road.home` (exit) | waypoint `road.door_up`, 0 degrees, 11.0 m | `run:warehouse`, flag | same, -3 | yes |
| the followers | `jerusalem.road.followers` (character `d02`) | +18 degrees, 5.1 m | no route; flag `gospel_followed`, +6 | -3 | no |

**Today.** Two followers walk with the camera and laugh; touching `d02` changes nothing visible.

**Archetype.** A7 ending: companions.

**Design.**
* The road (default): a long white road to the morning haze; sheep and cart beside it. No state needed.
* Followers IDLE: `d01` `sit@neutral` on the low wall, `d02` `beckon@sad` small. CUR: both stand, `d02` `beckon@hopeful`, `d01` `wave@happy`, one pace toward the camera, then `walk` beside it (the `walk` loop starts). RELEASE: back to the wall.
* Commit OK: they fall into step either side of the camera, `d02` `laugh@happy`; FAIL: `d02` `shrug@sulk`, the shepherd `sp1` `bow@awe` (cast, kept). The guards `g1_road`,`g2_road` `shake_head@doubt` stay.
* Payoff: the J00 shepherd flag `gospel_shepherds` makes `sp1` `bow@awe` use `H3 crook` (P3).

**Placement and camera.** Followers +18 degrees / 5 m, road 0 degrees: fine.

**Create.**
* NEW face `hopeful` F1, `sulk` F3.
* BAKE `d02`: `beckon@sad`, `beckon@hopeful`, `laugh@happy`, `shrug@sulk`; `d01`: `sit@neutral`, `wave@happy`.
* EXISTS: city far, olive, cart, sheep, wall.

**Effort S, priority P3.**

---

## New assets and expressions (roll-up)

Coverage verified by script against `content/paths/gospel/hotspots/*.json` and `run.json`: **17 of 17 scenes, 43 of 43 hotspot ids** each appear as an option row in their scene's section (J00 2, J01 2, J02 2, J03 3, J04 3, J05 3, J06 3, J07 3, J08 3, J09 3, J10 2, J11 3, J12 3, J13 2, J14 2, J15 2, J16 2).

| kind | count | detail |
| --- | --- | --- |
| new props (sprites) | **38** (36 scene-specific + 2 shared) | **65 state frames** in all (idle / cur / ok variants; looped animation sits inside a frame's own strip) |
| shared props | 2 (counted above) | `boat_moored_idle|_cur` (J04, J06), `donkey_idle|_cur` (J03, J08) |
| new actors (homes) | **8** | `camper1`, `camper2` (J02), `bt1` (J04), `bt2` (J06), `dr1` (J05), `d01_gate` (J10), `d09_temple` (J11), `g3_praetorium` (J13); plus about 14 re-homed existing actors (E6) |
| new wardrobe archetypes | 0 | all people are `fisher`, `villager`, `disciple`, `merchant`, `soldier`, `child`, `elder` of `wardrobe.gospel()` |
| new faces | **3** | `hopeful`, `smug`, `sulk` (definitions in the Shared kit) |
| new acts | **6** | `sweep_arm`, `turn_away`, `reach`, `hold_up`, `shrug`, `wash` |
| new held props | **8** | `loaf`, `lantern`, `crook`, `palm_frond`, `net`, `torch`, `lamb`, `bowl` |
| bake requests | about **69** distinct `act@face` combinations named in the entries | some already exist in the sheets (`kneel@awe`, `bow@awe`, `point@resolve`, `cover_face@grief`...); baked per named actor by `directed.py`, no crowd-wide bakes |
| existing acts and faces reused | 15 acts, 14 faces | the owner's wizard model (gesturing, happy vs sad) is done with `beckon@hopeful` vs `beckon@sad`, no new act needed |

Effort by scene: S = J00, J14, J15, J16 (4); M = J01, J02, J03, J06, J08, J09, J10, J11, J12, J13 (10); L = J04, J05, J07 (3). Build order: the shared kit first (3 faces, 6 acts, 8 held, `boat_moored`, `donkey`), then the P1 scenes J01, J04, J05, J07, J12, J13, then P2 (J00, J02, J03, J06, J08, J09, J10, J11), then P3 (J14, J15, J16).

## Cross-cutting issues

**E1. Option states on people.** The acting block needs persistent `current` and `idle` poses besides `available`/`selected`/`committed`/`success`/`failure`, plus `touched` (the one-beat reaction) and `released` (the drop when another option is touched). Today `selected` is a one-beat flash; here CUR is a held pose that lasts until the commit, and pose changes begin within one beat of the touch (0.48 s).

**E2. Option states on props.** A hotspot (or its map things) needs `states`: which pieces are on in `idle`, `cur`, `ok`, `fail`. The convention `<view>.<name>_idle|_cur|_ok|_fail` is enough: the engine swaps the matching piece. Instant swap is acceptable (looped frames inside a sprite carry the motion); only the dove (J01) and the boat (J07) need a 2-beat travel between two anchors.

**E3. Multi-anchor hotspots.** A hotspot must accept several anchors as one target: J01 (wilderness: `b1`, `dove_air`, `dove_perch`, `wild_track`; Nazareth: `town`, `post`, `cart_track`), J06 (crowd `c1`..`c8`), J07 (default = `storm.boat` + `door_up`), J09 (baskets 1 to 3), J10 (steps: `gate`, `stairs`, `door_up`), J11 (the three tables `t1_up`..`t3_up`; today only table 2 answers). Without it, the bigger and more readable the object, the less of it can be tapped.

**E4. `look_at: "@current"`.** Bystanders' heads follow the current option's anchor (used in J01, J03, J05, J06, J08, J09, J10, J11, J13): one data word, no per-scene authoring.

**E5. Cast conflicts.** Unconditional `cast` lines of an option's own actors overwrite CUR/IDLE poses (`t1` J02; `n1`,`c1` J03; `f1_lakeshore`,`f2` J04; `p1`,`p2`,`e1` J05; `d02_slope` J06; the six disciples J07; `s1`,`s2` J08; `pr1`,`pr2`,`k1` J10; `mc1`..`mc3`,`g1_temple` J11; `d12` J12; `gov` J13). State poses must take precedence over cast lines for those actors, or those lines gain `if_current` / `if_idle` conditions. Story lines for non-option actors stay as they are.

**E6. Rail and placement changes (map JSON `homes`, `things`, `waypoints`; run.json `rail.exits` and `next` dirs).**
* J01: add `bank_dawn.wild_track` (-28 degrees / 9 m) and `post` (+20 / 6 m); re-home `v1_bank_dawn` (+18 / 5.5), `v5` (+26 / 6), `v3` (-24 / 5).
* J02: move `rocks.fires`, `rocks.fires2` to -30 degrees / 8 m (a camp); cairns in the gap at 0 degrees; `t1` to +14 degrees.
* J03: `n1` to +10 degrees / 7 m; `workshop.door_up` into the gate opening at 0 degrees / 9 m.
* J04: `k1_lakeshore` to +8 degrees / 6 m; the moored boat at +34 / 6.5 m replaces `boat_far`.
* J05: caravan from +4 degrees / 12.8 m to a side lane at +36 / 10 m; `v1`,`v2`,`v3` onto the steps at 0 degrees / 11 m.
* J06: boat to +32 degrees / 6 m; `d01_slope` to -20; `d02_slope`,`d03_slope` to +24, +28.
* J07: beacon from -57 to -34 degrees / 8 m (mandatory: it is off screen today); `f1_storm` beside it.
* J08: donkey from +50 to +34 degrees / 7 m with the `courtyard.door_right` waypoint; gate raised 0.4 m behind the table.
* J10: `gate.door_left` moves to the right (+32 degrees / 11 m); rename to `door_right` in `rail.exits`, `next` and the hotspot anchor.
* J11: `g1_temple`,`g2_temple` to +30 degrees / 8 m.
* J12: swap the two exits: `shadowed` to `grove.door_left` (-32 degrees), default `trial` to `grove.door_right` (+30 degrees, the torch side); `rail.exits` and `next` dirs `up`/`left`; update `check_hotspots.py` expectations.
* J13: passage arch at -32 degrees (the `door_up` waypoint moves, `rail.exits` kept), gate +34 degrees; `g1_praetorium`,`g2_praetorium`,`sc2` re-homed.
* J00, J09, J14, J15, J16: no moves.
The route window clamps the head's glance to 8 degrees (`WINDOW_GLANCE_DEG` in `src/run/run_rail.gd`) and the stage shows about +-54 degrees, so every option above lies within +-40 degrees of the home yaw: nothing relies on the player turning.

**E7. Default exits are empty floor.** In 16 of 17 scenes the default's `door_up` waypoint is bare ground (J10's is the stairs, but off to the left). Each default must be a physical thing the player can see and learn is the current: a gate (J03, J08, J10), a track with steps (J04, J05, J06), the boat (J07), the bar and arch (J13), the torch track (J12), the road (J00, J09, J14, J16). This is the most frequent change in the document.

**E8. Failure that matches success.** Every exit sends success and failure to the same scene and differs only by a `stagger` cinematic and -5 energy (J00 road, J01 town, J02 both, J03 road, J04 track, J05 track, J06 crest, J07 default and south, J08 arch, J09 road, J10 both, J11 garden, J12 trial and shadowed, J13 both). They need a distinct, readable failure beat: the thing the player chose falters (gate bangs, hurdle drops, child trips) and the option's people react flat (`shrug@sulk`), before the stagger. These are `fail` frames of the state sets, not new routes.

**E9. Dark scenes (J00, J07, J09, J12).** The CUR person gets a 1 px warm rim in the people shader (not a colour change of the sprite), and CUR props must change shape (open, lifted, lit), never only brightness. J12 needs the moon light to cover the sleepers at 7 m.

**E10. No-route options (J00 shepherd, J14 women, J16 followers) and equal-route options (J15 both).** When such an option is CUR at the commit, the default exit is taken and the option's outcome plays as a short beat before the door walk (energy and flag only). Visually they are companions: the person walks with the camera (J00, J16) or kneels closer (J14).

**E11. Sheet budget.** About 69 `act@face` combinations at 2 to 3 facings and 3 to 5 frames each come to roughly 500 frames across the four maps (the `hillside` sheet already holds 25,353); the six new acts are the expensive part (`StoryCharacter` needs the three new faces and six acts registered, `HotspotContract.FACES`/`ACTS` follow), so bake only for the named actors, as `directed.py` already does.

**E12. Shared authoring recipes.** The open/shut assets (yard gate J03, courtyard gate J08, city gate and lane gate J10, curtain J11, arch bar and gate leaf J13, hurdle J12) share one recipe, a two-frame leaf set: build one generator in `gospel_things_c.py` and parametrise it. The two boat states (J04, J06) and the donkey (J03, J08) are built once.

**E13. Two laps.** All option states are state-driven. J12's arrival at beat 48 and J14/J15's staging (`block_fx`) are scene-timed: lap 1 should show the quiet version (guards not yet in), lap 2 the arrival, but both laps show CUR in the same way. Insistence in lap 2 (faster loops, one pace in) is an animation parameter, not new art.

**E14. Lint.** `check_hotspots.py --path gospel` should warn when a scene of 2+ options lacks a CUR and an IDLE state for any option (acting pose or state piece), and when an option's anchor is a bare waypoint (E7).

**E15. Tone.** Gospel scenes are handled with restraint: `smug` only for the tempter, money-changers and guards; no `hopeful` or `happy` faces in J12 to J14; no armed forces' emblems; the hero is never drawn; nothing depicts a published work. The teaching order is J00 (touch a person, the person answers), then J01 (the dove moves), then every later scene reuses the same grammar.
