# Game guide: how the run fits together today

For the owner, to give feedback. Written from the code and data on `main` (5 November 2026), not from playing. Where the older docs and the code disagree, this guide follows the code. Nobody has heard or played the paths by hand yet (see the handover); the scene looks below come from scene names and world notes, not from screenshots.

## 1. The shape of a run

You play four pads in time with drum and bass while a first-person camera walks through rooms full of dancers. A room is called a scene. Each scene is one 64-beat stretch of music (22 seconds at 174 BPM). You play cues, the music builds if you play well, and near the end of the scene you touch a door, a person or an object in the room to choose where to go. The route you pick takes you to the next scene. Doing nothing takes the default door. Your crowd's energy is your life: good blocks raise it, bad blocks drain it, and at zero the crowd goes home and the run ends. The main run has no ending. After the Hospital or the Ward it loops through "late" rooms until you lose. Three side adventures (paths) are entered through hidden doors in the Warehouse. They have endings and send you back to the Warehouse.

## 2. The places

Main run: 7 worlds, 36 scenes, all at 174 BPM, one 64-beat pass per scene. Paths: Gospel 17 scenes, Squadron 14, Ember 15. A scene's exits are the doors you can touch near the end of it.

**Warehouse (night club)**

| Scene | Looks like | Goes to |
| --- | --- | --- |
| The Floor (start) | Main dance floor, speaker stacks, a wizard at the left edge | Bar (default), Balcony. Wizard: the Bassment |
| The Bar | Club bar with a bartender and a stranger | Chill-out (default), Booth. Ember portal |
| The Balcony | Rail over the floor, a promoter | Chill-out (default), Booth. Gospel portal |
| The Chill-out | Sofas, lava lamp, the wizard again | The Door. Wizard: the Bassment |
| The Booth | DJ decks, headphones | The Door. Squadron portal (radio) |
| The Door | Club exit, a bouncer | Mothership (default), Underworld |

**The Mothership (spaceship)**

| Scene | Looks like | Goes to |
| --- | --- | --- |
| The Deck (start) | Ship deck, a grey alien, an alien DJ | Gallery (default), Reactor |
| The Gallery | Observation gallery with a window | Bridge |
| The Reactor | Reactor core, an engineer | Bridge |
| The Bridge | Helm and star chart | Airlock |
| The Airlock | Airlock wheel, an examiner | Hospital (default), Ward |

**The Underworld (hell club; the music is a stand-in, see section 6)**

| Scene | Looks like | Goes to |
| --- | --- | --- |
| The Arena (start) | Chains, a bouncer | Court (default), Furnace |
| The Court | A seal, a queen among dancers | Pit |
| The Furnace | Anvil and ladle | Pit |
| The Pit | Lava bridge, brazier | Throne |
| The Throne | A throne | Hospital (default), Ward |

**The Hospital**

| Scene | Looks like | Goes to |
| --- | --- | --- |
| The Ward (start) | Hospital ward, nurse, family, monitor | Corridor |
| The Corridor | Trolley, a quiet door | Day Room (default), Cafeteria |
| The Day Room | TV, a granny | Garden |
| The Cafeteria | Vending machine, a kid | Garden |
| The Garden | A lamp, a mum | Bandstand |
| The Bandstand | A microphone | Hospital late (default), Ward late |

**The Ward (mental hospital)**

| Scene | Looks like | Goes to |
| --- | --- | --- |
| The Day Room (start) | Orderly, window, the blackjack table | Art Room (default), Dormitory |
| The Art Room | Painter, easel | Corridor |
| The Dormitory | Sleeper, cabinet | Corridor |
| The Corridor | Phone, a king, a mural door | Courtyard |
| The Courtyard | Chef, lights | Stage |
| The Stage | A talent lamp | Hospital late (default), Ward late |

**Hospital, late** (loops): Garden (start) to Cafeteria (default) or Quiet Room, then Bandstand. The Bandstand goes back to the Garden (default, the loop) or on to Ward late.

**Ward, late** (loops): Courtyard (start) to Treatment Room (default) or Dormitory, then Day Room. The Day Room goes back to the Courtyard (default, the loop) or to Hospital late.

