# Bedsit prop kit - modelling brief (read first)

Project: first-person Unity game, a lived-in modest bedsit (stylised-realistic, "Sims 2 but better lit and more detailed").
Camera is at 1.62 m eye height inside the room, 4 views, objects are seen from 0.5-4 m. Props sit on beds, desks, sills,
shelves and the floor. They must hold up at close range and must NOT look like cubes/cylinders/spheres with colours.

## Tooling
* Blender 4.5 LTS: `"C:/Program Files/Blender Foundation/Blender 4.5/blender.exe" -b -P <script.py>`
* Shared helper lib: `Art/Source/blender/bsk.py` (READ IT FIRST). `from bsk import *` after `sys.path.insert(0, os.path.dirname(__file__))`.
  Helpers: `mat(role)`, `box`, `cylinder`, `lathe`, `tube`, `to_mesh`, `displace_noise`, `subdivide`, `subsurf`, `solidify`, `uv_box`,
  `uv_smart`, `join`, `parent_all`, `set_origin_bottom`, `export_fbx(root, family, name)`, `preview(objs, name, views=...)`.
  You may add helper functions inside YOUR OWN family script, or write `Art/Source/blender/lib_<yourfamily>.py`. Do NOT edit bsk.py
  (other agents import it); if you find a bug in it, work around it in your own file and mention it in your report.
  Known weak spot: `tube()` uses a POLY curve so bends are faceted - subdivide your point list yourself (Catmull-Rom / Bezier sampling)
  or use many points for smooth cables/handles.
* Python 3.x inside Blender only; bmesh + mathutils + mathutils.noise are available. numpy is available inside Blender.
* Do NOT run Unity, do NOT edit anything under `Assets/` except writing your own FBX files under `Assets/Bedsit/Art/Models/<family>/`
  (the exporter does that). Do not touch other agents' families or any existing C# / scene / project file.

## Conventions (hard requirements)
* 1 Blender unit = 1 metre. Real-world dimensions (a mug is ~9 cm tall, a single bed 0.95x2.0 m, a desk 0.75 m high).
* ORIGIN = bottom centre of the object (sits on the floor/surface). FRONT of the object faces Blender -Y.
  Wall-mounted/back-against-wall furniture: origin at the back-bottom centre is NOT needed - keep bottom centre, front -Y, and say
  in the manifest which side is the back.
* One prop per FBX, named `<family>_<name>.fbx`, a single root (joined mesh, or an empty with a few child meshes when parts must move
  separately e.g. doors/lids/monitor screen). Name child objects meaningfully (`door_L`, `lid`, `screen`).
* Materials: use ROLE names from `bsk.MATERIALS` (e.g. `cotton_white`, `wood_dark`, `plastic_black`, `screen_on`, `led_green`).
  You may ADD new roles by calling `MATERIALS["my_role"] = (colour, roughness, metallic)` in your script, but then also list them
  in the manifest `new_roles`. A prop should use several roles where the real object does (mug: ceramic + liquid; monitor: plastic + screen).
  Colour variety between instances of the same prop = separate roles (cotton_red / cotton_blue ...) or different variants - the room
  must NOT look like the same object copy-pasted. Make 2-4 VARIANTS of common clutter (different shape/proportion/seed), not just recolours.
* UVs on every mesh (bsk helpers add them; unwrap properly with `uv_smart` for hero props with detailed texturing needs).
* Bevel every hard edge a little (0.002-0.006 m) so edges catch light. Add real detail: seams, stitching grooves, buttons, labels
  (as geometry or colour region via separate material slots), handles, feet, screws, ports, rim lips, wear (use `displace_noise` very lightly).
* Soft things (duvets, pillows, clothes, towels, bags) must look soft and creased: build from a subdivided grid / closed cushion with
  noise + drape + fold displacement, not from smooth spheres. Hard things must look manufactured and slightly worn.
* Budgets: small clutter 300-6,000 tris; large furniture / bedding up to ~25,000 tris. No wasted geometry hidden inside.
* Closed, manifold-ish meshes where practical, normals outward, no flipped faces, no zero-area faces, no stray loose geometry.

## Verification you MUST do (the result is judged on what it looks like)
1. For EVERY prop call `preview(...)` with at least two views (`front34`, `back34`/`top`) and actually LOOK at the PNGs with the Read tool.
   Then also make a contact sheet per family if useful. If a prop looks crude, blobby, wrong-proportioned, inside-out or generic:
   reject it and rebuild it better. Iterate until you would be happy to see it 60 cm from the camera.
2. Re-import one exported FBX into a fresh Blender scene and confirm size, origin (bottom centre) and orientation (front = -Y in Blender).
3. Write `Art/Source/blender/manifest_<family>.json`: a list of `{name, file, category, dims_m:[x,y,z], tris, roles:[...], variant_of, notes}`.
   `notes` must state surface heights useful for placement (e.g. desk top height) and for cleanables which messy/tidy partner it pairs with.
4. Report (<250 words): list of exported props, anything you rejected/rebuilt, known visual weaknesses, and the preview PNG paths
   (all previews go to `Art/Source/previews/`, via `preview()`).

## Style target
Warm, slightly worn British/European domestic stuff of a young adult living modestly in a bedsit who loves electronic/rave music:
dented cans, creased clothes, stained mugs, scuffed trainers, peeling stickers, well-used furniture. Specific > generic. Believable first.
