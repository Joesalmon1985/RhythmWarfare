# Lead rulings during the one-PC work

Points that the agents raised and the lead decided, so that later agents do not decide them again. Each
names where it came from. The documents and the contract are brought into line with these in stage D4.
Where a ruling changes the owner's numbers it says so, and the owner can overrule it.

## 6 November 2026

### Interaction (from the interaction design agent)
1. The cap of 8 per scene counts **choices** (objects that lead somewhere). Reactive objects are a separate
   list, are not capped by it, never have a default and never take part in routing.
2. The hub rule adds **19** quest entrances, not 16: four in each of the four new hubs, and three on the
   Warehouse Floor, which today holds only the wizard (the other three Warehouse entrances are in the Bar,
   Balcony and Booth, behind flags and rhythm gates).
3. The smallest target stays 88 px in the 1280x720 design. It is 48 dp only up to 440 dpi; whether to raise
   it to 96 px is decided after the phone test (stage X4).
4. Touch region and visual bounds: as `INTERACTION_DESIGN.md` section 3.6 states them.

### Music transitions (from the music transitions agent)
5. `blend` applies up to **50 cents** of pitch change on the tail (a tempo ratio within 2.93%), not "within
   3%", which is 51.2 cents.
6. No real pair of the 61 tracks is near 2:1. `halftime_blend` is built and tested on fixture packs only;
   the owner's listening pairs are a blend, an echo-out (for example 174 to 140) and a cut.
7. The outgoing music is silent at least 4 bars before the incoming drop. That needs a lead-in of at least
   5 bars; a scene whose lead-in is shorter (first drops at bar 0 and bar 15 exist) is entered with `cut`.
8. What M1 leaves in place for M2 is section 12 of `MUSIC_TRANSITIONS.md`. The M1 agent was told on the day.

### The port (from the mock and conformance agent)
9. Laps are numbered from 1, as in the engine. `doors_from_lap` 2 with 4 laps gives departure laps 2, 3, 4.
10. A block is 16 beats. `when == &"soonest"` means the next 16-beat block boundary at least a lock lead away.
11. On a replace, `request_closed(old, &"replaced")` comes before `request_acknowledged(new, true, &"")`.
12. At a switch, `tempo_changed` comes before `switched`.
13. An unavailable destination may be refused at once (id 0) or acknowledged and closed before the lock.
14. A `&"blending"` deferral may repeat. `begin_scene` clears the default, so the narrative side sets the
    default again in its `switched` handler. A final lap reached while a blend is still running is extended
    by one lap without a signal.

### Narrative graph (from the narrative graph agent)
15. Every hub, the Warehouse Floor included, gets a Dungeon entrance that is **not** gated by rhythm and
    is taken at the lap's end through the port, like the other three quests' entrances. The wizard stays
    as he is (mid-scene, needs a passed block) as an extra way in. That makes **20** new entrances and
    brings every quest to 1 ungated choice from the start. This supersedes ruling 2's count of 19.
16. The cap of 8 choices is the default. A hub scene may set `max_hotspots` up to 10 (the per-node override
    exists today; the `ward` node uses it).
17. Seven path scenes cannot reach three choices from "onward, back, return" alone. The five restart routes
    and two second routes proposed in `graph/overlay_proposed.json` are accepted as the working design and
    are listed for the owner to confirm.
18. The mainline stays one-way (Warehouse, then Alien Spaceship or Hell, then Hospital Ward or Mental
    Hospital) with hub-to-hub links inside each pair. The owner's second illustrative route cannot be walked
    in the order written (Mental Hospital before Alien Spaceship); it is tested in the walkable order: Alien
    Spaceship, LOTR, Alien Spaceship, Mental Hospital, Catch-22, Mental Hospital. The owner is told.
19. The Bassment's passages that still offer fewer than three choices after the return object is added (42: the validator counts passage 23, whose third choice is item-locked)
    are the declared exception, reported by the validator on every run.

