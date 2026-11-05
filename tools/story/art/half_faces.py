"""The half-size (LOD 2) faces of the four species whose heads are too small for the full-size rules (greys, skeletons, cyclops, insects).

At the half level of detail a head is 5 to 9 pixels wide, so a mood is not a drawn expression but a handful of pixels that must differ from every other mood's
at silhouette level: the eye's shape (round, slanted, closed arc, drooping line), the brow, a tear column, an open mouth or a jaw dropped, the teeth. Each face
is a small picture: rows (offsets from the eye row, `ey`) of equal-width strings centred on the face's centre column; `.` leaves the pixel alone.

Legend (material, step):  D eye_d EDGE   d eye_d DARK   W eye_w LIT   w eye_w MID   T glass LIT   t glass MID   u glass DARK
                          M mouth EDGE   m mouth DARK   E teeth LIT   e teeth MID   S skin DARK  s skin EDGE   L skin LIT   Q skin2 MID
                          H horn DARK    h horn EDGE    l horn LIT    X extra DARK

`tests` (tools/story/test_faces_lod2.py) and `tools/story/check_assets.py` require every face of these species to differ from every other by at least
MIN_DIFF pixels at the half level (the rendered, coloured heads), the pairs the owner listed (relief / grief / laugh, anger / doubt / shame) included.
"""
from __future__ import annotations

LEGEND = {
    "D": ("eye_d", 0), "d": ("eye_d", 1), "W": ("eye_w", 3), "w": ("eye_w", 2),
    "T": ("glass", 3), "t": ("glass", 2), "u": ("glass", 1),
    "M": ("mouth", 0), "m": ("mouth", 1), "E": ("teeth", 3), "e": ("teeth", 2),
    "S": ("skin", 1), "s": ("skin", 0), "L": ("skin", 3), "Q": ("skin2", 2),
    "H": ("horn", 1), "h": ("horn", 0), "l": ("horn", 3), "X": ("extra", 1),
}

MIN_DIFF = 5  # the least number of pixels two faces of one head may differ by at the half level

# --- grey: a 9 pixel head, interior 7 wide; the eyes are the face ---------------------------------------------------------------------------------------
GREY = {
    "neutral": {-1: "DD...DD", 0: ".DD.DD.", 3: "...m..."},
    "happy":   {-1: ".D...D.", 0: "D.D.D.D", 2: ".m...m.", 3: "..mmm.."},
    "cheer":   {-2: ".D...D.", -1: "D.D.D.D", 2: "..EEE..", 3: "..mmm.."},
    "sad":     {-1: "..D.D..", 0: ".DD.DD.", 1: "D.....D", 3: "...m..."},
    "fear":    {-1: ".DD.DD.", 0: ".WD.DW.", 1: ".DD.DD.", 3: "...m...", 4: "...m..."},
    "anger":   {-2: "SS...SS", -1: "..SSS..", 0: ".DDDDD.", 3: ".EEEEE."},
    "plea":    {-2: "..S.S..", -1: ".DD.DD.", 0: ".WD.DW.", 1: ".DD.DD.", 3: ".mm.mm."},
    "doubt":   {-3: "SSS....", -1: "DD.....", 0: ".DD.DDD", 3: "....mm.", 4: ".mm...."},
    "relief":  {1: "DDD.DDD", 2: "Q.....Q", 3: "..mmm..", 4: "..mmm.."},
    "awe":     {-1: "DDD.DDD", 0: "DWD.DWD", 1: "DDD.DDD", 3: "..mmm..", 4: "..mmm.."},
    "grief":   {-2: "..S.S..", -1: "..D.D..", 0: ".D...D.", 1: "D.....D", 2: "T.mmm.T", 3: "t.m.m.t"},
    "laugh":   {-1: ".D...D.", 0: "D.D.D.D", 2: ".EEEEE.", 3: ".mmmmm.", 4: "..mmm.."},
    "resolve": {-2: "SSSSSSS", 0: ".DD.DD.", 1: ".DD.DD.", 3: ".mmmmm."},
    "shame":   {2: ".DD.DD.", 3: "Q.....Q"},
}

