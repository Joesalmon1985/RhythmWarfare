# The Bassment: choice briefs (visual representation of every branching point)

Owner verdict being answered: the branching must be *seen in the world* (NPCs, objects, doors), with the default and the "press to change" obvious, and not only as light. Scope: all 64 passages of `content/trial/passages.json` (0 to 63), 95 hotspots in `content/trial/hotspots.json`. Documents only; nothing here is built.

## 0. Read this first

**Assumed engine** (the other agent's generic engine): at any time exactly one option of a passage is CURRENT; it starts as the default; a touch on an option's thing makes it CURRENT within one beat; it can change until the commit tick (beat 12.75 of the 16-beat window). A failed plain phrase keeps you in the room and the failed option becomes the default (so it is CURRENT again on retry).

**Facts this brief relies on (measured from the repo)**
* Picture = the area above the pads: 1280x460 of 1280x720 in `docs/shots/trial/*.png` (about 64 % of the height), vertical FOV 52 degrees (`StoryProjector.FOV_V`), so horizontal half-view is about 53 degrees on that frame. The world renders at 360 internal lines and is shown with nearest filtering. The pad strip hides the lower 36 % of the window: floor decals only show beyond about 3 m, and a prop's identifying detail must sit in the upper two thirds of its sprite.
* Art scale: textures, props and creature figures are 128x128 RGBA (`assets/story/bassment/textures/`, drawn by `tools/story/art/tex_bassment.py` and `tools/trial/make_creatures.py`); props are billboards sized 0.5 to 5 m with `anim` in none|pulse|flicker|rotate|bob|sway|pump. A creature figure today is **one** portrait with 3 frames (`idle`, `attack`, `struck`) and motion by translate/squash only (`RunActing.figure_motion`: block, offer, laugh, stamp, recoil, bow, collapse, shake_head, nod, plead, stare). There are no faces or limbs on creatures; "faces" for them mean baked frames.
* Beat length is 0.345 s at 174 BPM and 0.69 s at the dungeon's 87-BPM ambient profile. Every state change below is at most 3 frames at 12 fps (0.25 s), so it lands inside one beat either way.
* Today every option is drawn the same way: a soft additive orb (`thing_glow`) on the anchor plus a floor ellipse, brighter on the default (`docs/shots/trial/select_after.png`, `zone_*.png`). The Bassment shows no caption band in play. Nothing in the room differs between options.
* Camera bearings were computed per hotspot from `waypoint` (cam position and yaw) to anchor, negative = left. Rule used below: option carriers within +/-30 degrees and 2.5 to 6 m of the camera, at least 1.6 m tall (about 70 px on a phone picture), no two carriers within 12 degrees of each other.

**Coverage check (script, run against `content/trial/hotspots.json`)**: see section 6. 64 of 64 passages, 95 of 95 hotspots.

## 1. Summary table: the 27 branching passages (2 or more hotspots)

D = default. "Today" is blunt and refers to what a player sees now. Archetypes: **A** usher fork, **B** physical path states (door barred/ajar, bridge raised/lowered, plug in/out), **C** creature or character whose pose encodes the current option, **D** safe path vs hazard stunt, **E** curiosity/object beside a way on. Effort S/M/L, priority P1 (teaches the grammar, or a trap passage, or the owner's own example), P2 (rest of the default walk), P3 (off the default walk).

| Passage (zone) | Options (hotspot id: option, kind) | Today | Arch | Eff | Pri |
| --- | --- | --- | --- | --- | --- |
| 1 Service Hatch (hatch) | `trial.1.0` climb the ladder (D, exit); `trial.1.1` read the chalk marks (exit) | Weak: two orbs in a dark shaft; the ladder is 4 stacked ladder sprites, "chalk" is a 0.5 m hand sprite; nothing says which is which. The first choice teaches nothing. | A (tutorial) | M | P1 |
| 3 Ladder Foot (hatch) | `trial.3.0` cables (D, exit); `trial.3.1` warm stairs (exit) | Unreadable: both anchors are bare waypoints 5.9 m away at -36 and +36 degrees with no prop near either. | A | M | P1 |
| 4 Cable Run (cables) | `trial.4.0` thickest cable (D, exit); `trial.4.1` LOST PROPERTY door (exit) | Overlap: bearings -6 and +5 degrees; cable `cab_b` and `door_lp` are 0.8 m apart; two orbs on top of each other. | B | M | P1 |
| 5 Live Junction (cables) | `trial.5.0` edge past (D, exit); `trial.5.1` dash under (feature, luck, fail 6) | Misleading: the dash is anchored to `junc2`, a 0.6 m **valve** sprite standing in for a junction box; the safe way is bare floor. | D | M | P2 |
| 8 Lost Property (cloakroom) | `trial.8.0` shoo the moth (encounter, fight); `trial.8.1` close the door and leave (D, exit) | Weak: moth portrait on the lamp is fine; the door is a plain 2.2 m door with an orb. Moth looks equally hostile whichever is picked. | C | S | P3 |
| 10 Warm Stairs (boiler) | `trial.10.0` wade in (D, exit); `trial.10.1` haul on the valve wheel (exit) | Unreadable: bare waypoints 27 degrees apart, a 1.1 m valve 0.6 m from one of them. | B | M | P3 |
| 12 Flooded Boiler Room (boiler) | `trial.12.0` fight the eel (D, encounter); `trial.12.1` climb the pipes (feature, luck, fail 13 = death) | Misleading: the pipe climb is anchored to `valve2`, a 0.9 m valve wheel at -41 degrees, 6.5 m away, at the screen edge. | C | M | P3 |
| 15 Crystal Stacks (stacks) | `trial.15.0` lit path (D, exit); `trial.15.1` terraces (exit) | Unreadable: anchors 10.2 m and 15.8 m away in a big cave, only a 1.4 m shard near each. | A | M | P2 |
| 16 Humming Hall (stacks) | `trial.16.0` walk on (D, exit); `trial.16.1` tap the cracked crystal (object, grants token) | Weak: the cracked crystal is a good 4.4 m sprite but never changes; the cellar door is 10 m off. | E | M | P2 |
| 18 Crystal Terraces (stacks) | `trial.18.0` cross the rope bridge (exit); `trial.18.1` climb back down (D, exit) | Unreadable: there is no bridge in the room; both anchors are bare waypoints (9.2 m and 5.6 m). | B | M | P3 |
| 20 Barrel Cellar (cellar) | `trial.20.0` challenge the knight (D, encounter); `trial.20.1` creep between the barrels (feature, luck, fail 22 = death); `trial.20.2` sit at the bar (exit) | Bad: three options; the luck test is a lone 1 m barrel `bar_g` 8.4 m away at -38 degrees, the stool a 0.9 m barrel at +28 degrees, 8.8 m away. | C | L | P1 |
| 23 Behind the Counter (cellar) | `trial.23.0` open the trapdoor (D, exit); `trial.23.1` lamp + dark archway (object, needs lamp) | Weak: orb 1.7 m from a ladder; the "dark archway" is `arch_door`, a door sprite. | B | M | P2 |
| 26 Fungus Farm (fungus) | `trial.26.0` stepping stones (D, exit); `trial.26.1` eat a glowing cap (exit) | Unreadable: stones are a bare waypoint 11.2 m away; cap is a 1.9 m mushroom at -39 degrees. | E | M | P2 |
| 28 Mildew Pond (fungus) | `trial.28.0` stand against the Mildew Mother (D, encounter); `trial.28.1` back away to the haze (exit) | Weak: Mother is a static portrait; the haze is a bare waypoint at -36 degrees. | C | M | P2 |
| 30 Mirror Mezzanine (mirrors) | `trial.30.0` centre aisle (D, exit); `trial.30.1` follow the waving reflection (exit) | Unreadable: two bare waypoints; there is no waving reflection anywhere in the map. | E | M | P2 |
| 32 Twin Steps Out (mirrors) | `trial.32.0` face your twin (D, encounter); `trial.32.1` turn your back (feature, luck, fail 33 = death) | **Worst**: twin fills the view at 1.6 m; the "turn your back" thing `hs_mirror` is a 0.05 m invisible marker, so a lone orb floats in empty air. | C | L | P1 |
| 35 Reverb Pit (pit) | `trial.35.0` climb down the rope (D, exit); `trial.35.1` shout into the pit (exit) | Unreadable: bare waypoints at -34 and +34 degrees, 5.3 m; shout has nothing to shout into. | E | M | P2 |
| 37 Rope Ledge (pit) | `trial.37.0` open the door (D, exit); `trial.37.1` slide down the rope (feature, luck, fail 39 = death) | Misleading: rope is 7.3 m up the wall at -45 degrees, near the edge; door is fine but identical in treatment. | D | M | P2 |
| 40 Vault of Records (vaults) | `trial.40.0` argue with the bouncer (D, encounter); `trial.40.1` show the GUEST LIST token (object, needs token); `trial.40.2` slip along the shelves (exit) | **Bad**: bouncer and `rope_sign` (a 0.8 m sign sprite) are both at 0 degrees, 3.0 m and 5.9 m: the token hotspot sits behind the bouncer's head and the two cannot be told apart by touch. | C | L | P1 |
| 42 Inner Vault (vaults) | `trial.42.0` damp stair (D, exit); `trial.42.1` hot door (exit) | Weak: two 2.7 m doors (`door_damp`, `door_hot`) exist 8.7 m off at -30/+33 degrees, but both look shut and identical in treatment; orbs only. | B | M | P1 |
| 43 Squeaking Stair (warren) | `trial.43.0` walk through the squeaking (D, exit); `trial.43.1` crawl the dry tunnel (exit) | Unreadable: bare waypoints 11 m and 6.7 m away, 24 degrees apart. | B | M | P2 |
| 45 Rat King's Court (warren) | `trial.45.0` take on the Rat King (D, encounter); `trial.45.1` offer a sandwich (exit) | Weak: king portrait fine; the "tribute" is a 1 m bones sprite 6.5 m away. | C | M | P2 |
| 48 Furnace Kitchens (kitchens) | `trial.48.0` take on the imp (D, encounter); `trial.48.1` freezer (exit); `trial.48.2` snatch the recipe book (exit; it is a trap, passage 50) | Misleading: the book is `book`, a 0.8 m **sign** sprite 9.5 m away; the freezer is a 0.8 m sign. The imp is the only readable thing. | C | L | P3 |
| 52 Hall of Hands (hall) | `trial.52.0` walk the aisle (D, exit); `trial.52.1` study the statue with no hands (exit); `trial.52.2` strike the fork on a palm (object, needs fork) | Bad: "the statue with no hands" is `statue_nohands`, a 0.9 m **skull** sprite; the palm `hand_ar0` is 13.8 m away; the aisle is a bare waypoint 8 m off. | E | L | P2 |
| 55 Hushing Gargoyle (hall) | `trial.55.0` fight the gargoyle (D, encounter); `trial.55.1` creep along the wall (feature, luck, fail 56) | Weak: gargoyle fine; the wall is one 2.2 m hand sprite 7.2 m away at -20 degrees. | C | M | P2 |
| 59 Echo Chamber (echo) | `trial.59.0` face the Echo (D, encounter); `trial.59.1` stand perfectly still (exit; death 60) | **Bad**: the one option that kills you is a bare waypoint at -33 degrees on empty floor with nothing saying "stand still". | C | M | P1 |
| 62 Last Landing (dawn) | `trial.62.0` push the door open (D, exit); `trial.62.1` ask if the sandwich is spare (exit) | **Bad**: the wizard the text talks about is not in the room at all (no wizard thing in `bassment_dawn.json`, none in `TrialScene.FIGURES`); two bare waypoints. | C (character) | M | P1 |

Totals: 27 branching passages, 58 hotspots; P1 9 (1, 3, 4, 20, 32, 40, 42, 59, 62), P2 13 (5, 15, 16, 23, 26, 28, 30, 35, 37, 43, 45, 52, 55), P3 5 (8, 10, 12, 18, 48). The remaining 37 passages have one hotspot each (the way on) and are in appendix A.

The three worst today: **32**, **59**, **40** (62 is a close fourth: its central character is missing).

## 2. The shared grammar (every archetype obeys this)

A **carrier** is the physical thing a hotspot is anchored to (a figure, prop or set piece). Every option gets one, named `cr_<passage>_<n>` after its hotspot id (`trial.40.1` -> `cr_40_1`), placed in the zone map (`content/story/maps/bassment_<zone>.json`) at the bearing and distance given in the passage rows. The hotspot's `anchor` becomes `{"thing": "cr_<p>_<n>"}` (add the entry to `THINGS` or `FIGURES` in `tools/trial/make_hotspots.py`). Its look is a **state pair**: CURRENT and IDLE, implemented as two things sharing a position with `piece` ids `cr_<p>_<n>_on` / `_off` (the map `piece` mechanism and the `piece`/`op` cast lines already exist, `HotspotContract.PIECE_OPS`), or, for a figure, as named frames. The engine's CURRENT event flips the pair.

1. **CURRENT = awake / open / offering. IDLE = asleep / shut / withdrawn / pleading.** Colour never carries the state: each pair differs in silhouette and in motion, and has a one-shot and a quiet loop of sound (audio not designed here).
2. **Default from beat 0.** The window opens with the default's carrier already in CURRENT (no blend from IDLE) and the others IDLE. When a zone swap is in progress the carriers are set before the frame opens.
3. **Touch (< 0.25 s).** The touched carrier plays IDLE to CURRENT (3 frames, a puff or creak); the previous CURRENT plays CURRENT to IDLE (the same frames reversed) in the same beat; an optional camera glance of at most 8 degrees toward the new CURRENT's bearing eases in over the beat (`RunRail.WINDOW_GLANCE_DEG` is the existing limit). The old CURRENT visibly "loses" (slump, door drops shut, rope hauled up). Touching the CURRENT one only plays a half-size `hop`/nudge; it never switches off (one option is always current).
4. **Commit (the flash beat).** The CURRENT carrier plays its COMMIT act (cheer, door swings wide, bridge settles) while the head turns to it (existing); the others stay IDLE and where a row says so react (wave goodbye, sag).
5. **Retry** (a failed phrase keeps the room): the failed option is CURRENT again and shows `resolve` (an usher's determined face, a door with fresh scratches, a creature's `attack` frame settling), plus a stumble FX on the camera side.
6. **Gated option** (needs lamp, token, fork): its carrier is always in the room, dormant and unremarkable; holding the item adds a **recognition beat** on entering the passage (one glint and a half `perk`) so the eye is drawn; never the default.
7. **No floating text, no orbs.** `thing_glow` orbs and floor ellipses move behind an "assist rings" accessibility setting (low vision); the default look is the carrier. Incidental diegetic writing is used only where a thing really would carry it (chalk tallies, a carved door symbol, a plaque with a music-notation glyph), always as pictograms.
8. **Draught.** One zone-level scalar "draught bearing" sways torches (`thing_torch_lean`), webs (`thing_web_hang`) and steam toward the CURRENT option's side. Cheap, non-light, and legible from the wall decoration alone.
9. **Hit areas.** Carrier bounding box at least 72 px; no two carriers overlapping in the picture at the passage's camera pose (fixes passage 4 and 40).
10. **Camera.** The camera does not turn during the window today; per-passage rows list the waypoint (in `content/trial/layout/<zone>.json`) changes needed. Hotspots beyond 40 degrees: 2.0, 9.0, 11.0, 12.1, 37.1, 50.0, 53.0.

## 3. Archetype A: the usher fork (1, 3, 15; and 18.1, 52.0 as components)

**The idea.** The owner's "NPC gesturing you to come, sad when you don't" for the places where a tunnel is just a tunnel. New NPC: the **Usher** (working name Wick): a candle-person, about 1.3 m tall, a stub of tallow with a flame for a head and a torch-bearer's sash, one of the wizard's cinema ushers in a club that has been closed for centuries. Face is drawn into the wax (two eyes, a mouth, an optional wax tear), so it reads at 40 px.

| State | Pose frames | Face | Reads as |
| --- | --- | --- | --- |
| CURRENT | `beckon_a` / `beckon_b` loop on the beat: near arm sweeps toward the way on, body upright, a small hop on the downbeat | happy: arc eyes, wide smile, **flame tall and steady** | "this way, come!" |
| IDLE | `plead_a` / `plead_b` loop: both arms out palms up, shoulders dropped, leaning toward the player, **flame low and guttering**, a wax drip every 2 beats | sad: drooped eyes, one wax tear, mouth down | "no, come with me instead" |
| Touch | IDLE to CURRENT: flame leaps (`perk`, 2 frames), dust puff; the old CURRENT: `slump`, flame shrinks, drip | | |
| Commit | CURRENT: `cheer` hop, then turns and `point`s down the way; the other: sad little wave (`flinch` then plead frame held) | cheer / sad | |
| Retry | CURRENT shows `resolve`: flame rekindled with a set jaw | resolve | |

Pose frames to draw (`fig_usher_<pose>.png`, 128x128): `idle, beckon_a, beckon_b, plead_a, plead_b, cheer, flinch, point, hush, snuffed` (10). Four palette variants generated in code (tallow cream, steam blue-grey, crystal pale cyan, bone white). Mapped faces: neutral, happy, sad, fear, cheer, plea, resolve, sheepish.

**First-run teaching (passage 1 only):** in the first 2 beats the IDLE usher's plead is at double amplitude with a drip, so a first-time player is invited to touch it; after the first swap this exaggeration is off for the whole session.

| Hotspot | Carrier and placement | CURRENT | IDLE | Commit / notes | Camera |
| --- | --- | --- | --- | --- | --- |
| `trial.1.0` ladder (D) | `cr_1_0`: tallow usher on the top rung of `ladder0..3`, at `ladder_top`, bearing -10 deg, 3.1 m, leaning over the shaft | beckons *down*; hatch chain and dust stream up the shaft (draught from below) | pleads, hugging the rail | cheers, drops down out of sight; the ladder rings | ok (-10 and +19) |
| `trial.1.1` chalk (exit) | `cr_1_1`: tallow usher at the chalk wall, +19 deg, 3.3 m, chalk stub in hand beside `thing_chalk_tally` (tally marks plus three pictograms: a lamp, an eel, an open mouth with sound lines, which is exactly passage 2's advice) | beckons with the chalk hand; a fresh tally mark is being drawn (tally frame 1) | chalk dropped, pleads; tally faded (frame 2) | cheers, tallies a mark | ok |
| `trial.3.0` cables (D) | `cr_3_0`: tallow usher in the left tunnel mouth, -30 deg, 4.5 m (anchor moves nearer than the 5.9 m waypoint); cables sway toward it | beckons; cables hum and sway out | pleads; cables hang limp | as table | ok (+/-30) |
| `trial.3.1` stairs | `cr_3_1`: steam-variant usher at the stair head, +30 deg, 4.5 m; steam curls toward it | beckons; steam rolls out toward the player | pleads; steam thins | as table | ok |
| `trial.15.0` lit path (D) | `cr_15_0`: crystal-variant usher at the foot of the lit column path, -25 deg, 5 m (the waypoint at 10.2 m stays the walk target) | beckons holding a small ringing crystal; nearest column rings | pleads; crystal still | as table | ok |
| `trial.15.1` terraces | `cr_15_1`: crystal usher at the terrace foot, +25 deg, 5 m, a rope in hand | beckons up the ledges | pleads | as table | ok |

Effort: kit L (new character), each passage M after it. Priority P1 (1, 3) and P2 (15).

## 4. Archetype B: physical path states (4, 10, 18, 23, 42, 43)

**The idea.** A way on is drawn as a thing that is either **open** (CURRENT) or **shut/withdrawn** (IDLE), and touching it physically opens it while its sibling closes. This is the owner's door example done in a dungeon: no red/green; a barred door vs a door ajar with something coming through the gap.

**Door-bar kit** (`thing_door_bar_<skin>`, 128x192, 2 frames each, skins `lp`, `damp`, `hot`, `plain`): IDLE = shut, a crossbar (`thing_crossbar`) dropped across the brackets, a carved symbol on the leaf; CURRENT = leaf ajar a hand-width, crossbar lifted and leaning on the wall, something streaming through the gap toward the player. Touch: bar lifts (3 frames, creak); the old CURRENT's bar drops (thud, 1-px camera shake). Commit: the leaf swings wide (swap to the existing `thing_door` doorway) while the head turns. Symbols are carved, fixed, and read without colour: damp = a drop, hot = a flame, lost property = a hook and coat.

| Hotspot | Carrier and placement | CURRENT | IDLE | Commit | Camera |
| --- | --- | --- | --- | --- | --- |
| `trial.4.0` thick cable (D) | `cr_4_0`: `thing_cable_thrum` (re-pose cable `cab_b`) at -28 deg, 4 m on the left wall | taut cable thrums (hum_a/hum_b on the beat), a spark runs along it down the tunnel showing where it leads | cable sags (`sag`), no sparks | sparks race away along it; camera follows | move `door_lp` and `sign_lp` to the right wall at +25 deg, 4.5 m so the two are 50 degrees apart (now 11) |
| `trial.4.1` LP door | `cr_4_1`: `thing_door_bar_lp` with `thing_glove_wave` caught in the gap | door ajar, an odd glove waves out of the gap like a beckoning hand | shut, crossbar down, glove hangs limp in the crack | door swings wide, glove waves you in | as above |
| `trial.10.0` wade in (D) | `cr_10_0`: the foot of the steps: `thing_tidemark` (wall waterline) with the existing 4 water frames; at +17 deg, 2.3 m | waterline at its high mark, ripple rings and a fin-wake lapping the bottom step, eel circling at full speed | tide mark one tile lower (frame 2), water still, eel slowed, steam jets hiss | wading splash; camera walks down | ok (27 deg apart); optional: waypoint `stairs_top` 1 m forward |
| `trial.10.1` valve wheel | `cr_10_1`: `thing_valve_turn` at the existing `valve`, -9 deg, 3.2 m, with `fx_steam_jet` on the pipe beside it | wheel turned a notch, steam jets, drip rate doubles (and the water preview above lowers: the consequence is shown before commit) | wheel still, cobweb across the spokes | wheel spins, pipes shriek, waterline drops | ok |
| `trial.18.0` rope bridge | `cr_18_0`: `thing_bridge` (256x128, 3 frames raised/mid/lowered) spanning the gap at -6 deg, 5 m | lowered across the gap, planks flat, ropes taut, dust trickling | hauled up vertical on its pulley, planks dangling | settles with a sway; camera steps onto it | ok (-6, +16) |
| `trial.18.1` climb down (D) | `cr_18_1`: crystal usher on the ledge steps, +16 deg, 5.6 m (archetype A states) | beckons down the steps | pleads | as A | ok |
| `trial.23.0` trapdoor (D) | `cr_23_0`: `thing_trapdoor` in the floor at the counter, -28 deg, 4.2 m | lid thrown open against the counter, ladder visible, spores rise | lid down, latch dogged, thin spore seep | lid clatters, ladder shows | ok |
| `trial.23.1` dark arch (needs lamp) | `cr_23_1`: `thing_arch_web` over `arch_door`, +26 deg, 4.6 m | web curtain parted, an iron lamp hook with the lamp on it (gold pool on the floor ahead) | web full, hook empty and dark | web flutters in as you go | ok |
| `trial.42.0` damp stair (D) | `cr_42_0`: `thing_door_bar_damp` at `door_damp`, -30 deg; bring the camera 3 m forward so it is at 5.5 m | ajar; water trickles, mist drifts toward the player, a rat tail curls round the edge | barred, drop glyph sharp | swings wide, squeaks swell | waypoint `inner_vault` 3 m forward |
| `trial.42.1` hot door | `cr_42_1`: `thing_door_bar_hot` at `door_hot`, +33 deg | ajar; heat shimmer and embers drift out, handle glows | barred, flame glyph sharp | swings wide, heat blast | as above |
| `trial.43.0` squeaking (D) | `cr_43_0`: `thing_rat_holes` in the left wall, +22 deg, 5 m | rat heads pop from the holes in sequence, tapping paws to the beat, tails flicking | holes empty, one tail withdrawing | all heads face you, squeak cadence up | ok after re-place |
| `trial.43.1` dry tunnel | `cr_43_1`: `thing_pipe_plug` pipe mouth, -22 deg, 5 m | rag plug out on the floor, feathers drift out on a dry draught | plug stuffed in, a feather stuck on it | pipe breathes out, camera crouches | ok |

Effort M each; 42 is P1 (owner's two-doors example), 4 is P1, 23 and 43 P2, 10 and 18 P3.

## 5. Archetype C: creature or character whose pose encodes the current option (8, 12, 20, 28, 32, 40, 45, 48, 55, 59, 62)

**The idea.** One person or monster is in the room and its **body language is the choice**. CURRENT fight = `poised` (faces you, weapon up, leaning in); fight not CURRENT = it relaxes and **looks at what you are about to do** (the other option). So a stealth option shows the monster looking away; a bribe shows it greedy; a trap shows it hopeful. The creature's existing `idle/attack/struck` frames stay; each creature gains 1 to 3 new frames and a handful of acts. Motions in `RunActing.figure_motion` to add: `perk`, `slump`, `hop` (bounce on the beat), `lean_toward` (a figure tilt toward a bearing), `look_away` (head/torso flip), `turn_back`, `rear_up`, `sink`, `shiver`, `cup_ear`, `lift_rope`, `hold_door`, `guard`, `hush`.

New faces named (baked into the creature frames; beyond the 14 of `docs/THREE_PATHS_AND_FACES_PLAN.md` section 2.1): `smirk`, `drowsy`, `hopeful`, `greedy`, `bored`, `sheepish`, `listening`.

| Creature | New frames (`fig_<name>_<pose>.png`, 128x128) | CURRENT-fight look | Stood-down look (other option current) |
| --- | --- | --- | --- |
| lampmoth | `flare`, `doze` | `flare`: wings wide, antennae forward, lamp swinging | `doze`: wings folded over back, slow breathing bob (face `drowsy`) |
| cable_eel | `rear`, `sunk` | `rear`: head and coils out of the water, sparks along the wire | `sunk`: only a fin-wake that glides toward the pipe option |
| barrel_knight | `fists`, `offer`, `back` | `fists`: glass slammed down, jaw clack, fists up (anger) | `offer` hand to the stool, glass in the other (happy); or `back` turned polishing (bored) |
| mildew_mother | `rear`, `sunk` | `rear`: reared, fur bristling, spores jetting at you | `sunk`: sinks to the eyes, gaze on the haze |
| mirror_twin | `mimic`, `frozen`, `back` | `mimic`: your stance, fists up, grinning | `frozen`: hand on the glass, still; `back`: back view for the panel |
| bouncer | `glare`, `rope`, `away` | `glare`: arms folded, chest out | `rope`: palm out, lifting the rope, a nod (face neutral); `away`: looks aside, checks his watch (bored) |
| rat_king | `rear`, `greedy` | `rear`: all heads up, crown wobbling | `greedy`: all heads turned to the pile, tongues out (greedy) |
| furnace_imp | `knives`, `hopeful`, `shiver` | `knives`: crouched, all knives out | `hopeful`: hands pressed, tiptoe toward the book; `shiver`: rubs arms, points a knife at the freezer |
| gargoyle | `fist`, `ear`, `asleep` | `fist`: unfolded, fist up, finger at lips | `ear`: hand cupped to ear, eyelids half (listening); `asleep`: eyes shut (aisle option, 52.0) |
| echo | `still` (the `attack` frame is reused for the fight) | existing `attack` lunge, ripples expanding | `still`: arms down, eyes shut, ripples flat |
| wizard | `beckon`, `guard` | | `beckon`: thumb to the door, grin (happy); `guard`: sandwich cradled to chest, one brow up (smirk) |

**Per-passage rows** (carrier for a figure option is the figure; add `wizard` to `FIGURES` in both `tools/trial/make_hotspots.py` and `TrialScene`):

| Hotspot | Carrier and placement | CURRENT | IDLE | Commit | Camera / notes |
| --- | --- | --- | --- | --- | --- |
| `trial.8.0` moth | figure `lampmoth` at `lamp`, 0 deg, 2.6 m | `flare`, lamp swings | `doze` (default state at beat 0, since the default is to leave) | win: struck, wings fold, lamp stops; loss: lunge | ok |
| `trial.8.1` leave (D) | `cr_8_1`: `thing_door_bar_plain` at `door_back`, -17 deg, 4 m; coat rack sways toward it | ajar, coats lean toward the gap, a glove waves | shut | swings wide | ok |
| `trial.12.0` eel (D) | figure `cable_eel` at 0 deg, 3.4 m | `rear` | `sunk`, wake runs under the pipe | existing win/loss | ok |
| `trial.12.1` pipes | `cr_12_1`: `thing_pipe_swing` over the water at -25 deg, 4 m (replaces `valve2`); the low frame carries a scorched mitten hanging from the pipe (the death 13 foreshadowed) | pipe swung down to hand height, rattling, mitten swaying | tucked against the ceiling, dripping | ok: swing across; miss: flash and the mitten's smoke | ok |
| `trial.20.0` knight (D) | figure `barrel_knight` at the bar | `fists` | (see below: `offer` or `back`) | win: collapse, shame; loss: bow then laugh | ok |
| `trial.20.1` creep | `cr_20_1`: `thing_barrel_stack` at -26 deg, 5 m (replaces `bar_g`) | stack leans, a lid cocked, a bone drops, dust trickles (the tell for death 22); knight shows `back` | tidy | ok: slips past; miss: lid cracks, stack tips | camera ok after re-place |
| `trial.20.2` sit | `cr_20_2`: `thing_stool_jukebox` at +25 deg, 5 m | stool pulled out facing you, jukebox disc spinning; knight `offer` | stool pushed in, disc still | stool scrapes, you sit | ok |
| `trial.28.0` Mother (D) | figure `mildew_mother` at 0 deg | `rear`, spores jet | `sunk` | existing | ok |
| `trial.28.1` haze | `cr_28_1`: `thing_cap_offer` bed at -26 deg, 5 m with `fx_spore_puff` | caps bow, a thick spore cloud rolls toward the player | caps upright, still | haze closes over | ok after re-place (now -36) |
| `trial.32.0` twin (D) | figure `mirror_twin`; pull its figure distance from 1.6 m to 2.8 m (`FIGURES`) | `mimic` | `frozen` | win: shards; loss: lunge | pull back |
| `trial.32.1` turn back | `cr_32_1`: `thing_mirror_panel` frame `back` (the twin's reflection turned away, shoulders hunched) with `thing_mirror_cracked`, at +25 deg, 4 m (replaces invisible `hs_mirror`) | panel shows the back view; hairline cracks spread (frame 2): the tell for death 33 | panel shows the stranger watching, glass clean | ok: gallery exhales; miss: every mirror cracks | ok |
| `trial.40.0` bouncer (D) | figure `bouncer` at 0 deg, 3 m | `glare` | `rope` or `away` | win: bow shame, waves you through; loss: shove | move the rope carrier off 0 deg |
| `trial.40.1` token (gated) | `cr_40_1`: `thing_stanchion_rope` on the right stanchion (`stanchion_r`), +18 deg, 4 m (replaces `rope_sign`); with the token held, a ticket-stub pictogram glints on the stanchion cap | bouncer `rope` (palm out, rope lifted off its hook in his other hand, nod) | rope hooked across | he lifts the rope, "go on" shrug | ok |
| `trial.40.2` shelves | `cr_40_2`: `thing_shelf_gap` at -22 deg, 5 m (replaces the bare `shelf_mouth` anchor at 8 m) | gap in the racks, sleeves slid out like beckoning fingers; bouncer `away` | racks flush | you slip in | ok |
| `trial.45.0` king (D) | figure `rat_king` at 0 deg, 2.6 m | `rear` | `greedy` | existing | ok |
| `trial.45.1` sandwich | `cr_45_1`: `thing_tribute_pile` at +19 deg, 4 m | sandwich on a plate held up by a small rat servant; king `greedy` | bare pile of bottle tops | king accepts; sleeve gnawed (passage 46) | ok |
| `trial.48.0` imp (D) | figure `furnace_imp` at 0 deg, 2.4 m | `knives` | `hopeful` or `shiver` | existing | ok |
| `trial.48.1` freezer | `cr_48_1`: `thing_freezer_hatch` at +25 deg, 5 m (replaces sign) | hatch open, frost fog pours toward you across the floor; imp `shiver` | shut and frosted | you step in | ok |
| `trial.48.2` book | `cr_48_2`: `thing_recipe_book` on the stove at -22 deg, 5 m (replaces the sign sprite `book`) | cover flaps like a jaw and for one frame shows a row of teeth (the mimic tell), sparks from the pages; imp `hopeful`, tiptoe | closed, lying still | you grab, cover snaps (passage 50) | ok |
| `trial.55.0` gargoyle (D) | figure `gargoyle` at 0 deg, 3.4 m | `fist` | `ear` | existing | ok |
| `trial.55.1` creep | `cr_55_1`: `thing_palm_cupped` on the wall at -20 deg, 4 m, with `thing_footprints_tiptoe` on the ledge | palm tilted into a handhold, tiptoe prints appear one by one; gargoyle `ear` | palm flat in the hush gesture | ok: round it on tiptoe; miss: stone finger on lips (56) | ok |
| `trial.59.0` Echo (D) | figure `echo` at 0 deg, 3 m | existing `attack`, ripples expanding | `still`, ripples flat | win: bow, relief | ok |
| `trial.59.1` stand still | `cr_59_1`: `thing_echo_dais` at -26 deg, 4.5 m (a worn standing ring with frozen ripples and a skeleton seated cross-legged, hands on knees: the previous victim; this is the tell) | rings dead flat, skeleton seems to nod, Echo `still` beside you | rings rippling, skeleton static | the room goes quiet (death 60) | ok |
| `trial.62.0` door (D) | `cr_62_0`: `thing_door_pushbar` at `dawn_door`, 0 deg, 5.4 m, wizard at the bench | bar pressed, door held ajar, daylight strip on the floor, wizard `beckon` (thumb to door, grin) | shut | door swings out | ok |
| `trial.62.1` sandwich | `cr_62_1`: figure `wizard` at the bench `dawn_landing_bench`, -27 deg, 3.1 m on `barrel_land`; **add the wizard to `bassment_dawn.json`** (not there today) | `guard` (sandwich cradled, one brow up) | `beckon` toward the door while eating | "No." he shrugs and holds the door | ok |

Three-way passages 20, 40, 48: the single figure shows three poses (the table above) so the creature's body is itself the readout, and the other two carriers carry the matching physical state. Effort: C group L (10 creatures x 1 to 3 frames, 14 acts, the wizard); 8 S, 20 L, 32 L, 40 L, 48 L, rest M. P1: 20, 32, 40, 59, 62. P2: 28, 45, 55. P3: 8, 12, 48.

## 6. Archetype D: safe path vs hazard stunt (5, 37) and E: curiosity beside a way on (16, 26, 30, 35, 52)

**D idea.** The risky option is the **armed hazard**: when CURRENT it looks more dangerous than when not. The safe way is shown by **tracks** or an unbarred door.

| Hotspot | Carrier and placement | CURRENT | IDLE | Commit | Camera |
| --- | --- | --- | --- | --- | --- |
| `trial.5.0` edge past (D) | `cr_5_0`: `thing_footprints_tiptoe` leading along the wall to `edge_past`, -14 deg, 4 m (floor decal beyond 3 m so it clears the pads) | prints appear one by one, dust puffs in each | prints scuffed and faded | you slip past between bursts | ok |
| `trial.5.1` dash | `cr_5_1`: `thing_junction_box` (replaces the valve-sprite `junc2`), 1.6 m, +24 deg, 3.5 m, with `thing_footprints_dash` skid marks under it | lid rattles, arcs twice as wide and reach the floor, burst on every half beat | one burst per beat (today's) | ok: you slide through; miss: white flash (6) | ok |
| `trial.37.0` door (D) | `cr_37_0`: `thing_door_bar_plain` at `door_ledge`, +17 deg, 3.4 m | bolt drawn, ajar, warm draught | barred | groans open | ok |
| `trial.37.1` slide | `cr_37_1`: `thing_rope_hang` at -28 deg, 4 m (replaces `rope_ledge`, 7.3 m up at -45 deg) | rope dropped to the ledge, a loop swinging at hand height, fibres glossy from use | coiled and tied up at the iron ring | ok: rope sings; miss: burns and lets go (39) | ok after re-place |

**E idea.** The curiosity option is **an object offering itself**; the way on stays calm.

| Hotspot | Carrier and placement | CURRENT | IDLE | Commit | Camera |
| --- | --- | --- | --- | --- | --- |
| `trial.16.0` walk on (D) | `cr_16_0`: `thing_door_bar_plain` at `door_cellar`, -17 deg (keep 3.4 m sprite; the waypoint stays 10.2 m) | ajar propped by a beer crate, a draught bends the crystal chimes | shut | swings wide | camera ok (bearing -17) |
| `trial.16.1` cracked crystal | `cr_16_1`: `thing_crystal_crack` at `crack_crystal` (4.4 m, bring it from 11.8 m to 6 m) | crack gapes, a sliver loosens, shards hover, the column leans 4 degrees toward you | closed hairline, upright | sliver falls, niche shows the token | ok |
| `trial.26.0` stones (D) | `cr_26_0`: `thing_stones_bed` starting 4 m ahead (the waypoint stays at 11 m) | stones risen in a staggered line across the bed, wet footprints on them | stones sunk, only ripples | each stone dips as you hop across | ok |
| `trial.26.1` cap | `cr_26_1`: `thing_cap_offer` at -28 deg, 4 m (replaces the -39 deg anchor) | stalk bows toward you, cap tilted showing a bite notch and a spore drip | upright, closed | cap tears, haze | ok |
| `trial.30.0` aisle (D) | `cr_30_0`: two `thing_stanchion_rope` posts framing the runway at centre, 4 m (velvet ropes hang; the club's own closure device) | ropes unhooked and hanging down: the aisle is open; all mirror strangers (`thing_mirror_panel` `watching`) face the aisle | ropes hooked across: closed | ropes drop, strangers part | ok |
| `trial.30.1` waving reflection | `cr_30_1`: `thing_mirror_panel` at -24 deg, 4.6 m (does not exist today) | stranger **beckons** happily, pointing at the seam | stranger **pleads**, arms out, sad | stranger bows, seam opens | ok |
| `trial.35.0` rope (D) | `cr_35_0`: `thing_rope_hang` at -30 deg, 4.5 m at the iron ring | rope dropped with a knotted loop, swaying toward you | coiled and tied up | rope runs, you climb | ok |
| `trial.35.1` shout | `cr_35_1`: `thing_speaking_horn` on a post at +30 deg, 4.5 m with `thing_bats` above | bell raised toward the pit, brass shine, echo rings drift out; bats stirring | bell slumped down, cobweb; bats asleep | bats burst out, the pit answers | ok |
| `trial.52.0` aisle (D) | `cr_52_0`: bone-variant usher at the aisle head, 0 deg, 4 m, finger to lips (`hush`) | beckons down the aisle, finger on lips; dust draught streams down the row | pleads silently | cheers silently, walks ahead | ok |
| `trial.52.1` handless statue | `cr_52_1`: `thing_statue_nohands` at -23 deg, 4.3 m (replaces the skull-sprite `statue_nohands`), `thing_plaque_fermata` on the plinth (a note with a fermata, i.e. the passage 53 riddle in music notation) | head turned to you, stumps raised, plaque catches the light | head bowed, stumps down | head tilts, you read the plaque | ok |
| `trial.52.2` palm (needs fork) | `cr_52_2`: `thing_palm_cupped` on a front-row statue at +28 deg, 5 m (replaces the 13.8 m `hand_ar0`) | palm tilts up and cups, dust shivers off it | palm flat | fork rings down the row | ok |

Effort: D M each, E M each except 52 L (3 new props, usher variant). P2 for all of D and E.

## 7. Appendix A: the 37 passages with one hotspot (the way on)

No branch, so no CURRENT/IDLE swap. Kit **W (way on)**: the exit's carrier is in its CURRENT form from beat 0 (door ajar with the bar leaning, ladder rungs ringing, a draught from the gap), and touching it just plays a `hop`/nudge. Kit **T (tableau)** for the 7 deaths and the defeat: the one way out is the wizard's staff lowered through the dark on a hook (`thing_staff_hook`, 64x256, two swing frames), at 0 degrees, 2.5 m; touching it hauls you up. Priority P3 unless stated.

| Passage | Hotspot | Carrier (state to show) | Camera note |
| --- | --- | --- | --- |
| 0 Defeated | `trial.0.0` | T: staff hook | ok |
| 2 Chalk on the Wall | `trial.2.0` | ladder; show the tally wall close-up with its three pictograms | turn left 40 deg (now -55) P2 |
| 6 Singed | `trial.6.0` | fresh tiptoe prints past the junction, box idle | ok |
| 7 Cable Nest | `trial.7.0` | the `gap` sprite (0.9 m) enlarged to 1.6 m, cold draught lines, a pebble rolling | ok |
| 9 Brass Lamp | `trial.9.0` | `door_back` as `thing_door_bar_plain` ajar; lamp on its hook | turn left 30 deg (now -45) P2 |
| 11 Valve Wheel | `trial.11.0` | steps down to the water, tide mark in its low frame | turn right 40 deg (now +52) P2 |
| 13 Fried | `trial.13.0` | T | ok |
| 14 Dry Landing | `trial.14.0` | `door_up` ajar, dust falling down the stair | ok |
| 17 Ringing Niche | `trial.17.0` | `thing_token_niche` (shows the token) beside the cellar door ajar | ok |
| 19 Cellar Stairs | `trial.19.0` | `thing_door_bar_plain` propped by a beer crate | ok |
| 21 Dead Bar | `trial.21.0` | the knight (`idle`) clearing his throat (hop) | ok |
| 22 Last Orders | `trial.22.0` | T | ok |
| 24 Dark Corridor | `trial.24.0` | corridor mouth, gig posters fluttering on the draught | ok |
| 25 Old Green Room | `trial.25.0` | `backdoor` ajar, moved nearer (9.4 m to 5 m) | P2 (on the default walk, far) |
| 27 Spore Haze | `trial.27.0` | caps bowed toward the pond (`thing_cap_offer` bowed) | ok (+24 deg, 7.1 m: move to 5 m) |
| 29 Spore Stairs | `trial.29.0` | `stair_door` ajar | ok |
| 31 Waving Reflection | `trial.31.0` | stranger (`beckon`) toward the aisle, runway ropes unhooked | ok |
| 33 Shattered | `trial.33.0` | T | ok |
| 34 Gallery's End | `trial.34.0` | rope over the edge, dropped (`thing_rope_hang`) | ok |
| 36 A Shout into the Dark | `trial.36.0` | rope dropped; horn slumped | ok |
| 38 Pit Floor | `trial.38.0` | rope hanging back up; `thing_tuning_fork` shivering in the crack (the item) | P2 |
| 39 A Long Way Down | `trial.39.0` | T | ok |
| 41 Long Shelves | `trial.41.0` | `thing_shelf_gap` gap, bouncer's hand lifting you by the collar | ok |
| 44 Dry Tunnel | `trial.44.0` | pipe mouth, plug out | turn right 20 deg (now +34) |
| 46 Chewed | `trial.46.0` | king `idle` licking its crown, bare tribute pile | ok |
| 47 Gnawed Door | `trial.47.0` | `thing_door_bar_plain` gnawed, ajar | ok |
| 49 Walk-in Freezer | `trial.49.0` | freezer hatch open, frost fog | ok |
| 50 Flambe | `trial.50.0` | T | turn right 40 deg (now +54) |
| 51 Cold Store | `trial.51.0` | `door_cold` ajar, frost fog | ok |
| 53 Statue Without Hands | `trial.53.0` | bone usher at the aisle head with `hush` | turn right 30 deg (now +42) |
| 54 Resonant Seam | `trial.54.0` | `thing_seam_slab` swung open | ok |
| 56 Hushed | `trial.56.0` | gargoyle settling back (`asleep` to `fist` on touch) | ok |
| 57 Resonance Door | `trial.57.0` | luck feature: `thing_round_door` (256x256, 3 frames: humming rings / locked rings / sour split rings) replacing the additive `door_glow` | ok P2 |
| 58 Door Says No | `trial.58.0` | `thing_round_door` sour frame settling back to hum | ok |
| 60 Swallowed by Silence | `trial.60.0` | T | ok |
| 61 Dawn Stair | `trial.61.0` | stair door ajar, grey light and wind | ok |
| 63 Daylight | `trial.63.0` | `thing_barrier_arm` raised at the car park exit, daylight beyond | P2 |

## 8. New assets and expressions: roll-up

| Category | Count | Detail |
| --- | --- | --- |
| New NPC species | 2 | Usher (10 poses, 4 palette variants generated); Reflection stranger (4 frames, inside `thing_mirror_panel`) |
| Creature and wizard pose frames | 26 | lampmoth 2, cable_eel 2, barrel_knight 3, mildew_mother 2, mirror_twin 3, bouncer 3, rat_king 2, furnace_imp 3, gargoyle 3, echo 1, wizard 2 (plus the wizard placed in `bassment_dawn.json`) |
| Prop and set-piece assets | 47 | 98 frames; list below |
| FX sets (64x64) | 6 | `fx_steam_jet` 4, `fx_frost_puff` 4, `fx_dust_puff` 4, `fx_chalk_puff` 4, `fx_wax_drip` 3, `fx_spore_puff` 4 (23 frames); with the props that is 53 named assets and 121 frames |
| New faces (beyond the 14) | 7 | smirk, drowsy, hopeful, greedy, bored, sheepish, listening; the Usher also has its own 8-name vocabulary (neutral, happy, sad, fear, cheer, plea, resolve, sheepish) mapped onto existing names |
| New acts and motions | 14 | perk, slump, hop, lean_toward, look_away, turn_back, rear_up, sink, shiver, cup_ear, lift_rope, hold_door, guard, hush |
| Engine hooks | 6 | named-frame figures, state-pair `piece` flips on CURRENT, a zone draught bearing, the window glance, the assist-rings setting, carrier anchors in `make_hotspots.py` (section 9) |

Props (name, size, frames; the six `fx_` sets are in the table above): `thing_chalk_tally` 128x192 x2; `thing_door_bar_lp|damp|hot|plain` 128x192 x2 each; `thing_glove_wave` 64x64 x2; `thing_crossbar` 64x128 x1; `thing_cable_thrum` 128x192 x3; `thing_trapdoor` 128x128 x2; `thing_arch_web` 128x192 x2; `thing_footprints_tiptoe` 128x64 x2; `thing_footprints_dash` 128x64 x2; `thing_junction_box` 128x128 x3; `thing_pipe_swing` 128x192 x2; `thing_tidemark` 128x64 x2; `thing_valve_turn` 128x128 x2; `thing_bridge` 256x128 x3; `thing_rope_hang` 128x256 x2; `thing_speaking_horn` 64x128 x2; `thing_bats` 128x64 x2; `thing_stones_bed` 256x64 x2; `thing_cap_offer` 128x128 x2; `thing_stool_jukebox` 128x128 x2; `thing_barrel_stack` 128x128 x2; `thing_tribute_pile` 128x64 x2; `thing_recipe_book` 64x64 x2; `thing_freezer_hatch` 128x128 x2; `thing_statue_nohands` 128x192 x2; `thing_plaque_fermata` 64x64 x1; `thing_palm_cupped` 128x128 x2; `thing_mirror_panel` 128x192 x4; `thing_mirror_cracked` 128x192 x2; `thing_echo_dais` 128x64 x2; `thing_crystal_crack` 128x192 x2; `thing_staff_hook` 64x256 x2; `thing_barrier_arm` 128x64 x2; `thing_stanchion_rope` 128x128 x3; `thing_torch_lean` 128x128 x2; `thing_web_hang` 64x128 x2; `thing_door_pushbar` 128x192 x2; `thing_rat_holes` 128x128 x2; `thing_pipe_plug` 128x128 x2; `thing_shelf_gap` 128x192 x2; `thing_token_niche` 64x64 x1; `thing_tuning_fork` 64x128 x2; `thing_seam_slab` 128x192 x2; `thing_round_door` 256x256 x3.

Already exists and is reused: `thing_door` (the wide-open commit frame), `thing_ladder`, `thing_valve`, `thing_rope`, `thing_cables`, `thing_hand`, `thing_mushroom`, `thing_lamp`, `thing_torch`, `thing_crystal`, `thing_coatrack`, the four `water*` frames, the `idle/attack/struck` frames of all creatures.

Effort by group: Usher kit L; creature kit L (26 frames, 14 acts); door-bar kit M; every other prop pair S. By priority: P1 needs the Usher, the knight/bouncer/twin/echo/wizard frames, the door-bar damp/hot/lp/plain skins, the cable thrum, the chalk tally, the mirror panel set, the shelf gap, the stanchion rope, the echo dais: about 60 % of the art. P3 (8, 10, 12, 18, 48) needs the valve/tide/steam, the pipe swing, the bridge, the book/freezer sets, the moth/eel/imp frames.

## 9. Cross-cutting issues

1. **Creatures have no per-pose frames.** `CREATURE_ACTING` only drives translate/squash on three frames. The new poses need named frames and an `acting.frames` (or equivalent) map in the hotspot data, with `available`/`selected` re-read as IDLE/CURRENT. The `act`/`face` values in `CREATURE_ACTING` that name faces are baked frames here (no face decal on a billboard).
2. **Anchors move.** 38 of the 58 branching hotspots anchor on a bare waypoint (nothing is drawn there but an orb); others sit on the wrong sprite (`junc2`, `valve2`, `rope_sign`, `book`, `statue_nohands`) or an invisible marker (`hs_mirror`). All become carrier things; `make_hotspots.py` `THINGS`, `FIGURES` and the zone map `things` need the new ids, and `tools/trial/check_maps.gd` should fail a branching passage whose hotspot lacks a carrier with a state pair.
3. **Camera.** Seven hotspots beyond 40 degrees (2.0, 9.0, 11.0, 12.1, 37.1, 50.0, 53.0) and two overlaps (4, 40) need layout changes in `content/trial/layout/<zone>.json` then `python3 tools/trial/apply_layout.py`. The optional window glance (at most 8 degrees toward the CURRENT option) is a strong extra cue but not required by any row.
4. **Visible area.** The pad strip hides the lower 36 %: footprints and the stones bed only work beyond 3 m; keep faces, glyphs and the key silhouette in the upper two thirds of each sprite.
5. **Distance.** 20 anchors (15 in branching passages) are further than 8 m (e.g. 15.1 at 15.8 m, 16.1 at 11.8 m, 26.0 at 11.2 m, 52.2 at 13.8 m). Carriers are placed at 2.5 to 6 m; the exit waypoint (where the camera walks) is unchanged.
6. **The Usher is a new character in the Bassment's voice.** If the owner prefers none, A falls back to archetype B (barred/ajar mouths); the cost is losing the "NPC beckons, sad when not chosen" reading in 1, 3, 15 and 18.1.
7. **Transition time.** Beats differ (0.345 s at 174, 0.69 s at 87), so every swap is authored in seconds (at most 0.25 s), not beats.
8. **Teaching.** Only passage 1 teaches by an exaggerated IDLE; every later passage relies on the same grammar. The wizard's voice at the hatch can say "tap a friend" in audio, no text.
9. **Failures and deaths.** The failure outcomes of luck tests (5.1, 12.1, 20.1, 32.1, 37.1, 55.1, 57) must show a tell on the CURRENT carrier before the commit (singed box arcs, mitten, wobbling stack, cracking mirror, burnt rope, cupped ear); those tells are in the rows and are the only foreshadowing a first-time player gets, so they must be visible at phone size.
10. **Wizard art.** The existing `fig_wizard_idle` is a bust with a staff. The Warehouse and passage 62 should share one set of wizard frames (`idle, beckon, guard, cheer`) so he looks like the same person; coordinate with the Warehouse brief.
11. **Colour.** Nothing here uses colour as the only difference. Each CURRENT/IDLE pair differs by silhouette (open vs barred, raised vs lowered, upright vs slumped) and by motion; the palette variants of the Usher only separate zones.
12. **Verification to add.** `tools/trial/capture.sh` should shoot each branching passage twice (default CURRENT, then each other option touched) and write `docs/shots/choice/bassment_<passage>_<option>.png` for review.

## 10. Coverage verification

Script (run once against `content/trial/hotspots.json` and this file): every hotspot id `trial.<p>.<n>` of the 95 appears in this document, and every passage id 0 to 63 is covered either in section 1 (27 branching passages, 58 hotspots) or appendix A (37 single-hotspot passages, 37 hotspots; the passage 0 hotspot is `trial.0.0`). Result: **95 of 95 hotspots, 64 of 64 passages**.
