"""The Ember Road's art list (docs/THREE_PATHS_AND_FACES_PLAN.md section 6): the four maps' textures, with what each one is and how it is used.

This is the contract between the map authoring (tools/story/ember_maps.py names these ids and nothing else) and the procedural texture drawing
(tools/story/art/tex_ember_tiles.py and tex_ember_things.py, built on pixeltex.py). Each entry: id -> (kind, px size, metres per repeat, brief).

kinds: floor / wall / ceil (opaque, tileable, 64 or 128 px square, RGB); sky (a 256 x 64 strip that wraps once round the world, horizon at the bottom edge);
       thing (a 128 x 128 RGBA billboard with HARD alpha, the prop standing on the bottom edge of the canvas, as tex_bassment.PROPS / tex_underworld.Sprite);
       piece (a thing that the run switches on and off: soft or hard alpha, 128 x 128 or 256 x 128, may be wide).
`anim` marks surfaces the map animates (scroll, pulse): draw them so a scroll along +u (floors/water) or a pulse of brightness reads as water / glow.

Art direction (original; no ring, no eye, no known-land imagery; no text on anything): hand-spun wool, leather and timber in the Hollow; white and silver in the Birch Hall; black-blue and
a single cold light in the Deep Halls; teal and bioluminescent green in the marsh; ash-grey and red under a smoke sky in the ash lands; black water and a white shaft at the Spring.
The Ember is the only warm light east of the ford. The Glass Mountain is a black cone of obsidian with a single red vent.
"""
from __future__ import annotations

# palette hints per map (dark to light), for the drawing code
PALETTES = {
    "orchard": "deep greens, harvest gold, amber lamplight, warm brown timber; the ford is blue-black with silver water",
    "birch_hall": "white, silver, pale grey-blue, birch-bark white with dark marks; the pass is snow and slate",
    "deep_halls": "black-blue, wet slate, one cold white-cyan light; the falls are black rock, white water and mist",
    "ash_land": "marsh: teal and bioluminescent green on black; wall and stair: black stone and bronze; plain: ash grey and dull red; mountain: red rock lit from within, black pool, white shaft",
}

ARTS = ["orchard", "birch_hall", "deep_halls", "ash_land"]

# ---- surfaces ---------------------------------------------------------------------------------------------------------------------------------

