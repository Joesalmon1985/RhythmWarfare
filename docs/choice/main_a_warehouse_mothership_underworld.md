# Choice briefs: Warehouse, Mothership, Underworld (the 174 BPM opening worlds)

Scope: `content/run/hotspots/warehouse.json`, `mothership.json`, `underworld.json` and their 16 scenes in `content/run/run.json`. Written 5 Nov 2026 against `origin/main` 55f6cd3f. Documents only: no code, no art.

The owner's playtest verdict this answers: the game is a walking sim behind the music game, so every branching point must be *in the world*: people, objects and places that show the choice, the default, and what a press changes. Not floating text, not only light.

**Coverage check** (script over the hotspot JSON and the run.json nodes of the three worlds):
`warehouse 27 hotspots, 6 scenes, 6 with 2+ | mothership 17 hotspots, 5 scenes, 5 with 2+ | underworld 17 hotspots, 5 scenes, 5 with 2+ | TOTAL 61 hotspots, 16 of 16 scenes have 2 or more hotspots.` Every one of the 16 is in the table and has its own section. The three Warehouse portals (balcony star, booth radio, bar ember) are options inside their scenes (sections 2, 3 and 5).

## 0. Facts every implementer needs (read once)

* **The assumed engine** (another agent builds it): at any time exactly one option of the window is CURRENT, starting as the scene's default; touching any option's thing makes it current within one beat; the choice can change until the commit at beat 60.5; a pass plays `on_success`, a miss `on_failure`; nothing touched takes the default exit.
* **Two kinds of option in these worlds.** *Route options* (an exit, or a gatekeeper whose failure re-routes: the Warehouse bouncer, the Mothership exam, the Underworld throne) change **where you go**. *Stops* (a dancer, a bartender, a lava lamp, an anvil) change **what you do on the way**; after a stop's cinematic the default exit still follows. So every scene has two layers: the **route tableau** (it shows `route_of(current)`: the touched exit's route, else the default route; a stop leaves the default route showing) and the **stops** (each shows "engaged" when current, "idle" otherwise). Scenes with one exit (chill, booth, gallery, reactor, bridge, court, furnace, pit) are "stop or go": the exit is itself an option and gets a person or object like the others.
* **Camera.** Vertical FOV 52 degrees, stage view about 1280 x 460 px, so horizontal FOV about 108 degrees: **only bearings inside +-54 degrees are on screen**. Yaw convention of the maps: yaw 0 looks toward -z, 90 toward -x, -90 toward +x, 180 toward +z. The four note lanes cross the stage above their pads (D F J K) at x of about 92-192, 308-408, 872-972 and 1088-1188; the gaps are 0-92, 192-308, 408-872 (centre), 972-1088 and 1188-1280 (lane positions read from the screenshots in `docs/shots/run`, to be checked on a phone). A bearing of +-40 degrees lands at x 245 / 1035, in a gap; +-0 to 22 degrees lands in the centre band. The hotspot hit radius is at least 36 px, and taps over a lane still count; this is a guideline for legibility, not a rule.
* **Where the camera is in the window.** The rail steps at beats 12.5, 28.5 and 44.5 (a 2 to 4 bar move each), so at beat 48 the camera is at the third place of the good rail (perfect play) or on the bad rail (misses), often still walking; the window's glance turns at most 8 degrees (`RunRail.WINDOW_GLANCE_DEG`). So what is in view varies with performance. Bearings under "Today" are from the scene's home waypoint (the best case); reality is worse. **Every brief below therefore names a fixed window vantage** (E2 in the cross-cutting list): a waypoint and yaw the camera settles on by beat 48, chosen so every option is on screen.
* **Art scale** (from `docs/STORY_ART.md`): the 3D view renders at 180 lines and is upscaled 2.55x, nearest-filtered. Things are billboard textures of 64 or 128 px (128 px is 1.5 to 2.4 m), wide ones 256 x 128, set pieces are map things with `"piece": id` switched by `piece_on/off/pulse`. A person is a baked pixel sheet: a full-detail adult is 112 px tall, 17 x 13 px head; at 5 to 7 m (the usual choice distance) the person is 40 to 55 low-res px and the face is 3 to 5 px. **Rule: pose and prop carry the message; faces confirm it only inside about 4 m.** The new faces below are still needed (close shots, the commit beat, the early window) but no choice may depend on a face alone.
* **Sheet budget.** People are baked only for the acts and faces the data names (`tools/story/art/directed.py`). Each new act on a directed person costs frames; the briefs keep directed people few (2 or 3 per scene) and reuse the same new acts everywhere.
* **Names.** New map things and pieces use the prefix `ch_` (`ch_wh_*`, `ch_ms_*`, `ch_uw_*`). "Frames" are separate pieces toggled together (on/off ops on the same beat). Hotspot ids, waypoints and actor ids below are the real ones; `NEW` marks something that does not exist yet.

### The grammar (rules used by every scene)

| # | Rule |
| --- | --- |
| G1 | **The default is the idle state.** From beat 0 of the scene the set already shows the default route and default stop as CURRENT (door open, person happy, paddle up). From beat 48 the alternatives *wake* (they begin soliciting). A player who touches nothing sees nothing change, and that is right. |
| G2 | **Everyone keeps asking.** Every option has a person or object that solicits (beckons, rattles, glows, sways). CURRENT is the happy, open, lit, extended version; NOT CURRENT is the sad (`sulk`, `plea`), shut, dim, withdrawn version, still soliciting at half strength. Never colour alone: each state differs in silhouette (posture, prop up or down, open or shut). |
| G3 | **Touch is answered within one beat** (0.345 s at 174 BPM): the loser visibly deflates (face drops, prop lowers, door eases shut) while the winner lights up (2 to 3 frame swap, a prop flick, a step). Both halves in the same beat: that is what teaches "pressing this changes it". |
| G4 | **Commit** (beat 60.5): the current thing acts the committed beat (usher, point, step), then success (open, cheer, nod) or failure (shrug, slam, spill) plays; the existing cinematic and cast lines carry on. |
| G5 | **Route layer vs stop layer** (above): the doors show the route that will be taken. A route person is CURRENT (happy, soliciting) when its own option is current and QUEUED (calm nod, `neutral`, no soliciting, door still open) when a stop is current; a stop never darkens the default door. A **gamble** (a gatekeeper whose failure re-routes) shows UNDECIDED: both doors half open, the gatekeeper centred; the verdict opens one wide. |
| G6 | **No text.** Allowed incidental pictograms: a pint glass, a stairs-up glyph, a fork, an anvil, a skull; painted on a paddle, banner or sign that would exist. No letters. |
| G7 | **Keep the ring, demote it.** The existing ring of light stays as a faint reinforcement on the CURRENT option only (E9); it never replaces the thing. |
| G8 | **Windows of view.** Options sit between about 2.5 and 8 m from the vantage, spread across +-40 degrees, never directly behind a note lane centre if avoidable. |

## 1. Summary of all 16 branching scenes

Verdict today is about what the player can see at the window (from the best case, the home waypoint). INVISIBLE = nothing in frame; BEHIND/EDGE = only edge beacons or past +-54 degrees; RING = the thing is in view but nothing says "option" except a faint ring of light and a wave.

| Scene | Options (hotspot ids) | Default | Verdict today | Archetype(s) chosen | Effort | Prio |
| --- | --- | --- | --- | --- | --- | --- |
| `warehouse` The Floor | exit_bar, exit_balcony, dancer, wizard (early), led_wall (return) | exit_bar | INVISIBLE: exits at +52/-51 (edge), wizard -100 (behind), dancer -62, ball above frame | Two stewards with pictogram paddles + roller shutter and scissor gate + LED chevron chase; dance ring opens; wizard with lit staff | L | P1 |
| `warehouse.bar` The Bar | exit_chill, exit_booth, bartender, stranger, ember | exit_chill | BEHIND/EDGE: curtain +73, door behind, ember +48; only bartender and stranger in view | Bead curtain vs stage door with roadie; the pint slid or withheld; stranger's matchbook; ember lantern | L | P1 |
| `warehouse.balcony` The Balcony | exit_chill, exit_booth, rail, promoter, star | exit_chill | BEHIND/EDGE: stairs -94, promoter -78, star behind; door and rail 1-2 m (ring only) | The club dog leads to one way; rope across the stairs; leaning raver at the rail; skylight star | M | P1 |
| `warehouse.chill` The Chill-out | exit_exit, sofas, wizard (early), lavalamp | exit_exit | RING: door +12, sofas -39, lamp +29; wizard behind (-114) | Friends pat the sofa vs coat-buddy at the door; lava lamp rises or settles; wizard at a trapdoor | M | P2 |
| `warehouse.booth` The Booth | exit_exit, decks, headphones, radio | exit_exit | EDGE: decks 0.8 m below frame, exit +51, headphones -56, radio behind (-105, edge beacon) | Platter/stylus and crossfader states; old radio with aerial; front row reaches up | M | P3 |
| `warehouse.exit` The Door | exit_mothership, exit_underworld, bouncer, bouncer_vip | exit_mothership | INVISIBLE: tunnel behind (180), crack +80, bouncer -108 | The bouncer between two doors: cyan tunnel gate vs cracked door, velvet rope | L | P1 |
| `mothership` The Deck | exit_gallery, exit_reactor, grey, dj | exit_gallery | BEHIND: doors +81/+102; grey, DJ in view (a wave) | Hover-drone usher between two iris doors; the grey's offered orb; DJ's slipping headphones | M | P1 |
| `mothership.gallery` The Gallery | exit_bridge, window, menu | exit_bridge | EDGE: exit 17.7 m away (a slit), window +66, menu 14.7 m | Window blinds; hologram menu and waiter drone; iris door at the far end | M | P2 |
| `mothership.reactor` The Reactor | exit_bridge, core, engineer | exit_bridge | BEHIND: exit +90; core and engineer in view (ring) | Knife-switch lever and control rods; engineer's badge; boom barrier | M | P3 |
| `mothership.bridge` The Bridge | exit_exit, helm, star_chart | exit_exit | BEHIND: door +100; helm 12 m (ring) | Captain's chair swivels; warp streaks on/off; hologram globe; door with ensign | M | P2 |
| `mothership.exit` The Airlock | exit_hospital, exit_ward, exam, airlock_wheel | exit_hospital | EDGE: airlock ahead in view; exam door -66, medic -84 | Airlock hatch and wheel vs medic's probe arm; gatekeeper gamble | L | P1 |
| `underworld` The Arena | exit_court, exit_furnace, bouncer, bouncer_grudge, chains | exit_court | INVISIBLE: gates +61/-69, bouncer -59, chains +74 | Gladiator thumbs: banner heralds, tier crowds cheer or boo, portcullises; hook chain | L | P1 |
| `underworld.court` The Court | exit_pit, seal, queen | exit_pit | RING: all in view (queen 2.3 m, seal a flat sigil at the horizon) | The queen's hand and fan; seal flares; lantern imp at the causeway | M | P2 |
| `underworld.furnace` The Furnace | exit_pit, anvil, ladle | exit_pit | BEHIND/EDGE: exit behind (-96), ladle -55 | Smith with tongs; anvil glows; ladle tilts; iron door | M | P3 |
| `underworld.pit` The Pit | exit_exit, lava_bridge, brazier | exit_exit | BEHIND: door behind (129), brazier +97; bridge 17 m | Basalt slabs rise from the lava or sink; brazier lit or cold; door | M | P2 |
| `underworld.exit` The Throne | exit_hospital, exit_ward, throne | exit_hospital | RING: doors +-32, throne 0 (best today) | Two humble doors (clinic white vs padded green) with cameo staff; the skull throne's jaw | L | P1 |

Priority: **P1** = the eight scenes with two real exits (where the run actually forks); **P2** = single-exit scenes on the default path; **P3** = single-exit scenes off the default path. Within any scene the portals and secrets (star, radio, ember, headphones, star_chart, led_wall) are the last to build.

Totals are in the roll-up at the end: **40 object families (26 new, 14 existing ones given new frames), 104 frames; 9 new people plus 5 re-dressed (6 new wardrobe looks); 2 animated non-person figures; 5 new faces; 12 new acts; 13 held props; 10 animation behaviours.**

## 2. The Warehouse (`night_one`, rooms are views of one map)

Shared by the six scenes: the chorus is the dance floor's own crowd (existing actors `c01`..`c10`, `e01`..`e04`, `g01`..`g08`, `l01`..`l04`, `p01`..`p04`), the bar's `b01`..`b04`, the chill-out's `s01`..`s04`, the balcony's `v01`..`v03`, the door's `d01`. Palette: brick, steel truss, amber and magenta lamps; LED floor tiles.

### 2.1 `warehouse` The Floor (entry scene) - P1, L

**Story.** The doors have just opened and the floor is going. A gap by the speaker stacks (east) leads to the bar, a side door (west) up to the balcony. A robed wizard lurks by the toilet corridor; one dancer keeps calling you into the circle.

