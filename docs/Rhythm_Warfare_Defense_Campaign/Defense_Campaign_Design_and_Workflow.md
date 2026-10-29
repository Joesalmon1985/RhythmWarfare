# Rhythm Warfare — defense campaign design and music workflow

This package turns the new direction into a concrete implementation brief, ten-level roadmap and the first three musical authoring examples. The current game repository was read at `ed8207faa231c9dc5c315e6b9ecda6e4a235c75e`. No game code was changed here.

## Research refinement before implementation

Read `Rhythm_Game_Research_and_Refinements.md` for the public-source review of Magic Tiles 3, Project SEKAI and osu!mania. The main refinement is a deliberate chart-design step: choose musical foreground and salient events, reuse readable phrase footprints, and validate each thumb's work. Required notes are selected from complete music; song pitch does not permanently assign a column.

Campaign progression, chart variant, instrument loadout and approach-speed readability are separate. Start with one campaign chart each for levels 1–3, plus the reduced level-2 practice example. The practice/campaign pair uses identical musical assets (80 versus 96 inputs), with no practice-wave/unlock rewards. Later challenge variants must have their combat balance tested independently.

The level-3 chart now uses explicit alternating-thumb note placements. This removes zero-gap same-thumb moves caused by its original pitch bands, while retaining all 29 notes/holds and every musical MIDI byte. The explicit source-note overrides and expected MIDI hash are authoritative; fallback pitch ranges only suggest positions. Default hand zones are 1/2 left and 3/4 right, with the conservative first-three gaps declared in `chart_rules.json`. These are design targets awaiting phone testing.

The first milestone for Claude is a small sound/chart playtest before the tower-defense expansion. Prototype taps and holds with a steady approach speed and clear feedback. A missed note loses its production opportunity, without extra direct core damage or an instant rhythm failure. Keep the survival game and the 2/2/3 loadout direction.

## The new game

Play a rhythm chart to produce groups that automatically defend a player base until the song ends. Enemies arrive in authored off-map waves. The player chooses instruments before the song and performs inputs during it; there are no troop commands during the run.

The important separation is:

- Music part: what notes actually sound.
- Chart: which of those notes currently require input, and on which physical button.
- Equipped instrument: what sound renders that part and what unit recipe the input activates.
- Wave plan: independent enemy pressure, timed to the musical structure.

Source MIDI supplies timing and musical pitches, not permanent input positions or unit roles. A kick can produce infantry; a snare can produce a vehicle. A single bass voice can move across all four buttons. Different unlocked sounds can render the same musical part while keeping its chart intact.

## Requirements and proposed defaults

The user's requirements are the ten-step difficulty ladder, instrument/unit unlocks, player-only base survival, authored enemy waves, three defense points, loadout caps of 2 kick / 2 snare / 3 bass instruments and four inputs that follow drums or bass by passage.

These defaults make the implementation concrete and can be revised:

1. All required tech objectives must survive. Levels 1–3 have one Command Core; level 6 introduces a second required Tech Core. Destruction is immediate defeat. Surviving the musical deadline is victory; enemies remaining on screen do not prevent a win.
2. Successive production GROUPS cycle point 1 → 2 → 3. All members of a group share the assignment, defend there and return after limited pursuit. This interprets “cycle” as assigning successive groups, not having every unit patrol continuously.
3. Clearing a level unlocks the next and its new catalogue entries. Accuracy is reported, but no high accuracy gate blocks the beginner ladder. Loadout choice occurs before the song.
4. Levels declare required musical slots. Players equip unlocked family-compatible instruments in those slots, with distinct choices within each family. Early levels use fewer slots. Omitting a required instrument never removes its notes from the challenge.
5. A successful available tap or hold completion advances that slot's deterministic unit-recipe cycle once. Good and Perfect initially have equal production; score still distinguishes them. Long holds do not give repeated production income.
6. Existing producer-loss/muting becomes a per-slot rule based on the selected recipe's required producers. Unavailable notes are inert/excluded from accuracy; automatic follow-drums/follow-bass changes do not mute the music. Air-support rebuilding is a later, explicit recipe rather than a rule for every bass instrument.

These are design choices, not newly implemented engine behavior. Reference production recipes and waves are starting data requiring battle tests.

## Ten-level ladder

All initial songs use 174 BPM / 4/4. First-three drum grooves have an 87 BPM half-time feel; faster backbeats arrive later. Duration alone is not the difficulty measure: each level introduces a musical or defensive skill. Keep timing windows consistent and require no more than two touches.

