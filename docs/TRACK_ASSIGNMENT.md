# Track assignment: which recording plays in which scene

For the owner to review and change. The data is `content/run/track_scenes.json`; this page explains it. Contract: `docs/RUN_TRACK_SCENES.md`. Catalogue: `docs/MUSIC_TRACKS.md`.

## Approach

- Every one of the 82 scenes (main run 36, Gospel 17, Squadron 14, Ember 15) has a first choice and two alternates. The run's seed picks one of the three, so repeat visits vary.
- Each world has its own palette. Warehouse: bright club anthems. Mothership: sparse, technical, spacey. Underworld: dark, heavy, low. Hospital: light and clean, then an anthem at the exit. Ward: odd, talkative, busy. The late worlds get the hardest tracks. Intensity rises through each world to its exit scene and through the run toward the late worlds.
- Where I know a track (the title, the artist, the release) its real character came first. Where I did not, the table says "numbers only" and I went by tempo, low-end share, brightness, busyness and dynamics. I could not listen to anything for this. Please treat every "why" as a guess to check by ear.
- As a first choice no track is used more than twice. When a track is used twice it is `drop1` in one scene and `drop2` in the other, and the two scenes are in different worlds or paths. No two connected scenes share a track in any slot, counting the links between worlds, the paths' endings back to the Warehouse and the three portals. A scene's three tracks are all different.
- In a scene whose first choice is `drop1`, the second alternate uses `drop2` where that track has two or more drops, so a repeat visit also changes where in the song you come in. In a `drop2` scene both alternates use `drop1`.
- Two tracks are not 172 to 176 BPM. Artifice (140) is in Squadron's quiet Hospital scene. Stars Are Calling (168) opens Gospel at the star. Neither is in the first two worlds of the main run.
- Gospel and Ember play real drum and bass at 174 BPM, not their placeholder 124 and 145 BPM. I chose their tracks for mood, not for those old tempos.
- Entry points: `drop1` is shown as d1, `drop2` as d2. Entries in brackets are for the alternates.

Tracks with only one drop (Vigilante, Lotus) always use `drop1`. Soldiers has its first drop at 0 s, so its `drop1` starts at bar 0 of the track.


## Main run: Warehouse

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `warehouse` | The Floor: main dance floor, speaker stacks, a wizard | Acuna, Go Back | d1 | DC Breaks, Slugs (d1); Moving Fusion, Makosa (d2) | Owner played and approved it. The reference for the whole run. |
| `warehouse.bar` | The Bar: bartender and a stranger | Need For Mirrors, Zero T, Top Shelf (feat. Spikey Tee) | d1 | Bennie & Jam Thieves, Madting (d1); Hamilton, Soundboy VIP (d2) | Top Shelf for a bar. Loose, bouncy, mid-bright. |
| `warehouse.balcony` | The Balcony: rail over the floor, a promoter | Chase & Status, No Problem | d1 | Sub Focus, Rock It (d1); Amplify & Crossy, Badman (d2) | Big bright anthem, the view over a full floor. |
| `warehouse.chill` | The Chill-out: sofas, lava lamp | Stimpy, Party Last Sounds | d1 | Annix, Kingdom (d1); Northern Zone, Faint (d2) | Last sounds of a party, darker and less bright than the floor. |
| `warehouse.booth` | The Booth: DJ decks, headphones | Fatboy Slim, Right Here, Right Now (One In The Jungle Remix) | d1 | DC Breaks, Take That VIP (d1); DC Breaks, Gambino (d2) | A famous crowd track for the DJ. Known and easy to love. |
| `warehouse.exit` | The Door: club exit, a bouncer | Fresh, The Gatekeeper | d1 | DC Breaks, Proton (d1); Bou & Kasra, Trenchfoot (d2) | The Gatekeeper for the bouncer. Heavier, leads out of the club. |

