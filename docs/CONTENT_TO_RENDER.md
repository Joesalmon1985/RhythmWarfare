# Content to render: every file that replaces a placeholder

Written by `python tools/content/render_list.py` from the loop library and the ten missions; rerun it after changing either.
Everything in the game is placeholder sound today. There are **23 clips** and **84 WAV renders** below. You never render whole songs: each clip is rendered once per sound it is offered with, and the build assembles the missions from those pieces.

## Export settings (every WAV)

- 48,000 Hz, stereo (2 channels), 16-bit PCM WAV. No normalising, no dither needed, leave headroom (peaks below about -3 dBFS:
  up to five stems play together).
- Tempo 174 BPM, 4/4, project start = bar 1. Render the clip's bars **from its bar 1**, starting exactly on the downbeat with
  no pre-roll, and let the release ring: the file is the clip's musical length plus the release tail, **at most one extra bar**
  (the build rejects longer files and warns when the tail is still sounding at its end).
- One WAV per part and sound: render the kick part with the kick sound named in the file name, the snare part with the
  snare sound, and so on. The accompaniment is one bus (pad and hats together).
- Ableton: Export Audio/Video, Rendered Track = the part's track (solo, or use the track's own export), Render Start = the clip's
  first bar, Render Length = the clip's bars (+ up to one bar for the tail), Sample Rate 48000, Bit Depth 16, File Type WAV,
  Normalize off, Create Analysis File off, Convert to Mono off.

## MIDI (only if you change the notes)

The clip MIDI files below are the structure the cues are made from. Every one exists already (cut from your First_Three MIDI,
or generated); you only export a new one when you want different notes. Export the clip as MIDI from Ableton (type 0 or 1,
any PPQ; with no tempo in the file 174 BPM is assumed), save it over the file named in the table, then re-render every WAV of
that part: the build refuses a WAV rendered from the earlier MIDI. Note lengths count (bass notes of an eighth or longer are
holds) and a hold must end inside its four-bar sequence.

## Where the files go and the one command

Put each WAV in the clip's folder under the name given (`content/library/<clip>/<part>__<sound>.wav`) and run, from the
project folder:

```
python tools/content/build.py
```

It checks every file (rate, channels, bit depth, length, tail, silence, alignment of the attacks to the MIDI, the MIDI's
tempo, meter and grid, cues, holds and headroom), uses your files instead of the placeholders, rebuilds the game's stems and
previews in `songs/`, and lists what is still placeholder in `content/REPORT.md` with the times to listen at. Your files are
never written; delete one to go back to its placeholder. Commit your WAVs together with `content/build_state.json`. Then
rebuild the exports (`docs/EXPORT.md`).

The placeholder of every file is already in place as a reference you can drag into Ableton:
`content/library/<clip>/placeholder/<part>__<sound>.wav` (same length and timing your render should have). If that folder is
missing on a fresh checkout, run the build once.

## The files

### `acc_first_watch`: First Watch accompaniment

accompaniment (pad and hats on one bus), **32 bars** (44.14 s; with the longest tail 45.52 s), key C# minor, used in mission 1. MIDI from your First_Three MIDI, level_01 bars 1-32.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| other | `content/library/acc_first_watch/other.mid` | `content/library/acc_first_watch/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` |

### `groove_watch`: Watch

groove (kick and snare parts), **2 bars** (2.76 s; with the longest tail 4.14 s), used in mission 1. MIDI from your First_Three MIDI, level_01 bars 1-2.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| kick | `content/library/groove_watch/kick.mid` | `content/library/groove_watch/kick__kick_armour.wav` | Armour Kick | `placeholder/kick__kick_armour.wav` |
| kick | `content/library/groove_watch/kick.mid` | `content/library/groove_watch/kick__kick_march.wav` | March Kick | `placeholder/kick__kick_march.wav` |
| snare | `content/library/groove_watch/snare.mid` | `content/library/groove_watch/snare__snare_guard.wav` | Guard Snare | `placeholder/snare__snare_guard.wav` |

### `acc_second_pulse`: Second Pulse accompaniment

accompaniment (pad and hats on one bus), **40 bars** (55.17 s; with the longest tail 56.55 s), key C# minor, used in mission 2. MIDI from your First_Three MIDI, level_02 bars 1-40.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| other | `content/library/acc_second_pulse/other.mid` | `content/library/acc_second_pulse/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` |

### `groove_push`: Push

