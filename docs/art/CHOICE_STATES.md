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
