class_name CloakroomTrials
extends RefCounted
## The cloakroom's trial generator (docs/briefs/BEDSIT_RAVES_BRIEF.md section 5), pure and seeded: the same seed gives the same sequence.
##
## A sequence is `coats + 1` symbols (indices into the theme's four): the first is the unscored reference, every later one is compared with the one right before it.
## `expected[i]` ("same" | "different") is the right answer for scored trial i (symbol i + 1 against symbol i). Balanced: the matches are `round(coats * match_share)`
## (for an odd workload at the default share, the extra one goes to either kind by the seed), so matches and non-matches differ by at most one; no run of the same
## kind is longer than MAX_RUN whenever the counts allow it (they always do at the default share).

const MAX_RUN := 3
const SYMBOLS := 4


## -> {seq: Array[int] (coats + 1 symbol indices), expected: Array[String] (coats), matches: int}.
static func generate(seed_value: int, coats: int, match_share := 0.5, symbols := SYMBOLS) -> Dictionary:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var n := maxi(coats, 0)
	var k := maxi(symbols, 2)
	var m := int(round(float(n) * match_share))
	if absf(match_share - 0.5) < 1e-9 and n % 2 == 1:
		m = n / 2 + (rng.randi() % 2)
	m = clampi(m, 0, n)
	var flags := _flags(rng, n, m)
	var seq: Array = [rng.randi() % k]
	var expected: Array = []
	for i in n:
		var prev: int = seq[i]
		if flags[i]:
			seq.append(prev)
			expected.append("same")
		else:
			var other := rng.randi() % (k - 1)
			seq.append(other if other < prev else other + 1)
			expected.append("different")
	return {"seq": seq, "expected": expected, "matches": m}


## `n` flags, `m` of them true, shuffled; reshuffled until no run is longer than MAX_RUN (bounded), else built greedily.
static func _flags(rng: RandomNumberGenerator, n: int, m: int) -> Array:
	for _try in 200:
		var f: Array = []
		for i in n:
			f.append(i < m)
		for i in range(n - 1, 0, -1):
			var j := rng.randi() % (i + 1)
			var tmp: Variant = f[i]
			f[i] = f[j]
			f[j] = tmp
		if longest_run(f) <= MAX_RUN:
			return f
	var out: Array = []
	var left_true := m
	var left_false := n - m
	var run := 0
	var last := false
	for i in n:
		var want := left_true >= left_false
		if i > 0 and run >= MAX_RUN and want == last and (left_true if not last else left_false) > 0:
			want = not want
		if want and left_true == 0:
			want = false
		elif not want and left_false == 0:
			want = true
		run = run + 1 if (i > 0 and want == last) else 1
		last = want
		out.append(want)
		if want:
			left_true -= 1
		else:
			left_false -= 1
	return out


static func longest_run(flags: Array) -> int:
	var best := 0
	var run := 0
	for i in flags.size():
		run = run + 1 if i > 0 and flags[i] == flags[i - 1] else 1
		best = maxi(best, run)
	return best


## The answer to compare symbol `cur` with `prev`.
static func answer_for(prev: int, cur: int) -> String:
	return "same" if prev == cur else "different"
