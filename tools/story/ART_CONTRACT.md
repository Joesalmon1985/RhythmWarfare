# Story Campaign art contract (Night One)

The art generator (`tools/story/build_assets.py`) and the Godot runtime (`src/story/`) meet at one file:
`assets/story/night_one/manifest.json`. The runtime reads **only** this manifest and the files it names. All file paths in
it are relative to `assets/story/night_one/`. Sources are SVG (written by the script, imported natively by Godot, editable
in Inkscape) in `source/`; Pillow-made PNGs (haze, glows, beams, grain, anything SVG blur cannot do) in `processed/`.
Godot's SVG importer (ThorVG) has **no filters/blur**: use gradients, layered translucent shapes and the Pillow PNGs.
Everything is original, drawn by the script. No OpenRA art, no downloads.

Style: stylised 2D neon vector/cartoon, bold shapes, strong silhouettes, crisp dark-indigo outlines, palette of
indigo/navy shadows, magenta/cyan/violet lights, a few warm amber highlights. Must look like a finished illustrated
indie-game nightclub, not clip art or placeholders.

## Design space

The stage is drawn in a 1280 x 720 design space (16:9), fixed camera = the DJ's eye line over the mixing desk. The bottom
~36% (y >= 460) is covered by the desk/pad strip drawn by the runtime, so the dance floor focus is y 150..440. Author art at
2x (for example a 2560 x 1440 viewBox for the backdrop) and say so with `"px_scale": 0.5` in each entry; the runtime
multiplies the sprite scale by `px_scale`.

## Characters (6 archetypes x 2 variants)

Archetype ids, with distinct hair, outfit, proportions (not recolours): `groover` (tall, spiky hair, tank top),
`ponytail` (crop top, wide trousers, swinging ponytail), `hoodie` (broad, cap, hoodie), `curly` (big curly hair, glasses,
jacket), `bob` (bob haircut, short dress/skirt), `punk` (mohawk, vest, boots, tall). Variants `a` and `b` differ in palette
and a clothing detail. Front view, facing the viewer (they look toward the DJ). Native height about 260 px (feet to top of hair
at px_scale-applied size); head about 50 px.

Rig-space: origin at the feet centre, +x right, **y up is negative** (a head at y -240). `l` = screen-left. The runtime
builds this hierarchy: `hips` > { `torso` > { `head`, `shoulder_l` > `elbow_l`, `shoulder_r` > `elbow_r` }, `hip_l`, `hip_r` }.
`joints` gives each joint's rest position in rig space. Rest pose: arms hang slightly outward, legs straight.

Per variant, `parts` is a list of `{name, joint, z, file, pivot, px_scale, swing?}`:
- `joint` is one of `hips torso head shoulder_l elbow_l shoulder_r elbow_r hip_l hip_r` (the part moves/rotates with it);
  upper arm parts on `shoulder_*`, forearm+hand on `elbow_*`, legs on `hip_*`, `hips` for a skirt/belt that stays at the pelvis.
- `pivot` is the joint's position **inside the texture in texture pixels** (the sprite is drawn at -pivot).
- `z` draws behind (negative) or in front (positive) within one character; typical: back hair -20, legs -10, torso 0,
  arms 5, head 10, hair front 20 (arm parts may use negative z to be behind the torso).
- `swing: true` marks hair/ponytail that gets a lagged pendulum rotation about its pivot.
- `faces`: `{neutral, happy, cheer, sad}` each `{file, pivot, px_scale}` anchored on joint `head`; they carry eyes, brows,
  mouth only (no skin) and must read at 50 px head size: `cheer` is open-mouthed shout/grin, `sad` is a downturned
  withdrawn look.
- `glow_hand`: per archetype `{"joint":"elbow_r","at":[x,y]}` = hand position in the forearm texture px (the runtime attaches a
  glow stick there for some dancers).

Rear crowd silhouettes: `silhouettes`: 3 shapes `sil_a sil_b sil_c`, each with `idle` and `up` (hands raised) files, dark
navy with a thin neon rim light, `pivot` at the bottom centre, `px_scale`. Cheap and simple: head and shoulders.

## Stage set pieces

`stage.design_size` = [1280, 720]. `stage.layers` is an ordered list of back-to-front static layers
`{id, file, pos:[x,y], size:[w,h], px_scale?}` (pos/size in design space). Required layer ids (the runtime also looks them up by
id to pulse or toggle them): `backdrop` (far wall, side walls, perspective floor tiles, ceiling truss, bar, entrance doors in
the closed state, LED screen frame/panel), `speaker_l`, `speaker_r` (stacks flanking the room, drawn *without* the woofers),
`riser` (a low performer platform, back centre, hidden until used by an event but positioned here), `desk_top` (the stretchable
mixing-desk strip, authored 1280 x 260 design px; it is stretched to the pad-strip rectangle and must tolerate that).

`stage.anchors` (design space) required keys: `led_screen` [x,y,w,h] (empty dark panel the runtime paints an equaliser/pattern
into), `doorway` [x,y,w,h], `floor_rows` list of `{y, scale}` from back to front for placing crowd feet and scaling characters
consistent with the floor perspective (4 to 6 rows; the front row `scale` 1.0, feet y <= 440), `floor_polygon` (points of the lit
dance floor), `light_points` list of 8 [x,y] ceiling mount points for moving heads, `woofers` list of [cx,cy,r] for each speaker
cone, `disco_ball` [x,y], `riser` [cx, floor_y, w], `circle_centre` [x,y] and `circle_radii` [rx, ry] for the dance-circle
ellipse on the floor.

Standalone sprites (`sprites` map id -> `{file, pivot, px_scale}`): `woofer` (circle cone drawn to pulse; pivot centre),
`fixture` (moving-head lamp: yoke + lamp pointing straight down; pivot at its mount), `disco_ball`, `glowstick`
(pivot at its grip end), `door_open` (open-door light spill overlay for `doorway`), `spot_pool` (soft ellipse, floor spotlight,
white to be tinted), `haze_a` `haze_b` (wide soft tileable smoke bands), `glow` (white radial), `beam` (soft cone pointing down
from its top-centre pivot, white, drawn additively and tinted), `vignette` (full screen dark edge), `grain` (optional),
`confetti` (small particle quad set, optional), `desk_lip_glow` (illuminated edge trim for the desk top).

Deck pieces for the runtime to place around the pad rectangles (`sprites` too): `pad_bezel` (a square frame that surrounds a
pad, scales uniformly), `platter` (turntable platter with record, circular, pivot centre, rotated on the beat), `knob`,
`fader_slot`, `fader_cap`, `crossfader`, `vu_segment` (one lit segment; the runtime draws meters), `deck_screw`.

## Pose vocabulary (runtime side, for the art to support)

idle/sway, dance (arms swing, knees bend), cheer (arms straight up, jump), disappointed (arms low, head down). The arm parts
rotate about their joint, so upper arm and forearm must each look right at any angle (rounded ends overlapping at the elbow,
no gaps). Legs rotate at the hip and must tolerate +/- 25 degrees.

## Deliverables

`tools/story/build_assets.py` (one command regenerates everything under `assets/story/night_one/`, deterministic),
`assets/story/night_one/manifest.json`, `docs/STORY_ART.md` (provenance, how to edit, style notes), and a
review contact-sheet scene `tools/story/preview_art.gd` / `.tscn` (poses the rigs from the manifest into the four states
and lays out the set pieces) so the art can be looked at with `tools/shoot.gd`. Keep the total assets small (SVG text plus a
handful of PNGs; no huge uncompressed images).
