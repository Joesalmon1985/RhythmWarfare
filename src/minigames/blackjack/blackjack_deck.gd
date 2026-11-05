class_name BlackjackDeck
extends RefCounted
## A standard 52-card deck with its own seeded random stream.
## The stream is consumed only by shuffles, so the card order is a pure function of the seed and the
## number of cards drawn (plus which cards were on the table at each rebuild). Cards are
## {"rank": 1..13, "suit": 0..3}; rank 1 is the ace, 11 jack, 12 queen, 13 king.

var _rng := RandomNumberGenerator.new()
var _pile: Array = []
var _drawn := 0


func _init(seed: int = 0) -> void:
	_rng.seed = seed
	_pile = _shuffled(_full_cards([]))


## A deck that deals exactly `cards` in order, then falls back to a shuffle seeded with `fallback_seed`.
## For tests that need an exact hand.
static func stacked(cards: Array, fallback_seed: int = 0) -> BlackjackDeck:
	var deck := BlackjackDeck.new(fallback_seed)
	deck._pile = []
	for c in cards:
		deck._pile.append({"rank": int(c["rank"]), "suit": int(c.get("suit", 0))})
	return deck


## Cards left before a rebuild is needed.
func remaining() -> int:
	return _pile.size()


## Total cards dealt out since the deck was made.
func drawn_count() -> int:
	return _drawn


## Takes the next card. `in_play` lists the cards currently on the table (each with "rank" and "suit");
## when the deck is empty it is rebuilt from the 52 cards minus those, and reshuffled from the same
## random stream. A draw never fails and never repeats a card in `in_play`.
func draw(in_play: Array = []) -> Dictionary:
	if _pile.is_empty():
		_pile = _shuffled(_full_cards(in_play))
	_drawn += 1
	return _pile.pop_front()


static func _full_cards(excluded: Array) -> Array:
	var out: Array = []
	for suit in range(4):
		for rank in range(1, 14):
			var skip := false
			for e in excluded:
				if int(e["rank"]) == rank and int(e["suit"]) == suit:
					skip = true
					break
			if not skip:
				out.append({"rank": rank, "suit": suit})
	return out


## Fisher-Yates using this deck's own stream.
func _shuffled(cards: Array) -> Array:
	var a := cards.duplicate()
	for i in range(a.size() - 1, 0, -1):
		var j := _rng.randi_range(0, i)
		var t: Variant = a[i]
		a[i] = a[j]
		a[j] = t
	return a
