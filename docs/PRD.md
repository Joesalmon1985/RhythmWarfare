# Rhythm Warfare — MVP Product Requirements

Version 0.1 · 27 October 2026 · Working title

**Product owner:** Joe Salmon  
**Purpose:** Define a small, playable mobile rhythm game using the OpenRA assets and relevant work from DuelMasterBattle. This is a product and implementation brief, not an assertion that the new game already exists.

## 1. Product vision

Play a drum and bass track to command an army. Accurate kick notes produce tanks, snare notes produce infantry, and bass notes build and launch a small air force. Units fight automatically on a battlefield that fits on one screen. When the enemy destroys a production building, its instrument disappears from the music. Rebuilding an airfield can bring the bass back.

The core experience is pure rhythm: listen, read the approaching notes and tap or hold the correct button. Battle outcomes follow from rhythm performance and an authored enemy production schedule. There are no tactical orders or construction menus during a song.

## 2. Scope and decision status

### Agreed requirements

| Area | Requirement |
| --- | --- |
| Platform | Mobile game, using the existing project as a source of reusable work. |
| Music | Four supplied stems: kicks, snares, bass and other. Primary style is 174 BPM drum and bass in 4/4, organised into 4-, 8-, 16- and 32-bar phrases. |
| Controls | Three buttons: kick tap, snare tap, and bass tap or hold. |
| Kick reward | One successful kick note produces one tank while the war factory survives. |
| Snare reward | One successful snare note produces five infantry while the barracks survives. |
| Bass | At most five air buildings per faction; aircraft have finite ammunition and require successful bass inputs to take off again. |
| Starting forces | Each side has a main base, barracks, war factory, walls and turrets. Power buildings form part of the base layout. |
| Combat | Fully automatic. The computer's production follows a preset pattern for the song. |
| Battlefield | Simple, fixed camera showing both bases and the middle. Reinforcements travel for a few seconds before fighting. |
| Destruction | Destroying a producer stops its production and mutes the corresponding human music stem. Only air buildings can be rebuilt. |
| Repair | Damaged structures use OpenRA building-repair rules; repair and rebuilding are separate operations. |
| Layout | Air buildings occupy protected positions at the back of each base. |
| Victory | Destroy the enemy main base and end the song immediately. |

### Proposed defaults used to make this draft implementable

These fill gaps in the conversation and remain adjustable; they are not additional owner decisions.

| Topic | Draft default |
| --- | --- |
| First release | Offline Android build, with a desktop build for authoring and testing. |
| Screen | Landscape, battlefield above three note lanes and buttons. |
| Initial air force | Zero air buildings. Successful bass notes establish the five reserved slots. Bass is audible at level start. |
| Aircraft capacity | One resident aircraft per slot: at most five live aircraft per faction, including aircraft whose home pad is temporarily destroyed. |
| Bass reward | One successful bass note services one slot and launches one eligible aircraft, rather than launching every aircraft. |
| Hold reward | One bass action on successful hold completion; no repeating rewards while held. |
| Repair | Automatically activate repair on surviving structures with the OpenRA repair trait, funded by an equal preset credit allowance for each side. |
| Loss | Player main base destroyed, or the song ends before the enemy main base is destroyed. Mutual destruction in the same simulation step counts as a loss. |

MVP content is one level, one supplied song, one battlefield, one mirrored roster and one authored enemy schedule. Unit preferences before a song are deferred. Multiplayer, eras, civilian economies, resources for production, drafting, heroes, camera controls and procedural beat detection are outside this version.

## 3. Player flow and presentation

1. Open the game and select the single available level.
2. Read a compact explanation of the three buttons; adjust timing calibration if needed.
3. Receive a short countdown, then start all four stems together.
4. Play the note chart while watching reinforcements march into an automatic battle.
5. See and hear the consequences of production-building damage and destruction.
6. Reach a result screen with victory/loss, accuracy, misses, best combo and battle duration; retry resets everything.

The battlefield occupies roughly the upper two-thirds of the screen. Three readable note lanes lead to large touch buttons below it. Show main-base health for both sides, production availability, and aircraft readiness/ammunition without requiring taps on buildings. Use labels and distinct shapes as well as colours. Keep effects away from the timing line.