## Main run: Mothership

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `mothership` | The Deck: ship deck, grey alien, alien DJ | SMG, Sono | d1 | RAM Trilogy, Evolution (Marcus Intalex & ST Files Remix) (d1); Metrik, Hackers (d2) | Sparse, dark and spacey. A strange first step after the club. |
| `mothership.gallery` | The Gallery: observation window | Annix, Kingdom | d1 | Madface, Dawning (d1); Paralel, In The Clouds (d2) | Few events, lots of room. The calm of looking out of a window. |
| `mothership.reactor` | The Reactor: core and an engineer | Bad Company UK & Trace, Nitrous (Audio Remix) | d1 | Ryme Tyme, Optiv & BTK, Ignition (d1); Metrik, T-2000 (d2) | Four-drop techstep, machine-like. The ship at full power. |
| `mothership.bridge` | The Bridge: helm and star chart | Metrik, Hackers | d1 | Break, Overstayed (d1); RAM Trilogy, Evolution (Marcus Intalex & ST Files Remix) (d2) | Four drops, tight and technical. Navigation and screens. |
| `mothership.exit` | The Airlock: wheel, an examiner | Culture Shock, Machine | d1 | Metrik, T-2000 (d1); Bad Company UK & Trace, Nitrous (Audio Remix) (d2) | Machine for the airlock wheel. The busiest track of the world. |

## Main run: Underworld

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `underworld` | The Arena: chains, a bouncer | Exile, Destructive Vibrations | d1 | Black Sun Empire, Extraction (d1); Origin Unknown, Valley of the Shadows (Chase & Status Remix) (d2) | Dark and heavy from the start. The floor has cracked. |
| `underworld.court` | The Court: a seal, a queen among dancers | Simula, Lazy Horn | d1 | K Motionz, Simula, Phantasm (d1); Visages, Liber Primus (d2) | Low, swaggering horn. The queen holds court. |
| `underworld.furnace` | The Furnace: anvil and ladle | PARTICLE, Pyro | d1 | Ryme Tyme, Optiv & BTK, Ignition (d1); Bou & Kasra, Trenchfoot (d2) | Pyro: fire, a dark heavy roll. |
| `underworld.pit` | The Pit: lava bridge, brazier | Black Sun Empire, Extraction | d1 | Teddy Killerz, Night Train (d1); Exile, Destructive Vibrations (d2) | Black Sun Empire at full weight. The peak before the throne. |
| `underworld.exit` | The Throne: a throne | Visages, Liber Primus | d1 | InsideInfo, Victory Over Death (Feat. MoniKali) (d1); AC13, Shostakovich (d2) | Darkest, lowest, most ceremonial track here. |

## Main run: Hospital

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `hospital` | The Ward: nurse, family, monitor | Sub Focus, X-Ray (Metrik Remix) | d1 | Warm Roller, Memory (Floodlight) (d1); Northern Zone, Faint (d2) | X-Ray: a hospital word. Tight and clean. |
| `hospital.corridor` | The Corridor: trolley, a quiet door | Loadstar, Dr.Karg | d1 | Trex, Chit Chat (d1); Original Sin, Therapy (Remix) (d2) | Dr. Karg, a doctor on the corridor. Recognised by name only, numbers say light. |
| `hospital.dayroom` | The Day Room: TV, a granny | Northern Zone, Faint | d1 | Warm Roller, Memory (Floodlight) (d1); Paralel, In The Clouds (d2) | Faint: low events, gentle. A quiet sitting room. |
| `hospital.cafeteria` | The Cafeteria: vending machine, a kid | Su3-ject, Crystal Eyes | d1 | Bennie & Jam Thieves, Madting (d1); Stimpy, Party Last Sounds (d2) | Crystal Eyes: bright and light, for the kid. |
| `hospital.garden` | The Garden: a lamp, a mum | Bungle, Cocooned | d1 | Madface, Dawning (d1); Frankee, Flim Flam (d2) | Cocooned: long, soft, steady. The calm of the world. |
| `hospital.exit` | The Bandstand: a microphone | Sub Focus, Rock It | d1 | Chase & Status, No Problem (d1); Amplify & Crossy, Badman (d2) | Anthem for the microphone. Lifts the exit scene. |

