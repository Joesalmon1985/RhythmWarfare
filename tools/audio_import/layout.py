"""How the focus voice's part is laid across the four pads (track pack format v2). One rule for every voice and no
names: lower sounds to the left, higher to the right, so the thumbs follow the shape of the part.

For one focus stretch, given the events picked for the hard chart (normal and easy are subsets, so all three
charts share the layout):

1. Sounds. Pitched parts: one sound per semitone (rounded pitch); more than MAX_SOUNDS distinct pitches are
   merged, rarest first, into their nearest neighbour. Drum hits: clustered (deterministic k-means, at most four)
   on how bright the attack is (log2 spectral centroid) and its band balance (low against mid, high against
   mid), so kick-like, snare-like and hat-like hits fall apart without being named; clusters closer than
   MERGE_DB or rarer than 4% are merged. A sound's
   height is the median pitch, or the median log2 spectral centroid for drum hits.
2. A part on one sound. If one sound carries at least 85% of the events and the part plays at least two events a
   bar, that sound is split by metric position: events on the beat on the lower pad, events off the beat on the
   higher one, or, when that leaves the strongest 60% of the events (what normal and easy keep) nearly all on
   one side, beats 1 and 3 against beats 2 and 4. So a rhythm on one note still moves between two pads, and the
   same position in the bar is always the same pad.
3. Thumbs. Every split of the sounds into left (pads 1, 2) and right (pads 3, 4) is scored: presses closer than
   half a beat on one thumb (the contract forbids them: one of the two would be dropped) weigh 1 per pair, a
   press while a held note of the same thumb is still sounding 0.5, and two sounds that go back and forth
   (a b a within 2.5 beats, as kick and snare do in a two-step, or a trill) 0.25 per alternation, so they land
   on opposite thumbs; against that, the height order is kept (every pair of sounds where the right thumb's is
   lower than the left thumb's costs by how often they are played). Playability weighs most. Both thumbs are
   used when there are two sounds or more.
4. Pads. Within each thumb the order of height is kept: the lower sounds on the left pad of that thumb. Where a
   thumb has several sounds the split point is the one that puts every sound nearest the pad its height rank
   in the whole stretch asks for (the lowest quarter of the presses pad 1, the highest quarter pad 4). A sound
   alone on its thumb takes the outer pad (1 or 4) when it is the lowest or highest sound of the stretch.
The same sound in the same stretch is therefore always the same pad, and a phrase that repeats gets the same pads.
"""
from __future__ import annotations

import numpy as np

MAX_SOUNDS = 10
MERGE_DB = 10.0  # drum sound clusters closer than this (in the feature units of sounds()) are one sound
EPS = 1e-6


