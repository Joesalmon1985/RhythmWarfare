# Track mode (developer test mode)

A whole recorded track plays start to finish. At any moment one instrument (the focus) is yours and all four pads
(keys D F J K, no names) play its part; the focus moves from instrument to instrument. The screen shows which one
("Playing: Lead"), counts down a change from 8 beats ahead ("Next: Bass in 5"), and says "Nothing to play" between
stretches. A missed cue silences the instrument you are playing (all four pads go dark and say MUTED) until you hit
one of its cues again; the other instruments keep playing. Format (version 2 only; a version 1 pack is refused, re-import it): `docs/TRACK_PACK_FORMAT.md`. No battle, no failing: the track always plays out.

All commands run from the project folder. Set `GODOT` to the Godot 4.5.1 binary and `PACK` to the pack folder.

    GODOT=/home/joe/godot451/Godot_v4.5.1-stable_linux.x86_64
    PACK=/home/joe/rw-audio-work/packs/<id>            # or tests/fixtures/track_fixture (absolute path needed)

Play by hand:

    RW_TRACK=$PACK $GODOT --path . res://src/track/track_play.tscn

Autoplay (`perfect`, `accuracy:0.7`, `none`), and quit when it ends, with the summary on stdout:

    RW_TRACK=$PACK RW_AUTOPLAY=perfect RW_TRACK_QUIT=1 $GODOT --headless --path . res://src/track/track_play.tscn | grep TRACK_SUMMARY

Start part-way in (cues before that second are skipped, not missed), another chart:

    RW_TRACK=$PACK RW_TRACK_START=60 RW_TRACK_CHART=easy $GODOT --path . res://src/track/track_play.tscn

| variable | meaning |
| --- | --- |
| `RW_TRACK` | absolute path of the pack folder (required) |
| `RW_TRACK_CHART` | chart name, default the pack's `default_chart` |
| `RW_AUTOPLAY` | `perfect`, `accuracy:<0..1>` or `none` (no pause on focus loss under autoplay) |
| `RW_TRACK_START` | seconds into the track to begin at |
| `RW_TRACK_QUIT` | `1`: quit when the track ends; a refused pack prints `TRACK_REFUSED [...]` and exits with code 2 |

Esc (or losing focus) pauses; resuming counts down 3 s. At the end the per-voice table is shown and one line
`TRACK_SUMMARY <json>` is printed. `Session` settings apply (calibration, pad size, note speed, high contrast); `RW_CALIBRATION_MS` works as elsewhere.

Tests: `$GODOT --headless --path . -s tests/run_tests.gd -- --filter test_track`. The synthetic fixture pack is made
by `tests/fixtures/track_fixture/make_fixture.py` (output is committed).

Files: `track_pack.gd` (loader and every rule that needs no audio analysis), `track_focus.gd` (which voice is played
when, and the change announcement, as plain logic), `track_game.gd` (rules, per-voice mutes, statistics, event log),
`track_autoplay.gd`, `track_transport.gd`, `track_pad_view.gd`, `track_play.gd` and `.tscn` (the scene).
