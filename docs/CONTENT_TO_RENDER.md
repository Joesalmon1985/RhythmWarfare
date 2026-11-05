# Content to render: every file that replaces a placeholder

Written by `python tools/content/build.py` (or `python tools/content/render_list.py`) from the loop library; it follows the library.
There are **42 clips** and **141 WAV renders** below, of which **42 are your recordings already in place** (marked *in place*; the rest play generated placeholders). You never render whole songs or missions: the game plays one 8-bar loop per clip part and sound, so each clip is rendered once per sound it is offered with, and the build turns every render into its loop (`songs/library/loops/`).

Batches exported from Ableton at 44.1 kHz (and MIDI longer than the clip) go through `tools/content/import_ableton.py`
with a manifest like `content/imports/first_watch.json`: it converts, trims, gain-stages and files them (see
`content/README.md`). Files already at 48 kHz can be dropped straight into the clip folder instead.

## Export settings (every WAV)

- 48,000 Hz, stereo (2 channels), 16-bit PCM WAV. No normalising, no dither needed, leave headroom (peaks below about -3 dBFS:
  a kick, a snare, a bass and a backing play together).
- Tempo 174 BPM, 4/4, project start = bar 1. Render the clip's bars **from its bar 1**, starting exactly on the downbeat with
  no pre-roll, and let the release ring: the file is the clip's musical length plus the release tail, **at most one extra bar**
  (the build rejects longer files and warns when the tail is still sounding at its end). The loop folds the tail onto its
  first bar, so a ringing tail is what makes the loop seam smooth.
- One WAV per part and sound: render the kick part with the kick sound named in the file name, the snare part with the
  snare sound, and so on. The backing is one bus (pad and hats together).
- Ableton: Export Audio/Video, Rendered Track = the part's track (solo, or use the track's own export), Render Start = the clip's
  first bar, Render Length = the clip's bars (+ up to one bar for the tail), Sample Rate 48000, Bit Depth 16, File Type WAV,
  Normalize off, Create Analysis File off, Convert to Mono off.

## How a render becomes a loop

Every loop is exactly 8 bars (529,655 frames at 48 kHz) so the game can switch them on and off at any phase boundary:
a 2-bar groove is placed at bars 1, 3, 5 and 7 and summed (its tail overlaps the next repetition); a 1-bar fill is placed
in bar 8 of an otherwise silent loop; an 8-bar bass line or backing is the loop as it is; a backing longer than 16 bars
(the generated ones are 32 to 48) is cut to its first 16 bars with a 10 ms fade. Whatever rings past the loop's end is
added onto its start. The cues (what the player taps) come from the clip's MIDI: every kick note is pad 1, every snare
note pad 4, bass notes spread over pads 1 to 4 by pitch (taps, at least 1440 ticks apart); ghost notes below the clip's
`cue_min_velocity` are heard but not cued.

## MIDI (only if you change the notes)

The clip MIDI files below are the structure the cues are made from. Every one exists already (cut from your First_Three MIDI,
or generated); you only export a new one when you want different notes. Export the clip as MIDI from Ableton (type 0 or 1,
any PPQ; with no tempo in the file 174 BPM is assumed), save it over the file named in the table, then re-render every WAV of
that part: the build refuses a WAV rendered from the earlier MIDI. The build checks the chart too: the same pad at least
480 ticks apart, the same thumb (pads 1 and 2 left, 3 and 4 right) at least 480 ticks between pads, and every groove
together with every fill (the groove's bars 1 to 7 and the fill's bar 8).

## Where the files go and the one command

Put each WAV in the clip's folder under the name given (`content/library/<clip>/<part>__<sound>.wav`) and run, from the
project folder:

```
python tools/content/build.py
```

It checks every file (rate, channels, bit depth, length, tail, silence, alignment of the attacks to the MIDI, the MIDI's
tempo, meter and grid, the chart and headroom), uses your files instead of the placeholders, rebuilds the loops and the
index in `songs/library/` (only the loops whose source changed are re-encoded), and lists what is still placeholder in
`content/REPORT.md`. Your files are never written; delete one to go back to its placeholder. Commit your WAVs together
with `content/build_state.json`.

The placeholder of every file is already in place as a reference you can drag into Ableton:
`content/library/<clip>/placeholder/<part>__<sound>.wav` (same length and timing your render should have). If that folder is
missing on a fresh checkout, run the build once.

## The files

### `groove_cold`: Cold Groove

groove (kick and snare parts), **8 bars** (11.03 s; with the longest tail 12.41 s), played only by its own recordings, MIDI from your Ableton export (imported through `content/imports/cold_meta.json`). Loop: tiled to fill the 8-bar loop (a 8-bar groove repeats 1 times).

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| kick | `content/library/groove_cold/kick.mid` | `content/library/groove_cold/kick__kick_cold.wav` | Cold Kick | *in place* | `loops/groove_cold__kick__kick_cold.ogg` |
| snare | `content/library/groove_cold/snare.mid` | `content/library/groove_cold/snare__snare_cold.wav` | Cold Snare | *in place* | `loops/groove_cold__snare__snare_cold.ogg` |

### `groove_double_step`: Double Step

groove (kick and snare parts), **8 bars** (11.03 s; with the longest tail 12.41 s), played only by its own recordings, MIDI from your Ableton export (imported through `content/imports/first_watch.json`). Loop: tiled to fill the 8-bar loop (a 8-bar groove repeats 1 times).

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| kick | `content/library/groove_double_step/kick.mid` | `content/library/groove_double_step/kick__kick_double_step.wav` | Double-Step Kick | *in place* | `loops/groove_double_step__kick__kick_double_step.ogg` |
| snare | `content/library/groove_double_step/snare.mid` | `content/library/groove_double_step/snare__snare_backbeat.wav` | Backbeat Snare | *in place* | `loops/groove_double_step__snare__snare_backbeat.ogg` |

### `groove_half_time`: Half-Time