| Level | Song | Duration | Main new skill | Profiles available on entry |
| --- | --- | --- | --- | --- |
| 1 | First Watch | 44 s | Two outer buttons; steady half-time pulse | kick_march, snare_guard |
| 2 | Second Pulse | 55 s | Add a third input and a second kick | kick_armour |
| 3 | Hold the Line | 66 s | Introduce bass mode and long holds across all four buttons | bass_patrol |
| 4 | Backbeat | 66 s | Second snare and first full-time drum passages | snare_crack |
| 5 | Counterpoint | 77 s | Second bass voice; hold plus opposite-thumb answering line | bass_reese |
| 6 | Fortress | 77 s | Review learned rhythms; support loadout and two objectives | kick_siege |
| 7 | Airbridge | 88 s | Three audible bass voices; chart at most two thumb roles | bass_growl |
| 8 | Crossfire | 88 s | Opposite-hand accents; anti-air loadout before enemy air | snare_flak |
| 9 | Iron Rhythm | 88 s | Heavy/light tank cycle and more syncopation | kick_heavy |
| 10 | Last Light | 110 s | Combine rehearsed motifs with recovery phrases | bass_command |

“Available on entry” means the previous clear grants access before playing that next level. Level 1's two profiles are available initially. Later names describe catalogue recipes, not a permanent instrument-to-unit law. The JSON plan has the active slot counts, critical objectives and wave themes. Future duration estimates now plateau; duration is not a mandatory rising difficulty measure.

The example unlocks bring riflemen/jeeps first; light tanks at level 2; mixed rifle/rocket squads at 3; grenadiers at 4; medium tanks at 5; artillery at 6; player air support and the third bass slot at 7; flak support before enemy aircraft at 8; heavy/light tank cycling at 9; and a final command-bass choice including a mammoth tank at 10. Catalogue entries are examples, not tested equal-power sidegrades. Claude should tune the recipes against waves and clearly show their unit cycles.

## First three: actual music and chart examples

### Level 1 — First Watch

32 bars / 44.138 seconds. One kick and one snare, 32 taps each, on outer buttons 1 and 4. There are no required chords or holds. Four opening bars give time to learn and build defenders before the first proposed enemy wave.

Default instruments: March Kick creates two riflemen per successful note; Guard Snare creates one jeep. This intentionally demonstrates that family does not dictate a unit class. Proposed enemy waves initially share one approach so the rhythm remains the learning focus. All three defensive points still exist.

### Level 2 — Second Pulse

40 bars / 55.172 seconds. Adds a second kick from bar 9: 40 primary kicks, 16 answering kicks and 40 snares, 96 prompts on buttons 1, 2 and 4. Keep the half-time feel and simple one-beat responses. Enemy approaches begin alternating.

The new Armour Kick cycles one light tank, then one jeep, repeating. Both kick profiles remain distinct selectable instruments. Source MIDI is split by slot, which allows independent audio rendering and profile choice.

### Level 3 — Hold the Line

48 bars / 66.207 seconds. The new Patrol Sub produces a group of two riflemen and one rocket soldier on each completed hold. The bass melody moves across buttons 1–4 while retaining the SAME slot/profile. Source drums continue during bass gameplay.

| Bars | Gameplay focus |
| --- | --- |
| 1–8 | Drums |
| 9–16 | Bass |
| 17–24 | Drums |
| 25–32 | Bass |
| 33–40 | Drums |
| 41–48 | Bass |

The chart has 60 drum taps and 29 bass holds (89 events). Holds include half bars (~0.69 s), full bars (~1.38 s) and two bars (~2.76 s). This starter lesson remains monophonic: the long-held note changes buttons, with no simultaneous second bass line yet. Level 5 introduces that extra coordination. Final required input resolves before the deadline.

All three charts are structurally valid reference content. Their proposed maps, wave pressure, unit recipes and overall difficulty still need in-engine play/balance tests. A smaller note-on count at level 3 does not make its mode changes, four-button melody and release control the same challenge as level 2.

## Why the audio workflow needs a change

Four WAVs—Kick, Snare, Bass, Other—work for a FIXED rendered loadout. Once two separately selected kicks or three separately selected bass instruments must sound different, a combined family WAV cannot swap just one of them.

Use an independently rendered stem for each active equipped slot, plus Other:

- Level 1: kick_1 + snare_1 + Other = 3 synchronized streams.
- Level 2: kick_1 + kick_2 + snare_1 + Other = 4.
- Level 3: kick_1 + kick_2 + snare_1 + bass_1 + Other = 5.
- Fully unlocked: up to seven slot stems + Other = 8.

Keep one shared transport clock. The game selects existing renders for the equipped profiles and mixes them at runtime. It does not load Ableton instruments or Omnisphere/Pigments presets. An extensible catalogue does not automatically create audio: each new profile needs a compatible render of the song part it can replace.

Separate stems mean rendering individual slot/profile alternatives, not every possible whole-loadout combination. Start with the default loadout for each of the first three songs, then render extra choices as needed. A pre-baked four-family mix can remain a compatibility export for a fixed loadout.

## Repeatable MIDI → music → chart → game workflow

