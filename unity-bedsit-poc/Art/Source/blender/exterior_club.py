"""exterior_club.py - second half of the `exterior` family: the rave/nightclub view (west window) + backdrops.
Imported by exterior.py (BUILDERS merged); not run directly."""
import math, random, os, sys
from mathutils import Vector, noise

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bsk
from lib_exterior import *   # noqa

CLUB_W, CLUB_D, CLUB_H = 15.0, 10.0, 7.2
ARCH_CX, ARCH_R, ARCH_ZS = 6.7, 2.5, 2.85       # facade-local u, radius, spring line
SIGN_W, SIGN_H = 4.2, 1.3


def graffiti_text(mb, tf, text, h, x, z, d, fill, outline="graffiti_white", stroke=None, spacing=0.12):
    stroke = stroke or h * 0.26
    block_text(mb, tf, text, h, x, z, d, d + 0.006, outline, stroke=stroke * 1.55, spacing=spacing)
    block_text(mb, tf, text, h, x, z, d + 0.006, d + 0.012, fill, stroke=stroke, spacing=spacing)


# ================================================================================================= club building

def build_club_building():
    W, D, H = CLUB_W, CLUB_D, CLUB_H
    mb = MB()
    tf = facade_tf(W)
    roles, weights, mortar = ("brick_sooty", "brick_sooty_dark", "brick_sooty_light"), (0.55, 0.30, 0.15), "mortar_dark"
    RV = "brick_sooty_dark"
    openings = []
    cx, r, zs = ARCH_CX, ARCH_R, ARCH_ZS
    # ---- railway arch with roller shutter ----
    openings.append({"x0": cx - r, "x1": cx + r, "z0": 0.0, "z1": zs})
    openings.append({"x0": cx - r - 0.13, "x1": cx + r + 0.13, "z0": zs, "z1": zs + r + 0.13, "arch_r": r + 0.13})
    arch_ring(mb, tf, cx, zs, r, 0.6, "brick_sooty_light", n=26, thick=0.26, proud=0.025, jamb_to=0.0)
    mb.face([tf((cx - r - 0.3, zs, -0.62)), tf((cx + r + 0.3, zs, -0.62)), tf((cx + r + 0.3, zs + r + 0.3, -0.62)), tf((cx - r - 0.3, zs + r + 0.3, -0.62))], "render_dark")
    shutter_corrugated(mb, tf, cx - r - 0.1, cx + r + 0.1, 0.0, zs + 0.25, -0.6)
    graffiti_text(mb, tf, "ACID", 0.72, cx - 1.55, 0.55, -0.58, "graffiti_b", stroke=0.16, spacing=0.1)
    # ---- entrance: heavy black double door, canopy with LED bars, side LED bars, CCTV ----
    openings.append(door(mb, tf, 10.0, 0.0, 1.9, 2.5, recess=0.4, leaf_role="wood_painted_black", reveal_role=RV, double=True, kick=True,
                         fanlight=False, lintel=0.2, sill_role="metal_painted_black", frame_role="metal_painted_black", panels=0, letterbox=False))
    for (a, b) in ((10.33, 10.6), (11.3, 11.57)):
        mb.box((a, 1.5, -0.4), (b, 1.77, -0.392), "metal_steel", tf)
        mb.face([tf((a + 0.03, 1.53, -0.391)), tf((b - 0.03, 1.53, -0.391)), tf((b - 0.03, 1.74, -0.391)), tf((a + 0.03, 1.74, -0.391))], "window_club")
    for (a, b) in ((10.12, 10.9), (11.0, 11.78)):      # studded steel bands across the leaves
        for zz in (0.5, 2.1):
            mb.box((a, zz, -0.4), (b, zz + 0.07, -0.388), "metal_painted_grey", tf)
    mb.box((9.6, 2.85, 0.0), (12.3, 3.15, 1.3), "metal_painted_black", tf, inset=0.02, inset_face="+z")
    for i in range(14):
        u = 9.72 + i * 0.185
        mb.box((u, 2.89, 1.3), (u + 0.035, 3.11, 1.318), "neon_cyan", tf)
    for dd in (0.42, 0.85, 1.2):
        mb.cyl((0, 0, 0), 0.07, 0.07, 0.012, "lamp_glow", 12, frame_tf(tf((10.95, 2.85, dd)), (1, 0, 0), (0, -1, 0)))
    for u in (9.78, 12.06):
        mb.box((u, 0.3, 0.0), (u + 0.06, 2.55, 0.045), "neon_cyan", tf)
    mb.box((12.4, 3.45, 0.0), (12.48, 3.53, 0.22), "metal_painted_grey", tf)
    mb.cyl((0, 0, 0), 0.04, 0.05, 0.16, "metal_painted_grey", 10, seg_tf(tf((12.44, 3.49, 0.22)), tf((12.3, 3.3, 0.45))))
    # ---- industrial windows (club-lit magenta / dark / tv) ----
    for (u, look) in ((0.7, "club"), (2.3, "dark"), (12.0, "club"), (13.5, "tv")):
        openings.append(window(mb, tf, u, 4.65, 1.2, 1.35, "industrial", look, None, "metal_painted_black", RV))
    # ---- fire exit door ----
    openings.append(door(mb, tf, 13.0, 0.0, 0.9, 2.1, recess=0.15, leaf_role="metal_painted_grey", reveal_role=RV, panels=0, fanlight=False,
                         letterbox=False, lintel=0.15, sill_role="stone_sill", frame_role="metal_painted_grey"))
    mb.box((13.15, 1.0, -0.15), (13.75, 1.06, -0.09), "metal_chrome", tf)             # push bar
    # ---- painted plinth band (between the openings) ----
    for (a, b) in ((0.0, cx - r), (cx + r, 10.0), (11.9, 13.0), (13.9, W)):
        mb.box((a, 0.0, -0.01), (b, 0.9, 0.03), "render_dark", tf)
    # graffiti tags on the wall
    graffiti_text(mb, tf, "RAVE", 0.42, 0.55, 2.62, 0.012, "graffiti_c", stroke=0.09)
    graffiti_text(mb, tf, "ZK", 0.32, 12.35, 0.3, 0.032, "graffiti_a", stroke=0.07)
    # ---- smoking area railing + sign ----
    for u in (12.5, 13.6, 14.7):
        mb.cyl((u, 0.0, 1.6), 0.025, 0.025, 1.1, "metal_painted_black", 10, frame_tf(tf((0, 0, 0)), (1, 0, 0), (0, 0, 1)) if False else
               frame_tf(tf((u, 0.0, 1.6)), (1, 0, 0), (0, 0, 1)))   # placeholder replaced below
    root_tf_dummy = None
    # (cyl along local z of a frame whose e3 is world +Z: e1 = X, e2 = -(-Y)... use e1=(1,0,0), e2=(0,1,0) -> e3 = +Z)
    # ---- neon sign brackets ----
    for u in (cx - SIGN_W / 2 + 0.2, cx + SIGN_W / 2 - 0.2):
        for zz in (5.85, 6.95):
            mb.box((u - 0.03, zz - 0.03, 0.0), (u + 0.03, zz + 0.03, 0.12), "metal_dark", tf)
    # ---- parapet, coping, roof plant, laser/spot fixtures ----
    mb.box((-0.05, H, -0.35), (W + 0.05, H + 0.15, 0.08), "stone_sill", tf)
    mb.box((-W / 2 + 3.0, 2.0, H), (-W / 2 + 5.0, 4.0, H + 0.8), "metal_painted_grey", inset=0.02, inset_face="+z")
    mb.box((W / 2 - 4.0, 3.0, H), (W / 2 - 2.5, 4.5, H + 1.1), "render_dark", inset=0.02, inset_face="+z")
    mb.cyl((-W / 2 + 7.0, 3.0, H), 0.25, 0.25, 0.6, "metal_painted_grey", 12)
    mb.lathe([(0.25, 0.6), (0.4, 0.75), (0.0, 0.8)], "metal_painted_grey", 12, base=(-W / 2 + 7.0, 3.0, H))
    for u in (1.5, 5.5, 9.5, 13.5):
        base = tf((u, H + 0.15, -0.15))
        mb.box((u - 0.16, H + 0.15, -0.31), (u + 0.16, H + 0.23, 0.01), "metal_painted_black", tf)
        for du in (-0.12, 0.12):
            mb.box((u + du - 0.015, H + 0.23, -0.17), (u + du + 0.015, H + 0.55, -0.13), "metal_painted_black", tf)
        piv = Vector(tf((u, H + 0.5, -0.15)))
        dirv = Vector((0, -0.55, 0.83)).normalized()
        p0 = piv - dirv * 0.12
        p1 = piv + dirv * 0.30
        mb.cyl((0, 0, 0), 0.10, 0.12, 0.42, "metal_painted_black", 14, seg_tf(p0, p1), caps=(True, False))
        mb.cyl((0, 0, 0), 0.105, 0.105, 0.02, "light_beam_emitter", 14, seg_tf(p1, p1 + dirv * 0.03))
    # ---- taxi sign projecting from the right corner ----
    mb.box((14.3, 3.6, 0.15), (14.4, 3.95, 1.05), "taxi_sign", tf, inset=0.01, inset_face="+z")
    sx0, sx1 = W / 2 - 0.2, W / 2 - 0.1
    block_text(mb, frame_tf((sx1 + 0.001, -1.05, 3.6), (0, 1, 0), (0, 0, 1)), "TAXI", 0.22, 0.0, 0.065, 0.0, 0.004, "sign_letters_dark", stroke=0.04, centre_w=0.9)
    block_text(mb, frame_tf((sx0 - 0.001, -0.15, 3.6), (0, -1, 0), (0, 0, 1)), "TAXI", 0.22, 0.0, 0.065, 0.0, 0.004, "sign_letters_dark", stroke=0.04, centre_w=0.9)
    mb.bar(tf((14.35, 3.95, 0.0)), tf((14.35, 3.95, 1.05)), 0.03, "metal_dark")
    mb.bar(tf((14.35, 3.3, 0.0)), tf((14.35, 3.6, 1.0)), 0.025, "metal_dark")
    # smoking-area sign
    mb.box((13.1, 2.0, 0.0), (14.1, 2.26, 0.02), "sign_letters_dark", tf)
    block_text(mb, tf, "SMOKING AREA", 0.1, 13.1, 2.08, 0.02, 0.024, "sign_letters", stroke=0.018, spacing=0.2, centre_w=1.0)
    # ---- bricks ----
    brick_wall(mb, tf, W, H, openings, roles, weights, mortar, z_from=0.9, seed=31)
    # ---- shell + tall chimney with graffiti piece ----
    mb.box((-W / 2, 0.0, 0.0), (W / 2, D, H), "brick_sooty", skip=("-y", "-z"))
    chx, chy = -5.5, 7.6
    mb.box((chx - 0.65, chy - 0.65, 0.0), (chx + 0.65, chy + 0.65, 12.5), "brick_sooty", skip=("-z",))
    mb.box((chx - 0.72, chy - 0.72, 12.5), (chx + 0.72, chy + 0.72, 12.85), "brick_sooty_dark")
    mb.box((chx - 0.80, chy - 0.80, 12.85), (chx + 0.80, chy + 0.80, 13.1), "stone_sill")
    mb.box((chx - 0.5, chy - 0.5, 13.1), (chx + 0.5, chy + 0.5, 13.3), "interior_dark")
    ctf = frame_tf((chx - 0.65, chy - 0.65, 0.0), (1, 0, 0), (0, 0, 1))
    for i, ch in enumerate("VOID"):
        graffiti_text(mb, ctf, ch, 0.62, 0.0, 10.3 - i * 0.78, 0.01, ("graffiti_a", "graffiti_b", "graffiti_c", "graffiti_a")[i], stroke=0.14)
    # bold colour blobs lower on the chimney
    for k, (zz, rl) in enumerate(((7.9, "graffiti_b"), (7.55, "graffiti_c"))):
        mb.ribbon(arc(0.65, zz, 0.16, 0, 360, 14, rx=0.42), 0.05, 0.004, 0.009 + k * 0.001, rl, ctf)
    root = mb.build("exterior_club_building")
    notes = ("Converted railway-arch nightclub, 15 x 10 m, parapet 7.2 m, chimney to 13.3 m at (-5.5, 7.6). Origin ground-level front-centre, facade plane y=0 (faces -Y). "
             f"Arch centre x={cx - W / 2:.1f}, shutter 0.6 m deep; black double door x {10.0 - W / 2:.1f}..{11.9 - W / 2:.1f} (recess 0.4) with canopy z 2.85-3.15 projecting 1.3 m; "
             f"smoking railing x {12.5 - W / 2:.1f}..{14.7 - W / 2:.1f} at y -1.6; taxi sign at x 6.85 z 3.6-3.95. Mount exterior_club_neon_sign on the brackets at x={cx - W / 2:.1f}, z 5.75, back face at y -0.12. "
             f"Hoarding goes on the wall at x {0.3 - W / 2:.1f}..{3.9 - W / 2:.1f}; speaker wall above it at z 3.3. Lit roles: window_club (magenta), window_tv, neon_cyan (LED bars), lamp_glow (canopy downlights), "
             "light_beam_emitter (4 lens discs on the parapet at z ~7.75 - attach Unity spot lights pointing (0,-0.55,0.83)), taxi_sign.")
    return root, dict(category="building", views=("front", "front34", "close"), notes=notes)


