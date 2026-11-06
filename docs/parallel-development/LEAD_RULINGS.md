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