groove (kick and snare parts), **2 bars** (2.76 s; with the longest tail 4.14 s), used in missions 2, 3, 4, 5, 6, 7, 8, 9, 10. MIDI from your First_Three MIDI, level_02 bars 9-10.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| kick | `content/library/groove_push/kick.mid` | `content/library/groove_push/kick__kick_armour.wav` | Armour Kick | `placeholder/kick__kick_armour.wav` |
| kick | `content/library/groove_push/kick.mid` | `content/library/groove_push/kick__kick_heavy.wav` | Heavy Kick | `placeholder/kick__kick_heavy.wav` |
| kick | `content/library/groove_push/kick.mid` | `content/library/groove_push/kick__kick_march.wav` | March Kick | `placeholder/kick__kick_march.wav` |
| kick | `content/library/groove_push/kick.mid` | `content/library/groove_push/kick__kick_siege.wav` | Siege Kick | `placeholder/kick__kick_siege.wav` |
| snare | `content/library/groove_push/snare.mid` | `content/library/groove_push/snare__snare_clap.wav` | Field Clap | `placeholder/snare__snare_clap.wav` |
| snare | `content/library/groove_push/snare.mid` | `content/library/groove_push/snare__snare_crack.wav` | Crack Snare | `placeholder/snare__snare_crack.wav` |
| snare | `content/library/groove_push/snare.mid` | `content/library/groove_push/snare__snare_guard.wav` | Guard Snare | `placeholder/snare__snare_guard.wav` |
| snare | `content/library/groove_push/snare.mid` | `content/library/groove_push/snare__snare_rim.wav` | Rimshot | `placeholder/snare__snare_rim.wav` |

### `groove_straight`: Straight

groove (kick and snare parts), **2 bars** (2.76 s; with the longest tail 4.14 s), used in mission 2. MIDI from your First_Three MIDI, level_02 bars 1-2.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| kick | `content/library/groove_straight/kick.mid` | `content/library/groove_straight/kick__kick_armour.wav` | Armour Kick | `placeholder/kick__kick_armour.wav` |
| kick | `content/library/groove_straight/kick.mid` | `content/library/groove_straight/kick__kick_march.wav` | March Kick | `placeholder/kick__kick_march.wav` |
| snare | `content/library/groove_straight/snare.mid` | `content/library/groove_straight/snare__snare_crack.wav` | Crack Snare | `placeholder/snare__snare_crack.wav` |
| snare | `content/library/groove_straight/snare.mid` | `content/library/groove_straight/snare__snare_guard.wav` | Guard Snare | `placeholder/snare__snare_guard.wav` |

### `acc_hold_the_line`: Hold the Line accompaniment

accompaniment (pad and hats on one bus), **48 bars** (66.21 s; with the longest tail 67.59 s), key C# minor, used in mission 3. MIDI from your First_Three MIDI, level_03 bars 1-48.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| other | `content/library/acc_hold_the_line/other.mid` | `content/library/acc_hold_the_line/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` |

### `bass_hold_a`: Long Line

bass line, **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, used in missions 3, 7, 9, 10. MIDI from your First_Three MIDI, level_03 bars 1-8.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| bass | `content/library/bass_hold_a/bass.mid` | `content/library/bass_hold_a/bass__bass_patrol.wav` | Patrol Sub | `placeholder/bass__bass_patrol.wav` |
| bass | `content/library/bass_hold_a/bass.mid` | `content/library/bass_hold_a/bass__bass_reese.wav` | Reese | `placeholder/bass__bass_reese.wav` |

### `bass_hold_b`: Answer Line

bass line, **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, used in missions 3, 5, 7, 9, 10. MIDI from your First_Three MIDI, level_03 bars 9-16.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| bass | `content/library/bass_hold_b/bass.mid` | `content/library/bass_hold_b/bass__bass_command.wav` | Command Saw | `placeholder/bass__bass_command.wav` |
| bass | `content/library/bass_hold_b/bass.mid` | `content/library/bass_hold_b/bass__bass_growl.wav` | Growl | `placeholder/bass__bass_growl.wav` |
| bass | `content/library/bass_hold_b/bass.mid` | `content/library/bass_hold_b/bass__bass_hollow.wav` | Hollow Sub | `placeholder/bass__bass_hollow.wav` |
| bass | `content/library/bass_hold_b/bass.mid` | `content/library/bass_hold_b/bass__bass_patrol.wav` | Patrol Sub | `placeholder/bass__bass_patrol.wav` |
| bass | `content/library/bass_hold_b/bass.mid` | `content/library/bass_hold_b/bass__bass_reese.wav` | Reese | `placeholder/bass__bass_reese.wav` |

