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