## Main run: Ward

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `ward` | The Day Room: orderly, window, blackjack table | Trex, Chit Chat | d1 | Unglued, Telefonik (d1); Frankee, Flim Flam (d2) | Chit Chat for a room of talk and a card table. |
| `ward.art` | The Art Room: painter, easel | K Motionz, Simula, Phantasm | d1 | SMG, Sono (d1); Nectax, Zephyr (d2) | Odd, ghostly, sparse. Strange pictures. |
| `ward.dorm` | The Dormitory: sleeper, cabinet | Warm Roller, Memory (Floodlight) | d1 | Bungle, Cocooned (d1); SMG, Sono (d2) | Warm Roller Memory: quiet, wide dynamics, dreamlike. |
| `ward.corridor` | The Corridor: phone, a king, a mural door | Unglued, Telefonik | d1 | Trex, Chit Chat (d1); Culture Shock, Machine (d2) | Telefonik for the phone. Mid-dark and busy. |
| `ward.courtyard` | The Courtyard: chef, lights | Radiax, Headway (Floodlight) | d1 | DC Breaks, Gambino (d1); Moving Fusion, Makosa (d2) | Busy, bright, dynamic. Lights and a cook at work. |
| `ward.exit` | The Stage: a talent lamp | Hamilton, Soundboy VIP | d1 | DC Breaks, Take That VIP (d1); Sub Focus, Rock It (d2) | Soundboy VIP, a stage track, jump-up swagger. |

## Main run: Hospital, late

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `hospital_late` | The Garden after dark (loops) | Teddy Killerz, Night Train | d1 | Black Sun Empire, Extraction (d1); Bad Company UK & Trace, Nitrous (Audio Remix) (d2) | Night Train: the garden is no longer kind. |
| `hospital_late.cafe` | The Cafeteria (loops) | A.M.C, Noise Of Thunder | d1 | DC Breaks, Slugs (d1); DC Breaks, Proton (d2) | Noise of Thunder: hard and loud, a big step up. |
| `hospital_late.quiet` | The Quiet Room (loops) | LSB, The Hurting | d1 | In:Most, Pulsar (Floodlight) (d1); InsideInfo, Victory Over Death (Feat. MoniKali) (d2) | The Hurting: long dark build then heavy. Not quiet at all. |
| `hospital_late.exit` | The Bandstand (loops) | Freestylers, Pendulum, SirReal, Painkiller - Noisia Remix | d1 | Exile, Destructive Vibrations (d1); Sub Focus, Rock It (d2) | Painkiller (Noisia remix): the hardest exit. |

## Main run: Ward, late

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `ward_late` | The Courtyard after hours (loops) | Break, Overstayed | d1 | Drumsound & Bassline Smith, Vigilante (d1); A.M.C, Noise Of Thunder (d2) | Overstayed: the night has gone on too long. |
| `ward_late.treat` | The Treatment Room (loops) | Original Sin, Therapy (Remix) | d1 | K Motionz, Simula, Phantasm (d1); Frankee, Flim Flam (d2) | Therapy (Remix): the name says it. Four drops. |
| `ward_late.dorm` | The Dormitory (loops) | Frankee, Flim Flam | d1 | In:Most, Pulsar (Floodlight) (d1); LSB, The Hurting (d2) | Heavy low end, sleepless. Numbers only. |
| `ward_late.exit` | The Day Room (loops) | Moving Fusion, Makosa | d1 | Freestylers, Pendulum, SirReal, Painkiller - Noisia Remix (d1); Metrik, T-2000 (d2) | Makosa: long, busy, rolling. A big finish to the loop. |

## Gospel (The Life of Jesus): Jordan

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `jordan` | Bethlehem, the Star (one pass) | Mantra, Decibella & Tim Reaper, Stars Are Calling | d1 | InsideInfo, Victory Over Death (Feat. MoniKali) (d1); Annix, Kingdom (d2) | A star. 168 BPM, a gentler change of pace to open. |
| `jordan.baptism` | Baptism in the Jordan | Paralel, In The Clouds | d1 | RAM Trilogy, Evolution (Marcus Intalex & ST Files Remix) (d1); Madface, Dawning (d2) | In the Clouds: the descending dove. |
| `jordan.wilderness` | Temptation in the Wilderness | AC13, Shostakovich | d1 | Origin Unknown, Valley of the Shadows (Chase & Status Remix) (d1); Visages, Liber Primus (d2) | Dark, bare, huge dynamics. Alone in the desert. |
| `jordan.nazareth` | Nazareth Workshop | Bennie & Jam Thieves, Madting | d1 | Bungle, Cocooned (d1); Warm Roller, Memory (Floodlight) (d2) | Lightest, least bass-heavy track. A home, a bench. |

