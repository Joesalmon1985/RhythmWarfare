# Choice briefs: the Hospital, Hospital late, Ward and Ward late (174 BPM main run)

Scope: `content/run/hotspots/{hospital,hospital_late,ward,ward_late}.json` and their scenes in `content/run/run.json`. Documents only; nothing here is built.
Owner's verdict this answers: every branching point must be readable in the world (people, doors, objects), the default must be clear, the player must see how pressing changes it, and it cannot be "things of light".

**Coverage check** (run from the repo root; counts scenes with 2 or more hotspots in the four files):

```
python -c "import json,collections;n=t=0
for f in ['hospital','hospital_late','ward','ward_late']:
  c=collections.Counter(h['scene'] for h in json.load(open('content/run/hotspots/%s.json'%f))['hotspots'])
  for s,k in c.items():
    if k>=2: n+=1;t+=k
print(n,t)"
=> 20 69        (20 branching scenes, 69 hotspots; every scene in the four files has 2+; all 20 are in the table below)
```

By file: hospital 6 scenes / 20 hotspots, hospital_late 4 / 16, ward 6 / 20, ward_late 4 / 13. At most 4 are available at once (`hospital_late.lamp`/`lamp_lit`, `.vending`/`vending_token`, `.mic`/`mic_encore` are the same object in two states; `hospital.corridor.quiet_door`, `hospital.cafeteria.vending` are once-only secrets; `ward.corridor.mural_door` needs `wd_painted`).

## 0. How to read the data, and what "the choice" is in these worlds

* Every scene has one **exit** (the default, always an exit) and, in 8 of the 20 scenes (`hospital.corridor`, `hospital.exit`, `hospital_late`, `hospital_late.exit`, `ward`, `ward.exit`, `ward_late`, `ward_late.exit`), a **second exit** (a true fork, 2 destinations). The other hotspots are **side options** (a person, an object or a feature): on success they give energy and a cinematic, on failure a setback, and **the route stays the default**. So the choice is always one of: *which way on* (fork), or *go on* versus *stop and do X first* (side option). A failed exit goes through the same door, staggering (`stagger_*` cinematics, -5): the destination never changes on failure, only the manner of arrival.
* Exactly one option is CURRENT at any time; it starts as the default exit when the window opens (beat 48) and a touch makes another current within one beat (345 ms at 174 BPM, so every visual change below is a 2 to 4 frame snap, never a slow tween).
* Acting phases map straight onto the existing contract: `available` = NOT CURRENT, `selected` = CURRENT (including the default at beat 48, which needs no touch), `committed`, `success`, `failure`. Things (not people) have no acting block today: see engine needs in section 5.

### Today, in one paragraph (blunt)
The route window lights hotspots as a ring of light at the anchor, or as a dim ring at the screen edge when the anchor is out of sight (`HotspotView`). Nothing in these worlds is a visible door, sign, prop or gesture. Measured from the waypoints (script, bearings from the rail place the camera holds in the window under good play, 0 = dead ahead, FOV_V 52 so about +-40 to +-50 degrees is in frame; the side lanes of the note pads cover the outer ~170 px each side of the 1280 px frame): **in 15 of the 20 scenes at least half of the options are out of frame (behind, or more than about 50 degrees off the heading) in the window under good play** (e.g. `hospital`: standing in the doorway, nurse/family/monitor 122 to 142 degrees behind; `hospital.dayroom`: 2 m from the TV, blurred to a blue slab, door and granny behind; `ward.dorm`, `hospital_late.quiet`, `hospital_late.cafe`, `ward.exit`: options behind), and **the two doors of a fork are 1.8 m apart on the same wall** in `ward` and `ward_late.exit` (`day_door_a` 6.3,6.8 and `day_door_b` 6.3,5.0) and 4 m apart in `hospital_late`. The people already have acting (`tools/run/acting_data.py`: 16 character hotspots, 5 states each, `docs/shots/acting/`), but they are one of ten dancers in a crowd and the frame never says "this one is a choice". The five-state acting reads in the close-up strips and not at all in the live shots (`docs/shots/run/contact_hotspots_*.jpg`).

## 1. Summary table

Archetypes (defined in section 2): **A** door held open by an usher (route rule) / **B** pointer device (finger-post, baton, follow-spot) / **C** lever or switch / **D** thing that comes to you or leaves (trolley, wheelchair) / **E** prop offered in the hand / **F** light state / **G** screen or dial / **H** hush (dorm, quiet room) / **P** person grammar (beckon, happy or sulk).
Verdict today: **Invisible** = no object or person identifiable; **Edge beacon** = out of view, a dim ring at the screen edge; **Ring only** = in view but only a ring of light; **Mixed** = some in view.

| # | scene | options (default first) | verdict today | archetypes | effort | prio |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `hospital` | exit_corridor, nurse, family, monitor | Edge beacon (3 of 4 behind), exit under the feet | A, D, P, G | L | P1 |
| 2 | `hospital.corridor` | exit_dayroom, exit_cafeteria, trolley, quiet_door (secret) | Mixed: dayroom door behind, cafeteria 24 m away, ring only | A, B, D, F | L | P1 |
| 3 | `hospital.dayroom` | exit_garden, tv, granny | Invisible: TV a blur, door and granny behind | A, G, P | M | P2 |
| 4 | `hospital.cafeteria` | exit_garden, vending (secret), kid | Edge beacon: looks out of a window, vending and kid sideways/behind | A, G, P | M | P2 |
| 5 | `hospital.garden` | exit_exit, lamp, mum | Ring only: lamp 14 m, mum 10 m at 49 degrees | A, F, P | M | P2 |
| 6 | `hospital.exit` | exit_hospital_late, exit_ward_late, mic | Mixed: left door 3 m ahead, right door (65 degrees) and mic (88 degrees) are edge beacons | A, B, P | L | P1 |
| 7 | `hospital_late` | exit_cafe, exit_quiet, lamp / lamp_lit, doctor | Mixed: all in front but doors 4 m apart, ring only | A, F, P | L | P1 |
| 8 | `hospital_late.cafe` | exit_exit, vending / vending_token, kid | Edge beacon: faces the exit, machine and kid behind | A, G, P | S | P3 |
| 9 | `hospital_late.quiet` | exit_exit, nightlight, nightlight_b | Edge beacon: faces the far wall (a window blur), door behind | A, F, H | M | P3 |
| 10 | `hospital_late.exit` | exit_hospital_late, exit_ward_late, mic / mic_encore | Mixed (as scene 6) | A, B, P | S (reuses 6) | P1 |
| 11 | `ward` | exit_art, exit_dorm, orderly, window | Ring only: all four on one wall, two doors 1.8 m apart | A, P, F | L | P1 |
| 12 | `ward.art` | exit_corridor, painter, easel | Edge beacon: easel under the feet, door at 68 degrees, painter at 51 degrees | A, E, P | M | P2 |
| 13 | `ward.dorm` | exit_corridor, sleeper, cabinet | Invisible: dark room, all three behind or beside | A, H, E | L | P2 |
| 14 | `ward.corridor` | exit_courtyard, phone, king, mural_door (secret) | Mixed: king passed, phone/mural far, exit 24 m | A, P, G | L | P2 |
| 15 | `ward.courtyard` | exit_exit, chef, lights | Edge beacon: door behind, lights at 58 degrees | A, C, P | M | P2 |
| 16 | `ward.exit` | exit_hospital_late, exit_ward_late, talent_lamp | Edge beacon: all behind (143, 143, 180 degrees) | A, B, F | L | P1 |
| 17 | `ward_late` | exit_treat, exit_dorm, stage_lamp, fireflies | Mixed: treat 12 m ahead, lamp behind | A, F, P | M | P1 |
| 18 | `ward_late.treat` | exit_exit, orderly, trolley | Edge beacon: all behind (155 to 180 degrees) | A, P, D | M | P3 |
| 19 | `ward_late.dorm` | exit_exit, sleeper, cabinet | Invisible (as scene 13) | A, H, E | S (reuses 13) | P3 |
| 20 | `ward_late.exit` | exit_ward_late, exit_hospital_late, stare | Ring only: two doors 1.8 m apart, x09 at 41 degrees | A, P | S (reuses 11) | P1 |