| Option (hotspot) | Anchored on today | Leads to / success / failure | Seen today (home view, yaw 0) |
| --- | --- | --- | --- |
| `warehouse.exit_bar` **DEFAULT** | waypoint `to_bar` (5.8, 2.0) | success `warehouse.bar`; failure the same door, staggering, -5 | bearing +52, edge beacon, a ring on the floor |
| `warehouse.exit_balcony` | waypoint `to_balcony` (-5.8, 1.75) | `warehouse.balcony`; failure same door, stagger -5 | -51, edge beacon |
| `warehouse.dancer` | actor `g07` (-6.4, 3.14) | success flag `wh_circle`, join the circle, +6, music variation; failure stumble -6; both then take the default route (bar) | -62, off screen; only a wave |
| `warehouse.wizard` (EARLY window, beats 16-47; `flags_none wh_wizard_met`) | map thing `wizard_floor` (-5.2, 7.4), a swaying billboard | success route `1` = the Bassment; failure `wh_wizard_shrug`, -2 | -100, **behind the camera**; no acting (billboard) |
| `warehouse.led_wall` (needs `wh_circle`: only on a return after a path) | thing `disco_ball` (0, 2.5, y 4.7) | +5 variation / -4 dip | straight ahead but above the top of the frame |

**Window vantage** `floor_choice` NEW (0.0, 8.9) yaw 0 (the back of the floor by the exit sign, facing the stage; sector `floor`). From there: stewards `c02` / `c03` at -33 / +36 degrees (4.8 m), dancer ring gap at -17 (5.3 m), wizard at +24 (3.2 m), ball dead ahead (6.4 m; lower it to y 3.6 so it is inside the 26 degree vertical half-FOV), the two gates at -44 / +48 behind their stewards. Early window: hold this vantage from beat 12.5 (E2b), otherwise the rail walks the camera to the steps with its back to the wizard.

**Concept: the stewards.** A rave has stewards in hi-vis with glow batons pointing the crowd. Two of them stand on the floor, each holding a round paddle with a painted pictogram: a pint glass (east) and a stairs-up glyph (west). Behind each, the real way on is a physical gate: a **roller shutter** at the bar mouth, a **scissor gate** across the balcony door. The current way has its steward cheerful with the paddle high and its gate wide open; the other steward is sulking with the paddle at the hip and the gate shut but rattling on the kick drum. A chase of LED floor tiles runs from the camera toward the current gate (supporting, never alone). Press the sulking steward: the paddles swap and the gates swap within one beat.

| Option | Embodied by | Idle / invitation (beat 0; wake at 48) | CURRENT | NOT CURRENT | Touched (within 1 beat) | Commit success / failure |
| --- | --- | --- | --- | --- | --- | --- |
| `exit_bar` | steward `c03` (east) + `ch_wh_shutter` at (6.95, 2.5); hotspot anchor = shutter plus `c03` | default shown from beat 0: paddle (pint) held high (`hold_up`), face `happy`, shutter UP with amber light spilling, chevrons point east | as idle, plus `beckon` every bar; chevrons chase at one tile per beat | paddle at hip (`hold_low`), face `sulk`, shutter half down, rattling 1 px on the kick; chevrons off | becomes current: `hopeful` then `happy`, paddle flicks up, shutter frame 3; loses current: face drops, paddle lowers, shutter frame 2 | S: steward `usher` toward the gate (1 beat), then `cheer`; nearby dancers `wave`. F: steward `shrug`, shutter jams half; camera staggers (existing cinematic `stagger_entry_right`) |
| `exit_balcony` | steward `c02` (west) + `ch_wh_scissor_gate` at (-6.95, 1.75) | paddle (stairs) low, `sulk`, gate CLOSED; at wake it `beckon`s small and tugs the gate once a bar | paddle up, `happy`, gate folded open (3 frames), a pool of white light from the stairs | as idle | mirror of the above | as above, with `stagger_entry_up` |
| `dancer` (stop) | `g07`, re-homed to the gap of the dance ring (-1.6, 3.8); ring dancers `c01`, `c06`, `c07` | dances in the ring; at 48 `beckon` | `happy`, ring dancers either side `clap`, the gap faces the camera. While current the bar steward goes QUEUED (calm nod, paddle half) | `shrug` then back to dancing; ring dancers `turn_away`, the ring closes | `nod`, hop; ring opens (cast lines on the same beat) | S: ring `cheer`, camera joins (existing `join_circle`). F: ring `stare` with `doubt`, `g07` `recoil` |
| `wizard` (early) | NEW actor `wz_floor` at (1.3, 6.0), robe, pointed hat, beard, staff | staff crystal LIT, `beckon` toward the corridor (staff points -x), face `hopeful`; both stewards idle | `happy`, staff flares on the beat, one step toward the corridor; both stewards go to "world turns away": paddles at hip, gates shut, nearby dancers `stare` at him (route = the Bassment) | staff dim, `shrug` with `sulk` | `nod` and a staff flare | S: `usher` toward the corridor and walks off. F: `shrug`, `shame` |
| `led_wall` (return) | `disco_ball`, lowered to y 3.6 | ball slow, dim | ball spins fast, facets spray, floor tiles switch to the ball's pattern, a dancer `point`s up with `cheer` | ball slow, a dancer points up with `sulk` | tilt-wobble toward the camera | S: floor flares; F: tiles blank for a bar |

**Default clarity.** From beat 0 the east steward is the only happy, paddle-up person and the east shutter the only open gate; the west steward visibly wants you (still beckoning) but is sad. Touching her flips the pair: that teaches the whole system in the first choice of the run.

**Create.**
* Objects: `ch_wh_shutter` NEW, 3 frames (down, half, up), 128 x 128 (2.4 m x 2.4 m), thing at (6.95, 2.5) y 1.2, anchored for the walk to `to_bar`. `ch_wh_scissor_gate` NEW, 3 frames (closed, half, open), 128 x 128 (2.1 m), thing at (-6.95, 1.75) y 1.05.
* People: wardrobe `steward` (hi-vis vest with a chest pictogram, glow baton, headset) for existing `c02`, `c03` (pin their homes); NEW actor `wz_floor` (wardrobe `wizard`: robe, pointed hat, long beard, staff; replaces the billboard `wizard_floor`; remove `warehouse.wizard` from `NO_ACTOR` and give it an `acting` block).
* Held props: paddle_pint, paddle_stairs (0.5 m disc, 12 px pictogram), staff (2 frames: lit, unlit).
* Faces: `hopeful`, `sulk`. Acts: `hold_up`, `hold_low`, `usher`, `shrug`, `turn_away` (existing `beckon`, `clap`, `cheer`, `nod`, `recoil`, `stare`, `point`).
* Animations: LED chevron chase toward a gate (X1); `light` ops for the two gate spills (E7); crowd cast lines for the ring and the "turns away" beat.
* Map edits: waypoint `floor_choice`; home `g07` to (-1.6, 3.8) and drop its `side`; `disco_ball` y 3.6; hotspot anchors: `exit_bar` thing `ch_wh_shutter` + extra actor `c03`; `exit_balcony` thing `ch_wh_scissor_gate` + extra actor `c02`; `wizard` anchor actor `wz_floor`.

### 2.2 `warehouse.bar` The Bar - P1, L

**Story.** The bar room: a counter along the east wall, pendant lamps, a bead curtain in the south wall to the chill-out, a door in the west wall back to the floor (and the booth). The bartender will serve you, a hooded stranger in the corner has something for you, and once you have the stranger's pass a lantern appears on the bar.

| Option | Anchored on today | Leads to / success / failure | Seen today (home (8.2, 3.0) yaw -90) |
| --- | --- | --- | --- |
| `warehouse.bar.exit_chill` **DEFAULT** | waypoint `bar_to_chill` (9, 5.55), the curtain in the south wall | `warehouse.chill`; failure same, stagger -5 | +73: out of view |
| `warehouse.bar.exit_booth` | waypoint `bar_door` (7.55, 2.5), the west door | `warehouse.booth`; failure same, stagger -5 | -142, behind the camera, 0.8 m |
| `warehouse.bar.bartender` | actor `b01` (11.2, 2.2) | success `wh_drink`, walk to the taps, +6, variation; failure `wh_spilled`, -8; both then take the default route | -15, in view; only a wave |
| `warehouse.bar.stranger` (secret, once; `flags_none wh_vip_pass, wh_stranger_gone`) | actor `b03` (9.6, 4.6) | success `wh_vip_pass`, whisper, +2; failure `wh_stranger_gone`, -3 | +49, edge; a flicker light |
| `warehouse.bar.ember` (portal; needs `wh_vip_pass`) | pos (10.0, 1.0, 5.0) | success route `path:ember`; failure -4 | +48, edge; a pulse of light |

**Window vantage** `bar_choice` NEW (7.6, 0.6) yaw -155 (the north-west corner by the floor door, looking diagonally across the room). Bearings: door +42 (2.0 m), curtain +10 (5.6 m), bartender -41 (3.9 m), stranger / lantern -2 / -4 (4.5 to 5 m, centre; never both at once), curtain keeper `b04` -6 (5.4 m), roadie in the doorway +49 (2.2 m).

**Concept: two exits with a person each, and a drink.** *Curtain* (default): a bead curtain tied back by a patron (`b04`) with the chill-out's pink glow behind it. *Door*: a door leaf ajar onto the floor's strobe, a **roadie** (headphones round his neck) in the doorway beckoning. The route pair works like the Floor's: the current way is open and its person cheerful; the other is shut/hanging and its person sulking. *The drink* (stop) is the owner's own example: the bartender **slides the pint along the counter to you** when current and **pulls it back to his chest** when not. *The stranger* slides a matchbook across the table when current and turns his back when not; *the ember* is a lantern on the table whose flame leans toward you when current.

| Option | Embodied by | Idle / invitation | CURRENT | NOT CURRENT | Touched (within 1 beat) | Commit S / F |
| --- | --- | --- | --- | --- | --- | --- |
| `exit_chill` | `ch_wh_bead_curtain` at (9, 6.0) + `b04` at (10.4, 5.2) | default from beat 0: curtain tied back (frame 3), pink light spilling, `b04` `usher` with a cup, `happy` | as idle; at 48 she adds a `beckon` | curtain hanging and swaying (frame 1), `b04` `sulk`, cup lowered | curtain frame swap; `b04` `hopeful` then `happy` | S: `b04` `cheer`; F: curtain whips shut (frame 1), `b04` `shrug`, camera staggers |
| `exit_booth` | `ch_wh_door_leaf` at (7.0, 2.5) + NEW actor `rd01` (roadie) at (6.7, 2.6) | door leaf shut; at 48 the roadie `beckon`s with headphones raised (`hold_up`) and a leaf crack of white strobe | leaf wide (frame 3), roadie `happy`, headphones up | leaf shut and rattling on the kick, roadie `lean_wall` `sulk` | leaf frame swap in one beat, roadie `hopeful` | S: roadie `usher`, `cheer`; F: leaf bangs shut once, roadie `shrug` |
| `bartender` (stop) | `b01` + `ch_wh_pint` on the counter | wiping a glass, pint at his end; at 48 `beckon` twice on the counter | `slide`: pint travels the counter to the near end (stops 1 m from the camera line), `wink`/`nod`; route stays shown open (curtain), `b04` goes QUEUED | `withhold`: pint hugged to his chest, `smug` shake of the head | slide starts the beat of the touch (X2) | S: glass lands in front of you, `nod` `relief`. F: glass tips (frame), `block` `anger` (existing failure act) |
| `stranger` (secret) | `b03` re-dressed `hood`, `ch_wh_matchbook` on his table | hunched, hood up, matchbook glinting; at 48 two-finger `beckon` | hood pushed back (face `wink`), slides the matchbook across | hood up, `turn_away`, matchbook pocketed | frame swap in one beat | S: matchbook arrives, he `nod`s. F: he stands and leaves (`hide`) |
| `ember` (portal) | `ch_wh_lantern` at (10.0, 5.0) | unlit lantern appears after the pass (stranger gone); at 48 a low flame | flame tall, leaning toward the camera, motes; route = path (both doors shown shut, patrons `stare` at the flame) | flame small, leaning away, lantern door half shut | flame frame swap | S: flame flares white, room stills (passage frame). F: flame gutters, -4 |

**Default clarity.** The curtain is open with a smiling person from beat 0; the door is shut with a roadie who looks glum. Pint on the counter; nothing else moves until beat 48.

**Create.**
* Objects: `ch_wh_bead_curtain` NEW 3 frames 128 x 128 (hang, sway, tied back); `ch_wh_door_leaf` NEW 3 frames (shut, ajar, wide) 128 x 128, reused at the balcony (2.3) and chill-out (2.4); `ch_wh_pint` NEW sprite 32 x 32 with a 3-stop counter path (X2); `ch_wh_matchbook` NEW 2 frames 16 x 16; `ch_wh_lantern` NEW 3 frames (unlit, low flame, tall flame) 48 x 64.
* People: NEW actor `rd01` (wardrobe `roadie`: black tee, cap, headphones round neck, tape roll on belt) at (6.7, 2.6); `b03` re-dressed (`hood`); `b04` directed (curtain keeper).
* Faces: `sulk`, `hopeful`, `smug`, `wink`. Acts: `slide`, `withhold`, `usher`, `turn_away`, `lean_wall`, `hold_up` (with the existing headphones prop), `shrug`.
* Animations: pint slide path (X2); `light` ops for the pink and white spills (E7); lantern flame lean.
* Map edits: waypoint `bar_choice`; home `rd01`; `b04` pinned at the curtain; hotspot `exit_booth` anchors thing `ch_wh_door_leaf` + actor `rd01`, `exit_chill` thing `ch_wh_bead_curtain` + actor `b04`.

### 2.3 `warehouse.balcony` The Balcony - P1, M

**Story.** The mezzanine above the floor, a rail over the dance floor on the east side, a door and steps down to the floor, stairs along the north end up to the booth, a promoter by the stair rope. Once you have looked over the rail, a star appears in a high window.