groove (kick and snare parts), **8 bars** (11.03 s; with the longest tail 12.41 s), played only by its own recordings, MIDI from your Ableton export (imported through `content/imports/first_watch.json`). Loop: tiled to fill the 8-bar loop (a 8-bar groove repeats 1 times).

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| kick | `content/library/groove_half_time/kick.mid` | `content/library/groove_half_time/kick__kick_half_time.wav` | Half-Time Kick | *in place* | `loops/groove_half_time__kick__kick_half_time.ogg` |
| snare | `content/library/groove_half_time/snare.mid` | `content/library/groove_half_time/snare__snare_backbeat.wav` | Backbeat Snare | *in place* | `loops/groove_half_time__snare__snare_backbeat.ogg` |

### `groove_meta_a`: Meta Groove A

groove (kick and snare parts), **8 bars** (11.03 s; with the longest tail 12.41 s), played only by its own recordings, MIDI from your Ableton export (imported through `content/imports/cold_meta.json`). Loop: tiled to fill the 8-bar loop (a 8-bar groove repeats 1 times).

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| kick | `content/library/groove_meta_a/kick.mid` | `content/library/groove_meta_a/kick__kick_meta_a.wav` | Meta Kick A | *in place* | `loops/groove_meta_a__kick__kick_meta_a.ogg` |
| snare | `content/library/groove_meta_a/snare.mid` | `content/library/groove_meta_a/snare__snare_meta.wav` | Meta Snare | *in place* | `loops/groove_meta_a__snare__snare_meta.ogg` |

### `groove_meta_b`: Meta Groove B

groove (kick and snare parts), **8 bars** (11.03 s; with the longest tail 12.41 s), played only by its own recordings, MIDI from your Ableton export (imported through `content/imports/cold_meta.json`). Loop: tiled to fill the 8-bar loop (a 8-bar groove repeats 1 times).

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| kick | `content/library/groove_meta_b/kick.mid` | `content/library/groove_meta_b/kick__kick_meta_b.wav` | Meta Kick B | *in place* | `loops/groove_meta_b__kick__kick_meta_b.ogg` |
| snare | `content/library/groove_meta_b/snare.mid` | `content/library/groove_meta_b/snare__snare_meta.wav` | Meta Snare | *in place* | `loops/groove_meta_b__snare__snare_meta.ogg` |

### `groove_push`: Push

groove (kick and snare parts), **2 bars** (2.76 s; with the longest tail 4.14 s), MIDI from your First_Three MIDI, level_02 bars 9-10. Loop: tiled to fill the 8-bar loop (a 2-bar groove repeats 4 times).

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| kick | `content/library/groove_push/kick.mid` | `content/library/groove_push/kick__kick_armour.wav` | Armour Kick | `placeholder/kick__kick_armour.wav` | `loops/groove_push__kick__kick_armour.ogg` |
| kick | `content/library/groove_push/kick.mid` | `content/library/groove_push/kick__kick_heavy.wav` | Heavy Kick | `placeholder/kick__kick_heavy.wav` | `loops/groove_push__kick__kick_heavy.ogg` |
| kick | `content/library/groove_push/kick.mid` | `content/library/groove_push/kick__kick_march.wav` | March Kick | `placeholder/kick__kick_march.wav` | `loops/groove_push__kick__kick_march.ogg` |
| kick | `content/library/groove_push/kick.mid` | `content/library/groove_push/kick__kick_siege.wav` | Siege Kick | `placeholder/kick__kick_siege.wav` | `loops/groove_push__kick__kick_siege.ogg` |
| snare | `content/library/groove_push/snare.mid` | `content/library/groove_push/snare__snare_clap.wav` | Field Clap | `placeholder/snare__snare_clap.wav` | `loops/groove_push__snare__snare_clap.ogg` |
| snare | `content/library/groove_push/snare.mid` | `content/library/groove_push/snare__snare_crack.wav` | Crack Snare | `placeholder/snare__snare_crack.wav` | `loops/groove_push__snare__snare_crack.ogg` |
| snare | `content/library/groove_push/snare.mid` | `content/library/groove_push/snare__snare_guard.wav` | Guard Snare | `placeholder/snare__snare_guard.wav` | `loops/groove_push__snare__snare_guard.ogg` |
| snare | `content/library/groove_push/snare.mid` | `content/library/groove_push/snare__snare_rim.wav` | Rimshot | `placeholder/snare__snare_rim.wav` | `loops/groove_push__snare__snare_rim.ogg` |

### `groove_roller`: Roller

groove (kick and snare parts), **2 bars** (2.76 s; with the longest tail 4.14 s), MIDI from generated placeholder MIDI. Loop: tiled to fill the 8-bar loop (a 2-bar groove repeats 4 times).

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| kick | `content/library/groove_roller/kick.mid` | `content/library/groove_roller/kick__kick_armour.wav` | Armour Kick | `placeholder/kick__kick_armour.wav` | `loops/groove_roller__kick__kick_armour.ogg` |
| kick | `content/library/groove_roller/kick.mid` | `content/library/groove_roller/kick__kick_heavy.wav` | Heavy Kick | `placeholder/kick__kick_heavy.wav` | `loops/groove_roller__kick__kick_heavy.ogg` |
| kick | `content/library/groove_roller/kick.mid` | `content/library/groove_roller/kick__kick_march.wav` | March Kick | `placeholder/kick__kick_march.wav` | `loops/groove_roller__kick__kick_march.ogg` |
| kick | `content/library/groove_roller/kick.mid` | `content/library/groove_roller/kick__kick_siege.wav` | Siege Kick | `placeholder/kick__kick_siege.wav` | `loops/groove_roller__kick__kick_siege.ogg` |
| snare | `content/library/groove_roller/snare.mid` | `content/library/groove_roller/snare__snare_clap.wav` | Field Clap | `placeholder/snare__snare_clap.wav` | `loops/groove_roller__snare__snare_clap.ogg` |
| snare | `content/library/groove_roller/snare.mid` | `content/library/groove_roller/snare__snare_crack.wav` | Crack Snare | `placeholder/snare__snare_crack.wav` | `loops/groove_roller__snare__snare_crack.ogg` |
| snare | `content/library/groove_roller/snare.mid` | `content/library/groove_roller/snare__snare_guard.wav` | Guard Snare | `placeholder/snare__snare_guard.wav` | `loops/groove_roller__snare__snare_guard.ogg` |
| snare | `content/library/groove_roller/snare.mid` | `content/library/groove_roller/snare__snare_rim.wav` | Rimshot | `placeholder/snare__snare_rim.wav` | `loops/groove_roller__snare__snare_rim.ogg` |

