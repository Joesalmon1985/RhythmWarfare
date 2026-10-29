# Rhythm-game research and refinements

Reviewed 28 October 2026. This is a public-source design review, not a hands-on app or phone playtest. The proposals below are our design choices for Rhythm Warfare; numerical limits are initial authoring targets, not measured industry standards.

## What the primary sources establish

### Magic Tiles 3: immediate, readable music-following

Amanotes' official store description presents descending tiles matched to the beat and says a missed tile stops the music. Its public material establishes the basic loop but does not document the internal MIDI/audio-to-tile algorithm. We should not claim that it automatically maps MIDI pitch to a particular column.

Source: [Amanotes' Google Play listing](https://play.google.com/store/apps/details?id=com.youmusic.magictiles&hl=en-GB&gl=GB).

Our adaptation: clear approaching targets, a stable judgement line, immediate hit feedback and recognisable repeating musical gestures. Rhythm Warfare's base health already creates consequences for missed production; an additional one-miss game-over rule would be excessive for this hybrid.

### Project SEKAI: deliberate musical interpretation

Colorful Palette's chart designers describe selecting musical layers, guiding hand movement and making release timing fit the sound. They also discuss teaching patterns from the next difficulty gradually. These are editorial decisions about playing experience, not a universal note-to-column conversion.

Source: [Chart designers' article, 24 December 2023](https://media.colorfulpalette.co.jp/n/nf36e1946d71b?hl=en).

Our adaptation: the same song can support different selected-note patterns; sustain should feel continuous, releases audible, repeated phrases consistent and each new coordination skill rehearsed before pressure rises. Timing and pitch are source data; placement is authored.

### osu!mania: useful formal chart constraints, with a different input device

The official wiki's ranking criteria tie chart notes to audible sounds and distinguish density, holds, releases, repeated-column patterns and difficulty spikes. Its standard 4K playstyle assumes a separate finger for each key, so its numerical limits cannot be copied directly to our two-thumb phone game.

Sources: [Ranking criteria](https://osu.ppy.sh/wiki/en/Ranking_criteria/osu!mania), [mapping guide](https://osu.ppy.sh/wiki/en/Guides/osu!mania_mapping_guide), [beatmapping overview](https://osu.ppy.sh/wiki/en/Beatmapping).

Our adaptation: make the device's hand constraints explicit, introduce one coordination skill at a time and inspect local bursts/release difficulty as well as total note count. Each required gesture should be heard in the music.

### Presentation and chart editing are separate concerns

SEGA's help distinguishes note approach speed, timing adjustment and appearance. Colorful Palette's 2026 chart-maker report describes authoring notes and reusing/mirroring groups of notes. These support separating the musical timeline, readable presentation and editable pattern data.

Sources: [Official show-settings help](https://sega.helpshift.com/hc/en/12-hatsune-miku-colorful-stage/faq/784-how-do-i-adjust-the-show-settings/), [chart-maker development report, 6 August 2026](https://media.colorfulpalette.co.jp/n/nf21536e63358), [SEGA announcement](https://www.sega.jp/topics/detail/260326_5/).

Our adaptation: keep playback/calibration authoritative; expose note visibility/approach as a readability setting. Use simple phrase templates and explicit note overrides before considering a large visual editor. We do not need swipes, slides or variable scroll-speed tricks for the first campaign prototype.

## The revised music-to-input model

1. Read the full musical MIDI as timed candidate events, preserving pitch, note-off, source ID and slot.
2. Choose the musical foreground for each 4/8-bar phrase. The MVP retains mutually exclusive drum or bass focus, with whole-bar boundaries that respect active holds.
3. Choose essential notes for the intended chart: pulse/backbeats and recognisable motif first, optional responses/ornaments later. A note can be audible accompaniment without requiring input. Avoid arbitrary random thinning.
4. Apply an authored phrase footprint: alternating hands, call/response, a held anchor with an opposite-thumb answer, or later two-handed accents. Repeat the footprint when its musical motif repeats. Pitch contour can suggest placement but does not permanently bind a pitch or instrument to a button.
5. Validate by physical button AND thumb. Preserve actual musical timings and sustain lengths. If the layout is awkward, revise placement/selection explicitly; if the sound itself is too short, revise the musical part and render.
6. Playtest with the actual sound, then compile a versioned chart. At runtime use the approved chart, not a live random generator.

The fixed 174 BPM remains compatible with very easy charts: two salient presses in a bar feel different from four presses and offbeat responses over exactly the same music. Increasing BPM, track length and scroll speed together is not a useful generic difficulty ladder.

## Two thumbs need more than a two-touch ceiling

Default phone zones are buttons 1–2 for the left thumb and 3–4 for the right. One thumb cannot simultaneously hold button 1 and press button 2. It also needs movement/release time when the next note changes column within its zone. Permit a held anchor plus an answer on the opposite side; two-note chords should use opposite hands.

Initial first-three targets: at least 960 ticks (~345 ms) between same-thumb note starts after a tap, and at least 480 ticks (~172 ms) after a hold ends before that thumb's next press. These are our conservative design targets, subject to actual phone testing. They do not change the judgement windows or allow extending a source note beyond its sound. Use a configurable thumb layout if supporting other grips later.

The original level-3 pitch-range mapping produced some zero-gap moves between adjacent buttons in one hand. The revised chart uses a repeating alternating-thumb footprint. Every source note, onset and hold length is preserved. All four buttons still occur, and the selected instrument/unit recipe still follows the same bass slot.

## Difficulty, progression and battle balance

Keep three separate concepts:

- Campaign mission: enemy waves, objective layout and unlocks.
- Chart variant: selected notes and gestures for that song.
- Instrument loadout: audible renders and production recipes, within the current unlocks.

The ten missions still introduce the planned instrument/units. Later duration estimates now plateau rather than increasing every level. New coordination patterns, not mandatory extra seconds, supply rhythmic progression.

For the first release, ship one campaign chart for each of levels 1–3. Also prove a reduced practice chart for level 2: 80 essential taps versus the 96-tap campaign chart, using the identical musical MIDI/render identities. The extra kick remains audible. Practice has a distinct chart ID, no waves/unlock progress and no persistent production rewards. Do not build every song in three difficulties before the basic chart feels good.

Later Easy/Standard/Expert campaign challenges need their own tested wave profile or explicit production-budget design. More required inputs can create MORE units, so a denser chart does not automatically make this defense game harder. Balance by the combination of chart ID, wave plan and loadout; do not silently weaken rewards or alter waves according to live accuracy. Keep initial campaign unlocks based on survival, with timing medals as optional mastery goals.

Do not make misses deal additional direct core damage. A missed reward already reduces the defense. Hold start/progress/completion should give clear feedback, while the production reward still occurs once at completion. Add readable wave warnings and cue drum/bass changes through incoming notes; do not change audio muting just because the focus changed.

## Measure the difficult parts

Authoring reports should record note-head density overall and in short windows, per-hand note counts/bursts, consecutive same-thumb timing, hold duty time and release-to-next-press gaps, simultaneous input demand, phrase/focus transitions and any abrupt change in workload. These are diagnostics for playtesting, not a validated universal star-rating formula.

A sensible early sequence is pulse → an answering/offbeat note → hold/release and four-position melody → full-time backbeat → opposite-thumb accompaniment → two-handed accents → syncopated variations and combinations. Stage each new pattern once in a readable, low-pressure passage before repeating it with stronger waves. Keep a stable initial approach window; about 2.2 seconds is a starting playtest value, not an established optimum.

## What was refined in the pack

- All 18 musical MIDI files are byte-identical to the previous pack, verified by SHA-256.
- Campaign event counts stay 64 / 96 / 89. Level 3 still has 29 holds at their full musical lengths; its button placement now alternates thumbs within each bass phrase.
- Level 2 adds an 80-note practice chart sharing the exact musical sources. It omits required second-kick prompts while preserving that audible part.
- The reference converter supports explicit authored selection, source-note button overrides, source-version guards and per-thumb validation.
- The Claude prompt now starts with a rhythm-only playtest milestone before the larger defense build. It asks for readable taps/holds first, not a full chart editor or extra gestures.
- The progression, render workflow and survival objective remain intact. Waves/recipes remain proposed and unbalanced until in-engine trials.

This is an evidence-informed design refinement and authoring example. No game implementation, audio render or phone playtest was performed in this research pass. The reference checks establish structural properties only.
