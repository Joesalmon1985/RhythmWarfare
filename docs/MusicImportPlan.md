# RhythmWarfare — Intelligent Music Library and Arrangement System

You are working on the Godot 4.5 RhythmWarfare repository.

https://github.com/Joesalmon1985/RhythmWarfare

## Objective

Import and intelligently arrange my growing collection of drum and bass WAV and MIDI files to give the game varied, exciting, coherent music across its levels and story chapters.

I have supplied folders of musical material, including `Cold`, containing Beat Shaper exports and Ableton renders.

**Do not simply assign one folder to one level or randomly combine every available instrument.** Build a reusable music library and arrangement system that makes musically sensible decisions, avoids repetition, and preserves accurate rhythm gameplay.

Complete the implementation autonomously, including code, content generation, testing and documentation.

## Phase 1 — Understand the existing game

Inspect the current music architecture before changing anything, particularly:

- `tools/content/import_ableton.py`
- `tools/content/import_recorded.py`
- `src/audio/stem_transport.gd`
- `src/core/mission_loader.gd`
- `songs/library/index.json`
- `content/story/`
- Existing story music packs and tests

Understand the 174 BPM timeline, four-pad controls, MIDI cue generation, two-bar sequence judgements, phase transitions, stem muting and existing chapter progression.

Preserve existing gameplay, campaign content, save compatibility and audio timing.

Work on a separate feature branch and preserve any uncommitted changes.

## Phase 2 — Catalogue and analyse all music

Recursively discover the source music folders and analyse every WAV and MIDI.

Create a reproducible asset catalogue containing:

- Filename, provenance and matching WAV/MIDI pair
- Actual tempo, time signature, sample rate and duration
- Musical bar count, leading silence and release tails
- Instrument role: kick, snare, percussion, bass, synth, pad or effects
- MIDI note positions, durations, velocities and density
- Estimated key, pitch classes and tonal centre
- Rhythmic character, complexity, intensity and musical mood
- Audio loudness, peaks and clipping risk
- Compatible and incompatible musical combinations

Do not trust MIDI tempo metadata when contradicted by the audio.

For example, much of the supplied `Cold` material is four bars at 174 BPM despite MIDI headers specifying 120 BPM. Other exports are considerably longer.

Detect actual timing before conversion. Extend the existing importers to support both 174 BPM patterns and 87 BPM half-time patterns.

Never silently time-stretch, truncate, transpose or discard source material.

Keep originals unchanged and ignore Ableton `.asd` files.

Produce a machine-readable catalogue and a human-readable analysis report.

## Phase 3 — Identify musical compatibility

Analyse which stems work together.

Use original export groupings as the strongest compatibility evidence, then consider:

- Harmonic compatibility between bass and synth parts
- Rhythmic compatibility between drums and bass
- Arrangement density and frequency masking
- Similar or complementary musical character
- Matching phrase lengths and musical boundaries

Different bass renderings of the same MIDI pattern should be treated as alternative timbres, not unrelated compositions.

Do not combine incompatible keys or chord progressions merely to increase variety.

Where two pieces do not fit, keep them in separate musical families.

Flag uncertain pairings for review rather than treating an estimated key as authoritative.

## Phase 4 — Build an intelligent arrangement system

Create a data-driven arrangement system that produces complete, coherent musical experiences.

Each story chapter should have a recognisable musical identity.

Arrange music in phrases, with introductions, builds, drops, breakdowns, variations and endings.

Use the existing story chapters:

1. Night One — energetic warehouse rave
2. Mothership — futuristic electronic sounds
3. Underworld — aggressive dark neurofunk
4. Hospital — atmospheric, fragile, gradually uplifting
5. The Ward — unsettling industrial and experimental music

Treat these as creative guidelines, not rigid filename-based assignments.

Integrate compatible assets into other game modes where appropriate without breaking the existing loadout system.

Vary the arrangement using:
- Alternative drum grooves
- Alternative compatible basslines
- Different synth textures
- Drum fills and rhythmic embellishments
- Introductions and breakdowns
- Instrument layering and removal
- Occasional contrasting sections
- Different arrangements across repeat playthroughs

Maintain a consistent musical identity within each scene. Avoid changing everything simultaneously or making random selections every bar.

Prefer changes on four- or eight-bar boundaries.

Use deterministic seeded choices so that replaying a given arrangement produces exactly the same audio and gameplay chart.

## Phase 5 — Preserve gameplay quality

Every playable note must align with the audible MIDI-derived instrument event.

Keep the existing pad mappings, judgement timing, note display and sequence mechanics.

Separate gameplay-relevant kick, snare and bass material where possible.

If a recorded drum WAV contains multiple instruments, do not pretend the isolated kick and snare audio is available. Either derive reliable individual stems from the MIDI and verified renders, or preserve the grouped-stem behaviour.

Not every audible note needs to become a playable note.

Create engaging, human-playable charts with a deliberate balance of rhythm, rests, holds and difficulty.

Avoid simultaneous notes and overlaps that violate existing gameplay rules.

Musical intensity may increase without increasing gameplay difficulty.

## Phase 6 — Technical implementation

Extend existing systems rather than introducing a competing music engine.

Prefer offline-prepared arrangements and metadata over expensive runtime audio processing.

Ensure:

- Sample-accurate alignment at 174 BPM
- Seamless phrase boundaries and transitions
- Correct handling of release tails
- Consistent levels without clipping
- No accumulated sync drift
- Safe audio streaming and memory usage on Android
- Continued use of the existing authoritative song clock
- No unexpected restarts or silence when the story branches

Where runtime variation would introduce timing or performance problems, pre-render several musically curated arrangement variants instead.

Keep branch and story outcomes independent of transport timing.

## Phase 7 — Populate the game

Use the available music to improve all suitable existing chapters and missions.

Do not overwrite the established Night One recording or remove existing music without a tested replacement.

Prefer authored, coherent arrangements over maximal asset utilisation.

Allow each chapter to contain multiple musical sections, and allow suitable alternative arrangements on subsequent playthroughs.

Integrate music changes with existing narrative moments, particularly entrances, energy shifts, successful performances, failures and endings.

Preserve the existing branching story, progression and gameplay.

## Phase 8 — Validation and deliverables

Implement automated tests for:

- Asset discovery and metadata
- MIDI/audio synchronisation
- Loop boundaries and phrase lengths
- Compatibility rules
- Peak levels and audible gaps
- Chart legality and note density
- Deterministic arrangement selection
- Every story chapter loading and completing
- Existing campaign and story regression tests

Generate short audition WAV previews for the main arrangements so I can listen to the combinations without launching the game.

Produce these deliverables:

1. Imported, organised and validated music assets
2. Reusable musical compatibility catalogue
3. Working arrangement selection and playback integration
4. Improved story chapters using the available music
5. Several arrangements for replay variety where possible
6. Audition previews
7. A report showing which music appears in which chapters and why
8. Test results, limitations and clear instructions for importing future folders

Include before/after metrics for playable variations, source utilisation and asset size.

Do not claim musical compatibility solely because two files share a tempo.

Prioritise music that sounds coherent and is fun to play over using every asset.

**Carry out the work in full, not merely a plan or proof of concept.** Make sensible implementation decisions, document trade-offs and continue through testing. Stop only for genuine blockers or potentially destructive actions.
