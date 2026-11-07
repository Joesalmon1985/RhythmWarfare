# Bar activity: hooks wanted in engine files (not made; the bar works without them)

The bar (`src/minigames/bar/`) touches no engine file. These are the small changes that would improve it, for the lead.

## H-bar-1: pictograms on the controls (src/run/run_activity_input.gd, src/run/run_minigame_host.gd `_show_controls`)

`BarActivity.controls()` returns `{id, label: "", icon: <ingredient id>, shape, color: "#rrggbb"}`. `RunActivityInput._draw` draws only `labels[i]` as text, so the four strip buttons
stand blank (the brief wants silhouette plus colour, no words). Wanted: `_show_controls` copies a `shape` and `color` per control into the layer (`controls_layer.shapes`,
`controls_layer.colors`), and `_draw` draws `BarDraw.texture(shape, Color(color))` centred in the button, about 70 % of the button's short side, nearest filtered; when `label == ""` it draws no text.
The bottles standing on the bar counter in the stage are touchable meanwhile (`BarView.hit`), so the game is playable without it. `tools/minigames/bar_demo.gd` draws the pictograms itself to show the intended look.

## H-bar-2: remembered order across leaving and returning (src/run/run_progress.gd, optional)

The order is remembered in `BarActivity._memory` (a static dictionary, keyed by theme and the run's wallet instance), so it lasts while the app runs and is forgotten on restart. To keep it in the
save: `RunProgress` would store `raves.<theme>.bar = {served, recipe}` and hand it to the activity in the request's config (`config.bar_resume`); `BarActivity` would read it in `setup` and write it
back through `result()` (`result.resume`). The activity side is small once the host passes it.

## H-bar-3: nothing else

Mode, controls ownership, suspension and resume on the boundary all work through the existing contract (tests/test_bar.gd runs them in the real run scene).
