# Face polish: the Story people's faces

Branch `feature/face-polish`. The faces of every baked Story person (the five 2.5D chapters: `night_one`, `mothership`, `underworld`, `hospital`,
`mental_hospital`) were redrawn in the pixel rig. Code: `tools/story/art/people.py` (head, face, skin ramp), `tools/story/art/wardrobe.py` (face traits and
face colours per actor). Tool: `tools/story/face_sheets.py` (zoomed head sheets). Everything else (the sheet and atlas format, `MATS`, frame anchors, the
shader, GDScript) is unchanged.

## What changed

- **A real head size.** The head is 1/6.8 of the height (it was 1/7.5; the art direction asks 1/6.5 to 1/7): 17 x 13 pixels at the full size instead
  of 15 x 11, enough room for a face. The head centre is snapped to the pixel grid so a front face is symmetric and every feature lands on whole pixels.
- **The face is a pixel decal.** Features are placed as whole pixels in the head's own frame (`Painter.put_decal`): a tilted head carries its face with no
  holes or doubled pixels, and only the head's own skin is painted.
- **Eyes.** An upper lid / lash line, the white (darker in the outer corner), an iris in the actor's own eye colour (the spare `extra` slot, which people
  never used), a lower lid under a wide eye. Lashes vary per actor (light, normal, heavy with a flick past the outer corner). Eye shapes vary (almond,
  round, hooded). Moods: a smile lifts the lower lid; a cheer widens the eyes; sad droops the outer lid; eyes closed to the music show a dark lash line
  with the lit lid above it; closed in a cheer they arc up in a smile ("bliss"). Eye colour: browns for dark skin, browns, hazels, greens, blues and greys
  for light skin.
- **Brows** with a shape per actor (straight, arched, thick, thin, angled) and emotion: raised in a cheer, the inner end up when sad, a little up when the
  eyes close to the music; raised one row above glasses.
- **Nose** per actor (button, straight, wide, long, hooked): the lit tip, the shadow side and the underside with nostrils in front; in the three-quarter
  view it points into the turn with its shadow on the far cheek.
- **Modelling in clean planes** instead of dithered noise: the face's skin is not dithered; a lit nose bridge, lit cheekbone, the socket by the bridge,
  the cheek turning away, the hollow under the cheekbone (for strong cheekbones and elders), the jaw and a lit chin; in the three-quarter view the side of
  the head is its own lit plane with the jawline under it. Jaw width, chin (round, square, pointed) and head width (11 or 13 pixels) vary per actor, so
  faces differ in shape, not only colour.
- **Skin**: a skin ramp of its own (`people.skin_ramp`): warm, slightly more saturated shadows (blood under the skin), never grey or violet, with an
  undertone per actor (warm, neutral, olive, cool). Blush/ruddiness (`skin2`) and lips (`mouth`) are mixed from the actor's own skin tone, so a dark skin
  gets deep plum lips and a subtle flush and a light skin rose lips and a pink flush; some ravers and residents wear lipstick. Sclera and teeth are tinted
  towards the skin so they do not glare.