TILES: dict = {
    "orchard": {
        "floor_grass": ("floor", 64, 3.0, "trodden orchard grass, fallen gold-brown leaves and windfall apples, dither of deep green and harvest gold"),
        "floor_lane": ("floor", 64, 2.5, "packed dirt lane with small stones and cart ruts, warm brown"),
        "floor_ford": ("floor", 64, 3.0, "shallow river water over pebbles at night, blue-black with silver ripples (anim: scroll)"),
        "floor_bank": ("floor", 64, 3.0, "wet river mud and pebbles with reed stubs, cold dark green-brown"),
        "floor_boards": ("floor", 64, 2.0, "worn oak floorboards of an inn, warm brown, spilled-ale stains"),
        "floor_flags": ("floor", 64, 2.5, "irregular stone flags by a hearth, soot-dark with warm firelight in the cracks"),
        "wall_hedge": ("wall", 128, 3.0, "dense hedge of dark green leaves with a few red haws and bramble"),
        "wall_cottage": ("wall", 128, 3.0, "whitewashed wattle and daub between dark timber frame, some plaster flaking, warm evening light"),
        "wall_fence": ("wall", 64, 2.0, "low split-rail orchard fence and drystone base, weathered grey wood"),
        "wall_reeds": ("wall", 128, 3.0, "tall dark river reeds and willow-herb in the dark, blue-green, a few silver highlights"),
        "wall_inn": ("wall", 128, 2.5, "inn wall: dark oak panelling to shoulder height, smoke-yellow plaster above, hung with a few pewter mugs and herbs"),
        "wall_inn_door": ("wall", 128, 2.5, "a heavy plank door with iron strap hinges and a ring, warm lamplight under it"),
        "wall_inn_window": ("wall", 128, 2.5, "small leaded windows in an inn wall, black night outside, one lit pane, a faint pale shape crossing it is NOT drawn (that is a separate piece)"),
        "ceil_beams": ("ceil", 64, 2.5, "dark smoke-stained oak beams and plaster between, hanging herbs"),
        "ceil_stars": ("ceil", 128, 6.0, "a black night sky with scattered small stars, a few thin cloud streaks (used as a ceiling tile)"),
        "sky_dusk": ("sky", 256, 1.0, "harvest dusk: indigo at the top, violet, then amber and gold at the horizon (bottom edge), low thin clouds, a few early stars at the top"),
    },
    "birch_hall": {
        "floor_birch": ("floor", 64, 2.5, "pale polished birch parquet with thin silver inlay lines, white-grey, very clean"),
        "floor_snow": ("floor", 64, 3.0, "trodden snow, blue-white with grey footprints and ice glints"),
        "floor_snow_rock": ("floor", 64, 3.0, "slate rock showing through patchy snow, blue-grey"),
        "wall_birch": ("wall", 128, 3.0, "a wall of white birch trunks side by side: white bark with dark horizontal marks, silver highlights"),
        "wall_hall": ("wall", 128, 3.0, "white lime-plaster hall wall with a pale-silver frieze of birch leaves running across it, cool grey shadow"),
        "wall_hall_door": ("wall", 128, 2.5, "a tall pale double door of birch planks with silver bands, a thin light under it"),
        "wall_rock_snow": ("wall", 128, 3.0, "a snowy cliff face: dark slate with snow caught on every ledge, blue shadows"),
        "wall_cave": ("wall", 128, 3.0, "dark cave rock with icicles and frost, nearly black, a cold blue edge light"),
        "ceil_hall": ("ceil", 64, 3.0, "a pale vault of birch rafters with white plaster between, cool light"),
        "ceil_overcast": ("ceil", 128, 6.0, "heavy grey-white overcast snow sky with streaks of falling snow (used as a ceiling tile)"),
        "sky_snow": ("sky", 256, 1.0, "a pale overcast snow sky, grey-white with a bluish band, distant dark ridges at the horizon edge"),
    },
    "deep_halls": {
        "floor_deep": ("floor", 64, 2.5, "wet black-blue flagstones, a sheen of water, faint cold highlights"),
        "floor_bridge": ("floor", 64, 2.0, "a narrow stone bridge: dark slabs with worn centre and moss at the edges"),
        "floor_lake": ("floor", 64, 3.0, "perfectly black still water with faint cold ripples, a pale reflection streak (anim: scroll)"),
        "floor_wet_rock": ("floor", 64, 3.0, "wet black rock with white spray and shallow puddles"),
        "floor_boardwalk": ("floor", 64, 2.0, "wet dark planks of a landing stage above a waterfall, white spray, rope-worn"),
        "wall_deep": ("wall", 128, 3.0, "huge dressed black-blue stone blocks, damp, carved with plain vertical fluting (no letters, no symbols)"),
        "wall_deep_arch": ("wall", 128, 3.0, "a tall dark arch recess in the stone with deeper black in the arch"),
        "wall_rock_wet": ("wall", 128, 3.0, "natural wet cave rock, black with glistening streaks and a little pale mineral"),
        "wall_falls": ("wall", 128, 4.0, "the face of a great waterfall seen from the side: falling white water streaks over black rock, mist (anim: scroll downward)"),
        "ceil_black": ("ceil", 128, 4.0, "a vast black cave roof with faint paler stone flecks, almost invisible"),
        "ceil_stars": ("ceil", 128, 6.0, "a black night sky with scattered small stars and a drift of mist (used as a ceiling tile)"),
        "sky_falls": ("sky", 256, 1.0, "night over a gorge: black-blue with many stars, silver mist rising at the horizon"),
    },
    "ash_land": {
        "floor_marsh": ("floor", 64, 3.0, "shallow marsh water between reed clumps, teal on black with tiny bioluminescent green specks (anim: scroll)"),
        "floor_mud": ("floor", 64, 3.0, "black bog mud with sunken planks and green glints"),
        "wall_reed": ("wall", 128, 3.0, "dense dark teal reeds and dead trunks in mist, a few faint green lights deep inside"),
        "wall_obsidian": ("wall", 128, 3.0, "a wall of huge black stone blocks, glassy, with thin red reflections and no mortar lines"),
        "wall_gate": ("wall", 128, 3.0, "a colossal iron-bound black gate wall: vertical bronze straps, studs, no emblem, no letters"),
        "floor_basalt": ("floor", 64, 2.5, "black basalt paving with ash drifted in the joints"),
        "floor_stair": ("floor", 64, 2.0, "worn cut stone stair treads in a cliff, dark grey with bronze green stains and ash"),
        "wall_cliff": ("wall", 128, 3.0, "a dark cliff face with hanging bronze bells' green stains and iron ring bolts"),
        "wall_ash_dune": ("wall", 128, 3.0, "grey ash dunes and clinker, a dull red underglow low down"),
        "floor_ash": ("floor", 64, 3.0, "cracked grey ash plain with dull red in the cracks"),
        "floor_red_rock": ("floor", 64, 3.0, "red-grey scorched rock with ash"),
        "wall_vent": ("wall", 128, 3.0, "a tunnel wall of glowing red volcanic rock with black crust, veins of light (anim: pulse in brightness)"),
        "floor_vent": ("floor", 64, 3.0, "black crusted rock floor with red glowing cracks"),
        "ceil_hot": ("ceil", 64, 3.0, "a low red-lit rock tunnel roof, black crust and orange glow"),
        "ceil_smoke": ("ceil", 128, 6.0, "a red-grey smoke sky with dark roiling streaks (used as a ceiling tile)"),
        "ceil_mist_teal": ("ceil", 128, 6.0, "a low teal marsh mist with dark streaks and a few green points of light (used as a ceiling tile)"),
        "wall_cavern": ("wall", 128, 3.0, "a deep cavern wall: black rock with pale wet streaks and cold highlights"),
        "floor_cavern": ("floor", 64, 3.0, "dark smooth cavern floor with scattered pale pebbles"),
        "floor_pool": ("floor", 64, 3.0, "a black pool with a slow ring ripple and a thin white reflection (anim: scroll)"),
        "ceil_cavern": ("ceil", 64, 4.0, "a black cavern roof with pale stalactite points"),
        "floor_camp": ("floor", 64, 3.0, "trampled ash and boot prints, a few ember specks, grey"),
        "wall_tent": ("wall", 128, 2.5, "grey canvas tent wall with dark ropes and stakes, a faint red firelight, no emblem"),
        "sky_ash": ("sky", 256, 1.0, "a smoke sky: red-grey and black roiling cloud, a dull red glow at the horizon edge; the black cone of the Glass Mountain with one red vent is NOT drawn here (a billboard does that)"),
    },
}