### After the document review
20. How the Bassment is entered and left through the port (the narrative graph document says through the
    port; the music transitions document says `RunEngine.resume`, a `cut`) is decided by a short spike at
    the start of N2.2, with the music stream's M1 code in hand. Until then both documents stand, and a
    Bassment transition is always a `cut`.
21. While the music stream holds `run_hotspots.gd` and `run_journey.gd` for M1, it does not edit
    `tests/test_hotspots_*`. If an M1 change makes one of them fail, that is reported to the lead.
22. The baseline of the work is the plan commit `ad5d1849` on `feature/one-pc-plan` (child of the handover
    commit `90a42877`). `feature/one-pc` started from it.
23. The coverage targets as the audit tool reads them stand: touch coverage at least 50% in at least 80% of
    samples, and choice coverage at least 25% in at least 80% of samples, a sample with nothing selectable
    counting as 0%. Measured on 6 November: 0 of 82 scenes pass (`coverage/baseline.md`).

### From the owner, during the work
24. On 6 November 2026 the owner stated that they hold the rights to include all the music tracks in the
    game, and asked that, once the work is done, the Android APK be updated with the tracks included. So
    the final build bundles the tracks (stage X4): a build step re-encodes the stems for the phone, the
    packs are found inside the build, and nothing has to be pushed to the device by hand. The earlier
    wording "a build with these recordings cannot be given to anyone" is withdrawn. Two things do not
    change: audio is not committed to the public Git repository (the owner's statement was about the game,
    and the packs are several GB), and `main` is not touched until the owner says so.
25. From the owner, 6 November 2026: the entrances to the quests from the main flow must be more obvious.
    Each entrance has a **herald**: a character from that quest standing at the entrance and gesturing
    towards it. A herald is scenery that belongs to the entrance: it is not a choice, does not count
    towards the cap of choices (ruling 1) and never takes part in routing. The art stream builds the
    herald (the character, the gesture, a way to attach one to an entrance) and shows it on the entrances
    that exist today; N2.4 places one at every one of the 20 new entrances.
26. From the owner, the same day: "a big visual polish so the graphics look seamless, and none of the
    artwork is jarring", in parallel with the other work. So there is a third stream, **art (A)**, from now
    until stage X (it replaces X5). It owns: `assets/**` art, the art builders under `tools/story/**` and
    the art scripts `tools/run/make_choice_art.py`, `make_ember.py`, `acting_*.py`, the generated people
    sheets (regenerated only by the art stream, one commit at a time, never merged), the look of the
    stage in `src/story/**` (style, shaders, world drawing), and `docs/shots/art/`, `docs/art/`. It does
    not edit `src/run/**`, `src/transition/**`, `src/narrative/**`, `src/track/**`, the tests of those, or
    `tools/run/hotspot_tables/**` except where ruling 25 needs a herald attached. The narrative stream's
    N2.4 to N2.6 add new objects as new files and follow the art stream's style guide. It starts with an
    audit (every scene captured, compared with the owner's references in `pixelexample/` and with
    `docs/STORY_25D_ART_DIRECTION.md`), then fixes by world in parallel.
27. After the art audit (`docs/art/VISUAL_AUDIT.md`, `docs/art/STYLE_GUIDE.md`): the art packages are the
    audit's section 4, and each owns only the files its row names. The world packages (W1 to W9) own their
    world's map and chapter JSON under `content/story/**` as well as its art. A4 (choice art) may make the
    one small change it needs in `src/run/choice_props.gd` (the door and lamp looked up per world). The
    camera findings (F5, F16) wait for the entrance-visibility work, which is in the rails now. The style
    guide binds every stream that adds an object.
28. `tools/dev/godot.sh` gives each worktree its own user data folder (`<work>/userdata/<worktree>`), so
    worktrees run Godot at the same time; the lock is per worktree. `RW_GODOT_SHARED=1` is the old
    behaviour (the real user folder, one lock for the machine). This supersedes "one Godot at a time on
    this machine" in the plan and in `FILE_OWNERSHIP.md`.