### `groove_rolling`: Rolling

groove (kick and snare parts), **8 bars** (11.03 s; with the longest tail 12.41 s), played only by its own recordings, MIDI from your Ableton export (imported through `content/imports/first_watch.json`). Loop: tiled to fill the 8-bar loop (a 8-bar groove repeats 1 times).

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| kick | `content/library/groove_rolling/kick.mid` | `content/library/groove_rolling/kick__kick_rolling.wav` | Rolling Kick | *in place* | `loops/groove_rolling__kick__kick_rolling.ogg` |
| snare | `content/library/groove_rolling/snare.mid` | `content/library/groove_rolling/snare__snare_backbeat.wav` | Backbeat Snare | *in place* | `loops/groove_rolling__snare__snare_backbeat.ogg` |

### `groove_straight`: Straight

groove (kick and snare parts), **2 bars** (2.76 s; with the longest tail 4.14 s), MIDI from your First_Three MIDI, level_02 bars 1-2. Loop: tiled to fill the 8-bar loop (a 2-bar groove repeats 4 times).

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| kick | `content/library/groove_straight/kick.mid` | `content/library/groove_straight/kick__kick_armour.wav` | Armour Kick | `placeholder/kick__kick_armour.wav` | `loops/groove_straight__kick__kick_armour.ogg` |
| kick | `content/library/groove_straight/kick.mid` | `content/library/groove_straight/kick__kick_heavy.wav` | Heavy Kick | `placeholder/kick__kick_heavy.wav` | `loops/groove_straight__kick__kick_heavy.ogg` |
| kick | `content/library/groove_straight/kick.mid` | `content/library/groove_straight/kick__kick_march.wav` | March Kick | `placeholder/kick__kick_march.wav` | `loops/groove_straight__kick__kick_march.ogg` |
| kick | `content/library/groove_straight/kick.mid` | `content/library/groove_straight/kick__kick_siege.wav` | Siege Kick | `placeholder/kick__kick_siege.wav` | `loops/groove_straight__kick__kick_siege.ogg` |
| snare | `content/library/groove_straight/snare.mid` | `content/library/groove_straight/snare__snare_clap.wav` | Field Clap | `placeholder/snare__snare_clap.wav` | `loops/groove_straight__snare__snare_clap.ogg` |
| snare | `content/library/groove_straight/snare.mid` | `content/library/groove_straight/snare__snare_crack.wav` | Crack Snare | `placeholder/snare__snare_crack.wav` | `loops/groove_straight__snare__snare_crack.ogg` |
| snare | `content/library/groove_straight/snare.mid` | `content/library/groove_straight/snare__snare_guard.wav` | Guard Snare | `placeholder/snare__snare_guard.wav` | `loops/groove_straight__snare__snare_guard.ogg` |
| snare | `content/library/groove_straight/snare.mid` | `content/library/groove_straight/snare__snare_rim.wav` | Rimshot | `placeholder/snare__snare_rim.wav` | `loops/groove_straight__snare__snare_rim.ogg` |

### `groove_twostep`: Two-Step

groove (kick and snare parts), **2 bars** (2.76 s; with the longest tail 4.14 s), MIDI from generated placeholder MIDI. Loop: tiled to fill the 8-bar loop (a 2-bar groove repeats 4 times).

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| kick | `content/library/groove_twostep/kick.mid` | `content/library/groove_twostep/kick__kick_armour.wav` | Armour Kick | `placeholder/kick__kick_armour.wav` | `loops/groove_twostep__kick__kick_armour.ogg` |
| kick | `content/library/groove_twostep/kick.mid` | `content/library/groove_twostep/kick__kick_heavy.wav` | Heavy Kick | `placeholder/kick__kick_heavy.wav` | `loops/groove_twostep__kick__kick_heavy.ogg` |
| kick | `content/library/groove_twostep/kick.mid` | `content/library/groove_twostep/kick__kick_march.wav` | March Kick | `placeholder/kick__kick_march.wav` | `loops/groove_twostep__kick__kick_march.ogg` |
| kick | `content/library/groove_twostep/kick.mid` | `content/library/groove_twostep/kick__kick_siege.wav` | Siege Kick | `placeholder/kick__kick_siege.wav` | `loops/groove_twostep__kick__kick_siege.ogg` |
| snare | `content/library/groove_twostep/snare.mid` | `content/library/groove_twostep/snare__snare_clap.wav` | Field Clap | `placeholder/snare__snare_clap.wav` | `loops/groove_twostep__snare__snare_clap.ogg` |
| snare | `content/library/groove_twostep/snare.mid` | `content/library/groove_twostep/snare__snare_crack.wav` | Crack Snare | `placeholder/snare__snare_crack.wav` | `loops/groove_twostep__snare__snare_crack.ogg` |
| snare | `content/library/groove_twostep/snare.mid` | `content/library/groove_twostep/snare__snare_guard.wav` | Guard Snare | `placeholder/snare__snare_guard.wav` | `loops/groove_twostep__snare__snare_guard.ogg` |
| snare | `content/library/groove_twostep/snare.mid` | `content/library/groove_twostep/snare__snare_rim.wav` | Rimshot | `placeholder/snare__snare_rim.wav` | `loops/groove_twostep__snare__snare_rim.ogg` |

### `groove_watch`: Watch

