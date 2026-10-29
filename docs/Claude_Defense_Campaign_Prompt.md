# Claude implementation prompt: Rhythm Warfare defense campaign

Implement the next version of my existing Godot project:
https://github.com/Joesalmon1985/RhythmWarfare

I am attaching `Rhythm_Warfare_Defense_Campaign.zip`. Read `Defense_Campaign_Design_and_Workflow.md`, then the proposed data in `Plan/`, then the first-three song authoring examples. Inspect the current repository, its AGENTS instructions and docs before editing. The pack was checked against commit `ed8207faa231c9dc5c315e6b9ecda6e4a235c75e`; adapt to newer work already present. Preserve uncommitted user changes. Use a new working branch for this implementation.

Read `Rhythm_Game_Research_and_Refinements.md` and `Plan/chart_design_refinement.proposed.json` before implementing. This revised prompt includes the research-driven changes.

The goal is a playable three-level rhythm defense campaign, with a data-driven plan for ten levels. My new decisions below supersede conflicting old PRD assumptions: remove the enemy base from the campaign; surviving the song wins; instruments determine production recipes; physical buttons do not permanently identify instruments. The old maximum of four bass instruments is replaced by three equipped bass instruments.

## 1. Game loop and battlefield

This is automatic tower defense controlled by rhythm inputs. The player chooses a loadout before the song; during play they only perform the rhythm chart. There are no manual attack, rally or building commands during the song.

Create a player base with production/support buildings, defenses and required critical tech objectives. Levels 1–3 have one required `command_core`; later plans add a second `tech_core`. All required objectives must survive. Lose immediately when any required objective is destroyed. Win at the authored song end when all required objectives remain alive, even if enemies are still present. On a same-tick boundary, process rewards/combat, then critical losses, then the survival win. Audio release-tail length must not extend the gameplay deadline. Keep the existing audio-derived clock, calibration, pause/resume and timing windows.

There is no enemy base, enemy producer or enemy construction yard. Enemy units spawn through authored waves at off-screen/boundary entry points and attack toward the player's objectives. Ensure absence of an enemy base cannot trigger the old instant-victory condition. Wave spawning bypasses enemy production-building requirements and is independent of the player's performance or note count.

Add three defense points. Successive successful production groups are assigned round-robin to point 1, then 2, then 3, repeating. Keep each produced group together. Troops move there, defend locally and return after limited pursuit. This is successive group assignment, not a requirement that every troop continuously patrol all three points. Failed/unavailable inputs do not advance the point cycle. Record group ID and assignment for debugging.

Enemy waves specify start tick, entry, route/defense point, target objective and actor groups with spawn spacing. Telegraphed routes should be readable. Enemy units fight nearby defenders/blockers and continue toward their objective. Preserve working OpenRA actors, sprite animation, damage/armour, movement, projectiles and finite building repair rather than substituting placeholder combat. Add a defense-specific behavior path where the current two-sided Rush AI assumes two bases.

## 2. Campaign and progression

Implement levels 1–3 now and keep levels 4–10 as data/planning entries. The first three reference music/chart examples are attached. Level 1 is initially unlocked. Clearing a level unlocks the next and its new profiles before entry; any survival win clears it, with accuracy/medals as optional extra goals rather than compulsory progression gates. Save progress and loadouts locally using stable IDs and versioned, robust writes. Replaying a cleared level must not reset progress.

- Level 1, First Watch: 32 bars / 44.14 s; one kick and one snare; two outer buttons; easy half-time rhythm.
- Level 2, Second Pulse: 40 bars / 55.17 s; unlock a second kick; three active input positions; simple extra rhythmic responses.
- Level 3, Hold the Line: 48 bars / 66.21 s; unlock one bass synth; alternate drum and bass passages; the same bass instrument moves across all four input positions and uses long holds.

All three use a fixed 174 BPM, perceived half-time feel and 960 ticks/quarter. Difficulty is a combination of new skills, rhythm, hold patterns and wave pressure; note-on density need not rise on every level. Do not tighten judgement windows as a substitute for authored difficulty. Keep a two-thumb maximum of two required simultaneous touches at every level.

## 3. Instruments, sound and unit production

Build an extensible instrument catalogue. A player eventually equips up to TWO distinct kick instruments, TWO distinct snare instruments and THREE distinct bass instruments. There can be any number of catalogue choices; the equipped-slot caps remain 2/2/3. Each level declares its active required musical slots. Fill those slots from unlocked compatible profiles; unused future slots need not be equipped. A player must not remove a required part to delete its chart notes. Required defaults can be auto-equipped for a first visit.

Separate these concepts explicitly:

1. Musical part/slot: `kick_1`, `kick_2`, `snare_1`, `snare_2`, `bass_1`…`bass_3`.
2. Instrument profile selected for that slot: sound identity plus production profile.
3. Production recipe: a group or deterministic cycle of groups, with each step defining actor IDs and counts.
4. Physical chart button: 1–4, chosen by the authored musical pattern.