# ---- billboards -------------------------------------------------------------------------------------------------------------------------------

THINGS: dict = {
    "orchard": {
        "thing_apple_tree": ("thing", 128, 1.0, "a gnarled apple tree heavy with red apples, dark trunk, green and gold leaves, standing on the bottom edge"),
        "thing_apple_basket": ("thing", 128, 1.0, "two wicker baskets heaped with red apples, a few spilled"),
        "thing_cot": ("thing", 128, 1.0, "a plain wooden cot bed with a patchwork quilt and a pillow, seen from the foot of the bed"),
        "thing_lantern_post": ("thing", 128, 1.0, "a wooden post with a hanging horn lantern giving a warm round glow"),
        "thing_lantern_stake": ("thing", 128, 1.0, "a tall lantern held on a pole stuck in the riverbank, small warm light, a wisp of moth"),
        "thing_hearth": ("thing", 128, 1.0, "a stone inn hearth with a large fire and an iron pot on a hook (flames drawn static; the map flickers it)"),
        "thing_inn_table": ("thing", 128, 1.0, "a rough wooden inn table with pewter mugs, a loaf and a candle"),
        "thing_barrel": ("thing", 128, 1.0, "an oak barrel with iron hoops and a tap"),
        "thing_stool": ("thing", 128, 1.0, "a three-legged wooden stool"),
        "thing_hanging_lamp": ("thing", 128, 1.0, "an iron ring lamp hanging from a chain with five small candles, drawn from the chain down"),
        "thing_ember": ("thing", 128, 1.0, "THE EMBER: a glowing orange-red coal the size of a fist cupped in a small shallow iron bowl, bright yellow core, soft orange halo drawn in dithered pixels (hard alpha), tiny sparks above it. It is the one warm hero light of the whole road: make it read at once. Original design, plain."),
        "thing_gate": ("thing", 128, 1.0, "a wooden orchard gate between two stone posts, half open"),
        "thing_hay_bale": ("thing", 128, 1.0, "two round hay bales"),
        "thing_willow": ("thing", 128, 1.0, "a weeping willow at the riverside, long drooping branches, dark blue-green"),
        "thing_horse_far": ("thing", 128, 1.0, "a tall black horse seen side on, head up and one forefoot raised, snorting, ash-grey rug and bridle with a faint red glint at the eye (no rider)"),
        "thing_signpost": ("thing", 128, 1.0, "a plain wooden signpost with two blank arms"),
        "thing_rock_ford": ("thing", 128, 1.0, "a cluster of mid-river stepping stones with water curling round them"),
        "thing_door_back": ("thing", 128, 1.0, "a small low back door of an inn, ajar, with cold blue night showing through the gap"),
        "piece_river_rise": ("piece", 128, 1.0, "a wall of rising dark river water with silver foam crests, wider than tall, translucent edge: the river swelling to bar the crossing"),
        "piece_rider_shadow": ("piece", 128, 1.0, "the black silhouette of a hooded rider on a horse, cast across a pale lit window, elongated, soft edge"),
    },
    "birch_hall": {
        "thing_birch_tree": ("thing", 128, 1.0, "a tall white birch tree with a few last yellow leaves"),
        "thing_birch_pillar": ("thing", 128, 1.0, "a hall pillar made of a whole white birch trunk, base to top, silver band at the foot, branches carved into a vault at the top"),
        "thing_silver_lamp": ("thing", 128, 1.0, "a standing silver lamp with a white-blue flame and a leaf-shaped shade"),
        "thing_banner_birch": ("thing", 128, 1.0, "a long white hanging banner with a silver-embroidered birch leaf spray (a pattern of leaves only, no letters)"),
        "thing_table_map": ("thing", 128, 1.0, "a long white table with a hide spread across it showing only a few faint ink contours and a river line, an abstract invented chart (no real land, no writing)"),
        "thing_snow_pine": ("thing", 128, 1.0, "a dark spruce heavily loaded with snow"),
        "thing_cairn": ("thing", 128, 1.0, "a snow-capped cairn of flat grey stones with a bit of red cloth tied to it"),
        "thing_cave_mouth": ("thing", 128, 1.0, "the dark mouth of a cave in a snowy rock face, icicles over it, blackness inside"),
        "thing_chair_white": ("thing", 128, 1.0, "a tall white wooden chair with a high carved birch-leaf back"),
        "thing_vial_stand": ("thing", 128, 1.0, "a small white stone pedestal holding a tiny stoppered glass vial of pale blue-white liquid with a soft cold glow"),
        "thing_ember": ("thing", 128, 1.0, "THE EMBER: a glowing orange-red coal the size of a fist cupped in a small shallow iron bowl, bright yellow core, soft orange halo drawn in dithered pixels (hard alpha), tiny sparks above it; the one warm hero light of the road. Same design in every map."),
        "thing_ridge_marker": ("thing", 128, 1.0, "a leaning wooden marker post on a snowy ridge with a strip of grey cloth snapping in the wind"),
        "thing_door_far": ("thing", 128, 1.0, "a tall pale narrow doorway at the far end of a hall, blue-white light spilling out"),
        "piece_storm_snow": ("piece", 256, 1.0, "a wall of wind-driven snow: diagonal white streaks and soft grey-blue billows, wide (256 x 128), soft translucent alpha, the storm of a high pass"),
    },
    "deep_halls": {
        "thing_pillar_deep": ("thing", 128, 1.0, "a colossal fluted black stone pillar, wider than tall in the base, one cold white-cyan highlight edge"),
        "thing_cold_light": ("thing", 128, 1.0, "a single cold white-cyan light: a hanging pale crystal-like lamp with a long thin shaft of light falling from it"),
        "thing_drum": ("thing", 128, 1.0, "a huge old skin drum on a stone, taut skin with a faint pulse of light, as if struck from below (a few dust motes)"),
        "thing_stalagmite": ("thing", 128, 1.0, "a cluster of wet black stalagmites with pale tips"),
        "thing_boat": ("thing", 128, 1.0, "a small clinker-built boat tied at a landing, seen from the bow, a lantern at the prow, a coil of rope"),
        "thing_rope_post": ("thing", 128, 1.0, "a mooring post with rope loops, wet wood, dark"),
        "thing_horn": ("thing", 128, 1.0, "a curved grey horn, bound with leather and plain iron bands, resting on a rock with a ranger's grey cloak thrown beside it"),
        "thing_bridge_rail": ("thing", 128, 1.0, "a section of low stone parapet with chain slung between two short posts"),
        "thing_mist": ("thing", 128, 1.0, "a drifting bank of pale mist, soft, low, wide, translucent"),
        "thing_lantern_boat": ("thing", 128, 1.0, "a hand lantern with a warm light standing on a wet rock (a lone warm point in the cold dark)"),
        "thing_ember": ("thing", 128, 1.0, "THE EMBER: a glowing orange-red coal the size of a fist cupped in a small shallow iron bowl, bright yellow core, soft orange halo drawn in dithered pixels (hard alpha), tiny sparks above it; the one warm hero light of the road. Same design in every map."),
        "thing_waterfall_edge": ("thing", 128, 1.0, "the lip of a waterfall seen from above: a curved sheet of white water pouring over black rock, spray rising"),
        "piece_drowned_thing": ("piece", 256, 1.0, "something enormous rising from a black lake: a tangle of pale, wet, many-jointed limbs and a long slow back breaking the surface, ripples, water pouring from it. Original creature: unsettling, not a known monster, no eyes visible. Wide 256 x 128, hard alpha."),
    },
    "ash_land": {
        "thing_reed_clump": ("thing", 128, 1.0, "a thick clump of dark teal reeds with bulrush heads and a few drifting green motes"),
        "thing_marsh_light": ("thing", 128, 1.0, "a hovering pale green-teal globe of light with a faint, sad, almost-face in it (two dark eye hollows and a mouth hollow, drawn in the glow), a trailing wisp below"),
        "thing_gate_black": ("thing", 128, 1.0, "a colossal closed gate in a black wall seen from the front, two great doors, bronze straps, a lower rim of wet rubble; stands on the bottom edge"),
        "thing_wall_crack": ("thing", 128, 1.0, "a tall narrow crack in a black stone wall, with a thin warm light and a trickle of ash falling from it"),
        "thing_bell": ("thing", 128, 1.0, "a large green-bronze bell hung from an iron frame with a rope, dull metallic highlights"),
        "thing_bell_row": ("thing", 128, 1.0, "three bells of different sizes hung on a rough beam over a cliff stair, green-bronze, ropes dangling"),
        "thing_tower_light": ("thing", 128, 1.0, "a distant dark tower, thin and tall, on a ridge, with a single steady pale-red light at its top; stands on the bottom edge"),
        "thing_dead_tree": ("thing", 128, 1.0, "a leafless blackened tree, bent, with ash on its branches"),
        "thing_stake": ("thing", 128, 1.0, "a wooden stake driven in the ash with a heavy chain and an open shackle on it"),
        "thing_tent": ("thing", 128, 1.0, "a grey canvas war tent with dark guy ropes, no emblem, a dull red glow at its door"),
        "thing_brazier_red": ("thing", 128, 1.0, "an iron brazier with a dull red coal fire and ash smoke"),
        "thing_banner_rider": ("thing", 128, 1.0, "a plain ash-grey banner on a black pole, torn, with a single small red glint in the middle (no emblem, no letters)"),
        "thing_vent_glow": ("thing", 128, 1.0, "a crack in black rock venting a column of dull red glow and ash"),
        "thing_glass_mountain": ("thing", 128, 1.0, "THE GLASS MOUNTAIN: a huge black cone of glassy obsidian, a faint sheen on one flank, a single red vent glowing at its summit and a thin red plume; stands on the bottom edge, far distance (low detail, simple silhouette)"),
        "thing_stalagmite_red": ("thing", 128, 1.0, "a cluster of black pointed rocks catching red light on one side"),
        "thing_chain_post": ("thing", 128, 1.0, "an iron post with a loop of heavy chain"),
        "thing_ember_altar": ("thing", 128, 1.0, "THE EMBER on a flat black stone: a glowing orange-red coal the size of a fist, bright yellow core, strong orange halo drawn in dithered pixels, sparks; the cavern is lit by it alone; the same design as the Ember elsewhere but on a stone"),
        "thing_pool_stones": ("thing", 128, 1.0, "a ring of flat black stones around the rim of a still black pool, a thin white glint on the water"),
        "thing_camp_fire": ("thing", 128, 1.0, "a smoky fire of dark logs with a ring of stones, red flames"),
        "piece_gate_mouths": ("piece", 128, 1.0, "the gate's door panels each showing a wide open dark mouth with ragged teeth, pushed out of the bronze like a relief that has come alive, laughing; hard alpha, the gate doors shape"),
        "piece_light_shaft": ("piece", 128, 1.0, "a tall narrow shaft of white light falling from above through dust, soft edges, translucent, bright core"),
        "piece_white_swell": ("piece", 256, 1.0, "a huge soft radial bloom of white light, pure white centre fading to transparent at the edge, wide 256 x 128, translucent (the spring's light swelling)"),
        "piece_long_shadow": ("piece", 256, 1.0, "a long thin dark shadow of a standing figure stretched along the ground towards the viewer, soft edge, wide 256 x 128, translucent black"),
    },
}
