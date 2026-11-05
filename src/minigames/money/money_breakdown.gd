class_name MoneyBreakdown
extends RefCounted
## Splits an amount of pence into the notes and coins that show it on the table. Fivers stay loose so a 5 pound stake is always a visible note:
## a 20 pound note is only made once there are more than four fivers' worth (20 pounds is four fivers, 40 pounds is a twenty and four fivers).

const DENOMINATIONS: Array[int] = [2000, 1000, 500, 200, 100, 50, 20, 10, 5, 2, 1]
const COINS: Array[int] = [200, 100, 50, 20, 10, 5, 2, 1]


static func is_note(denomination: int) -> bool:
	return denomination >= 500


## The denominations (int pence, largest first) that make `pence`. Empty for zero or less. Deterministic.
static func breakdown(pence: int) -> Array:
	var out: Array = []
	if pence <= 0:
		return out
	var fivers := pence / 500
	var twenties := maxi(0, (fivers - 4) / 4)
	for i in twenties:
		out.append(2000)
	for i in fivers - twenties * 4:
		out.append(500)
	var rest := pence - fivers * 500
	for coin in COINS:
		while rest >= coin:
			out.append(coin)
			rest -= coin
	return out


## What changes when a pile goes from one amount to another: `keep + remove` is breakdown(from), `keep + add` is breakdown(to). Each list is largest first.
static func diff(from_pence: int, to_pence: int) -> Dictionary:
	var from_counts := _counts(breakdown(from_pence))
	var to_counts := _counts(breakdown(to_pence))
	var keep: Array = []
	var remove: Array = []
	var add: Array = []
	for d in DENOMINATIONS:
		var a: int = from_counts.get(d, 0)
		var b: int = to_counts.get(d, 0)
		for i in mini(a, b):
			keep.append(d)
		for i in maxi(0, a - b):
			remove.append(d)
		for i in maxi(0, b - a):
			add.append(d)
	return {"keep": keep, "remove": remove, "add": add}


static func _counts(parts: Array) -> Dictionary:
	var c: Dictionary = {}
	for d in parts:
		c[d] = int(c.get(d, 0)) + 1
	return c