### `bass_hold_end`: Answer Line (ending)

bass line, **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, used in mission 3. MIDI from your First_Three MIDI, level_03 bars 41-48.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| bass | `content/library/bass_hold_end/bass.mid` | `content/library/bass_hold_end/bass__bass_patrol.wav` | Patrol Sub | `placeholder/bass__bass_patrol.wav` |
| bass | `content/library/bass_hold_end/bass.mid` | `content/library/bass_hold_end/bass__bass_reese.wav` | Reese | `placeholder/bass__bass_reese.wav` |

### `acc_backbeat`: Backbeat accompaniment

accompaniment (pad and hats on one bus), **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, used in mission 4. MIDI from generated placeholder MIDI.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| other | `content/library/acc_backbeat/other.mid` | `content/library/acc_backbeat/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` |

### `fill_snare_run`: Snare Run

fill (kick and snare parts), **1 bars** (1.38 s; with the longest tail 2.76 s), used in missions 4, 5, 6, 7, 8, 9, 10. MIDI from generated placeholder MIDI.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| kick | `content/library/fill_snare_run/kick.mid` | `content/library/fill_snare_run/kick__kick_armour.wav` | Armour Kick | `placeholder/kick__kick_armour.wav` |
| kick | `content/library/fill_snare_run/kick.mid` | `content/library/fill_snare_run/kick__kick_heavy.wav` | Heavy Kick | `placeholder/kick__kick_heavy.wav` |
| kick | `content/library/fill_snare_run/kick.mid` | `content/library/fill_snare_run/kick__kick_march.wav` | March Kick | `placeholder/kick__kick_march.wav` |
| kick | `content/library/fill_snare_run/kick.mid` | `content/library/fill_snare_run/kick__kick_siege.wav` | Siege Kick | `placeholder/kick__kick_siege.wav` |
| snare | `content/library/fill_snare_run/snare.mid` | `content/library/fill_snare_run/snare__snare_clap.wav` | Field Clap | `placeholder/snare__snare_clap.wav` |
| snare | `content/library/fill_snare_run/snare.mid` | `content/library/fill_snare_run/snare__snare_crack.wav` | Crack Snare | `placeholder/snare__snare_crack.wav` |
| snare | `content/library/fill_snare_run/snare.mid` | `content/library/fill_snare_run/snare__snare_guard.wav` | Guard Snare | `placeholder/snare__snare_guard.wav` |
| snare | `content/library/fill_snare_run/snare.mid` | `content/library/fill_snare_run/snare__snare_rim.wav` | Rimshot | `placeholder/snare__snare_rim.wav` |

### `groove_twostep`: Two-Step

groove (kick and snare parts), **2 bars** (2.76 s; with the longest tail 4.14 s), used in missions 4, 5, 6, 7, 8, 9, 10. MIDI from generated placeholder MIDI.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| kick | `content/library/groove_twostep/kick.mid` | `content/library/groove_twostep/kick__kick_armour.wav` | Armour Kick | `placeholder/kick__kick_armour.wav` |
| kick | `content/library/groove_twostep/kick.mid` | `content/library/groove_twostep/kick__kick_heavy.wav` | Heavy Kick | `placeholder/kick__kick_heavy.wav` |
| kick | `content/library/groove_twostep/kick.mid` | `content/library/groove_twostep/kick__kick_march.wav` | March Kick | `placeholder/kick__kick_march.wav` |
| kick | `content/library/groove_twostep/kick.mid` | `content/library/groove_twostep/kick__kick_siege.wav` | Siege Kick | `placeholder/kick__kick_siege.wav` |
| snare | `content/library/groove_twostep/snare.mid` | `content/library/groove_twostep/snare__snare_clap.wav` | Field Clap | `placeholder/snare__snare_clap.wav` |
| snare | `content/library/groove_twostep/snare.mid` | `content/library/groove_twostep/snare__snare_crack.wav` | Crack Snare | `placeholder/snare__snare_crack.wav` |
| snare | `content/library/groove_twostep/snare.mid` | `content/library/groove_twostep/snare__snare_guard.wav` | Guard Snare | `placeholder/snare__snare_guard.wav` |
| snare | `content/library/groove_twostep/snare.mid` | `content/library/groove_twostep/snare__snare_rim.wav` | Rimshot | `placeholder/snare__snare_rim.wav` |

### `acc_counterpoint`: Counterpoint accompaniment

accompaniment (pad and hats on one bus), **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, used in mission 5. MIDI from generated placeholder MIDI.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| other | `content/library/acc_counterpoint/other.mid` | `content/library/acc_counterpoint/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` |

