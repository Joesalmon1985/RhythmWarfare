class_name PixelGlyphs
extends RefCounted
## A tiny 3 x 5 cell bitmap font for playing cards and currency: `0123456789AJQK£p` and nothing else. Each lit cell is a `cell` x `cell` rect; glyphs are one cell apart. Unknown characters are skipped.
## Edges are rounded to whole pixels so the glyphs stay crisp in the low-res viewport even for fractional cells.

const GLYPH_W := 3
const GLYPH_H := 5
const GAP := 1

## Each glyph is five rows of three bits (bit 2 = left column).
const ROWS := {
	"0": [7, 5, 5, 5, 7],
	"1": [2, 6, 2, 2, 7],
	"2": [7, 1, 7, 4, 7],
	"3": [7, 1, 7, 1, 7],
	"4": [5, 5, 7, 1, 1],
	"5": [7, 4, 7, 1, 7],
	"6": [7, 4, 7, 5, 7],
	"7": [7, 1, 1, 2, 2],
	"8": [7, 5, 7, 5, 7],
	"9": [7, 5, 7, 1, 7],
	"A": [2, 5, 7, 5, 5],
	"J": [1, 1, 1, 5, 2],
	"Q": [7, 5, 5, 7, 1],
	"K": [5, 5, 6, 5, 5],
	"£": [3, 4, 6, 4, 7],
	"p": [7, 5, 7, 4, 4],
}


## Draws `text` with its top-left at `pos`.
static func draw_text(ci: CanvasItem, text: String, pos: Vector2, cell: float, color: Color) -> void:
	var x := 0
	for i in text.length():
		var rows: Array = ROWS.get(text[i], [])
		if rows.is_empty():
			continue
		for r in GLYPH_H:
			var bits: int = rows[r]
			var c := 0
			while c < GLYPH_W:
				if bits & (4 >> c) == 0:
					c += 1
					continue
				var start := c
				while c < GLYPH_W and bits & (4 >> c) != 0:
					c += 1
				var x0 := roundf(pos.x + (x + start) * cell)
				var x1 := roundf(pos.x + (x + c) * cell)
				var y0 := roundf(pos.y + r * cell)
				var y1 := roundf(pos.y + (r + 1) * cell)
				ci.draw_rect(Rect2(x0, y0, maxf(1.0, x1 - x0), maxf(1.0, y1 - y0)), color)
		x += GLYPH_W + GAP


## The width of `text` in pixels (known characters only, no trailing gap).
static func text_width(text: String, cell: float) -> float:
	var n := 0
	for i in text.length():
		if ROWS.has(text[i]):
			n += 1
	if n == 0:
		return 0.0
	return (n * GLYPH_W + (n - 1) * GAP) * cell


static func text_height(cell: float) -> float:
	return GLYPH_H * cell