A kick may produce infantry. Another kick may alternate a heavy tank and a light tank. A snare or bass may produce any supported group when its profile says so. Remove hardwired campaign assumptions that kick always means a vehicle, snare always means five infantry, or bass always means air support. Keep family as musical metadata, not the production dispatch key. Resolve a successful note through its `slot_id` to the equipped profile and recipe.

Use deterministic per-equipped-slot recipe counters, reset per run. Only a successful available reward advances a recipe. Perfect and Good give the same production in the initial campaign. Misses give none. A hold gives one reward at successful completion, never repeated income while held. `Plan/instrument_catalogue.proposed.json` contains baseline recipes and unlock examples, not tested balance numbers; tune them transparently.

Retain producer-loss/muting as a data-driven slot rule: a profile declares required producer tags, which can differ from its family. By default all declared producers must be available. An unavailable slot's prompts are inert/excluded from judged accuracy and its audio is muted; its recipe and group-assignment counters do not advance. A destroyed critical core still ends the run immediately. If availability returns, restore the audio at its current timeline position. Mode switches alone never mute audio. Later air-support profiles should explicitly adapt the existing pad/ammo/sortie behavior; levels 1–3 need only ground production.

Show instrument sound and its unit mix/cycle on the pre-song loadout screen. Show locked choices and the level that unlocks them. Validate family, availability, distinct profiles within each family, required slots and 2/2/3 caps. Use existing real actors whose art and behavior are available.

## 4. Four physical buttons and authored focus

There are four unlabelled physical input positions. They represent recurring musical gestures/feel, not permanent instrument identities. Position is authored and predictable, never randomly remapped at runtime. Start simply: level 1 uses buttons 1/4; level 2 adds button 2; level 3's one bass voice uses all four. Keep repeated musical motifs consistent and cue focus changes in the incoming chart.

Each passage is `drums` or `bass` focus, selected in an authored section map. Drum focus charts selected kick/snare parts; bass focus charts selected bass parts. Enforce whole-bar exclusivity including active hold tails. Music can contain continuous drums and bass accompaniment while only one family creates player prompts. Uncharted accompaniment does not miss or produce units. Other parts are always accompaniment.

Preserve explicit `button`, `source_note_id`, `part_id` and `slot_id` through authoring, runtime serialization, loader, judge, renderer and production events. Never infer reward from the button. Judge and validate holds/conflicts by physical button; determine producer availability by slot/profile. Existing button-based judgement is reusable, but existing fixed kick/snare button checks and lane-based production dispatch are not the campaign contract.

## 4a. Research-driven chart design and thumb constraints

The four columns are authored performance positions. MIDI is timed candidate material, not a requirement to press every note. After phrase focus, select essential pulse/motif notes and then optional responses for each chart. Keep source-note IDs and an explicit selection/placement audit. Repeated motifs should reuse coherent patterns; automatic pitch placement is only a starting suggestion. The attached level-3 explicit overrides take priority over its fallback pitch ranges and are guarded by the source MIDI hash.

Validate thumb zones as well as physical buttons: left controls 1/2, right controls 3/4 by default. Reject a note on button 2 while that thumb holds button 1, and provide release/reach time before the same thumb moves to another column. For these first-three starter charts, use the authored minimum gaps: 960 ticks between same-thumb onsets after taps, 480 ticks from a hold end to that thumb's next press. These are initial design targets to test on a phone, not medical/industry limits. The revised bass phrases alternate thumbs without changing the music or sustain lengths. Later hold-plus-answer patterns use the opposite thumb; two-note chords use opposite hands. At most two global touches remains a separate check.

Separate campaign unlocks, chart difficulty, loadout and note approach speed. Provide a readability/approach setting independent of playback tempo and timing calibration; start playtesting around 2.2 seconds of lookahead. Keep the initial charts' scroll speed steady. Raise challenge through authored subdivisions, rests, hand independence and phrase variation, not mandatory longer songs or tighter timing windows.

Prove two charts over one source/render set with level 2: `player_chart.practice.json` has 80 essential inputs while the campaign chart has 96. The second kick is audible in both. Practice has no enemy waves, campaign unlocks or persistent production rewards; chart IDs and results must remain separate. Ship one campaign chart per first-three level rather than making every song in many tiers now. Future denser campaign variants need their own tested wave plan/explicit reward-budget design, because extra correct inputs also produce more units.

Do not add a one-miss song failure or direct core damage for a chart miss: lost production already creates a defense consequence. Preserve musical sound and note durations. Record overall and short-window/per-thumb density, hold workload and awkward release/reach transitions; do not claim these are a validated universal star rating.

## 5. Reusable music-to-chart pipeline