groove (kick and snare parts), **2 bars** (2.76 s; with the longest tail 4.14 s), MIDI from your First_Three MIDI, level_01 bars 1-2. Loop: tiled to fill the 8-bar loop (a 2-bar groove repeats 4 times).

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| kick | `content/library/groove_watch/kick.mid` | `content/library/groove_watch/kick__kick_armour.wav` | Armour Kick | `placeholder/kick__kick_armour.wav` | `loops/groove_watch__kick__kick_armour.ogg` |
| kick | `content/library/groove_watch/kick.mid` | `content/library/groove_watch/kick__kick_heavy.wav` | Heavy Kick | `placeholder/kick__kick_heavy.wav` | `loops/groove_watch__kick__kick_heavy.ogg` |
| kick | `content/library/groove_watch/kick.mid` | `content/library/groove_watch/kick__kick_march.wav` | March Kick | `placeholder/kick__kick_march.wav` | `loops/groove_watch__kick__kick_march.ogg` |
| kick | `content/library/groove_watch/kick.mid` | `content/library/groove_watch/kick__kick_siege.wav` | Siege Kick | `placeholder/kick__kick_siege.wav` | `loops/groove_watch__kick__kick_siege.ogg` |
| snare | `content/library/groove_watch/snare.mid` | `content/library/groove_watch/snare__snare_clap.wav` | Field Clap | `placeholder/snare__snare_clap.wav` | `loops/groove_watch__snare__snare_clap.ogg` |
| snare | `content/library/groove_watch/snare.mid` | `content/library/groove_watch/snare__snare_crack.wav` | Crack Snare | `placeholder/snare__snare_crack.wav` | `loops/groove_watch__snare__snare_crack.ogg` |
| snare | `content/library/groove_watch/snare.mid` | `content/library/groove_watch/snare__snare_guard.wav` | Guard Snare | `placeholder/snare__snare_guard.wav` | `loops/groove_watch__snare__snare_guard.ogg` |
| snare | `content/library/groove_watch/snare.mid` | `content/library/groove_watch/snare__snare_rim.wav` | Rimshot | `placeholder/snare__snare_rim.wav` | `loops/groove_watch__snare__snare_rim.ogg` |

### `fill_break`: Break

fill (kick and snare parts), **1 bars** (1.38 s; with the longest tail 2.76 s), MIDI from generated placeholder MIDI. Loop: placed in bar 8 of an otherwise silent 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| kick | `content/library/fill_break/kick.mid` | `content/library/fill_break/kick__kick_armour.wav` | Armour Kick | `placeholder/kick__kick_armour.wav` | `loops/fill_break__kick__kick_armour.ogg` |
| kick | `content/library/fill_break/kick.mid` | `content/library/fill_break/kick__kick_heavy.wav` | Heavy Kick | `placeholder/kick__kick_heavy.wav` | `loops/fill_break__kick__kick_heavy.ogg` |
| kick | `content/library/fill_break/kick.mid` | `content/library/fill_break/kick__kick_march.wav` | March Kick | `placeholder/kick__kick_march.wav` | `loops/fill_break__kick__kick_march.ogg` |
| kick | `content/library/fill_break/kick.mid` | `content/library/fill_break/kick__kick_siege.wav` | Siege Kick | `placeholder/kick__kick_siege.wav` | `loops/fill_break__kick__kick_siege.ogg` |
| snare | `content/library/fill_break/snare.mid` | `content/library/fill_break/snare__snare_clap.wav` | Field Clap | `placeholder/snare__snare_clap.wav` | `loops/fill_break__snare__snare_clap.ogg` |
| snare | `content/library/fill_break/snare.mid` | `content/library/fill_break/snare__snare_crack.wav` | Crack Snare | `placeholder/snare__snare_crack.wav` | `loops/fill_break__snare__snare_crack.ogg` |
| snare | `content/library/fill_break/snare.mid` | `content/library/fill_break/snare__snare_guard.wav` | Guard Snare | `placeholder/snare__snare_guard.wav` | `loops/fill_break__snare__snare_guard.ogg` |
| snare | `content/library/fill_break/snare.mid` | `content/library/fill_break/snare__snare_rim.wav` | Rimshot | `placeholder/snare__snare_rim.wav` | `loops/fill_break__snare__snare_rim.ogg` |

### `fill_kick_drop`: Kick Drop

fill (kick and snare parts), **1 bars** (1.38 s; with the longest tail 2.76 s), MIDI from generated placeholder MIDI. Loop: placed in bar 8 of an otherwise silent 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| kick | `content/library/fill_kick_drop/kick.mid` | `content/library/fill_kick_drop/kick__kick_armour.wav` | Armour Kick | `placeholder/kick__kick_armour.wav` | `loops/fill_kick_drop__kick__kick_armour.ogg` |
| kick | `content/library/fill_kick_drop/kick.mid` | `content/library/fill_kick_drop/kick__kick_heavy.wav` | Heavy Kick | `placeholder/kick__kick_heavy.wav` | `loops/fill_kick_drop__kick__kick_heavy.ogg` |
| kick | `content/library/fill_kick_drop/kick.mid` | `content/library/fill_kick_drop/kick__kick_march.wav` | March Kick | `placeholder/kick__kick_march.wav` | `loops/fill_kick_drop__kick__kick_march.ogg` |
| kick | `content/library/fill_kick_drop/kick.mid` | `content/library/fill_kick_drop/kick__kick_siege.wav` | Siege Kick | `placeholder/kick__kick_siege.wav` | `loops/fill_kick_drop__kick__kick_siege.ogg` |
| snare | `content/library/fill_kick_drop/snare.mid` | `content/library/fill_kick_drop/snare__snare_clap.wav` | Field Clap | `placeholder/snare__snare_clap.wav` | `loops/fill_kick_drop__snare__snare_clap.ogg` |
| snare | `content/library/fill_kick_drop/snare.mid` | `content/library/fill_kick_drop/snare__snare_crack.wav` | Crack Snare | `placeholder/snare__snare_crack.wav` | `loops/fill_kick_drop__snare__snare_crack.ogg` |
| snare | `content/library/fill_kick_drop/snare.mid` | `content/library/fill_kick_drop/snare__snare_guard.wav` | Guard Snare | `placeholder/snare__snare_guard.wav` | `loops/fill_kick_drop__snare__snare_guard.ogg` |
| snare | `content/library/fill_kick_drop/snare.mid` | `content/library/fill_kick_drop/snare__snare_rim.wav` | Rimshot | `placeholder/snare__snare_rim.wav` | `loops/fill_kick_drop__snare__snare_rim.ogg` |

### `fill_snare_run`: Snare Run