Support independent touch identifiers so a bass hold can coexist with a kick or snare tap. The first chart must be playable with two thumbs: avoid mandatory three-button chords and same-lane overlapping holds. Desktop keys are a testing convenience, with the same judgement rules as touch.

## 4. Rhythm and production

### Judgement

Each chart event has a unique ID and resolves once. A tap matches the nearest eligible unjudged note in that lane; use a stable tie-break rule. One press cannot satisfy two notes. Keyboard repeat, a continuously held finger and extra taps cannot produce additional units.

Starting tuning values are Perfect within ±45 ms and Good within ±100 ms. Both give the full stated military reward. A missed note produces nothing and breaks the combo; there is no direct health penalty. An unmatched extra press gives no reward and breaks the combo. Natural silence is never a miss: the JSON chart is the authority on required inputs.

For a bass hold, the initial press must meet the start window and remain down until the tail, allowing a proposed 60 ms early-release tolerance. Resolve the military reward at the scheduled tail. An early release beyond tolerance fails the hold and grants no aircraft or building. Holding longer does not create more rewards. Show progress during the hold without granting an operational building early.

Provide immediate note feedback on the next rendered frame. Tank and infantry creation occurs immediately after judgement; it is not accumulated until a phrase boundary. Phrases organise chart difficulty and enemy waves, not the basic reward rate. If an exit is occupied, retain the exact awarded units in a short physical spawn queue; never silently discard them or charge for them.

### Producer gates

| Producer state | Production | Music and chart |
| --- | --- | --- |
| War factory alive | Successful kick creates one tank. | Kick stem and lane available. |
| War factory destroyed | No further tanks; no factory rebuilding. Existing tanks continue fighting. | Kick muted; future kick notes marked unavailable and excluded from misses/accuracy. |
| Barracks alive | Successful snare creates five infantry. | Snare stem and lane available. |
| Barracks destroyed | No further infantry; no barracks rebuilding. Existing infantry continue fighting. | Snare muted; future snare notes marked unavailable and excluded from misses/accuracy. |
| Air building damaged but alive | Remains usable unless its selected actor rules state otherwise; repairs do not require a bass hit. | Bass remains audible. |
| Last air building destroyed | Aircraft cannot rearm there, but successful bass inputs can rebuild. | Bass muted; bass notes remain visible and playable. |
| Air building rebuilt and operational | Aircraft operations resume. | Restore bass at the current song position. |

Disable unavailable ground-lane notes rather than manufacture unavoidable misses. Do not erase accuracy already earned before destruction. A bass hold remains eligible when all pads are gone because rebuilding is its recovery function.

## 5. Airfields and aircraft

Reserve five fixed, non-overlapping slots behind each base. For the MVP, use one compatible OpenRA helicopter/helipad pair to avoid mixing runway and helicopter landing behaviour. A candidate is HELI with HPAD, subject to confirming the existing sprite set. Use its resolved finite ammo pool, weapon burst behaviour and rearming parameters.

Every successful bass action follows this deterministic priority:

1. If a slot has never been built or its building was destroyed, construct that slot's air building. Prefer destroyed previously used slots, then unused slots. Create its aircraft if that slot has no surviving aircraft; otherwise reconnect the existing aircraft. Launch that aircraft if it is ready.
2. Otherwise, if an intact slot has lost its aircraft, create one replacement there and launch it.
3. Otherwise, launch one landed, fully rearmed aircraft. Choose the longest-waiting ready aircraft, breaking ties by slot index.
4. If all five aircraft are flying, returning or rearming, record the successful note and combo, but do not clone aircraft or bank unlimited future sorties. Show “Air wing busy” as brief feedback.

Slots, airborne aircraft and pending replacements count consistently towards the capacity rules. Rebuilding a pad cannot duplicate an aircraft still alive in the air. A destroyed pad frees a building slot, not an entitlement to exceed the aircraft limit.

An aircraft automatically seeks targets, spends ammunition, returns when empty, lands and rearms. Once ready, it waits for a later successful bass action; completing rearm alone must not trigger takeoff. A missed bass note leaves ready aircraft grounded. Aircraft do not fire without ammunition.