**The Bassment (the wizard's dungeon).** Touch the wizard in the Floor or the Chill-out early in the scene. A separate 63-passage dungeon (16 zones, 10 creatures) plays inside the run with the same pads and music. It returns to the Warehouse on death, victory or the back key.

**The Life of Jesus (Gospel, 124 BPM, entered by the star on the Balcony).** Needs the floor seen from the balcony rail first.

| World and scene | Goes to |
| --- | --- |
| Jordan: Bethlehem, the Star (start, one pass) | Baptism |
| Jordan: Baptism | Nazareth (default), Wilderness |
| Jordan: Temptation in the Wilderness | Calling the Fishermen, Healing in Capernaum |
| Jordan: Nazareth Workshop | Calling the Fishermen, Healing in Capernaum |
| Galilee: Calling the Fishermen | Sermon on the Mount, Storm |
| Galilee: Healing in Capernaum | Sermon on the Mount, Bethany |
| Galilee: Sermon on the Mount | Loaves and Fishes, Storm |
| Galilee: Storm on Galilee | Loaves and Fishes, Bethany |
| Road: Bethany, the Shared Table | Loaves and Fishes, Entry into Jerusalem |
| Road: Loaves and Fishes | Entry into Jerusalem, or round again to Bethany |
| Road: Entry into Jerusalem | The Temple, Gethsemane |
| Jerusalem: The Temple | Gethsemane, The Trial |
| Jerusalem: Gethsemane | The Trial, Road Beyond Jerusalem |
| Jerusalem: The Trial | Golgotha, Road Beyond Jerusalem |
| Jerusalem: Golgotha (one pass) | The Empty Tomb |
| Jerusalem: The Empty Tomb (ending "tomb") | Back to the Warehouse |
| Jerusalem: The Road Beyond Jerusalem (ending "road") | Back to the Warehouse |

**The Mission Count (Squadron, 140 BPM, entered by the radio in the Booth).** A bomber crew under an absurd rule.

| Scene | Goes to |
| --- | --- |
| Base: C01 Briefing Room (start) | Hospital C03 (default), Flight Line C02 |
| Base: C02 Flight Line | Bombing Mission C04, Syndicate C05 |
| Base: C03 Hospital | Syndicate C05, Surgeon's Office C06 |
| Air: C04 Bombing Mission | Gunner's Last Flight C07, back to C03 |
| Air: C05 Syndicate | Old City C08, loop to C06 |
| Air: C06 Surgeon's Office | back to C02, Colonel's Deal C09 |
| City: C07 Gunner's Last Flight | loop to Ruined City C10, back to C03 |
| City: C08 Old City | Ruined City C10, Colonel's Deal C09 |
| City: C09 Colonel's Deal | Escape North C12, Endless Missions C11 |
| City: C10 Ruined City | loop to C09, Escape North C12 |
| Escape: C11 Endless Missions | loop to C02, loop to C12 |
| Escape: C12 Escape North | Captured C14, Neutral Coast C13 |
| Escape: C13 Neutral Coast (ending "free") | Back to the Warehouse |
| Escape: C14 Captured | loop to C11, loop to C12 |

**The Ember Road (Ember, 145 BPM, entered by the ember on the Bar table).** Needs the stranger's VIP pass first.

| Scene | Goes to |
| --- | --- |
| Hollow: E00 Orchard (start, one pass) | Ford |
| Hollow: E01 Ford at Night | Lantern Inn, Birch Hall |
| Hollow: E02 Lantern Inn | Birch Hall, High Pass |
| North: E03 Birch Hall | High Pass, Deep Halls |
| North: E04 High Pass | Deep Halls, Falls |
| Deeps: E05 Deep Halls | Falls, back to High Pass (loop) |
| Deeps: E06 Falls | Reed Marsh, Black Wall, Taken |
| Marsh: E07 Reed Marsh | Black Wall, Stair of Bells |
| Marsh: E08 Black Wall | Stair of Bells, Ash Plain, Taken |
| Marsh: E09 Stair of Bells | Ash Plain, Throat, Taken |
| Marsh: E10 Ash Plain | Throat, Taken |
| Mountain: E11 Throat | Drowned Spring, Keeper |
| Mountain: E12 Drowned Spring (ending "quenched") | Back to the Warehouse |
| Mountain: E13 Keeper (ending "kept") | Back to the Warehouse |
| Mountain: E14 Taken | loop to Ash Plain, loop to Black Wall |

A fourth path, the Stub (2 scenes, 124 BPM), is a developer test and not part of the game.

## 3. The map

```
WAREHOUSE (4 scenes)  Floor > Bar | Balcony > Chill-out | Booth > Door
  |-- hidden: Balcony star > GOSPEL   Booth radio > SQUADRON   Bar ember > EMBER  (each ends back here)
  |-- wizard (Floor, Chill-out) > BASSMENT dungeon > back to the Warehouse
  +-- Door > MOTHERSHIP (4)  or  UNDERWORLD (4)
        both > HOSPITAL (5)  or  WARD (5)
        Hospital Bandstand and Ward Stage > HOSPITAL LATE (3) or WARD LATE (3)
        the two late worlds loop round and into each other until you lose
```

A full pass through the first three worlds is 13 scenes (about 4.8 minutes). The late worlds then repeat 3 scenes at a time.

## 4. Time

At 174 BPM: one beat is 0.345 s, a bar 1.38 s, a block (16 beats) 5.5 s, a scene (64 beats, 4 blocks) 22.1 s. Gospel scenes are 31.0 s a pass, Squadron 27.4 s, Ember 26.5 s.

**Two laps.** Every path scene plays two passes in a row (62 s Gospel, 55 s Squadron, 53 s Ember), except the three openers and Golgotha, which play one. Lap one has no doors and no choice. The doors, the choice and the exit are in lap two only. The main run has one pass per scene, so about 22 s a room.

**What happens in a scene (beat counts from the scene's first beat, 0 to 64):**

| Beat | What happens |
| --- | --- |
| 0 | New scene on the downbeat. Drums alone. Lamps swell, the camera starts its tour, people start their acts. |
| 0 to 12 of each block | Cues fall. The last 4 beats of a block are empty on purpose. |
| 12.5 of each block (12.5, 28.5, 44.5, 60.5) | The block is judged. 60% of the cues or better is a pass. A pass moves the music one step up, a miss repeats the step. Energy changes. The camera takes one step on its rail. |
| 16 | Bass enters (if block 1 passed). Bass cues. |
| 32 | Drums return, bass stays. Drum cues. |
| 48 | Bass strongest, bass cues. A riser sound if the top step is already reached, a fall sound if not. |
| 44.5 | By the code the doors become touchable here (the older docs say beat 48 or 49). The camera turns to show them by about beat 49. |
| 60.5 | The choice is made. If you touched something, the last block's pass or miss decides its good or bad outcome. If you touched nothing, the default exit is taken whatever you played. |
| 61 | Same-world move: the camera walks through the chosen door. |
| 62 to 64 | World change: the picture closes to a lit doorway. |
| 64 | Next scene begins. The next block's first cues were already placed at 60.5. |

Cues are judged at 45 ms (perfect), 90 ms (great) and 140 ms (accept). A hold counts by how much of it you held. Special doors: the wizard (the Bassment) can be touched in blocks 1 and 2 only. The blackjack table can be touched in any block.

## 5. How you move on

* **Choosing.** Touch a lit door, a person or an object. You may change your mind until beat 60.5. Doors are lit with light, not words. Keys 1 to 4 pick the doors on a desktop.
* **What decides the way.** The thing you touched, then whether the last block passed. Most exits lead to the same place either way, but a failure gives a stumble (energy loss, rough walk). Some people and objects only act as extra story or flags. Some doors and flags decide later scenes (Ember especially).
* **The default.** The first-listed exit of every scene. Doing nothing always takes it.
* **A route lock.** If the two routes lead to scenes with different chart packs, the next scene's first cues are fixed at 60.5, so the other route greys out from then.
* **Energy.** Starts at 60, max 100. A pass gives +5 to +11, a miss takes 3 to 10. Six full misses in a row from the start end the run. Hotspot outcomes can add or take a few points (never to zero).
* **Failing.** At zero the music fades over 2 beats and "The crowd has gone home" appears: Retry the world, choose a reached level, or home. Reached worlds are saved, and the home screen lists them.
* **Laps and loops.** Late worlds and some path routes are marked as loops and bring you back to an earlier scene. A path scene's lap two repeats lap one's music and cues.
* **Leaving a path.** Pause has "Leave this path" (from beat 61 of a lap).

## 6. The music today

**In a scene.** The music is built from loops of drums, bass and a synth layer, all at 174 BPM. Each phase starts on drums alone. The bass and synth enter when you pass block 1 and then keep running. Each block's pass or miss sets the mix: step 1 drums only, step 2 bass plus drums at half, step 3 drums back with bass, step 4 bass strongest. Drum blocks ask for drum cues (mostly the kick pad and the snare pad). Bass blocks ask for bass notes across all four pads. The mix fades smoothly over 0.35 s. A touched door can briefly sink the bass and synth ("dip", 6 beats). The bass of the scene you leave carries under the next scene's drums if they are the same music family.

**Which music where (main run, from content/story/music.json).** Every scene plays a 16-bar slice of a longer arrangement of its world's music family. Each world has three arrangements and the game picks one per run by a random seed. Each slice is one 16-bar part or two 8-bar parts, taken from that family's loops. Slot numbers run in scene order.

| Area | Music family (owner's own Beat Shaper loops) | Status |
| --- | --- | --- |
| Warehouse (6 scenes) | Lv1 Warehouse | Real |
| Mothership (5) | Lv2 Alien Spaceship | Real |
| Underworld (5) | Cold Fusion Interface | Real loops, marked temporary: a stand-in for a Lv3 Hell set that does not exist |
| Hospital (6) and Hospital late (4) | Lv4 Hospital | Real |
| Ward (6) and Ward late (4) | Lv5 Asylum | Real |
| Bassment | dd_part1 (a fight set is named but not used) | Real |
| Gospel (17 scenes) | Synthesised placeholder, house, 124 BPM | Placeholder, never listened to |
| Squadron (14) | The owner's loops C01 to C14, 140 BPM | Real (4-bar loops, six scenes loosely timed) |
| Ember (15) | Synthesised placeholder, psytrance, 145 BPM | Placeholder, never listened to |

The docs still say the Underworld plays Lv2 variants and that each scene names one pack. The code does neither: every main scene uses an arrangement, and the Underworld uses Cold Fusion.

**The four pads.** Four lit pads on screen (touch on a phone). They have no names. In drum blocks the cues are the kick on pad 1 and the snare on pad 4. In bass blocks any of the four pads can be asked for. Words PERFECT, GREAT and MISS still show on the pads.

## 7. Other things on the way

* **Blackjack table** (Ward, The Day Room only). A table with three players in the room. Touch it in any block. If that block's cues were 25% right or better you sit down. The run stays in the scene while you play. Two missed blocks in a row make you wobble and three drop you off the chair. Stake 5 pounds from a 20 pound wallet. The table is silent. You can get up by any door in the room. Other rooms have no minigame.
* **The Bassment (a trial).** Part of the run, described in section 2. The pads and clock keep going. The "Wizard Duel" over wifi and the old military campaign are developer only and not part of the run.
* **Cinematics.** Short scripted camera walks and people's acts that play when an outcome fires: 141 in the main run, 23 Gospel, 4 Squadron, 7 Ember. They are measured in bars or beats.
* **No text in play.** No titles or captions unless the developer text switch is on.

## 8. How to try things

Use the Godot 4.5.1 binary in `/home/joe/godot451/` (as in the docs).

* **Debug / Playtest** on the home screen: lists all 82 scenes, starts at any one, shows which music files play, and writes your likes and dislikes to a notes file. Plays in a throwaway save. Easiest route.
* `RW_RUN_START=<scene id>` plus `res://src/run/run_play.tscn`: start the main run at a scene (for example `ward`).
* `RW_RUN_PATH=gospel` (or `squadron`, `ember`) plus `RW_RUN_START=<scene id>`: start inside a path.
* `RW_RUN_BOT=perfect` plays the pads for you. Other values: `none`, `accuracy:0.7`.
* `RW_DEBUG=1`: debug overlay on a normal run. `RW_DEV_TEXT=1`: the old play text.
* `RW_RUN_SEED=<n>`: fixes which arrangement each scene gets.
* `RW_RUN_FLAGS=wh_saw_floor` or `wh_vip_pass`: opens the Gospel or Ember portal in the Warehouse.

## Unfinished, placeholder or off

* Gospel and Ember music are synthesised placeholders. The Underworld uses stand-in music.
* Nothing has been played by hand or on a phone, and no one has listened to the paths.
* Track mode (whole recorded songs) exists as a separate test scene and is not reachable from the home screen or the run.
* Three portals are small and gated and may be hard to find. A different look for a finished path is not built.
* The main run's `min_cues_for_pass` setting in the data is not read by any code.