fill (kick and snare parts), **1 bars** (1.38 s; with the longest tail 2.76 s), MIDI from generated placeholder MIDI. Loop: placed in bar 8 of an otherwise silent 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| kick | `content/library/fill_snare_run/kick.mid` | `content/library/fill_snare_run/kick__kick_armour.wav` | Armour Kick | `placeholder/kick__kick_armour.wav` | `loops/fill_snare_run__kick__kick_armour.ogg` |
| kick | `content/library/fill_snare_run/kick.mid` | `content/library/fill_snare_run/kick__kick_heavy.wav` | Heavy Kick | `placeholder/kick__kick_heavy.wav` | `loops/fill_snare_run__kick__kick_heavy.ogg` |
| kick | `content/library/fill_snare_run/kick.mid` | `content/library/fill_snare_run/kick__kick_march.wav` | March Kick | `placeholder/kick__kick_march.wav` | `loops/fill_snare_run__kick__kick_march.ogg` |
| kick | `content/library/fill_snare_run/kick.mid` | `content/library/fill_snare_run/kick__kick_siege.wav` | Siege Kick | `placeholder/kick__kick_siege.wav` | `loops/fill_snare_run__kick__kick_siege.ogg` |
| snare | `content/library/fill_snare_run/snare.mid` | `content/library/fill_snare_run/snare__snare_clap.wav` | Field Clap | `placeholder/snare__snare_clap.wav` | `loops/fill_snare_run__snare__snare_clap.ogg` |
| snare | `content/library/fill_snare_run/snare.mid` | `content/library/fill_snare_run/snare__snare_crack.wav` | Crack Snare | `placeholder/snare__snare_crack.wav` | `loops/fill_snare_run__snare__snare_crack.ogg` |
| snare | `content/library/fill_snare_run/snare.mid` | `content/library/fill_snare_run/snare__snare_guard.wav` | Guard Snare | `placeholder/snare__snare_guard.wav` | `loops/fill_snare_run__snare__snare_guard.ogg` |
| snare | `content/library/fill_snare_run/snare.mid` | `content/library/fill_snare_run/snare__snare_rim.wav` | Rimshot | `placeholder/snare__snare_rim.wav` | `loops/fill_snare_run__snare__snare_rim.ogg` |

### `bass_cold_2`: Cold Bass 2

bass line, **4 bars** (5.52 s; with the longest tail 6.90 s), key B minor, played only by its own recordings, MIDI from your Ableton export (imported through `content/imports/cold_meta.json`). Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| bass | `content/library/bass_cold_2/bass.mid` | `content/library/bass_cold_2/bass__bass_flaring_anger.wav` | Flaring Anger | *in place* | `loops/bass_cold_2__bass__bass_flaring_anger.ogg` |
| bass | `content/library/bass_cold_2/bass.mid` | `content/library/bass_cold_2/bass__bass_hard_harmonic.wav` | Hard Harmonic | *in place* | `loops/bass_cold_2__bass__bass_hard_harmonic.ogg` |
| bass | `content/library/bass_cold_2/bass.mid` | `content/library/bass_cold_2/bass__bass_trap.wav` | Trap Bass | *in place* | `loops/bass_cold_2__bass__bass_trap.ogg` |

### `bass_cold_3`: Cold Bass 3

bass line, **4 bars** (5.52 s; with the longest tail 6.90 s), key A# minor, played only by its own recordings, MIDI from your Ableton export (imported through `content/imports/cold_meta.json`). Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| bass | `content/library/bass_cold_3/bass.mid` | `content/library/bass_cold_3/bass__bass_flaring_anger.wav` | Flaring Anger | *in place* | `loops/bass_cold_3__bass__bass_flaring_anger.ogg` |
| bass | `content/library/bass_cold_3/bass.mid` | `content/library/bass_cold_3/bass__bass_hard_harmonic.wav` | Hard Harmonic | *in place* | `loops/bass_cold_3__bass__bass_hard_harmonic.ogg` |
| bass | `content/library/bass_cold_3/bass.mid` | `content/library/bass_cold_3/bass__bass_trap.wav` | Trap Bass | *in place* | `loops/bass_cold_3__bass__bass_trap.ogg` |

### `bass_cold_4`: Cold Bass 4

bass line, **4 bars** (5.52 s; with the longest tail 6.90 s), key F major, played only by its own recordings, MIDI from your Ableton export (imported through `content/imports/cold_meta.json`). Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| bass | `content/library/bass_cold_4/bass.mid` | `content/library/bass_cold_4/bass__bass_flaring_anger.wav` | Flaring Anger | *in place* | `loops/bass_cold_4__bass__bass_flaring_anger.ogg` |
| bass | `content/library/bass_cold_4/bass.mid` | `content/library/bass_cold_4/bass__bass_hard_harmonic.wav` | Hard Harmonic | *in place* | `loops/bass_cold_4__bass__bass_hard_harmonic.ogg` |
| bass | `content/library/bass_cold_4/bass.mid` | `content/library/bass_cold_4/bass__bass_trap.wav` | Trap Bass | *in place* | `loops/bass_cold_4__bass__bass_trap.ogg` |

### `bass_cold_5`: Cold Bass 5

bass line, **4 bars** (5.52 s; with the longest tail 6.90 s), key E minor, played only by its own recordings, MIDI from your Ableton export (imported through `content/imports/cold_meta.json`). Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| bass | `content/library/bass_cold_5/bass.mid` | `content/library/bass_cold_5/bass__bass_flaring_anger.wav` | Flaring Anger | *in place* | `loops/bass_cold_5__bass__bass_flaring_anger.ogg` |
| bass | `content/library/bass_cold_5/bass.mid` | `content/library/bass_cold_5/bass__bass_hard_harmonic.wav` | Hard Harmonic | *in place* | `loops/bass_cold_5__bass__bass_hard_harmonic.ogg` |
| bass | `content/library/bass_cold_5/bass.mid` | `content/library/bass_cold_5/bass__bass_trap.wav` | Trap Bass | *in place* | `loops/bass_cold_5__bass__bass_trap.ogg` |

### `bass_hold_a`: Long Line