# --- cyclops: a 9 pixel head, one great eye across the interior (7 wide); lids and brow carry the mood ------------------------------------------------------
CYCLOPS = {
    "neutral": {-1: ".WWWWW.", 0: ".WDDDW.", 1: "..sss..", 3: "..mmm.."},
    "happy":   {-1: "..sss..", 0: ".WDDDW.", 1: ".sssss.", 2: ".m...m.", 3: "..mmm.."},
    "cheer":   {-2: "..LLL..", -1: ".WWWWW.", 0: ".WDDDW.", 2: ".EEEEE.", 3: "..mmm.."},
    "sad":     {-2: "S.....S", -1: ".sSSSs.", 0: ".WDDDW.", 1: ".WWWWW.", 3: "..mmm..", 4: ".m...m."},
    "fear":    {-2: ".WWWWW.", -1: "WWWDWWW", 0: "WWDDDWW", 1: ".WWDWW.", 3: ".mmmmm.", 4: "..mmm.."},
    "anger":   {-2: "SS...SS", -1: "..SSS..", 0: ".DDDDD.", 3: ".EEEEE.", 4: "m.....m"},
    "plea":    {-2: "..S.S..", -1: ".WDDDW.", 0: ".WDDDW.", 1: ".WWWWW.", 3: "...m...", 4: "..m.m.."},
    "doubt":   {-3: "SSS....", -1: ".sssss.", 0: ".WDDDW.", 3: "...mmm.", 4: ".mm...."},
    "relief":  {-1: "..sss..", 0: ".s...s.", 1: "Q.....Q", 3: "..mmm..", 4: "...m..."},
    "awe":     {-2: ".WWWWW.", -1: "WWDDDWW", 0: "WWDWDWW", 1: ".WDDDW.", 3: "..mmm..", 4: "..mmm.."},
    "grief":   {-2: "..S.S..", 0: ".s...s.", 1: "..sss..", 2: "......T", 3: ".mmmm.T", 4: ".m...mT"},
    "laugh":   {-2: "..LLL..", -1: "..sss..", 0: ".s...s.", 2: ".EEEEE.", 3: ".mmmmm.", 4: "..mmm.."},
    "resolve": {-2: "SSSSSSS", -1: ".WWWWW.", 0: ".WDDDW.", 1: ".sssss.", 3: ".mmmmm."},
    "shame":   {-1: "sssssss", 0: ".W...W.", 1: ".WDDDW.", 2: "Q.....Q", 3: "..m.m.."},
}

# --- insect: a 5 pixel head (interior 5 wide), compound eyes at the sides, mandibles as the mouth ----------------------------------------------------------
INSECT = {
    "neutral": {-1: ".D.D.", 0: ".D.D.", 2: "M...M", 3: ".M.M."},
    "happy":   {0: ".D.D.", 1: "M...M", 2: ".M.M."},
    "cheer":   {-1: "L...L", 0: ".D.D.", 1: "M...M", 2: "M...M", 3: "..m.."},
    "sad":     {-1: "D...D", 0: ".D.D.", 1: ".D.D.", 3: ".M.M.", 2: "M...M"},
    "fear":    {-2: ".D.D.", -1: ".D.D.", 0: ".D.D.", 2: "M...M", 3: "M.m.M"},
    "anger":   {-1: "D...D", 0: ".D.D.", 2: ".MMM.", 3: "M...M"},
    "plea":    {-1: ".D.D.", 0: ".W.W.", 1: ".D.D.", 3: ".M.M."},
    "doubt":   {-2: ".S...", -1: ".D...", 0: ".D.s.", 1: "....S", 2: "M....", 3: "..M.M"},
    "relief":  {0: ".D.D.", 1: ".....", 2: "..M..", 3: ".M.M."},
    "awe":     {-2: ".W.W.", -1: ".D.D.", 0: ".D.D.", 1: ".D.D.", 3: "..m.."},
    "grief":   {0: ".D.D.", 1: ".t.t.", 2: ".T.T.", 3: ".M.M."},
    "laugh":   {0: "D...D", 1: ".D.D.", 2: "M.m.M", 3: "M.m.M"},
    "resolve": {0: "DD.DD", 2: ".MMM.", 3: "..M.."},
    "shame":   {1: ".D.D.", 2: "L...L", 3: "..M.."},
}

