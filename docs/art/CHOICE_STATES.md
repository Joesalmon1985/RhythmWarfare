# Choice states without rings (package A7)

Lead ruling 35 (b), the owner's direction of 7 November 2026: the red and green rings go. A choice's state (available, selected, committed, and the cost of a
wrong one) is shown by the artwork itself and how it is animated and changes: a door that lights and opens, a figure that beckons or steps aside, a lamp that
changes colour, a floor that glows under the thing. Never a routine uniform symbol drawn over the world. Contract 9 (`docs/parallel-development/CONTRACTS.md`)
carries the states; this package replaces the rings in the existing worlds.

## What draws a ring today

The inventory before A7 (line numbers of `feature/shared-contracts` at `04cd0d7b`). Every abstract marker drawn for a hotspot or a herald, what it says, and the
tests that pin it. "Crisp" is `HotspotView._draw` (the canvas over the picture); "light" is `HotspotView._draw_light` (the additive `Light` child).

### `src/run/hotspot_view.gd`

| Where (file:line) | What is drawn | State it conveys | Pinned by |
| --- | --- | --- | --- |
| `:32`-`:33` `CURRENT_COL`, `OTHER_COL`; `:508` `_colours_of` | every ring, pool and shaft of a staged option green or red | current choice (green) vs any other option (red) | `test_hotspots_view.gd` `test_a_staged_option_is_lit_by_its_role_and_keeps_to_the_floor` |
| `:529` `_is_default` | the doubled ring | the default / the current option | same test |
| `:760`-`:763` `_draw_marks` available | a thick ring on the floor round the anchor, dark pixel outline | available | `test_interaction_model.gd:139` (the ring's circle is the touch target of a hotspot with nothing drawn) |
| `:764`-`:765` | a second ring inside | the default (or the current option) | `test_hotspots_view.gd` (via `_is_default`) |
| `:766`-`:769` | a ripple leaving the ring on every beat | available (alive, touchable) | none |
| `:770`-`:779`; light `:666`-`:672` | the crown: a ring of light round the portal and three motes circling it | a finished path's portal (plan D10) | `test_hotspots_view.gd` `test_a_finished_portal_keeps_its_own_tint_and_the_crown_look` |
| `:780`-`:787` | a glowing crack drawn on the floor | `look.available: crack` | none |
| `:789`-`:792` selected | the ring white-hot (a staged option: its role colour), thumping on the beat | selected | none |
| `:793`-`:795` | a second ring closing in at the touch | the moment of the touch | none |
| `:796`-`:802`, `:805` | four motes circling the ring once a bar; a mote lifting | selected | none |
| `:808`-`:812` committed | the ring bursting outward (FLASH_S), then a calm ring fading (SETTLE_S) | committed | `test_hotspots_view.gd` claim test (draw count) |
| `:1005` `_marks_refused` | a cold dark pool, the ring broken into falling segments, a dark wash round the picture | refused (a tap in the lock) and the card table's waved-off claim | `test_hotspots_view.gd` claim test |
| `:635` `_light_entry` `:665`, `:680`, `:688`-`:689` | a glow over the thing itself | available, selected, committed (unstaged hotspots only) | none |
| `:690`-`:693` | the glow pool: a disc of light on the floor, brighter at its heart | every state | none |
| `:703`-`:712` | a shaft of light rising from the pool, motes riding up it | available, selected (unstaged only) | none |
| `:713`-`:732` | a lit slit standing in the doorway and its spill toward the player (`look.available: open`) | a door ajar (unstaged only) | none |
| `:816` `_draw_edge`; light `:847` `_light_edge` | the corner glow: a ring, ripple and core at the picture's edge, a leak of light along the border and a half-sun | a hotspot out of sight, on the side it lies | `test_hotspots_view.gd` `test_an_anchor_out_of_sight_is_a_beacon_at_the_edge_that_can_still_be_touched` (layout only), `test_interaction_model.gd:135` (edge target 88 px) |
| `:606` `_draw_reaction`, `:627` `_light_reaction` | a ring bursting out of a reactive object (flare), a ring thumping twice (pulse), a thin ring (shake, squash) and a flare glow | a reactive object's reaction | none (the reaction itself is pinned in `test_interaction_scene.gd` by state) |
| `:936` `_light_claim`, `:969` `_marks_claim`, `:1032` `_claim_countdown`, `:1046` `_claim_pips`, `:897` `_frame_wash` | the card table: floor pools, a breathing ring with a halo, a white thumping ring, a countdown ring closing in, four lamps lighting on the last four beats, rings flying out, a warm or dark wash round the whole picture | free, touched, seated, waved off | `test_hotspots_view.gd` `test_the_claim_look_draws_selected_committed_and_refused_with_reduced_and_high_contrast`, `test_only_the_card_table_takes_the_claim_path...` |
| `:1199`-`:1202` (`ChoiceStaging.lamp_of`, `choice_staging.gd:140`) | the choice layer's lamp over a door, object or feature: `lamp_go` (round green lens with an up chevron) or `lamp_stop` (square red lens with a bar) | this way / not this way (the route door open, or the current option) | `test_choice_clarity.gd` `test_lamps_and_doors_use_shape_as_well_as_colour`, `test_the_warehouse_floor_stages...` (`lamp_stop`), `test_the_choice_state_is_the_same_at_any_frame_step` (`lamp`) |

### `src/story/story_heralds.gd` (the quest entrances, ruling 30)

| Where | What is drawn | State it conveys | Pinned by |
| --- | --- | --- | --- |
| `:217`-`:229` `_make` (`HeraldMark_<id>` prop) and `:287` `_draw_mark` `:322`-`:327` | the quest's mark: a small lit sign in the quest's colour over the entrance, with a soft halo on the wall behind | "this is a quest entrance" (every state alike; it swells on the beat) | `test_heralds.gd:29` (the art has a mark), `:151` (the mark is a prop of the crowd); `test_heralds_view.gd` (the mark's top is a point the camera must hold) |
| `:303`-`:310` | the pool: the quest's colour on the floor round the entrance | on offer (every state alike) | none |
| `:312`-`:320` | the gate: a lit doorway (`gate: true`), its glow | on offer (every state alike) | `test_heralds.gd:85` (validation only) |
| `:277`-`:280` | the herald's own glow frames, pulsing | on offer | none |

### Elsewhere

| Where | What is drawn | State | Pinned by |
| --- | --- | --- | --- |
| `tools/run/returns_common.py:95` | the return door's `lamp_go` prop (the round green chevron lamp) over the Warehouse door in every scene of a quest path | "this way home" | none |
| `src/run/hotspot_contract.gd:21` `LOOK_SELECTED ["ring", "claim"]` | the data word for the ring | selected | the validator |

Nothing else in `src/` draws an abstract marker for a choice (`draw_arc`/`draw_circle` appear only in the duel, the story result and the characters' own effects).

## The states (package A7)

`HotspotView.RINGS` (`src/run/hotspot_view.gd`) is the one switch for the old look; it is `false`. With it off the view's canvas draws nothing for a choice
(`drawn_kinds` stays empty), the heralds draw no mark, no go/stop lamp stands in the world, and a choice out of the picture has no beacon and no touch target.

**State machine** (`src/run/choice_state.gd`, `ChoiceState`), from the run's own events (`RunPlay.choice_state` / `TrialScene.choice_state` and the hotspot items):

| Event | State | Stamped with |
| --- | --- | --- |
| staged (on offer this visit), not the current choice | available | the event that made it so (a touch elsewhere) |
| the current choice: the touched one, else the scene's default | selected | the touch's song time (`touched[id]`): the next frame shows it, inside 0.1 s |
| the lock passed (no final-window choice in the items any more; `window_closed` when the snapshot carries it) | the others declined, the pick stays selected | the frame's song time |
| the commit at the boundary (as today: `RunHotspots.commit_final` at the lock) | committed (success) or cost (a failed outcome); the others declined | the commit's song time (`changed_t`) |
| no longer staged | idle (forgotten) | |

A refused tap (the lock) is not a state: the option shakes and its lamp flickers red for `REFUSE_S`.

**Data** (`src/run/choice_show.gd`, `ChoiceShow`; defaults `content/run/choice_show.json`). Every hotspot row carries a `show` block, written by
`tools/run/apply_staging.py` (called by `make_hotspots.py`; the returns by `returns_common.py`) from the archetype its row gets by default, so nothing is
hand-authored:

```json
"show": {"archetype": "door"}
"show": {"archetype": "figure"}
"show": {"archetype": "object"}
"show": {"archetype": "door", "set": "warehouse"}
```

The full shape a block may give (merged over the archetype's defaults, a state key by key, its light key by key; validated by `ChoiceShow.validate` from
`HotspotContract`):

```json
"show": {
  "archetype": "door | figure | object | none",
  "light": "lamp | self | gate | none | <thing id of the map>",
  "floor_light": "spill | pool | none | <thing id of the map>",
  "set": "<choice art set that wins over the map's>",
  "states": {
    "<idle|available|selected|committed|declined|cost>": {
      "frames": ["door_2"], "frame_beats": 0.25, "over_s": 0.25,
      "motion": "still|bob|beckon|slump|pulse|sway_left|sway_right|lean|step_aside|shake",
      "light": {"floor_glow": 0.55, "lamp": "off|dim|lit|open", "tint": "#ffe0a0"},
      "sound": "choice_door_open"
    }
  }
}
```

The door defaults (`content/run/choice_show.json`):

| State | Frames | Lamp | Floor | Tint | Motion | Sound |
| --- | --- | --- | --- | --- | --- | --- |
| idle | door_0 | off | 0 | | still | |
| available | door_1 (ajar) | lit | 0.18 | warm #ffc27a | still | |
| selected | door_2 (swung open) | open (eases up over 0.25 s) | 0.55 | #ffe0a0 | still | choice_door_open |
| committed | door_3 (wide) | open | 1.0 (light spilling) | #fff2d6 | still | choice_commit |
| declined | door_1, door_0 over 0.25 s | off | 0 | | still | choice_door_shut |
| cost | door_1, door_0 over 0.25 s | dim, flickering for 2 beats | 0 | red #ff4a30 | shake | choice_cost |

A figure: available `beckon`, selected `step_toward`, committed `gesture`, declined `step_back`, cost `recoil` (a person of the room plays the acts the choice layer
already bakes for them: beckon happy, nod, cheer, plead; a billboard figure its `current_tex`/`other_tex`; a herald its gesture loop, the point held with a step
toward, a step back into the dark, a recoil). An object: its own sprite (`self`), its own light pulsing (available), brighter (selected), held (committed), dimmed
(declined), flickering red with a shake (cost). A quest entrance with a herald is a door whose lamp is its gate's light and whose floor light is its pool.

The lamp is `lamp_lit` (new art, every set: `python tools/run/make_choice_art.py --only lamp_lit`): the world's own lamp fixture with a plain round lens and no
symbol, tinted by the state. A thing of the map takes a `light` multiplier through `StoryWorld.thing_pose`.

**Sounds.** The run has no sfx player for taps. Each state change with a sound emits `HotspotView.cue(sound, hotspot, state, t)` and logs it in
`HotspotView.cues`; the ids (`choice_select`, `choice_door_open`, `choice_door_shut`, `choice_commit`, `choice_cost`) have no audio files yet.

**Touch targets.** Unchanged API (`HotspotView.layout(..., rects)`, `hit`, `touch_rect_of`): the art's projected bounds (a drawn door, a gate, a person, a thing)
plus at most 24 px, at least 88 px, inside the picture. A quest gate's target is the gate's bounds; a return door's the door's. An entry with nothing drawn keeps
its 88 px circle. With RINGS off an anchor out of the picture is not laid out.