29. The owner's answers to the audit's questions of taste (6 November 2026): falling notes and holds are
    drawn **as light** (a glowing outline with a faint body, holds a thin lit core; timing unchanged); the
    pad strip has **a skin per world family** (club desk, ship console, hell's copper, a wooden board for
    Galilee, an instrument panel for the Squadron, a carved board for the Ember road); the title screen is
    the menu over **a live, slowly moving view of the Warehouse floor** in the chapters menu's neon style,
    without the engine version line. Package A3 (UI) builds these and may edit `src/scenes/main_menu.*`
    and `src/run/run_hud.gd` for them.
30. The standard for a quest entrance, after the entrance-visibility work (`docs/art/HERALDS.md`,
    `docs/shots/art/entrances/`): every entrance to a quest from the main flow is **a lit doorway or gate in
    the quest's colour**, with **its herald beside it gesturing at it**, **the mark over it** and **a pool of
    light on the floor**; and the scene's camera keeps the herald and the gate in frame for the scene's
    opening bars (`herald_looks` in `src/run/run_journey.gd`; `tests/test_heralds_view.gd` checks it). A
    small object alone (the radio, the ember, the star as first built) does not count as an entrance. The
    owner was told of this on 6 November and may still ask for objects instead. N2.4 builds the twenty new
    entrances to this standard; the Warehouse's radio and ember entrances are brought up to it in the same
    package.
31. Package A4 (choice art) is merged: `ChoiceProps.tex_in(name, map_id)` picks `assets/run/choice/<set>/`
    by the map and falls back to the shared files. A new map gets its door set by a line in `SETS` in
    `src/run/choice_props.gd` and a set in `tools/run/make_choice_art.py`; a world package that adds a map
    asks stream A for the set and does not draw its own door.
32. The spike of ruling 20 is closed: **the Bassment stays outside the port.** Its entry at the lap's lock,
    its passages and its return to the checkpoint are committed by the router outside `switched`, and a
    Bassment change is always a `cut` through the engine. The director does not accept "bassment/*". The
    music stream gives a scene entered without a lock (the return from the Bassment) the same aligned
    start as a scene entered through a lock.
33. Packages A1 (shared stage look) and W1 (Warehouse) are merged. The world packages tune light against
    A1's values (`docs/shots/art/a1/frame_check_after.txt`): the post shader is always on, black is lifted
    to the sector's fog colour, people are capped at 1.25x their sheet. A1's change to
    `tests/test_story_crowd_world.gd` (two checks that assumed the old near fade) is accepted.
34. Merged on 7 November: A3, A5, W4, W9, N2.2, M2.4, A6 (wall decals: a wall-mounted thing is a `decal`,
    a free-standing one a billboard; `docs/art/WALL_DECALS.md`), W7 (Squadron), N2.4 Hell. The daylight rule
    for world packages: daylight exteriors are not dimmed to hit a median; p50 at or under 0.42, p95 0.68 to
    0.78, p5 at or under 0.14, blown under 0.5%. `tests/test_heralds_view.gd` projects points only and does
    not see walls or the crowd: every entrance package checks its shots by eye for occlusion.
35. **The owner's direction of 7 November, game-wide:** (a) **more moments with the camera relatively
    stationary**: the rail arrives at a choice viewpoint and holds there, still, for the choice window, and
    journeys are paced with holds, not continuous drift; (b) **the red and green rings go**: a choice's
    state (available, selected, committed, and the cost of a wrong one) is shown by the artwork itself and
    how it is animated and changes (a door that lights and opens, a figure that beckons or steps aside, a
    lamp that changes colour, a floor that glows under the thing), never by a routine uniform symbol drawn
    over the world. This applies to the legacy campaign's hotspots and marks as much as to the Doom scenes
    and the raves. The contracts (rail, choice states) carry it; a dedicated art and engine package (A7,
    Opus) replaces the rings in the existing worlds; the shoot sheets stay as the proof.