Totals: 20 scenes, 69 hotspots. Effort: 8 L (1, 2, 6, 7, 11, 13, 14, 16), 8 M (3, 4, 5, 9, 12, 15, 17, 18), 4 S (8, 10, 19, 20; each reuses an earlier scene's kit). Priority: 9 P1 (1, 2, 6, 7, 10, 11, 16, 17, 20: the entry scene that teaches the grammar plus every true fork), 7 P2 (3, 4, 5, 12, 13, 14, 15: first-pass side options), 4 P3 (8, 9, 18, 19: late-world side scenes).

## 2. The shared grammar (every scene entry below uses these; defined once so entries can be short)

**G1. Snap, don't tween.** A beat is 345 ms. CURRENT/NOT CURRENT swaps are 2 to 4 frame pose changes on the next half beat. The option that stops being current relaxes into its NOT CURRENT state in the same beat as the new one engages, so the player always sees a trade (one wakes up, one lets go).

**G2. The Route Rule (exits).** An exit is a physical door, gate, curtain or path. Its state is a function of *where the currently selected option ends up*:
* **WIDE** if the current option is this exit: leaf swung open, held by a doorstop or by its usher, light and the next room visible beyond it.
* **AJAR** (a hand's width, a slit of light, no wedge) if the current option is a side option and this exit is where it ends (the fall-through default: "you will still go this way").
* **SHUT** otherwise (the other exit of a fork): leaf closed and a hospital A-frame sign in front of it (`wetfloor_a` standing), or in the Ward a paper-chain strung across (`paperchain_gate`).
So a fork reads as one door open and one closed; touching the shut one swaps them. When a side option is current both doors dim: the default goes AJAR, the other stays SHUT. No colour is involved: open/shut/ajar, the barrier, and the usher's posture carry it.

**G3. Person grammar (P).** Any person who is an option invites in the same way:
* NOT CURRENT: faces the camera, `beckon` or `plead` at half strength (arm half-raised), face `hopeful`; after two bars slumps to face `sulk`/`sad` with the head turning away (the owner's "look sad"). One small tell every 2 bars (a hop, a wave) staggered between people so they never move together.
* CURRENT: stands taller, `beckon` full, face `happy`; on each bar a `nod`. Holds their prop out (`offer`).
* TOUCHED: a one-frame hop and the face flips (`sulk` to `happy`) on the next half beat; the previously current person's arms drop and the face goes `happy` to `sulk` in the same beat.
* COMMIT: success = the existing `success` act (cheer, nod, relief...) and the world reacts; failure = the existing `failure` act plus the set-piece named in the entry.
(Existing acts and faces cover this; the new face `hopeful`/`sulk` and acts `shrug`, `hold_door`, `sweep_arm` make it read. The `acting` blocks in `tools/run/acting_data.py` give `available` = NOT CURRENT and `selected` = CURRENT.)

**G4. Thing grammar.** An object has an idle tell (a 2 frame loop every 2 bars: flicker, rattle, twitch), a CURRENT "primed" pose (the thing is caught mid-action, ready to go), and a committed result. State frames are **sibling pieces**: two or three map things with `piece` ids (`<name>_a`, `_b`, `_c`) of which one shows; the engine already switches pieces on/off (`pieces: {on, off}`, cast `piece`/`op`).

**G5. One pointer for a set.** Where options are several places, one in-world device points at the current one: a hanging **finger-post** whose arrow board swings (corridor), a **conductor's baton** (bandstand), a **follow-spot** that swings and lands (stage). The device is *not* a hotspot; it is the cheapest way to show "exactly one is current" across 3 options and it carries the default from beat 48.

**G6. Staging rule.** Every option is inside the central band of the frame (x 220 to 1060 of 1280, clear of the pad lanes and the pause button), within +-40 degrees of the window heading, at least 25 degrees apart, from **both** the good-rail place and the first bad-rail place. People who are options stand within 7 m of the window camera (the new faces need LOD 2 or better to read; farther they fall back to the four old ones). Implementation: a new waypoint per scene (`rail.window`, listed per scene) that the rail holds from beat 44.5 on; the other options are moved to suit (re-homes below are approximate and must be checked on the capture).

**G7. No text.** Allowed: pictogram plates on doors and signs (a TV, a cup, a moon, a palette, a tree, a mic, a bed: one shared 32 x 32 sheet, `plates_icons`), the existing hand-lettered banners (TALENT SHOW, WELCOME HOME). Never a word that names the choice.

**Art scale used below.** World things are 128 x 128 px billboard tiles (about 1 to 2.2 m; `assets/story/<map>/textures/thing_*.png`), small props 64 x 64, pictogram plates 32 x 32, wall decals and signs 128 x 64, a floor mark 32 x 32 (a flat quad: see engine needs). People are the pixel rig (`tools/story/art/people.py`; a new face or act is baked only for the directed actors, `directed_actors` derives from the data). "Frames" are the state frames of G4.

## 3. Scene briefs

Each entry: the choice, the data and what is seen today, the window view and its fix, the design (one row per option: embodiment and invitation, CURRENT versus NOT CURRENT, TOUCHED, COMMIT success and failure), the default at beat 48, what to create and what already exists. "Create" names are the roll-up's keys (section 4).

---

### 3.1 `hospital` The Ward (private room, entry of the Hospital) | effort L | P1

**Choice.** You have woken in a hospital bed at visiting hours. Go: out of the door into the corridor (default), or let the nurse wheel you out, or stay for the family's cheer, or make the heart monitor keep the beat. (All four end in the corridor; they differ in what happens on the way and in energy.)

| hotspot | anchor | what | success | failure | today |
| --- | --- | --- | --- | --- | --- |
| `hospital.exit_corridor` (default) | waypoint `ward_door` | the ward door | corridor | same door, stagger (-5) | camera stands on the waypoint in the window (0 m): a ring under your feet |
| `hospital.nurse` | actor `h02` (nurse a) | the nurse | `hp_wheeled`, carried to the door (+6) | back to bed, queasy (-7) | 142 degrees behind: edge beacon |
| `hospital.family` | actor `h03` (mum b) | the family | `hp_family`, family cheers (+8, music variation) | `hp_visitor_asleep` (-4) | 122 degrees behind: edge beacon |
| `hospital.monitor` | thing `monitor_w` (0.6 m heart monitor piece) | the monitor | keeps the beat (+5, variation) | flatline (-9, dip) | 138 degrees behind, 0.6 m tall: edge beacon |

**View.** Window place today: `ward_door` yaw -90 (the camera stands in the doorway, back to the room). Fix: new waypoint `bed_window` ~(0.6, 4.2) yaw ~-15, the camera at the foot of the bed looking at the door across the room; rail good `[ward_chair, bed_window]`, bad unchanged. Re-home: nurse and wheelchair to the left (about -30 degrees, 2.5 m), family and balloons to the right (+25, 2.5 m), monitor on a tall stand centre-left (-10, 3 m, enlarge to 0.9 m), the door far ahead (+5, 6 m) with the door-holder in it.

| option | embodiment and invitation | CURRENT vs NOT CURRENT | TOUCHED (<= 1 beat) | COMMIT success / failure |
| --- | --- | --- | --- | --- |
| door (default) | the ward door in the far wall (`door_hosp`) with a **dad** (re-home crowd actor `c08`, dad a) standing in it | CURRENT: leaf WIDE on its wedge, corridor lit beyond, dad `hold_door` + `beckon`, face `happy`. NOT CURRENT: AJAR (a side option current) or SHUT with `wetfloor_a`, dad `shrug`, face `sulk` | leaf snaps WIDE, dad's face flips, the previous option's person relaxes | S: dad sweeps the door fully open, light floods the floor, dad `cheer`. F: door swings back, thumps his shoulder, dad `shame` (the stagger plays) |
| nurse (h02) | nurse beside a **wheelchair** (`wheelchair_h`) with a folded blanket on the seat | CURRENT: brake off, footplates down, blanket spread open on the seat, nurse `offer` toward the seat (hand on the push handle), face `resolve` to `happy`. NOT CURRENT: brake on (a small wedge), blanket folded, nurse `check` her clipboard, face `hopeful` glancing at you | blanket whips open (frame swap), nurse tucks the clipboard under her arm | S (existing `hospital.wheel_on`): nurse `push`, chair rolls to the door. F (existing `back_to_bed`): chair rolls back to the bed, nurse `shake_head` and points at the pillow |
| family (h03) | mum b at the bedside holding a **bunch of balloons** (`balloons_tether`) on a ribbon, others around the bed (c01, c02 kids) | CURRENT: balloons held high and bobbing, mum `cheer` ready, face `happy`, kids bounce. NOT CURRENT: balloons tied low to the bed rail, mum `wring_hands`, face `worry` | balloons snap up (frame), mum's face `worry` to `happy` | S: balloons release to the ceiling (piece `balloon_bunch` pulse), confetti, all `cheer`. F: one visitor (dad b `h01`) asleep in the chair, `sleep` with Zs, the rest stop cheering and look at him, mum `cover_face` |
| monitor | the monitor stand with a **moving trace** (`monitor_h`) at hand height beside the bed | CURRENT: bright screen, trace jumps in time with the beat (a tall spike on each beat), a heart glyph blinking. NOT CURRENT: dim screen, a small slow bump trace, no glyph | spike frame fires once, brightness up | S: trace goes double time, screen flashes the heart glyph, nurse looks up `happy`. F (existing flatline): trace goes flat, long tone shown as a steady glow, nurse `recoil` then `point` at the bed |

**Default from beat 48.** The dad is in the open doorway, waving you out, the door wide with light on the floor; the other three are in their quiet states (chair braked, balloons tied, trace small). Beat 0 to 47 the same set is visible as scenery (door ajar, dad leaning), so nothing pops.

**Create.** Objects: `door_hosp`, `wetfloor_a`, `wheelchair_h`, `balloons_tether`, `monitor_h`, `plates_icons`. People: `c08` re-homed to the door; no new archetype. Acts: `hold_door`, `shrug`, `push`, `wring_hands`. Faces: `hopeful`, `sulk`, `worry`. VFX: confetti already exists. **Exists:** nurse and family acting, `heart_monitor`, `balloon_bunch` pieces, `thing_door_lit`, hospital cinematics.

---

### 3.2 `hospital.corridor` The Corridor | effort L | P1

**Choice.** A fork in a long ward corridor: the day room (left door, default) or the cafeteria (glass doors at the far end), or stop for the tea trolley, or try the quiet room's door (a secret, once).

| hotspot | anchor | what | success | failure | today |
| --- | --- | --- | --- | --- | --- |
| `.exit_dayroom` (default) | waypoint `corridor_day_door` (19.75,-0.65) | day room door, left wall | day room | stagger | good rail ends at `corridor_fork` past it: 128 degrees behind |
| `.exit_cafeteria` | waypoint `corridor_cafe` (30.8,1) | glass doors at the end | cafeteria | stagger | 24 m from home, +10 degrees: a ring a mile away |
| `.trolley` | actor `h07` (nurse b, pacing 3 m with a tray) | tea trolley | `hp_tea`, tea (+6) | tea spill (-5, the room laughs) | 152 degrees behind |
| `.quiet_door` (secret, once, needs not `hp_saw_quiet`/`hp_quiet_locked`) | waypoint `corridor_quiet_door` (14.2,2.2) | the quiet room's door | peek, `hp_saw_quiet` (+3) | `hp_quiet_locked` (-4) | 178 degrees behind |

**View.** Today the good rail walks past every door. Fix: new waypoint `corridor_window` ~(12.6, 0.9) yaw -90 (facing east down the corridor); good `[corridor_mid, corridor_window]`. From there: quiet door ahead-right at about +35 degrees (1.7 m), trolley ahead 5.5 m, day room door left 7 m (-20 degrees), cafeteria doors dead ahead 18 m. Move the day room door to double doors (wider, 1.6 m) so it reads at 7 m.

**Design.** The fork uses a pointer (G5): a **finger-post** hung from the ceiling above the junction with two icon plates (a TV for the day room, a cup for the cafeteria) and a pivoting arrow board that swings to the current exit; centre = a side option is current.

| option | embodiment and invitation | CURRENT vs NOT CURRENT | TOUCHED | COMMIT S / F |
| --- | --- | --- | --- | --- |
| day room (default) | left double door (`door_hosp` double variant, plate TV) with a **kid b** (`corridor_c10`) in the doorway | CURRENT: leaf WIDE on a wedge, blue TV flicker spilling out, kid `beckon` + face `laugh`, finger-post arrow swung left. NOT CURRENT: SHUT + `wetfloor_a` (or AJAR when the trolley/quiet door is current), kid `shrug`, face `sulk` | leaf snaps, arrow swings 2 frames, kid hops | S: laugh track audible as a visual burst (kid `cheer`), doors flap. F: leaf bounces back on the kid, he `recoil`s; the stagger plays |
| cafeteria | far glass doors (`door_hosp` glass variant, plate cup, 18 m away: too far for a face to read) with **nurse b** (`corridor_c08`, re-homed to (19.5,1.6), 7 m ahead in front of the doors) holding a cup, steam rising | CURRENT: leaves WIDE, steam drifts into the corridor, nurse `offer` a cup, face `happy`, arrow right. NOT CURRENT: shut + sign, nurse sips, face `sulk` | same snap | S: nurse raises the cup `cheer`. F: she drops the cup (small splash frame), `recoil` |
| tea trolley (h07) | the trolley (`tea_trolley_h`) rolling slowly *away* down the corridor on its pace axis (3 m) | CURRENT: **stops, turns to face you**, h07 `pour` into a mug (steam), face `proud`, finger-post arrow straight down at it. NOT CURRENT: rolling away with the nurse `serve`, back half turned, mug rattle (idle tell) | trolley stops dead (frame), she spins and `offer`s a mug | S (`hospital.tea`): she hands the mug, you drink, `nod` + `relief`. F (`tea_spill`): jug tips, a spill frame, h07 `recoil`, kid `laugh`, dad `recoil` (existing cast) |
| quiet door (secret) | a door on the right wall with a moon plate and a **crack of warm light** (`door_hosp`, frame AJAR-CRACK) | CURRENT: crack widens to two fingers, a hush glow, a tiny `shush` person-icon plate hung on the handle. NOT CURRENT: crack hairline, light flickers once per 2 bars | leaf creaks wider (frame) | S: leaf opens, a slice of the quiet room with a nightlight (`hospital.peek_quiet`). F: a keycard reader (`keypad_reader`, 2 frames) beeps and the handle rattles, door stays shut; a nurse `shush`es from behind you (cast, optional) |

**Default from beat 48.** Day room door WIDE with the kid waving you in, finger-post arrow pointing left, TV light spilling; cafeteria door shut behind a sign, nurse sulking; trolley rolling away; quiet door hairline crack. Touch the cafeteria: arrow swings right, doors swap, kid and nurse swap faces.

**Create.** Objects: `door_hosp` (single, double, glass, crack variants), `finger_post`, `wetfloor_a`, `tea_trolley_h`, `keypad_reader`, `plates_icons` (tv, cup, moon). Acts: `hold_door` (optional), `shrug`, `pour`. Faces: `hopeful`, `sulk`, `proud`. VFX: steam loop exists (`cafeteria_steam`). **Exists:** `corridor_doorglow` piece, `corridor_lights`, the hanging WARD/CAFE signs in the front layer (replace by the finger-post), cinematics `tea`, `tea_spill`, `peek_quiet`.

---

### 3.3 `hospital.dayroom` The Day Room | effort M | P2

**Choice.** Go through to the garden (default), or fix the TV to the right channel, or let granny tell her story.

| hotspot | anchor | what | success | failure | today |
| --- | --- | --- | --- | --- | --- |
| `.exit_garden` (default) | waypoint `dayroom_door` (20.25,-1.4): the door you came in by | the way out | garden | stagger | good rail ends 2 m from the TV (`day_tv_in`), exit 12 m behind |
| `.tv` | thing `tv_set` (wall_tv, 1.4 m, at 20,-14.6) | the wall TV | `hp_tv_on` (+6, variation) | static (-5, dip) | camera 1.6 m from it: a huge blurred blue slab (see `contact_hotspots_hospital.jpg`) |
| `.granny` | actor `h08` (granny a, `watch`ing h10) | granny | `hp_granny_tale` (+8) | the long version (-5, queasy) | 178 degrees behind |

**View.** Fix: move the exit to a glazed **garden door on the east wall** at about (23.6,-8.5) (`french_door_h`), new waypoint `dayroom_window` ~(19.2,-4.2) yaw ~+10: granny 1 m ahead-left at -25 degrees, the TV 10 m ahead (+5 degrees), the garden door at +40 degrees. Stop the good rail at `dayroom_window` (never `day_tv_in`; delete that step or drop it to 4 m from the TV). The kid `h10` stays in front of the TV.

| option | embodiment and invitation | CURRENT vs NOT CURRENT | TOUCHED | COMMIT S / F |
| --- | --- | --- | --- | --- |
| garden door (default) | glazed French door (`french_door_h`, plate tree) with dusk light and a **dad a** holding it (`h04`, dad a, re-homed from the ward) | CURRENT: WIDE, leaves of garden light on the floor, dad `hold_door` + `beckon`, `happy`. NOT CURRENT: AJAR (tv/granny current) | snap | S: dad sweeps, petals blow in. F: door bangs, dad `shame`, stagger |
| TV | the set on a trolley, **tuning knob** drawn on the bezel, kid h10 sitting in front | CURRENT: picture steady and animated (a dancing show in time with the beat, `tv_set_h` frame show_a/b), kid `laugh` pointing. NOT CURRENT: picture rolling with static bands (`roll` frame), kid `hit`s the side lightly (idle tell: `flick`) face `worry` | roll snaps to steady | S (existing `tv_watch`): the show stays, kid `cheer`. F (`tv_static`): snow burst fills the set, hiss as flicker, kid `recoil`, picture lost |
| granny (h08) | granny in the armchair knitting, a **sweet tin** on her knee (prop `sweet_tin`) | CURRENT: leans forward, offers the tin, face `relief` then `happy`, pats the seat (`pat_seat`). NOT CURRENT: `watch` the TV, knitting needles twitch; every 2 bars she glances at you and pats the seat (face `hopeful`) | tin lid pops open | S (existing `granny`): she nods, sweet in hand, `relief`. F (`granny_long`): she keeps talking, hands going, `shake_head` ignored; the **wall clock runs fast** (`wall_clock_fast`, hands whirring) and h10 `laugh`s |

**Default from beat 48.** The French door open with the dad holding it; TV rolling; granny with the tin shut. **Create:** `french_door_h`, `tv_set_h` (frames roll, show_a, show_b, snow), `wall_clock_fast`; prop `sweet_tin`; acts `hold_door`, `pat_seat`, `flick` (a light slap on the set); faces `hopeful`, `sulk`, `worry`. **Exists:** `wall_tv` animated texture, cinematics, h08/h10 acting.

---

### 3.4 `hospital.cafeteria` The Cafeteria | effort M | P2

**Choice.** On to the garden (default), or the vending machine (a secret: a snack and a brass token, or it eats the coin), or the waving kid's trick.

| hotspot | anchor | what | success | failure | today |
| --- | --- | --- | --- | --- | --- |
| `.exit_garden` (default) | waypoint `cafe_garden_door` (46.2,1) | the garden door | garden | stagger | camera faces a window onto the night garden; the door is 67 degrees aside |
| `.vending` (secret, once) | thing `vending_f` (1.8 m, piece `cafeteria_vending`) at (42.5,-5.4) | vending machine | `hp_token` (+6) | `hp_jam` (-3) | 80 degrees left, 6 m: edge beacon |
| `.kid` | actor `h14` (kid a, waving) at (37.5,3) | the kid | `hp_kid_friend` (+6) | -5, the kid cries | 139 degrees behind at the good place |

**View.** New waypoint `cafe_window` ~(41.0,1.0) yaw -90 (facing east). Re-home the vending machine to the north wall at about (45.0,-3.0) (-40 degrees, 5 m) and the kid to (44.0,3.2) (+35 degrees, 4 m, in front of a table); the door dead ahead (4.2 m).

| option | embodiment and invitation | CURRENT vs NOT CURRENT | TOUCHED | COMMIT S / F |
| --- | --- | --- | --- | --- |
| garden door (default) | glazed door (`french_door_h`) with a **mum a** (`cafeteria_c06`) beside it holding the door | CURRENT: WIDE, night garden and moon visible, mum `hold_door`, `happy`. NOT CURRENT: AJAR or SHUT with sign | snap | S: mum sweeps. F: door swings back, mum `shame` |
| vending machine | the coral machine (`vending_h`) with a **chase of lit selection tiles** and a **coin-slot plate** (round, ridged icon = the token slot) | CURRENT: the spiral turns and a packet hangs on the lip (primed), the slot flashes the ridged token shape. NOT CURRENT: tiles chasing, packet still, the slot dark | packet slips to the edge, slot flashes | S (existing `vend`): flap drops the packet and a brass token (a 16 px token sprite lands on the tray). F: the packet jams, a coin bounces back (`jam` frame), a small thump (flicker) |
| kid h14 | the kid at a table, waving (`wave`, face `laugh`) | CURRENT: **stands on the chair**, arms out (`hop`), face `laugh` then `wink`. NOT CURRENT: sits, small wave, face `hopeful`, glances at the machine | hops up on the chair (1 frame) | S: a spin and a landing, `cheer` + `laugh`, two other kids clap. F: wobbles, `sad`, `shame` face, sits |

**Default from beat 48.** Mum holding the open garden door; machine tiles chasing; kid waving from his chair. **Create:** `vending_h` (idle, primed, jam), `token_16`, `french_door_h` (shared with 3.3); acts `hold_door`, `hop`; faces `wink`, `hopeful`, `sulk`. **Exists:** `cafeteria_vending` piece, `vend`/`kid` cinematics, kid and nurse acting.

---

### 3.5 `hospital.garden` The Garden | effort M | P2

**Choice.** On through the gate to the bandstand (default), or light the lamppost, or take mum's phone.

| hotspot | anchor | what | success | failure | today |
| --- | --- | --- | --- | --- | --- |
| `.exit_exit` (default) | waypoint `garden_door_e` (58.2,1) | the east gate | bandstand | stagger | in front (-4 degrees, 3 m) from `bandstand` yaw 90 |
| `.lamp` | thing `lamp_g0` (thing_lamppost 2.8 m) at (48,-4.6) | lamppost | `hp_lamp_lit` (+5, variation) | the bulb pops (-5, dip) | 14 m away, -24 degrees: a ring |
| `.mum` | actor `h16` (mum a, `phone`) at (54.5,8.9) | mum on the phone | `hp_called_home` (+6) | no answer (-4) | 10 m, 49 degrees: out of frame |

**View.** Today's window place faces the gate but the other two are far and wide. Fix: `garden_window` ~(51.0,1.0) yaw -90 (facing east): gate dead ahead 7 m, mum moved to (55.0,5.0) (+30 degrees, 5 m), lamp `lamp_g0` moved to (55.5,-3.0) (-35 degrees, 6 m) beside the gate.

| option | embodiment and invitation | CURRENT vs NOT CURRENT | TOUCHED | COMMIT S / F |
| --- | --- | --- | --- | --- |
| gate (default) | a garden gate (`garden_gate`) in the east hedge, a lantern on each post | CURRENT: gate WIDE, both lanterns lit, bandstand bunting visible behind, petals drift through. NOT CURRENT: gate latched, lanterns dark | gate swings (2 frames) | S: gate bangs wide, bunting waves. F: gate swings back and clips the post, lanterns flicker |
| lamppost | the lamp (`lamppost_h`) with moths | CURRENT: bulb lit, steady, **moths gather in a ring**, a cone of light on the bench. NOT CURRENT: dark, a single flicker every 2 bars (a lit bulb that will not hold) | flicker frame becomes lit | S: lamp steady, moths circle, bench lit. F: bulb pops, glass sparkle frame, moths scatter, light out |
| mum (h16) | mum on a bench by the path, phone to her ear back half-turned | CURRENT: turns to you, **holds the phone out** (`offer`, prop `phone` with a lit screen), face `grief` to `hopeful`. NOT CURRENT: phone to ear, `rock`, face `worry` | turns and holds out the phone | S (existing `phone`): `nod`, then `cheer` with `relief`. F: the screen goes dark, `cover_face`, `sad` |

**Create:** `garden_gate`, `lamppost_h` (dark, flicker, steady+moths, popped), prop `phone` screen frames lit/dark, faces `hopeful`, `worry`. **Exists:** garden art, mum acting, `garden_*` pieces.

---

### 3.6 `hospital.exit` The Bandstand | effort L | P1

**Choice.** The end of the Hospital: back to the garden (loop into Hospital late, default, left gate), out to the Ward (right gate), or step up to the mic and sing.

| hotspot | anchor | what | success | failure | today |
| --- | --- | --- | --- | --- | --- |
| `.exit_hospital_late` (default) | waypoint `bandstand_door_l` (59.8,-1.8) | left gate | hospital_late | stagger | in front (0 degrees, 3 m) but a ring |
| `.exit_ward_late` | waypoint `bandstand_door_r` (59.8,3.8) | right gate | ward_late | stagger | 65 degrees: edge beacon |
| `.mic` | thing `mic_band` (thing_mic 1.5 m) at (62.3,1.4) | the mic | `hp_sang` (+10, variation) | feedback (-8, dip) | 88 degrees: edge beacon |

**View.** The player stands on the stage facing the audience; the stage things are beside and behind. Fix: `bandstand_window` ~(56.5,1.0) yaw -90 (facing the bandstand): left gate (-25 degrees, 3.5 m), mic centre (+0, 5.5 m), right gate (+30 degrees, 3.5 m). A **bandleader** stands centre-stage behind the mic.

**Design.** A pointer (G5): the bandleader's **baton** points at the current thing.

| option | embodiment and invitation | CURRENT vs NOT CURRENT | TOUCHED | COMMIT S / F |
| --- | --- | --- | --- | --- |
| left gate (default) | `garden_gate`, hospital style (lanterns), a **nurse** (`garden_c10`) at it | CURRENT: gate WIDE, nurse `beckon` + `happy`, baton aimed left. NOT CURRENT: gate shut, nurse `sulk`, arms folded | snap | S: nurse `cheer`, lanterns up. F: gate rebound, nurse `shame` |
| right gate | `garden_gate`, **ward style** (paper-chain barrier, crown on the post); a **crowned visitor** (new hospital-wardrobe NPC: dad b with a paper crown and a dressing gown, a nod to the Ward) peeks from it | CURRENT: paper chain drops, king `beckon` + `proud`, baton right. NOT CURRENT: chain strung, king `shrug` | chain falls (frame) | S: king `bow`. F: chain tangles on his arm, `shame` |
| mic | `mic_stand` on a small platform, cable | CURRENT: stand tilted to you (`primed`), spot pool, bandleader's baton down on it, crowd glowsticks up. NOT CURRENT: upright, cable twitching, a tiny squeal ring at the head (idle tell) | tilts toward you | S (existing `sing`): crowd `cheer`, glowsticks, stage lights lift. F (`feedback`): the squeal ring bursts, crowd `cover_face`, bandleader `recoil` |

**Default from beat 48.** Baton pointing at the left gate, nurse open-armed, ward gate shut. **Create:** NPCs `bandleader` (hospital wardrobe: dad variant c, peaked bandmaster cap, braid jacket; prop `baton`) and `crowned_visitor`, `garden_gate` (hospital and ward variants), `paperchain_gate`, `mic_stand` (idle, primed, feedback), acts `shrug`, `sweep_arm`, `point` with baton; faces `hopeful`, `sulk`, `proud`. **Exists:** `thing_mic`, bandstand, `sing`/`feedback` cinematics, `h15` cheering.

---

### 3.7 `hospital_late` The Garden (second round) | effort L | P1

**Choice.** Left to the cafeteria (default) or right to the quiet room; or light/relight the lamppost; or follow the doctor.

| hotspot | anchor | what | success | failure | today |
| --- | --- | --- | --- | --- | --- |
| `.exit_cafe` (default) | waypoint `garden_door_w` (47.8,1) | west door A | cafe | stagger | 166 degrees behind at the good place |
| `.exit_quiet` | waypoint `garden_door_w2` (47.8,-3) | west door B (4 m north of A) | quiet | stagger | 101 degrees behind |
| `.lamp` (not `hp_lamp_lit`) / `.lamp_lit` (when lit) | thing `lamp_g1` (lamppost) at (48,6.6) | lamp, first or second round | `hp_lamp_lit` / `hl_lamp_again` (+5 / +6, variation) | pops (-5, dip) / gutters (-3) | 96 degrees behind |
| `.doctor` | actor `h17` (doctor a) at (51.5,7.5) | the garden doctor | `hl_doctor`, beckons you on (+5) | checks his clipboard, frowns (-5) | 65 degrees |

**View.** Home (`garden_edge`) already faces west with all of them ahead; the good rail then turns the camera to face east. Fix: good rail `[garden_north, garden_late_window]` where `garden_late_window` ~(52.5,2.0) yaw 90 (west): the two doors (-5 and -25 degrees), lamp (+40 degrees), doctor (+35 degrees). Move the quiet door A to the south side of the hedge wall so the doors are 8 m apart.

| option | embodiment and invitation | CURRENT vs NOT CURRENT | TOUCHED | COMMIT S / F |
| --- | --- | --- | --- | --- |
| cafeteria door (default) | glazed door with steam in the window, plate cup, **nurse b** (`garden_c04`) in the doorway with a mug | CURRENT: WIDE, steam out, nurse `offer` the mug `happy`. NOT CURRENT: SHUT + sign, nurse sips and `sulk` | snap | as 3.2 |
| quiet room door | a dark door with a moon plate, a **nurse** (`garden_c10`) with a finger to her lips | CURRENT: AJAR-wide, a warm night-light slice on the path, nurse `shush` then `beckon` slowly. NOT CURRENT: SHUT, nurse folds arms, `sulk` | snap | S: nurse `nod`. F: door clicks, nurse `shush` harder |
| lamp / lamp_lit | `lamppost_h` | `lamp`: CURRENT = lit, moths ring; NOT CURRENT = dark and flickering. `lamp_lit` (flag set): always **already lit**, steady; CURRENT = the halo switches to a **star burst and moth spiral** (`lamppost_h` frame lit_b = "lit differently"), NOT CURRENT = plain steady | frame swap | S: lit_b holds. F: it gutters (a 2 frame stutter) |
| doctor (h17) | doctor with clipboard | CURRENT: clipboard lowered to hip, `beckon` + `happy`, steps one pace toward the path. NOT CURRENT: `write`, face `doubt` | clipboard drops | S (existing `doctor`): `nod`, walks a step. F: `shake_head`, back to writing |

**Default from beat 48.** Cafeteria door open with the nurse offering a mug; quiet door shut; lamp as it was left; doctor writing. **Create:** `door_hosp` (glass, quiet variants), `wetfloor_a`, `lamppost_h` frame lit_b, acts `shush`, `hold_door`, `shrug`; faces `hopeful`, `sulk`, `doubt` exists. **Exists:** garden, lamp thing, doctor acting.

---

### 3.8 `hospital_late.cafe` The Cafeteria (late) | effort S | P3

**Choice.** On (default), or the vending machine (a snack, or with the token a free drink), or the kid again.

| hotspot | anchor | what | success | failure | today |
| --- | --- | --- | --- | --- | --- |
| `.exit_exit` (default) | `cafe_garden_door` | east door | exit | stagger | 0 degrees at the good place: a ring on the door |
| `.vending` (no `hp_token`) / `.vending_token` | thing `vending_f2` (2 m) at (36.5,-5.4) | machine | `hp_token` (+6) / `hl_free_drink` (+10, variation) | out of order (-3) / wrong token (-3) | 129 degrees behind |
| `.kid` | actor `h14` | the kid | cinematic (+6) | cries (-5) | 155 degrees behind |

**View.** Same kit as 3.4 (`cafe_window`): vending moved to the east end, kid forward.

**Design.** As 3.4 with these differences: the machine's **coin slot plate shows the token (round, ridged brass) when `hp_token` is held** and an empty slot otherwise; with the token, CURRENT also drops a free paper cup onto the tray; `vending_token` failure shows the token returned to the slot (wrong token). The kid's tell is the same trick, a **cartwheel** on `hop` (`kid again`: face `wink`). Door as 3.4 (mum holds it). Default at beat 48: mum holding the door open. **Create:** nothing new (reuses 3.4's `vending_h`, `french_door_h`, `token_16`, `hop`, `wink`).

---

### 3.9 `hospital_late.quiet` The Quiet Room | effort M | P3

**Choice.** A hushed room with two night lights: the way on (default, back out the door), or the first night light (calm: +10, or it goes out), or the second (a softer mix: +5, or it flickers).

| hotspot | anchor | what | success | failure | today |
| --- | --- | --- | --- | --- | --- |
| `.exit_exit` (default) | waypoint `quiet_door` (14.2,3.8) | the door | exit | stagger | camera at `quiet_far`, yaw 180 facing the wall: door 180 degrees behind |
| `.nightlight` | thing `nl_q0` (nightlight 0.28 m, low) at (13.07,6.0) | night light 1 | `hl_calm`, calm (+10) | goes out (-5) | 172 degrees behind, tiny |
| `.nightlight_b` | thing `nl_q2` at (13.07,12.0) | night light 2 | softer mix (+5, variation) | flickers (-4, dip) | 156 degrees behind |

**View.** The quiet room is a long thin room (door at z 3.8, far end z 14.5). Fix: camera `quiet_window` ~(14.2,14.0) yaw 0 (facing the door end); re-home the two night lights onto one side wall at z 8.0 and z 10.5 (6 m and 3.5 m ahead, +-20 degrees, enlarge to 0.5 m), door dead ahead 10 m. The camera is never facing the window blur.

**Design.** A hush kit (H): everything is slow, quiet, and moves on the beat at half time. The two lights are **different shapes** (a moon and a star plate on the lamp body) so they are never told apart by colour.

| option | embodiment and invitation | CURRENT vs NOT CURRENT | TOUCHED | COMMIT S / F |
| --- | --- | --- | --- | --- |
| door (default) | `door_hosp` with moon plate, a **nurse** (`h07`, existing cast: stares at the door) at it | CURRENT: AJAR-WIDE, corridor light a slice, nurse `shush` + slow `beckon`, `relief`. NOT CURRENT: AJAR (a night light is current) | snap | S: nurse `nod`. F: handle squeaks, nurse `recoil` (a hush broken) |
| night light 1 (moon) | `nightlight_moon` on the wall plug, projects a **moon shape on the wall** | CURRENT: bright, **breathes in time with the beat** (slow glow-pulse per bar), the moon shape on the wall. NOT CURRENT: dim ember, no projection | glow jumps to the bright frame | S: warm pool, room relaxes (the people `rock`, `relief`). F: goes out, the wall shape vanishes, nurse `shush` |
| night light 2 (star) | `nightlight_star` | same with a star-shaped projection; CURRENT breathes at half the pace | same | S: softer mix, the pool wide. F: flickers (2 frame stutter) |

**Default from beat 48.** Door AJAR with the nurse's `shush`; both lights dim embers. **Create:** `nightlight_moon`, `nightlight_star` (off, ember, bright; wall-projection decals 128 x 128), `door_hosp` moon variant, act `shush`, face `relief` exists, `hopeful`.

---

### 3.10 `hospital_late.exit` The Bandstand (late) | effort S | P1

Same stage and kit as 3.6 (left gate default = loop into Hospital late, right gate = Ward late, mic). Differences: the mic hotspot is `mic` until `hp_sang`, then `mic_encore` (the same `mic_stand`). When `hp_sang` is set the stage carries a **bouquet** on the stand (`bouquet_stage`, 64 x 64) and the crowd's glowsticks are already up, so the encore reads as "they remember": CURRENT = bouquet raised, bandleader `bow`s toward the mic, baton on it; failure `hoarse`: the mic droops, bandleader `shrug`. Right gate exit label in `hospital_late`: the loop door (left) is also the default here, so the **nurse's gate has a looped wreath** (a ring of paper stars on the post: "round again") to differ from the 3.6 gate. **Create:** `bouquet_stage`, `wreath_loop` (64 x 64), otherwise reuse 3.6.

---

### 3.11 `ward` The Day Room (entry of the Ward) | effort L | P1

**Choice.** The ward's first fork: the art room (right door, default) or the dormitory, or get past the orderly, or let the window light in.

| hotspot | anchor | what | success | failure | today |
| --- | --- | --- | --- | --- | --- |
| `ward.exit_art` (default) | waypoint `day_door_a` (6.3,6.8) | east door A | ward.art | stagger | +30 degrees at the good place (13 m): a ring |
| `ward.exit_dorm` | waypoint `day_door_b` (6.3,5.0) | east door B, 1.8 m from A | ward.dorm | stagger | +34 degrees, on top of A |
| `ward.orderly` | actor `e04` (orderly b) at (4.39,1.47) | the orderly | `wd_orderly_ok`, lets it pass (+4) | `wd_treated`, carried to the treatment room (-9) | +38 degrees, 7 m |
| `ward.window` | thing `wlight_d` (window light, 2.6 m) at (6.6,3.0) | the window | `wd_window`, light comes in (+5, variation) | the glazing bars rattle (-5, dip) | +43 degrees, 10 m |

**View.** All four are on the east wall, so they are in front at the good place but crowded. Fix: new waypoint `ward_window` ~(0.0,4.0) yaw -90 (facing the east wall, 6.3 m): door B moved to the north end (6.3,1.0, -26 degrees), window at (6.6,3.4) (-5 degrees), door A at (6.3,6.8) (+24 degrees); orderly moved to (3.0,4.4) in the aisle (+8 degrees, 3 m). Good rail `[bars_in, ward_window]`.

**Design.** Pictogram plates tell the two doors apart without words: **palette** on door A (art), **moon** on door B (dorm). The usher gestures follow the Ward's whimsy.

| option | embodiment and invitation | CURRENT vs NOT CURRENT | TOUCHED | COMMIT S / F |
| --- | --- | --- | --- | --- |
| door A, art (default) | pastel door (`door_ward`, palette plate) with a **painter** (`c10`, ponytail b) in the doorway, paint on her hands, a brush behind her ear | CURRENT: leaf WIDE, warm studio light and a paper-chain gate (`paperchain_gate`) dropped on the floor, painter `hold_door` + `beckon`, face `proud`. NOT CURRENT: AJAR (side option current) or SHUT with the chain strung across, painter `shrug`, face `sulk`, brush drooping | chain drops, leaf snaps | S: she `cheer`s, flicks paint (small splat frame, harmless). F: leaf swings back, she `recoil`s |
| door B, dorm | pastel door (`door_ward`, moon plate) with a **sleepy resident** (`sleepy_usher`: `curly b` in a dressing gown, nightcap, hugging a pillow) | CURRENT: WIDE on a soft blue night glow, chain dropped, resident `stretch` + `beckon` with face `yawn` (a happy yawn). NOT CURRENT: chain strung, resident `sulk` slumped on the pillow | same snap | S: resident lies down on the pillow in the doorway, `relief`. F: leaf swings back, resident drops pillow, `shame` |
| orderly (e04) | the orderly standing in the aisle, arms folded, a **sign-out clipboard and a ring of keys** | CURRENT: arms unfold, steps aside with `sweep_arm`, face `resolve` to a small `proud`, clipboard turned to you. NOT CURRENT: `block` (arms folded, feet apart), face `resolve`, taps his watch every 2 bars (`tap_watch`) | arms drop, he steps one pace sideways (frame) | S (existing `orderly_nod`): `nod`, steps aside, you walk through. F (existing `to_treatment`): he takes the wheelchair parked behind him (`wheelchair_w`, ward variant) by the handles, `point` at the treatment door; x03 `recoil`, x04 `cover_face` (existing) |
| window | the tall sash window (`window_sash_w`) with a long curtain | CURRENT: sash **up**, curtain billows in on the beat, the moon beam wide on the floor, a small bird (`bird_sill`, 2 frames) on the sill. NOT CURRENT: sash down, glazing bars, the beam thin, curtain still, one small rattle every 2 bars (idle tell) | sash jumps up | S: beam sweeps across the floor (existing `window_light` pulse), bird flaps out, the dancers look up `awe`. F: sash slams, glass rattles (2 frame shake), beam snaps off, bird gone |

**Default from beat 48.** The painter holds door A open, chain on the floor, warm light out; the dorm door shut behind its chain with the sleepy resident slumped; orderly blocking; window shut. **Create:** objects `door_ward`, `paperchain_gate`, `plates_icons` (palette, moon), `window_sash_w`, `bird_sill`, `wheelchair_w`; NPC `sleepy_usher` (a dressing-gown, nightcap and pillow look on any ward body, chosen so it shares no build, hair and top with `x13`/`x14`: the `look_key` rule) (+ prop `pillow`); acts `hold_door`, `stretch`, `shrug`, `sweep_arm`, `tap_watch`; faces `yawn`, `sulk`, `proud`, `hopeful`. **Exists:** `window_light`, `notice_board`, orderly acting and cinematics.

---

### 3.12 `ward.art` The Art Room | effort M | P2

**Choice.** Back out to the corridor (default), or watch the painter's painting of a door (the flag `wd_painted` opens a secret in the corridor), or paint your own.

| hotspot | anchor | what | success | failure | today |
| --- | --- | --- | --- | --- | --- |
| `.exit_corridor` (default) | waypoint `art_door` (33.8,6) | the art room's door | ward.corridor | stagger | 68 degrees at the good place (11 m) |
| `.painter` | actor `x10` (ponytail a) at (35.1,2.9) | the painter | `wd_painted` (+6) | `wd_paint_spill`, paint over you (-6) | 51 degrees |
| `.easel` | thing `easel_a3` (thing_easel_b 1.8 m) at (44,10.8) | an easel | `wd_own_painting` (+5) | a smudge (-4) | under the camera at `art_easels` (1 m, 156 degrees) |

**View.** `art_window` ~(41.0,7.0) yaw 90 (west). Move the easel to (37.0,9.6) (about +30 degrees, 4.5 m), the painter to (37.0,4.6) (-35 degrees, 4.5 m), door dead ahead 7 m. Good rail `[art_mid, art_window]`.

| option | embodiment and invitation | CURRENT vs NOT CURRENT | TOUCHED | COMMIT S / F |
| --- | --- | --- | --- | --- |
| door (default) | `door_ward` (pale blue, palette plate), a paper-chain gate; a **chef** (`art_room_c07`) leaning in it with a tea towel | CURRENT: WIDE, corridor tubes light the floor, chain down, chef `hold_door` + `beckon`, `happy`. NOT CURRENT: AJAR / chain strung, chef `shrug` | snap | S: chef `bow`. F: leaf swings, chef `recoil` |
| painter (x10) | painter at an easel (`painter_canvas`) holding a **brush offered at arm's length**; her canvas shows a **painted door** | CURRENT: canvas swung to face you (frame B: a painted door with a bright handle, the same art as the corridor's `mural_door`), brush `offer`, face `awe` to `proud`. NOT CURRENT: back half turned painting (frame A: just smears), face `hopeful`, one glance every 2 bars | canvas pivots to you (frame swap) | S (existing `paint_look`): the painted door's handle gleams (frame C), she `cheer`s with `awe`; art-room people `awe`. F (`paint_spill`): she flicks the brush (`flick`), a **splat overlay** (`screen_splat`) hits the lens, the room `laugh`s; she `recoil`s |
| easel (a3) | a spare easel with a **drop cloth** over the canvas, a brush in a jar of water dripping | CURRENT: cloth whisked off, canvas blank and primed, brush lifted out of the jar and **dripping** (a bead of paint falls each beat). NOT CURRENT: covered by the cloth, brush jar still | cloth flies off (frame) | S: a small sun-and-house painting appears on the canvas (`easel_canvas` frame painting), `art_room_c03` `awe`. F: the brush slides, the canvas smears (frame smudge) |

**Default from beat 48.** Chef holding the pale blue door open, chain down; painter's back to you; easel covered. **Create:** `door_ward` (reuse), `painter_canvas` (3 frames), `easel_canvas` (4 frames), `screen_splat`, acts `flick`, `shrug`, `hold_door`, faces `awe` exists, `proud`, `hopeful`, `sulk`. **Exists:** `craft_table`, `hanging_paintings`, painter acting and cinematics, `thing_easel_b`.

---

### 3.13 `ward.dorm` The Dormitory | effort L | P2

**Choice.** Back out to the corridor (default), or sing a lullaby for the sleeper, or search the cabinet (a key, or an alarm bell).

| hotspot | anchor | what | success | failure | today |
| --- | --- | --- | --- | --- | --- |
| `.exit_corridor` (default) | waypoint `dorm_door` (26,8.6) | the door | corridor | stagger | at the good place (`dorm_bed`, yaw 180): 7 m, 180 degrees behind |
| `.sleeper` | actor `x14` (punk b, asleep in the alcove) at (30.4,11.5) | the sleeper | `wd_lullaby`, lullaby (+8) | `ward.woken`, you wake him (-6, queasy) | 132 degrees behind |
| `.cabinet` | thing `cab_m0` (thing_cabinet 1.2 m) at (21.5,8.35) | locker | `wd_dorm_key`, a key (+3) | the alarm bell (-7, dip) | 147 degrees behind |

**View.** A dark room: the contact sheet is nearly black with three edge beacons. Fix: `dorm_window` ~(26.0,14.2) yaw 0 (facing the door end, i.e. back toward it), beds in the front arc: sleeper's bed re-homed to (28.4,10.4) (+20 degrees, 4 m), cabinet at (23.6,8.6) beside the door (-25 degrees, 5.6 m), door dead ahead (5.6 m). Add a **low moon-spill** through the slit window (`quiet_slit`) so the shapes read; the dorm gets a floor lamp pool on the sleeper.

**Design.** A hush kit (H, as 3.9): everything slow, one `shush` on every bar line.

| option | embodiment and invitation | CURRENT vs NOT CURRENT | TOUCHED | COMMIT S / F |
| --- | --- | --- | --- | --- |
| door (default) | `door_ward` with moon plate, the **sleepy usher** (`sleepy_usher`) with a pillow in the doorway | CURRENT: WIDE on corridor light, chain down, usher `stretch` + `beckon` quietly. NOT CURRENT: AJAR a sliver / chain strung | snap | S: usher `relief`. F: door creaks, usher `recoil`, `shush` |
| sleeper (x14) | sleeper in the bed under the **moon-and-stars mobile** (`sleeper_mobile`); the neighbour **x13** (curly b) awake in the next bed signals with `shush` and points at him | CURRENT: x13 sits up, **rocks an invisible baby** (`rock`, face `hopeful`), the mobile turns slowly (3 frames), the sleeper's face `relief`, small Zs. NOT CURRENT: x13 lying, `shush`, eyes on you (`hopeful`), mobile still, sleeper `sleep` neutral | x13 sits up (frame), mobile starts | S (existing `lullaby`): x13 `nod`, both `sleep` with `relief`, the mobile spins steadily, stars twinkle. F (`woken`): the sleeper **`sit_up`** with `fear`, x13 `recoil` under the blanket, the mobile tangles |
| cabinet | cabinet with a **brass key on a nail** inside a gap, and above it an **alarm bell** (`alarm_bell`, on the wall, visible) | CURRENT: door ajar, key swings and **glints**, the bell trembles slightly (the risk is in view). NOT CURRENT: door shut, key a dull edge, the bell still | door creaks open (frame) | S (existing `search`): the key in hand (key sprite near the lens edge), bell silent. F: the bell **rings** (2 frame shake + arcs), the sleeper stirs, x13 `cover_face` |

**Default from beat 48.** Usher at the open door, mobile still, cabinet shut and the bell still. **Create:** `door_ward` (moon), `sleeper_mobile` (4 frames), `alarm_bell` (2), `cabinet_m` (closed, ajar+key A/B), `key_16`; NPC `sleepy_usher` (shared with 3.11); acts `shush`, `stretch`, `sit_up`, `rock` exists; faces `yawn`, `hopeful`, `relief` exists. **Exists:** dorm sector, `x13`/`x14` cast, `rock`, `sleep`, `cinematics`.

---

### 3.14 `ward.corridor` The Corridor | effort L | P2

**Choice.** On to the courtyard (default, far end), or the pacing king, or answer the office phone, or (after the painter) the painted door.

| hotspot | anchor | what | success | failure | today |
| --- | --- | --- | --- | --- | --- |
| `.exit_courtyard` (default) | waypoint `corr_art_door` (32.4,6) | glazed end doors | courtyard | stagger | 24 m from home (a ring), dead ahead (0 degrees) |
| `.king` | actor `x06` (king a, pacing 1.2 m) at (10.8,5) | the pacing king | `wd_king`, bows you past (+6) | he will not be disturbed (-5) | behind the camera after the first step (177 degrees) |
| `.phone` | thing `phone_o` (0.9 m) at (27.6,0.7), the office | the office phone | `wd_phone_call` (+5) | dial tone (-3) | 117 degrees, 20 m |
| `.mural_door` (secret, `wd_painted`) | thing `mural_door` (2 m) at (24,7.85) | a painted door | route `ward.courtyard`, `wd_mural_open` (+8) | only paint, bump (-5) | 164 degrees, ring |

**View.** `corr_window` = `corr_mid` (17.25,5.25) yaw -90 (east); the good rail stops there (drop `corr_east`). Re-home the king to (21.0,4.6) (-10 degrees, 4 m, still pacing 1.2 m), the office phone to a desk in a window niche on the left wall (24.5,3.0) (-30 degrees, 8 m, enlarge to 1.1 m), the mural at (24.0,7.85) (+20 degrees, 7 m), the end doors dead ahead 15 m.

| option | embodiment and invitation | CURRENT vs NOT CURRENT | TOUCHED | COMMIT S / F |
| --- | --- | --- | --- | --- |
| end doors (default) | the glazed double doors (`door_ward`, glazed, garden light), a **chef** (`corridor_c04`, chef b) holding one leaf with a whisk in the other hand | CURRENT: leaves WIDE, courtyard dusk and fireflies visible beyond, chef `hold_door` `proud`. NOT CURRENT: AJAR | snap | S: chef `bow`, fireflies drift in. F: leaf swings, chef `recoil`, stagger |
| king (x06) | the king pacing, hands behind his back, paper crown | CURRENT: **stops dead, turns, `tip_hat` (the crown), then `sweep_arm` toward the end doors**, face `proud`. NOT CURRENT: pacing and glancing at you, `stare` with `resolve`; every 2 bars a haughty `smug` raised eyebrow | pacing halts on the beat | S (existing `king`): full `bow`, courtiers (corridor_c03 `salute`, c02 `kneel`) copy. F: `stamp`, `anger`, turns his back (`block`) |
| phone | an old black phone on a desk by the office window, **ringing** | CURRENT: the receiver **lifted off the cradle** hanging by the curly cord, the cord swinging. NOT CURRENT: ringing: receiver + bell hop on the beat (2 frame shake) | receiver pops up (frame) | S: the receiver settles in the air as if held, the cord still (someone is there: a muffled 'voice' drawn as three small notes `note_16` rising). F: the receiver drops and dangles, 'tone' as a thin flat line (decal) |
| mural door (secret) | the trompe l'oeil door on the right wall (`mural_door`) in the same style as the painter's canvas | CURRENT: the painted door's **real brass handle gleams**, a warm slit of courtyard light at its edge. NOT CURRENT (before `wd_painted` it is only a mural; after, it is ajar, the slit hairline) | slit widens | S (existing `mural_walk`): the painted door swings open into a real doorway. F (`mural_bump`): paint only, a flat bump (a squash frame), a flake falls |

**Default from beat 48.** Chef holding the end doors open; king pacing; phone ringing; mural quiet. **Create:** `door_ward` glazed variant, `mural_door` (3 frames), `phone_o` (3), `note_16`; acts `tip_hat`, `sweep_arm`, `hold_door`; faces `smug`, `proud`. **Exists:** corridor art, king and courtier acting, `corridor_end_glow`, `corridor_tubes`.

---

### 3.15 `ward.courtyard` The Courtyard | effort M | P2

**Choice.** On to the stage (default), or take the chef's plate, or bring the string lights up.

| hotspot | anchor | what | success | failure | today |
| --- | --- | --- | --- | --- | --- |
| `.exit_exit` (default) | waypoint `court_stage_door` (60.4,7) | the stage | ward.exit | stagger | at `stage_edge` 1 m, 180 degrees behind |
| `.chef` | actor `x01` (chef a, `serve`, pacing 2.2 m) at (57.8,8.8) | the chef | `wd_plate` (+6) | the plate lands on you (-5) | +48 degrees, 2 m |
| `.lights` | thing `lights_y` (string lights, 1 m wide at 2.9 m high) at (54,-1.5) | the festoon | `wd_lights` (+5, variation) | a fuse blows (-5, dip) | -58 degrees, 10 m, high |

**View.** `court_window` = `court_mid` (53.75,7.75) yaw -90 (east): stage door dead ahead 7 m, chef 4 m (+15 degrees), a new **fuse box on a post** at (57.0,3.2) (-30 degrees, 5.5 m) with the festoon running from it across the courtyard overhead. Good rail `[court_mid]`.

| option | embodiment and invitation | CURRENT vs NOT CURRENT | TOUCHED | COMMIT S / F |
| --- | --- | --- | --- | --- |
| stage (default) | the pallet stage (existing `riser`) with the **TALENT SHOW banner** (diegetic) and a **stage curtain** (`stage_curtain_wing`) | CURRENT: curtain **drawn open**, the spot pool on the boards, a **king** (`courtyard_c06`) `hold_door`-style holding the curtain edge and `beckon`ing, `happy`. NOT CURRENT: curtain closed (AJAR a hand when a side option is current), king `sulk` | curtain snaps (2 frames) | S: curtain flies wide, king `bow`, light rises. F: curtain drops on his head (a frame), he flaps, stagger |
| chef (x01) | chef pacing with a tray under a **cloche** (prop `cloche`) | CURRENT: stops, faces you, lifts the cloche (a **steam puff**), `offer`, face `proud`. NOT CURRENT: pacing, tray held high, face `hopeful`, a glance every 2 bars | pacing stops, cloche lifts (frame) | S (existing `plate`): `laugh`, plate offered, `courtyard_c01` `bow`. F (`plate_spill`): the tray tips, plate flies (`plate_fly`, 2 frames) and lands as a splat on the lens, chef `recoil` then `stamp` |
| festoon lights | the string lights on the cable and a **fuse box with a big lever** (`fuse_lever`) on the post | CURRENT: lever **UP**, the bulbs **chase** along the cable. NOT CURRENT: lever DOWN, the bulbs dim and flicker unevenly | lever clunks up (frame) | S: all bulbs on, a wave of light across the courtyard, fireflies lift. F: lever sparks (flash frame), a pop, the string goes dark, a thin smoke wisp |

**Default from beat 48.** Curtain open, king beckoning, chef pacing, lever down. **Create:** `stage_curtain_wing` (3 frames), `fuse_lever` (2) + `string_lights` states, prop `cloche`, `plate_fly`, `screen_splat` (shared), acts `hold_door`, `tip_hat`; faces `proud`, `sulk`. **Exists:** TALENT SHOW banner, `string_lights` piece, chef acting, `riser`.

---

### 3.16 `ward.exit` The Stage | effort L | P1

**Choice.** The end of the Ward: the left wing (back to the Hospital late, default), the right wing (the Ward again, late), or step into the cage lamp's spot for a star turn.

| hotspot | anchor | what | success | failure | today |
| --- | --- | --- | --- | --- | --- |
| `.exit_hospital_late` (default) | waypoint `stage_door_l` (62.6,4.6) | left wing | hospital_late | stagger | -76 degrees at the good place: out of frame |
| `.exit_ward_late` | waypoint `stage_door_r` (62.6,9.4) | right wing | ward_late | stagger | +76 degrees: out of frame |
| `.talent_lamp` | thing `cage_y` (cage lamp 0.45 m at 2.75 m high) at (64.8,7) | the stage lamp | `wd_star`, star turn (+10, variation) | `wd_lights_out` (-10, dip) | behind (180 degrees) |

**View.** The player stands on the stage facing the audience; everything is behind. Fix: `stage_window` ~(59.6,7.0) yaw -90 (facing the back of the stage): left wing (-35 degrees, 3.5 m), right wing (+35 degrees, 3.5 m), the lamp over centre stage (0 degrees, 5 m, +13 degrees up). Enlarge the lamp (0.9 m) and hang it on a boom.

**Design.** A pointer (G5): the **follow-spot**. The cage lamp throws a visible cone and pool that the lamp swings onto the current option (left wing, right wing, centre mark) in one beat.

| option | embodiment and invitation | CURRENT vs NOT CURRENT | TOUCHED | COMMIT S / F |
| --- | --- | --- | --- | --- |
| left wing (default) | a stage wing with a **curtain** (`stage_curtain_wing`) and an **orderly a** in scrubs (`courtyard_c03`, a hospital stand-in) at it | CURRENT: curtain open, spot pool on the wing, orderly `beckon` `happy`. NOT CURRENT: curtain drawn, orderly `sulk` | spot swings, curtain flips | S: orderly `cheer`. F: curtain drops, orderly `shame` |
| right wing | wing with a curtain and a **pirate** (`courtyard_c05`, pirate a) | same; pirate `sweep_arm`, face `proud` | same | S: pirate `bow`. F: curtain tangles, pirate `recoil` |
| cage lamp | the lamp itself and a chalk **X mark** (`stage_mark`, decal 32 x 32) on the centre boards | CURRENT: pool on the mark, lamp aimed down, filament bright, bulbs of the festoon sparkle, the crowd below `cheer`. NOT CURRENT: the cone sweeping idly across the audience | cone swings onto the mark | S (existing `star_turn`): spot locks, crowd `cheer`, confetti. F (`lights_out`): lamp pops, the whole stage drops to a dim rim, crowd `cover_face` |

**Default from beat 48.** The follow-spot is on the left wing, the orderly waving from an open curtain, the right wing closed with the pirate sulking. **Create:** `stage_curtain_wing` (shared with 3.15), `cagelamp_swing` (2), `stage_mark`, acts `sweep_arm`, `shrug`; faces `sulk`, `proud`, `hopeful`. **Exists:** `cage_y`, `riser`, courtyard people, `star_turn` cinematics.

---

### 3.17 `ward_late` The Courtyard (second round) | effort M | P1

**Choice.** Left to the treatment room (default) or right to the dormitory, or take the stage lamp's warmth, or let the fireflies settle.

| hotspot | anchor | what | success | failure | today |
| --- | --- | --- | --- | --- | --- |
| `.exit_treat` (default) | waypoint `court_door_w` (47.8,7) | the west door | ward_late.treat | stagger | 173 degrees behind at the good place |
| `.exit_dorm` | waypoint `court_south` (53,12), an open spot, not a door | the south path | ward_late.dorm | stagger | -100 degrees |
| `.stage_lamp` | thing `cage_y` | the stage lamp | warms the courtyard (+8, variation) | blinds you (-6, dip) | behind (180 degrees) at home |
| `.fireflies` | thing `flies_y` (3 m swarm) at (55,6) | the fireflies | `wl_fireflies` (+6) | scatter (-4) | in front but a swarm of dots |

**View.** `court_late_window` ~(59.4,7.0) yaw 90 (west): treat door dead ahead 12 m (a clinical door, `door_ward` treat variant), a **new garden gate** at (53,12) rebuilt as a gate in the south wall (`garden_gate`, ward style, moon plate: +35 degrees, 8 m), fireflies centre-left (-12 degrees, 5 m), and a **second cage lamp on a pole** `cage_p` at (54.5,3.0) (-35 degrees, 6.5 m) so the lamp is in front (the hotspot's anchor moves to `cage_p`).

| option | embodiment and invitation | CURRENT vs NOT CURRENT | TOUCHED | COMMIT S / F |
| --- | --- | --- | --- | --- |
| treat door (default) | clinical door (`door_ward`, plate: a sun, `plates_icons`), an **orderly b** (`courtyard_l01`) with a clipboard in it | CURRENT: WIDE, white light, orderly `beckon` `happy`. NOT CURRENT: SHUT + chain, orderly `write`, `sulk` | snap | S: orderly `nod`. F: door rebound, orderly `recoil` |
| dorm gate | garden gate (moon plate), the **sleepy usher** with the pillow | CURRENT: gate WIDE, blue night glow, usher `stretch`, `yawn`. NOT CURRENT: latched, usher slumped | snap | S: usher `relief`. F: latch drops, usher `shame` |
| stage lamp (`cage_p`) | the pole lamp, dark with a swinging chain | CURRENT: swung onto the centre, warm cone on the ground, filament bright. NOT CURRENT: hangs down and swings idly, dark | cone snaps | S: courtyard warms (palette lift), people `relief`. F: white flash over the frame (`flash_white`), people `cover_face`, then dark |
| fireflies | the swarm over the beds | CURRENT: the swarm **gathers into a loose ring around the lens** on the beat. NOT CURRENT: scattered high, flickering | ring forms | S: motes settle on the edge of the frame and glow softly. F: they scatter outward with a flutter |

**Default from beat 48.** Treat door open with the orderly, gate latched with the usher slumped, lamp idle, fireflies high. **Create:** `door_ward` (treat plate), `garden_gate` (ward style), `cage_p` (pole lamp: 2 frames), `firefly_swarm` (3 states), `flash_white`, `plates_icons` (sun); NPC `sleepy_usher` (shared); acts `stretch`, `write` exists; faces `yawn`, `sulk`, `proud`. **Exists:** fireflies piece, cage lamp art, orderly.

---

### 3.18 `ward_late.treat` The Treatment Room | effort M | P3

**Choice.** Out (default), or the orderly checks the clipboard (a nod, or a needle), or the trolley (a gift, or it rattles away).

| hotspot | anchor | what | success | failure | today |
| --- | --- | --- | --- | --- | --- |
| `.exit_exit` (default) | waypoint `treat_door` (16,8.6) | the door | exit | stagger | 180 degrees behind at the good place |
| `.orderly` | actor `x02` (orderly b) at (17.3,11.4) | the orderly | `wl_orderly_ok` (+4) | `ward_late.injection` (-9, dip) | 155 degrees behind |
| `.trolley` | thing `trolley_t` (0.9 m) at (18.2,13.2) | the trolley | (+6) | (-5) | 154 degrees behind |

**View.** `treat_window` ~(16.0,10.0) yaw 180 (home, facing +z); the exit is moved to a swing door on the far wall (new waypoint `treat_door_far` (16,15.4), dead ahead 5.4 m), orderly right (+30 degrees, 2.5 m), trolley left (-30 degrees, 3.5 m).

| option | embodiment and invitation | CURRENT vs NOT CURRENT | TOUCHED | COMMIT S / F |
| --- | --- | --- | --- | --- |
| swing door (default) | a pair of rubber-edged swing doors (`door_ward`, double) with a **pirate** (`x03`) holding one leaf | CURRENT: WIDE, the next room visible, pirate `hold_door`, `happy`. NOT CURRENT: SHUT, sign (`wetfloor_a`), pirate `shrug` | snap | S: pirate `bow`. F: leaf swings back |
| orderly (x02) | writing on the clipboard beside a **wall chart** (a tick-box sheet pinned up) | CURRENT: looks up, **clipboard turned to you showing a big drawn tick**, `nod`, `beckon` with the pen, `happy`. NOT CURRENT: `write`, face neutral, brow furrow (`doubt`) | clipboard flips | S (existing `orderly`): tick stays, `nod`. F: tone: show the injection as a **plaster-and-lollipop jab** (a cartoon plaster frame near the lens, the orderly `recoil`ing apologetically); keep the existing dip |
| trolley | trolley with a **cloth over something box-shaped**, a small bell on the handle | CURRENT: cloth **lifted** to show a gift box with a ribbon, bell ringing. NOT CURRENT: covered, one bell tinkle every 2 bars | cloth lifts (frame) | S: the box opens on a paper star (`paper_stars` piece pulse). F: the trolley **rattles away** through the swing door (a motion blur frame), the box left behind |

**Default from beat 48.** Pirate holding the swing door; orderly writing; trolley covered. **Create:** `door_ward` double, `trolley_gift` (3), `wall_chart` (64 x 64), `plaster_jab` (small overlay); acts `write`; faces `doubt`; no new NPC (pirate `x03`).

---

### 3.19 `ward_late.dorm` The Dormitory (second round) | effort S | P3

Same room and kit as 3.13 (the sleeper and cabinet exist as `x13`/`x14` and `cab_m1` at (30.5,8.35)): the sleeper in the other bed is **x13** (curly b, now the sleeper, `wl_lullaby`) and the awake neighbour who signals is **x14** (punk b), so the roles are swapped between rounds. The cabinet `cab_m1` is on the east side of the door. `wl_cabinet` and `wl_lullaby` are separate flags from round one; **if `wd_dorm_key` is set, the cabinet shows the key gone and a small empty hook** (a visible memory) and its CURRENT pose is a rattling drawer. Same `dorm_window`, same default (usher at the open door). **Create:** nothing beyond 3.13 except `cabinet_m` frame "empty hook".

---

### 3.20 `ward_late.exit` The Day Room (second round) | effort S | P1

**Choice.** Round again to the Ward's courtyard (default, door A) or across to the Hospital's garden (door B), or join x09 at the window.

| hotspot | anchor | what | success | failure | today |
| --- | --- | --- | --- | --- | --- |
| `.exit_ward_late` (default) | waypoint `day_door_a` | door A | ward_late (loop) | stagger | +30 degrees at 13 m, on top of B |
| `.exit_hospital_late` | waypoint `day_door_b` | door B | hospital_late | stagger | +34 degrees |
| `.stare` | actor `x09` (bob a) at (5.2,-1.4) | the man staring at the window | `wl_window` (+5) | he turns away (-5) | +62 degrees: edge beacon |

**View.** As 3.11 (`ward_window`), with door B moved to the north end and the window as the stage for x09: x09 stands at the window (6.6,3.4 after the move) in front of the sash. **Design.** Doors as 3.11 but with the late twist: **door A (loop) has a looped paper-chain wreath** (`wreath_loop`, a ring of paper stars: "round again") on it; **door B is the Hospital's door**, a hospital-teal `door_hosp` leaf with a heart plate and a **nurse stand-in** (`orderly a`, scrubs) in the doorway, so the foreign world's door looks foreign. x09: NOT CURRENT: back to you, staring out of the sash window (existing `stare`, face neutral); CURRENT: turns to you, `point` at the window, face `awe`, the sash opening a hand (`window_sash_w`); S (existing `stare`): arms up in wonder (`cheer`, `awe`), beam sweeps; F: he turns away with `stamp`, face `anger`, the sash slams. Default at beat 48: door A WIDE with the painter holding it. **Create:** `wreath_loop` (shared with 3.10), `door_hosp` (shared); acts `sweep_arm`; nothing else.

## 4. New assets and expressions (roll-up)

Sizes: tile = 128 x 128 px, small = 64 x 64, plate = 32 x 32, sign = 128 x 64, tiny = 16 x 16, overlay = 320 x 180 px drawn at 4x like `fluoro_wash`. "f" = state frames (siblings, G4). Scenes use the section 3 numbers.

### 4.1 Objects and set pieces (47 sprite sets + 2 overlays, about 145 frames)

| key | what | size | frames | used in |
| --- | --- | --- | --- | --- |
| `door_hosp` | hospital door (teal, paper heart, porthole): single, double, glass, quiet (crack frame) variants | tile | 10 (shut, ajar, wide each; +1 crack) | 3.1 3.2 3.7 3.9 3.10 3.20 |
| `door_ward` | ward door (lilac/mint, round porthole, paper stars): single, glazed, double | tile | 9 | 3.11 3.12 3.13 3.14 3.17 3.18 3.19 |
| `french_door_h` | glazed garden door, dusk glow | tile | 3 | 3.3 3.4 3.8 |
| `garden_gate` | gate with lanterns: hospital style and ward style (paper chain, moon plate) | tile | 6 | 3.5 3.6 3.10 3.17 |
| `plates_icons` | pictogram plates: tv, cup, tree, palette, moon, sun, heart, mic, bed, key | plate | 10 (one sheet) | all doors |
| `wetfloor_a` | A-frame caution sign: standing / folded flat | small | 2 | 3.1 3.2 3.7 3.18 |
| `paperchain_gate` | paper-chain barrier: strung across / dropped on the floor | sign | 2 | 3.11 3.12 3.13 3.14 3.17 3.19 3.20 |
| `finger_post` | ceiling-hung two-icon board with pivoting arrow: left / centre / right | sign | 3 | 3.2 |
| `wheelchair_h`, `wheelchair_w` | wheelchair: brake on + blanket folded / brake off + blanket spread (hospital); parked (ward) | tile | 2 + 1 | 3.1, 3.11 |
| `balloons_tether` | balloon bunch: tied low / held high | tile | 2 | 3.1 |
| `monitor_h` | heart monitor on a stand: idle / beat-synced spikes / flat | small | 3 (+ loop) | 3.1 |
| `tea_trolley_h` | tea trolley: rolling / pouring with steam / spill | tile | 3 | 3.2 |
| `keypad_reader` | keycard reader by the quiet door | plate | 2 | 3.2 |
| `tv_set_h` | wall TV: rolling static / show A / show B / snow burst | tile (wall) | 4 | 3.3 |
| `wall_clock_fast` | clock whose hands whirr | small | 2 | 3.3 |
| `vending_h` | vending machine: idle chase / primed (packet on the lip) / jam | tile | 3 | 3.4 3.8 |
| `token_16` | brass ridged token and its coin-slot icon | tiny | 2 | 3.4 3.8 |
| `lamppost_h` | lamppost: dark / flicker / steady with moths / lit_b star burst / popped | tile | 6 | 3.5 3.7 |
| `mic_stand` | mic: idle (cable twitch) / primed (tilted) / feedback ring | tile | 3 | 3.6 3.10 |
| `bouquet_stage`, `wreath_loop` | encore bouquet on the stand; "round again" wreath of paper stars | small | 1 + 1 | 3.10, 3.20 |
| `nightlight_moon`, `nightlight_star` + wall projections | night lights: off / ember / bright; moon and star shapes projected on the wall | small, 128 tile | 6 + 2 | 3.9 |
| `window_sash_w`, `bird_sill` | ward window: sash down / up with curtain billow / slammed; a bird on the sill | tile, tiny | 3 + 2 | 3.11 3.20 |
| `painter_canvas`, `easel_canvas` | the painter's canvas: smears / painted door / handle gleam; spare easel: cloth / primed + dripping brush / painting / smudge | tile | 3 + 4 | 3.12 |
| `mural_door` | corridor trompe l'oeil door: mural / ajar with gleaming handle / flat bump | tile | 3 | 3.12 3.14 |
| `phone_o`, `note_16` | office phone: ring A / ring B / receiver lifted / dangling; three rising notes | small, tiny | 4 + 1 | 3.14 |
| `sleeper_mobile` | moon-and-stars mobile: still + 3 rotation frames | tile | 4 | 3.13 3.19 |
| `alarm_bell` | wall bell: still / ringing | small | 2 | 3.13 3.19 |
| `cabinet_m`, `key_16` | cabinet: closed / ajar key A / ajar key B / empty hook; a brass key | tile, tiny | 4 + 1 | 3.13 3.19 |
| `fuse_lever`, festoon chase | fuse box lever: down / up; string lights chase (2 frame additive loop) | small | 2 + 2 | 3.15 |
| `stage_curtain_wing` | stage wing curtain: drawn / half / open (mirrored L/R) | tile | 3 | 3.15 3.16 |
| `cagelamp_swing`, `cage_p` | cage lamp: hangs / aimed with cone; the same on a pole | tile | 2 + 2 | 3.16 3.17 |
| `stage_mark` | chalk X on the boards (floor mark) | plate | 1 | 3.16 |
| `trolley_gift`, `wall_chart` | trolley: covered / cloth lifted with gift / rolled away; a tick-box chart | tile, small | 3 + 1 | 3.18 |
| `firefly_swarm` | the swarm: scattered / ring / settled (additive) | tile | 3 | 3.17 |
| `plate_fly`, `plaster_jab` | the chef's flying plate; a cartoon plaster for the jab | plate, small | 2 + 1 | 3.15 3.18 |
| `screen_splat`, `flash_white` | lens overlays: paint splat; white flash (reduced effects: no flash, a held tint) | overlay | 1 + 1 | 3.12 3.15 3.17 |

### 4.2 People

* **New wardrobe looks (3):** `bandleader` (hospital, dad variant c: peaked cap, braided jacket; prop `baton`), `crowned_visitor` (hospital: dad b with a paper crown and a dressing gown), `sleepy_usher` (ward: dressing gown, nightcap, pillow; unique `look_key` in its room).
* **Existing crowd people promoted to directed ushers (15, no new body):** hospital `c08`, `h04`, `corridor_c10`, `corridor_c08`, `cafeteria_c06`, `garden_c10`, `garden_c04`; ward `c10`, `art_room_c07`, `corridor_c04`, `courtyard_c06`, `courtyard_c03`, `courtyard_c05`, `courtyard_l01`, `x03`. Each needs a re-home at its door and an `acting` block (available = NOT CURRENT, selected = CURRENT) and gets its directed sheets baked (`directed_actors` follows the data; budget +15 % per chapter sheet, `check_assets.py` enforces).
* **New props held (4):** `baton`, `pillow`, `sweet_tin`, `cloche`; plus a lit/dark screen frame for the existing `phone`.

### 4.3 Faces (7 new on top of the 14)

| face | what it looks like at the pixel rig (17 x 13 head) | scenes |
| --- | --- | --- |
| `hopeful` | brows raised in the middle, eyes wide and looking at the camera, a small closed smile with one corner lifted; no blush | 3.1 3.2 3.3 3.4 3.5 3.6 3.7 3.11 3.12 3.13 3.17 (the NOT CURRENT invitation) |
| `sulk` | brows flat and low, eyes slid away to one side, lower lip pushed out, one cheek puffed | every usher at a shut door (3.1 to 3.20) |
| `worry` | brows knit with the inner ends up, small wavy mouth, no tear (milder than `fear`) | 3.1 3.3 3.5 |
| `smug` | one brow high, upper lids half down, a one-sided smirk | 3.14 (the king) |
| `wink` | one eye closed, wide grin, cheek lifted | 3.4 3.8 (the kid) |
| `yawn` | eyes shut, mouth a tall oval, head tipped back a pixel | 3.11 3.13 3.17 (the sleepy usher) |
| `proud` | chin up one pixel, eyes half-closed in a soft smile, brows lifted, chest out (act decides) | 3.2 3.6 3.11 3.12 3.14 3.15 3.16 3.17 |

LOD 4 fallbacks: `hopeful` to `happy`, `sulk` to `sad`, `worry` to `sad`, `smug` to `neutral`, `wink` to `happy`, `yawn` to `neutral`, `proud` to `happy`.

### 4.4 Acts (14 new on top of the 15 and the older states)

| act | pose (cycle in beats, frames) | reads as | scenes |
| --- | --- | --- | --- |
| `hold_door` | one arm out to the side pressing an invisible leaf at head height, leaning toward the camera, the other hand free to beckon (4, 4) | "I'm holding it for you" | 3.1 3.2 3.3 3.4 3.7 3.11 3.12 3.13 3.14 3.15 3.18 |
| `sweep_arm` | an arm swept from the chest outward and held toward a target, a small bow of the head (2, 6) | "after you / this way" | 3.6 3.11 3.14 3.16 3.20 |
| `shrug` | shoulders up, palms up, head tilt (2, 4) | "not me" (NOT CURRENT usher) | 3.1 3.2 3.6 3.10 3.11 3.12 3.16 3.18 |
| `shush` | one finger to the lips, the other hand patting the air down (4, 4) | quiet | 3.2 3.7 3.9 3.13 |
| `tip_hat` | two fingers to the brim, hat or crown, nod (2, 4) | greeting from the king, a cap, a crown | 3.14 3.15 |
| `pour` | tilt a jug over the mug held in the other hand (4, 6) | tea | 3.2 |
| `pat_seat` | pats the seat beside her twice, leans in (2, 4) | "sit with me" | 3.3 |
| `stretch` | both arms up with a yawn, then a lazy beckon (4, 6) | sleepy welcome | 3.11 3.13 3.17 |
| `push` | both hands forward on handles, walking lean (2, 8, loops) | the wheelchair ride | 3.1 |
| `tap_watch` | taps a wrist, impatient weight shift (2, 4) | "hurry up" | 3.11 |
| `wring_hands` | hands twisting at the chest, weight shifting (4, 4) | family worry | 3.1 |
| `hop` | a small jump, arms out, land (1, 4) | the kid's trick | 3.4 3.8 |
| `flick` | a quick wrist flick (brush, a slap on the TV) (1, 3) | paint flick, tap on a set | 3.3 3.12 |
| `sit_up` | from `sleep` or `lie` to sitting up with a jolt (2, 6) | woken | 3.13 3.19 |

Also needed (existing acts with a prop that does not exist yet): `point` with `baton` (3.6), `offer` with `sweet_tin`, `cloche`, `phone` screen lit, `serve` with a cloche (3.15).

### 4.5 Animations (the moving parts, each a loop or a one-shot on the beat)

1. Door swing: shut to ajar to wide, 3 frames across half a beat, plus a rebound on failure (6 frames).
2. Finger-post arrow swing, 3 frames over one beat.
3. Beat-synced heart trace: a spike on every beat; flatline hold.
4. TV: rolling static (4 frame loop), show loop (2 frames per beat), snow burst.
5. Festoon chase: a bright bulb running along the cable (8 frame loop).
6. Moth ring around the lamp (4 frame loop); firefly ring around the lens (4 frames).
7. Mobile rotation (4 frames per 2 bars).
8. Tea trolley: rolls away (loop) to stops dead (1 frame) to pour (4 frames).
9. Follow-spot swing between three targets (a cone that eases 2 frames in one beat).
10. Night-light breathing: glow pulse once per bar, half-time for the second light.
11. Steam puff (cafeteria nurse, cloche): 4 frame loop, additive (reuse `cafeteria_steam`).
12. Paint drip: a bead each beat from the brush (3 frame loop).
13. Curtain flip (3 frames), chain drop (2 frames), lever clunk (2 frames), bell shake (2 frames), receiver hop (2 frames), key swing (2 frames).
14. Idle tells, one per option, staggered by bar: nurse glances, trolley bell tinkle, TV bar roll, vending tile chase, phone ring shake, window rattle, squeal ring on the mic.

### 4.6 Counts

| kind | count |
| --- | --- |
| object / set piece sprite sets | 47 (about 145 frames) |
| lens overlays | 2 |
| new wardrobe looks | 3 |
| crowd people promoted to directed ushers | 15 |
| new held props | 4 (+ 1 prop frame) |
| new faces | 7 |
| new acts | 14 |
| named animations | 14 groups |
| new waypoints (window places) and one door anchor | 14 + 1 (listed in 5.2) |
| map re-homes (things and people moved to suit the window view) | about 30, in 17 scenes |
| **New assets, faces and acts proposed** | **47 objects + 2 overlays + 3 looks + 4 props + 7 faces + 14 acts = 77** |

### 4.7 Work packages (so implementers can work separately)

* **WP-A Doors, gates, barriers:** `door_hosp`, `door_ward`, `french_door_h`, `garden_gate`, `plates_icons`, `wetfloor_a`, `paperchain_gate`, `stage_curtain_wing`, `finger_post`, `keypad_reader` (serves all 20 scenes; the shared route rule).
* **WP-B Hospital objects:** `wheelchair_h`, `balloons_tether`, `monitor_h`, `tea_trolley_h`, `tv_set_h`, `wall_clock_fast`, `vending_h`, `token_16`, `lamppost_h`, `mic_stand`, `bouquet_stage`, `wreath_loop`, `nightlight_*`.
* **WP-C Ward objects:** `wheelchair_w`, `window_sash_w`, `bird_sill`, `painter_canvas`, `easel_canvas`, `mural_door`, `phone_o`, `note_16`, `sleeper_mobile`, `alarm_bell`, `cabinet_m`, `key_16`, `fuse_lever`, festoon chase, `cagelamp_swing`, `cage_p`, `stage_mark`, `trolley_gift`, `wall_chart`, `plaster_jab`, `firefly_swarm`, `plate_fly`, overlays.
* **WP-D People:** 7 faces, 14 acts, 4 props, 3 looks, the 15 re-homes and their `acting` blocks (`tools/run/acting_data.py`).
* **WP-E Engine and rail:** section 5.1 and 5.2.
* **WP-F Map and data:** moves of things and people and the new hotspot anchors, regenerated through the map generator and `tools/run/make_hotspots.py`, then `tools/run/check_hotspots.py`.

## 5. Cross-cutting issues

### 5.1 Engine needs (assume the generic "current choice" engine; these are the additions this world needs)

1. **A staging block on every hotspot (things as well as people).** `acting` exists for people only. Add `staging: {available, selected, committed, success, failure}` each `{on: [piece ids], off: [piece ids]}` so a thing's state frames switch with the hotspot's phase and not only with an outcome (the engine already has `pieces`; this adds phases). Needed by every scene.
2. **`available` = NOT CURRENT, `selected` = CURRENT, and the default is `selected` from beat 48 without a touch**, so the default exit's usher and door are already in the CURRENT pose in the first beat of the window. Touching another option sends the previous one back to `available` in the same beat.
3. **Route rule input:** expose `route_if(current)` (the route the current option ends in: its own for an exit, the default's for a side option) so a door can be WIDE, AJAR or SHUT (G2). Needed by all 20 scenes (every scene has an exit).
4. **Idle tells** scheduled per option, staggered by bar (G3, G4): a per-hotspot `tell: {every_bars, piece or act}`.
5. **Pointer devices** (finger-post, baton, follow-spot) are not hotspots: give them a `follows_current: {a: piece, b: piece, c: piece}` table that picks the pointer's frame from the current option. Scenes 3.2, 3.6, 3.10, 3.16.
6. **Touch target = the whole embodiment** (the person plus the door leaf, the lever plus the lamp it drives) and no ring is required; keep the existing ring only as a fallback. A touch on an usher selects the door's hotspot.
7. **Ground decal** thing kind for flat marks (`stage_mark`, optional corridor guide chevrons). Without it use a low billboard.
8. **Persistent memory pieces:** props that show a flag (the encore bouquet `hp_sang`, the key gone `wd_dorm_key`, the token `hp_token`, the painted door `wd_painted`) via `if_flags_all` on a piece, as cast lines already can.
9. **Reduced effects:** `flash_white` and `screen_splat` must obey `reduced` (a held tint, no flash).
10. **Optional gaze lean:** on a touch the window glance leans up to 8 degrees (the existing cap `WINDOW_GLANCE_DEG`) toward the new current option; never pitched.

### 5.2 Camera and rail: the window place per scene (new waypoints; all approximate, to be tuned on `tools/run/capture.sh`)

| scene | new waypoint (map) | approx. place and yaw | what it fixes |
| --- | --- | --- | --- |
| `hospital` | `bed_window` (hospital) | (0.6,4.2) -15 | stops standing in the doorway with the room behind |
| `hospital.corridor` | `corridor_window` | (12.6,0.9) -90 | stops the rail walking past both doors |
| `hospital.dayroom` | `dayroom_window` + door anchor `dayroom_garden_door` | (19.2,-4.2) +10; door (23.6,-8.5) | the blurred TV and the exit that is the entry door |
| `hospital.cafeteria` | `cafe_window` | (41.0,1.0) -90 | window-facing view |
| `hospital.garden` | `garden_window` | (51.0,1.0) -90 | far lamp and mum |
| `hospital.exit`, `hospital_late.exit` | `bandstand_window` | (56.5,1.0) -90 | player no longer faces away from the stage |
| `hospital_late` | `garden_late_window` | (52.5,2.0) +90 | rail turned the camera away from both doors |
| `hospital_late.cafe` | `cafe_window` (shared) | | machine and kid behind |
| `hospital_late.quiet` | `quiet_window` | (14.2,14.0) 0 | window blur and a door behind |
| `ward`, `ward_late.exit` | `ward_window` (ward map) | (0.0,4.0) -90 | two doors 1.8 m apart on one wall |
| `ward.art` | `art_window` | (41.0,7.0) +90 | easel under the feet |
| `ward.dorm`, `ward_late.dorm` | `dorm_window` | (26.0,14.2) 0 | dark room, everything behind |
| `ward.corridor` | none (use `corr_mid`) | stop the rail there | rail overshoots to `corr_east` |
| `ward.courtyard` | none (use `court_mid`) | yaw -90 | camera on the stage looking away |
| `ward.exit` | `stage_window` | (59.6,7.0) -90 | player faces the audience, everything behind |
| `ward_late` | `court_late_window` | (59.4,7.0) +90 | treat door and gate behind |
| `ward_late.treat` | `treat_door_far` (exit moved to a far swing door) | (16.0,15.4) | exit behind the camera |

The rail's `exits` (the lit doorway of each route) must name the same doors as the hotspots; `RunData` already checks every doorway exists in the map.

### 5.3 Shared pieces reused across scenes (build once)

* The **door set** (`door_hosp`, `door_ward`, `french_door_h`, `garden_gate`) with a plate sheet and the two barriers (`wetfloor_a` for the Hospital, `paperchain_gate` for the Ward) serves all 20 scenes: it is the route rule.
* The **usher** is one grammar (G3): the same `hold_door`, `shrug`, `sulk`/`hopeful` on 15 promoted crowd people.
* The **sleepy usher** is shared by `ward`, `ward.dorm`, `ward_late` and `ward_late.dorm` (4 scenes).
* Hospital forks reuse each other: the bandstand (3.6) is reused whole by 3.10; the cafeteria (3.4) by 3.8; the garden lamp (3.5) by 3.7; the dorm (3.13) by 3.19; the Ward day room (3.11) by 3.20 (with the loop wreath).
* Mirrored kits across worlds: the follow-spot (Ward stage) and the conductor's baton (bandstand) are the same device (G5) in two settings; the lever (courtyard) and the finger-post (corridor) are the same "one pointer" idea.

### 5.4 Risks and judgement calls

* **Tone.** The Ward is "kind, whimsical, nobody menacing" (`docs/STORY_ART.md`): the `to_treatment` carry, the injection and the barred window are the three darkest outcomes. The briefs soften them (wheelchair, a plaster and a lollipop, glazing bars on a sash window) but the data and the cinematics still say needle and bars; the owner should decide.
* **Dark rooms.** `ward.dorm`, `ward_late.dorm` and the Ward courtyard are nearly black in the contact sheets: each design adds a visible light (moon spill, floor lamp, night light) so the options read; the light levels are the tuning risk.
* **Distance.** People read at 7 m or less (the new faces fall back to the old ones beyond LOD 2): the corridor's cafeteria usher is therefore brought to 7 m; check every re-home against that.
* **Colour independence.** Every CURRENT versus NOT CURRENT pair differs by shape (open, shut, held, folded, raised, lowered) and pose, never only by tint: verify each scene's capture in greyscale.
* **Count of moving parts.** 4 options means 4 idle tells; stagger them (5.1 item 4) so the window does not shimmer with simultaneous noise; and the falling notes cover the outer lanes, so keep everything in x 220 to 1060.
* **Numbers are approximate.** Coordinates and bearings come from `content/story/maps/{hospital,mental_hospital}.json` waypoints and homes and a flat bearing calculation (`StoryMap.forward_of_yaw`, FOV_V 52); they were not tested in a live capture. The window poses and re-homes are proposals to be tuned on `tools/run/capture.sh`.