| Option | Anchored on today | Leads to / success / failure | Seen today (home (-9, 1.5) yaw -90) |
| --- | --- | --- | --- |
| `warehouse.balcony.exit_chill` **DEFAULT** | waypoint `balcony_door` (-7.8, 1.0) | `warehouse.chill`; failure same, stagger -5 | -23, but 1.3 m away: a ring |
| `warehouse.balcony.exit_booth` | waypoint `balcony_stairs` (-9.25, -2.55) | `warehouse.booth`; stagger -5 | -94, behind |
| `warehouse.balcony.rail` (once; `flags_none wh_saw_floor`) | pos (-7.15, 1.2, 1.0) | success `wh_saw_floor`, look over, +4, variation; failure vertigo -6 | -15, 1.9 m: a glow |
| `warehouse.balcony.promoter` | actor `v03` (-8.2, -2.2) | success route **booth** + `wh_promoter_nod` +4; failure snub -4 (then the default, chill) | -78, behind |
| `warehouse.balcony.star` (portal; needs `wh_saw_floor`) | pos (-10.4, 1.8, 0.8) | success route `path:gospel`; failure -4 | behind (-153) |

**Window vantage** `balcony_choice` NEW (-8.6, 4.4) yaw 5 (the south end of the mezzanine, looking up its length). Door +18 (3.5 m), rail raver +32 (2.5 m), stairs and rope -1 (6.6 m), promoter +8 (6.6 m), skylight -28 (4.3 m).