def rank_corr(a, b) -> float | None:
    """Spearman rank correlation (average ranks for ties), numpy only."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 3 or np.ptp(a) == 0 or np.ptp(b) == 0:
        return None

    def ranks(x):
        order = np.argsort(x, kind="mergesort")
        r = np.empty(len(x))
        r[order] = np.arange(len(x))
        for v in np.unique(x):
            m = x == v
            r[m] = r[m].mean()
        return r
    return float(np.corrcoef(ranks(a), ranks(b))[0, 1])


def _kmeans(X: np.ndarray, k: int, iters: int = 30) -> np.ndarray:
    """Deterministic k-means: farthest-point initialisation from the first row (callers sort rows by height)."""
    centers = [X[0]]
    for _ in range(1, min(k, len(X))):
        d = np.min([((X - c) ** 2).sum(1) for c in centers], 0)
        if d.max() <= EPS:
            break
        centers.append(X[int(np.argmax(d))])
    C = np.array(centers, float)
    lab = np.zeros(len(X), int)
    for _ in range(iters):
        lab = np.argmin(((X[:, None, :] - C[None]) ** 2).sum(2), 1)
        newC = np.array([X[lab == j].mean(0) if (lab == j).any() else C[j] for j in range(len(C))])
        if np.allclose(newC, C):
            break
        C = newC
    return lab


def _merge_labels(lab: np.ndarray, X: np.ndarray, min_count: int) -> np.ndarray:
    """Merge clusters whose centres are closer than MERGE_DB, then clusters smaller than min_count."""
    lab = lab.copy()
    while True:
        ids = sorted(set(lab.tolist()))
        if len(ids) < 2:
            return lab
        C = {j: X[lab == j].mean(0) for j in ids}
        n = {j: int((lab == j).sum()) for j in ids}
        pairs = [(float(np.linalg.norm(C[a] - C[b])), a, b) for i, a in enumerate(ids) for b in ids[i + 1:]]
        d, a, b = min(pairs)
        if d < MERGE_DB:
            lab[lab == b] = a
            continue
        small = [j for j in ids if n[j] < min_count]
        if not small:
            return lab
        j = min(small, key=lambda j: n[j])
        other = min((x for x in ids if x != j), key=lambda x: float(np.linalg.norm(C[x] - C[j])))
        lab[lab == j] = other


def sounds(evs: list, kind: str) -> tuple[np.ndarray, dict[int, float]]:
    """Sound id per event and the height of each sound (step 1 of the module doc)."""
    n = len(evs)
    if n == 0:
        return np.zeros(0, int), {}
    h = np.array([e.height for e in evs], float)
    if np.isnan(h).all():
        return np.zeros(n, int), {0: 0.0}
    # an event with no measurable height takes the height of the nearest event in time that has one
    ok = np.nonzero(~np.isnan(h))[0]
    for i in np.nonzero(np.isnan(h))[0]:
        h[i] = h[ok[np.argmin(np.abs(ok - i))]]
    if kind == "drums":
        # brightness (log2 centroid, 1 octave = 16 units) with the band balance at half weight (dB / 2): on Go
        # Back this put 95% of the drop's picked hits with the others of their place in the two-step bar (kick,
        # snare, hat), against 86% for the band balance alone and 91% for brightness alone
        X = np.array([[hh * 16.0, *(0.5 * np.array(e.feat if len(e.feat) == 2 else [0.0, 0.0]))]
                      for hh, e in zip(h, evs)], float)
        order = np.argsort(h, kind="mergesort")
        lab_sorted = _kmeans(X[order], 4)
        lab = np.empty(n, int)
        lab[order] = lab_sorted
        lab = _merge_labels(lab, X, max(2, int(np.ceil(0.04 * n))))
    else:
        lab = np.round(h).astype(int)
        while len(set(lab.tolist())) > MAX_SOUNDS:
            ids, cnt = np.unique(lab, return_counts=True)
            j = ids[np.argmin(cnt)]
            rest = ids[ids != j]
            lab[lab == j] = rest[np.argmin(np.abs(rest - j))]
    ids = sorted(set(lab.tolist()), key=lambda j: (float(np.median(h[lab == j])), j))
    remap = {j: i for i, j in enumerate(ids)}
    lab = np.array([remap[j] for j in lab.tolist()], int)
    return lab, {i: float(np.median(h[lab == i])) for i in range(len(ids))}


def _split_one_sound(evs: list, lab: np.ndarray, heights: dict[int, float], B: float) -> tuple[np.ndarray, dict, str | None]:
    n = len(evs)
    if n < 4:
        return lab, heights, None
    ids, cnt = np.unique(lab, return_counts=True)
    top = int(ids[np.argmax(cnt)])
    span_beats = (evs[-1].t - evs[0].t) / B + 1
    if cnt.max() < 0.85 * n or n / max(span_beats / 4, 1) < 2.0:
        return lab, heights, None
    m = lab == top
    pos = np.array([e.pos for e in evs])
    sc = np.array([e.score for e in evs])
    strong = m & (sc >= np.quantile(sc[m], 0.4))  # what the easier charts keep: the split must work there too
    for name, side in (("off the beat", np.abs(pos - np.round(pos)) > 1e-6),
                       ("beats 2 and 4", (np.floor(pos + 1e-6) % 2) == 1)):
        hi = m & side
        if 0.15 <= hi.sum() / m.sum() <= 0.85 and 0.25 <= (strong & side).sum() / max(strong.sum(), 1) <= 0.75:
            new = lab.copy()
            new[lab > top] += 1
            new[hi] = top + 1
            hs = {(j + 1 if j > top else j): v for j, v in heights.items()}
            hs[top + 1] = heights[top] + 0.01
            return new, hs, f"one sound carries {cnt.max()}/{n} presses: split by metric position ({name} on the higher pad)"
    return lab, heights, None


def layout_stretch(evs: list, kind: str, B: float) -> dict:
    """Pads for the events of one stretch (sorted by time). Returns {"pads": [...], plus the reasons}."""
    evs = sorted(evs, key=lambda e: e.t)
    n = len(evs)
    if n == 0:
        return {"pads": [], "sounds": [], "note": "no events"}
    lab, heights = sounds(evs, kind)
    lab, heights, split_note = _split_one_sound(evs, lab, heights, B)
    k = len(heights)
    cnt = np.bincount(lab, minlength=k).astype(float)
    t = np.array([e.t for e in evs])
    W = np.zeros((k, k))
    for i in range(n):
        for j in range(i + 1, n):
            gap = t[j] - t[i]
            hold = kind != "drums" and evs[i].length >= B and t[j] < t[i] + evs[i].length
            if gap >= 0.5 * B - EPS and not hold:
                break
            a, b = lab[i], lab[j]
            if a == b:
                continue
            w = 1.0 if gap < 0.5 * B - EPS else 0.5
            W[a, b] += w
            W[b, a] += w
    # back-and-forth: two sounds that alternate (a b a within 2.5 beats, other sounds in between ignored), like
    # kick and snare in a two-step or a trill; a line that just moves on is not an alternation
    for a in range(k):
        for b in range(a + 1, k):
            idx = np.nonzero((lab == a) | (lab == b))[0]
            for x, y, z in zip(idx, idx[1:], idx[2:]):
                if lab[x] == lab[z] != lab[y] and t[z] - t[x] <= 2.5 * B + EPS:
                    W[a, b] += 0.25
                    W[b, a] += 0.25
    hv = np.array([heights[i] for i in range(k)])
    best = None
    for mask in range(1 << k):
        right = np.array([(mask >> i) & 1 for i in range(k)], bool)
        if k >= 2 and (right.all() or not right.any()):
            continue
        same = right[:, None] == right[None, :]
        conf = float((W * same).sum() / 2)
        inv = float(sum(cnt[i] * cnt[j] for i in range(k) for j in range(k)
                        if right[i] and not right[j] and hv[i] < hv[j] - EPS)) / (n * n)
        cost = 10.0 * conf / n + 3.0 * inv
        key = (round(cost, 9), mask)
        if best is None or key < best[0]:
            best = (key, right, conf, inv)
    if best is None:  # k == 1 and nothing split: one sound, one pad near the middle-left
        right = np.zeros(k, bool)
        conf = inv = 0.0
    else:
        _, right, conf, inv = best
    q = (np.cumsum(cnt) - cnt / 2) / n          # height rank of each sound among the presses, 0..1
    ideal = 1.0 + 3.0 * q
    pad_of = {}
    for thumb, (lo, hi) in ((False, (1, 2)), (True, (3, 4))):
        ss = [i for i in range(k) if right[i] == thumb]
        if not ss:
            continue
        if len(ss) == 1:
            # a sound alone on its thumb takes the outer pad when it is the extreme of the stretch (the lowest on
            # the left thumb, the highest on the right), else the inner one
            others = [hv[i] for i in range(k) if right[i] != thumb]
            outer = (not thumb and all(hv[ss[0]] <= o for o in others)) or (thumb and all(hv[ss[0]] >= o for o in others))
            pad_of[ss[0]] = (lo if not thumb else hi) if outer else (hi if not thumb else lo)
            continue
        cut = min(range(1, len(ss)), key=lambda c: (sum(cnt[i] * abs(ideal[i] - lo) for i in ss[:c])
                                                     + sum(cnt[i] * abs(ideal[i] - hi) for i in ss[c:]), c))
        for i in ss[:cut]:
            pad_of[i] = lo
        for i in ss[cut:]:
            pad_of[i] = hi
    pads = [pad_of[int(c)] for c in lab]
    return {
        "pads": pads,
        "sounds": [{"height": round(float(hv[i]), 2), "presses": int(cnt[i]), "pad": pad_of[i]} for i in range(k)],
        "same_thumb_cost": round(conf, 2), "height_inversions": round(inv, 3),
        "inverted_sound_pairs": int(sum(1 for i in range(k) for j in range(k)
                                         if right[i] and not right[j] and hv[i] < hv[j] - EPS)),
        "height_pad_rank_corr": None if (c := rank_corr([e.height for e in evs if np.isfinite(e.height)],
                                                        [p for e, p in zip(evs, pads) if np.isfinite(e.height)])) is None
        else round(c, 3),
        "split": split_note,
    }