- **Mouths**: the line between the lips with a lower lip catching the light (full and wide lips have a cupid's bow / wider mouth), a smile curling up at
  the corners with smile lines, a laugh in a cheer (upper lip, teeth, the dark mouth, the lower lip), singers who open their mouth in an O when the head goes
  back to the music in the dance, a sad mouth turned down with a puckered chin.
- **Ears** with a lit rim and a shadowed bowl; **beards** in the hair's colour along the jaw, up the cheeks to the sideburns, lit at the upper left, with
  the lips showing through; moustaches; stubble as a jaw shadow with a few hairs; freckles; crow's feet, bags and smile lines for elders.
- **Glasses**: a frame bar on the lid line, the sides and (square) a lower rim, wire (metal) for round frames, a glint on the rim; the eyes stay visible.
  Shades: dark lenses with a sharp glint. In the three-quarter view the far lens shortens and the arm runs back to the ear.
- **Species**: greys get big slanted almond eyes with catch-lights, nostrils and a small expressive mouth; the cyclops one great eye with white, ringed
  iris, pupil and catch light, a heavy lid and brow; insects faceted compound eyes and mandibles; blobs round eyes with catch lights and a wide mouth;
  skeletons sockets with a glint, a nasal cavity and a row of teeth; demons the human face with a hot amber sclera, heavy lashes (fiends, queens), a heavy
  brow ridge and tusks (brutes); aliens' lips are a dark version of their skin.
- **LOD 2 and 4**: the half-size head keeps two eyes, brows when they move, a nose shadow, a mouth that differs per mood (closed, smile, laugh with
  teeth, sad), blush; the quarter-size head keeps two eye shadows and an open mouth when shouting.
- **Hair**: the mohawk's crest no longer runs down the middle of the face (it stops at the hairline in front, at the nape behind); a ponytail covers the
  back of the head in the back view.

The face traits come from a random stream of their own (`wardrobe._face_detail`, the actor's seed with a salt), so no actor's clothes, hair or build
changed.

## How to rebuild

```
python3 tools/story/build_assets.py night_one people
python3 tools/story/build_assets.py mothership people
python3 tools/story/build_assets.py underworld people
python3 tools/story/build_assets.py hospital people
python3 tools/story/build_assets.py mental_hospital people
python3 tools/story/figure_sheets.py                  # docs/shots/story/figures_<chapter>.jpg
python3 tools/story/face_sheets.py after              # docs/shots/faces/<chapter>_after.jpg (any tag)
```

then `godot --headless --path . --import` once.

**Merging**: the sheets (`assets/story/<chapter>/people/*`, and the `people.pages` list in a chapter's `manifest.json` when the page count changes) are
generated. On a conflict, do not merge them: take either side, then rerun the five `build_assets.py <chapter> people` commands above on the merged code and
commit the result. The code change and the regenerated assets are separate commits for this reason.

## Proof

Before/after head sheets (8x, unlit; columns neutral, happy, cheer, sad, three-quarter, back, LOD 2, LOD 4):
`docs/shots/faces/<chapter>_before.jpg` and `docs/shots/faces/<chapter>_after.jpg` for the five chapters. Figure sheets: `docs/shots/story/figures_*.jpg`.
In-game crowd shots (a windowed `story_play` run on the virtual clock, perfect play; bars 107, 10 and 47.5), before and after:
`docs/shots/faces/ingame_crowd_{peak,dancer,circle}_{before,after}.jpg`, and `ingame_<shot>_zoom_before_after.jpg` (the crowd band at 2x, before above,
after below). `docs/shots/faces/.gdignore` keeps Godot from importing these large JPEGs.

### Sheet sizes (page PNGs, bytes)

| chapter | before | after | pages |
| --- | --- | --- | --- |
| night_one | 3,158,604 | 3,148,136 | 6 (6) |
| mothership | 9,081,037 | 8,988,941 | 18 (18) |
| underworld | 8,670,665 | 8,595,585 | 19 (19) |
| hospital | 8,272,618 | 8,228,798 | 15 (16) |
| mental_hospital | 9,225,477 | 9,192,245 | 17 (17) |
| total | 38,408,401 | 38,153,705 | 75 (76) |

The unique frame count is the same within a few frames (for example Night One 7539 -> 7538): faces are already part of the frame key, so no new frames
were added. The hospital's last page (a 10 KB sliver) no longer exists, so `assets/story/hospital/manifest.json` loses `people/page_15.png` from its
`people.pages` list and `page_15.png(.import)` are deleted; that manifest line is a generated output of `build_assets.py hospital people`.

### Checks

- `python3 tools/story/check_assets.py --determinism` (with `GODOT` set, after a `--import`): every chapter OK, determinism OK, manifest check OK. Note: the
  full rebuild it runs also rewrites the chapters' `processed/` and `textures/` PNGs with bytes that differ from the committed ones on this machine
  (not related to the people); those were restored with `git checkout`, not committed.
- Story tests: `godot --headless --path . -s tests/run_tests.gd -- --filter story`: 28901 checks, 0 failures. No test asserts people pixel counts or sheet
  sizes, so none needed changing.

### Left undone / doubtful

- At the full size an iris is one pixel: the eye is lid, white, iris (a pupil and a catch light inside the iris would need a bigger head). The cyclops and
  the greys, with bigger eyes, do get the pupil and catch light.
- The three-quarter view is mirrored by the runtime for the left turn, so a left-facing person is lit from the right on the face (as the bodies always were).
- Hair over the brows (fringes, hat brims) hides the brows' expression for those actors; that is deliberate, but their mood then rests on eyes and mouth.
- Singing (an open O) is shown on dance frames with the head tilted back, for the actors with the singer trait; no new frames are baked for it.