**Concept: the dog.** A glow-collared club dog (an animal leading one way; owner's list) stands at one of two spots: by the door (A) or at the foot of the stairs (B). **The dog is the route marker**: it trots to the current way. The stair end also has a velvet rope (hooked or unhooked) held by the promoter; the door end a door leaf. The rail has a raver leaning over pointing down; the star is a skylight.

| Option | Embodied by | Idle / invitation | CURRENT | NOT CURRENT | Touched (within 1 beat) | Commit S / F |
| --- | --- | --- | --- | --- | --- | --- |
| `exit_chill` | `ch_wh_dog` at spot A (-8.3, 1.9) + `ch_wh_door_leaf` at (-7.8, 1.0) | default from beat 0: dog sitting at A facing the door, tail wagging, looks back at the camera on the 2 and 4; leaf ajar with floor light | dog stands, tail up; leaf wide | dog elsewhere (at B), leaf shut | the dog starts its trot the beat of the touch (2 beats to arrive, X3) while the leaf swaps | S: dog bounds through the door; F: dog yelps and skids (a stagger of its own) |
| `exit_booth` | rope `ch_wh_velvet_rope` at (-9.25, -2.2) + promoter `v03` | rope hooked across the stairs; promoter arms folded; at 48 he `beckon`s | dog at B facing the stairs; rope unhooked and lying; promoter `usher`, `happy` | rope hooked, promoter `lean_wall` `sulk` | rope frame in one beat | S: promoter steps aside; F: rope whips back |
| `promoter` (route booth, a gamble: failure goes chill) | `v03`, rope end in hand, tickets | tickets in the other hand; at 48 `offer` | holds the rope end (`hold_up`) and tickets out (`offer`), `happy`; dog trots to B (route = booth) | `shrug`, tickets pocketed, `sulk` | as above | S: unhooks the rope and `nod`s; F: hooks it back, `shake_head` (dog trots back to A) |
| `rail` (stop, once) | `v02` re-homed to the rail (-7.5, 2.2), leaning over | leaning over, pointing at the floor with `awe` | `point` + `cheer`, waves you over (`beckon`) | stands straight, `shrug`, `sulk` | pose swap | S: you lean over (existing `rail_look`); F: `recoil`, vertigo |
| `star` (portal) | `ch_wh_skylight_star` high in the west wall (-10.9, 0.8) y 2.2 | dim star (frame 1); appears once `wh_saw_floor` is set | star bright with a shaft of light across the floor, the dog sits and looks up (route = path: door and rope both shut) | dim star | frame swap | S: shaft widens to white (passage). F: star dims, -4 |

**Default clarity.** The dog sits at the open door, tail wagging; the stairs are roped off. The dog is the thing a player will tap or follow: pressing the rope sends it trotting across the room.

**Create.**
* NEW non-person figure `ch_wh_dog` (N5): about 0.5 m high, ~32 x 40 px; frames sit (1), tail-wag (2), trot (4), look-back (1), bark (2); mirrored for direction; collar glow is part of the sprite (a plain ring, no colour dependence). Played through the existing `figure` acting contract (E8) and a trot path between waypoints `dog_a` (-8.3, 1.9) and `dog_b` (-9.0, -0.6) NEW.
* Objects: `ch_wh_velvet_rope` NEW 2 frames (hooked across, unhooked lying) 64 x 64, reused at the Door (2.6); `ch_wh_door_leaf` (from 2.2); `ch_wh_skylight_star` NEW 3 frames (dim, bright, bright plus shaft) 128 x 128 plus the existing `beam` PNG.
* People: `v02` re-homed to the rail; `v03` directed (rope end prop). Held props: rope_end.
* Faces: `sulk`, `hopeful`. Acts: `usher`, `hold_up`, `lean_wall`, `shrug`.
* Map edits: waypoints `balcony_choice`, `dog_a`, `dog_b`; things `ch_wh_velvet_rope`, `ch_wh_skylight_star`, `ch_wh_door_leaf`; `balcony.star` anchor thing `ch_wh_skylight_star`.

### 2.4 `warehouse.chill` The Chill-out - P2, M

**Story.** A low room of sofas, festoon bulbs and a lava lamp. One exit (back to the door). The choice is stop or go: sink into the sofa, stare at the lamp, or move on. The wizard waits here too.

| Option | Anchored on today | Leads to / success / failure | Seen today (home (10, 9) yaw 0) |
| --- | --- | --- | --- |
| `warehouse.chill.exit_exit` **DEFAULT** | waypoint `chill_door` (10.5, 6.55) | `warehouse.exit`; failure stagger -5 | +12, 2.5 m: ring and a slit |
| `warehouse.chill.sofas` | thing `sofa_left` (7.9, 6.45) | success `wh_rested`, +10 (walk to the sofa nook); failure `wh_dozed`, -10; both then the default exit | -39, a glow on the sofa |
| `warehouse.chill.wizard` (EARLY; `flags_none wh_wizard_met`) | thing `wizard_chill` (8.4, 9.7), billboard | success route `1` (the Bassment); failure shrug -2 | -114, **behind** |
| `warehouse.chill.lavalamp` | thing `lavalamp` (11.4, 6.45) | +5 variation / -3 dip | +29, a pulse |

**Window vantage** `chill_choice` NEW (9.6, 11.4) yaw 0 (the back of the room by the rear sofa; sector `sofa_a`). Door +10 (4.9 m), buddy +8 (4.3 m), sofa pals -8 (4.2 m), sofa -19 (5.2 m), lamp +20 (5.3 m), trapdoor -33 (2.4 m), wizard -35 (3.3 m).

**Concept: sink or go.** The two friends on the sofa (`s02`, `s03`) pat the cushion beside them; a friend in the doorway with a coat over his arm and car keys waves you out. Whichever is current is happy and active, the other droops. The lava lamp is the third voice: blobs rising and bright vs settled and dim. The wizard stands by a **trapdoor** in the floor, its lid propped open with light underneath when he is current (the same trapdoor-and-lamp idiom as the corridor firedoor of the Floor).

| Option | Embodied by | Idle / invitation | CURRENT | NOT CURRENT (or QUEUED when a stop is current) | Touched | Commit S / F |
| --- | --- | --- | --- | --- | --- | --- |
| `exit_exit` | NEW actor `cb01` (coat friend) at (10.2, 7.1) in the doorway + `ch_wh_door_leaf` at (10.5, 6.55) | default from beat 0: leaf wide with floor strobe, `cb01` coat over arm, `tug`, `happy` | as idle, `usher` on the bar | NOT: `lean_wall`, arms folded, `sulk`, leaf ajar a crack. QUEUED: `nod`, `neutral`, leaf stays wide | face/pose swap, leaf frame | S: `cb01` `cheer`; F: leaf slams, `shrug` |
| `sofas` (stop) | `s02`, `s03` seated; sofa `sofa_left` | chatting; at 48 `pat_seat` | both `pat_seat`, `happy`, leaning toward the camera | `yawn` face, `sit`, heads on each other | `pat_seat` within the beat | S: they shuffle apart for you, `cheer`; F: they `laugh` as you doze (existing cast) |
| `lavalamp` (stop) | `lavalamp` thing with frames | blobs low, slow | blobs high and fast, glow pulses each beat, pink wash on the wall | settled, glow slow and dim | frame swap, speed x2 (X5) | S: wash blooms; F: lamp flickers out |
| `wizard` (early) | NEW actor `wz_chill` at (7.7, 8.7) + `ch_wh_trapdoor` at (8.3, 9.4) | lid shut, staff lit, `beckon` at the trapdoor, `hopeful` | lid up (frame 3) with warm light under it, wizard `happy`; the door friend goes calm | lid down, wizard `shrug`, `sulk` | lid frame swap | S: wizard `usher`, descends; F: `shrug`, `shame` |

**Default clarity.** The doorway friend is the only one in motion at beat 0; the lamp is quiet; the sofa is a still tableau. At 48 the sofa pals begin to pat the seat: a clear second option, with a sad friend in the door when tapped.

**Create.**
* People: NEW actor `cb01` (coat friend, a raver with a coat over one arm); `wz_chill` (second instance of the wizard from 2.1). Props: coat (held over arm).
* Objects: `ch_wh_trapdoor` NEW 3 frames (shut, ajar, open with light) 128 x 128 (1.5 m); `thing_lavalamp` 2 new frames (settled, rising) 64 x 64; door leaf (2.2).
* Faces: `yawn`, `sulk`, `hopeful`. Acts: `pat_seat`, `tug`, `lean_wall`, `usher`, `shrug`.
* Animations: lamp blob speed (X5).
* Map edits: waypoint `chill_choice`; homes `cb01`, `wz_chill`; hotspot `sofas` anchor extra actors `s02`, `s03`; `exit_exit` thing leaf + actor `cb01`.

### 2.5 `warehouse.booth` The Booth - P3, M

**Story.** Up on the stage you are the DJ: decks in front, the floor beyond, an old radio on the speaker stack. Stops: drop the record, put on the headphones (needs the stranger's pass), tune the radio (the Squadron path). One way on: down the steps to the floor.

| Option | Anchored on today | Leads to / success / failure | Seen today (home (0, -9) yaw 180) |
| --- | --- | --- | --- |
| `warehouse.booth.exit_exit` **DEFAULT** | waypoint `booth_down` (-0.75, -8.4) | `warehouse.exit`; stagger -5 | +51, 1 m: ring |
| `warehouse.booth.decks` | pos (0, 1.1, -8.25) | success `wh_dj_set`, +8, variation; failure wrong record -8, dip | dead ahead, 0.8 m, at the bottom edge of the frame |
| `warehouse.booth.headphones` (secret, once; needs `wh_vip_pass`) | thing `headphones_booth` (0.9, -8.4) | success `wh_headphones` +6; failure -3 | -56, edge |
| `warehouse.booth.radio` (portal) | pos (1.5, 1.2, -9.4) | success route `path:squadron`; failure -4 | -105, **behind**: an edge beacon (A9 already flags it) |

**Window vantage** `booth_choice` NEW (0, -9.7) yaw 180 (the DJ stands at the back wall; sector `booth`). Decks dead ahead 1.4 m, headphones -35 (1.6 m), radio (re-sited to (-1.0, -8.6)) +42 (1.5 m), the crowd and steps beyond at 0 (5.2 m). A close-up of the table; the room beyond is the context.

**Concept: the DJ's table.** Three objects on the table, each with an on/off state you can read at a glance, and the front row reaching up for you. The radio is an old valve set with an aerial; when tuned a bomber's shadow drifts over the back wall (the existing `thing_bomber_shadow`).

| Option | Embodied by | Idle | CURRENT | NOT CURRENT | Touched | Commit S / F |
| --- | --- | --- | --- | --- | --- | --- |
| `exit_exit` | the front row: existing `c10`, `g03`, `e01` re-homed to the stage lip (-1.6, -3.2), (0.2, -3.0), (1.8, -3.2) | default from beat 0: arms up reaching (`beckon`), `happy` | as idle, `tug` | arms drop, `turn_away` to the decks, `sulk`. QUEUED: bounce `cheer` small | pose swap | S: they part and cheer; F: they `laugh`, lurch (existing stagger) |
| `decks` (stop) | `thing_decks` with 3 frames | platter slow, stylus up | stylus down, platter at speed, VU lit to the beat, nearest stack pumps double | platter stopped, crossfader parked | frame swap | S: crowd erupts (cast); F: record-scratch frame, crowd `recoil` |
| `headphones` (secret) | `thing_headphones` with 2 frames and a gold lanyard | flat on the table | lifted off the table, swinging on its cable toward the camera, lanyard glint | flat, dim | frame swap | S: they settle on the ears; F: they slip and fall |
| `radio` (portal) | `thing_booth_radio` with 3 frames + `thing_bomber_shadow` | dial dim; at 48 the dial crackles | dial warm, aerial extended, bomber shadow drifts across the back wall | dial dim, aerial down, shadow off | frame swap | S: static roars into engine noise (passage); F: crackle dies, -4 |

**Create.** Objects: `thing_decks` 3 frames (idle, stylus down A, B) 128 x 128; `thing_headphones` 2 frames 64 x 64; `thing_booth_radio` 3 frames (off, crackle, tuned plus aerial) 128 x 128, re-sited to (-1.0, -8.6); `thing_bomber_shadow` control (piece on/off). People: front-row re-homes; acts `tug`, `turn_away`, `shrug`; faces `sulk`. Map: waypoint `booth_choice`. Animations: platter/VU sync on the beat.

### 2.6 `warehouse.exit` The Door - P1, L

**Story.** The last room of the Warehouse: a short entrance with a bouncer, a tunnel to the outside that goes cyan with something like a tractor beam, and a crack in the wall glowing orange. Mothership or Underworld. The bouncer is a gamble on the Mothership: succeed and he lets you through; fail and he throws you at the crack.

| Option | Anchored on today | Leads to / success / failure | Seen today (home (0, 11.2) yaw 0, **facing the floor**) |
| --- | --- | --- | --- |
| `warehouse.exit.exit_mothership` **DEFAULT** | waypoint `tunnel` (0, 16) | `mothership`; failure same, stagger -5 | 180: **behind**, 4.8 m |
| `warehouse.exit.exit_underworld` | thing `crack_door` (2.85, 10.7) | `underworld`; stagger -5 | +80, on the right wall |
| `warehouse.exit.bouncer` (`flags_none wh_vip_pass`) | actor `d01` (-2.4, 12.0) | success route mothership, `wh_door_clear` +4; failure route **underworld**, `wh_thrown_out`, thrown out -6 | -108, behind |
| `warehouse.exit.bouncer_vip` (`flags_all wh_vip_pass`) | actor `d01` | success mothership, `wh_guest_list` +6; failure mothership -3 (scuffed pass) | -108 |

**Window vantage** `door_choice` NEW (0, 9.2) yaw 180 (just inside the entrance from the floor, facing the tunnel). Tunnel gate dead ahead (4 to 6.8 m), crack door -30 (4.3 m; moved to the south-wall stub at (2.2, 12.95)), bouncer +31 (4.1 m; re-homed to (-2.1, 12.7)), velvet rope +14 (3.7 m). The walk waypoint `door_r` moves to (2.2, 12.4) yaw 180 so the Underworld walk goes to the crack.

**Concept: the doorman between two doors.** Three things line up in the frame: tunnel (centre), crack door (left), bouncer (right) with a velvet rope between him and the tunnel. The tunnel is the default and idles OPEN (gate up, rope unhooked, cyan shaft with drifting dust). The crack idles as a hairline glow. When the **bouncer** is current the route is UNDECIDED: the tunnel gate eases half shut, the rope hooks, the crack gapes half, and he stands square in the middle, arms unfolded, hand to his ear (listening). That is the gamble made visible; success unhooks the rope and he steps aside; failure he points at the crack and the crack opens wide.

| Option | Embodied by | Idle | CURRENT | NOT CURRENT | Touched | Commit S / F |
| --- | --- | --- | --- | --- | --- | --- |
| `exit_mothership` | `ch_wh_tunnel_gate` at the tunnel mouth (0, 13.0) | open (frame 3), rope unhooked | open, shaft pulses on the kick; bouncer steps beside it, `usher` (non-VIP: `shrug`) | half shut (frame 2), rope hooked | gate frame swap in one beat | S: gate spreads, bouncer `nod`; F: bouncer `stamp` and shoves (existing stagger) |
| `exit_underworld` | `thing_crack` with 3 frames at (2.2, 12.95) | hairline, flicker | split wide, red-orange spill, sulphur wisp; bouncer `turn_away`, `shrug` ("your funeral") | hairline | frame swap | S: heat blast, camera pulled in; F: crack closes a notch |
| `bouncer` | `d01` + `ch_wh_velvet_rope` | `block` beside the tunnel, `neutral`; at 48 `stare` at you | UNDECIDED: square in the middle, `stare` with `doubt`, hand to ear; tunnel and crack both half | arms folded | pose swap, both doors move to half | S: unhooks rope, `nod` `smug`; F: `point` at the crack, crack wide, `stamp` (existing `thrown_out`) |
| `bouncer_vip` | `d01`, clipboard with a gold sticker | rope already unhooked, `beckon`, clipboard up (`hold_up`) | `bow`, `relief` | `shrug` | pose swap | S: `bow`; F: `shake_head`, rope hooked a moment |

**Default clarity.** The tunnel is open and lit; the bouncer stands beside it, not in it; the crack is a dim line. A first-timer sees an open way and a mean-looking doorman between two doors, and the music tells them what pressing the doorman means.

**Create.** Objects: `ch_wh_tunnel_gate` NEW 3 frames (shut with a cyan seam, ajar, open with a shaft) 128 x 128 (2.4 m); `thing_crack` 3 frames (hairline, half, wide with heat shimmer) 128 x 128; `ch_wh_velvet_rope` (from 2.3). People: `d01` directed. Faces: `smug`, `sulk`. Acts: `shrug`, `turn_away`, `usher`, `lean_wall`, `hold_up` (clipboard exists). Animations: `light` ops for the cyan and orange spills (E7); dust motes in the shaft. Map edits: waypoint `door_choice`; `crack_door` re-sited; `door_r` moved; `d01` home; hotspot `exit_underworld` anchor thing `crack_door`, `bouncer` anchors actor `d01` + thing `ch_wh_velvet_rope`.

## 3. The Mothership (`mothership`, an alien ship's ring deck; greys, antennae, blobs, insects, cyclops, tentacles)

Language: iris doors, hover-drones, holograms, pipes and consoles; teal, violet and amber hazard. Aliens read by silhouette (a grey's big head, an insect's mandibles), so poses are exaggerated; species face rules apply to each new face (a grey `sulk` is drooping lids and a down-turned slit mouth; a cyclops `sulk` is a lowered lid over the one eye; an insect's mandibles droop).

Shared pieces: **`ch_ms_iris_door`** (3 states: sealed, half, open) in three skins (wreath of soft lamps for gallery and bridge doors; hazard chevrons plus a spinning amber beacon for the reactor; medical white for the exam bay): 9 frames, used in 2 to 4 instances per scene. **`ch_ms_drone`** (N6), a hover-drone figure (a jelly orb with two lamp eyes and a small tray arm) in two variants: *usher* (perks its lamp up, glides) and *waiter* (carries a tray of glowing orbs).

### 3.1 `mothership` The Deck (entry) - P1, M

**Story.** The ring-shaped rave deck. Two doors in the east wall, 2.3 m apart: the gallery (a viewing lounge) and the reactor. A grey wonders at you; the alien DJ on the dais wears his headphones the wrong way round.

| Option | Anchored on today | Leads to / success / failure | Seen today (home (0, 6.5) yaw 0) |
| --- | --- | --- | --- |
| `mothership.exit_gallery` **DEFAULT** | waypoint `deck_gallery_door` (6.3, 5.5) | `mothership.gallery`; stagger -5 | +81: out of view |
| `mothership.exit_reactor` | waypoint `deck_reactor_door` (6.3, 7.8) | `mothership.reactor`; stagger -5 | +102: out |
| `mothership.grey` | actor `g08` (-0.59, 3.42) | success `ms_grey_friend`, +5 (walk to the ramp); failure `ms_probed`, -7 (stagger to the corner) | -11: in view, a wave |
| `mothership.dj` | actor `m01` on the dais (1.2, -3.9) | success `ms_dj_pal`, +6, variation (climb to the dais); failure `ms_feedback`, -6, dip | +7, 10.5 m: small |

**Window vantage** `deck_choice` NEW (-4.2, 6.9) yaw -65 (the south-west of the deck, looking toward the east wall and the dais). DJ -38 (12 m), grey -19 (5.0 m), gallery door +17 (10.6 m), reactor door +30 (10.5 m).

**Concept: the drone that leads.** A hover-drone (an "animal leading one way") hovers beside the current door with its lamp up. The doors are different shapes so the pair reads without colour: the gallery door is ringed with a wreath of round lamps and has a potted plant beside it; the reactor door has hazard chevrons and a spinning amber beacon. The current door's iris is open; the other is sealed. Tapping the sealed door: the iris opens, the drone glides across (1.5 beats), the beacon speeds up.

| Option | Embodied by | Idle / invitation | CURRENT | NOT CURRENT | Touched | Commit S / F |
| --- | --- | --- | --- | --- | --- | --- |
| `exit_gallery` | `ch_ms_iris_door` (wreath) at (6.3, 5.5) + usher drone | default from beat 0: iris open (frame 3), drone beside it, lamp up, bobbing | same, bobs at the beat | iris sealed, drone elsewhere | iris frame swap; drone glides across | S: drone `perk`, iris dilates, light floods; F: iris stutters shut, drone droops, camera staggers |
| `exit_reactor` | `ch_ms_iris_door` (hazard) at (6.3, 7.8) + beacon | sealed; the beacon turns slowly; at 48 the beacon jitters | iris open (teal light and heat shimmer), drone beside it, beacon fast | iris sealed, beacon slow | as above | S/F as above |
| `grey` (stop) | `g08` with an orb in hand (existing orb wand prop) | dancing; at 48 `beckon` with `awe` | `hopeful`, `offer` the glowing orb, `nod`; the doors go QUEUED (drone stays, calm) | `turn_away`, hand over the huge eyes, `sulk` | pose swap | S: `cheer` `awe`, orb floats to you; F: `recoil` `fear` (existing) |
| `dj` (stop) | `m01` on the dais; existing pieces `ring_lights`, `hologram_dome` | spins his disc, headphones wrong way; at 48 `laugh` and point | `laugh`, `point` at the camera; ring lights and dome pulse on the beat | `shrug`, headphones slip over his face, `sulk`; dome and ring dark | pieces on/off the same beat | S: `cheer`; F: feedback squeal frame, `shake_head` |

**Default clarity.** The drone sits at the gallery's lit wreath door from the first beat; the hazard door is sealed with a slow beacon. Nothing needs reading.

**Create.**
* Objects: `ch_ms_iris_door` NEW (wreath and hazard skins here; 3 frames each; 128 x 128, 1.2 m x 2.2 m, on the east wall), `ch_ms_beacon` as part of the hazard skin (2 frames).
* Figure: `ch_ms_drone` usher variant NEW (frames: bob 4, glide 2, perk 1, droop 1; about 0.5 m, 32 x 32 px; E8).
* People: `g08`, `m01` directed (acts exist except `turn_away`, `shrug`). Faces: `hopeful`, `sulk`. Acts: `turn_away`, `shrug`.
* Map: waypoint `deck_choice`; doors become things (iris) at the two waypoints; hotspot anchors thing iris + extra figure drone.

### 3.2 `mothership.gallery` The Gallery - P2, M

**Story.** A long viewing lounge: a planet outside the south window, a holographic menu on the north wall, one way on at the far east end. Two aliens stare at the planet. Stops: look out of the window; order from the menu.

| Option | Anchored on today | Leads to / success / failure | Seen today (home (8.6, 6.5) yaw -90) |
| --- | --- | --- | --- |
| `mothership.gallery.exit_bridge` **DEFAULT** | waypoint `gallery_east` (26.3, 7.5) | `mothership.bridge`; stagger -5 | +3, 17.7 m away: a slit |
| `mothership.gallery.window` | thing `glow_g` (10.0, 9.6) | success `ms_saw_planet` +5, variation (walk to the window); failure a cruiser glares, -5 (stagger to the west) | +66: out |
| `mothership.gallery.menu` | thing `menu_g` (23.0, 3.5), piece `gallery_holo_menu` | success `ms_ordered` +8; failure `ms_bad_order` -6 | -12, 14.7 m: small |

**Window vantage** `gallery_choice` NEW (15.5, 4.0) yaw -125 (mid-hall at the north wall, looking south-east). Exit -17 (11.4 m), menu -39 (7.5 m), window re-sited to (17.0, 9.8) +40 (6.0 m).

**Concept: blinds, menu, door.** The long window has **louvre blinds**: open (planet and a cruiser drifting by) when current, shut (slats) when not. The menu is a hologram pillar that unfolds and offers a dish on a **waiter drone's tray** when current, collapses to a pillar when not. The far door is an iris that stands open with a stream of light when it is the current way.

| Option | Embodied by | Idle / invitation | CURRENT | NOT CURRENT | Touched | Commit S / F |
| --- | --- | --- | --- | --- | --- | --- |
| `exit_bridge` | `ch_ms_iris_door` (wreath skin) at the far end + gallery crew `gallery_c01` `wave` | default from beat 0: iris open with a long shaft of light down the hall; at 48 `gallery_c01` beckons from the doorway (a speck at 11 m: the shaft is the cue) | iris open, shaft pulsing | iris half sealed | frame swap | S: shaft widens; F: iris stutters, stagger |
| `window` (stop) | `ch_ms_window_blind` (3 frames) + piece `gallery_cruiser` + `gallery_c03`, `gallery_c05` | blinds half; the two aliens stare out (`awe`) | blinds fully open, planet blazing, cruiser glides in (piece on, bob), aliens `point` and `cheer` | blinds shut (slats), aliens `shrug`, `sulk` | blind frame swap, cruiser on in the same beat | S: cruiser passes, awe; F: cruiser's searchlight sweeps you, aliens `recoil` |
| `menu` (stop) | piece `gallery_holo_menu` (2 frames) + waiter drone | dim pillar; at 48 the drone arrives with an empty tray | menu unfolds into a ring of dish glyphs, one rises onto the tray, drone `perk` | pillar collapsed, drone `droop` and backs off | frame swap, drone glides 1.5 beats | S: dish orb floats to you; F: dish spits a sooty puff |

**Default clarity.** The far door glows and its shaft lies down the whole hall from beat 0; the blinds are partly open and the menu is a quiet pillar.

**Create.** Objects: `ch_ms_window_blind` NEW 3 frames (shut, half, open) 256 x 128 on the south wall; `gallery_holo_menu` piece 2 new frames (collapsed, unfolded) 128 x 128; iris wreath skin instance at (26.3, 7.5). Figures: waiter drone variant NEW (adds a tray, 2 frames). Faces: `sulk`. Acts: `shrug`, `turn_away`. Map: waypoint `gallery_choice`; window `glow_g` re-sited to (17.0, 9.8); hotspot `window` anchor thing blind.

### 3.3 `mothership.reactor` The Reactor - P3, M

**Story.** A catwalk over the reactor pit. The core glows below, an engineer waves up from the floor, the way on is the far end of the catwalk. Stops: throw the switch to surge the core (risk: alarm), help the engineer.

| Option | Anchored on today | Leads to / success / failure | Seen today (home (30.5, 7.5) yaw 0) |
| --- | --- | --- | --- |
| `mothership.reactor.exit_bridge` **DEFAULT** | waypoint `catwalk_bridge` (40.2, 7.5) | `mothership.bridge`; stagger -5 | +90: out |
| `mothership.reactor.core` | thing `core_r` (34, -2.6, y 5.5) | success `ms_surge` +8 variation (climb to the core); failure `ms_alarm` -8 dip (run) | +19, 10.7 m (ring) |
| `mothership.reactor.engineer` (`flags_none ms_badge`) | actor `reactor_s01` (28.9, 0.6), down in the pit | success `ms_badge` +4; failure `ms_shooed` -3 | -13, 7.1 m (ring, a plead act) |

**Window vantage** `reactor_choice` NEW (28.5, 8.5) yaw -45 (the west end of the catwalk). Core -19 (12.4 m), engineer -42 (7.9 m), boom barrier +40 (11.7 m), the new lever +12 (2.7 m).

**Concept: the lever.** A big knife-switch on the catwalk rail within arm's reach. When the core is current, the lever is thrown down, the control rods rise out of the core, the ring spins fast and steam vents; when not, the lever is up and the core is calm. The engineer holds a badge up toward you from the pit. The way on is a striped **boom barrier** at the far end: raised for the current way; its post lamp pulses.

| Option | Embodied by | Idle | CURRENT | NOT CURRENT / QUEUED | Touched | Commit S / F |
| --- | --- | --- | --- | --- | --- | --- |
| `exit_bridge` | `ch_ms_boom_barrier` at (40.2, 7.5) | default from beat 0: boom up, post lamp slow | boom up, lamp fast on the beat | QUEUED (a stop is current): boom up, lamp slow. (There is no second exit, so "not current" is the queued state.) | lamp speed swap | S: boom nods; F: boom drops and bounces, stagger |
| `core` | `core_r` + `ch_ms_lever` (2 frames) + `ch_ms_core_rods` (2 frames); pieces `reactor_core_ring`, `reactor_steam`, `reactor_pylon_arcs` | lever up, rods in, ring slow | lever down, rods out, ring fast, steam on, arcs flicker | lever up, rods in, ring slow | lever and rods swap on the beat | S: surge flares, camera climbs; F: rods slam, lamps flash, run |
| `engineer` | `reactor_s01` with a badge prop | `plead` at the pit rail; at 48 `hold_up` the badge | `nod`, `hopeful`, badge up toward the camera | `sulk`, badge lowered, `turn_away` to a console | pose swap | S: `nod` `relief`; F: `collapse` (existing) |

**Create.** Objects: `ch_ms_lever` NEW 2 frames 64 x 64 on the catwalk rail at (30.8, 7.0); `ch_ms_core_rods` NEW 2 frames 128 x 128 on the core; `ch_ms_boom_barrier` NEW 2 frames 128 x 64. People: `reactor_s01` directed (badge prop). Faces: `hopeful`, `sulk`. Acts: `hold_up`, `turn_away`. Map: waypoint `reactor_choice`; hotspot `core` anchor thing `core_r` + extra thing lever.

### 3.4 `mothership.bridge` The Bridge - P2, M

**Story.** The command bridge: consoles, a viewscreen of space at the far end, the captain at the helm. A holographic star globe (secret, after you have the engineer's badge). The way on is the door you came in by.

| Option | Anchored on today | Leads to / success / failure | Seen today (home (42.6, 3.0) yaw -90) |
| --- | --- | --- | --- |
| `mothership.bridge.exit_exit` **DEFAULT** | waypoint `bridge_door` (41.8, 7.5) | `mothership.exit`; stagger -5 | +100: **behind** |
| `mothership.bridge.helm` | thing `captain_h` (54.5, 1.4), a billboard | success `ms_warp` +10 variation (climb to the helm); failure `ms_crash` -10 dip (stagger to the door) | -8, 12 m |
| `mothership.bridge.star_chart` (secret, once; needs `ms_badge`) | thing `globe_b` (50.4, 3.0) | success `ms_star_chart` +6; failure `ms_lockout` -4 | 0, 7.8 m |

**Window vantage** `bridge_choice` NEW (41.5, -1.5) yaw -140 (the north-west corner, looking south-east). Helm -37 (13.3 m), globe -23 (10 m), door +38 (9 m). (A search of the whole sector found no vantage with all three inside +-35.)

**Concept: the chair swivel.** The captain (a baked person) sits in a high-backed chair at the helm. Idle: the chair faces the viewscreen (his back to you), a hand waves over the shoulder. When the helm is current the chair **swivels to face you**, he `offer`s the empty seat, and the viewscreen streaks into warp (the existing piece `bridge_warp_streaks`); when not, the chair faces the screen and the stars are still. The globe flares when current. The door has an ensign who ushers.

| Option | Embodied by | Idle | CURRENT | NOT CURRENT / QUEUED | Touched | Commit S / F |
| --- | --- | --- | --- | --- | --- | --- |
| `exit_exit` | `ch_ms_iris_door` (wreath) at (41.8, 7.5) + ensign `bridge_s02` re-homed to (42.6, 7.2) | default from beat 0: iris open, ensign `usher`, `happy` | as idle | NOT n/a; QUEUED: ensign `nod`, `neutral`, iris stays open | pose swap | S: ensign `salute`; F: iris stutters |
| `helm` | NEW actor `bridge_cap` seated at (54.5, 1.4) + `ch_ms_helm_chair` (2 frames) + `bridge_warp_streaks` | back to us, hand `wave` over shoulder; screen static | chair faces the camera, `offer` the seat, `hopeful`; warp streaks ON | chair faces the screen, `turn_away`, `sulk`; streaks OFF | chair frame and piece swap on the same beat | S: warp surge; F: streaks strobe white, chair spins, crash |
| `star_chart` | piece `bridge_holo_globe` (2 frames) | dim, slow | flares, constellations light, rotates faster | dim | frame swap | S: map blooms; F: globe blanks (lockout) |

**Create.** NEW actor `bridge_cap` (a cyclops or grey captain in uniform with a hat); `ch_ms_helm_chair` NEW 2 frames 128 x 128; `bridge_holo_globe` 2 new frames; iris wreath instance; `bridge_s02` re-homed and directed. Faces: `hopeful`, `sulk`. Acts: `offer` (exists), `turn_away`, `usher`. Map: waypoint `bridge_choice`; remove billboard `captain_h` (or keep as the chair back).

### 3.5 `mothership.exit` The Airlock - P1, L

**Story.** The medbay and airlock: the airlock hatch ahead (to the Hospital), an examination bay through a door on the east (to the Ward). A medic examines you: pass and you go on to the Hospital; fail and you are strapped to the table and wheeled to the Ward. A hand wheel cycles the lock.

| Option | Anchored on today | Leads to / success / failure | Seen today (home (34, 10.9) yaw 180) |
| --- | --- | --- | --- |
| `mothership.exit.exit_hospital` **DEFAULT** | waypoint `airlock_door` (34, 14.6) | `hospital`; stagger -5 | 0, 3.7 m: in view, a slit |
| `mothership.exit.exit_ward` | waypoint `exam_door` (36.5, 12.0) | `ward`; stagger -5 | -66: out |
| `mothership.exit.exam` | actor `med02` (43.9, 11.9) at the exam table | success `ms_exam_ok` +6 (stay on the default, hospital); failure route **ward**, `ms_probed`, strapped -8 | -84, 10 m: out |
| `mothership.exit.airlock_wheel` | thing `wheel_a` (32.25, 17.0) in the airlock | success route hospital, `ms_airlock_cycled` +5; failure hospital, `ms_airlock_alarm`, -6 (back to the med door) | +16, 6.3 m: tiny |

**Window vantage** `airlock_choice` NEW (34.5, 9.6) yaw 180 (the north end of the medbay, facing the airlock). Hatch +6 (5.0 m), wheel +17 (7.7 m), exam door -40 (3.1 m), medic (re-homed into the doorway at (36.9, 12.6)) -39 (3.8 m), probe arm (re-sited to (36.3, 12.0)) -37 (3.0 m).

**Concept: hatch against probe.** Left: the exam door (a white iris) with the medic standing in it holding a clipboard and a **probe arm** folded against the ceiling. Right/ahead: the airlock hatch with a wheel. When Ward is current the probe arm **descends toward you with a light cone** and the white iris opens; when Hospital is current the hatch iris opens on a chamber with two hanging spacesuits and the probe arm stays folded. The medic is the gamble (UNDECIDED: both iris half open, medic `stare` with `doubt`, probe arm hovering halfway). The wheel (a stop) spins by itself and the hatch cycles with a blink.

| Option | Embodied by | Idle | CURRENT | NOT CURRENT / QUEUED | Touched | Commit S / F |
| --- | --- | --- | --- | --- | --- | --- |
| `exit_hospital` | `ch_ms_airlock_hatch` (3 frames) at (34, 14.6), existing suits `suit_a0`, `suit_a1` | default from beat 0: hatch open, chamber lit, suits hanging, wheel still | hatch open, shaft pulses | hatch sealed and ringed with a slow amber blink | frame swap | S: hatch dilates, suits sway; F: hatch jams half, stagger |
| `exit_ward` | white iris at (36.5, 12.0) + `ch_ms_probe_arm` (3 frames) | iris sealed, probe folded up | iris open, probe arm extended toward the camera with a light cone (`probe_light`) | sealed, probe folded | probe and iris swap on the beat | S: probe lowers and retracts; F: probe snaps, stagger |
| `exam` (gamble) | `med02` in the doorway, clipboard (`hold_up`) | `write`; at 48 `beckon` with the clipboard | UNDECIDED: iris half, hatch half, medic `stare` `doubt`, probe hovering midway | `write` | both doors move to half | S: `nod` `relief`, probe retracts, hatch opens; F: `block` `anger`, `point` at the exam door, iris opens, strapped |
| `airlock_wheel` (stop) | `ch_ms_wheel` (piece: still frame and a rotating frame) | still | spins on its own, hatch iris cycles with an amber blink per beat, steam puff | still | piece swap | S: iris completes; F: alarm blink, stagger back to the med door |

**Create.** Objects: `ch_ms_airlock_hatch` NEW 3 frames (sealed, half, open with chamber) 128 x 128 (2 m); `ch_ms_probe_arm` 3 frames (folded, half, extended with cone) 128 x 128 (re-site `thing_probe_arm`); iris white skin (3); `ch_ms_wheel` NEW piece 2 frames 64 x 64. People: `med02` re-homed and directed (clipboard exists); the exam table is no longer the stage for this beat. Faces: `sulk`, `hopeful`. Acts: `hold_up`, `usher`, `turn_away`. Map: waypoint `airlock_choice`; `med02` home; `probe_arm` re-site; hotspot `exit_ward` anchors the iris + probe.

## 4. The Underworld (`underworld`, a demon arena, court, furnace, lava pit and throne)

Language: braziers, chains, bone arches, portcullises, banners, lava, a skull throne. Demons (imps, brutes, skeletons, queens) read by horns, wings and posture; species face rules apply to each new face (a skeleton's `sulk` is its jaw clenched sideways and sockets narrowed; a brute's shows lower teeth). Note the Underworld is still on temporary music (CONTINUOUS_RUN.md), which does not affect this work.

Shared pieces: **`ch_uw_portcullis`** (3 frames: down, half, up; 2 instances in the Arena), **`ch_uw_iron_door`** (3 frames: shut, ajar, open with torchlight; used by the Furnace and the Pit), the held props `banner_anvil`, `banner_skull`, `lantern_hand`, `fan`, `hammer`.

### 4.1 `underworld` The Arena (entry) - P1, L

**Story.** A sunken gladiator arena, the tiers packed with demons. Two tunnel gates: right to the court (the queen), left to the furnace (the smith). A bouncer guards the hellmouth gate at the far end (he remembers you if you were thrown out of the Warehouse door); a chain hangs from the ceiling.

| Option | Anchored on today | Leads to / success / failure | Seen today (home (0, 6.5) yaw 0) |
| --- | --- | --- | --- |
| `underworld.exit_court` **DEFAULT** | waypoint `arena_tier_r` (6.4, 3.0) | `underworld.court`; stagger -5 | +61: out |
| `underworld.exit_furnace` | waypoint `arena_tier_l` (-6.4, 4.0) | `underworld.furnace`; stagger -5 | -69: out |
| `underworld.bouncer` (`flags_none wh_thrown_out`) | actor `gate_bouncer` (-6.3, 2.7) | success `uw_gate_pass` +5 (walk to the gate); failure `uw_tossed` -7 (stagger to the edge); then the default court | -59: out |
| `underworld.bouncer_grudge` (`flags_all wh_thrown_out`) | actor `gate_bouncer` | success +4; failure route **furnace**, -8 | -59 |
| `underworld.chains` | thing `chains_a` (9.0, 4.0) | success `uw_swung` +8 variation (swing to the gate); failure `uw_caged` -9 (dragged to the cage) | +74: out |

**Window vantage** `arena_choice` NEW (0, 8.6) yaw 0 (the south edge of the arena floor, looking at the hellmouth). Heralds at -40 / +40 (6.2 m), tunnel gates at -54 / +49 (edge, behind their heralds), bouncer re-homed to (-2.2, -0.5) -14 (9.4 m), chain re-sited to (2.8, 0.8) +20 (8.3 m).

**Concept: the arena's thumbs.** Gladiator arenas decide with thumbs. Two **heralds** (demons in tabards) stand on the floor, each carrying a **banner** with a pictogram (a skull for the court, an anvil for the furnace) and a free hand for the verdict. The current herald holds the banner high, blows a horn and gives a **thumbs up**; the other lowers the banner, grimaces and gives a **thumbs down**. Behind each herald the **portcullis** of that gate is raised (current) or half down and clanking (not). The tier crowds, when near the frame edge, flip cheering (arms up) or booing. Touch the booing herald: thumbs flip, banners swap, portcullises swap.

| Option | Embodied by | Idle / invitation | CURRENT | NOT CURRENT / QUEUED | Touched | Commit S / F |
| --- | --- | --- | --- | --- | --- | --- |
| `exit_court` | herald R (re-dressed arena demon at (4.0, 3.8)) + `ch_uw_portcullis` at (6.4, 3.0) | default from beat 0: banner (skull) high, `thumbs_up`, `happy` grin, portcullis up with red light | as idle, horn blast `cheer` every bar | banner lowered (`hold_low`), `thumbs_down`, `sulk`, portcullis half down, rattling | herald flips, portcullis frame swap | S: herald `usher` toward the gate, portcullis rises fully; F: herald `shrug` and winces, portcullis drops a notch; stagger |
| `exit_furnace` | herald L at (-4.0, 3.8) + portcullis at (-6.4, 4.0) | banner (anvil) low, `thumbs_down`, `sulk`; at 48 it `beckon`s with the banner hand | banner up, `thumbs_up`, orange light behind the gate | as idle | mirror | as above |
| `bouncer` (stop) | `gate_bouncer` at the hellmouth; piece `hellmouth_portal` (rotating) | arms folded (`block`), `anger`; at 48 `stamp` once | `stare` with `doubt`, arms down, the portal spins faster; both heralds go QUEUED | arms folded, portal slow | pose swap, portal speed | S: `bow` with a `laugh` (existing) , portal flares; F: `stamp` and `point` back at the edge |
| `bouncer_grudge` | same actor, remembers you | `stamp` `anger` | `block`, `stare` `anger` | as idle | | S: `bow` `laugh`; F: `point` toward the furnace (the herald L flips to `thumbs_up` as the verdict) |
| `chains` (stop) | piece `chains_swing` + new hook ring | hangs still | swings wide arcs, ring lit | still | piece frame swap | S: you swing (existing climb); F: chain recoils and snaps down, the cage cinematic |

**Default clarity.** The skull-banner herald is grinning with the banner up and a thumb up; the anvil herald is scowling with a thumb down. At 48 the scowler starts to beckon.

**Create.**
* People: wardrobe `herald` (tabard, horn) for two existing arena demons, re-homed to (-4.0, 3.8) and (4.0, 3.8) and pinned; `gate_bouncer` re-homed to (-2.2, -0.5).
* Props: `banner_skull`, `banner_anvil` (0.8 m cloth banners with 12 px pictograms; held up and lowered), horn.
* Objects: `ch_uw_portcullis` NEW 3 frames 128 x 128 x2 instances; `thing_crowd` 2 new frames (arms up, thumbs down) 128 x 128, 8 instances flip per tier; `chains_swing` piece 2 frames (still, swinging with a lit ring) 64 x 128, re-sited to (2.8, 0.8).
* Faces: `sulk`, `smug`. Acts: `thumbs_up`, `thumbs_down`, `hold_up`, `hold_low`, `usher`, `shrug`, `lean_wall`.
* Animations: tier-wide crowd flip (X7); portal spin speed; horn blast.
* Map: waypoint `arena_choice`; three homes; chain site; hotspot anchors: `exit_court` thing portcullis R + actor herald R; `exit_furnace` thing portcullis L + herald L.

### 4.2 `underworld.court` The Court - P2, M

**Story.** A long hall of columns and skull plaques leading to a throne. The queen of the court stands near you; a glowing seal is on the floor; a causeway leads off south to the pit. Stops: dance with the queen, stand on the seal. Way on: the causeway.

| Option | Anchored on today | Leads to / success / failure | Seen today (home (12.6, 4.0) yaw -90) |
| --- | --- | --- | --- |
| `underworld.court.exit_pit` **DEFAULT** | waypoint `court_causeway` (19, 7.4) | `underworld.pit`; stagger -5 | +28, 7.2 m (ring) |
| `underworld.court.seal` | thing `seal_c` (21, 4.0) | success `uw_seal` +6 variation (stand on the seal); failure burn -8 dip (stagger back) | 0, 8.4 m, a sigil at the horizon: flat, almost invisible |
| `underworld.court.queen` | actor `court_g06` (14.9, 4.0) | success `uw_queen_favour` +8 (dance, walk to court mid); failure `uw_hexed` -6 dip | 0, 2.3 m (a stare/nod; "success and committed look alike" per A9) |

**Window vantage** `court_choice` NEW (11.6, 4.0) yaw -90 (the court door). Queen 0 (3.3 m), seal re-sited to (16.5, 2.6) -16 (5.1 m), causeway +25 (8.1 m).

**Concept: the queen's hand.** The queen is a regal figure with a **fan**. Current: she extends her hand palm down (`offer`) with the fan open, smiling `smug`/`hopeful`; two courtiers beside her `clap`. Not current: fan snapped shut, `turn_away` with a sulk, courtiers `stare`. The seal: runes flare tall and bright when current, a smouldering low ring when not. The causeway has a **lantern imp** at its head: lantern raised and an `usher` arm when the way is current, lantern lowered when a stop is current.

| Option | Embodied by | Idle | CURRENT | NOT CURRENT / QUEUED | Touched | Commit S / F |
| --- | --- | --- | --- | --- | --- | --- |
| `exit_pit` | NEW actor `ci01` (lantern imp) at the causeway head (19.0, 7.0) | default from beat 0: lantern high (`hold_up`), `usher`, `happy` | as idle | QUEUED: lantern mid, `nod` | pose swap | S: imp bows and leads off; F: lantern gutters, stagger |
| `seal` (stop) | `court_seal` piece (new frames) at (16.5, 2.6) + piece `court_flames` | low smouldering ring | tall rune ring, flames up, a hum of motes | low ring | frame swap | S: ring holds, you step in; F: ring bursts (burn) |
| `queen` (stop) | `court_g06` with a fan; courtiers `court_c03`, `court_c04` | `stare` `resolve`, fan closed; at 48 `beckon` | `offer`, fan open, `smug`; courtiers `clap` | `turn_away`, fan shut, `sulk`; courtiers `stare` | pose swap | S: `nod`, dance (existing); F: she points at the pit and the court `laugh` (existing failure act) |

**Create.** Objects: `court_seal` piece 2 new frames (smoulder, flare) 128 x 128. People: NEW actor `ci01` (imp with a lantern; wardrobe from the Underworld imps); queen directed with a fan prop. Props: fan (open and closed), lantern_hand. Faces: `smug`, `hopeful`, `sulk`. Acts: `usher`, `turn_away`, `hold_up`. Map: waypoint `court_choice`; seal site; home `ci01`.

### 4.3 `underworld.furnace` The Furnace - P3, M

**Story.** The smith's furnace: anvils, tongs, molten channels, a glowing door at the far end. The way on is back the way you came (east). Stops: work the anvil, tip the ladle.

| Option | Anchored on today | Leads to / success / failure | Seen today (home (-11.8, 4.0) yaw 90) |
| --- | --- | --- | --- |
| `underworld.furnace.exit_pit` **DEFAULT** | waypoint `furnace_out` (-11.6, 6.0) | `underworld.pit`; stagger -5 | -96: **behind**, 2 m |
| `underworld.furnace.anvil` | thing `anvil_f0` (-15, 0.8) | success `uw_forged` +6 variation (forge); failure burn -8 (stagger to the door) | +45, 4.5 m |
| `underworld.furnace.ladle` | thing `ladle_f` (-14, 7.2), piece `furnace_ladle` | success `uw_molten` +5; failure spill -7 | -55: edge |

**Window vantage** `furnace_choice` NEW (-19.0, 4.0) yaw -90 (the far, west end, looking back east toward the entrance). Anvil -39 (5.1 m), smith -40 (3.3 m), ladle +33 (5.9 m), exit door +15 (7.7 m).

**Concept: the smith's hammer.** The smith (`smith_carry`) raises his hammer over the anvil when it is current and the anvil's face glows orange with a spark on every beat; lowered hammer and a cold dark anvil when not. The ladle tilts and pours a molten stream into the channel when current, hangs upright and dripping when not. The exit is an iron door at the east wall with a demon beside it.

| Option | Embodied by | Idle | CURRENT | NOT CURRENT / QUEUED | Touched | Commit S / F |
| --- | --- | --- | --- | --- | --- | --- |
| `exit_pit` | `ch_uw_iron_door` at (-11.6, 6.0) + `furnace_c10` re-homed to (-12.4, 5.6) | default from beat 0: door ajar with torchlight, `furnace_c10` `usher`, `cheer` | as idle | QUEUED: `nod` | pose swap | S: door swings wide; F: door bangs, stagger |
| `anvil` | `ch_uw_anvil_hot` (2 frames) + `smith_carry` with a hammer | smith `stamp`s at the anvil, anvil cold | hammer overhead (`hold_up`), `happy`, anvil face orange, sparks | hammer lowered, `sulk`, anvil dark | frame swap | S: strike and a shower of sparks; F: spark burns the camera hand, stagger |
| `ladle` | piece `furnace_ladle` (2 frames) + piece `furnace_channels` | upright, dripping | tilted, stream pouring, channel glows, shimmer | upright | frame swap | S: ladle holds; F: spills (existing) |

**Create.** Objects: `ch_uw_anvil_hot` NEW 2 frames 64 x 64; `furnace_ladle` 2 new frames (upright, pouring) 96 x 128; `ch_uw_iron_door` NEW 3 frames 128 x 128. People: `smith_carry` directed (hammer prop), `furnace_c10` re-homed. Faces: `sulk`. Acts: `hold_up`, `usher`. Map: waypoint `furnace_choice`.

### 4.4 `underworld.pit` The Pit - P2, M

**Story.** A platform in a lava lake: the stage on the far shore, a fortress glowing beyond. The only physical way on is the door you came in by; stops: dare the lava bridge to the far shore, light a brazier.

| Option | Anchored on today | Leads to / success / failure | Seen today (home (19, 11.2) yaw 180) |
| --- | --- | --- | --- |
| `underworld.pit.exit_exit` **DEFAULT** | waypoint `pit_door` (18.25, 10.6) | `underworld.exit`; stagger -5 | +129: **behind**, 1 m |
| `underworld.pit.lava_bridge` | thing `lavaflow_p` (19, 28) | success `uw_bridge` +8 variation (walk to the edge); failure `uw_scorched` -12 dip (stagger to the east rim) | 0, 16.8 m, a flat glow at the horizon |
| `underworld.pit.brazier` | thing `uw_br_p0` (13.5, 10.5) | success `uw_lit` +4; failure -5 | +97: out |

**Window vantage** `pit_choice` NEW (24.2, 11.2) yaw 125 (the north-east corner of the deck, looking south-west across the pit). Door +41 (6.0 m), bridge head -36 (15.7 m), brazier (anchor moved to `uw_br_p2` at (13.5, 21.6), enlarged) -9 (14.9 m), guard `pit_c06` re-homed to (17.2, 11.8) +30 (7.0 m).

**Concept: the slabs.** The lava bridge is a line of **basalt slabs** that rise out of the lava toward the far shore when current (cracks glowing) and sink when not (lava surface bubbling). A lantern imp on the far shore waves its lantern when current and shields its eyes when not. The brazier: cold dark coals vs a roaring tall flame. The door: iron, with the brute `pit_c06` beside it (he `block`s at beat 0 by cast; here he steps aside and `usher`s when it is the way).

| Option | Embodied by | Idle | CURRENT | NOT CURRENT / QUEUED | Touched | Commit S / F |
| --- | --- | --- | --- | --- | --- | --- |
| `exit_exit` | `ch_uw_iron_door` at (18.25, 10.6) + `pit_c06` | default from beat 0: door ajar, torchlight; `pit_c06` `usher`, `happy` | as idle | QUEUED: `nod`, `neutral` | pose swap | S: door wide; F: door slams, stagger |
| `lava_bridge` | `ch_uw_slabs` (2 frames) at x 17-21, z 22-27 + far-shore NEW actor `pit_lamp` with a lantern | slabs sunk; imp waves (`beckon`) at 48 | slabs risen, cracks lit, lava glow brighter; imp lantern high, `happy` | sunk, bubbling; imp shields its eyes, `sulk` | frame swap | S: slabs hold, imp `cheer`; F: slabs crumble in the lava (scorched) |
| `brazier` | `thing_brazier` (2 frames, enlarged) at (13.5, 21.6) | cold coals | tall flame, sparks | cold | frame swap | S: flame roars; F: flame snuffs |

**Create.** Objects: `ch_uw_slabs` NEW 2 frames (sunk, risen) 256 x 128; `thing_brazier` 2 frames (cold, roaring) enlarged to 128 x 128; iron door (4.3). People: NEW actor `pit_lamp` (lantern imp, the same wardrobe as `ci01`), `pit_c06` re-homed and directed. Faces: `sulk`, `hopeful`. Acts: `usher`, `hold_up`. Map: waypoint `pit_choice`; hotspot `brazier` anchor to `uw_br_p2`.

### 4.5 `underworld.exit` The Throne - P1, L

**Story.** The skull throne at the head of a stair, two doors on the far wall, left and right of it. Left leads out to the Hospital, right to the Ward: two small, humble doors in the middle of hell. The throne is a gamble: take it and the way is the Hospital; fail and it eats you and you are dragged to the Ward.

| Option | Anchored on today | Leads to / success / failure | Seen today (home (25.4, 4.0) yaw -90) |
| --- | --- | --- | --- |
| `underworld.exit.exit_hospital` **DEFAULT** | waypoint `throne_door_l` (30.2, 1.0) | `hospital`; stagger -5 | -32: in view, a ring |
| `underworld.exit.exit_ward` | waypoint `throne_door_r` (30.2, 7.0) | `ward`; stagger -5 | +32: in view |
| `underworld.exit.throne` | thing `uw_throne` (30.75, 4.0) | success `uw_throned` +10 variation (take the throne; then the default route, Hospital); failure route **ward**, `uw_devoured` -10 | 0, 5.4 m |

**Window vantage** `throne_choice` NEW (24.5, 4.0) yaw -90 (one step back down the stair). Doors -28 / +28 (6.4 m), throne 0 (6.2 m).

**Concept: two humble doors and a hungry throne.** The left door is a **clinic door** (white, round windows, a wire handrail); the right a **padded green ward door** with a wire-glass window. Each has a cameo person peeking: a **nurse** (white) at the left, an **orderly** (green uniform) at the right, foreshadowing the worlds beyond. Current: the door is wide open, the cameo beckons with `hopeful`; not current: ajar or latched, the cameo peers sadly (nurse) or leans away (orderly). The throne is the gamble: UNDECIDED = both doors half, the **skull's jaw opens wide** (a maw with a floating crown), courtiers on the steps `kneel`; success: the jaw eases shut and the crown floats toward you; failure: the jaw snaps and the orderly hauls the right door open.

| Option | Embodied by | Idle | CURRENT | NOT CURRENT | Touched | Commit S / F |
| --- | --- | --- | --- | --- | --- | --- |
| `exit_hospital` | `ch_uw_door_clinic` (3 frames) at (30.2, 1.0) + NEW actor `ths_nurse` | default from beat 0: door open a hand's width with pale light, nurse peeking, `hopeful` | door wide, nurse `beckon` `happy` | door latched, nurse `sulk` peering through the glass | frame and pose swap | S: nurse `cheer`; F: door slams, stagger |
| `exit_ward` | `ch_uw_door_ward` (3 frames) at (30.2, 7.0) + NEW actor `ths_orderly` | latched, orderly arms folded (`lean_wall`) | door wide, orderly `usher`, `neutral` | latched, orderly `turn_away` | as above | as above |
| `throne` (gamble) | piece `skull_throne` (new jaw frames) + `uw_throne`; courtiers `stair_chat_a`, `stair_chat_b`, `stair_sit` | jaw shut, crown on top, courtiers `bow` (existing cast) | UNDECIDED: both doors half, jaw wide open, courtiers `kneel` | jaw shut, courtiers `stare` | frame swap | S: jaw eases shut, crown lifts, you climb (existing); F: jaw snaps, orderly hauls the ward door open, devoured |

**Default clarity.** The clinic door is ajar with pale light and a hopeful nurse from beat 0; the ward door is latched and its orderly leans away; the throne's jaw is shut. Tapping either door's person or the door flips the pair.

**Create.** Objects: `ch_uw_door_clinic` NEW 3 frames and `ch_uw_door_ward` NEW 3 frames (128 x 128, 1.2 m x 2.2 m); `skull_throne` piece 2 new frames (jaw shut with crown, jaw open) 128 x 160. People: NEW actors `ths_nurse` and `ths_orderly` (underworld sheets with the Hospital's nurse and the Ward's staff wardrobes; they stand in the doorways); courtiers directed. Faces: `hopeful`, `sulk`. Acts: `usher`, `lean_wall`, `turn_away`, `kneel` (exists). Map: waypoint `throne_choice`; doors as things at the two waypoints; homes `ths_nurse` (30.0, 1.4), `ths_orderly` (30.0, 6.6).

## 5. New assets and expressions (roll-up)

Counts first: **40 object families (26 new, 14 existing ones that gain frames), 104 frames; 9 new people plus 5 re-dressed existing ones (6 new wardrobe looks); 2 animated non-person figures (20 frames); 5 new faces; 12 new acts; 13 held props; 10 animation behaviours.**

### 5.1 Objects and set pieces (map things and pieces; each frame is a piece toggled with the others on the same beat)

| Family | Frames (states) | Size (authoring px; metres) | Scene(s) | Status |
| --- | --- | --- | --- | --- |
| `ch_wh_shutter` | 3: down, half, up | 128 x 128; 2.4 m | Floor | NEW |
| `ch_wh_scissor_gate` | 3: closed, half, open | 128 x 128; 2.1 m | Floor | NEW |
| `ch_wh_bead_curtain` | 3: hang, sway, tied back | 128 x 128; 2.0 m | Bar | NEW |
| `ch_wh_door_leaf` | 3: shut, ajar, wide | 128 x 128; 2.1 m | Bar, Balcony, Chill-out | NEW |
| `ch_wh_pint` | 1 sprite plus a 3-stop path | 32 x 32 | Bar | NEW |
| `ch_wh_matchbook` | 2: on table, slid across | 16 x 16 | Bar | NEW |
| `ch_wh_lantern` | 3: unlit, low flame, tall flame | 48 x 64; 0.5 m | Bar | NEW |
| `ch_wh_velvet_rope` | 2: hooked across, unhooked lying | 64 x 64; 1.2 m | Balcony, Door | NEW |
| `ch_wh_skylight_star` | 3: dim, bright, bright plus shaft (uses `beam` PNG) | 128 x 128 | Balcony | NEW |
| `ch_wh_trapdoor` | 3: shut, ajar, open with light | 128 x 128; 1.5 m | Chill-out | NEW |
| `ch_wh_tunnel_gate` | 3: shut with seam, ajar, open with shaft | 128 x 128; 2.4 m | Door | NEW |
| `thing_lavalamp` | +2: settled, rising | 64 x 64 | Chill-out | existing, new frames |
| `thing_decks` | +3: idle, stylus down A, B | 128 x 128 | Booth | existing |
| `thing_headphones` | +2: flat, lifted and swinging (gold lanyard) | 64 x 64 | Booth | existing |
| `thing_booth_radio` | +3: off, crackle, tuned plus aerial | 128 x 128 | Booth | existing |
| `thing_crack` | +3: hairline, half, wide with heat | 128 x 128 | Door | existing |
| `ch_ms_iris_door` | 9: 3 states (sealed, half, open) x 3 skins (wreath, hazard, medical white) | 128 x 128; 1.2 x 2.2 m | Deck x2, Gallery, Bridge, Airlock | NEW |
| `ch_ms_beacon` | 2: slow, fast (amber) | 32 x 32 | Deck (reactor door) | NEW |
| `ch_ms_window_blind` | 3: shut, half, open | 256 x 128 | Gallery | NEW |
| `ch_ms_boom_barrier` | 2: down, up | 128 x 64 | Reactor | NEW |
| `ch_ms_lever` | 2: up, down | 64 x 64 | Reactor | NEW |
| `ch_ms_core_rods` | 2: in, out | 128 x 128 | Reactor | NEW |
| `ch_ms_helm_chair` | 2: facing screen, swivelled | 128 x 128 | Bridge | NEW |
| `ch_ms_airlock_hatch` | 3: sealed, half, open with chamber | 128 x 128; 2 m | Airlock | NEW |
| `ch_ms_wheel` | 2: still, spinning (rotate anim) | 64 x 64 | Airlock | NEW |
| `gallery_holo_menu` | +2: collapsed, unfolded | 128 x 128 | Gallery | existing piece |
| `bridge_holo_globe` | +2: dim, flared | 64 x 64 | Bridge | existing piece |
| `thing_probe_arm` (`ch_ms_probe_arm`) | +3: folded, half, extended with cone | 128 x 128 | Airlock | existing |
| `ch_uw_portcullis` | 3: down, half, up (2 instances) | 128 x 128 | Arena | NEW |
| `ch_uw_iron_door` | 3: shut, ajar, open with torchlight | 128 x 128 | Furnace, Pit | NEW |
| `ch_uw_slabs` | 2: sunk, risen | 256 x 128 | Pit | NEW |
| `ch_uw_door_clinic` | 3: latched, ajar, open | 128 x 128 | Throne | NEW |
| `ch_uw_door_ward` | 3: latched, ajar, open | 128 x 128 | Throne | NEW |
| `ch_uw_anvil_hot` | 2: cold, glowing | 64 x 64 | Furnace | NEW |
| `thing_crowd` | +2: arms up, thumbs down (8 instances) | 128 x 128 | Arena | existing |
| `chains_swing` | +2: still, swinging with lit ring | 64 x 128 | Arena | existing piece |
| `court_seal` | +2: smoulder, flare | 128 x 128 | Court | existing piece |
| `furnace_ladle` | +2: upright, pouring | 96 x 128 | Furnace | existing piece |
| `thing_brazier` | +2: cold, roaring (enlarged for the Pit) | 128 x 128 | Pit | existing |
| `skull_throne` | +2: jaw shut with crown, jaw open | 128 x 160 | Throne | existing piece |

### 5.2 People (baked pixel sheets) and figures

| Who | Kind | Scene(s) | Notes |
| --- | --- | --- | --- |
| `wz_floor`, `wz_chill` | NEW actors, wardrobe `wizard` (robe, pointed hat, long beard; staff prop) | Floor, Chill-out | replace the two `thing_wizard` billboards; give both hotspots an `acting` block |
| `rd01` | NEW actor, wardrobe `roadie` (black tee, cap, headphones round neck, tape roll) | Bar | doorway to the floor |
| `cb01` | NEW actor, a raver with a coat over one arm | Chill-out | the doorway friend |
| `bridge_cap` | NEW actor, wardrobe `captain` (uniform, hat; cyclops or grey) | Bridge | seated at the helm |
| `ci01`, `pit_lamp` | NEW actors, the Underworld imp wardrobe with a lantern | Court, Pit | lantern imps |
| `ths_nurse`, `ths_orderly` | NEW actors in the Underworld sheets, the Hospital nurse's and the Ward orderly's wardrobes | Throne | doorway cameos |
| `c02`, `c03` | re-dressed existing, wardrobe `steward` (hi-vis, baton, headset) | Floor | pin homes |
| two arena demons | re-dressed existing, wardrobe `herald` (tabard, horn) | Arena | pin homes at (+-4.0, 3.8) |
| `b03` | re-dressed existing, wardrobe `hood` | Bar | the stranger |
| `ch_wh_dog` | NEW non-person figure, about 32 x 40 px: sit 1, tail-wag 2, trot 4, look-back 1, bark 2 = 10 frames, mirrored | Balcony | acted through the `figure` contract (E8) |
| `ch_ms_drone` | NEW non-person figure, about 32 x 32 px: bob 4, glide 2, perk 1, droop 1 = 8 frames; waiter variant adds a tray (2 frames) = 10 | Deck, Gallery | `figure` contract |

Existing people re-homed or pinned (no new sheet except for the new acts and faces): `g07` (Floor), `b04`, `v02`, `v03`, `d01`, `c10`, `g03`, `e01`, `s02`, `s03`, `bridge_s02`, `med02`, `furnace_c10`, `pit_c06`, `gate_bouncer`, `court_g06`, `smith_carry`, `reactor_s01`, `g08`, `m01`, `b01`.

### 5.3 Faces (five new; each must read at the 17 x 13 full head and at half size; at the quarter size they fall back)

| Face | Brows / eyes / mouth at the pixel rig | Quarter-size fallback | Species rule |
| --- | --- | --- | --- |
| `hopeful` | brows up with the inner ends raised, eyes bright and looking up and toward you, a small closed smile | `happy` | grey: eyes widen with one catch-light; insect: mandibles part slightly |
| `sulk` | brows low, outer ends down, eyes cast down and aside, mouth flat and pushed out, lower lip a dark pixel | `sad` | skeleton: jaw clenched sideways; brute: lower teeth show; cyclops: lowered lid |
| `smug` | one brow up, half-lidded eyes, a lopsided smirk with one cheek pixel | `neutral` | imp: fanged smirk; grey: one eye slit |
| `wink` | one eye a flat line, the other open, a broad grin | `happy` | grey and cyclops: a slow lid drop instead |
| `yawn` | eyes shut, brows relaxed, mouth a tall open oval with a tongue pixel | `neutral` | skeleton: the jaw drops |

### 5.4 Acts (twelve new; state, pose, beats and frames, default face, facings; baked only for the directed people who use them)

| Act | Pose at the pixel rig | Beats / frames | Default face | Facings |
| --- | --- | --- | --- | --- |
| `shrug` | both hands out palms up, shoulders up 2 px, head tilted, hold | 2 / 6 | `doubt` | front, side |
| `tug` | the near arm reaches toward the camera and pulls back twice (forearm foreshortened on the front view), weight forward | 2 / 8 | `hopeful` | front, three-quarter |
| `turn_away` | body turned to the back or three-quarter view, head glancing over the shoulder, hold | 4 / 6 | `sulk` | back, three-quarter |
| `usher` | one arm sweeps from the hip across the body and holds palm up toward `look_at`, the other behind | 4 / 6 | `happy` | front, side |
| `thumbs_up` | arm bent, fist with the thumb up (2 px), a small nod | 2 / 4 | `happy` | front, side |
| `thumbs_down` | the same with the thumb down, head back | 2 / 4 | `anger` | front, side |
| `hold_up` | one arm overhead holding a prop (prop frame "up": paddle, banner, lantern, badge, hammer, rope end), chin up | 4 / 4 | `happy` | front, side |
| `hold_low` | the prop at the hip, shoulders dropped, head lowered | 4 / 4 | `sulk` | front, side |
| `pat_seat` | seated, the near hand pats the cushion beside twice, leaning toward the viewer | 2 / 6 | `happy` | side, three-quarter |
| `slide` | torso leans, the flat hand pushes a glass along the counter (the glass itself is the piece `ch_wh_pint`, X2) | 2 / 6 | `happy` | front, three-quarter |
| `withhold` | glass hugged to the chest, a finger wags, head shakes | 2 / 4 | `smug` | front |
| `lean_wall` | shoulder against a wall or post, arms folded, one foot crossed and tapping on the kick | 8 / 4 | `sulk` | side |

### 5.5 Held props (pixel-rig hand props; replace the placeholders of `StoryCharacter._draw_held`)

`paddle_pint`, `paddle_stairs` (0.5 m discs with 12 px pictograms), `staff` (2 frames: lit, unlit), `rope_end`, `coat` (over the arm), `banner_skull`, `banner_anvil` (0.8 m cloth, 12 px pictograms), `horn`, `lantern_hand`, `fan` (open, closed), `hammer`, `badge`, `gold_clipboard` (the existing clipboard with a gold sticker). Existing and reused: pint, headphones, clipboard, orb wand.

### 5.6 Animation behaviours (no new art unless stated)

| # | What | Scene(s) |
| --- | --- | --- |
| X1 | LED floor chevron chase toward a target gate (the tile chase of `floor_led`, a new pattern) | Floor |
| X2 | a piece sliding along a 3-stop path in about 1 beat (the pint) | Bar |
| X3 | a figure trotting between two waypoints in 2 beats (the dog) | Balcony |
| X4 | a figure gliding between two doors in 1.5 beats (the drone) | Deck, Gallery |
| X5 | change of a piece's speed (lava lamp blobs, reactor ring, beacon, hellmouth) | Chill-out, Reactor, Deck, Arena |
| X6 | `light` ops: switching a map light on or off or pulsing it (door spills) | Floor, Bar, Door |
| X7 | tier-wide crowd flip between cheer and boo frames (8 billboards) | Arena |
| X8 | platter and VU sync to the beat | Booth |
| X9 | slab rise and sink with lava bubbling | Pit |
| X10 | quantised door, iris and gate tween: 3 frames inside one beat | every door |

## 6. Cross-cutting issues

### 6.1 Engine needs (for the generic-choice agent and the run engine)

| # | Need | Why |
| --- | --- | --- |
| E1 | **`stance` per hotspot**: `{idle, current, other, queued}`, each a list of `piece` ops and `cast` lines (act, face, look_at, beats) that fire when the hotspot becomes current, stops being current, or is queued behind a stop; applied on the same beat as the touch | today `acting` only drives the hotspot's own actor; the choice needs chorus people, doors and props to react |
| E2 | **Window vantage**: `place.rail.window = {to, bars}` (a waypoint with yaw) which the block-3 decision move goes to instead of the next good/bad place (role still follows the rail); the window glance stays at most 8 degrees. **E2b**: scenes with an early-window hotspot (Floor, Chill-out) hold the vantage from beat 12.5 | the options must be on screen whatever the performance; today the camera is on the rail, often walking |
| E3 | **Route-derived tableau**: the route pieces read `route_of(current)`; a *stop* leaves the default route showing and puts its person in QUEUED; a **gamble** (bouncer, exam, throne) shows UNDECIDED (both doors half, gatekeeper centred) and the commit resolves it | the two-layer model of section 0 |
| E4 | **Multi-anchor hotspots**: an anchor list (thing, actor, figure) where a touch on any counts, the nearest wins, the hit radius is the union's | the gate plus its steward, the lever plus the core |
| E5 | Data edits only: homes (re-home, pin: no `side`), new actors, hotspot anchors, `NO_ACTOR` for the wizards, `tools/run/acting_data.py` entries for every directed person | |
| E6 | Held props baked into the pixel rig with up/down frames (`prop:<id>` on `hold_up`/`hold_low`) | the paddle, banner, lantern, rope |
| E7 | Cast ops **`light`** (on, off, pulse a map `kind: light` thing) and **`piece_move`** (tween a piece along waypoints over n beats) | door spills; the pint slide |
| E8 | The `figure` acting contract (today the Bassment's creatures) available in run hotspots and cast lines for the dog and the drone | already exists for creatures: `RunActing.figure_motion`, `TrialScene._animate_figure` |
| E9 | `HotspotView` shows the ring only on the current option and fainter (G7), and ignores it for options that have a thing with a stance | keep it a reinforcement |
| E10 | A reaction to a touch is scheduled for the next half beat at latest; frame swaps are quantised to beat sub-divisions (the cast `at_beat` can be fractional already) | G3, within one beat |

### 6.2 Camera and rail changes: the window vantage of every scene

Yaw 0 looks toward -z; 90 toward -x; -90 toward +x; 180 toward +z. Bearings are computed (positive = right of the view centre; screen x for a 1280 px stage, FOV +-54). Everything marked NEW must be added to the map's waypoints; check with `tools/story/check_map.gd` and screenshots with `RW_STORY_CAM`.

| Scene | Waypoint (NEW) | x, z, yaw | Options in view (bearing, distance) |
| --- | --- | --- | --- |
| `warehouse` | `floor_choice` | 0.0, 8.9, 0 | steward W -33 (4.8), dancer -17 (5.3), wizard +24 (3.2), steward E +36 (4.7), ball 0 (6.4) |
| `warehouse.bar` | `bar_choice` | 7.6, 0.6, -155 | bartender -41 (3.9), stranger / lantern -2 (4.5), curtain +10 (5.6), door +42 (2.0), roadie +49 (2.2) |
| `warehouse.balcony` | `balcony_choice` | -8.6, 4.4, 5 | skylight -28 (4.3), rope and stairs -1 (6.6), promoter +8 (6.6), door +18 (3.5), rail raver +32 (2.5) |
| `warehouse.chill` | `chill_choice` | 9.6, 11.4, 0 | wizard -35 (3.3), trapdoor -33 (2.4), sofa -19 (5.2), pals -8 (4.2), buddy +8 (4.3), door +10 (4.9), lamp +20 (5.3) |
| `warehouse.booth` | `booth_choice` | 0.0, -9.7, 180 | headphones -35 (1.6), decks 0 (1.4), crowd 0 (5.2), radio +42 (1.5) |
| `warehouse.exit` | `door_choice` | 0.0, 9.2, 180 | crack -30 (4.3), tunnel 0 (4 to 6.8), rope +14 (3.7), bouncer +31 (4.1) |
| `mothership` | `deck_choice` | -4.2, 6.9, -65 | DJ -38 (12), grey -19 (5.0), gallery door +17 (10.6), reactor door +30 (10.5) |
| `mothership.gallery` | `gallery_choice` | 15.5, 4.0, -125 | menu -39 (7.5), exit -17 (11.4), window +40 (6.0) |
| `mothership.reactor` | `reactor_choice` | 28.5, 8.5, -45 | engineer -42 (7.9), core -19 (12.4), lever +12 (2.7), boom barrier +40 (11.7) |
| `mothership.bridge` | `bridge_choice` | 41.5, -1.5, -140 | helm -37 (13.3), globe -23 (10), door +38 (9) |
| `mothership.exit` | `airlock_choice` | 34.5, 9.6, 180 | exam door -40 (3.1), medic -39 (3.8), probe -37 (3.0), hatch +6 (5.0), wheel +17 (7.7) |
| `underworld` | `arena_choice` | 0.0, 8.6, 0 | herald L -40 (6.2), bouncer -14 (9.4), chain +20 (8.3), herald R +40 (6.2) |
| `underworld.court` | `court_choice` | 11.6, 4.0, -90 | seal -16 (5.1), queen 0 (3.3), causeway +25 (8.1) |
| `underworld.furnace` | `furnace_choice` | -19.0, 4.0, -90 | smith and anvil -39 (3.3, 5.1), exit +15 (7.7), ladle +33 (5.9) |
| `underworld.pit` | `pit_choice` | 24.2, 11.2, 125 | bridge -36 (15.7), brazier -9 (14.9), guard +30 (7.0), door +41 (6.0) |
| `underworld.exit` | `throne_choice` | 24.5, 4.0, -90 | door L -28 (6.4), throne 0 (6.2), door R +28 (6.4) |

Far options (more than 10 m: the Mothership DJ, the Gallery exit, the Bridge helm, the Pit bridge) are 40 to 90 px tall on screen: they carry the choice with big shapes (light shafts, a swivelling chair, rising slabs) and a person who has a prop, never with a face.

### 6.3 Shared pieces reused across scenes

* **The pair idiom** (Floor stewards, Arena heralds, Throne doors, Deck doors, Bar curtain and door): current is open, up and cheerful; the other is shut, down and sulking and still soliciting. One engine feature (E1, E3) serves all of them.
* **The gatekeeper gamble** (Warehouse bouncer, Mothership medic, Underworld throne): UNDECIDED = both doors half open, the gatekeeper centred; the verdict opens one wide. One E3 feature.
* **The wizard**: one wardrobe, two instances, the same lit-staff and trapdoor idiom as the Floor's corridor.
* `ch_wh_door_leaf` (Bar, Balcony, Chill-out), `ch_wh_velvet_rope` (Balcony, Door), `ch_ms_iris_door` (5 uses), `ch_ms_drone` (Deck, Gallery), `ch_uw_portcullis` (2), `ch_uw_iron_door` (Furnace, Pit), the lantern imp (Court, Pit).
* The acts and faces are shared where they can be: `sulk` appears in all 16 scenes, `usher` in 12, `hopeful` in 11, `turn_away` in 11, `hold_up` in 10, `shrug` in 9. Some are single-scene by design (`wink`, `slide`, `withhold` at the Bar; `yawn`, `pat_seat` at the Chill-out; `thumbs_up` and `thumbs_down` at the Arena; `tug` at the Chill-out and Booth): cut those first if the sheet budget bites.

### 6.4 Other issues and risks

1. **Note lanes cover the stage** (x about 92-192, 308-408, 872-972, 1088-1188 on 1280 px). The vantages put options at about +-40 or inside +-22 degrees where possible; still, a lane in the last block will sometimes cross an option for a second. Verify on 844 x 390 and keep every option's sprite at least 72 px (hit radius 36 px minimum).
2. **Pixel budget at distance** (section 0): faces fail past 4 m. Chorus people are placed at 3 to 5 m where the room allows; the Floor stewards, the Arena heralds and the Deck drone are at 5 to 10 m and rely on a big prop and silhouette.
3. **Map edits** (homes, re-sites, new waypoints, new things) must keep the portal graph: the Door's `door_r` and `crack_door` move together; the Arena chain and bouncer sites must keep the cinematics' targets (`arena_gate`) valid; check with `tools/run/check_hotspots.py` and `tests/test_hotspots_data.gd`.
4. **Sheet budget**: about 45 directed people across the three worlds gain at least one new act or face (about 20 in the Warehouse, 9 in the Mothership, 17 in the Underworld); the plan's cap was +15 % per chapter (`docs/THREE_PATHS_AND_FACES_PLAN.md` 2.2). The roll-up favours few acts (12) over many people; measure the sheet bytes before and after as `docs/FACE_POLISH.md` did.
5. **Colour independence**: every pair differs in silhouette: paddle up or down, gate up or down, door open or shut, banner raised or furled, chair turned or not, rods in or out, slabs risen or sunk, jaw open or shut. Colour (amber, cyan, orange, white, green) only supports.
6. **Default first beat**: the idle state is the default; the alternatives wake at beat 48 (the window), when a non-current person's solicitation begins. A player who never touches anything still sees the default way open and cheerful.
7. **Wizards**: the early window (beats 16-47) needs E2b or the camera has its back to him; if E2b is not built, keep the wizard where the rail passes (at the steps) instead.
8. **Portals and secrets** (star, radio, ember, headphones, star_chart, led_wall) are conditional; build them after their scene's route pair, since a new player never sees them early.
9. **Suggested build order**: (1) E1, E2, E3 and the Floor, which proves the pair idiom; (2) the Door and the Throne (the two world exits, the gatekeeper gamble); (3) the Bar, Deck, Airlock, Arena; (4) the Balcony; (5) the single-exit scenes (Chill-out, Gallery, Bridge, Court, Pit); (6) the P3 scenes and portals.
10. **Not covered here**: the Hospital, Ward, their late worlds, the Bassment and the three paths (other designers), and the 3D art of the existing set (these briefs only add pieces and people to it).
