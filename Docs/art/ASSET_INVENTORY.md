# Asset inventory (bedroom overhaul)

| Asset | Count | Source | Format | Licence / status |
|---|---|---|---|---|
| Furniture, lamps, window/door frames (`furniture_*`) | 30 | **Original** - Blender Python (`Art/Source/blender/furniture.py`) | FBX | Original work of this project; redistributable |
| Books, paper, records, boxes (`paper_*`) | 37 | **Original** - `paper.py` | FBX | Original |
| Dishes, rubbish, bins, cables (`kitchen_*`) | 46 | **Original** - `kitchen.py` | FBX | Original |
| Bed set, bedding, clothes, bags, shoes, curtains, rug (`textiles_*`) | 31 | **Original** - `textiles.py` | FBX | Original |
| Electronics + DJ gear (`electronics_*`) | 24 | **Original** - `electronics.py` | FBX | Original |
| Shop street (corner shop, terraces, cars, lamp, kerb, props) | 8 | **Original** - `exterior.py` (a first agent pass, finished partly) | FBX | Original |
| Nightclub "VOID" building | 1 | **Original** - `club.py` | FBX | Original |
| Surface textures (plaster, boards, dark wood, laminate, carpet, brick, asphalt, paving, concrete, metal, denim, cotton, fabric pattern) | 18 sets (albedo+normal) | **Poly Haven** (polyhaven.com), 1k | JPG | **CC0** (https://polyhaven.com/license); list in `Art/inventory/third_party.csv`, staged by `Tools/art/stage_textures.py` |
| Kenney Furniture Kit, City Kit (Commercial/Suburban/Roads), Retro Urban Kit, Modular Buildings | 6 packs (downloaded, **not used in the game**) | kenney.nl | FBX/OBJ/GLB | **CC0** (each pack's License.txt). Kept in `Art/ThirdParty/` (git-ignored) as optional filler; nothing imported into Assets |
| Poly Haven night HDRIs (rooftop_night, modern_buildings_night) | 2 (downloaded, not used) | polyhaven.com | HDR | CC0 |
| Quaternius, Sketchfab, Unity Asset Store | 0 | - | - | Not acquired: Quaternius downloads need Google Drive/itch.io interaction; Sketchfab/Asset Store need logins and per-asset licences. No paywalls bypassed |
| **Sims 2 / OpenTS2 (EA) assets still used** | door (`doorQuaint`, animated), floor mirror frame, the 4 character Sims, garden trees/fence, lawn | The Sims 2 Legacy Collection on the user's PC via OpenTS2 (live) or locally baked prefabs (`Assets/LocalBaked`, git-ignored) | cres/shpe/skel -> Unity | **EA copyright; not redistributable.** Not shipped in this repo. A standalone commercial release must replace them (door/frame/characters/trees) |
| Old Sims 2 furniture (bed, dresser, bookcase, chair, lamp, plant, windows, painting, poster) and the procedural blocky clutter | - | - | - | **Replaced** (hidden by `hideLegacy`; `-legacyroom` brings them back) |

Procedural/script-generated sounds (`SfxSynth`) and the club/shop lights are code, not assets. The Blender prop scripts are the "source files" for the original models.