### `bass_steps`: Steps

bass line, **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, used in missions 5, 7, 9, 10. MIDI from generated placeholder MIDI.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| bass | `content/library/bass_steps/bass.mid` | `content/library/bass_steps/bass__bass_command.wav` | Command Saw | `placeholder/bass__bass_command.wav` |
| bass | `content/library/bass_steps/bass.mid` | `content/library/bass_steps/bass__bass_growl.wav` | Growl | `placeholder/bass__bass_growl.wav` |
| bass | `content/library/bass_steps/bass.mid` | `content/library/bass_steps/bass__bass_hollow.wav` | Hollow Sub | `placeholder/bass__bass_hollow.wav` |
| bass | `content/library/bass_steps/bass.mid` | `content/library/bass_steps/bass__bass_patrol.wav` | Patrol Sub | `placeholder/bass__bass_patrol.wav` |
| bass | `content/library/bass_steps/bass.mid` | `content/library/bass_steps/bass__bass_reese.wav` | Reese | `placeholder/bass__bass_reese.wav` |

### `acc_fortress`: Fortress accompaniment

accompaniment (pad and hats on one bus), **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, used in mission 6. MIDI from generated placeholder MIDI.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| other | `content/library/acc_fortress/other.mid` | `content/library/acc_fortress/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` |

### `groove_roller`: Roller

groove (kick and snare parts), **2 bars** (2.76 s; with the longest tail 4.14 s), used in missions 6, 7, 8, 9, 10. MIDI from generated placeholder MIDI.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| kick | `content/library/groove_roller/kick.mid` | `content/library/groove_roller/kick__kick_armour.wav` | Armour Kick | `placeholder/kick__kick_armour.wav` |
| kick | `content/library/groove_roller/kick.mid` | `content/library/groove_roller/kick__kick_heavy.wav` | Heavy Kick | `placeholder/kick__kick_heavy.wav` |
| kick | `content/library/groove_roller/kick.mid` | `content/library/groove_roller/kick__kick_march.wav` | March Kick | `placeholder/kick__kick_march.wav` |
| kick | `content/library/groove_roller/kick.mid` | `content/library/groove_roller/kick__kick_siege.wav` | Siege Kick | `placeholder/kick__kick_siege.wav` |
| snare | `content/library/groove_roller/snare.mid` | `content/library/groove_roller/snare__snare_clap.wav` | Field Clap | `placeholder/snare__snare_clap.wav` |
| snare | `content/library/groove_roller/snare.mid` | `content/library/groove_roller/snare__snare_crack.wav` | Crack Snare | `placeholder/snare__snare_crack.wav` |
| snare | `content/library/groove_roller/snare.mid` | `content/library/groove_roller/snare__snare_guard.wav` | Guard Snare | `placeholder/snare__snare_guard.wav` |
| snare | `content/library/groove_roller/snare.mid` | `content/library/groove_roller/snare__snare_rim.wav` | Rimshot | `placeholder/snare__snare_rim.wav` |

### `acc_crossroads`: Crossroads accompaniment

accompaniment (pad and hats on one bus), **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, used in mission 7. MIDI from generated placeholder MIDI.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| other | `content/library/acc_crossroads/other.mid` | `content/library/acc_crossroads/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` |

### `bass_octaves`: Octaves

bass line, **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, used in missions 7, 9, 10. MIDI from generated placeholder MIDI.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| bass | `content/library/bass_octaves/bass.mid` | `content/library/bass_octaves/bass__bass_command.wav` | Command Saw | `placeholder/bass__bass_command.wav` |
| bass | `content/library/bass_octaves/bass.mid` | `content/library/bass_octaves/bass__bass_growl.wav` | Growl | `placeholder/bass__bass_growl.wav` |
| bass | `content/library/bass_octaves/bass.mid` | `content/library/bass_octaves/bass__bass_hollow.wav` | Hollow Sub | `placeholder/bass__bass_hollow.wav` |
| bass | `content/library/bass_octaves/bass.mid` | `content/library/bass_octaves/bass__bass_patrol.wav` | Patrol Sub | `placeholder/bass__bass_patrol.wav` |
| bass | `content/library/bass_octaves/bass.mid` | `content/library/bass_octaves/bass__bass_reese.wav` | Reese | `placeholder/bass__bass_reese.wav` |

### `acc_crossfire`: Crossfire accompaniment

accompaniment (pad and hats on one bus), **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, used in mission 8. MIDI from generated placeholder MIDI.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| other | `content/library/acc_crossfire/other.mid` | `content/library/acc_crossfire/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` |

