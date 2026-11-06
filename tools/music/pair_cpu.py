"""CPU and memory of one transition_pair.gd run, from tools/music/spike/cpu_sampler.py's samples of the process (cpu.csv in the capture folder, started with the pid file).
   python pair_cpu.py <folder> [...]
The samples start when the run writes its pid file, just before its clock starts, so sample time minus the first sample is about song time (within a frame or two). Prints the process's CPU
(percent of one core) and private memory over 12 s of the outgoing scene alone before T and over the blend (T to complete_t), and the most memory seen."""
import csv, json, os, re, sys

for F in sys.argv[1:]:
    j = json.loads(re.sub(r"nan", "NaN", open(os.path.join(F, "pair.json")).read()))
    lk = j["lock"][0]
    T, C = float(lk["boundary"]), float(lk["plan"]["complete_t"])
    rows = [(float(r["unix"]), float(r["cpu_s"]), float(r["private_mb"])) for r in csv.DictReader(open(os.path.join(F, "cpu.csv")))]
    u0 = rows[0][0]

    def span(a, b):
        xs = [r for r in rows if a <= r[0] - u0 <= b]
        if len(xs) < 2:
            return None, None
        return (xs[-1][1] - xs[0][1]) / (xs[-1][0] - xs[0][0]) * 100.0, max(r[2] for r in xs)

    c0, m0 = span(T - 13.0, T - 1.0)
    end = C if C - T > 2.0 else T + 4.0
    c1, m1 = span(T + 0.2, end)
    if c0 is None or c1 is None:
        print("PAIRCPU %s: too few samples" % os.path.basename(F))
        continue
    print("PAIRCPU %s (%s): outgoing alone %.1f%% of a core, private %.0f MB; during the transition (T to %s) %.1f%%, private %.0f MB; most private memory %.0f MB" % (
        os.path.basename(F), lk["plan"]["mode"], c0, m0, "complete_t" if C - T > 2.0 else "T + 4 s", c1, m1, max(r[2] for r in rows)))