## Gospel (The Life of Jesus): Galilee

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `galilee` | Calling the Fishermen | Su3-ject, Crystal Eyes | d2 | Radiax, Headway (Floodlight) (d1); Mr Traumatik ft. Posk, Lotus (d1) | Crystal Eyes: water, light, bright. |
| `galilee.capernaum` | Healing in Capernaum | Northern Zone, Faint | d2 | Loadstar, Dr.Karg (d1); Nectax, Zephyr (d1) | Faint: gentle and sparse for the healing. |
| `galilee.mount` | Sermon on the Mount | Madface, Dawning | d1 | DC Breaks, Take That VIP (d1); Paralel, In The Clouds (d2) | Dawning: a crowd on a hillside, uplifting. |
| `galilee.storm` | Storm on Galilee | Bad Company UK & Trace, Nitrous (Audio Remix) | d2 | Freestylers, Pendulum, SirReal, Painkiller - Noisia Remix (d1); Teddy Killerz, Night Train (d1) | Four-drop techstep for the storm. Peak of the world. |

## Gospel (The Life of Jesus): Road

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `road` | Bethany, the Shared Table | Warm Roller, Memory (Floodlight) | d2 | Mr Traumatik ft. Posk, Lotus (d1); Bennie & Jam Thieves, Madting (d1) | Memory: warm, quiet, a meal among friends. |
| `road.loaves` | Loaves and Fishes | Amplify & Crossy, Badman | d1 | Su3-ject, Crystal Eyes (d1); Stimpy, Party Last Sounds (d2) | Badman: bright and jubilant. Baskets fill. |
| `road.entry` | Entry into Jerusalem | DC Breaks, Take That VIP | d1 | DJ Fresh, Tombraider (d1); Chase & Status, No Problem (d2) | Take That VIP: a crowd cheering a procession. |

## Gospel (The Life of Jesus): Jerusalem

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `jerusalem` | The Temple | DC Breaks, Slugs | d1 | Drumsound & Bassline Smith, Vigilante (d1); A.M.C, Noise Of Thunder (d2) | Slugs: the tables go over. Hard and angry. |
| `jerusalem.gethsemane` | Gethsemane | LSB, The Hurting | d2 | Nectax, Zephyr (d1); Bungle, Cocooned (d1) | The Hurting: a night of anguish. Second drop only, so a long wait first. |
| `jerusalem.trial` | The Trial | Origin Unknown, Valley of the Shadows (Chase & Status Remix) | d1 | Fresh, The Gatekeeper (d1); AC13, Shostakovich (d2) | Valley of the Shadows: dark, accusing. |
| `jerusalem.golgotha` | Golgotha (one pass) | Visages, Liber Primus | d2 | LSB, The Hurting (d1); In:Most, Pulsar (Floodlight) (d1) | Darkest track, heavy and bare. Used from its second drop. |
| `jerusalem.tomb` | The Empty Tomb (ending: tomb) | InsideInfo, Victory Over Death (Feat. MoniKali) | d1 | Mantra, Decibella & Tim Reaper, Stars Are Calling (d1); Annix, Kingdom (d2) | Victory Over Death. The title is the scene. |
| `jerusalem.road` | The Road Beyond Jerusalem (ending: road) | Paralel, In The Clouds | d2 | Mantra, Decibella & Tim Reaper, Stars Are Calling (d1); Mr Traumatik ft. Posk, Lotus (d1) | In the Clouds again, hopeful, for the walk out. |

## Squadron (The Mission Count): Base

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `base` | C01 Briefing Room | Mampi Swift, Soldiers | d1 | Drumsound & Bassline Smith, Vigilante (d1); Bou & Kasra, Trenchfoot (d2) | Soldiers: it opens with its drop. The tune of the squadron. |
| `base.c02` | C02 Flight Line | Nu Elementz, Trenches | d1 | Break, Overstayed (d1); Metrik, Hackers (d2) | Trenches: short, bright and military. |
| `base.c03` | C03 Hospital | Ternion Sound, Artifice | d1 | In:Most, Pulsar (Floodlight) (d1); Northern Zone, Faint (d2) | Artifice at 140 BPM. A slower, quiet scene, Squadron's own tempo. |