# ================================================================================================= neon sign

def build_club_neon_sign():
    W, H = SIGN_W, SIGN_H
    stf = frame_tf((-W / 2, 0.08, 0.0), (1, 0, 0), (0, 0, 1))     # backing d 0..0.06 (y 0.08..0.02), tubes at d 0.13 (y -0.05)
    back = MB()
    back.box((0, 0, 0), (W, H, 0.06), "neon_backing", stf, inset=0.012, inset_face="+z")
    for (u, v) in ((0.08, 0.08), (W - 0.08, 0.08), (0.08, H - 0.08), (W - 0.08, H - 0.08)):
        back.cyl((u, v, 0.06), 0.012, 0.012, 0.004, "metal_chrome", 8, stf)
    pink = MB()
    strokes, tw = text_strokes("VOID", 0.8, 0.0, 0.3, 0.22)
    x0 = (W - tw) / 2
    neon_text(pink, stf, "VOID", 0.8, 0.0, 0.3, 0.13, 0.028, "neon_pink", spacing=0.22, centre_w=W)
    # standoffs from the backing to the tubes (at stroke starts / ends)
    for s in text_strokes("VOID", 0.8, x0, 0.3, 0.22)[0]:
        for p in (s[0], s[len(s) // 2]):
            back.cyl((p[0], p[1], 0.06), 0.008, 0.008, 0.07, "metal_dark", 6, stf)
    cyan = MB()
    rr = fillet([(0.14, 0.12), (W - 0.14, 0.12), (W - 0.14, H - 0.12), (0.14, H - 0.12), (0.14, 0.12)], 0.3, 6, closed=True)
    cyan.tube([stf((p[0], p[1], 0.13)) for p in rr], 0.02, "neon_cyan", 8, caps=False)
    # underline flick
    flick = [(x0 + 0.1, 0.22), (x0 + tw * 0.5, 0.17), (x0 + tw + 0.05, 0.22)]
    cyan.tube([stf((p[0], p[1], 0.13)) for p in fillet(flick, 0.3, 6)], 0.02, "neon_cyan", 8)
    for (u, v) in ((0.14, H / 2), (W - 0.14, H / 2), (W / 2, 0.12), (W / 2, H - 0.12)):
        back.cyl((u, v, 0.06), 0.008, 0.008, 0.07, "metal_dark", 6, stf)
    ob_b = back.build("backing")
    ob_p = pink.build("tubes_pink")
    ob_c = cyan.build("tubes_cyan")
    root = bsk.parent_all([ob_b, ob_p, ob_c], "exterior_club_neon_sign")
    notes = (f"Neon wordmark 'VOID' {W} x {H} m. Children: backing (dark panel, back face at y=+0.08), tubes_pink (letters, role neon_pink), tubes_cyan (border + flick, role neon_cyan) "
             "- separate meshes so Unity can pulse/flicker emission independently. Origin bottom centre; mount with bottom at z 5.75 above the club arch, back face on the wall brackets.")
    return root, dict(category="sign", views=("front", "front34"), notes=notes)


# ================================================================================================= queue barriers

def build_club_queue_barriers():
    mb = MB()
    xs = [-1.5, -0.5, 0.5, 1.5]
    for x in xs:
        mb.lathe([(0.0, 0), (0.18, 0), (0.18, 0.025), (0.13, 0.045), (0.04, 0.07), (0.03, 0.92), (0.05, 0.95), (0.05, 0.98), (0.0, 1.0)], "metal_chrome", 18, base=(x, 0, 0))
        mb.sphere((x, 0, 1.04), 0.05, "metal_chrome", 1)
        mb.lathe([(0.03, 0.86), (0.045, 0.86), (0.045, 0.9), (0.03, 0.9)], "metal_chrome", 12, base=(x, 0, 0))
    for a, b in zip(xs[:-1], xs[1:]):
        pts = [(a + 0.05 + (b - a - 0.1) * t, 0.0, 0.9 - 0.17 * math.sin(math.pi * t)) for t in [i / 14 for i in range(15)]]
        mb.tube(pts, 0.024, "rope_red", 8)
        for p in (pts[0], pts[-1]):
            mb.sphere(p, 0.03, "metal_chrome", 1)
    root = mb.build("exterior_club_queue_barriers")
    notes = "4 chrome stanchions 1.04 m with red velvet ropes, 3.0 m line along x. Origin bottom centre of the line. Place in front of the club door (x ~3.5, y -1.2) rotated as needed."
    return root, dict(category="props", views=("front", "front34"), notes=notes)


# ================================================================================================= posters hoarding

def build_club_posters_hoarding():
    W, H = 3.6, 2.4
    mb = MB()
    tf = frame_tf((-W / 2, 0.0, 0.0), (1, 0, 0), (0, 0, 1))
    mb.box((0.0, 0.05, -0.02), (W, H, 0.0), "hoarding_wood", tf)
    for u in (0.06, W / 2, W - 0.06):
        mb.box((u - 0.05, 0.0, -0.12), (u + 0.05, H + 0.08, -0.02), "wood_dark", tf)
    mb.box((0.0, 0.0, -0.12), (W, 0.12, -0.02), "wood_dark", tf)
    mb.box((0.0, H - 0.1, -0.12), (W, H, -0.02), "wood_dark", tf)
    rnd = random.Random(9)
    roles = ["poster_a", "poster_b", "poster_c", "poster_d", "poster_e", "poster_a", "poster_b", "poster_c"]
    pw, ph = 0.6, 0.85
    k = 0
    for row, zb in ((0, 1.35), (1, 0.32)):
        u = 0.1 + (0.15 if row else 0.0)
        while u + pw < W - 0.05:
            rot = rnd.uniform(-0.05, 0.05) if rnd.random() < 0.6 else 0.0
            base = roles[k % len(roles)]
            poster(mb, tf, u, zb + rnd.uniform(-0.04, 0.04), pw, ph, 0.001 + 0.0015 * (k % 3), base, rot, seed=k, headline="poster_white" if base != "poster_white" else "poster_d")
            k += 1
            u += pw + rnd.uniform(0.02, 0.12)
    # a torn poster remnant and one pasted over the top at an angle
    mb.face([tf((0.4, 2.0, 0.006)), tf((0.9, 2.0, 0.006)), tf((0.75, 2.3, 0.006)), tf((0.5, 2.28, 0.006))], "poster_white")
    poster(mb, tf, 1.5, 0.9, 0.5, 0.7, 0.007, "poster_c", 0.18, seed=77, headline="poster_d")
    root = mb.build("exterior_club_posters_hoarding")
    recentre_root(root)
    notes = ("Plywood hoarding 3.6 x 2.4 m with ~10 pasted gig posters (roles poster_a..e + poster_white bands; each poster has headline/image/text blocks as separate colour quads). "
             "Origin bottom centre; back of the posts is at y +0.06 - place against the club wall at x -5.4.")
    return root, dict(category="props", views=("front", "front34"), notes=notes)


# ================================================================================================= speaker wall

def build_club_speaker_wall():
    mb = MB()
    tilt = 0.18
    for sx in (-0.62, 0.62):
        ctf = frame_tf((sx, 0.0, 0.0), (1, 0, 0), (0, -math.sin(tilt), math.cos(tilt)))      # e3 points to -Y (street) and down
        mb.box((-0.32, 0.0, 0.0), (0.32, 0.92, 0.46), "speaker_black", ctf, inset=0.015, inset_face="+z")
        mb.box((-0.27, 0.05, 0.455), (0.27, 0.87, 0.465), "speaker_grille", ctf)
        circ = [ctf((0.19 * math.cos(a), 0.30 + 0.19 * math.sin(a), 0.47)) for a in [2 * math.pi * i / 20 for i in range(21)]]
        mb.tube(circ, 0.02, "speaker_black", 8, caps=False)
        mb.cyl((0.0, 0.30, 0.465), 0.16, 0.06, 0.03, "interior_dark", 16, ctf, caps=(False, True))
        mb.cyl((0.0, 0.70, 0.465), 0.05, 0.15, 0.07, "speaker_black", 4, ctf, caps=(False, True), cap_role="interior_dark", phase=math.pi / 4, smooth=False)
        for (cx_, cy_) in ((-0.3, 0.02), (0.3, 0.02), (-0.3, 0.9), (0.3, 0.9)):     # corner protectors
            mb.box((cx_ - 0.03, cy_ - 0.02, 0.40), (cx_ + 0.03, cy_ + 0.02, 0.47), "metal_painted_grey", ctf)
        mb.box((-0.06, 0.4, -0.01), (0.06, 0.55, 0.0), "metal_painted_grey", ctf)        # back handle plate
        # bracket arms to the wall plate (wall at y = +0.32)
        for (ax, az) in ((-0.22, 0.1), (0.22, 0.1), (0.0, 0.8)):
            mb.bar(ctf((ax, az, 0.0)), (sx + ax, 0.32, az if az < 0.5 else 0.75), 0.035, "metal_painted_black")
        mb.box((sx - 0.3, 0.30, 0.0), (sx + 0.3, 0.33, 0.9), "metal_painted_black")
    # cable between cabinets and down the wall
    mb.tube([(-0.5, 0.25, 0.06), (-0.2, 0.28, -0.05), (0.2, 0.28, -0.05), (0.5, 0.25, 0.06)], 0.012, "rubber_black", 6)
    mb.tube([(0.0, 0.30, -0.02), (0.0, 0.30, -0.6)], 0.012, "rubber_black", 6)
    root = mb.build("exterior_club_speaker_wall")
    recentre_root(root)
    notes = ("Two wall-hung PA cabinets (0.64 x 0.92 m) tilted 10 deg down towards the street, on steel brackets with a wall plate (back face at y +0.16 after recentring). "
             "Origin bottom centre; hang with bottom at z 3.3 above the hoarding on the club wall (x -5.4).")
    return root, dict(category="props", views=("front", "front34"), notes=notes)


# ================================================================================================= club props

def keg(mb, x, y, z=0.0, tf=None):
    prof = [(0.0, 0), (0.185, 0), (0.20, 0.012), (0.20, 0.06), (0.182, 0.075), (0.182, 0.43), (0.20, 0.445), (0.20, 0.495), (0.185, 0.505), (0.0, 0.505)]
    tf = tf or IDENT
    mb.lathe(prof, "keg_steel", 20, tf, base=(x, y, z), rolemap={1: "metal_steel", 2: "metal_steel", 6: "metal_steel", 7: "metal_steel"})
    mb.cyl((x, y, z + 0.505), 0.14, 0.14, 0.002, "interior_dark", 16, tf)


def bollard(mb, x, y):
    prof = [(0.0, 0), (0.13, 0), (0.13, 0.05), (0.095, 0.09), (0.085, 0.58), (0.085, 0.70), (0.085, 0.80), (0.105, 0.84), (0.105, 0.92), (0.065, 0.97), (0.0, 1.02)]
    mb.lathe(prof, "metal_painted_black", 16, base=(x, y, 0), rolemap={4: "road_paint_white"})


def big_bin(mb, x, y, rot, role):
    tf = frame_tf((x, y, 0), (math.cos(rot), math.sin(rot), 0), (0, 0, 1))
    w, d = 1.2, 1.0
    mb.box((-w / 2, -d / 2, 0.22), (w / 2, d / 2, 1.3), role, tf, inset=0.02, inset_face="-z")
    mb.box((-w / 2 - 0.02, -d / 2 - 0.02, 1.3), (w / 2 + 0.02, d / 2 + 0.02, 1.36), role, tf)
    mb.poly_prism([(-d / 2 - 0.02, 1.36), (d / 2 + 0.02, 1.36), (d / 2 - 0.08, 1.48), (0.0, 1.56), (-d / 2 + 0.08, 1.48)], -w / 2 - 0.02, w / 2 + 0.02, role,
                  frame_tf(tf((0, 0, 0)), (Vector(tf((0, 1, 0))) - Vector(tf((0, 0, 0)))), (0, 0, 1)))
    for (wx, wy) in ((-w / 2 + 0.12, -d / 2 + 0.1), (w / 2 - 0.12, -d / 2 + 0.1), (-w / 2 + 0.12, d / 2 - 0.1), (w / 2 - 0.12, d / 2 - 0.1)):
        mb.cyl((0, 0, 0), 0.1, 0.1, 0.05, "rubber_black", 12, frame_tf(tf((wx - 0.025, wy, 0.1)), (0, 1, 0), (0, 0, 1)), cap_role="plastic_grey")
    mb.bar(tf((-w / 2 + 0.1, -d / 2 - 0.05, 0.95)), tf((w / 2 - 0.1, -d / 2 - 0.05, 0.95)), 0.035, role)
    mb.box((-0.25, -d / 2 - 0.003, 0.5), (0.25, -d / 2 - 0.0, 0.8), "poster_white", tf)      # council label


def build_club_props():
    mb = MB()
    rnd = random.Random(4)
    # kegs stacked by the door (right of the entrance)
    for (x, y) in ((5.0, -0.55), (5.45, -0.55), (5.9, -0.55)):
        keg(mb, x, y)
    for (x, y) in ((5.22, -0.55), (5.68, -0.55)):
        keg(mb, x, y, 0.505)
    keg(mb, 0, 0, 0, frame_tf((5.0, -1.15, 0.2), (0, 1, 0), (0, 0, 1)))     # one lying on its side along x
    # commercial bins at the left end
    big_bin(mb, -6.6, -0.95, 0.08, "plastic_blue")
    big_bin(mb, -5.2, -1.0, -0.05, "plastic_dark_green")
    # bollards along the kerb line
    for x in (-2.5, -0.5, 1.5):
        bollard(mb, x, -1.9)
    # cigarette bin post in the smoking area
    mb.cyl((6.8, -0.5, 0.0), 0.08, 0.08, 0.03, "metal_painted_black", 12)
    mb.cyl((6.8, -0.5, 0.03), 0.03, 0.03, 0.95, "metal_painted_black", 10)
    mb.cyl((6.8, -0.5, 0.98), 0.09, 0.09, 0.32, "metal_painted_black", 14)
    mb.box((6.71, -0.6, 1.17), (6.89, -0.56, 1.2), "interior_dark")
    mb.lathe([(0.09, 1.30), (0.10, 1.31), (0.0, 1.34)], "metal_painted_black", 14, base=(6.8, -0.5, 0))
    # traffic cone
    mb.box((-3.2, -2.5, 0.0), (-2.8, -2.1, 0.03), "plastic_black")
    mb.lathe([(0.0, 0.03), (0.15, 0.03), (0.13, 0.08), (0.12, 0.28), (0.11, 0.40), (0.08, 0.64), (0.0, 0.70)], "plastic_red", 14, base=(-3.0, -2.3, 0),
             rolemap={3: "road_paint_white"})
    # flyers on the ground
    for i in range(16):
        x = rnd.uniform(1.5, 5.5)
        y = rnd.uniform(-2.3, -0.5)
        rot = rnd.uniform(0, math.pi)
        c, s = math.cos(rot), math.sin(rot)
        def P(u, v, z=0.002):
            return (x + u * c - v * s, y + u * s + v * c, z)
        base = rnd.choice(["poster_a", "poster_b", "poster_c", "poster_e", "poster_white"])
        lift = rnd.uniform(0.0, 0.03)
        mb.face([P(-0.075, -0.105), P(0.075, -0.105), P(0.075, 0.105, 0.002 + lift), P(-0.075, 0.105, 0.002 + lift)], base)
        mb.face([P(-0.06, 0.02, 0.0025 + lift * 0.6), P(0.06, 0.02, 0.0025 + lift * 0.6), P(0.06, 0.07, 0.0025 + lift * 0.85), P(-0.06, 0.07, 0.0025 + lift * 0.85)],
                "poster_d" if base != "poster_d" else "poster_white")
    # crushed cans
    for i in range(5):
        x, y = rnd.uniform(-1, 6), rnd.uniform(-2.2, -0.4)
        mb.cyl((0, 0, 0), 0.033, 0.033, 0.11, rnd.choice(["foil", "plastic_red", "plastic_blue"]), 10, frame_tf((x, y, 0.033), (0, 0, 1), (math.cos(i), math.sin(i), 0)))
    root = mb.build("exterior_club_props")
    notes = ("Club pavement clutter. Origin = SAME as exterior_club_building origin (drop at the club origin): 6 beer kegs by the door (x 4.8..6.1), two 1100 L bins at x -7.2..-4.6, "
             "3 bollards at y -1.9, cigarette bin at (6.8,-0.5), traffic cone (-3,-2.3), flyers + cans on the pavement around the door. Pavement assumed y 0..-2.")
    return root, dict(category="props", views=("front", "front34"), notes=notes)


# ================================================================================================= arch bridge backdrop

def lit_windows(mb, x0, x1, y, z0, z1, rnd, p_lit=0.35, p_tv=0.08, pitch_x=2.6, pitch_z=3.0, w=1.2, h=1.4, proud=0.02):
    cols = max(1, int((x1 - x0 - 1.0) / pitch_x))
    rows = max(1, int((z1 - z0 - 1.5) / pitch_z))
    for c in range(cols):
        for r_ in range(rows):
            cx = x0 + (x1 - x0) / 2 + (c - (cols - 1) / 2) * pitch_x
            cz = z0 + 1.2 + r_ * pitch_z
            u = rnd.random()
            if u < p_lit:
                role = "window_lit"
            elif u < p_lit + p_tv:
                role = "window_tv"
            else:
                continue
            yy = y - proud
            mb.face([(cx - w / 2, yy, cz), (cx + w / 2, yy, cz), (cx + w / 2, yy, cz + h), (cx - w / 2, yy, cz + h)], role)


def build_arch_bridge_backdrop():
    mb = MB()
    rnd = random.Random(12)
    W, Dp = 40.0, 8.0
    n, r, pier, zs = 6, 2.75, 1.0, 4.2
    deck, par = 8.6, 9.6
    role = "brick_sooty"
    tf = frame_tf((-W / 2, 0.0, 0.0), (1, 0, 0), (0, 0, 1))
    for i in range(n + 1):
        px = i * (2 * r + pier)
        mb.box((px, 0.0, 0.0), (px + pier, deck - 0.5, 0.0) if False else (px, 0.0, 0.0), role) if False else None
        mb.box((-W / 2 + px, 0.0, 0.0), (-W / 2 + px + pier, Dp, zs), role, skip=("-z",))
    centres = [pier + i * (2 * r + pier) + r for i in range(n)]
    # spandrel wall (rows) above the spring line, arches subtracted
    z = zs
    while z < deck - 0.5:
        z1 = min(z + 0.3, deck - 0.5)
        zc = (z + z1) / 2
        strips = [(0.0, W)]
        for cx in centres:
            if zc < zs + r:
                half = math.sqrt(r * r - (zc - zs) ** 2)
                strips = _subtract(strips, cx - half, cx + half)
        for (a, b) in strips:
            mb.face([tf((a, z, 0)), tf((b, z, 0)), tf((b, z1, 0)), tf((a, z1, 0))], role)
        z = z1
    for k, cx in enumerate(centres):
        arch_ring(mb, tf, cx, zs, r, Dp, "brick_sooty_light", n=16, thick=0.36, proud=0.04, jamb_to=None)
        if k in (1, 4):      # bricked-up workshop arch: shutter + small lit window
            shutter_corrugated(mb, tf, cx - r + 0.1, cx + r - 0.1, 0.0, zs + 0.3, -0.5, slat=0.12, amp=0.02)
            mb.face([tf((cx - r - 0.2, zs, -0.52)), tf((cx + r + 0.2, zs, -0.52)), tf((cx + r + 0.2, zs + r + 0.2, -0.52)), tf((cx - r - 0.2, zs + r + 0.2, -0.52))], "render_dark")
            mb.face([tf((cx - 0.6, zs + 0.5, -0.51)), tf((cx + 0.6, zs + 0.5, -0.51)), tf((cx + 0.6, zs + 1.4, -0.51)), tf((cx - 0.6, zs + 1.4, -0.51))], "window_lit")
        else:                # open arch: dark depth
            mb.face([tf((cx - r - 0.2, 0.0, -(Dp - 0.6))), tf((cx + r + 0.2, 0.0, -(Dp - 0.6))), tf((cx + r + 0.2, zs + r + 0.2, -(Dp - 0.6))), tf((cx - r - 0.2, zs + r + 0.2, -(Dp - 0.6)))], "interior_dark")
    # deck slab, parapets, coping, OLE masts
    mb.box((-W / 2 - 0.3, -0.25, deck - 0.5), (W / 2 + 0.3, Dp + 0.25, deck), "concrete")
    mb.box((-W / 2 - 0.3, -0.25, deck), (W / 2 + 0.3, 0.2, par), role)
    mb.box((-W / 2 - 0.35, -0.3, par), (W / 2 + 0.35, 0.25, par + 0.15), "stone_sill")
    mb.box((-W / 2 - 0.3, Dp - 0.2, deck), (W / 2 + 0.3, Dp + 0.25, par), role)
    for x in (-15.0, -5.0, 5.0, 15.0):
        mb.bar((x, 1.0, deck), (x, 1.0, deck + 7.0), 0.25, "metal_painted_grey")
        mb.bar((x, 1.0, deck + 6.5), (x, Dp - 1.0, deck + 6.5), 0.12, "metal_painted_grey")
    mb.tube([(-W / 2, 2.0, deck + 5.9), (W / 2, 2.0, deck + 5.9)], 0.02, "metal_dark", 6)
    # rooftops behind the viaduct (low poly, lit windows)
    for (x0, x1, y0, y1, h, rl) in ((-19, -10, 14, 24, 11, "skyline_mid"), (-9, -2, 16, 26, 14, "skyline_mid"), (0, 7, 13, 22, 9.5, "skyline_mid"),
                                    (8, 16, 15, 27, 16, "skyline_mid"), (17, 22, 14, 20, 12, "skyline_mid")):
        mb.box((x0, y0, 0.0), (x1, y1, h), rl, skip=("-z",))
        mb.box((x0 - 0.15, y0 - 0.15, h), (x1 + 0.15, y1 + 0.15, h + 0.4), rl)
        lit_windows(mb, x0, x1, y0, 1.0, h - 1.0, rnd, p_lit=0.3)
        for k in range(int((x1 - x0) / 4)):
            chx = x0 + 1.5 + k * 4
            mb.box((chx - 0.4, y0 + 2, h), (chx + 0.4, y0 + 2.8, h + 1.6), "brick_sooty_dark")
    # water tank on legs + a rooftop sign frame
    mb.cyl((12.0, 20.0, 18.5), 1.6, 1.6, 2.2, "corrugated_metal", 14)
    mb.cyl((12.0, 20.0, 20.7), 1.6, 0.3, 0.6, "corrugated_metal", 14)
    for (dx, dy) in ((-1.1, -1.1), (1.1, -1.1), (-1.1, 1.1), (1.1, 1.1)):
        mb.bar((12.0 + dx, 20.0 + dy, 16.0), (12.0 + dx, 20.0 + dy, 18.5), 0.15, "metal_painted_grey")
    root = mb.build("exterior_arch_bridge_backdrop")
    notes = ("Distant backdrop for the club view: 40 m brick railway viaduct (6 arches r 2.75, deck 8.6 m, parapet 9.6 m, OLE masts to 15.6 m), two arches are workshops with "
             "shutters + a lit window, the others read as deep dark openings. Behind it (y 13-27) five low-poly rooftops with lit windows, chimneys and a water tank. Faces -Y; origin ground centre of the front face. "
             "Place ~25-40 m behind the club building.")
    return root, dict(category="backdrop", views=("front", "front34"), notes=notes)


# ================================================================================================= skyline

def skyline_building(mb, x, y0, w, d, h, role, rnd, tower=False):
    mb.box((x, y0, 0.0), (x + w, y0 + d, h), role, skip=("-z",))
    mb.box((x - 0.2, y0 - 0.2, h), (x + w + 0.2, y0 + d + 0.2, h + 0.5), role)
    lit_windows(mb, x, x + w, y0, 1.0, h - 1.0, rnd, p_lit=0.36 if tower else 0.28, p_tv=0.08, pitch_x=2.8 if tower else 2.4, pitch_z=2.9)
    if tower:
        mb.box((x + w * 0.3, y0 + d * 0.3, h + 0.5), (x + w * 0.6, y0 + d * 0.7, h + 3.2), role)
        mb.bar((x + w * 0.45, y0 + d * 0.5, h + 3.2), (x + w * 0.45, y0 + d * 0.5, h + 6.0), 0.15, "metal_painted_grey")
        if h > 38:
            mb.box((x + w * 0.45 - 0.2, y0 + d * 0.5 - 0.2, h + 6.0), (x + w * 0.45 + 0.2, y0 + d * 0.5 + 0.2, h + 6.4), "led_red")
    else:
        for k in range(max(1, int(w / 3.5))):
            cx = x + 1.2 + k * 3.5
            if cx < x + w - 0.6:
                mb.box((cx - 0.35, y0 + d * 0.45, h), (cx + 0.35, y0 + d * 0.45 + 0.7, h + 1.4), "skyline_dark")
        if rnd.random() < 0.4:
            mb.bar((x + w * 0.7, y0 + d * 0.5, h + 0.5), (x + w * 0.7, y0 + d * 0.5, h + 3.0), 0.08, "metal_painted_grey")


def build_skyline_backdrop():
    mb = MB()
    rnd = random.Random(42)
    W = 120.0
    x = -W / 2
    while x < W / 2 - 4:
        w = rnd.uniform(4.5, 9.0)
        h = rnd.uniform(8.0, 22.0)
        skyline_building(mb, x, rnd.uniform(0.0, 4.0), w, rnd.uniform(8, 14), h, "skyline_dark", rnd)
        x += w + rnd.uniform(0.0, 1.6)
    x = -W / 2 + 2.0
    while x < W / 2 - 10:
        w = rnd.uniform(8.0, 16.0)
        h = rnd.uniform(24.0, 58.0)
        skyline_building(mb, x, rnd.uniform(24.0, 34.0), w, rnd.uniform(10, 16), h, "skyline_mid", rnd, tower=True)
        x += w + rnd.uniform(2.0, 9.0)
    # tower crane
    cx, cy = 22.0, 20.0
    mb.bar((cx, cy, 0), (cx, cy, 48.0), 1.2, "metal_painted_grey")
    mb.bar((cx - 28.0, cy, 47.0), (cx + 10.0, cy, 47.0), 1.0, "metal_painted_grey")
    mb.bar((cx, cy, 48.0), (cx - 26.0, cy, 47.5), 0.15, "metal_dark")
    mb.box((cx + 7.0, cy - 1.0, 45.5), (cx + 10.0, cy + 1.0, 47.0), "concrete")
    mb.box((cx - 0.3, cy - 0.3, 48.0), (cx + 0.3, cy + 0.3, 48.5), "led_red")
    # gasholder frame
    gx, gy, gr = -42.0, 30.0, 11.0
    for zz in (6.0, 14.0, 22.0):
        mb.tube([(gx + gr * math.cos(a), gy + gr * math.sin(a), zz) for a in [2 * math.pi * i / 24 for i in range(25)]], 0.3, "metal_painted_grey", 6, caps=False)
    for i in range(12):
        a = 2 * math.pi * i / 12
        mb.bar((gx + gr * math.cos(a), gy + gr * math.sin(a), 0.0), (gx + gr * math.cos(a), gy + gr * math.sin(a), 23.0), 0.5, "metal_painted_grey")
    mb.cyl((gx, gy, 0.0), gr - 0.6, gr - 0.6, 9.0, "skyline_dark", 24)
    root = mb.build("exterior_skyline_backdrop")
    notes = ("120 m low-poly city silhouette band: front row of 8-22 m rooftops (role skyline_dark, y 0-18) and a back row of 24-58 m tower blocks (skyline_mid, y 24-50), lit windows as "
             "separate emissive quads (window_lit warm / window_tv blue), red led_red warning lights on tall towers + crane, a gasholder frame at x -42. Faces -Y; origin ground centre. "
             "Place 150-300 m away and scale up if needed; it is a flat-ish band, do not look at it from the side.")
    return root, dict(category="backdrop", views=("front", "front34"), notes=notes)


# ================================================================================================= street tree

def build_tree_street():
    mb = MB()
    rnd = random.Random(5)
    segs = 12
    levels = [(0.0, 0.34), (0.12, 0.27), (0.5, 0.22), (1.1, 0.20), (1.8, 0.185), (2.4, 0.17), (2.8, 0.16)]
    rings = []
    for (z, r) in levels:
        ring = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            n = noise.noise(Vector((math.cos(a) * 1.7 + 3.1, math.sin(a) * 1.7, z * 1.3)))
            rr = r * (1 + 0.14 * n) + (0.09 * max(0, math.cos(3 * a)) if z < 0.2 else 0)      # root flare
            ring.append(Vector((rr * math.cos(a) + 0.04 * math.sin(z * 1.7), rr * math.sin(a) + 0.03 * math.cos(z * 2.1), z)))
        rings.append(ring)
    for A, B in zip(rings[:-1], rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            mb.face([A[i], A[j], B[j], B[i]], "bark", True)
    mb.face(list(reversed(rings[0])), "bark")
    top = rings[-1]
    # main branches (tapered tubes) + secondary twigs
    dirs = [(1.0, 0.2), (-0.8, 0.6), (0.1, -1.0), (-0.5, -0.7), (0.7, -0.5)]
    tips = []
    for k, (dx, dy) in enumerate(dirs):
        d = Vector((dx, dy, 0)).normalized()
        base = Vector((d.x * 0.08, d.y * 0.08, 2.65 + 0.08 * k))
        pts = [base]
        for s in range(1, 5):
            t = s / 4
            pts.append(Vector((d.x * (0.4 + 1.3 * t) + 0.15 * math.sin(3 * t + k), d.y * (0.4 + 1.3 * t) + 0.15 * math.cos(2 * t + k), 2.65 + 0.08 * k + 1.9 * t - 0.4 * t * t)))
        mb.tube(pts, 0.1, "bark", 8, taper=(0.11, 0.035))
        tips.append(pts[-1])
        for s in (1, 2):
            p0 = pts[s]
            side = Vector((-d.y, d.x, 0)) * (0.5 if s == 1 else -0.5)
            mb.tube([p0, p0 + side * 0.6 + Vector((0, 0, 0.5)), p0 + side * 1.0 + Vector((0, 0, 1.0))], 0.03, "bark", 6, taper=(0.04, 0.012))
    # canopy: lumpy leaf-cluster masses
    blobs = [((0, 0, 4.7), 1.55, "leaf_green"), ((1.2, 0.4, 4.3), 1.25, "leaf_dark"), ((-1.1, 0.8, 4.4), 1.2, "leaf_green"), ((0.2, -1.3, 4.2), 1.2, "leaf_green"),
             ((-0.7, -0.9, 4.0), 1.05, "leaf_dark"), ((0.9, -0.6, 5.1), 1.05, "leaf_green"), ((-0.4, 0.3, 5.5), 1.05, "leaf_dark"), ((0.5, 1.2, 5.0), 0.95, "leaf_green"),
             ((-1.4, -0.2, 4.9), 0.9, "leaf_green")]
    for i, (c, rr, rl) in enumerate(blobs):
        mb.sphere(c, rr, rl, 2, scale=(1.0, 1.0, 0.78), noise_amp=0.2, noise_scale=1.6, seed=i)
    # tree pit grille
    mb.box((-0.7, -0.7, 0.0), (0.7, 0.7, 0.03), "drain_iron")
    for k in range(6):
        mb.box((-0.6 + k * 0.2 + 0.07, -0.6, 0.03), (-0.6 + k * 0.2 + 0.13, 0.6, 0.032), "interior_dark")
    root = mb.build("exterior_tree_street")
    notes = ("Street tree ~6.3 m: irregular trunk with root flare, 5 tapered branches with twigs, 9 noise-displaced leaf masses (leaf_green / leaf_dark), cast-iron tree grille 1.4 m at the base. "
             "Origin at the trunk base. Canopy spans ~4.6 m; keep 2.5 m from facades.")
    return root, dict(category="nature", views=("front", "front34"), notes=notes)


BUILDERS = {
    "club_building": build_club_building,
    "club_neon_sign": build_club_neon_sign,
    "club_queue_barriers": build_club_queue_barriers,
    "club_posters_hoarding": build_club_posters_hoarding,
    "club_speaker_wall": build_club_speaker_wall,
    "club_props": build_club_props,
    "arch_bridge_backdrop": build_arch_bridge_backdrop,
    "skyline_backdrop": build_skyline_backdrop,
    "tree_street": build_tree_street,
}