bass line, **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, MIDI from your First_Three MIDI, level_03 bars 1-8. Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| bass | `content/library/bass_hold_a/bass.mid` | `content/library/bass_hold_a/bass__bass_command.wav` | Command Saw | `placeholder/bass__bass_command.wav` | `loops/bass_hold_a__bass__bass_command.ogg` |
| bass | `content/library/bass_hold_a/bass.mid` | `content/library/bass_hold_a/bass__bass_growl.wav` | Growl | `placeholder/bass__bass_growl.wav` | `loops/bass_hold_a__bass__bass_growl.ogg` |
| bass | `content/library/bass_hold_a/bass.mid` | `content/library/bass_hold_a/bass__bass_hollow.wav` | Hollow Sub | `placeholder/bass__bass_hollow.wav` | `loops/bass_hold_a__bass__bass_hollow.ogg` |
| bass | `content/library/bass_hold_a/bass.mid` | `content/library/bass_hold_a/bass__bass_patrol.wav` | Patrol Sub | `placeholder/bass__bass_patrol.wav` | `loops/bass_hold_a__bass__bass_patrol.ogg` |
| bass | `content/library/bass_hold_a/bass.mid` | `content/library/bass_hold_a/bass__bass_reese.wav` | Reese | `placeholder/bass__bass_reese.wav` | `loops/bass_hold_a__bass__bass_reese.ogg` |

### `bass_hold_b`: Answer Line

bass line, **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, MIDI from your First_Three MIDI, level_03 bars 9-16. Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| bass | `content/library/bass_hold_b/bass.mid` | `content/library/bass_hold_b/bass__bass_command.wav` | Command Saw | `placeholder/bass__bass_command.wav` | `loops/bass_hold_b__bass__bass_command.ogg` |
| bass | `content/library/bass_hold_b/bass.mid` | `content/library/bass_hold_b/bass__bass_growl.wav` | Growl | `placeholder/bass__bass_growl.wav` | `loops/bass_hold_b__bass__bass_growl.ogg` |
| bass | `content/library/bass_hold_b/bass.mid` | `content/library/bass_hold_b/bass__bass_hollow.wav` | Hollow Sub | `placeholder/bass__bass_hollow.wav` | `loops/bass_hold_b__bass__bass_hollow.ogg` |
| bass | `content/library/bass_hold_b/bass.mid` | `content/library/bass_hold_b/bass__bass_patrol.wav` | Patrol Sub | `placeholder/bass__bass_patrol.wav` | `loops/bass_hold_b__bass__bass_patrol.ogg` |
| bass | `content/library/bass_hold_b/bass.mid` | `content/library/bass_hold_b/bass__bass_reese.wav` | Reese | `placeholder/bass__bass_reese.wav` | `loops/bass_hold_b__bass__bass_reese.ogg` |

### `bass_hold_end`: Answer Line (ending)

bass line, **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, MIDI from your First_Three MIDI, level_03 bars 41-48. Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| bass | `content/library/bass_hold_end/bass.mid` | `content/library/bass_hold_end/bass__bass_command.wav` | Command Saw | `placeholder/bass__bass_command.wav` | `loops/bass_hold_end__bass__bass_command.ogg` |
| bass | `content/library/bass_hold_end/bass.mid` | `content/library/bass_hold_end/bass__bass_growl.wav` | Growl | `placeholder/bass__bass_growl.wav` | `loops/bass_hold_end__bass__bass_growl.ogg` |
| bass | `content/library/bass_hold_end/bass.mid` | `content/library/bass_hold_end/bass__bass_hollow.wav` | Hollow Sub | `placeholder/bass__bass_hollow.wav` | `loops/bass_hold_end__bass__bass_hollow.ogg` |
| bass | `content/library/bass_hold_end/bass.mid` | `content/library/bass_hold_end/bass__bass_patrol.wav` | Patrol Sub | `placeholder/bass__bass_patrol.wav` | `loops/bass_hold_end__bass__bass_patrol.ogg` |
| bass | `content/library/bass_hold_end/bass.mid` | `content/library/bass_hold_end/bass__bass_reese.wav` | Reese | `placeholder/bass__bass_reese.wav` | `loops/bass_hold_end__bass__bass_reese.ogg` |

### `bass_meta_1`: Meta Bass 1

bass line, **8 bars** (11.03 s; with the longest tail 12.41 s), key F major, played only by its own recordings, MIDI from your Ableton export (imported through `content/imports/cold_meta.json`). Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| bass | `content/library/bass_meta_1/bass.mid` | `content/library/bass_meta_1/bass__bass_flaring_anger.wav` | Flaring Anger | *in place* | `loops/bass_meta_1__bass__bass_flaring_anger.ogg` |
| bass | `content/library/bass_meta_1/bass.mid` | `content/library/bass_meta_1/bass__bass_hard_harmonic.wav` | Hard Harmonic | *in place* | `loops/bass_meta_1__bass__bass_hard_harmonic.ogg` |
| bass | `content/library/bass_meta_1/bass.mid` | `content/library/bass_meta_1/bass__bass_trap.wav` | Trap Bass | *in place* | `loops/bass_meta_1__bass__bass_trap.ogg` |

### `bass_octaves`: Octaves

bass line, **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, MIDI from generated placeholder MIDI. Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| bass | `content/library/bass_octaves/bass.mid` | `content/library/bass_octaves/bass__bass_command.wav` | Command Saw | `placeholder/bass__bass_command.wav` | `loops/bass_octaves__bass__bass_command.ogg` |
| bass | `content/library/bass_octaves/bass.mid` | `content/library/bass_octaves/bass__bass_growl.wav` | Growl | `placeholder/bass__bass_growl.wav` | `loops/bass_octaves__bass__bass_growl.ogg` |
| bass | `content/library/bass_octaves/bass.mid` | `content/library/bass_octaves/bass__bass_hollow.wav` | Hollow Sub | `placeholder/bass__bass_hollow.wav` | `loops/bass_octaves__bass__bass_hollow.ogg` |
| bass | `content/library/bass_octaves/bass.mid` | `content/library/bass_octaves/bass__bass_patrol.wav` | Patrol Sub | `placeholder/bass__bass_patrol.wav` | `loops/bass_octaves__bass__bass_patrol.ogg` |
| bass | `content/library/bass_octaves/bass.mid` | `content/library/bass_octaves/bass__bass_reese.wav` | Reese | `placeholder/bass__bass_reese.wav` | `loops/bass_octaves__bass__bass_reese.ogg` |

### `bass_reese_line`: Reese Line