If a pad is destroyed with its aircraft parked on it, destroy the parked aircraft. An airborne aircraft continues its current sortie and attempts to return to a compatible surviving pad; if none is usable, it waits visibly near its side until one is rebuilt. It remains vulnerable and cannot rearm in flight. Keep these transitions explicit: ready → sortie → returning → rearming → ready, with destroyed/orphaned states where required.

**Initial music exception:** bass begins audible even though its five slots are initially empty. After the faction has established air facilities, losing its last operational pad mutes bass. A successful bass action can rebuild the first pad and restore it. This avoids beginning the level with an inaudible bass tutorial.

## 6. Battlefield and opponent

Use a compact, mirrored battlefield with a broad central fighting area. Choose scale and movement speeds so new ground units take approximately 2–4 seconds to reach the initial contact area. This is a tuning target, not an artificial wait imposed on every unit.

Each side starts with a main base, one barracks, one war factory, power buildings and a small arrangement of walls and turrets. Include appropriate anti-air defence so aircraft can be shot down. Walls must have usable exits; production cannot be trapped behind its own defences. Put the five air slots deepest in the base and use sensible automatic target priorities so frontline threats and forward buildings are normally engaged first.

Units automatically attack enemy units and defences, then advance through production and support structures towards the main base. Respect weapon target filters and armour rules. Aircraft ignore ground-path obstructions. Combat continues between notes; attacks do not wait for musical beats.

The enemy has no adaptive production AI. Its timestamped song events call the same kick, snare and bass production actions as the player, subject to the same building, ammo and capacity restrictions. A scheduled tank event cannot bypass a destroyed war factory. Rebuilding enemy airfields requires scheduled bass events. Events blocked at their scheduled time are skipped, not delayed into an unexpected later wave.

Tune the schedule so consistently accurate play wins before the song ends, while sustained missed production allows the enemy to win. The opponent must not secretly increase output in response to good play. Do not introduce a hidden population cap that changes one tank or five infantry per successful note; optimise simulation and rendering around the authored worst-case army size.

## 7. Destruction, power and repair

At zero health, a building immediately stops operating. Destruction art may continue afterwards, but the building cannot produce, repair itself or accept aircraft. Existing armies remain active. Only air buildings can be reconstructed; the main base, barracks, factory, turrets, power buildings and walls are not resurrected.

Repair applies only while a structure is alive. Automatically start the ordinary OpenRA building-repair process when an eligible structure takes damage. Stop at maximum health, when the repair trait is disabled, when funds are unavailable, or when the building is destroyed. Repair must not make a destroyed barracks or factory return.

OpenRA's pinned `RepairableBuilding` implementation uses actor value, health restored, repair percentage, step timing and a minimum per-step credit charge. Resolve Red Alert actor inheritance: the RA building template overrides the trait's base repair step with 700; do not use the generic step of 7 against RA-scaled health. Preserve source counter behaviour and rounding. Actor-specific overrides win.

**MVP adaptation:** activation is automatic and each side receives the same level-configured repair credit budget. A starting proposal is 5,000 credits per side, reset on retry, with no replenishment or spending controls. Production itself remains free and rhythm-driven. This preserves repair costs without adding an economy for the player to manage. Repair coverage and budget are tunable defaults, not agreed numeric requirements.

Use the selected actor's power and turret conditions where supported. For the MVP, low power may affect source-defined defences, but must not introduce an additional hidden rhythm-production gate or mute music: the lane-loss trigger is destruction of its producer. Record any power adaptation in the actor configuration.

## 8. Four-stem music behaviour

| Stem | Contents | Audible while |
| --- | --- | --- |
| Kick | Kicks only | Human war factory survives. |
| Snare | Snares only | Human barracks survives. |
| Bass | Bass only | Initial construction state, or at least one human air building is operational. |
| Other | Remaining musical material | Battle is active, irrespective of production losses. |

Only the human faction's buildings control the player's music mix. Destroying an enemy producer changes enemy production but does not remove a human stem. Missed notes alone do not mute stems.

All four stems share one start, transport, pause state and playhead. Muting changes gain; it never stops or restarts a stem. Use a short gain ramp, proposed 30 ms, to avoid clicks while making destruction audible promptly. Rebuilding restores the bass already playing silently at the current position. Existing aircraft do not keep the bass audible after the last pad is lost.

