# Story Campaign chapters 4 and 5: the waking chapters (hospital and mental hospital)

Read first: `ART_CONTRACT.md`, `ART_CONTRACT_CHAPTERS.md`, `ART_CONTRACT_VIEWS.md`, `docs/STORY_ART.md`, and the finished, polished chapters' generator modules
(`mothership_*`, `alien_chars.py`, `uw_*.py`, `chapter_underworld.py`) as the working reference for structure, helpers, manifest shape and quality bar.
Everything in those contracts applies: same rig/face contract, same `stage.sprites` ids, 1280 x 720 design space, the desk strip, `stage.pieces`,
`manifest.interlude`, and the moving camera: **this chapter has `main` plus three extra rooms (`stage.views`) and a `passage_frame`**.

## The story beat

After the aliens or the demons, the player wakes up. It was all a dream, or it was not what it seemed. The set is still a party and still
a drum and bass set played from a deck, but the setting is now an ordinary place and the mood is human. Keep the same friendly stylised
neon-cartoon look as the earlier chapters (bold outlines, readable silhouettes, expressive faces, light colour accents), the setting merely
re-skinned toward plain daylight-and-fluorescent reality with party lighting added on top. No gore, no restraint imagery, no violence, nothing
frightening or mocking: warm for the hospital, gently surreal and kind for the ward.

| chapter | art dir | setting and mood | crowd (6 archetypes x 2 variants) | rooms |
| --- | --- | --- | --- | --- |
| `hospital` | `assets/story/hospital/` | You wake in a hospital bed, a private room with a window of morning light, flowers, balloons and cards, and your loving family around you. Warm, soft, golden and teal; the "disco lights" are fairy lights, a bedside lamp and sunlight, the mirror ball a hanging paper-star lantern. | `mum`, `dad`, `granny`, `kid` (a child with a balloon), `nurse`, `doctor` | `main` = the private room around the bed (the "dance floor" is the open floor at the foot of the bed); extra views `corridor` (a long bright hospital corridor with a nurses' desk and a get-well banner), `cafeteria` (a family lounge with tables, a vending machine and a tea trolley), `garden` (a sunlit courtyard garden with benches, a fountain and bunting at golden hour) |
| `mental_hospital` | `assets/story/mental_hospital/` | You are on a hospital ward, a day room of pastel walls, mismatched armchairs, notice boards and a table of craft supplies, and everyone around you is an eccentric in a costume, gently and affectionately drawn: a ward that is a party of oddballs. Cool mint and lilac fluorescent light warmed by party lights. It must read as a kind, whimsical place and never as a joke at anyone's expense: the costumes are fancy dress, nobody is menacing or ridiculed. | `pirate`, `king` (paper crown and a dressing gown), `chef`, `superhero` (towel cape), `ballerina`, `orderly` (a calm friendly staff member) | `main` = the day room; extra views `corridor` (a long corridor with a trolley and doors with paper stars), `art_room` (an art room with easels, paint pots, hanging paintings and a kiln), `courtyard` (a walled courtyard garden at dusk with raised beds, a washing line of bunting and string lights) |

Archetype ids are fixed (the runtime and the checker rely on them); variants `a` and `b` differ in palette and a clothing detail.

## Build targets

`python3 tools/story/build_assets.py hospital` and `python3 tools/story/build_assets.py mental_hospital` (hooks already registered in `build_assets.py`
and `check_assets.py`: do not edit those; implement `tools/story/art/hp_chars.py` + `hp_stage.py` (+ `hp_views*.py`) and `mh_chars.py` + `mh_stage.py`
(+ `mh_views*.py`); the stub entry modules `chapter_hospital.py` / `chapter_mental_hospital.py` already call `hp_chars.build_all()`,
`hp_stage.build_silhouettes() / build_stage() / build_interlude()` (and the `mh_` equivalents) in the same way as the underworld). Output is
deterministic; Night One and the other chapters' files stay byte-identical.

## Required content (per chapter)

- Everything the chapters and views addenda list: archetypes, the `main` room (layers, anchors, 5 floor rows, light points etc.), 6 to 8
  `stage.pieces`, three views (ids below) each with `backdrop` + `front_frame` layers, the required anchors and 2 to 4 pieces, `passage_frame`
  (a door frame or archway, the camera passes through it), the re-themed deck pieces and the shared sprite ids (`woofer` = a speaker
  or a radio, `fixture` = a lamp/spotlight, `disco_ball` = the paper lantern / a glitter ball, `confetti` = paper confetti or petals...).
- `hospital` rooms: `corridor`, `cafeteria`, `garden`. `mental_hospital` rooms: `corridor`, `art_room`, `courtyard`.
- Pieces (suggested ids, 6 to 8 in `main`): hospital: `window_sunbeams`, `fairy_lights`, `balloon_bunch`, `cards_garland`, `heart_monitor` (a friendly monitor with a heart
  line that pulses), `flower_vase`, `paper_stars`. mental_hospital: `notice_board`, `mood_lamp`, `bunting`, `craft_table`, `wall_clock`, `paper_chains`, `fairy_lights`.
- `manifest.interlude` for the waking cutscenes (composited over the previous chapter's room): hospital `eyelid_top`, `eyelid_bottom`
  (large soft shapes that open to reveal the scene), `white_wash` (full-screen warm white), `monitor_line` (a heartbeat trace); mental_hospital
  `fluoro_wash` (cold mint-white full-screen wash), `tunnel_vignette` (a soft dark tunnel closing in), `cell_door` (a plain ward door frame
  that swings open to reveal the new room, friendly, not a prison door), `flicker_tube` (a fluorescent tube sprite). Give each sprite an entry in
  `manifest.interlude.sprites` with `{file, pivot, px_scale}`.
- Characters: real silhouettes, not recolours; clothing, hair, accessories carry the personality (nurse's cap/scrubs, doctor's coat and stethoscope,
  granny's cardigan and glasses, kid with a balloon; pirate hat and eyepatch, king's paper crown, chef's hat, towel cape, tutu, orderly's scrubs). Faces
  `neutral happy cheer sad` that read at 50 px head size. Swinging parts (`swing: true` + `swing_pivot`) for hair/capes/hats where it helps.

## Quality bar

Real Godot screenshots (display :0, `tools/shoot.gd`, previews like `preview_chapter.gd` / `preview_views.gd`) reviewed with the Read tool until each room is a
finished, attractive, distinct place with believable floors and crowd footing. Keep files sensible in size.