# --- skeleton: a 5 pixel skull (interior 5 wide, tMe cMin 3): sockets, nasal cavity, teetM and tMe jaw -----------------------------------------------------
SKELETON = {
    "neutral": {-1: ".D.D.", 0: ".D.D.", 1: "..s..", 2: "EeEeE"},
    "happy":   {0: ".D.D.", 1: "L...L", 2: "EEEEE"},
    "cheer":   {-1: ".D.D.", 1: "L...L", 2: "EEEEE", 3: ".DDD."},
    "sad":     {0: ".D.D.", 1: ".D.D.", 2: ".eee.", 3: "..S.."},
    "fear":    {-2: ".D.D.", -1: ".D.D.", 0: ".D.D.", 2: "EEEEE", 3: "DDDDD"},
    "anger":   {-1: "D...D", 0: ".D.D.", 1: "S...S", 2: "EEEEE", 3: ".MMM."},
    "plea":    {-1: ".D.D.", 0: ".D.D.", 1: ".D.D.", 2: ".EEE.", 3: "..D.."},
    "doubt":   {-1: ".D...", 0: ".D.D.", 2: "EEEE.", 3: "..DD."},
    "relief":  {0: ".S.S.", 1: "L.s.L", 2: "EeEeE"},
    "awe":     {-2: ".D.D.", -1: ".D.D.", 0: ".D.D.", 1: ".D.D.", 3: ".DDD."},
    "grief":   {0: ".D.D.", 1: ".t.t.", 2: ".u.u.", 3: ".EEE."},
    "laugh":   {0: "D...D", 1: "S...S", 2: "EEEEE", 3: ".DDD."},
    "resolve": {-1: "SSSSS", 0: ".D.D.", 2: ".EEE.", 3: ".MMM."},
    "shame":   {1: ".D.D.", 2: "S.e.S", 3: ".EEE."},
}



def _merge(*parts):
    out = {}
    for p in parts:
        for dy, row in p.items():
            if dy in out:
                row = "".join(b if b != "." else a for a, b in zip(out[dy], row))
            out[dy] = row
    return out


# --- the full-size heads of the skeleton and the insect (11 pixels wide, 15 rows): rows are offsets from the eye row; the x range is -5..5 -------------------
SKELETON1 = {
    "neutral": {-1: "..DD...DD..", 0: "..DW...WD..", 1: "...D...D...", 2: ".....D.....", 3: "....DDD....", 5: "..EeEeEeE..", 6: "...EeEeE..."},
    "happy":   {0: "..DD...DD..", 1: "..LL...LL..", 3: "....DDD....", 5: "S.EEEEEEE.S", 6: "..SEEEEES.."},
    "cheer":   {-1: "..DD...DD..", 1: "..LL...LL..", 3: "....DDD....", 5: ".EEEEEEEEE.", 6: "..DDDDDDD..", 7: "...DDDDD..."},
    "sad":     {-1: "..DD...DD..", 0: "..DD...DD..", 1: "..DD...DD..", 2: "...D...D...", 3: "....DDD....", 5: "...eeeee...", 6: "..S.....S.."},
    "fear":    {-3: "..DD...DD..", -2: "..DW...WD..", -1: "..DD...DD..", 0: "..DD...DD..", 1: "...D...D...", 3: "....DDD....", 5: ".EEEEEEEEE.", 6: ".DDDDDDDDD.", 7: "..EEEEEEE.."},
    "anger":   {-3: "..SS...SS..", -2: "..DD...DD..", -1: "...DD.DD...", 0: "....D.D....", 3: "....DDD....", 5: ".EEEEEEEEE.", 6: ".MMMMMMMMM."},
    "plea":    {-2: "..DDD.DDD..", -1: "..DWD.DWD..", 0: "..DDD.DDD..", 1: "...D...D...", 3: "....DDD....", 5: ".....DDD...", 6: "....EDDDE.."},
    "doubt":   {-3: "..SSS......", -1: "..DD...DD..", 0: "..DD...D...", 3: "....DDD....", 5: "..EEEEE....", 6: "....EEEEE.."},
    "relief":  {0: "..SS...SS..", 1: "..LL...LL..", 3: "....DDD....", 4: "L.........L", 5: "..EeEeEeE..", 6: "...EeEeE..."},
    "awe":     {-3: "..DDD.DDD..", -2: "..DWD.DWD..", -1: "..DDD.DDD..", 0: "..DDD.DDD..", 1: "...D...D...", 3: "....DDD....", 5: "....DDD....", 6: "....DDD....", 7: "....EEE...."},
    "grief":   {-1: "...D...D...", 0: "..DD...DD..", 1: "..D.....D..", 2: "..T.....T..", 3: "..t.....t..", 4: "..u.....u..", 5: "..eeeeeee..", 6: ".S.......S."},
    "laugh":   {0: "..DD...DD..", 1: "..LL...LL..", 3: "....DDD....", 5: "EEEEEEEEEEE", 6: "DDDDDDDDDDD", 7: ".DDDDDDDDD."},
    "resolve": {-2: ".SSSS.SSSS.", 0: "..DD...DD..", 1: "...D...D...", 3: "....DDD....", 5: ".EEEEEEEEE.", 6: "...MMMMM..."},
    "shame":   {1: "..DD...DD..", 2: "..LL...LL..", 3: "....DDD....", 5: "...EEEEE...", 6: ".S..e.e..S."},
}