Use Godot 4.5's `AudioStreamSynchronized` as the initial implementation candidate, with independent substream gain. Follow the official audio-clock guidance for judgement timing: compensate for mixing/output latency, account for calibration and avoid accumulating frame-delta time as the song clock. Cache output latency and prevent reported song time moving backwards because of audio-thread jitter. Validate behaviour on the target device rather than assuming the API alone proves synchronisation.

Keep authored chart offset and user/device timing calibration separate. Define and document their signs. Pause freezes music, notes, enemy events, combat and repair together. On resume, use a visual countdown and re-anchor timing; restart an interrupted active hold with no free reward or penalty. App backgrounding pauses the battle. Full retry resets all stems, judgements, units, health, credits and queued events.

On victory or defeat, stop combat and note processing immediately, fade out all stems briefly, and show the result. Do not wait for the end of a phrase or track. If the track reaches its defined end without a destroyed enemy main base, end as an incomplete-objective loss; no automatic looping.

## 9. Song-pack contract

The owner supplies four aligned audio stems and one JSON level definition. MP3 is accepted; WAV or Ogg may also be used. Export every stem from the same Ableton timeline start, at the same sample rate, with equal musical duration and leading silence preserved. Keep the “other” stem free of duplicate kicks, snares or bass that would undermine muting.

Validate decoded alignment, especially MP3 encoder padding/delay. If preparation converts audio, use consistent conversion settings and retain the aligned source exports. Do not trim each stem independently. The game does not need to infer beats from audio or MIDI in this MVP.

Use integer ticks for authored timing: 960 ticks per quarter-note beat, four beats per bar, with bar 1 starting at tick 0. At 174 BPM a bar lasts approximately 1.37931 seconds. Resolve each event directly from its absolute tick position:

`event_seconds = song_offset_ms / 1000 + tick * 60 / (bpm * ticks_per_beat)`

The input below illustrates the proposed contract. Notes and enemy events are abbreviated examples, not a complete playable chart or a balanced schedule. Paths are relative to the song-pack root.

```json
{
  "schema_version": 1,
  "level_id": "mvp_01",
  "title": "First Contact",
  "bpm": 174,
  "time_signature": [4, 4],
  "ticks_per_beat": 960,
  "song_offset_ms": 0,
  "duration_ticks": 245760,
  "seed": 27,
  "stems": {
    "kick": "audio/01_Kicks.mp3",
    "snare": "audio/02_Snares.mp3",
    "bass": "audio/03_Bass.mp3",
    "other": "audio/04_Other.mp3"
  },
  "battlefield": "mvp_mirrored_01",
  "roster": "openra_mvp_01",
  "rules": {
    "airfield_limit": 5,
    "aircraft_limit": 5,
    "initial_airfields": 0,
    "tank_per_kick": 1,
    "infantry_per_snare": 5,
    "repair_budget_credits_per_side": 5000,
    "song_end_result": "defeat"
  },
  "sections": [
    {"id": "intro", "start_tick": 0, "length_bars": 16},
    {"id": "drop_1", "start_tick": 61440, "length_bars": 32},
    {"id": "finale", "start_tick": 184320, "length_bars": 16}
  ],
  "notes": [
    {"id": "n001", "tick": 0, "lane": "kick", "type": "tap"},
    {"id": "n002", "tick": 960, "lane": "snare", "type": "tap"},
    {"id": "n003", "tick": 1920, "lane": "bass", "type": "hold", "duration_ticks": 1920},
    {"id": "n004", "tick": 2400, "lane": "kick", "type": "tap"},
    {"id": "n005", "tick": 2880, "lane": "snare", "type": "tap"},
    {"id": "n006", "tick": 3840, "lane": "bass", "type": "tap"}
  ],
  "enemy_events": [
    {"id": "e001", "tick": 0, "action": "kick"},
    {"id": "e002", "tick": 960, "action": "snare"},
    {"id": "e003", "tick": 1920, "action": "bass"}
  ]
}
```

The example is 64 bars, approximately 88.28 seconds. Song length is configurable; the actual supplied track need not be 64 bars.