### `fill_break`: Break

fill (kick and snare parts), **1 bars** (1.38 s; with the longest tail 2.76 s), used in missions 8, 9, 10. MIDI from generated placeholder MIDI.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| kick | `content/library/fill_break/kick.mid` | `content/library/fill_break/kick__kick_armour.wav` | Armour Kick | `placeholder/kick__kick_armour.wav` |
| kick | `content/library/fill_break/kick.mid` | `content/library/fill_break/kick__kick_heavy.wav` | Heavy Kick | `placeholder/kick__kick_heavy.wav` |
| kick | `content/library/fill_break/kick.mid` | `content/library/fill_break/kick__kick_march.wav` | March Kick | `placeholder/kick__kick_march.wav` |
| kick | `content/library/fill_break/kick.mid` | `content/library/fill_break/kick__kick_siege.wav` | Siege Kick | `placeholder/kick__kick_siege.wav` |
| snare | `content/library/fill_break/snare.mid` | `content/library/fill_break/snare__snare_clap.wav` | Field Clap | `placeholder/snare__snare_clap.wav` |
| snare | `content/library/fill_break/snare.mid` | `content/library/fill_break/snare__snare_crack.wav` | Crack Snare | `placeholder/snare__snare_crack.wav` |
| snare | `content/library/fill_break/snare.mid` | `content/library/fill_break/snare__snare_guard.wav` | Guard Snare | `placeholder/snare__snare_guard.wav` |
| snare | `content/library/fill_break/snare.mid` | `content/library/fill_break/snare__snare_rim.wav` | Rimshot | `placeholder/snare__snare_rim.wav` |

### `acc_iron`: Iron Rhythm accompaniment

accompaniment (pad and hats on one bus), **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, used in mission 9. MIDI from generated placeholder MIDI.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| other | `content/library/acc_iron/other.mid` | `content/library/acc_iron/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` |

### `fill_kick_drop`: Kick Drop

fill (kick and snare parts), **1 bars** (1.38 s; with the longest tail 2.76 s), used in missions 9, 10. MIDI from generated placeholder MIDI.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| kick | `content/library/fill_kick_drop/kick.mid` | `content/library/fill_kick_drop/kick__kick_armour.wav` | Armour Kick | `placeholder/kick__kick_armour.wav` |
| kick | `content/library/fill_kick_drop/kick.mid` | `content/library/fill_kick_drop/kick__kick_heavy.wav` | Heavy Kick | `placeholder/kick__kick_heavy.wav` |
| kick | `content/library/fill_kick_drop/kick.mid` | `content/library/fill_kick_drop/kick__kick_march.wav` | March Kick | `placeholder/kick__kick_march.wav` |
| kick | `content/library/fill_kick_drop/kick.mid` | `content/library/fill_kick_drop/kick__kick_siege.wav` | Siege Kick | `placeholder/kick__kick_siege.wav` |
| snare | `content/library/fill_kick_drop/snare.mid` | `content/library/fill_kick_drop/snare__snare_clap.wav` | Field Clap | `placeholder/snare__snare_clap.wav` |
| snare | `content/library/fill_kick_drop/snare.mid` | `content/library/fill_kick_drop/snare__snare_crack.wav` | Crack Snare | `placeholder/snare__snare_crack.wav` |
| snare | `content/library/fill_kick_drop/snare.mid` | `content/library/fill_kick_drop/snare__snare_guard.wav` | Guard Snare | `placeholder/snare__snare_guard.wav` |
| snare | `content/library/fill_kick_drop/snare.mid` | `content/library/fill_kick_drop/snare__snare_rim.wav` | Rimshot | `placeholder/snare__snare_rim.wav` |

### `acc_last_light`: Last Light accompaniment

accompaniment (pad and hats on one bus), **8 bars** (11.03 s; with the longest tail 12.41 s), key C# minor, used in mission 10. MIDI from generated placeholder MIDI.

| Part | MIDI (structure) | WAV to render | Sound | Reference placeholder |
| --- | --- | --- | --- | --- |
| other | `content/library/acc_last_light/other.mid` | `content/library/acc_last_light/other__ensemble.wav` | Ensemble | `placeholder/other__ensemble.wav` |

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

Adding a sound or a clip: add the sound to `content/sounds.json` (or copy `content/fixtures/example_groove/` to
`content/library/<new_id>/` and edit its `clip.json`), offer it in a mission's choices (`content/missions/level_NN.json`)
and run the build: it lists the renders it still needs as placeholders.
