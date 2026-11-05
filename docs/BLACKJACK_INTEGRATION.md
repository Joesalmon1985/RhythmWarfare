# Blackjack minigame: design contract and integration notes

Branch `feature/blackjack-minigame`, based on `main` b51e08d2, built in its own worktree. Never merged, rebased or pushed by the agents.
This file is the contract the build agents work to; the coordinator finalises it (files, commands, conflicts) when the feature is done.

## 0. Decisions made by the owner (do not re-ask)

| # | Decision |
| --- | --- |
| B1 | **The table is a close-up 2D layer over the live 2.5D room.** The camera walks to the chair; a close-up layer (table top, cards, notes, coins, hands, three large people with expressive faces) is drawn inside the low-res viewport over the still-running day room. |
| B2 | **The music decides who sits.** The table is an ordinary hotspot (final window, beats 49 to 64). Touched and the last block passed: you sit on the downbeat. Touched and missed: the dealer waves you off (`on_failure`), the scene continues by its default exit. Once seated every card touch is immediate and independent of the rhythm. |
| B3 | **The day room, with a cap of 5 hotspots there.** A scene may raise its own maximum; every other scene keeps 2 to 4. |
| B4 | **Leaving a live hand forfeits the stake.** Falling off the chair, the run ending or any other interruption that is not the player's choice refunds it, once. |
| B5 | **No text.** No labels, counters, prompts or buttons in the minigame. Only what is printed on cards and currency. While seated the run HUD's title card and captions are silent too. |
| B6 | **Rhythm and cards are independent.** The deck's random stream is consumed only by card draws; nothing about the judge feeds it. Rhythm only decides whether the player stays on the chair: 2 failed blocks in a row wobble, 3 in a row fall. A pass resets the count. |
| B7 | **Energy rules are unchanged while seated.** If the crowd's energy reaches 0 at the table the run ends as it always does; the stake is refunded first. |

## 1. Layers (each knows only the ones above it in this list)

1. **Wallet** `src/run/run_wallet.gd` (`RunWallet`, pure). Owned by `RunProgress` (`Session.run_progress.wallet`). Knows nothing of minigames.
2. **Money breakdown** `src/minigames/money/money_breakdown.gd` (`MoneyBreakdown`, pure static). Pence to physical notes and coins, and the difference between two piles.
3. **Blackjack rules** `src/minigames/blackjack/blackjack_deck.gd`, `blackjack_game.gd` (pure). No wallet, no clock, no nodes.
4. **Minigame lifecycle** `src/minigames/minigame_activity.gd` (base class), `minigame_controller.gd` (pure), plus the run's hooks: `RunEngine.hold`, the `activity` outcome key, `RunPlay` hosting.
5. **Blackjack activity** `src/minigames/blackjack/blackjack_activity.gd` (pure director: binds rules + wallet to a song-time timeline, NPC moods and gestures as data). Config `content/minigames/blackjack.json`.
6. **Presentation** `src/minigames/money/money_view.gd` (reusable drawing of cash), `src/minigames/blackjack/blackjack_view.gd` and its drawing helpers. Reads the activity's state; owns no game state.
7. **Content** `content/run/hotspots/ward.json`, `content/run/run.json`, `content/story/maps/mental_hospital.json`: the day room declares a hotspot whose success outcome is `"activity": "blackjack"`. Nothing in layers 1 to 6 names the ward, the room or the hotspot.

## 2. Wallet (layer 1)

Integer pence. The source of truth for the player's money in a run.