## Squadron (The Mission Count): Air

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `air` | C04 Bombing Mission | Drumsound & Bassline Smith, Vigilante | d1 | Mampi Swift, Soldiers (d1); Black Sun Empire, Extraction (d2) | Vigilante: bright, hard and one long drop. The raid. |
| `air.c05` | C05 Syndicate | DC Breaks, Proton | d1 | Culture Shock, Machine (d1); Bad Company UK & Trace, Nitrous (Audio Remix) (d2) | Proton: clean, tight, a business. |
| `air.c06` | C06 Surgeon's Office | Metrik, T-2000 | d1 | SMG, Sono (d1); Sub Focus, X-Ray (Metrik Remix) (d2) | T-2000: cold, mechanical, a bureaucracy. |

## Squadron (The Mission Count): City

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `city` | C07 Gunner's Last Flight | Nectax, Zephyr | d1 | LSB, The Hurting (d1); InsideInfo, Victory Over Death (Feat. MoniKali) (d2) | Zephyr: short, one wide quiet break. A sad one. |
| `city.c08` | C08 Old City | RAM Trilogy, Evolution (Marcus Intalex & ST Files Remix) | d1 | Origin Unknown, Valley of the Shadows (Chase & Status Remix) (d1); SMG, Sono (d2) | Evolution: long, atmospheric, a city seen from above. |
| `city.c09` | C09 Colonel's Deal | Fresh, The Gatekeeper | d2 | AC13, Shostakovich (d1); Visages, Liber Primus (d1) | Gatekeeper again, from the second drop. Brass-like menace. |
| `city.c10` | C10 Ruined City | Bou & Kasra, Trenchfoot | d1 | Mampi Swift, Soldiers (d1); Exile, Destructive Vibrations (d2) | Trenchfoot: dark and rolling over ruins. |

## Squadron (The Mission Count): Escape

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `escape` | C11 Endless Missions (loops) | Culture Shock, Machine | d2 | DC Breaks, Proton (d1); Metrik, T-2000 (d1) | Machine: relentless, cyclical, industrial. |
| `escape.c12` | C12 Escape North | Black Sun Empire, Extraction | d2 | Freestylers, Pendulum, SirReal, Painkiller - Noisia Remix (d1); Teddy Killerz, Night Train (d1) | Extraction: a chase, the hardest of the path. |
| `escape.c13` | C13 Neutral Coast (ending: free) | Metal Work, Freedom | d1 | Mantra, Decibella & Tim Reaper, Stars Are Calling (d1); Madface, Dawning (d2) | Freedom: wide dynamics and a release. |
| `escape.c14` | C14 Captured (loops) | Exile, Destructive Vibrations | d2 | Bou & Kasra, Trenchfoot (d1); Visages, Liber Primus (d1) | Destructive Vibrations from the second drop. Heavy and sour. |

## Ember (The Ember Road): Hollow

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `hollow` | E00 Orchard (one pass) | Mr Traumatik ft. Posk, Lotus | d1 | Mantra, Decibella & Tim Reaper, Stars Are Calling (d1); Paralel, In The Clouds (d2) | Lotus: bright, light, gentle start. |
| `hollow.ford` | E01 Ford at Night | DC Breaks, Gambino | d1 | K Motionz, Simula, Phantasm (d1); Ryme Tyme, Optiv & BTK, Ignition (d2) | Gambino: a gallop, riders on the bank. |
| `hollow.inn` | E02 Lantern Inn | Stimpy, Party Last Sounds | d2 | Su3-ject, Crystal Eyes (d1); Amplify & Crossy, Badman (d1) | Party Last Sounds: lamplight and a last song. |

## Ember (The Ember Road): North

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `north` | E03 Birch Hall | Bungle, Cocooned | d2 | RAM Trilogy, Evolution (Marcus Intalex & ST Files Remix) (d1); Northern Zone, Faint (d1) | Cocooned from its second drop. Hall of birch wind. |
| `north.pass` | E04 High Pass | Annix, Kingdom | d2 | Mantra, Decibella & Tim Reaper, Stars Are Calling (d1); SMG, Sono (d1) | Kingdom: wide and cold, thin air. |