_I_EYE = {-2: "..D.....D..", -1: ".DDD...DDD.", 0: ".DWD...DWD.", 1: "..D.....D.."}
_I_SQUINT = {-1: "..D.....D..", 0: ".D.D...D.D."}
_I_WIDE = {-3: "..D.....D..", -2: ".DDD...DDD.", -1: ".DWD...DWD.", 0: ".DDD...DDD.", 1: "..D.....D.."}
_I_SLANT = {-1: ".DDD...DDD.", 0: "..DD...DD..", 1: "...D...D..."}
_I_DROOP = {-1: "...D...D...", 0: "..DDD.DDD..", 1: ".DDD...DDD.", 2: "..D.....D.."}
_I_SHUT = {0: ".DDD...DDD."}
_I_DOWN = {1: ".DDD...DDD.", 2: ".DDD...DDD.", 3: "..D.....D.."}
INSECT1 = {
    "neutral": _merge(_I_EYE, {5: "..M.....M..", 6: "...M...M...", 7: "....M.M...."}),
    "happy":   _merge(_I_SQUINT, {4: "M.........M", 5: ".M.......M.", 6: "..M.....M..", 7: "...MMMMM..."}),
    "cheer":   _merge(_I_SQUINT, {-3: "..L.....L..", 4: "M.........M", 5: "M.........M", 6: ".M.......M.", 7: "..M.MMM.M.."}),
    "sad":     _merge(_I_DROOP, {5: "...M...M...", 6: "..M.....M..", 7: ".M.......M."}),
    "fear":    _merge(_I_WIDE, {4: "M.........M", 5: "M....m....M", 6: "M....m....M", 7: ".M..m....M."}),
    "anger":   _merge(_I_SLANT, {-2: ".DD.....DD.", 5: "..MM...MM..", 6: "..MMM.MMM..", 7: "...MM.MM..."}),
    "plea":    _merge(_I_WIDE, {5: "...M...M...", 6: "...M...M...", 7: "..M.....M.."}),
    "doubt":   _merge({-2: "..D........", -1: ".DDD...DDD.", 0: ".DWD...D...", 1: "..D........"}, {5: "..M........", 6: "...M....MM.", 7: ".....M.M..."}),
    "relief":  _merge(_I_SHUT, {1: "..L.....L..", 5: "...M...M...", 6: "....M.M....", 7: ".....M....."}),
    "awe":     _merge(_I_WIDE, {-4: "..L.....L..", 5: "....mmm....", 6: "....mmm....", 7: "...M...M..."}),
    "grief":   _merge(_I_DROOP, {2: "..T.....T..", 3: "..T.....T..", 4: "..t.....t..", 6: "...M...M...", 7: "..M.....M.."}),
    "laugh":   _merge(_I_SQUINT, {4: "M....m....M", 5: "M...mmm...M", 6: "M...mmm...M", 7: ".M..mmm..M."}),
    "resolve": _merge({-1: ".DDD...DDD.", 0: ".DDD...DDD."}, {-2: ".SSS...SSS.", 5: "..MMMMMMM..", 6: "...MMMMM...", 7: "....MMM...."}),
    "shame":   _merge(_I_DOWN, {5: "....MMM....", 6: "...M...M...", 7: "..........."}),
}

GREY1 = {  # the full-size grey (15 pixels wide): the three that looked alike on it, relief, grief and laugh
    "relief": {-1: "..DDD.....DDD..", 0: ".D...D...D...D.", 2: ".QQ.........QQ.", 5: "...d.......d...", 6: "....ddddddd...."},
    "grief":  {-3: ".....SS.SS.....", -1: "....DD...DD....", 0: "..DD.......DD..", 1: ".D...........D.", 2: ".u...........u.", 3: ".u...........u.", 4: ".u...........u.", 5: ".T...........T.",
               6: "....ddddddd....", 7: "...d.......d..."},
    "laugh":  {-1: "..DDD.....DDD..", 0: ".D...D...D...D.", 4: "..S.........S..", 5: "...EEEEEEEEE...", 6: "...DDDDDDDDD...", 7: "....DDDDDDD....", 8: ".....DDDDD....."},
}

PICTURES = {"grey": GREY, "cyclops": CYCLOPS, "insect": INSECT, "skeleton": SKELETON}
PICTURES_L = {"insect": INSECT1, "skeleton": SKELETON1, "grey": GREY1}  # the full-size heads that are drawn as pictures too