1. **Generate/compose the musical source.** Each playable slot has its own full musical MIDI. Other accompaniment is separate. The pack's `Music/` folders contain those parts; `References/Full_Music_Master.mid` is their exact combined view. Choose the separate parts OR the master for routing, rather than sounding both.
2. **Choose the available instruments.** Start with each level's `song.json` default loadout. In Ableton, put a suitable sample/synth on each active slot. MIDI 36 is the primary kick selector, 48 the second kick, 38 the snare; assign the intended samples explicitly. The bass part needs a patch that audibly sustains until note-off. Save the exact preset/settings as that profile's sound identity.
3. **Arrange on one timeline.** Set 174 BPM and 4/4. Put every MIDI at bar 1 without trimming leading silence or moving a late first note to time zero. Keep musical MIDI complete, including drums under bass-focus sections. Add pad/hats/effects to Other; no Other note creates a player prompt.
4. **Render each slot separately.** For game copies, use 48 kHz, 16-bit PCM WAV, normalization off, with the same start/end for every stem in that song. You can retain 24-bit production masters separately. Render from bar 1 through one common tail bar: level 1 ends at the start of bar 34, level 2 at bar 42, level 3 at bar 50. Their musical deadlines remain starts of bars 33, 41 and 49. Use the per-level `Render_Checklist.csv` for exact file names and ranges.
5. **Keep a reproducible mix.** Put track effects on the slot they belong to. Keep shared nonlinear master processing out of independently exported game stems, or verify a documented equivalent rendering path. All stems together should reproduce the intended mix with headroom. A rendered ducking/envelope pattern remains baked in when a different stem is muted; audition those states. Record slot/profile ID, patch version, source-MIDI hash, sample rate, frame count and gain.
6. **Compile the independent chart.** `chart_rules.json` states passage focus and authored button placement. The reference command below reads the full musical MIDI and creates `player_chart.json` plus `chart_audit.json`. It does not alter the musical files. During bass focus it omits drum prompts, not drum audio. It preserves bass note lengths and rejects a hold that would cross into a drum passage. Source or mapping edits require chart regeneration; a compatible timbre-only change can reuse the chart but needs a new render.
7. **Build the runtime level.** Claude combines the compiled chart, selected render manifest, authored waves, objective/map data and loadout definitions into the supported game schema. The included JSON is a proposed authoring format, not a drop-in `level.json` for the current game.
8. **Preflight and play.** Check exact audio sample count/rate, common-start provenance, source/render hashes and chart coverage. Listen at the beginning, focus switches and end; matching lengths alone cannot prove alignment. Test production/muting by slot, enemy waves, survival conditions, progression and the default loadout on a phone. Use perfect, plausible 85%, weaker 60% and no-input trials to tune waves and recipes.

Example after installing `mido==1.3.3`, from the extracted pack root:

```bash
python Authoring_Tools/compile_chart.py First_Three/level_03
python Authoring_Tools/compile_chart.py First_Three/level_02 --rules chart_rules.practice.json --out player_chart.practice.json
python Authoring_Tools/validate_campaign.py .
```

The converter supports fixed-tempo, 4/4 synchronous PPQ MIDI for these examples. Tempo/meter mismatch, inexact PPQ rescaling, physical-button conflicts, hold leakage and more than two touches are authoring errors. It is a reference command, not yet the production Godot importer. The contained tools never load plugins or read secrets.

## Integration and delivery order

Give Claude `Claude_Defense_Campaign_Prompt.md` and attach this ZIP. It should inspect the current project, implement contracts/conversion, reach a playable first defense level, then integrate slot-driven loadouts/audio, progression and levels 2–3. Temporary synthesized sound is sufficient until you supply real renders; it must come from the full musical source and be labelled placeholder.

The current code already has four physical buttons and button-based hold judgement. The important changes are the old enemy-base/song-end outcomes, two-sided setup/AI assumptions, enemy producer-based spawning, `Match` dispatch through `sim.produce(lane)`, lane-bound producer availability, fixed kick/snare button checks, four hardcoded audio stem keys and absence of campaign progression. Preserve useful OpenRA behavior, calibration and the one-clock transport.

Instruments and recipes should be data, with validated actor references and separate per-slot cycle state. Advance the defensive-point assignment once per successfully queued group; all its units share the point. Author enemy pressure independently of the note chart. Reject missing renders as a selectable sound option, while keeping a known default/placeholder set playable.

What is ready here: ten-level design, first-three musical MIDI, focus maps, reference chart converter, compiled charts, proposed catalogue/waves and structural validation. What remains: production Godot schema/importer, battlefield/defender AI, progression UI/save, per-slot transport, real WAVs, battle balance and device tests.

102 structural checks passed, including source-version, same-thumb transition and same-side hold/tap conflict checks, plus the shared-source practice/campaign example. All 18 musical MIDI files remain byte-identical; see `Musical_Source_Integrity.json`. No Godot run, WAV alignment, preset audition, phone test or battle balance result is claimed.