## Ember (The Ember Road): Deeps

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `deeps` | E05 Deep Halls | AC13, Shostakovich | d2 | K Motionz, Simula, Phantasm (d1); In:Most, Pulsar (Floodlight) (d1) | Shostakovich: cavernous, dark. Measured detail exists for it. |
| `deeps.falls` | E06 Falls | Nectax, Zephyr | d2 | Su3-ject, Crystal Eyes (d1); Paralel, In The Clouds (d1) | Zephyr: wind and water, a cascade. |

## Ember (The Ember Road): Marsh

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `marsh` | E07 Reed Marsh | SMG, Sono | d2 | K Motionz, Simula, Phantasm (d1); Warm Roller, Memory (Floodlight) (d1) | Sono: mist and low light. Four drops. |
| `marsh.wall` | E08 Black Wall | Origin Unknown, Valley of the Shadows (Chase & Status Remix) | d2 | Bou & Kasra, Trenchfoot (d1); AC13, Shostakovich (d1) | Valley of the Shadows again, dark and tall. |
| `marsh.stair` | E09 Stair of Bells | In:Most, Pulsar (Floodlight) | d2 | LSB, The Hurting (d1); Metal Work, Freedom (d1) | Pulsar: sparse, held breath, huge dynamics. |
| `marsh.plain` | E10 Ash Plain | DJ Fresh, Tombraider | d1 | Hamilton, Soundboy VIP (d1); Break, Overstayed (d2) | Tombraider: a long march over open ground. |

## Ember (The Ember Road): Mountain

| Scene | What it is | Track | Entry | Alternates | Why |
|---|---|---|---|---|---|
| `mountain` | E11 Throat | PARTICLE, Pyro | d2 | Ryme Tyme, Optiv & BTK, Ignition (d1); Culture Shock, Machine (d1) | Pyro, second drop. Red walls pulsing. |
| `mountain.spring` | E12 Drowned Spring (ending: quenched) | Madface, Dawning | d2 | Metal Work, Freedom (d1); InsideInfo, Victory Over Death (Feat. MoniKali) (d1) | Dawning: light on black water. |
| `mountain.keeper` | E13 Keeper (ending: kept) | Simula, Lazy Horn | d2 | Exile, Destructive Vibrations (d1); Visages, Liber Primus (d1) | Lazy Horn, second drop: the seductive bass of the Ember. |
| `mountain.taken` | E14 Taken | Ryme Tyme, Optiv & BTK, Ignition | d1 | Teddy Killerz, Night Train (d1); Black Sun Empire, Extraction (d2) | Ignition: pursuit, riders. Heavy and driving. |

## Every track

Order: by first-choice use. "Entries" lists the entry points it is used with; "(alt)" means as an alternate.

