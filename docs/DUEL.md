# Wizard Duel (local wifi multiplayer)

Two wizards on two phones (or two windows), one recorded track, the same falling notes at the same time. Every two bars each player's phrase is judged on their own device; **pass it and your wizard
throws a spell at the other one**. Better timing and a longer streak make a bigger spell. First wizard to zero health wins. Built on the continuous-run pieces: the same pads, judge, clock, packs and note lane.

Home > **Wizard Duel (wifi)**.

## How a duel plays

* **Same notes, same time.** Both phones chart the same pack (`dd_part2`, the Bassment's fight set) from the same pattern, so a duel is a fair test of who plays the phrase more precisely. Phrase `j` covers beats
  `8j` to `8j+8` (two bars, 2.76 s). The pattern `DDBDDDBD` (repeating) gives drum phrases (kick on pad 1, snare on pad 4, taps) and bass phrases (held notes on the lit pads). The tier (cue density, 1 to 4)
  rises with the duel: phrase 0, 6, 14, 24.
* **Judging.** At beat `8j+7.5`, after the phrase's last cue window has closed, the phrase is judged on that phone: **passed** at 60% of cues hit (`pass_credit`), else **fizzle** (no spell, streak lost).
* **Spell power** (`content/duel/duel.json` `power`): `quality = clamp((precision - 0.4) / 0.6)`; `precision` is the summed weights of the cues (perfect 1, great 0.8, ok 0.55, missed 0) over the cue count
  less 0.05 per stray press; `power = lerp(5, 11, quality) x (1 + 0.12 x streak, at most 5) x 1.35 for bass x (1 + 0.05 x (tier - 1))`. Power and health are integers in tenths.
* **Landing.** When both players' results for phrase `j` are in, both spells fly (0.95 s) and land together; each takes the other's power off their health (300). Phrases resolve strictly in order.
* **Ending.** Health 0 loses (a double knock-out goes to whoever is less far below zero; exactly equal is a draw). After 40 phrases the higher health wins; equal health is **sudden death**: play on until a
  phrase leaves them unequal (after 16 extra phrases, more total credit wins, else a draw). If the other phone leaves or drops, you win by forfeit.
* **Length and balance** (`godot --headless --path . -s tools/duel/simulate.gd -- 30`, bots stepped without a window): a duel is 47 s between two archmages to about 70 s between two apprentices;
  evenly matched bots win about half each; an archmage beats an adept or an apprentice every time; a flawless pair draws (identical play is a true tie).

## Running it

| Want | How |
| --- | --- |
| Two phones | Both on the same wifi. One taps **Host a duel** (it shows its address and broadcasts); the other taps **Join <name>** in the list (or types the address). The host taps **Start the duel**. |
| Two windows on one PC | Run the game twice. Host in one, join in the other (the list may be empty on one machine: type `127.0.0.1`). |
| Alone | **Practise alone** on the same screen: the Apprentice, the Adept or the Archmage play the other wizard through the same engine and rules. |
| Scripted pair, no windows | `bash tools/duel/two_players.sh adept apprentice` runs two separate processes over loopback and checks both agree on the result. |
| Simulate balance | `godot --headless --path . -s tools/duel/simulate.gd -- 30 [skill_a skill_b]` |
| Tests | `bash tools/test.sh --filter test_duel` (30 tests) |

Environment switches (all optional): `RW_DUEL_SOLO=1`, `RW_DUEL_SKILL`, `RW_DUEL_BOT` (plays this wizard: apprentice, adept, archmage, perfect), `RW_DUEL_VIRTUAL=1` (no audio, wall-clock song time, for headless
runs), `RW_DUEL_QUIT=1`, `RW_DUEL_AUTO=host|join` with `RW_DUEL_ADDR` and `RW_DUEL_NAME` (skip the lobby), `RW_DUEL_SEED`. The end prints one `DUEL_RESULT {...}` line.

## How it is built

| Piece | File |
| --- | --- |
| numbers and pure rules (family, tier, power) | `content/duel/duel.json`, `src/duel/duel_rules.gd` |
| the score book: two results in, spells land, health, winner (no nodes) | `src/duel/duel_match.gd` |
| one wizard's side: charts the phrases, judges them with `PadJudge`, makes the result (no nodes) | `src/duel/duel_engine.gd` |
| the scripted players | `src/duel/duel_bot.gd` |
| the wifi link (autoload `DuelNetwork`) | `src/duel/duel_network.gd` |
| the picture: arena, wizards, health, spells | `src/duel/duel_stage.gd` |
| the duel screen (countdown handshake, results, end panel, rematch) | `src/duel/duel_play.gd/.tscn` |
| the home screen (host, join, practise) | `src/duel/duel_lobby.gd/.tscn` |
| tests and tools | `tests/test_duel.gd`, `tools/duel/simulate.gd`, `tools/duel/two_players.sh` |

### The network

* ENet on UDP port **24710** (`duel.json` `port`), one host and one client; messages are JSON sent with `SceneMultiplayer.send_bytes` (reliable, in order), so no node paths have to match and the link survives scene changes.
* The host also **broadcasts** `{"rw":"duel","v":1,"name","port"}` every second on UDP port **24711** (to the limited broadcast address, each private /24 and loopback); a joining phone lists the games it hears for 4 s.
  The address field always works if broadcast does not (guest wifi and some routers block it).
* Messages: `hello` (name, protocol version), `ready`/`start` (lobby), `loaded` and `go` (the countdown handshake: the host sends `go` when both scenes are loaded and starts its own countdown half a round
  trip later, the round trip measured by `ping`/`pong`), `res` (one phrase result), `rematch`, `bye`. Messages carry the duel's round number so a late message of the last duel is ignored.
* **Each phone judges its own taps** against its own audio clock (so wifi latency never changes how a note is judged) and sends only the finished result per phrase; both phones then run the same `DuelMatch` on the
  same integer numbers in the same order and reach the same result. A start that is a few tens of milliseconds apart only changes when a spell appears.
* A phone that is silent for 7 s, or leaves, forfeits. Android needs `INTERNET`, `ACCESS_NETWORK_STATE` and `ACCESS_WIFI_STATE` (switched on in `export_presets.cfg`).
* Friendly-game trust: the result is whatever each phone reports. There is no anti-cheat.

## Checked

* `tests/test_duel.gd` (30 tests, 372 checks): the data, power rules, the score book (order, knock-out, double knock-out, time limit, sudden death, forfeit, both phones agreeing), the engine (cue placement, a
  perfect player, silence, a missed phrase breaking the streak, strays), the wire format, whole bot duels, the link's message handling and an ENet handshake on loopback, and the scene driven in virtual time.
* `tools/duel/two_players.sh`: two real processes, host and join over loopback, full duel, same result on both.
* Seen: screenshots of the countdown, spells in flight and a mid-duel state on a 1280x720 window.

## Not done / known

* **Nobody has played it on two phones yet**: broadcast discovery and the wifi path on a real router (and the Android firewall/permissions in an exported APK) are unproven. Typing the address is the fallback.
* The wizards are the Bassment wizard sprite (96x96) for both sides, the rival tinted red; there is no spell art beyond glowing orbs, and no sound effects for casts and hits yet.
* Both wizards cast every phrase they pass, so a better player wins every time. A comeback mechanic, spell types by pad, or blocking would be design changes.
* The music is `dd_part2` only; the audio and chart packs are named in `duel.json` `music` and any pack at 174 BPM with the same cue shape works.
