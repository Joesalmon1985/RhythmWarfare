"""Hand-authored `staging` blocks (docs/CHOICE_CLARITY.md): how an option shows that it is the current choice or not, where the archetype's defaults
(content/run/choice_staging.json, derived from the hotspot's kind and anchor by src/run/choice_staging.gd) are not enough. Keyed by hotspot id, for the main run, the paths and
the Bassment alike; `python tools/run/apply_staging.py` writes them into the shipped hotspot files (run it after any generator rewrites them: make_scenes.py, make_gospel.py,
make_squadron.py, make_ember.py, tools/trial/make_hotspots.py). Every block is validated by HotspotContract (ChoiceStaging.validate).

A block may name: archetype (person | door | object | feature | figure | custom | none), actor, current / other / touched / committed / declined (a person's act specs), door
(drawn | bars | pieces | none), open_piece / shut_piece, door_at [x, z], width_m, height_m, lamp (bool), lamp_y, current_tex / other_tex / thing / current_motion / other_motion (a billboard),
touch {w, h}, states {current|other|touched|committed|declined: [step, ...]} (see ChoiceStaging).
"""

WIZARD = {"archetype": "figure", "current_tex": "wizard_happy", "other_tex": "wizard_sad", "current_motion": "beckon", "other_motion": "slump", "touch": {"w": 1.4, "h": 2.0}}

STAGING = {
    # --- the pilot: the Warehouse ---------------------------------------------------------------------------------------------
    "warehouse.wizard": dict(WIZARD),
    "warehouse.chill.wizard": dict(WIZARD),
    # the floor's exits are points 1.2 m inside the room: the drawn door stands in the wall's opening (the bar's at x 7, the balcony stairs' at x -7)
    "warehouse.exit_bar": {"door_at": [6.85, 2.0]},
    "warehouse.exit_balcony": {"door_at": [-6.85, 1.75]},
    # --- the pilot: the Gospel, J04 Calling the Fishermen ------------------------------------------------------------------------
    # Simon (f1) invites you to his boat; when the boat is the current choice its two men there wave you aboard too
    # --- the pilot: the Bassment --------------------------------------------------------------------------------------------------
}