| Track | First choice | Alternate | Entries |
|---|---|---|---|
| Paralel, In The Clouds (`paralel_in_the_clouds`) | 2 | 5 | d1, d1(alt), d2, d2(alt) |
| SMG, Sono (`smg_sono_original_mix`) | 2 | 5 | d1, d1(alt), d2, d2(alt) |
| Visages, Liber Primus (`visages_liber_primus`) | 2 | 5 | d1, d1(alt), d2, d2(alt) |
| AC13, Shostakovich (`ac13_shostakovich`) | 2 | 4 | d1, d1(alt), d2, d2(alt) |
| Black Sun Empire, Extraction (`black_sun_empire_extraction`) | 2 | 4 | d1, d1(alt), d2, d2(alt) |
| Exile, Destructive Vibrations (`exile_destructive_vibrations`) | 2 | 4 | d1, d1(alt), d2, d2(alt) |
| Warm Roller, Memory (Floodlight) (`floodlight_dnb_aid_for_pakistan_warm_roller_memory`) | 2 | 4 | d1, d1(alt), d2, d2(alt) |
| LSB, The Hurting (`lsb_the_hurting`) | 2 | 4 | d1, d1(alt), d2, d2(alt) |
| Madface, Dawning (`madface_dawning`) | 2 | 4 | d1, d1(alt), d2, d2(alt) |
| Northern Zone, Faint (`northern_zone_faint`) | 2 | 4 | d1, d1(alt), d2, d2(alt) |
| Annix, Kingdom (`annix_kingdom`) | 2 | 3 | d1, d1(alt), d2, d2(alt) |
| Bad Company UK & Trace, Nitrous (Audio Remix) (`bad_company_uk_trace_nitrous_audio_remix`) | 2 | 3 | d1, d2, d2(alt) |
| Bungle, Cocooned (`bungle_cocooned`) | 2 | 3 | d1, d1(alt), d2 |
| Culture Shock, Machine (`culture_shock_machine`) | 2 | 3 | d1, d1(alt), d2, d2(alt) |
| Nectax, Zephyr (`nectax_zephyr`) | 2 | 3 | d1, d1(alt), d2, d2(alt) |
| Origin Unknown, Valley of the Shadows (Chase & Status Remix) (`origin_unknown_valley_of_the_shadows_chase_status_remix`) | 2 | 3 | d1, d1(alt), d2, d2(alt) |
| Su3-ject, Crystal Eyes (`su3_ject_crystal_eyes`) | 2 | 3 | d1, d1(alt), d2 |
| Stimpy, Party Last Sounds (`stimpy_party_last_sounds`) | 2 | 2 | d1, d2, d2(alt) |
| Fresh, The Gatekeeper (`fresh_the_gatekeeper_original_mix`) | 2 | 1 | d1, d1(alt), d2 |
| PARTICLE, Pyro (`particle_pyro`) | 2 | 0 | d1, d2 |
| Simula, Lazy Horn (`simula_lazy_horn`) | 2 | 0 | d1, d2 |
| Bou & Kasra, Trenchfoot (`bou_kasra_trenchfoot`) | 1 | 5 | d1, d1(alt), d2(alt) |
| In:Most, Pulsar (Floodlight) (`floodlight_dnb_aid_for_pakistan_in_most_pulsar`) | 1 | 5 | d1(alt), d2 |
| InsideInfo, Victory Over Death (Feat. MoniKali) (`insideinfo_victory_over_death_feat_monikali`) | 1 | 5 | d1, d1(alt), d2(alt) |
| K Motionz, Simula, Phantasm (`k_motionz_simula_phantasm_original_mix`) | 1 | 5 | d1, d1(alt) |
| Mantra, Decibella & Tim Reaper, Stars Are Calling (`mantra_decibella_tim_reaper_stars_are_calling`) | 1 | 5 | d1, d1(alt) |
| Metrik, T-2000 (`metrik_t_2000`) | 1 | 4 | d1, d1(alt), d2(alt) |
| RAM Trilogy, Evolution (Marcus Intalex & ST Files Remix) (`ram_trilogy_evolution_marcus_intalex_st_files_remix`) | 1 | 4 | d1, d1(alt), d2(alt) |
| Ryme Tyme, Optiv & BTK, Ignition (`ryme_tyme_optiv_btk_ignition_original_mix`) | 1 | 4 | d1, d1(alt), d2(alt) |
| Teddy Killerz, Night Train (`teddy_killerz_teddy_killerz_night_train_t3ggcfz1vs`) | 1 | 4 | d1, d1(alt) |
| Amplify & Crossy, Badman (`amplify_crossy_badman`) | 1 | 3 | d1, d1(alt), d2(alt) |
| Bennie & Jam Thieves, Madting (`bennie_jam_thieves_madting`) | 1 | 3 | d1, d1(alt) |
| Break, Overstayed (`break_overstayed`) | 1 | 3 | d1, d1(alt), d2(alt) |
| DC Breaks, Proton (`dc_breaks_proton_original_mix`) | 1 | 3 | d1, d1(alt), d2(alt) |
| DC Breaks, Take That VIP (`dc_breaks_take_that_vip`) | 1 | 3 | d1, d1(alt) |
| Drumsound & Bassline Smith, Vigilante (`drumsound_bassline_smith_vigilante`) | 1 | 3 | d1, d1(alt) |
| Frankee, Flim Flam (`frankee_frankee_flim_flam_oggt1uhj5bs`) | 1 | 3 | d1, d2(alt) |
| Freestylers, Pendulum, SirReal, Painkiller - Noisia Remix (`freestylers_pendulum_sirreal_painkiller_noisia_remix`) | 1 | 3 | d1, d1(alt) |
| Mr Traumatik ft. Posk, Lotus (`mr_traumatik_ft_posk_lotus`) | 1 | 3 | d1, d1(alt) |
| Sub Focus, Rock It (`sub_focus_rock_it`) | 1 | 3 | d1, d1(alt), d2(alt) |
| A.M.C, Noise Of Thunder (`a_m_c_noise_of_thunder_original_mix`) | 1 | 2 | d1, d2(alt) |
| Chase & Status, No Problem (`chase_status_no_problem_original_mix`) | 1 | 2 | d1, d1(alt), d2(alt) |
| DC Breaks, Gambino (`dc_breaks_gambino_original_mix`) | 1 | 2 | d1, d1(alt), d2(alt) |
| DC Breaks, Slugs (`dc_breaks_slugs_original_mix`) | 1 | 2 | d1, d1(alt) |
| Hamilton, Soundboy VIP (`hamilton_soundboy_vip`) | 1 | 2 | d1, d1(alt), d2(alt) |
| Mampi Swift, Soldiers (`mampi_swift_soldiers_gyrhlx7pafa`) | 1 | 2 | d1, d1(alt) |
| Metal Work, Freedom (`metal_work_freedom`) | 1 | 2 | d1, d1(alt) |
| Metrik, Hackers (`metrik_metrik_hackers_chn2k5wwufc`) | 1 | 2 | d1, d2(alt) |
| Moving Fusion, Makosa (`moving_fusion_makosa`) | 1 | 2 | d1, d2(alt) |
| Trex, Chit Chat (`trex_chit_chat`) | 1 | 2 | d1, d1(alt) |
| DJ Fresh, Tombraider (`dj_fresh_tombraider_hq_6pfchcwomjg`) | 1 | 1 | d1, d1(alt) |
| Radiax, Headway (Floodlight) (`floodlight_dnb_aid_for_pakistan_radiax_headway`) | 1 | 1 | d1, d1(alt) |
| Loadstar, Dr.Karg (`loadstar_dr_karg_original_mix`) | 1 | 1 | d1, d1(alt) |
| Original Sin, Therapy (Remix) (`original_sin_therapy_remix`) | 1 | 1 | d1, d2(alt) |
| Sub Focus, X-Ray (Metrik Remix) (`sub_focus_x_ray_metrik_remix`) | 1 | 1 | d1, d2(alt) |
| Unglued, Telefonik (`unglued_telefonik`) | 1 | 1 | d1, d1(alt) |
| Acuna, Go Back (`acuna_go_back`) | 1 | 0 | d1 |
| Fatboy Slim, Right Here, Right Now (One In The Jungle Remix) (`fatboy_slim_fatboy_slim_right_here_right_now_one_in_the_jungle_remix_osrqel13kmo`) | 1 | 0 | d1 |
| Need For Mirrors, Zero T, Top Shelf (feat. Spikey Tee) (`need_for_mirrors_zero_t_top_shelf_feat_spikey_tee`) | 1 | 0 | d1 |
| Nu Elementz, Trenches (`nu_elementz_trenches`) | 1 | 0 | d1 |
| Ternion Sound, Artifice (`ternion_sound_artifice`) | 1 | 0 | d1 |

