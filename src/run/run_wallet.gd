class_name RunWallet
extends RefCounted
## The player's money for a run, in whole pence (no floats anywhere). Stakes placed on a table are held under a tag until they are settled or released,
## so a payout or a refund can only ever happen once per tag. `changed` is emitted after every real change and never when a call is refused.

signal changed()

const START_PENCE := 2000

var _pence := START_PENCE
var _held: Dictionary = {}  # tag -> pence


func balance_pence() -> int:
	return _pence


func held_pence() -> int:
	var total := 0
	for tag in _held:
		total += int(_held[tag])
	return total


func can_afford(amount_pence: int) -> bool:
	return amount_pence > 0 and amount_pence <= _pence


func spend(amount_pence: int) -> bool:
	if not can_afford(amount_pence):
		return false
	_pence -= amount_pence
	changed.emit()
	return true


func add(amount_pence: int) -> void:
	if amount_pence <= 0:
		return
	_pence += amount_pence
	changed.emit()


func refund(amount_pence: int) -> void:
	add(amount_pence)


## Moves the stake from the balance into escrow under `tag`. False when it cannot be afforded or the tag is already held.
func hold(tag: String, amount_pence: int) -> bool:
	if _held.has(tag) or not can_afford(amount_pence):
		return false
	_pence -= amount_pence
	_held[tag] = amount_pence
	changed.emit()
	return true


## Ends the hold and puts `payout_pence` (0 for a lost stake) into the balance. False when the tag is not held, so a hold settles exactly once.
func settle(tag: String, payout_pence: int) -> bool:
	if not _held.has(tag):
		return false
	_held.erase(tag)
	_pence += maxi(0, payout_pence)
	changed.emit()
	return true


## Returns the held stake whole to the balance (an interrupted hand). False when the tag is not held.
func release(tag: String) -> bool:
	if not _held.has(tag):
		return false
	_pence += int(_held[tag])
	_held.erase(tag)
	changed.emit()
	return true


## Returns every held stake to the balance; the pence returned.
func release_all() -> int:
	var returned := held_pence()
	if _held.is_empty():
		return 0
	_held.clear()
	_pence += returned
	changed.emit()
	return returned


func reset() -> void:
	_pence = START_PENCE
	_held.clear()
	changed.emit()


func to_dict() -> Dictionary:
	return {"pence": _pence, "held": _held.duplicate()}


## Tolerant load: anything malformed becomes a fresh wallet. Held stakes found in the data are folded back into the balance (a hand does not survive a restart).
## Does not emit `changed`; the caller decides whether to write.
func load_dict(d: Variant) -> void:
	_held.clear()
	_pence = START_PENCE
	if typeof(d) != TYPE_DICTIONARY:
		return
	var pence: int = _whole(d.get("pence", null))
	if pence < 0:
		return
	var total := pence
	var held: Variant = d.get("held", null)
	if typeof(held) == TYPE_DICTIONARY:
		for tag in held:
			var amount: int = _whole(held[tag])
			if amount > 0:
				total += amount
	_pence = total


## A non-negative whole number of pence from a JSON value (JSON gives floats), or -1 when it is not one.
static func _whole(v: Variant) -> int:
	if typeof(v) == TYPE_INT:
		return v if v >= 0 else -1
	if typeof(v) == TYPE_FLOAT and is_finite(v) and v >= 0.0 and v == floorf(v) and v < 1e12:
		return int(v)
	return -1