bass line, **8 bars** (11.03 s; with the longest tail 12.41 s), key F minor, played only by its own recordings, MIDI from your Ableton export (imported through `content/imports/first_watch.json`). Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| bass | `content/library/bass_reese_line/bass.mid` | `content/library/bass_reese_line/bass__bass_reese_dark.wav` | Dark Reese | *in place* | `loops/bass_reese_line__bass__bass_reese_dark.ogg` |
| bass | `content/library/bass_reese_line/bass.mid` | `content/library/bass_reese_line/bass__bass_reese_deep.wav` | Deep Reese | *in place* | `loops/bass_reese_line__bass__bass_reese_deep.ogg` |
| bass | `content/library/bass_reese_line/bass.mid` | `content/library/bass_reese_line/bass__bass_reese_round.wav` | Round Reese | *in place* | `loops/bass_reese_line__bass__bass_reese_round.ogg` |
| bass | `content/library/bass_reese_line/bass.mid` | `content/library/bass_reese_line/bass__bass_reese_soft.wav` | Soft Reese | *in place* | `loops/bass_reese_line__bass__bass_reese_soft.ogg` |

### `bass_steps`: Steps

bass line, **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, MIDI from generated placeholder MIDI. Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| bass | `content/library/bass_steps/bass.mid` | `content/library/bass_steps/bass__bass_command.wav` | Command Saw | `placeholder/bass__bass_command.wav` | `loops/bass_steps__bass__bass_command.ogg` |
| bass | `content/library/bass_steps/bass.mid` | `content/library/bass_steps/bass__bass_growl.wav` | Growl | `placeholder/bass__bass_growl.wav` | `loops/bass_steps__bass__bass_growl.ogg` |
| bass | `content/library/bass_steps/bass.mid` | `content/library/bass_steps/bass__bass_hollow.wav` | Hollow Sub | `placeholder/bass__bass_hollow.wav` | `loops/bass_steps__bass__bass_hollow.ogg` |
| bass | `content/library/bass_steps/bass.mid` | `content/library/bass_steps/bass__bass_patrol.wav` | Patrol Sub | `placeholder/bass__bass_patrol.wav` | `loops/bass_steps__bass__bass_patrol.ogg` |
| bass | `content/library/bass_steps/bass.mid` | `content/library/bass_steps/bass__bass_reese.wav` | Reese | `placeholder/bass__bass_reese.wav` | `loops/bass_steps__bass__bass_reese.ogg` |

### `bass_sub_line`: Sub Line

bass line, **8 bars** (11.03 s; with the longest tail 12.41 s), key F minor, played only by its own recordings, MIDI from your Ableton export (imported through `content/imports/first_watch.json`). Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| bass | `content/library/bass_sub_line/bass.mid` | `content/library/bass_sub_line/bass__bass_sub_bright.wav` | Bright Sub | *in place* | `loops/bass_sub_line__bass__bass_sub_bright.ogg` |
| bass | `content/library/bass_sub_line/bass.mid` | `content/library/bass_sub_line/bass__bass_sub_deep.wav` | Deep Sub | *in place* | `loops/bass_sub_line__bass__bass_sub_deep.ogg` |
| bass | `content/library/bass_sub_line/bass.mid` | `content/library/bass_sub_line/bass__bass_sub_pure.wav` | Pure Sub | *in place* | `loops/bass_sub_line__bass__bass_sub_pure.ogg` |
| bass | `content/library/bass_sub_line/bass.mid` | `content/library/bass_sub_line/bass__bass_sub_warm.wav` | Warm Sub | *in place* | `loops/bass_sub_line__bass__bass_sub_warm.ogg` |
| bass | `content/library/bass_sub_line/bass.mid` | `content/library/bass_sub_line/bass__bass_sub_wide.wav` | Wide Sub | *in place* | `loops/bass_sub_line__bass__bass_sub_wide.ogg` |

### `acc_backbeat`: Backbeat accompaniment

backing (pad and hats on one bus), **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, MIDI from generated placeholder MIDI. Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| other | `content/library/acc_backbeat/other.mid` | `content/library/acc_backbeat/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` | `loops/acc_backbeat__other__ensemble.ogg` |

### `acc_cold_loop`: Cold Percussion Loop

backing (pad and hats on one bus), **16 bars** (22.07 s; with the longest tail 23.45 s), played only by its own recordings, MIDI from no MIDI (audio-only backing, never cued). Loop: used as the 16-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| other | (none: audio only) | `content/library/acc_cold_loop/other__backing_cold_loop.wav` | Cold Percussion Loop | *in place* | `loops/acc_cold_loop__other__backing_cold_loop.ogg` |

### `acc_counterpoint`: Counterpoint accompaniment

backing (pad and hats on one bus), **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, MIDI from generated placeholder MIDI. Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| other | `content/library/acc_counterpoint/other.mid` | `content/library/acc_counterpoint/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` | `loops/acc_counterpoint__other__ensemble.ogg` |

### `acc_crossfire`: Crossfire accompaniment

backing (pad and hats on one bus), **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, MIDI from generated placeholder MIDI. Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| other | `content/library/acc_crossfire/other.mid` | `content/library/acc_crossfire/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` | `loops/acc_crossfire__other__ensemble.ogg` |

### `acc_crossroads`: Crossroads accompaniment

backing (pad and hats on one bus), **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, MIDI from generated placeholder MIDI. Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| other | `content/library/acc_crossroads/other.mid` | `content/library/acc_crossroads/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` | `loops/acc_crossroads__other__ensemble.ogg` |

### `acc_first_watch`: First Watch accompaniment

backing (pad and hats on one bus), **32 bars** (44.14 s; with the longest tail 45.52 s), key C# minor, MIDI from your First_Three MIDI, level_01 bars 1-32. Loop: used as the 16-bar loop (the clip's first 16 of 32 bars).

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| other | `content/library/acc_first_watch/other.mid` | `content/library/acc_first_watch/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` | `loops/acc_first_watch__other__ensemble.ogg` |

### `acc_fortress`: Fortress accompaniment

backing (pad and hats on one bus), **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, MIDI from generated placeholder MIDI. Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| other | `content/library/acc_fortress/other.mid` | `content/library/acc_fortress/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` | `loops/acc_fortress__other__ensemble.ogg` |

### `acc_hats_busy`: Busy Hats