## Choices I am least sure of

1. **Soldiers in the Briefing Room (`base`).** The measurement says its first drop is at 0 s. If the pack has no clear drop section the entry may fall back to the loudest section. Check by ear.
2. **Quiet Room (`hospital_late.quiet`) with The Hurting.** I wanted a contrast in the late Hospital, but the track is long, busy and heavy once it starts. A softer track would suit the name better.
3. **Golgotha with Liber Primus from `drop2`.** It is a one-pass scene and `drop2` enters late in the song. The track is also the Throne's first choice. They are far apart, but the same darkness twice in a run may be noticed.
4. **Stars Are Calling (168 BPM) at Bethlehem, and Artifice (140 BPM) at the Squadron Hospital.** The tempo changes are the point, but they are the only two. If the pace change feels wrong at the portal hand-off, swap them for 174 tracks.
5. **The tracks I did not recognise.** Frankee, Trex, Nu Elementz, Su3-ject, Bennie & Jam Thieves, Nectax, Mr Traumatik, Particle, Metal Work, Stimpy, Mantra and Northern Zone are placed mainly by the numbers and, in a few cases, by the title. Any of them may be in the wrong world.

Also worth a listen: Chit Chat in the Ward Day Room (a talk theme for the card-table room, a guess from the title) and Party Last Sounds in the Chill-out and the Lantern Inn (used in two very different places, `drop1` and `drop2`).