36. **The art standard (owner, 7 November).** The concept paintings in `art/reference/doom_worlds/` and the
    four in `art/reference/standard/` are the bar for all art polish: dense pixel painting, dithered highlights,
    wet reflections, warm practical lights against cool ambience, every surface drawn, no flat fills. The
    **sprite standard is `art/reference/standard/guide_floor_sprite_standard.png`** (the Floor guide: braids,
    hoop earrings, magenta sequin top, silver sequin trousers, gold bangles): game sprites are drawn to that
    density and finish, with sequins and skin shading dithered, readable costume colours and silhouette, a
    face with an expression. For a 1.8 m figure at the style guide's 128 texels per metre that is a sheet
    about 230 px tall (256 px sheets), not the 128 px figures of today; the figure cap of 1.25x still holds.
    This governs the Doom scenes' guides, the raves' customers and guides, and the people re-bake (A2) of the
    legacy worlds. Placeholder figures are called placeholders in every report.
37. **Decisions on the contracts' open questions** (`docs/parallel-development/CONTRACTS.md`, merged into
    `feature/shared-contracts`): the bass knob runs in rhythm mode (pads stay live); leaving the bedsit goes at
    the next block boundary; race wins carry across runs; **race energy loss never ends the run** (penalties
    are bounded and only slow the car); save VERSION 3, the loader accepts 2 and 3 (an older build sets a v3
    save aside: the owner is told); the opening is its own path `content/paths/bedsit`; the race is an
    activity with a stage swap. The stem lock in `stem_transport.gd` (H7.0) is accepted as the contracts
    agent built it. The remaining hooks H1 to H9 in CONTRACTS.md are lead-owned engine work, built by the
    engine agents in the order the pilots need them: H5 (suspend/resume, tap owner, controls layer), H6
    (save), H3 (holds), H1 (threshold walk, relaxed node), H7 (song-time unlock), H4, H8, H9.
38. **One world, one HUD (owner, 8 November).** Every minigame and activity (the cloakroom, the bar, the
    bass knob, the race's start and finish, the card table, anything later) takes place in the same 2.5D world
    the rhythm game is played in, and the transition between the two is seamless: no scene change, no fade, no
    separate screen, no close-up card or panel laid over the room. The camera walks to the activity's spot
    along the rail and holds there (ruling 35a); the room keeps rendering with its crowd, lights, haze and
    music; the activity's things (the counter, the coat rail and coats, the glasses and the shelf, the deck and
    its knob, the customers and the attendant) are objects in the room, drawn by the stage at their depth,
    in the room's light and tint, with the pixel density of the style guide, and their state (a coat handed
    over, a glass filling, a knob freed, a customer's reaction) is shown by those objects' frames and motion
    (ruling 35b). The HUD is the run's own HUD throughout: the same meter, pips and pause button; the pad
    strip is where the activity's controls appear, in the pads' own slots, morphing in at the bar boundary
    the activity starts on and back into pads at the boundary it ends on (contract 5), drawn in the pads' frame
    style with pictograms and no words. The only canvas-layer drawing an activity may add is in that strip and
    small in-world feedback attached to its objects (a tick or cross that flashes on the tag, a glow on the
    counter). Contract 10 carries this; engine package A8 (Opus) builds the dynamic props API (H8.1) and the
    pad-strip controls' morph; the card table (blackjack), built earlier as a 2D close-up layer, is converted
    to the same staging in its own package (A8b) rather than kept as an exception.