backing (pad and hats on one bus), **8 bars** (11.03 s; with the longest tail 12.41 s), key F minor, played only by its own recordings, MIDI from no MIDI (audio-only backing, never cued). Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| other | (none: audio only) | `content/library/acc_hats_busy/other__hats_busy.wav` | Busy Hats | *in place* | `loops/acc_hats_busy__other__hats_busy.ogg` |

### `acc_hats_driving`: Driving Hats

backing (pad and hats on one bus), **8 bars** (11.03 s; with the longest tail 12.41 s), key F minor, played only by its own recordings, MIDI from no MIDI (audio-only backing, never cued). Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| other | (none: audio only) | `content/library/acc_hats_driving/other__hats_driving.wav` | Driving Hats | *in place* | `loops/acc_hats_driving__other__hats_driving.ogg` |

### `acc_hats_offbeat`: Offbeat Hats

backing (pad and hats on one bus), **8 bars** (11.03 s; with the longest tail 12.41 s), key F minor, played only by its own recordings, MIDI from no MIDI (audio-only backing, never cued). Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| other | (none: audio only) | `content/library/acc_hats_offbeat/other__hats_offbeat.wav` | Offbeat Hats | *in place* | `loops/acc_hats_offbeat__other__hats_offbeat.ogg` |

### `acc_hold_the_line`: Hold the Line accompaniment

backing (pad and hats on one bus), **48 bars** (66.21 s; with the longest tail 67.59 s), key C# minor, MIDI from your First_Three MIDI, level_03 bars 1-48. Loop: used as the 16-bar loop (the clip's first 16 of 48 bars).

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| other | `content/library/acc_hold_the_line/other.mid` | `content/library/acc_hold_the_line/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` | `loops/acc_hold_the_line__other__ensemble.ogg` |

### `acc_iron`: Iron Rhythm accompaniment

backing (pad and hats on one bus), **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, MIDI from generated placeholder MIDI. Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| other | `content/library/acc_iron/other.mid` | `content/library/acc_iron/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` | `loops/acc_iron__other__ensemble.ogg` |

### `acc_last_light`: Last Light accompaniment

backing (pad and hats on one bus), **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, MIDI from generated placeholder MIDI. Loop: used as the 8-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| other | `content/library/acc_last_light/other.mid` | `content/library/acc_last_light/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` | `loops/acc_last_light__other__ensemble.ogg` |

### `acc_meta_a`: Meta Percussion A

backing (pad and hats on one bus), **16 bars** (22.07 s; with the longest tail 23.45 s), played only by its own recordings, MIDI from no MIDI (audio-only backing, never cued). Loop: used as the 16-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| other | (none: audio only) | `content/library/acc_meta_a/other__backing_meta_a.wav` | Meta Percussion A | *in place* | `loops/acc_meta_a__other__backing_meta_a.ogg` |

### `acc_meta_b`: Meta Percussion B

backing (pad and hats on one bus), **16 bars** (22.07 s; with the longest tail 23.45 s), played only by its own recordings, MIDI from no MIDI (audio-only backing, never cued). Loop: used as the 16-bar loop.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| other | (none: audio only) | `content/library/acc_meta_b/other__backing_meta_b.wav` | Meta Percussion B | *in place* | `loops/acc_meta_b__other__backing_meta_b.ogg` |

### `acc_second_pulse`: Second Pulse accompaniment

backing (pad and hats on one bus), **40 bars** (55.17 s; with the longest tail 56.55 s), key C# minor, MIDI from your First_Three MIDI, level_02 bars 1-40. Loop: used as the 16-bar loop (the clip's first 16 of 40 bars).

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder | Loop |
| --- | --- | --- | --- | --- | --- |
| other | `content/library/acc_second_pulse/other.mid` | `content/library/acc_second_pulse/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` | `loops/acc_second_pulse__other__ensemble.ogg` |

## Sounds

| Sound id | Name | Family |
| --- | --- | --- |
| `kick_march` | March Kick | kick |
| `kick_armour` | Armour Kick | kick |
| `kick_siege` | Siege Kick | kick |
| `kick_heavy` | Heavy Kick | kick |
| `snare_guard` | Guard Snare | snare |
| `snare_crack` | Crack Snare | snare |
| `snare_clap` | Field Clap | snare |
| `snare_rim` | Rimshot | snare |
| `bass_patrol` | Patrol Sub | bass |
| `bass_reese` | Reese | bass |
| `bass_growl` | Growl | bass |
| `bass_command` | Command Saw | bass |
| `bass_hollow` | Hollow Sub | bass |
| `ensemble` | Ensemble | other |
| `kick_half_time` | Half-Time Kick | kick |
| `kick_double_step` | Double-Step Kick | kick |
| `kick_rolling` | Rolling Kick | kick |
| `snare_backbeat` | Backbeat Snare | snare |
| `bass_sub_bright` | Bright Sub | bass |
| `bass_sub_deep` | Deep Sub | bass |
| `bass_sub_pure` | Pure Sub | bass |
| `bass_sub_wide` | Wide Sub | bass |
| `bass_sub_warm` | Warm Sub | bass |
| `bass_reese_dark` | Dark Reese | bass |
| `bass_reese_deep` | Deep Reese | bass |
| `bass_reese_soft` | Soft Reese | bass |
| `bass_reese_round` | Round Reese | bass |
| `hats_driving` | Driving Hats | other |
| `hats_busy` | Busy Hats | other |
| `hats_offbeat` | Offbeat Hats | other |
| `kick_cold` | Cold Kick | kick |
| `snare_cold` | Cold Snare | snare |
| `kick_meta_a` | Meta Kick A | kick |
| `kick_meta_b` | Meta Kick B | kick |
| `snare_meta` | Meta Snare | snare |
| `bass_hard_harmonic` | Hard Harmonic | bass |
| `bass_flaring_anger` | Flaring Anger | bass |
| `bass_trap` | Trap Bass | bass |
| `backing_cold_loop` | Cold Percussion Loop | other |
| `backing_meta_a` | Meta Percussion A | other |
| `backing_meta_b` | Meta Percussion B | other |

Adding a sound or a clip: add the sound to `content/sounds.json` and say what it produces in
`data/campaign/instruments.json` (or copy `content/fixtures/example_groove/` to `content/library/<new_id>/` and edit
its `clip.json`) and run the build: it adds the loops (placeholders until you drop your own WAVs in) to the index the
player's loadout picks from.