The importer must check version, required stems, resolved file paths, audio duration/alignment, unique IDs, supported lane/action names, valid non-negative ticks, positive bass-hold duration, hold endpoints within the song, section coverage, same-lane conflicts and enemy event ordering. Reject path escapes from the song-pack root. Flag unavoidable three-touch chords for author review. No event may lie beyond the song's playable end.

For equal timestamps, process input judgement/eligible production against the building state at the start of the simulation step, then scheduled enemy events, combat damage, destruction/gain changes and outcome resolution. Use stable event/entity ordering. Once an outcome is resolved, process no later events.

## 10. Reuse and technical direction

Reference repository: [DuelMasterBattle](https://github.com/Joesalmon1985/DuelMasterBattle). Inspected `main` documentation and the `feature/god-world` source branch. Several project status documents identify themselves as historical; executable source is the stronger basis for reuse decisions.

| Existing work | Proposed reuse | Qualification |
| --- | --- | --- |
| `godot_project/client/hybrid/hybrid_art.gd` and imported art catalogue | Sprite lookup, facing, body/turret layers, animation and health presentation. | Reuse the relevant OpenRA subset; the renderer also contains unrelated world/industry code. |
| `WizardRTSHybrid/wizard_rts/military.py` | Combat/targeting behaviour, imported weapon values and damage conventions as reference. | Python simulation, not the OpenRA engine; movement is an adaptation. |
| `WizardRTSHybrid/wizard_rts/openra_abilities.py` | Finite ammo, ammo spending, return-to-pad and rearming concepts. | Existing rearm/repair uses old stock/iron mechanics. Adapt it and fix lifecycle gaps rather than carrying that economy into the rhythm game. |
| `WizardRTSHybrid/sources/manifest.json` | Pin the upstream rules reference and preserve provenance. | Current documented OpenRA pin is `e7e9e4ad270221d7fb9725b348c75504d48c1ebd`. |
| Existing Godot project and mobile work | Project structure, asset imports and export configuration where suitable. | A mobile build must prove this new mode works independently. |

Implement a separate rhythm-game scene and entry point in the existing project, preserving current modes. The mobile MVP should run locally inside the Godot application, without a desktop Python server or network connection. Port the small required combat/aircraft slice if needed; shared rules and parity fixtures should prevent accidental changes in damage, ammo and repair behaviour. Do not attempt to port the entire existing world simulation or embed the complete OpenRA engine for this slice.

Separate responsibilities into song transport, chart scheduling, input judgement, rhythm production, battle simulation, building/aircraft lifecycle and presentation. The battle emits building-loss/restoration events; the audio layer translates those events into gain changes. Render stalls must not change the musical schedule or skip awards.

Prefer the existing tank, infantry, barracks, factory and turret art. Verify or import the required aircraft, pad, power, wall and main-base sprites with the project's current extraction workflow. Preserve the existing asset provenance. Imported art or rules alone do not count as a completed playable feature.

## 11. Delivery milestones

| Milestone | Demonstrable result |
| --- | --- |
| M0 — Music and input | Four aligned stems, one clock, three working touch lanes, tap/hold judgement, calibration and pause. Manual debug toggles prove muting and restoration without restart. |
| M1 — Ground battle | Mirrored fixed battlefield; each kick makes one tank and each snare five infantry; preset enemy events; autonomous combat and main-base outcomes. |
| M2 — Air and damage | Five-slot airfields, finite ammo, automatic return/rearm, bass-controlled sorties, pad replacement and producer destruction linked to stem gain. |
| M3 — Complete mobile level | Automatic repair, real supplied song pack, readable effects/results, offline Android build, repeatable balance runs and device performance evidence. |

MVP is complete only when the supplied song is playable end to end on a phone and every agreed mechanic above is exercised. Do not substitute a desktop-only simulation or a non-interactive battle video.

## 12. Acceptance and verification

| ID | Required evidence |
| --- | --- |
| A01 | With all producers intact, a deterministic sequence of ten successful kick and ten successful snare notes awards exactly ten tanks and fifty infantry. Misses and stray taps award zero. |
| A02 | Perfect and Good windows behave at their boundaries; chords, repeated keys and multiple fingers cannot duplicate rewards. A hold grants one action only on completion; an early release grants none. |
| A03 | Destroying the factory or barracks immediately blocks its production and mutes only the matching stem. Existing units continue. Future unavailable-lane notes cannot inflate misses. |
| A04 | Destroying the last air building mutes bass while preserving visible bass prompts. A successful muted bass note rebuilds an eligible pad, restores the correct current musical position and obeys capacity limits. |
| A05 | Repeated bass actions never exceed five buildings or five resident live aircraft per faction. Test pad destruction during flight, lost aircraft, busy aircraft and simultaneous rebuilding/rearming. |
| A06 | Aircraft fire only with ammo, return when empty, rearm at a valid pad and remain grounded until a subsequent successful bass action. Rebuilding a pad cannot duplicate a surviving aircraft. |
| A07 | Repair matches resolved OpenRA step, cadence and rounded cost fixtures, never exceeds maximum HP and stops when funds run out. Destroyed structures cannot repair themselves back into existence. |
| A08 | Enemy events repeat the authored schedule at the same timestamps for the same level seed and input trace. Dead producers and the airfield cap constrain enemy events too. |
| A09 | Repeated stem mute/unmute cycles do not shift relative audio alignment. Target no cumulative chart drift exceeding 10 ms over the test track after calibration; record the measurement method and device. |
| A10 | Pause, background/resume and retry preserve or reset every relevant clock and lifecycle consistently. No duplicate enemy waves, hold rewards or units appear. |
| A11 | Enemy main-base destruction ends battle and song immediately. Player destruction, mutual destruction and track-end without victory resolve according to the documented loss rules. |
| A12 | Scripted perfect-input play wins before the track ends. Sustained misses produce a loss. Record winning/losing traces and timings; balance by the authored schedule and declared parameters. |
| A13 | On the chosen phone, target 60 FPS and require a 95th-percentile frame time below 33 ms during a perfect-input worst-case run, with uninterrupted music. Report peak live-unit count and memory; do not suppress awarded units to pass. |
| A14 | Android installation launches and completes the level offline. The fixed view shows both bases, the central fight and readable rhythm controls throughout. |

No implementation tests were run while authoring this PRD. These are delivery requirements. The illustrative JSON and its timing arithmetic can be checked independently of the future game.

## 13. Source references

- [Hybrid README](https://github.com/Joesalmon1985/DuelMasterBattle/blob/main/WizardRTSHybrid/README.md), [source reuse notes](https://github.com/Joesalmon1985/DuelMasterBattle/blob/main/WizardRTSHybrid/docs/SOURCE_REUSE.md) and [upstream manifest](https://github.com/Joesalmon1985/DuelMasterBattle/blob/main/WizardRTSHybrid/sources/manifest.json): project reuse context and source pins.
- [Current military source](https://github.com/Joesalmon1985/DuelMasterBattle/blob/feature/god-world/WizardRTSHybrid/wizard_rts/military.py), [aircraft/ability source](https://github.com/Joesalmon1985/DuelMasterBattle/blob/feature/god-world/WizardRTSHybrid/wizard_rts/openra_abilities.py) and [Godot art renderer](https://github.com/Joesalmon1985/DuelMasterBattle/blob/feature/god-world/godot_project/client/hybrid/hybrid_art.gd): inspected implementation, including finite aircraft ammo and existing stock-based rearming.
- [Pinned OpenRA building-repair implementation](https://github.com/OpenRA/OpenRA/blob/e7e9e4ad270221d7fb9725b348c75504d48c1ebd/OpenRA.Mods.Common/Traits/Buildings/RepairableBuilding.cs), [Red Alert defaults](https://github.com/OpenRA/OpenRA/blob/e7e9e4ad270221d7fb9725b348c75504d48c1ebd/mods/ra/rules/defaults.yaml) and [aircraft rules](https://github.com/OpenRA/OpenRA/blob/e7e9e4ad270221d7fb9725b348c75504d48c1ebd/mods/ra/rules/aircraft.yaml): source behaviour and actor overrides.
- [Godot 4.5 synchronised streams](https://docs.godotengine.org/en/4.5/classes/class_audiostreamsynchronized.html) and [audio/gameplay synchronisation guidance](https://docs.godotengine.org/en/4.5/tutorials/audio/sync_with_audio.html): audio implementation references. The latter page marks itself as not yet updated for 4.5, so device validation remains necessary.

Product rules come from this design conversation. Items explicitly marked as draft defaults require playtesting or owner refinement, not additional engine research.

## 14. Defense campaign, schema 2 (superseded by section 15)

Section 14 described the per-note production build of 29 to 30 October 2026 (instrument recipes, round-robin groups,
2/2/3 loadout caps, a falling-note lane on four unlabelled buttons). The owner's brief of 31 October 2026
(`docs/BRIEF_PADS_SEQUENCES_TEN_MISSIONS.md`) retired that model; section 15 is the only campaign rule set. The schema 2
packs and their loader were removed; their source MIDI under `campaign/First_Three/` is the default content of missions
1 to 3.

## 15. Missions (schema 3): four pads, sequences, rewards

Written 31 October 2026 from `docs/BRIEF_PADS_SEQUENCES_TEN_MISSIONS.md` (Part A wins over Part B). Schema 1 packs keep the
duel rules of sections 1 to 13 as the legacy free-play mode. The numbers live in `data/campaign/rules.json`, which the
game (`MissionRules`) and the content build (`tools/content`) both read.

### The game

- One-sided defense, centred base, three approaches (left, top, right), enemy entries outside the visible window, no
  enemy base. Waves are authored by song time and never depend on the player's accuracy. Required objectives
  (`command_core`, plus `power_plant` or `radar_dome` where a mission says so) must survive to `duration_ticks`; losing
  one is an immediate defeat, reaching the deadline is a victory. A miss never damages anything directly.
- The player selects a mission by name, makes the few musical choices it asks for (or none), and plays four illuminated
  pads while the battle runs. Missions author the song: phase order, length, which choices play where, fills, which
  family is followed, rewards and waves. Nothing on the menus reveals that structure.

### Pads

- Four pads, stable positions: 1 and 2 under the left thumb, 3 and 4 under the right. At most two touches at a time,
  and two simultaneous requirements are always on different thumbs.
- Each phase follows one family. Drum phases: kick sound slot 1 is pad 1, slot 2 pad 2; snare slot 1 pad 4, slot 2 pad
  3. Bass phases: bass voice slot 1 pad 2, slot 2 pad 3, slot 3 pad 1, slot 4 pad 4. One pad per voice; pitches are
  never mapped to pads. A pad with no cue in the current phase is dim; its label is the friendly sound name.
- A cue's ring closes onto its pad over the cue lead-in (a setting, 0.4 to 1.2 s, default 0.7 s; it replaces the old
  note-approach setting) and the pad pulses at the onset. A hold stays lit and fills until its tail, then flashes. All of
  it is drawn from the one song clock (countdown, pause and calibration included). A short in-play banner announces the
  incoming family one bar before a mode change; there is no roadmap.
- Desktop keys D F J K are pads 1 to 4.

### Recognition, sequences and precision

- Windows (ms, either side of the onset): perfect 45, great 90, accept 140. A press takes the nearest unresolved cue of
  its pad inside the accept window; one press resolves at most one cue; a second finger on a held pad does nothing; a
  press with nothing in reach is a stray. Held keys and fingers never repeat.
- Holds: a hold starts like a tap. Released within 0.15 s of its tail (or still held there) it is complete (credit 1);
  released earlier its credit is the held fraction. An early release never fails anything. Pause ends an active hold
  where it stands.
- Sequences are authored per phase (`sequence_bars`, normally 4 bars at 174 BPM, i.e. 2 bars of the half-time feel).
  Boundaries never cut a hold (the build rejects it) and never span a mode change. A sequence resolves once, when its
  last cue is final, at the latest resolution time of its cues (never earlier, and independent of the frame rate).
- Success: the sum of cue credits / cue count >= the mission threshold (0.6 by default). Success earns the sequence's one
  reward; failure earns nothing and nothing already earned is lost.
- Precision (successes only): mean absolute onset error of the accepted cues + 25 ms x strays / cues. Sharp <= 35 ms:
  0.5 s construction delay; steady <= 70 ms: 1.5 s; loose: 3.0 s. Mashing passes at best as loose.
- Denser grooves never mean more rewards: the reward count is the sequence count, fixed by the arrangement for every
  compatible choice.

### Rewards and capacity

- A reward is one of: a building (`pillbox`, `turret`, `flame_tower`), one unit (`e1`, `e2`, `e3`, `e4`, `jeep`, `apc`,
  `1tnk`, `2tnk`, `arty`, `ftrk`) or a `repair`. The first drum-sequence reward of mission 1 is one pillbox.
- Buildings go to prepared sockets (`data/battlefields/defense_02.json`, five per approach flanking the route outside
  the wall; a mission opens `sockets_per_point` of them). The approach with the fewest defenses wins, ties go to the
  approach of the next wave. Units are produced by the barracks or war factory and hold the defense point with the
  fewest defenders (at most `units_per_point`, 6).
- At capacity the reward becomes a repair crew for its approach (every damaged defense to full); when nothing is
  damaged it reinforces the oldest defense once (+50 % health). The HUD names what happened; nothing is discarded
  silently.
- The placement is chosen when the sequence resolves and shown on the battlefield (socket outline, countdown ring)
  during the construction delay; the building or unit appears when it ends. Construction, delays, waves and grading all
  run on song / simulation time and pause together.
- Wave units attack-move via their approach's defense point to their objective and fight units and defensive structures
  on the way (not other buildings); defenses block or are destroyed, so no stalemate is possible.

### Content: library, missions, build

- Loop library (`content/library/<clip_id>/`): mission-independent clips at 174 BPM 4/4 with stable ids. Kinds: `groove`
  (kick and snare parts), `fill` (kick and snare), `bass`, `accompaniment` (part `other`). One MIDI per part
  (`kick.mid`, ...); one WAV per part and sound (`kick__kick_march.wav`); several sounds share a clip's MIDI. Sounds live
  in `content/sounds.json`.
- Missions (`content/missions/level_NN.json`): choices (`groove`, `fill`, `bass`, `kick_sound`, `snare_sound`,
  `bass_voice`, each with a pool, a count and a default), phases (bars, mode, the clip and sound of each family as a
  choice slot or a fixed id, `sequence_bars`, rewards), accompaniment placements, battle (battlefield, waves file, rules).
- `python tools/content/build.py` validates everything and writes `songs/<pack>/level.json` (schema 3), full-length
  per-slot stems for every offered clip and sound combination of every usage (`audio/sNN__<clip>__<sound>.ogg`) and
  short auditions (`preview/<choice>__<option>.ogg`). The transport plays the selected stems unchanged; there is no
  runtime clip engine.

### Schema 3 pack (`level.json`, written by the build; never hand-edited)

```
schema_version 3, mode "defense", level_id, campaign_level, title, bpm 174, time_signature [4,4], ticks_per_beat 960,
song_offset_ms 0, duration_ticks, seed, battlefield, roster, rules, sequence_threshold, intro, placeholder,
choices    [{id, label, count, default [...], pool [{id, name}]}]
names      {library id: friendly name}
phases     [{id, start_tick, end_tick, mode, pads {"1": {family, ref}}}]
stems      [{key, family, deps ["groove#1", "kick_sound#1"], files {"<opt>|<opt>": {file, placeholder, clip, sound, peak_db}}}]
cue_blocks [{phase, family, pad, voice, deps, start_tick, end_tick, options {"<clip id>": [[tick, hold_ticks], ...]}}]
sequences  [{index, phase, mode, start_tick, end_tick, reward}]
previews   {choice: {option: file}}
content    {files, placeholder_files, owner_files, default_mix_peak_db}
waves      [{id, start_tick, entry, via_defense_point, target_objective, groups [{actor, count, spawn_spacing_ticks}]}]
```

A selection `{choice: [options in slot order]}` picks one file per stem (`deps` resolved in order) and one cue list per
block. An invalid or stale selection falls back to the defaults.

### Acceptance

Cue and hold recognition; generous acceptance with precision setting only the delay; sequence pass/fail and exactly one
reward per pass; spam, duplicate and held-pad prevention; pause and retry determinism; continuity of stems across
phases; valid sockets and capacity behaviour; all ten missions load and complete; progression and unlocks; save
migration; content replacement through the build. Seeded trials (perfect, beginner, sloppy, none) in `docs/BALANCE.md`.