```gdscript
class_name RunWallet extends RefCounted
signal changed()
const START_PENCE := 2000
func balance_pence() -> int                        # spendable cash (excludes held stakes)
func held_pence() -> int                           # the sum of unresolved stakes
func can_afford(amount_pence: int) -> bool
func spend(amount_pence: int) -> bool              # false (and no change) when it cannot be afforded or amount <= 0
func add(amount_pence: int) -> void                # winnings, rewards; amount <= 0 is ignored
func refund(amount_pence: int) -> void             # as add; kept apart so callers say what they mean
func hold(tag: String, amount_pence: int) -> bool  # balance -> escrow under `tag`; false when unaffordable or the tag is already held
func settle(tag: String, payout_pence: int) -> bool # the hold ends and `payout_pence` (0 lost, stake push, 2 x stake win ...) joins the balance; false when no such hold: a hold settles exactly once
func release(tag: String) -> bool                  # the hold returns whole to the balance (an interrupted hand); false when no such hold
func release_all() -> int                          # every hold returned; the pence returned
func reset() -> void                               # START_PENCE, no holds
func to_dict() -> Dictionary                       # {"pence": int, "held": {tag: int}}
func load_dict(d: Variant) -> void                 # tolerant: anything malformed becomes a fresh wallet; held stakes found in a save are released into the balance
```

`RunProgress`: `var wallet: RunWallet`; stored as `data["wallet"]` (added on load when missing, exactly as `seed` is: the save version stays 2, old saves load unchanged);
written on `wallet.changed`; `run_started()` resets it to £20 (a new run; the run scene calls it once per run, never when a minigame is entered or left).

## 3. Money breakdown (layer 2)

`MoneyBreakdown.breakdown(pence) -> Array[int]`: the denominations (pence values, largest first) that make the amount, deterministic:
notes 2000, 1000, 500; coins 200, 100, 50, 20, 10, 5, 2, 1. Fivers are kept loose so a £5 stake is always a visible note: with `f = pence / 500` whole fivers,
`twenties = max(0, (f - 4) / 4)` £20 notes are made and the rest stay as £5 notes (£20 is four fivers, £40 is one twenty and four fivers); the remainder under £5 is greedy coins (£7.50 is a fiver, a £2 coin and a 50p).
`MoneyBreakdown.diff(from_pence, to_pence) -> {"keep": [...], "remove": [...], "add": [...]}` for animating a pile from one amount to another. `sum(breakdown(p)) == p` always.

## 4. Blackjack rules (layer 3)

