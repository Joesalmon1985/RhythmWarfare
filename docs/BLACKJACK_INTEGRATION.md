# Blackjack minigame: design contract and integration notes

Branch `feature/blackjack-minigame`, based on `main` b51e08d2, built in its own worktree (`../MusicGame-blackjack`). It is not merged, rebased or pushed anywhere.
Sections 0 to 8 are the design the feature was built to; section 9 is the integration guide (files, storage, how to move the table, how to add another minigame, merge risks, commands).

## 0. Decisions made by the owner (do not re-ask)

| # | Decision |
| --- | --- |
| B1 | **The table is a close-up 2D layer over the live 2.5D room.** The camera walks to the chair; a close-up layer (table top, cards, notes, coins, hands, three large people with expressive faces) is drawn inside the low-res viewport over the still-running day room. |
| B2 | **The music decides who sits, gently.** First built as an ordinary final-window hotspot; the owner played it and found it too hard to join, so (2026-11-05): the table can be touched in any block of the visit (`window: "any"`), with a touch target covering the table, its chairs and the three players. At the touch the camera leaves its tour, walks to the table and tips down to it. The block being played is judged at its decision beat (12.5 into the block): a quarter of its credit is enough (`pass_credit` 0.25, against the run's 0.6) and the player sits at the end of that block (beat 16, 32, 48 or 64). Below that the dealer waves you off (3 energy), the camera goes back to its tour and the table can be touched again at once. Once seated every card touch is immediate and independent of the rhythm. |
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

Joining fields (all optional, at the hotspot's top level except `look.*`; the prose is in `docs/CONTINUOUS_RUN.md`, "Joining any block"). `HotspotContract` validates them and `tools/run/check_hotspots.py` makes the same checks:

* `window`: `"final"` (the default; `normalize` fills it in) or `"any"` (`HotspotContract.WINDOWS`). `"any"` needs an `on_success` `activity`. An "any" hotspot is on show in every block of the phase until a final commit has happened, and a touch commits at the decision beat of the block being played (`RunHotspots.on_block`), not at the last block. It never latches `committed`, so it can be touched again. `RunHotspots.window_of` answers `"early"`, `"any"` or `"final"`.
* `pass_credit`: a number from 0 to 1, only with an `on_success` `activity`. The touch succeeds when the judged block's credit reaches it (`RunHotspots._success_of`). Without it, or when the credit is unknown (`-1`), the run's own pass decides. `RunEngine._hotspot_decision` passes the block's credit down.
* `look.selected`: `"ring"` or `"claim"` (`HotspotContract.LOOK_SELECTED`). `"claim"` is the table's look (`HotspotView._draw_claim`).
* `look.ring_m`: a number above 0 and at most 4. The radius of the ring that is drawn, when it is not the touch radius `radius_m`.
* `on_select`: exactly `{"cinematic": <name>}`, a walk the touch itself starts. It resolves like an outcome's cinematic and its steps are validated like any other. `RunPlay._on_select_walk` plays it.

`RunHotspots.on_block` and `commit_final` take the block's `credit` (default `-1`). The table sets `window: "any"`, `pass_credit: 0.25`, `look.selected: "claim"`, `look.ring_m: 1.7`, `radius_m: 2.4`, `min_px: 220` and `on_select: {"cinematic": "ward.cards_approach"}`.

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

| File | What it proves |
| --- | --- |
| `tests/test_wallet.gd` | wallet arithmetic, holds settle or release exactly once, persistence in the run save, an old save without a wallet loads with 20 pounds, a new run resets it |
| `tests/test_money_breakdown.gd`, `tests/test_money_view.gd` | the denominations always sum to the amount; the pile layout draws exactly the breakdown; a transition never invents or loses an item |
| `tests/test_blackjack_rules.gd` | aces, naturals, busts, pushes, the dealer rule, the NPC policy, payouts, deck exhaustion, determinism by seed, refused calls change nothing |
| `tests/test_minigame_lifecycle.gd`, `tests/test_minigame_scene.gd` | the hold across phases, release before and after the route lock, the `activity` outcome, the per-scene cap, wobble and fall counting, the real run scene hosting a fake activity |
| `tests/test_blackjack_activity.gd` | every money path once (win, blackjack, push, loss, bust, forfeit on leaving, refund on a fall or the run ending), rapid taps, broke, wobble changes nothing, the same snapshots at 30, 60, 144 fps and irregular steps |
| `tests/test_blackjack_draw.gd`, `tests/test_blackjack_visual_state.gd` | the vocabulary is all drawn; targets are at least 72 px on a phone, inside the picture, never overlapping; the visible pile and bet equal the wallet; no text anywhere under `src/minigames/` |
| `tests/test_hotspots_any_window.gd` | the "any" window: shown in every block, a touch commits at that block's decision, `pass_credit` at its boundary and the fallback to the run's pass, a wave-off leaves the table touchable, final and early windows unchanged, the same taps give the same log; inside `RunEngine` on the real ward; the contract rules for `window`, `pass_credit`, `look.ring_m`, `on_select` and the claim look; the shipped table has the new fields and no other hotspot does |
| `tests/test_blackjack_integration.gd` | fourteen end-to-end cases on the real run scene (listed in section 9.8) |

Existing files that gained cases: `tests/test_hotspots_view.gd` (`t_commit` and `success` carried through the layout, `hotspot_items()` on the real ward scene, the claim look drawn in every state with reduced motion and high contrast) and `tests/test_minigame_lifecycle.gd` (a mid-phase sit changes no timing, charting or judging of the phase).

One file: `GODOT=/home/joe/godot451/Godot_v4.5.1-stable_linux.x86_64 bash tools/test.sh --filter <part of the file name>`; the whole suite: the same with no arguments (about 17 minutes).
The runner prints `0 failures` even when a script fails to parse, so also check the raw output for `SCRIPT ERROR`: `$GODOT --headless --path . -s tests/run_tests.gd 2>&1 | grep -c "SCRIPT ERROR"` must print 0.

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

## 9. Integration guide

### 9.1 Files added (all new; nothing here exists on `main`)

| Area | Files |
| --- | --- |
| Wallet | `src/run/run_wallet.gd` |
| Generic minigame layer | `src/minigames/minigame_activity.gd`, `src/minigames/minigame_controller.gd`, `src/run/run_minigame_host.gd` |
| Money (reusable) | `src/minigames/money/money_breakdown.gd`, `src/minigames/money/money_view.gd`, `src/minigames/draw/pixel_glyphs.gd` |
| Blackjack | `src/minigames/blackjack/blackjack_deck.gd`, `blackjack_game.gd`, `blackjack_activity.gd`, `blackjack_view.gd`, `blackjack_draw.gd`, `blackjack_people.gd`; `content/minigames/blackjack.json` |
| Art | `assets/minigames/blackjack/world_table.png` (the table in the room, drawn by `tools/minigames/make_world_table.py`); everything in the close-up is drawn in code |
| Tools | `tools/minigames/`: `capture_blackjack.sh` (the nineteen acceptance shots), `blackjack_demo` (the real activity and view on their own clock), `money_gallery`, `people_gallery`, `table_gallery`, `make_world_table.py`, `profile_blackjack.gd` (frame cost of the table view, section 9.11) |
| Tests | the eleven files of section 7, `tests/fixtures/fake_minigame.gd`, `tests/fixtures/fake_minigame_view.gd` |
| Proof | `docs/shots/blackjack/01..19` and four `demo_*` shots; 17 to 19 show joining: `17_touch_registered` (the burst and the camera setting off), `18_waiting_to_sit` (the countdown ring closing), `19_waved_off` (the cold broken ring) |

### 9.2 Existing files modified (every edit; these are where merges can conflict)

| File | Edit |
| --- | --- |
| `src/run/run_engine.gd` (+11 -5) | `var hold`; `selected_route()` answers `node_id` while held; `_decide` skips `_hotspot_decision` while held and sets `choice = node_id` before `_chart_next_phase()` at the last block. With `hold` false nothing differs. `_hotspot_decision(b, passed, t_dec, credit := -1.0)` takes the block's credit and hands it to `hotspots.on_block` and `hotspots.commit_final`. A doc comment on `_decision_beat()`. |
| `src/run/run_hotspots.gd` (+41 -10) | the outcome carries `activity` and `stays`; `commit_final` answers `route = <this scene>`, `stays = true` for an activity outcome. `window_of` answers `"any"` for `window: "any"`; `shown` lists an "any" hotspot while nothing has committed; `on_block(b, passed, credit := -1.0)` commits a selected "any" hotspot (new `_commit_any`: success stays at the scene, failure is `on_failure` with no route, `committed` is not latched); `commit_final(passed, credit := -1.0)` accepts an "any" hotspot as well as a final one; new `_success_of` (`pass_credit`, else the run's pass). |
| `src/run/hotspot_contract.gd` (+44 -5) | `OUTCOME_KEYS` gains `activity`; `_validate_outcome` checks it (a non-empty id, only in `on_success`, never with a route, known when `ctx.activities` is given). New `WINDOWS`; `LOOK_SELECTED` gains `claim`; `normalize` fills `window` with `"final"`; `_validate_one` checks `window`, `pass_credit`, `on_select` and `look.ring_m` (the rules of section 5.2). |
| `src/run/run_data.gd` (+3 -1) | `validate_scene` gets `max_available` from the node's `max_hotspots` and `activities` from the registry (read once per load). |
| `src/run/run_hud.gd` (+7) | `var silent`; `caption()`, `show_title()` and `_outlined()` (every text draw) do nothing while it is true, except the count back in after a pause. The meter and the stage pips stay. |
| `src/run/run_play.gd` (+106 -12; nine sites marked `# minigames`, the joining ones are not) | `minigames` and `_mg` vars; the controller and host made in `_ready`; `minigames.update(t)` and `_mg.step(t)` in `_advance`; the journey is not fed while a minigame lives, nor a `block_result` while a claim walk stands; `block_result` and `run_over` are passed on; `hotspot_items()` empty and `hotspot_select()` refused while seated; `hotspot_tap` hands the touch to the view; `_on_hotspot_commit` requests the activity (seated at the end of the block just judged) and latches `_door_phase`; `_hotspot_cinematic` lets a `stays` outcome move the camera; one key in `summary()`. Joining: `CLAIM_TIP`, `_claim_id`, `_claim_to`; `hotspot_items()` entries carry `t_commit` (`_t_commit_of`) and a committed entry `success`; `hotspot_select` calls `_on_select_walk` (a repeat touch keeps the claim; touching another hotspot gives the rail back); `_claim_frame` tips the camera down; `_back_to_rail(t)` (also used by `RunMinigameHost._resume`); `_update_passage` starts no door walk while a claim stands; `_on_phase_start` clears the claim; `_on_hotspot_commit` ends the claim walk and gives the rail back on a failure; `_hotspot_cinematic(out, t, claim_to)` drops a move the claim walk already made. |
| `src/run/run_progress.gd` (+18 -1) | `var wallet`; loaded from, and written to, `data["wallet"]`; reset in `run_started()`; `_fresh()` includes it. The save version stays 2. A hold or a release of a stake does not write the file (a load folds a held stake back into the balance, so the file already says the same); every change of the total writes at once. |
| `src/story/story_assets.gd`, `src/story/world/story_world.gd`, `src/story/world/story_map.gd`, `src/story/story_crowd.gd` (one line each, three more in `story_map.gd`) | a map texture whose file starts with `res://` is loaded as it stands, so art can live outside a chapter's folder. |
| `tools/run/check_hotspots.py` (+48 -5) | the same rules as the Godot validator: the per-scene `max_hotspots`, the `activity` key (`minigame_ids()` reads `content/minigames/*.json`), `window`, `pass_credit`, `on_select`, `look.ring_m` and `look.selected` `claim`; an `on_select` cinematic counts as used. |
| `tools/run/make_hotspots.py` (+19 -3), `tools/run/make_scenes.py` (+39 -2) | `out(..., activity=)`; `add(..., selected=, window=, pass_credit=, on_select=, ring_m=)`; the `ward.cards` hotspot (`radius=2.4, min_px=220, ring_m=1.7, selected="claim", window="any", pass_credit=0.25`) and its three cinematics (`ward.cards_sit`, `ward.cards_waved_off`, `ward.cards_approach`, all a walk to `day_cards`); the `day_cards` waypoint, the `cards_table` occluder, the `lt_cards_lamp` light and `max_hotspots: 5` for the `ward` node. |
| `content/run/hotspots/ward.json` (+44), `content/run/run.json` (+38 -1), `content/story/maps/mental_hospital.json` (+9 -4), `docs/VISUAL_COVERAGE.md` (+1) | regenerated by those tools; only the additions above: the `ward.cards` entry, `max_hotspots: 5` on the `ward` node and the three cinematics, the map's texture, waypoint, occluder and light, one coverage row. |
| `tests/test_hotspots_engine.gd` (1 line) | the "every outcome's route is a route of its scene" assertion also accepts an outcome that stays at its own scene (`stays` and `route == scene`). |
| `src/run/hotspot_view.gd` (+130 -3) | `CLAIM_BURST_S`, `CLAIM_REFUSE_S`; `layout` entries carry `t_commit` and `success`, and a `claim` thing just below the picture still counts as in view; `_draw` skips the plain "available" look of a hotspot that has just committed; `_draw_entry` draws the ring at `look.ring_m`, caps an edge beacon of a `claim` thing and hands `claim` in the selected and committed states to the new `_draw_claim`; new `_frame_wash`, `_claim_ring`, `_disc`, `_claim_beam`, `_claim_success`, `_claim_refused`. |
| `docs/CONTINUOUS_RUN.md` (+10) | one paragraph, "Joining any block", in the hotspots section: `window: "any"`, `pass_credit`, the claim look, `look.ring_m`, `on_select`. |
| `tests/test_hotspots_view.gd` (+103) | three new cases (section 7). |

`tools/run/make_scenes.py` also rewrites `content/story/music.json` with differences that are already there on `main` (nothing to do with this branch). After running it: `git checkout -- content/story/music.json`.

### 9.3 Where the money is

One place: `RunProgress.wallet` (`Session.run_progress.wallet`, a `RunWallet`), integer pence. It is saved as `data["wallet"] = {"pence": n, "held": {tag: n}}` in `user://story_run.json` on every change.
A save without the key loads with 20 pounds; a held stake found in a save is put back in the balance (a hand does not survive a restart). `run_started()` (once per run, from the run scene's `_ready`) resets it to 20 pounds;
nothing else resets it. A stake is `hold("blackjack", 500)`: out of the balance, into `held`. It ends exactly once: `settle(tag, payout)` or `release(tag)`; a second call on the same tag is refused.
A shop or another minigame uses the same object: `can_afford`, `spend`, `add`, or `hold`/`settle` with its own tag.

### 9.4 The pile on the table is the wallet

The view keeps no number. Each frame it draws `MoneyBreakdown.breakdown(wallet.balance_pence())` as the pile and `breakdown(wallet.held_pence())` on the bet spot, through the activity's snapshot
(`pile` and `bet`: `{pence, from_pence, t0, dur, via}`), where `pence` is read from the wallet at that moment and `from_pence` is only what the animation starts from. `MoneyDraw.transition_items` moves exactly the
notes and coins that differ between the two amounts, so mid-flight the picture is always a mix of the old pile and the new, and at rest it is the wallet. The two exceptions are deliberate and visual only:
while sitting down the pile grows from nothing as the money comes out of the pockets, and while leaving it empties back into them; the wallet does not change in either.
`tests/test_blackjack_visual_state.gd` and case 4 of the integration test assert pile == balance and bet == held at every step.

### 9.5 How a minigame lives inside the run

1. A hotspot's success outcome names it: `"on_success": {"activity": "blackjack", "cinematic": "..."}`. The touch is an intent like any other. With the default window (`final`) the last block decides; with `window: "any"` (the card table) the block being played when it is touched decides, and `pass_credit` sets how much of that block is enough (section 5.2).
2. At the commit (beat 60.5 for a `final` hotspot, the decision beat of the judged block for an `any` one) `RunHotspots` answers a route that is the scene itself; `RunPlay` calls `MinigameController.request`, which sets `RunEngine.hold` and creates the activity; the cinematic walks the camera to the chair (for the card table the camera has already walked over at the touch, `on_select`).
3. On the downbeat the controller calls `begin`. From then the engine re-enters the same scene every 64 beats: phases, cues, the judge, the mix stages, the energy and the audio events are exactly those of any phase. Nothing is paused or restarted; the song clock never knows.
4. While it lives: the journey (rail steps, glances, door walks) is not fed, the hotspot window shows nothing, the HUD draws no text, stage touches go to the activity's view; the pads and `LaneInput` are untouched.
5. Block results reach the controller: two fails in a row `set_wobble(1)`, three `interrupt("fall")`, a pass resets. The run ending is `interrupt("run_over")`.
6. When the activity says `is_done()` the hold is released, the view is freed, the rail restarts and the camera walks back to the scene's home waypoint. A release before beat 48 opens the hotspot window as usual; a release after the route lock stays one more phase (the chart was already made for this scene) and leaves on the next.

### 9.6 Moving the table to another room

Everything is in the two generators; the blackjack code names no room. In `tools/run/make_scenes.py`: move the `day_cards` waypoint (`NEW_WAYPOINTS`), the `cards_table` occluder (`NEW_OCCLUDERS`) and the `lt_cards_lamp` light (`NEW_LIGHTS`)
to the new map and coordinates, and move `n["max_hotspots"] = 5` to the new scene if it already has four hotspots (or drop it). In `tools/run/make_hotspots.py`: move the `ob("ward", "cards", ...)` line under the new scene, with its anchor position
and the waypoint in its three cinematics. Then `python3 tools/run/make_hotspots.py && python3 tools/run/make_scenes.py && git checkout -- content/story/music.json && python3 tools/run/check_hotspots.py`.
Two things found while placing it: an occluder nearer than about 3.3 m to the camera is culled, so the chair waypoint stands that far back; and "things" (billboards) are drawn behind the dancers, which is why the table is an occluder.

### 9.7 Adding another minigame

1. `content/minigames/<id>.json`: `{"id": "<id>", "script": "res://src/minigames/<id>/<id>_activity.gd", "wobble_at": 2, "fall_at": 3, ...}` (the whole file is handed to the activity as `config`).
2. The script extends `MinigameActivity` (section 5.3): `begin`, `update`, `targets`, `tap`, `set_wobble`, `request_leave`, `interrupt`, `is_done`, `state`, `make_view`. Keep it a pure function of the taps and song time.
3. The view is any `Control` with `hit(local_pos) -> String`; the host sets `now_fn`, `beat_s`, `state_fn`, `screen_size`, `reduced`, `high_contrast` if it has them (`src/run/run_minigame_host.gd`).
4. A hotspot anywhere with `"on_success": {"activity": "<id>"}`. Nothing in the engine, the controller or the run scene changes. `MoneyDraw`, `MoneyBreakdown`, `PixelGlyphs` and the wallet are there to be reused.

### 9.8 What the end-to-end test covers (`tests/test_blackjack_integration.gd`)

1 the table is on show in the day room and its touch target is at least 72 px on a phone (the table asks for 220 px, section 5.2), clear of the pads; 2 touched and passed: seated on the downbeat, the camera at the chair, 20 pounds laid out; 3 touched and missed: not seated, energy -3, the default exit;
4 bet, twist, stick, four hands in a row, each settled as the cards say, the pile and the bet equal to the wallet at every frame; 5 three phase boundaries seated: the same scene every 64 beats, cues charted and judged, no commit, no journey, no HUD text;
6 a perfect player and a missing one see the same cards and money; 7 two fails wobble, a pass steadies, three fall, the live stake refunded once, the run goes on; 8 leaving between hands keeps the money, leaving a live hand forfeits the stake, sitting down again starts from the kept balance;
9 broke: only the exit is a target; 10 repeated taps never move money outside the rules; 11 the run ending at the table refunds the stake once; 12 a run that ignores the table is untouched; 13 the same log and wallet at 30 and 60 steps a second;
14 joining at any block (thirteen tests in the file): a touch in block 1 seats the player at the end of that block and the run stays in the room; a weak block between the table's credit and the run's still seats; no pad input waves off, the table stays on show and can be touched again; a touch near the table's edge hits it while the other day room hotspots keep their own centres; after getting up mid-phase the table is on show again; a touch at beat 52 still sits at the next phase start; the touch walks the camera to the table at once and the rail stands still; a repeat touch keeps the claim; a wave-off, or touching another hotspot, gives the camera back to the rail; a failed last block after touching the table still leaves by the default exit; getting up in the phase the player sat down in still walks to the door and moves on; getting up after the route lock of a held phase keeps the run in the day room.

### 9.9 Merging with the graphics and gameplay overhaul

* **Likely conflicts** are the files of 9.2. The engine, contract, hotspot-logic and HUD edits are a few guarded lines each and can be re-applied by hand from this table if the surrounding code has moved; the claim look in `hotspot_view.gd` is one block of new functions. `run_play.gd` has the most sites (search `# minigames`).
* **The acting system** (`docs/THREE_PATHS_AND_FACES_PLAN.md`): the close-up people are self-contained (`BlackjackPeople`, ten moods, twelve gestures, drawn in code) and do not use `StoryCharacter` faces. Nothing needs to change when the fourteen faces arrive.
  If the plan's `acting` block is added to hotspots, `ward.cards` can take one (the dealer beckons) without touching the minigame.
* **The silent HUD** (plan decision D3): `RunHud.silent` does for the seated minutes what `RW_DEV_TEXT` will do for all play. When D3 lands, `silent` can simply go, with its three guards.
* **Hotspot files and `run.json`** are generated: resolve conflicts by taking the overhaul's generators, re-adding the lines of 9.6 and regenerating, not by merging JSON by hand.
* **`content/story/maps/mental_hospital.json`**: one texture, one waypoint, one occluder, one light. If the day room is rebuilt, re-place them (9.6).
* **Sister runs at other tempos** (plan decision D1): every duration in the minigame is in beats times `engine.beat_s`, so the table plays in time at 124, 140 or 145 BPM unchanged.
* **Art**: nothing shared was edited. The close-up is code; the room table is one PNG made by its own tool.

### 9.10 Running it

```
GODOT=/home/joe/godot451/Godot_v4.5.1-stable_linux.x86_64
cd ../MusicGame-blackjack
$GODOT --path .                                              # the game: start the run and reach the ward
RW_RUN_START=ward $GODOT --path . res://src/run/run_play.tscn   # straight into the ward's day room
# a self-playing demonstration (a perfect player touches the table, bets, sticks, leaves):
RW_RUN_START=ward RW_RUN_BOT=perfect RW_RUN_SELECT=ward.cards@52 RW_MINIGAME_SEED=3 RW_MINIGAME_TAPS=bet@5,hand@13,exit@40 $GODOT --path . res://src/run/run_play.tscn
bash tools/minigames/capture_blackjack.sh                    # the nineteen acceptance shots into docs/shots/blackjack (RW_SHOTS=<regex> for some)
```

In play: the table shows its light through the whole visit to the day room; touch it (anywhere on or near the table) and the camera walks over; hit at least a quarter of the notes of the block you are in and you sit at the end of that block.
Touch the top five-pound note to bet, the deck to twist, your own cards to stick, the door at the right edge to get up.

### 9.11 What it costs per frame

Measured on the development laptop (i5-6200U, HD 520, Godot's debug build) with `tools/minigames/profile_blackjack.gd`:

```
$GODOT --path . --disable-vsync --resolution 640x230 -s tools/minigames/profile_blackjack.gd -- 300
```

| | before the efficiency pass | after |
| --- | --- | --- |
| The view's script work per frame, seated | about 13.4 ms | about 1.5 ms |
| Renderer CPU for the table's viewport | about 2.4 ms | about 0.9 ms |
| Draw calls | about 437 | about 180 |
| `BlackjackActivity.state()` per call | 110 to 200 µs | 16 to 24 µs |
| Real run scene, seated, mean frame | 20.3 ms | 14.9 ms (not seated: 14.4 ms) |

How: the view is about twenty layers, each redrawn only when the exact inputs of its drawing change (`_Layer` in `blackjack_view.gd`); limbs and outlined polygons go to the renderer as one triangle list each; the activity's snapshot is rebuilt only after an input, a fired step, a card turning or landing, or a change of the wallet.
The picture is unchanged: 59 reference frames of the demo scene (every phase, low resolution, reduced motion, high contrast) are pixel-identical before and after.

Two rules follow for anyone changing the drawing:

- A layer's spec must list every input its draw function reads. A draw that reads something new without adding it to the spec leaves a stale picture.
- The nested parts of a snapshot are shared between calls and read-only. Code that writes into them gets an error; copy first.

One frame of about 280 ms happens when the player sits (the view being mounted); it was there before the efficiency pass and has not been looked into.

### 9.12 On the combined main (5 November 2026: blackjack + choice clarity + look pass; HANDOVER A16)

* **The table in the room (shots 30 to 33, `docs/shots/blackjack/`).** Before any touch the day room's table is lit by a warm floor pool and a breathing ring, its three players beckon (`30_invitation_from_across_the_room`, `31_invitation_close`); a touch brings a burst, the players' arms up (`32_pleased_at_the_touch`) and the countdown lamps; a wave-off darkens the picture's edge, breaks the ring and has the dealer shake his head (`33_refusal_on_the_people`). The people are `src/run/run_card_table.gd` (sheet `assets/minigames/blackjack/world_table_sheet.*`, made by `tools/minigames/make_world_table.py`); the light is the claim look of `HotspotView`.
* **The look pass's drawing structure.** `HotspotView` now draws in two halves: `_draw_light` (an additive child control: pools, glows, shafts, the picture's edge wash) and `_draw` (the crisp rings with the dark pixel edge), both over the layout `_process` builds each frame; the choice layer (`choice_snapshot`, `_stage_choice`, `_manage_acting`) also runs in `_process`. The claim look is ported as `_light_claim` and `_marks_claim` (dispatched from `_light_entry` and `_draw_marks` for any hotspot with `look.selected: "claim"`, `uses_claim_look`), with `_claim_ring`, `_disc`, `_frame_wash`, `_claim_countdown`, `_claim_pips`, `_marks_refused`. The refusal is dark, so all of it is in the crisp half (light that is added cannot darken). Rings use `look.ring_m` (`_ring_r`); an edge beacon of a claim thing is capped (`_beacon_of`). Timings (`CLAIM_BURST_S` 0.35, `CLAIM_SUCCESS_S` 0.8, `CLAIM_REFUSE_S` 0.8) are the claim's own, not `FLASH_S`.
* **The table is not an option of the choice.** `RunHotspots.staged()` skips a `window: "any"` hotspot. Without that the choice layer treated the table as one more option: its ring was red ("another way"), and touching it turned the day room's exits red and made the table the "current choice". The table keeps the world's warm light.
* **The window camera and the table.** Look-pass turns the head to frame the final window's hotspots from the block-2 decision (`RunPlay._window_face`, `RunJourney.window_face`). `_window_face` only lists `final`-window hotspots, so the table never pulls that frame; the exits and the table are both in the picture in the ward (see the ward shots of HANDOVER A16). A touch of the table releases any held face look over two beats (`StoryPlayer.release_faces`) so the walk to `day_cards` and the tip down are the camera's; when the claim ends in a refusal, or the player gets up, `_back_to_rail` puts the window frame back if the window of the last block is still open.