Implement/integrate a real offline conversion step, separate from musical composition. The attached `Authoring_Tools/compile_chart.py` is a working reference for the first three examples; its JSON output is a proposed interchange format, not already a supported Godot pack. It reads `song.json`, full musical MIDI and `chart_rules.json`, preserves source note IDs/times, applies section focus and authored placement, then writes `player_chart.json` and an omission audit.

Turn that into the project's repeatable authoring/import workflow. Validate source tempo/meter/PPQ, exact rescaling, duration, required slot IDs, profile compatibility, button conflicts, two-touch maximum, release gaps and holds crossing focus changes. Flag conflicts for explicit authoring repair; never silently move note-ons, shorten long holds, drop required notes or randomly move buttons. Source musical MIDI must remain complete and untouched. Chart conversion must never require altering audible drums just because bass is the current input focus.

Create a supported runtime defense song pack combining the compiled chart, waves, objectives/map, default loadout, render assets and any supported schema migration. Document how to regenerate it with one command. Keep source/import versions and hashes so an edited MIDI cannot silently keep an old chart/render. Update tests for intentionally superseded outcome/production assumptions while retaining their useful coverage.

## 6. Audio and instrument choice

Player-selectable sounds require separately rendered audio assets. A single pre-mixed Kick or Bass WAV cannot replace only one selected instrument. Support one synchronized stem per active equipped slot plus one Other stem: at most seven selected slot streams plus Other. The first three defaults need 3, 4 and 5 streams respectively. Preserve one transport clock and synchronized start/pause/resume/muting; verify the target Godot API's stream capacity and phone performance.

The owner renders each song-part/instrument combination in Ableton, with consistent tempo, start, sample rate and frame count. The game selects existing renders for the chosen loadout; it does not run Omnisphere/Pigments/VSTs or render new instruments live. Catalogue growth is data-driven, but a sound becomes selectable for a song only when a compatible render exists. Separate stems avoid rendering every possible whole-loadout combination.

Keep a four-family-stem compatibility option for a fixed pre-baked loadout if useful. Explain that arbitrary sound swapping is unavailable in that legacy representation. For this first campaign, implement the per-slot path and provide at least the default rendered/placeholder loadout for each of levels 1–3. Use the full musical MIDI for placeholder sound, not the filtered chart. Missing final WAVs must not block a playable development build; label temporary sound honestly and make replacement straightforward.

Add an audio preflight: files exist and decode; matching sample rate/frame count/common start provenance; audio covers chart duration; sum/peak and listening checks; selected render's part/profile/source hash matches. Length checks alone cannot prove alignment, so provide a beginning/transition/end listening check. Release-tail audio does not extend the authored survival duration.

## 7. Implementation order and verification

First prove the rhythm feel in a lightweight audio/chart playtest screen using the current timing/input systems, before the new battle/campaign work. Use taps and holds only. Demonstrate level 2 practice and campaign charts over identical audio, and the alternating-thumb level-3 bass motif. Then work in reviewable stages: (1) contracts and reference importer, (2) defense objectives/waves/three-point assignment, (3) profile-driven production and slot audio, (4) campaign/unlocks/loadout UI, (5) first-three integration, balancing and device evidence. Reach a playable first level early, then add levels 2 and 3. Preserve and use the existing synchronized audio, calibration, button judge and OpenRA combat where compatible.

Acceptance requires:

- No enemy base, no old instant victory because an enemy core is absent, correct immediate loss and survival-at-song-end win including a same-tick tie.
- Deterministic authored waves and round-robin production groups; spawn/route handling works without enemy producers.
- A kick profile producing infantry and another alternating vehicles, proven independently of the button used.
- The SAME bass slot producing its configured group when played on each of buttons 1–4, with authored repeating alternating-thumb placement.
- A two-touch same-side hold/tap conflict is rejected; two chart variants share source/render hashes but have independent chart IDs, selection and progression policy.
- No missed-note penalties for uncharted accompaniment; exact hold lengths and one reward at each completed tail; pause/calibration still work.
- Per-slot producer gating and gain restoration through focus changes, with recipe counters unaffected by unavailable notes.
- Progress save/reload, first-clear unlocks, loadout constraints and missing-render handling.
- Required importer/simulation/audio checks and integration of the 64 / 96 / 89 authored player events for levels 1 / 2 / 3.
- Run seeded trials with perfect play, plausible ~85% play, weaker ~60% play and no input. Tune default first-three recipes/waves so competent play survives and no-input play fails; report outcomes, seeds, miss patterns and objective health rather than asserting balance from note counts.
- Make a playable build with placeholder or final audio. Run a phone playthrough if the environment permits; otherwise identify that exact remaining check. Measure the game's actual new peak units/frame times without claiming unrun tests.

The attached 102 passed checks establish MIDI/chart structure only. They do not establish Godot integration, audio sync, enemy balance or phone performance. Deliver working first-three levels, updated docs, validation results and build instructions; leave the remaining seven levels as the supplied extensible roadmap. Commit the implementation in sensible stages and explain any material divergence from this plan.