39. **A geography guide's tap is the decision; the walk is the leg the scene authored** (8 November, lead).
    In a Doom-geography world (contract 1, H1.6: one scene per world, routes straight to the other worlds'
    entry scenes) the choice viewpoint holds still through the window as ruling 35 asks, but the first tap
    on a guide whose route leads to another world commits at the tap's own beat: that guide goes committed,
    the others declined, later taps in the window are ignored, and the threshold walk starts then along the
    route's authored polyline with its hold at the doorway (2 to 4 bars; cut to end on the boundary when the
    tap comes late). An untouched window keeps the default at the lock and the 3-beat walk. The tap commit
    is a success whatever the rhythm (as a quest entrance, ruling 15); the window hold gives way to the walk
    (StoryPlayer.end_window_holds). Built on wip/engine-geography; tests/test_geography.gd.

40. **The card table's mode: `replace`, kept as built (owner, 8 November).** A8b runs blackjack in `replace` mode (judging suspended while
    seated, no wobble or fall, the run cannot end at the table, getting up finishes on the resume boundary),
    because under ruling 38 the pad slots carry the four card controls and cannot also be the rhythm pads.
    That overrides the owner's decisions B6/B7 (`rhythm`: the pads keep you on the chair). The alternative
    that keeps B6/B7 is controls as in-world touches (the deck = twist, the chips = bet, the dealer = stick,
    the door = up) with the pads staying rhythm. The owner chose to keep it as built: while seated the pads
    are the card controls and judging is suspended; B6/B7 are superseded for the card table (contracts 4/5:
    blackjack is `replace`).

41. **How the opening ends (lead, 9 November; the owner may overrule).** The bedsit's way out (`bedsit.way_out`
    → `bedsit.end` → the Warehouse) opens once any ONE rave's three activities are done in the save
    (`raves.<theme>.bass_fixed`, `cloakroom_done`, `bar_done`); a visit alone does not open it; once open it
    stays open and the other raves stay reachable. This follows the brief (line 279: the player does not have
    to visit all four flavours to complete the opening) and replaces the raves agent's stand-in that needed
    all four `bedsit_been_<theme>` flags.

42. **Walk-outs at a walking pace (lead, 9 November; the owner may overrule).** The walk from the tap along the
    authored leg (ruling 39) takes as long as the leg needs at no more than 3 m/s: bars = ceil(length / 3 m/s /
    bar length), clamped to 2..8 bars; the doorway hold and the cut are unchanged; the music keeps playing. A leg
    longer than 8 bars allows at 3 m/s (about 33 m at 174 bpm) is the scene's fault: shorten it or add a hold.
    The review found 2–4 bar walks over 17–28 m legs (5–7 m/s), which read as a sprint in a 2.5D world.

    **42b (lead, 9 November, after the engine package; the owner may overrule after playing).** From a tap at beat 50
    only about 3.5 bars remain before the phase boundary, so a paced walk over a leg longer than about 14.5 m cannot
    reach its doorway by the drop. Accepted for the first playable: the next phase and its music start on time; the
    player keeps walking in the old world at walking pace; the world swap happens when the hold ends, on a whole beat,
    never later than beat 32 of the next phase; the arrival is done before that scene's window. The picture therefore
    cuts after the drop on long legs. Scenes should author legs short enough that the swap lands near the drop where
    the painting allows; `check_rail_paths.gd` prints each leg's pace and bars (WALKOFF lines). If the owner prefers
    the cut always on the drop, the alternative is a mid-leg cut at the boundary with the doorway hold dropped.

43. **The rail check measures the worst case (lead, 9 November; the owner may overrule).** The engine starts a paced
    walk-out from the place the rail stands on at the tap (`rail.place()`: home, or the good or bad place reached by
    the blocks passed), not from the `"choice": true` viewpoint. `check_rail_paths.gd` therefore measures every
    walk-out from every place the rail can stand on and reports the longest leg (`WALKOFF ... from <place> (worst case of
    <n> rail places; choice place <wp>)`); its bars, pace and the > 8 bars warning use that worst case. A scene whose
    home or bad-place leg is too long adds a hold or shortens the leg; the check is not softened to the choice place.
