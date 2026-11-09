# Remaining visual limitations (honest report)

Verified: the live room was run in Unity, 8 captures (messy/tidy x 4 views) were inspected by eye, a Unity-side prop sheet per family was inspected,
and 71/71 PlayMode tests pass (5 new `RoomTests`). Not verified: any playtest by a human, performance on a real modest PC (only polygon budget is checked: ~550k triangles, 0 missing props),
Android, the baked-content route with the new room (the baked tests pass, but the baked world was not re-baked; the new room is built at run time from original assets, so it works in both).

* **Clothes and soft goods**: bed, pillows, folded stacks, basket, backpack read well; the crumpled clothes piles are smooth, tube-like mounds (fabric detail relies on a normal map).
* **Flat decals**: stickers, scuffs, labels, magazine/flyer print and picture-frame prints are colour regions, not textured artwork or text. Walls are plain textured plaster, with few posters.
* **Sims 2 leftovers**: the door (and the corridor behind it), the ornate floor-mirror frame, the characters and the garden trees clash in style with the new props and are not redistributable.
* **Exteriors**: the shop street (first pass by an agent that was cut off) and the club are blocky, low-detail and un-LODed; the club view is mostly neon letters and facade seen through the window; no skyline backdrop yet; sky is a flat colour (HDRIs not wired).
* **Lighting**: realtime only (sun, pendant, pulsing magenta/cyan venue point lights); no baked GI/ambient occlusion, so contact shadows are soft and corners flat. The sun colour is fixed dusk.
* **Camera**: eye height unchanged, so floor-level objects are still mostly out of frame; a 12-degree resting downward tilt was added so desks/beds/dressers are visible.
* **Interaction**: hover highlight is a small pulsing star plus a warm tint (no outline shader); animations are procedural tweens (no skeletal cloth). Sounds are synthesised placeholders.
* **Layout**: the door still opens next to the bedside table; no check that the open door swing clears it (the table and bed were placed beside it).
* **Pipeline**: Blender materials map by role name; adding a role without a rule falls back to the imported colour. The exterior family is incomplete (no club-side street furniture beyond reused shop props).