Pure and seedable. A card is `{"rank": 1..13, "suit": 0..3}` (1 ace, 11 J, 12 Q, 13 K). `BlackjackDeck.new(seed)`: 52 cards, shuffled with its own `RandomNumberGenerator`; `draw()`;
when it runs out it is rebuilt from the cards not on the table and reshuffled from the same stream. `BlackjackGame`: seats `player`, `npc_a`, `npc_b`, `dealer`;
`hand_value(cards) -> {total, soft, bust, natural}`; `start_hand()` (two cards each, in table order, dealer's second face down); `twist()`, `stick()`; NPC seats play by a fixed policy
(no randomness: hit under 12 always, 12 to 16 hit when the dealer's up card is 7 or higher, stand otherwise, soft 17 or less hit); the dealer hits under 17 and stands on every 17;
`result()` per seat: `"blackjack" | "win" | "push" | "lose" | "bust"`; `payout_pence(stake, result)`: blackjack `stake * 5 / 2`, win `stake * 2`, push `stake`, lose and bust `0`
(the stake itself is included, so the wallet's `settle(tag, payout)` is the whole movement). Everything the game does is also appended to an ordered `events` list
(`{"kind": "deal" | "reveal" | "twist" | "stick" | "bust" | "result", "seat", "card" ...}`) that the activity plays out in time.

## 5. Minigame lifecycle (layer 4)

### 5.1 The engine: `RunEngine.hold`

`var hold := false`. While it is true the run stays at the current scene: at the last block's decision `choice` becomes `node_id` before the next phase is charted (so the chart and the
route lock see the same scene and a release after the lock cannot change the destination), `_hotspot_decision` is skipped (nothing commits, no outcome energy, no flags) and
`selected_route()` answers `node_id`. Phases keep their 64 beats; charting, judging, the mix stages and the energy rules are untouched; the transport is never paused.
Releasing the hold mid-phase returns the scene to normal from that moment (the hotspot window opens at beat 49 as usual).

### 5.2 The contract: outcome key `activity`

`HotspotContract.OUTCOME_KEYS` gains `"activity"`: the id of a minigame (a `content/minigames/<id>.json` exists). Only valid in `on_success`, and not together with a `route`.
`RunHotspots` carries it on the outcome (`out["activity"]`); for such an outcome `commit_final` answers `route = <the scene itself>` and `stays = true` instead of continuing by the default exit.
Per-scene cap: a scene node in `run.json` may carry `"max_hotspots": n` (default 4); `RunData` passes it to `validate_scene` as `max_available`, and `tools/run/check_hotspots.py` reads the same field.

### 5.3 `MinigameActivity` (base class, `RefCounted`)

```gdscript
class_name MinigameActivity extends RefCounted
func setup(ctx: Dictionary) -> void        # {"wallet": RunWallet, "seed": int, "beat_s": float, "config": Dictionary}
func begin(t: float) -> void               # the player is seated at song time t
func update(t: float) -> void              # advance to song time t; a pure function of the taps so far and t
func targets() -> Array                    # ids of what may be touched now, e.g. ["bet", "exit"]
func tap(target: String, t: float) -> bool # a touch on a target; false when it is not touchable now (repeated taps are simply refused)
func set_wobble(level: int, t: float) -> void # 0 steady, 1 wobbling (two failed blocks in a row)
func request_leave(t: float) -> void       # the player chose to get up (the activity's own exit target calls this too)
func interrupt(reason: String, t: float) -> void # "fall" | "run_over" | "host": not the player's choice; unresolved stakes are refunded
func is_done() -> bool                     # the leaving or falling animation has finished: the host may resume the adventure
func done_reason() -> String               # "left" | "fall" | "run_over" | "host"
func state() -> Dictionary                 # a snapshot for the view and the tests
func make_view() -> Control                # the presentation node (null in pure tests); the host mounts it in the low-res viewport
```

### 5.4 `MinigameController` (pure, `RefCounted`)

Owns the life of one activity and the generic rules. `register(id, script_path, config_path)` / `load_registry()` (reads `content/minigames/*.json`, each `{"id", "script", ...}`).
`request(id, t_commit, t_seat) -> bool`: creates the activity, sets `engine.hold = true`, state `entering`; at `t_seat` (the next downbeat) `begin`, state `active`.
`on_block_result(passed, t)`: counts failed blocks in a row while active (`wobble_at` 2, `fall_at` 3, from the activity's config, a pass resets): `set_wobble`, then `interrupt("fall")`.
`on_run_over(t)`: `interrupt("run_over")`. `update(t)`: advances the activity; when `is_done()` the hold is released, state `""`, and `finished` is appended to `log`.
`tap(target, t)`, `active() -> bool` (entering, active or leaving), `log: Array` (every lifecycle step with its song time, for tests and walks).

### 5.5 `RunPlay` hosting (the only scene that knows minigames exist)

* `_on_hotspot_commit`: an outcome with `activity` calls `minigames.request(...)`; the outcome's cinematic walks the camera to the chair in the guard as any cinematic does.
* `_advance`: `minigames.update(t)` every frame; while `minigames.active()` the journey (rail steps, glances, strolls, door walks) is not fed, the hotspot view shows nothing and the HUD is silent (`RunHud.silent`).
* `_handle`: `block_result` goes to `minigames.on_block_result`; `run_over` to `on_run_over`.
* Taps: while active a stage tap is hit-tested by the activity's view (`view.hit(pos) -> target id`) and given to `minigames.tap`; a point over a pad is never a target. The pads, `LaneInput` and the judge are untouched.
* The view is mounted with `StoryLowRes.add_overlay(view, "Minigame")` (canvas layer 3, above the hotspots) and freed when the activity is done. When done the rail restarts from where the camera is.
* Scripted play for tests, walks and screenshots: `RW_MINIGAME_TAPS="bet@2,twist@8,stick@12,exit@40"` (target@beats after sitting) and `RW_MINIGAME_SEED=<n>`.

## 6. Blackjack activity and view (layers 5 and 6)

The activity is a deterministic director: taps and song time in, a state snapshot out. Phases: `sitting` (pockets emptied onto the table), `await_bet`, `dealing`, `player_turn`, `others` (NPCs then the dealer),
`settling`, `broke`, `leaving`, `falling`. Money: `wallet.hold("blackjack", 500)` when the bet is touched; `wallet.settle("blackjack", payout)` when the dealer pays or collects;
voluntary exit during a hand `settle("blackjack", 0)`; `interrupt` `release("blackjack")`. The snapshot carries everything the view needs (cards per seat with deal times and face-up flags,
each person's mood, gaze and gesture with start times, the balance and the held stake, the wobble level, the touchable targets) and the view derives all motion from `now - start time`:
no game state lives in the view. The pile on the table is always `MoneyBreakdown.breakdown(wallet.balance_pence())`, the bet spot always `breakdown(wallet.held_pence())`.

Targets: `bet` (the top £5 note of the pile), `deck` (twist), `hand` (the player's cards: stick), `exit` (a door standing ajar at the edge of the picture, the run's own exit language).
Each is at least 72 px on screen and wholly inside the stage area (never over the pads). Nothing is communicated by colour alone: every target also moves (a pulse, a nudge, a pointing hand).

## 7. Tests

`tests/test_wallet.gd`, `test_money_breakdown.gd`, `test_blackjack_rules.gd`, `test_minigame_lifecycle.gd`, `test_blackjack_activity.gd`, `test_blackjack_visual_state.gd`,
`test_blackjack_integration.gd` (the real run scene on the virtual clock). Run one file with
`GODOT=/home/joe/godot451/Godot_v4.5.1-stable_linux.x86_64 bash tools/test.sh --filter <name>`; the whole suite with no arguments.

## 8. The picture: canvas, vocabulary and drawing kit

**Canvas.** The view is drawn with `_draw()` primitives inside the stage's low-res viewport, so it comes out as pixel art with no asset pipeline and nothing shared with the art sheets.
The internal picture is wide and short: about 640 x 230 at the default 360 lines (16:9 window, standard pads), 780 x 231 on an 844 x 390 phone, and half that at 180 lines.
Everything is laid out from the canvas size with the unit `u = size.y / 230.0`; nothing assumes a fixed size. No fonts and no `draw_string`: the only glyphs are `PixelGlyphs` on cards and currency.

**Seats across the picture.** `npc_a` far left, `dealer` centre, `npc_b` far right, all behind the table; the table top fills the lower part; the player's cards bottom centre, the money pile
bottom left, the bet spot between the pile and the dealer, the deck by the dealer's hand; the exit is a door standing ajar at the right edge. The room shows above and between the people.

**Vocabulary (data in the activity's snapshot, drawn by the kit).**
* moods: `neutral`, `happy`, `laugh`, `surprised`, `annoyed`, `sad`, `wince`, `concerned`, `smug`, `thinking`.
* gestures (people): `rest`, `invite`, `point_deck`, `point_hand`, `deal`, `sweep`, `pay`, `shrug`, `clap`, `facepalm`, `tap_table` (an NPC twists), `wave_off` (an NPC sticks; the dealer refusing).
* gestures (the player's own hands): `none`, `pockets` (hands go down to the pockets and come up with the money), `lay_money`, `push_bet`, `reach_deck`, `cover_cards`, `drop_cards`, `empty_pockets`, `gather_money`.
* gaze targets: `player`, `deck`, `own_cards`, `dealer`, `npc_a`, `npc_b`, `pile`, `bet`, `away`.

**Kit files.** `src/minigames/draw/pixel_glyphs.gd` (`PixelGlyphs`: a 3 x 5 cell font for `0123456789AJQK£p`, `draw_text(ci, text, pos, cell, color)`, `text_width(text, cell)`),
`src/minigames/money/money_view.gd` (`MoneyDraw`: notes, coins, pile layout and the animated transition between two amounts; reusable by shops and other minigames),
`src/minigames/blackjack/blackjack_draw.gd` (cards, deck, table) and `src/minigames/blackjack/blackjack_people.gd` (the three people: parametric faces, gaze, gestures; the player's hands).
