# Music catalogue

Written by `python tools/content/catalogue.py` from the owner's folders (never modified; `.asd` and `.import` files ignored). Do not edit; regenerate.
The machine-readable form is `content/music/catalogue.json` (schema 1); the arrangement tool reads only that. Tempo is measured, never taken from the MIDI header.

## Summary

123 WAV files (117 already used by a pack or library clip), 97 MIDI files, 32 families; 388 family pairs have parts that can be layered, 276 pass the rules and 244 of those are flagged uncertain.

| Folder | WAV | Used in game | MIDI | Profile | Musical bars | MIDI header BPM |
| --- | --- | --- | --- | --- | --- | --- |
| ToAddTry1 | 16 | 16 | 6 | 174x1 x16 | 8 x16 | none |
| ToAddTry2 | 66 | 60 | 63 | 174x1 x29, 87x2 x36, unknown x1 | 4 x27, 8 x36, 16 x3 | 120.0 x63 |
| ToAddTry3/Cold | 27 | 27 | 18 | 174x1 x27 | 4 x23, 16 x4 | 120.0 x12 |
| ToAddTry3/Meta | 14 | 14 | 10 | 174x1 x14 | 8 x6, 16 x8 | 120.0 x6 |

## Facts the audio shows

- ToAddTry1: 16 Ableton renders (MIDI carries no tempo); 174x1 x16; musical length 8 bars x16.
- ToAddTry1: 4 render(s) shorter than their MIDI (the MIDI runs on past the recording): Kick1.wav, Kick2.wav, Kick3.wav, Snare1.wav.
- ToAddTry1: 9 file(s) clip or exceed full scale (Kick1.wav, Kick2.wav, Kick3.wav, Snare1.wav, bass1a.wav, bass1c.wav).
- ToAddTry2: 63 Beat Shaper WAVs with MIDI; MIDI headers say 120 BPM, the audio measures 174x1 x27, 87x2 x36; musical length 4 bars x27, 8 bars x36.
- ToAddTry2: 1 render(s) still sounding at their end (Beat Shaper - Lv5 Asylum-Bass (1).wav); the release is cut there.
- ToAddTry3/Cold: 12 Beat Shaper WAVs with MIDI; MIDI headers say 120 BPM, the audio measures 174x1 x12; musical length 4 bars x12.
- ToAddTry3/Cold: 15 Ableton renders (MIDI carries no tempo); 174x1 x15; musical length 4 bars x11, 16 bars x4.
- ToAddTry3/Cold: 2 render(s) shorter than their MIDI (the MIDI runs on past the recording): Bass2FlaringAnger.wav, Bass2Hardharmonic.wav.
- ToAddTry3/Cold: 3 render(s) still sounding at their end (Bass5FlaringAnger.wav, Bass5HardHarmonic.wav, Bass5Trap.wav); the release is cut there.
- ToAddTry3/Cold: 5 file(s) clip or exceed full scale (Bass2Trap.wav, Bass3Trap.wav, Bass4Trap.wav, Bass5Trap.wav, Beat Shaper - Cold Fusion Interface-Bass (3).wav).
- ToAddTry3/Meta: 6 Beat Shaper WAVs with MIDI; MIDI headers say 120 BPM, the audio measures 174x1 x6; musical length 8 bars x6.
- ToAddTry3/Meta: 8 Ableton renders (MIDI carries no tempo); 174x1 x8; musical length 16 bars x8.
- ToAddTry3/Meta: 2 file(s) clip or exceed full scale (Bass1Trap.wav, Snare1.wav).
- Ableton renders whose MIDI is a shorter pattern repeated: Snare1.wav (1-bar pattern x8), Bass2Trap.wav (4-bar pattern x4), Kick2.wav (8-bar pattern x2), Snare2.wav (1-bar pattern x16), Bass1FlaringAnger.wav (8-bar pattern x2), Bass1HardHarmonic.wav (8-bar pattern x2), Bass1Trap.wav (8-bar pattern x2), Kick1.wav (8-bar pattern x2), Kick2.wav (8-bar pattern x2), Snare1.wav (1-bar pattern x16).

## Files by folder

Profile `174x1`: one source quarter is one game beat; `87x2`: one quarter is two. Bars are whole game bars of music (4 beats at 174 BPM); `pat` is the repeating pattern length of the MIDI; tail is the release after the musical end. Key is a Krumhansl-Schmuckler estimate with its confidence (advisory). Clip = samples at full scale (an over-full-scale float counts). Used = the packs and library clips built from the file (`used_by` in the JSON).

### ToAddTry1

| File | Role | Family | Pair | Profile | BPM | Bars (pat) | Lead ms | Tail s | Key | RMS | Peak | Clip | Used |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Kick1.wav | kick | ab_toaddtry1_kick1 | MIDI | 174x1 | 174.2 | 8 (8) | 0 | 0.00 none | atonal | -14.8 | 0.0 | 3600 | groove_half_time |
| Kick2.wav | kick | ab_toaddtry1_kick2 | MIDI | 174x1 | 174.2 | 8 (8) | 0 | 0.00 none | atonal | -14.4 | 0.0 | 3960 | groove_double_step |
| Kick3.wav | kick | ab_toaddtry1_kick3 | MIDI | 174x1 | 174.1 | 8 (8) | 0 | 0.00 none | atonal | -12.8 | 0.0 | 5760 | groove_rolling |
| Other1.wav | perc | ab_toaddtry1_other1 | audio only | 174x1 | 174.0 | 8 (-) | 345 | 8.28 silence | atonal | -23.9 | -1.5 | 0 | acc_hats_driving |
| Other2.wav | perc | ab_toaddtry1_other2 | audio only | 174x1 | 174.0 | 8 (-) | 862 | 0.00 none | atonal | -22.5 | -1.7 | 0 | acc_hats_busy |
| Other3.wav | perc | ab_toaddtry1_other3 | audio only | 174x1 | 174.0 | 8 (-) | 172 | 0.00 none | atonal | -23.0 | -1.7 | 0 | acc_hats_offbeat |
| Snare1.wav | snare | ab_toaddtry1_snare1 | MIDI | 174x1 | 174.0 | 8 (1) | 690 | 0.00 none | atonal | -20.0 | 0.0 | 536 | groove_double_step, groove_half_time, groove_rolling |
| bass1.wav | bass | ab_toaddtry1_bass1 | MIDI | 174x1 | 174.0 | 8 (8) | 0 | 0.00 none | F minor (0.01) | -13.1 | 0.0 | 1 | bass_sub_line |
| bass1a.wav | bass | ab_toaddtry1_bass1 | MIDI | 174x1 | 174.0 | 8 (8) | 0 | 0.00 none | F minor (0.01) | -15.1 | 0.0 | 316 | bass_sub_line |
| bass1b.wav | bass | ab_toaddtry1_bass1 | MIDI | 174x1 | 174.0 | 8 (8) | 0 | 0.00 none | F minor (0.01) | -7.5 | -6.3 | 0 | bass_sub_line |
| bass1c.wav | bass | ab_toaddtry1_bass1 | MIDI | 174x1 | 174.0 | 8 (8) | 0 | 0.00 none | F minor (0.01) | -12.3 | 0.0 | 50 | bass_sub_line |
| bass1d.wav | bass | ab_toaddtry1_bass1 | MIDI | 174x1 | 174.0 | 8 (8) | 0 | 0.00 none | F minor (0.01) | -12.5 | 0.0 | 44 | bass_sub_line |
| bass2a.wav | bass | ab_toaddtry1_bass2 | MIDI | 174x1 | 173.9 | 8 (8) | 0 | 0.00 none | F minor (0.50) | -10.4 | 0.0 | 192 | bass_reese_line |
| bass2b.wav | bass | ab_toaddtry1_bass2 | MIDI | 174x1 | 174.0 | 8 (8) | 4 | 0.00 none | F minor (0.50) | -12.2 | -0.4 | 0 | bass_reese_line |
| bass2c.wav | bass | ab_toaddtry1_bass2 | MIDI | 174x1 | 174.0 | 8 (8) | 4 | 0.00 none | F minor (0.50) | -13.5 | -6.6 | 0 | bass_reese_line |
| bass2d.wav | bass | ab_toaddtry1_bass2 | MIDI | 174x1 | 174.2 | 8 (8) | 0 | 0.00 none | F minor (0.50) | -11.4 | 0.0 | 2877 | bass_reese_line |

### ToAddTry2

| File | Role | Family | Pair | Profile | BPM | Bars (pat) | Lead ms | Tail s | Key | RMS | Peak | Clip | Used |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Beat Shaper - DD Part1-Bass (1).wav | bass | bs_dd_part1 | MIDI | 87x2 | 87.0 | 8 (8) | 0 | 1.43 release | C major (1.00) | -24.9 | -15.0 | 0 | dd_part1_v1 |
| Beat Shaper - DD Part1-Bass (2).wav | bass | bs_dd_part1 | MIDI | 87x2 | 87.0 | 8 (8) | 0 | 1.39 release | C minor (0.34) | -25.2 | -13.0 | 0 | dd_part1_v2 |
| Beat Shaper - DD Part1-Bass (3).wav | bass | bs_dd_part1 | MIDI | 87x2 | 87.0 | 8 (8) | 0 | 1.18 release | A minor (0.89) | -25.1 | -14.0 | 0 | dd_part1_v3 |
| Beat Shaper - DD Part1-Bass.wav | bass | bs_dd_part1 | MIDI | 87x2 | 87.0 | 8 (8) | 0 | 1.74 release | A major (1.00) | -24.9 | -11.8 | 0 | dd_part1 |
| Beat Shaper - DD Part1-Drums (1).wav | drums | bs_dd_part1 | MIDI | 87x2 | 87.0 | 8 (4) | 3 | 0.18 release | atonal | -24.6 | -8.5 | 0 | dd_part1_v1 |
| Beat Shaper - DD Part1-Drums (2).wav | drums | bs_dd_part1 | MIDI | 87x2 | 87.0 | 8 (4) | 3 | 0.18 release | atonal | -26.1 | -8.4 | 0 | dd_part1_v2 |
| Beat Shaper - DD Part1-Drums (3).wav | drums | bs_dd_part1 | MIDI | 87x2 | 87.0 | 8 (2) | 3 | 0.17 release | atonal | -24.6 | -8.5 | 0 | dd_part1_v3 |
| Beat Shaper - DD Part1-Drums.wav | drums | bs_dd_part1 | MIDI | 87x2 | 87.0 | 8 (4) | 3 | 0.18 release | atonal | -26.1 | -8.5 | 0 | dd_part1 |
| Beat Shaper - DD Part1-Synth (1).wav | pad | bs_dd_part1 | MIDI | 87x2 | 87.0 | 8 (8) | 1 | 1.25 release | C minor (0.00) | -41.7 | -28.8 | 0 | dd_part1_v1 |
| Beat Shaper - DD Part1-Synth (2).wav | synth | bs_dd_part1 | MIDI | 87x2 | 86.9 | 8 (8) | 1 | 1.72 release | C major (0.01) | -43.4 | -28.8 | 0 | dd_part1_v2 |
| Beat Shaper - DD Part1-Synth (3).wav | pad | bs_dd_part1 | MIDI | 87x2 | 87.0 | 8 (8) | 1 | 0.48 release | F minor (0.00) | -42.0 | -28.4 | 0 | dd_part1_v3 |
| Beat Shaper - DD Part1-Synth.wav | pad | bs_dd_part1 | MIDI | 87x2 | 87.0 | 8 (8) | 1 | 0.51 release | E minor (0.60) | -42.1 | -29.0 | 0 | dd_part1 |
| Beat Shaper - DD Part2-Bass.wav | bass | bs_dd_part2 | MIDI | 174x1 | 174.0 | 4 (4) | 345 | 1.52 release | F minor (0.81) | -25.8 | -14.5 | 0 | dd_part2 |
| Beat Shaper - DD Part2-Drums.wav | drums | bs_dd_part2 | MIDI | 174x1 | 173.8 | 4 (2) | 3 | 0.35 release | atonal | -21.3 | -7.5 | 0 | dd_part2 |
| Beat Shaper - DD Part2-Synth.wav | pad | bs_dd_part2 | MIDI | 174x1 | 174.0 | 4 (4) | 2 | 0.58 release | F minor (0.60) | -41.8 | -28.6 | 0 | dd_part2 |
| Beat Shaper - Default Project-Bass.wav | bass | bs_default_project | MIDI | 87x2 | 87.0 | 8 (8) | 1 | 0.03 short | A major (0.48) | -24.9 | -12.4 | 0 | - |
| Beat Shaper - Default Project-Drums.wav | drums | bs_default_project | MIDI | 87x2 | 87.0 | 8 (8) | 3 | 0.49 release | atonal | -23.6 | -7.2 | 0 | - |
| Beat Shaper - Default Project-Synth.wav | synth | bs_default_project | MIDI | 87x2 | 87.0 | 8 (8) | 2 | 2.15 release | E minor (0.29) | -37.8 | -28.8 | 0 | - |
| Beat Shaper - Lv1 Warehouse-Bass (1).wav | bass | bs_lv1_warehouse | MIDI | 87x2 | 87.0 | 8 (8) | 1 | 0.00 none | A major (1.00) | -24.9 | -12.6 | 0 | lv1_warehouse_v1 |
| Beat Shaper - Lv1 Warehouse-Bass (2).wav | bass | bs_lv1_warehouse | MIDI | 87x2 | 87.0 | 8 (8) | 1 | 0.03 short | A minor (0.79) | -25.3 | -12.0 | 0 | lv1_warehouse_v2 |
| Beat Shaper - Lv1 Warehouse-Bass.wav | bass | bs_lv1_warehouse | MIDI | 87x2 | 87.0 | 8 (8) | 0 | 1.40 release | E minor (0.40) | -24.7 | -14.2 | 0 | lv1_warehouse |
| Beat Shaper - Lv1 Warehouse-Drums (1).wav | drums | bs_lv1_warehouse | MIDI | 87x2 | 87.0 | 8 (8) | 3 | 0.35 release | atonal | -23.4 | -7.5 | 0 | lv1_warehouse_v1 |
| Beat Shaper - Lv1 Warehouse-Drums (2).wav | drums | bs_lv1_warehouse | MIDI | 87x2 | 87.0 | 8 (8) | 3 | 0.60 release | atonal | -23.4 | -7.6 | 0 | lv1_warehouse_v2 |
| Beat Shaper - Lv1 Warehouse-Drums.wav | drums | bs_lv1_warehouse | MIDI | 87x2 | 87.0 | 8 (8) | 3 | 0.60 release | atonal | -23.9 | -7.6 | 0 | lv1_warehouse |
| Beat Shaper - Lv1 Warehouse-Synth (1).wav | synth | bs_lv1_warehouse | MIDI | 87x2 | 87.0 | 8 (8) | 2 | 1.84 release | E minor (0.95) | -39.1 | -26.0 | 0 | lv1_warehouse_v1 |
| Beat Shaper - Lv1 Warehouse-Synth (2).wav | synth | bs_lv1_warehouse | MIDI | 87x2 | 87.0 | 8 (8) | 2 | 1.83 release | E minor (0.85) | -39.1 | -26.0 | 0 | lv1_warehouse_v2 |
| Beat Shaper - Lv1 Warehouse-Synth.wav | synth | bs_lv1_warehouse | MIDI | 87x2 | 87.0 | 8 (8) | 2 | 1.94 release | E minor (0.93) | -39.3 | -29.1 | 0 | lv1_warehouse |
| Beat Shaper - Lv2 Alien Spaceship-Bass (1).wav | bass | bs_lv2_alien_spaceship | MIDI | 174x1 | 174.0 | 4 (4) | 0 | 0.03 short | F minor (0.61) | -25.8 | -12.5 | 0 | lv2_alien_spaceship_v1 |
| Beat Shaper - Lv2 Alien Spaceship-Bass (2).wav | bass | bs_lv2_alien_spaceship | MIDI | 174x1 | 174.2 | 4 (4) | 0 | 0.04 short | C major (1.00) | -22.3 | -16.0 | 0 | lv2_alien_spaceship_v2 |
| Beat Shaper - Lv2 Alien Spaceship-Bass (3).wav | bass | bs_lv2_alien_spaceship | MIDI | 174x1 | 174.0 | 4 (4) | 0 | 1.02 release | C major (0.99) | -22.9 | -9.4 | 0 | lv2_alien_spaceship_v3 |
| Beat Shaper - Lv2 Alien Spaceship-Bass.wav | bass | bs_lv2_alien_spaceship | MIDI | 174x1 | 174.0 | 4 (2) | 0 | 1.54 release | - | -25.6 | -12.6 | 0 | lv2_alien_spaceship |
| Beat Shaper - Lv2 Alien Spaceship-Drums (1).wav | drums | bs_lv2_alien_spaceship | MIDI | 174x1 | 174.0 | 4 (4) | 3 | 0.43 release | atonal | -28.8 | -9.8 | 0 | lv2_alien_spaceship_v1 |
| Beat Shaper - Lv2 Alien Spaceship-Drums (2).wav | drums | bs_lv2_alien_spaceship | MIDI | 174x1 | 174.0 | 4 (2) | 3 | 0.47 release | atonal | -23.4 | -8.5 | 0 | lv2_alien_spaceship_v2 |
| Beat Shaper - Lv2 Alien Spaceship-Drums (3).wav | drums | bs_lv2_alien_spaceship | MIDI | 174x1 | 174.0 | 4 (4) | 3 | 0.60 release | atonal | -27.7 | -8.4 | 0 | lv2_alien_spaceship_v3 |
| Beat Shaper - Lv2 Alien Spaceship-Drums.wav | drums | bs_lv2_alien_spaceship | MIDI | 174x1 | 173.9 | 4 (4) | 3 | 0.60 release | atonal | -23.4 | -7.1 | 0 | lv2_alien_spaceship |
| Beat Shaper - Lv2 Alien Spaceship-Synth (1).wav | synth | bs_lv2_alien_spaceship | MIDI | 174x1 | 174.0 | 4 (4) | 3 | 0.79 release | F minor (1.00) | -38.8 | -24.8 | 0 | lv2_alien_spaceship_v1 |
| Beat Shaper - Lv2 Alien Spaceship-Synth (2).wav | synth | bs_lv2_alien_spaceship | MIDI | 174x1 | 174.0 | 4 (4) | 1 | 0.97 release | C minor (0.57) | -39.5 | -26.1 | 0 | lv2_alien_spaceship_v2 |
| Beat Shaper - Lv2 Alien Spaceship-Synth (3).wav | synth | bs_lv2_alien_spaceship | MIDI | 174x1 | 174.1 | 4 (4) | 5 | 0.80 release | C major (0.71) | -37.7 | -22.7 | 0 | lv2_alien_spaceship_v3 |
| Beat Shaper - Lv2 Alien Spaceship-Synth.wav | synth | bs_lv2_alien_spaceship | MIDI | 174x1 | 173.9 | 4 (4) | 0 | 0.85 release | F minor (0.79) | -39.9 | -24.7 | 0 | lv2_alien_spaceship |
| Beat Shaper - Lv3 Hell-Bass.wav | bass | bs_lv3_hell | audio only | unknown | - | 16 (-) | 0 | 0.17 release | G# minor (0.00) | -26.1 | -11.4 | 0 | - |
| Beat Shaper - Lv3 Hell-Drums.wav | drums | bs_lv3_hell | audio only | 174x1 | 174.0 | 16 (-) | 3 | 0.40 release | atonal | -21.6 | -4.6 | 0 | - |
| Beat Shaper - Lv3 Hell-Synth.wav | synth | bs_lv3_hell | audio only | 174x1 | 174.0 | 16 (-) | 8 | 0.00 none | E minor (0.45) | -48.4 | -27.4 | 0 | - |
| Beat Shaper - Lv5 Asylum-Bass (1).wav | bass | bs_lv5_asylum | MIDI | 87x2 | 87.0 | 8 (8) | 345 | 0.38 cut while sounding | F major (0.64) | -28.3 | -10.1 | 0 | lv5_asylum_v1 |
| Beat Shaper - Lv5 Asylum-Bass (2).wav | bass | bs_lv5_asylum | MIDI | 87x2 | 87.0 | 8 (8) | 1 | 0.00 none | E minor (0.79) | -26.6 | -9.9 | 0 | lv5_asylum_v2 |
| Beat Shaper - Lv5 Asylum-Bass (3).wav | bass | bs_lv5_asylum | MIDI | 87x2 | 87.0 | 8 (8) | 1 | 0.03 short | E minor (0.79) | -27.3 | -11.3 | 0 | lv5_asylum_v3 |
| Beat Shaper - Lv5 Asylum-Bass.wav | bass | bs_lv5_asylum | MIDI | 87x2 | 87.0 | 8 (8) | 1 | 0.03 short | D minor (0.68) | -27.9 | -10.4 | 0 | lv5_asylum |
| Beat Shaper - Lv5 Asylum-Drums (1).wav | drums | bs_lv5_asylum | MIDI | 87x2 | 87.0 | 8 (8) | 353 | 1.28 release | atonal | -23.3 | -6.9 | 0 | lv5_asylum_v1 |
| Beat Shaper - Lv5 Asylum-Drums (2).wav | drums | bs_lv5_asylum | MIDI | 87x2 | 87.0 | 8 (2) | 3 | 0.82 release | atonal | -23.2 | -6.3 | 0 | lv5_asylum_v2 |
| Beat Shaper - Lv5 Asylum-Drums (3).wav | drums | bs_lv5_asylum | MIDI | 87x2 | 87.0 | 8 (4) | 3 | 0.52 release | atonal | -26.3 | -6.9 | 0 | lv5_asylum_v3 |
| Beat Shaper - Lv5 Asylum-Drums.wav | drums | bs_lv5_asylum | MIDI | 87x2 | 87.0 | 8 (4) | 3 | 0.99 release | atonal | -22.7 | -6.9 | 0 | lv5_asylum |
| Beat Shaper - Lv5 Asylum-Synth (1).wav | synth | bs_lv5_asylum | MIDI | 87x2 | 87.0 | 8 (8) | 347 | 1.27 release | C minor (0.10) | -40.5 | -26.3 | 0 | lv5_asylum_v1 |
| Beat Shaper - Lv5 Asylum-Synth (2).wav | synth | bs_lv5_asylum | MIDI | 87x2 | 86.9 | 8 (8) | 3 | 0.61 release | G major (0.55) | -42.9 | -25.9 | 0 | lv5_asylum_v2 |
| Beat Shaper - Lv5 Asylum-Synth (3).wav | synth | bs_lv5_asylum | MIDI | 87x2 | 87.0 | 8 (8) | 1 | 1.10 release | E major (0.77) | -38.1 | -26.7 | 0 | lv5_asylum_v3 |
| Beat Shaper - Lv5 Asylum-Synth.wav | synth | bs_lv5_asylum | MIDI | 87x2 | 87.2 | 8 (8) | 5 | 1.66 release | D minor (1.00) | -39.6 | -28.1 | 0 | lv5_asylum |
| Beat Shaper - lv4 Hospital-Bass (1).wav | bass | bs_lv4_hospital | MIDI | 174x1 | 174.0 | 4 (4) | 0 | 0.49 release | F major (0.09) | -21.7 | -12.8 | 0 | lv4_hospital_v1 |
| Beat Shaper - lv4 Hospital-Bass (2).wav | bass | bs_lv4_hospital | MIDI | 174x1 | 174.0 | 4 (4) | 1 | 0.48 release | E minor (0.58) | -22.2 | -12.8 | 0 | lv4_hospital_v2 |
| Beat Shaper - lv4 Hospital-Bass (3).wav | bass | bs_lv4_hospital | MIDI | 174x1 | 174.0 | 4 (4) | 1 | 0.48 release | C# major (1.00) | -21.8 | -13.1 | 0 | lv4_hospital_v3 |
| Beat Shaper - lv4 Hospital-Bass.wav | bass | bs_lv4_hospital | MIDI | 174x1 | 174.0 | 4 (4) | 1 | 0.48 release | F# major (0.15) | -21.6 | -12.8 | 0 | lv4_hospital |
| Beat Shaper - lv4 Hospital-Drums (1).wav | drums | bs_lv4_hospital | MIDI | 174x1 | 174.0 | 4 (2) | 3 | 0.69 release | atonal | -21.5 | -7.4 | 0 | lv4_hospital_v1 |
| Beat Shaper - lv4 Hospital-Drums (2).wav | drums | bs_lv4_hospital | MIDI | 174x1 | 173.8 | 4 (2) | 3 | 0.68 release | atonal | -22.3 | -7.2 | 0 | lv4_hospital_v2 |
| Beat Shaper - lv4 Hospital-Drums (3).wav | drums | bs_lv4_hospital | MIDI | 174x1 | 174.1 | 4 (1) | 3 | 0.69 release | atonal | -20.1 | -7.2 | 0 | lv4_hospital_v3 |
| Beat Shaper - lv4 Hospital-Drums.wav | drums | bs_lv4_hospital | MIDI | 174x1 | 174.0 | 4 (2) | 3 | 0.47 release | atonal | -22.4 | -8.6 | 0 | lv4_hospital |
| Beat Shaper - lv4 Hospital-Synth (1).wav | synth | bs_lv4_hospital | MIDI | 174x1 | 174.2 | 4 (4) | 2 | 1.25 release | C major (0.96) | -38.2 | -27.9 | 0 | lv4_hospital_v1 |
| Beat Shaper - lv4 Hospital-Synth (2).wav | synth | bs_lv4_hospital | MIDI | 174x1 | 174.9 | 4 (4) | 2 | 1.27 release | C major (0.75) | -39.5 | -29.3 | 0 | lv4_hospital_v2 |
| Beat Shaper - lv4 Hospital-Synth (3).wav | synth | bs_lv4_hospital | MIDI | 174x1 | 174.0 | 4 (4) | 2 | 1.23 release | F minor (0.55) | -39.2 | -29.0 | 0 | lv4_hospital_v3 |
| Beat Shaper - lv4 Hospital-Synth.wav | synth | bs_lv4_hospital | MIDI | 174x1 | 174.7 | 4 (4) | 2 | 1.37 release | F# major (0.03) | -38.9 | -28.7 | 0 | lv4_hospital |

### ToAddTry3/Cold

| File | Role | Family | Pair | Profile | BPM | Bars (pat) | Lead ms | Tail s | Key | RMS | Peak | Clip | Used |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Bass2FlaringAnger.wav | bass | ab_cold_bass2 | MIDI | 174x1 | 174.4 | 4 (4) | 0 | 0.00 none | B minor (0.37) | -8.1 | -6.2 | 0 | bass_cold_2 |
| Bass2Hardharmonic.wav | bass | ab_cold_bass2 | MIDI | 174x1 | 173.0 | 4 (4) | 0 | 0.00 none | B minor (0.37) | -12.9 | -2.4 | 0 | bass_cold_2 |
| Bass2Trap.wav | bass | ab_cold_bass2 | MIDI | 174x1 | 174.0 | 16 (4) | 6 | 0.00 none | B minor (0.37) | -15.0 | 0.0 | 342 | bass_cold_2 |
| Bass3FlaringAnger.wav | bass | ab_cold_bass3 | MIDI | 174x1 | 174.8 | 4 (4) | 0 | 0.00 none | A# minor (0.20) | -7.8 | -6.3 | 0 | bass_cold_3 |
| Bass3HardHarmonic.wav | bass | ab_cold_bass3 | MIDI | 174x1 | 173.8 | 4 (4) | 0 | 0.00 none | A# minor (0.20) | -11.7 | -3.2 | 0 | bass_cold_3 |
| Bass3Trap.wav | bass | ab_cold_bass3 | MIDI | 174x1 | 174.8 | 4 (4) | 6 | 0.00 none | A# minor (0.20) | -13.3 | 0.0 | 255 | bass_cold_3 |
| Bass4FlaringAnger.wav | bass | ab_cold_bass4 | MIDI | 174x1 | 175.1 | 4 (4) | 0 | 0.00 none | F major (0.56) | -7.8 | -6.2 | 0 | bass_cold_4 |
| Bass4HardHarmonic.wav | bass | ab_cold_bass4 | MIDI | 174x1 | 175.8 | 4 (4) | 0 | 0.00 none | F major (0.56) | -12.1 | -2.3 | 0 | bass_cold_4 |
| Bass4Trap.wav | bass | ab_cold_bass4 | MIDI | 174x1 | 175.8 | 4 (4) | 10 | 0.00 none | F major (0.56) | -13.8 | 0.0 | 195 | bass_cold_4 |
| Bass5FlaringAnger.wav | bass | ab_cold_bass5 | MIDI | 174x1 | 174.0 | 4 (4) | 0 | 2.48 cut while sounding | E minor (0.51) | -7.9 | -5.8 | 0 | bass_cold_5 |
| Bass5HardHarmonic.wav | bass | ab_cold_bass5 | MIDI | 174x1 | 174.0 | 4 (4) | 0 | 2.48 cut while sounding | E minor (0.51) | -12.2 | -3.0 | 0 | bass_cold_5 |
| Bass5Trap.wav | bass | ab_cold_bass5 | MIDI | 174x1 | 174.0 | 4 (4) | 8 | 2.48 cut while sounding | E minor (0.51) | -13.2 | 0.0 | 290 | bass_cold_5 |
| Beat Shaper - Cold Fusion Interface-Bass (1).wav | bass | bs_cold_fusion_interface | MIDI | 174x1 | 174.0 | 4 (4) | 0 | 0.00 none | A# minor (0.35) | -24.4 | -16.2 | 0 | cold_fusion_v1 |
| Beat Shaper - Cold Fusion Interface-Bass (2).wav | bass | bs_cold_fusion_interface | MIDI | 174x1 | 174.6 | 4 (4) | 1 | 0.04 short | F major (0.56) | -23.3 | -12.1 | 0 | cold_fusion_v2 |
| Beat Shaper - Cold Fusion Interface-Bass (3).wav | bass | bs_cold_fusion_interface | MIDI | 174x1 | 173.1 | 4 (4) | 0 | 0.28 release | E minor (0.51) | -23.5 | 1.3 | 68 | cold_fusion_v3 |
| Beat Shaper - Cold Fusion Interface-Bass.wav | bass | bs_cold_fusion_interface | MIDI | 174x1 | 173.7 | 4 (4) | 0 | 0.04 short | B minor (0.37) | -23.6 | -11.9 | 0 | cold_fusion |
| Beat Shaper - Cold Fusion Interface-Drums (1).wav | drums | bs_cold_fusion_interface | MIDI | 174x1 | 174.0 | 4 (1) | 3 | 0.55 release | atonal | -22.1 | -8.1 | 0 | cold_fusion_v1 |
| Beat Shaper - Cold Fusion Interface-Drums (2).wav | drums | bs_cold_fusion_interface | MIDI | 174x1 | 174.0 | 4 (4) | 3 | 0.47 release | atonal | -22.6 | -8.7 | 0 | cold_fusion_v2 |
| Beat Shaper - Cold Fusion Interface-Drums (3).wav | drums | bs_cold_fusion_interface | MIDI | 174x1 | 174.0 | 4 (2) | 3 | 0.55 release | atonal | -22.0 | -8.0 | 0 | cold_fusion_v3 |
| Beat Shaper - Cold Fusion Interface-Drums.wav | drums | bs_cold_fusion_interface | MIDI | 174x1 | 173.9 | 4 (1) | 3 | 0.47 release | atonal | -23.5 | -8.1 | 0 | cold_fusion |
| Beat Shaper - Cold Fusion Interface-Synth (1).wav | synth | bs_cold_fusion_interface | MIDI | 174x1 | 173.8 | 4 (4) | 1384 | 1.34 release | A# minor (0.55) | -41.1 | -26.7 | 0 | cold_fusion_v1 |
| Beat Shaper - Cold Fusion Interface-Synth (2).wav | synth | bs_cold_fusion_interface | MIDI | 174x1 | 173.9 | 4 (4) | 3 | 0.96 release | A minor (0.57) | -40.3 | -29.1 | 0 | cold_fusion_v2 |
| Beat Shaper - Cold Fusion Interface-Synth (3).wav | synth | bs_cold_fusion_interface | MIDI | 174x1 | 173.8 | 4 (4) | 2 | 1.00 release | E minor (0.90) | -40.3 | -28.4 | 0 | cold_fusion_v3 |
| Beat Shaper - Cold Fusion Interface-Synth.wav | synth | bs_cold_fusion_interface | MIDI | 174x1 | 174.0 | 4 (4) | 0 | 1.46 release | D major (0.75) | -40.1 | -25.0 | 0 | cold_fusion |
| Kick2.wav | kick | ab_cold_kick2 | MIDI | 174x1 | 174.0 | 16 (8) | 0 | 0.00 none | atonal | -20.2 | -0.7 | 0 | groove_cold |
| Other2.wav | perc | ab_cold_other2 | audio only | 174x1 | 174.0 | 16 (-) | 0 | 0.00 none | atonal | -18.7 | -1.6 | 0 | acc_cold_loop |
| Snare2.wav | snare | ab_cold_snare2 | MIDI | 174x1 | 174.0 | 16 (1) | 345 | 0.00 none | atonal | -18.0 | -0.1 | 0 | groove_cold |

### ToAddTry3/Meta

| File | Role | Family | Pair | Profile | BPM | Bars (pat) | Lead ms | Tail s | Key | RMS | Peak | Clip | Used |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Bass1FlaringAnger.wav | bass | ab_meta_bass1 | MIDI | 174x1 | 174.1 | 16 (8) | 0 | 0.00 none | F major (0.82) | -7.6 | -6.5 | 0 | bass_meta_1 |
| Bass1HardHarmonic.wav | bass | ab_meta_bass1 | MIDI | 174x1 | 174.0 | 16 (8) | 0 | 0.00 none | F major (0.82) | -11.3 | -2.4 | 0 | bass_meta_1 |
| Bass1Trap.wav | bass | ab_meta_bass1 | MIDI | 174x1 | 174.0 | 16 (8) | 9 | 0.00 none | F major (0.82) | -12.6 | 0.0 | 1486 | bass_meta_1 |
| Beat Shaper - Metaverse Ready Fusion-Bass (1).wav | bass | bs_metaverse_ready_fusion | MIDI | 174x1 | 173.9 | 8 (8) | 1 | 0.04 short | F major (0.82) | -23.4 | -12.2 | 0 | meta_fusion_v1 |
| Beat Shaper - Metaverse Ready Fusion-Bass.wav | bass | bs_metaverse_ready_fusion | MIDI | 174x1 | 174.0 | 8 (8) | 1 | 0.04 short | D major (0.39) | -23.1 | -12.0 | 0 | meta_fusion |
| Beat Shaper - Metaverse Ready Fusion-Drums (1).wav | drums | bs_metaverse_ready_fusion | MIDI | 174x1 | 174.0 | 8 (8) | 3 | 0.68 release | atonal | -20.8 | -7.6 | 0 | meta_fusion_v1 |
| Beat Shaper - Metaverse Ready Fusion-Drums.wav | drums | bs_metaverse_ready_fusion | MIDI | 174x1 | 174.0 | 8 (8) | 3 | 0.60 release | atonal | -22.2 | -9.0 | 0 | meta_fusion |
| Beat Shaper - Metaverse Ready Fusion-Synth (1).wav | synth | bs_metaverse_ready_fusion | MIDI | 174x1 | 174.0 | 8 (4) | 7 | 1.50 release | C minor (0.08) | -37.8 | -26.4 | 0 | meta_fusion_v1 |
| Beat Shaper - Metaverse Ready Fusion-Synth.wav | synth | bs_metaverse_ready_fusion | MIDI | 174x1 | 173.9 | 8 (8) | 0 | 0.84 release | D minor (0.59) | -38.9 | -25.0 | 0 | meta_fusion |
| Kick1.wav | kick | ab_meta_kick1 | MIDI | 174x1 | 174.0 | 16 (8) | 0 | 0.00 none | atonal | -16.2 | -0.0 | 0 | groove_meta_a |
| Kick2.wav | kick | ab_meta_kick2 | MIDI | 174x1 | 174.0 | 16 (8) | 0 | 0.00 none | atonal | -15.0 | -0.0 | 0 | groove_meta_b |
| Other1.wav | perc | ab_meta_other1 | audio only | 174x1 | 174.0 | 16 (-) | 172 | 0.00 none | atonal | -21.4 | -2.4 | 0 | acc_meta_a |
| Other2.wav | perc | ab_meta_other2 | audio only | 174x1 | 174.0 | 16 (-) | 172 | 0.00 none | atonal | -21.7 | -2.4 | 0 | acc_meta_b |
| Snare1.wav | snare | ab_meta_snare1 | MIDI | 174x1 | 174.0 | 16 (1) | 345 | 0.00 none | atonal | -21.3 | -0.0 | 96 | groove_meta_a, groove_meta_b |

## Families

A family is the strongest grouping the exports give: a Beat Shaper project with all its variants, or an Ableton pattern with all its timbre renders.

| Family | Kind | Sets | Roles (bars, profile) | Timbres | Key |
| --- | --- | --- | --- | --- | --- |
| ab_cold_bass2 | ableton_pattern | 1 | bass (4/16, 174x1) | FlaringAnger, Hardharmonic, Trap | bass: B minor (0.37) |
| ab_cold_bass3 | ableton_pattern | 1 | bass (4, 174x1) | FlaringAnger, HardHarmonic, Trap | bass: A# minor (0.20) |
| ab_cold_bass4 | ableton_pattern | 1 | bass (4, 174x1) | FlaringAnger, HardHarmonic, Trap | bass: F major (0.56) |
| ab_cold_bass5 | ableton_pattern | 1 | bass (4, 174x1) | FlaringAnger, HardHarmonic, Trap | bass: E minor (0.51) |
| ab_cold_kick2 | ableton_pattern | 1 | kick (16, 174x1) | - | atonal |
| ab_cold_other2 | ableton_pattern | 1 | perc (16, 174x1) | - | atonal |
| ab_cold_snare2 | ableton_pattern | 1 | snare (16, 174x1) | - | atonal |
| ab_meta_bass1 | ableton_pattern | 1 | bass (16, 174x1) | FlaringAnger, HardHarmonic, Trap | bass: F major (0.82) |
| ab_meta_kick1 | ableton_pattern | 1 | kick (16, 174x1) | - | atonal |
| ab_meta_kick2 | ableton_pattern | 1 | kick (16, 174x1) | - | atonal |
| ab_meta_other1 | ableton_pattern | 1 | perc (16, 174x1) | - | atonal |
| ab_meta_other2 | ableton_pattern | 1 | perc (16, 174x1) | - | atonal |
| ab_meta_snare1 | ableton_pattern | 1 | snare (16, 174x1) | - | atonal |
| ab_toaddtry1_bass1 | ableton_pattern | 1 | bass (8, 174x1) | a, b, c, d | bass: F minor (0.01) |
| ab_toaddtry1_bass2 | ableton_pattern | 1 | bass (8, 174x1) | a, b, c, d | bass: F minor (0.50) |
| ab_toaddtry1_kick1 | ableton_pattern | 1 | kick (8, 174x1) | - | atonal |
| ab_toaddtry1_kick2 | ableton_pattern | 1 | kick (8, 174x1) | - | atonal |
| ab_toaddtry1_kick3 | ableton_pattern | 1 | kick (8, 174x1) | - | atonal |
| ab_toaddtry1_other1 | ableton_pattern | 1 | perc (8, 174x1) | - | atonal |
| ab_toaddtry1_other2 | ableton_pattern | 1 | perc (8, 174x1) | - | atonal |
| ab_toaddtry1_other3 | ableton_pattern | 1 | perc (8, 174x1) | - | atonal |
| ab_toaddtry1_snare1 | ableton_pattern | 1 | snare (8, 174x1) | - | atonal |
| bs_cold_fusion_interface | beat_shaper_project | 4 | bass (4, 174x1); drums (4, 174x1); synth (4, 174x1) | - | bass: F major (0.00); synth: D minor (0.07) |
| bs_dd_part1 | beat_shaper_project | 4 | bass (8, 87x2); drums (8, 87x2); pad (8, 87x2); synth (8, 87x2) | - | bass: A minor (1.00); pad: C major (0.58); synth: C major (0.01) |
| bs_dd_part2 | beat_shaper_project | 1 | bass (4, 174x1); drums (4, 174x1); pad (4, 174x1) | - | bass: F minor (0.81); pad: F minor (0.60) |
| bs_default_project | beat_shaper_project | 1 | bass (8, 87x2); drums (8, 87x2); synth (8, 87x2) | - | bass: A major (0.48); synth: E minor (0.29) |
| bs_lv1_warehouse | beat_shaper_project | 3 | bass (8, 87x2); drums (8, 87x2); synth (8, 87x2) | - | bass: A major (0.21); synth: E minor (0.94) |
| bs_lv2_alien_spaceship | beat_shaper_project | 4 | bass (4, 174x1); drums (4, 174x1); synth (4, 174x1) | - | bass: C major (0.41); synth: F minor (0.70) |
| bs_lv3_hell | beat_shaper_project | 1 | bass (16, unknown); drums (16, 174x1); synth (16, 174x1) | - | bass: G# minor (0.00); synth: E minor (0.45) |
| bs_lv4_hospital | beat_shaper_project | 4 | bass (4, 174x1); drums (4, 174x1); synth (4, 174x1) | - | bass: G major (0.00); synth: C major (0.32) |
| bs_lv5_asylum | beat_shaper_project | 4 | bass (8, 87x2); drums (8, 87x2); synth (8, 87x2) | - | bass: C major (0.67); synth: E minor (0.69) |
| bs_metaverse_ready_fusion | beat_shaper_project | 2 | bass (8, 174x1); drums (8, 174x1); synth (8, 174x1) | - | bass: D minor (0.93); synth: F major (0.19) |

Variants of a Beat Shaper project whose tonal estimates disagree or are weak (the variants may be different progressions; listen before mixing sets):

- bs_cold_fusion_interface: v0 B minor, v1 A# minor, v2 F major, v3 E minor
- bs_dd_part1: v0 A major, v1 C major, v2 C minor, v3 F major
- bs_lv1_warehouse: v0 E minor, v1 A minor, v2 A minor
- bs_lv2_alien_spaceship: v0 F minor, v1 F minor, v2 C major, v3 C major
- bs_lv4_hospital: v0 F# major, v1 C major, v2 E minor, v3 C# major
- bs_lv5_asylum: v0 D minor, v1 F minor, v2 G major, v3 E major
- bs_metaverse_ready_fusion: v0 D minor, v1 F major

## Compatibility

Within a family every part is compatible (the export grouping is the strongest evidence). Across families a pair of parts is compatible only when the phrase lengths are equal or tile, the profiles are the same, and the tonal centres are the same or relative or one part is atonal; a nearby key (parallel or a fifth), a low-confidence estimate or a phrase that tiles rather than matches makes it `uncertain`; keys that disagree are incompatible. A shared tempo never decides anything. The full table (every family pair, every combination of parts, why each failed) is in the JSON.

388 family pairs have parts that can be layered; 276 are compatible (32 firm, 244 uncertain).

### Compatible pairs involving ToAddTry1 or ToAddTry3 (firm)

| Family A | Family B | Basis | Parts that fit |
| --- | --- | --- | --- |
| ab_cold_bass2 | bs_cold_fusion_interface | same folder | bass+drums |
| ab_cold_bass3 | bs_cold_fusion_interface | same folder | bass+drums |
| ab_cold_bass4 | bs_cold_fusion_interface | same folder | bass+drums |
| ab_cold_bass5 | bs_cold_fusion_interface | same folder | bass+drums |
| ab_cold_kick2 | ab_meta_bass1 | rules only | kick+bass |
| ab_cold_kick2 | bs_metaverse_ready_fusion | rules only | kick+bass, kick+synth |
| ab_meta_bass1 | ab_meta_kick1 | same folder, same pattern number | bass+kick |
| ab_meta_bass1 | ab_meta_kick2 | same folder | bass+kick |
| ab_meta_bass1 | bs_metaverse_ready_fusion | same folder | bass+drums |
| ab_meta_kick1 | bs_metaverse_ready_fusion | same folder | kick+bass, kick+synth |
| ab_meta_kick2 | bs_metaverse_ready_fusion | same folder | kick+bass, kick+synth |
| ab_toaddtry1_bass1 | ab_toaddtry1_kick1 | same folder, same pattern number | bass+kick |
| ab_toaddtry1_bass1 | ab_toaddtry1_kick2 | same folder | bass+kick |
| ab_toaddtry1_bass1 | ab_toaddtry1_kick3 | same folder | bass+kick |
| ab_toaddtry1_bass1 | ab_toaddtry1_other1 | same folder, same pattern number | bass+perc |
| ab_toaddtry1_bass1 | ab_toaddtry1_other2 | same folder | bass+perc |
| ab_toaddtry1_bass1 | ab_toaddtry1_other3 | same folder | bass+perc |
| ab_toaddtry1_bass2 | ab_toaddtry1_kick1 | same folder | bass+kick |
| ab_toaddtry1_bass2 | ab_toaddtry1_kick2 | same folder, same pattern number | bass+kick |
| ab_toaddtry1_bass2 | ab_toaddtry1_kick3 | same folder | bass+kick |
| ab_toaddtry1_bass2 | ab_toaddtry1_other1 | same folder | bass+perc |
| ab_toaddtry1_bass2 | ab_toaddtry1_other2 | same folder, same pattern number | bass+perc |
| ab_toaddtry1_bass2 | ab_toaddtry1_other3 | same folder | bass+perc |
| bs_cold_fusion_interface | bs_metaverse_ready_fusion | rules only | drums+synth |

### Flagged for the owner's ear (uncertain)

Compatible by the rules but resting on a low-confidence or nearby key, or a phrase that tiles. Listen before relying on them.

| Family A | Family B | Basis | Parts | Why uncertain |
| --- | --- | --- | --- | --- |
| ab_cold_bass2 | ab_cold_kick2 | same folder, same pattern number | bass+kick | phrases tile rather than match |
| ab_cold_bass2 | ab_cold_other2 | same folder, same pattern number | bass+perc | phrases tile rather than match |
| ab_cold_bass2 | ab_cold_snare2 | same folder, same pattern number | bass+snare | phrases tile rather than match |
| ab_cold_bass2 | ab_meta_kick1 | rules only | bass+kick | phrases tile rather than match |
| ab_cold_bass2 | ab_meta_kick2 | rules only | bass+kick | phrases tile rather than match |
| ab_cold_bass2 | ab_meta_other1 | rules only | bass+perc | phrases tile rather than match |
| ab_cold_bass2 | ab_meta_other2 | rules only | bass+perc | phrases tile rather than match |
| ab_cold_bass2 | ab_meta_snare1 | rules only | bass+snare | phrases tile rather than match |
| ab_cold_bass2 | ab_toaddtry1_kick1 | rules only | bass+kick | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass2 | ab_toaddtry1_kick2 | rules only | bass+kick | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass2 | ab_toaddtry1_kick3 | rules only | bass+kick | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass2 | ab_toaddtry1_other1 | rules only | bass+perc | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass2 | ab_toaddtry1_other2 | rules only | bass+perc | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass2 | ab_toaddtry1_other3 | rules only | bass+perc | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass2 | ab_toaddtry1_snare1 | rules only | bass+snare | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass2 | bs_dd_part2 | rules only | bass+drums | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass2 | bs_lv2_alien_spaceship | rules only | bass+drums | only rules (no shared source folder) support it |
| ab_cold_bass2 | bs_lv3_hell | rules only | bass+drums, bass+synth | only rules (no shared source folder) support it, phrases tile rather than match, tonal estimate weak or nearby key |
| ab_cold_bass2 | bs_lv4_hospital | rules only | bass+drums | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass2 | bs_metaverse_ready_fusion | rules only | bass+drums | phrases tile rather than match |
| ab_cold_bass3 | ab_cold_kick2 | same folder | bass+kick | phrases tile rather than match |
| ab_cold_bass3 | ab_cold_other2 | same folder | bass+perc | phrases tile rather than match |
| ab_cold_bass3 | ab_cold_snare2 | same folder | bass+snare | phrases tile rather than match |
| ab_cold_bass3 | ab_meta_kick1 | rules only | bass+kick | phrases tile rather than match |
| ab_cold_bass3 | ab_meta_kick2 | rules only | bass+kick | phrases tile rather than match |
| ab_cold_bass3 | ab_meta_other1 | rules only | bass+perc | phrases tile rather than match |
| ab_cold_bass3 | ab_meta_other2 | rules only | bass+perc | phrases tile rather than match |
| ab_cold_bass3 | ab_meta_snare1 | rules only | bass+snare | phrases tile rather than match |
| ab_cold_bass3 | ab_toaddtry1_kick1 | rules only | bass+kick | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass3 | ab_toaddtry1_kick2 | rules only | bass+kick | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass3 | ab_toaddtry1_kick3 | rules only | bass+kick | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass3 | ab_toaddtry1_other1 | rules only | bass+perc | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass3 | ab_toaddtry1_other2 | rules only | bass+perc | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass3 | ab_toaddtry1_other3 | rules only | bass+perc | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass3 | ab_toaddtry1_snare1 | rules only | bass+snare | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass3 | bs_dd_part2 | rules only | bass+drums, bass+pad | only rules (no shared source folder) support it, phrases tile rather than match, tonal estimate weak or nearby key |
| ab_cold_bass3 | bs_lv2_alien_spaceship | rules only | bass+drums, bass+synth | only rules (no shared source folder) support it, tonal estimate weak or nearby key |
| ab_cold_bass3 | bs_lv3_hell | rules only | bass+drums | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass3 | bs_lv4_hospital | rules only | bass+drums | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass3 | bs_metaverse_ready_fusion | rules only | bass+drums | phrases tile rather than match |
| ab_cold_bass4 | ab_cold_kick2 | same folder | bass+kick | phrases tile rather than match |
| ab_cold_bass4 | ab_cold_other2 | same folder | bass+perc | phrases tile rather than match |
| ab_cold_bass4 | ab_cold_snare2 | same folder | bass+snare | phrases tile rather than match |
| ab_cold_bass4 | ab_meta_kick1 | rules only | bass+kick | phrases tile rather than match |
| ab_cold_bass4 | ab_meta_kick2 | rules only | bass+kick | phrases tile rather than match |
| ab_cold_bass4 | ab_meta_other1 | rules only | bass+perc | phrases tile rather than match |
| ab_cold_bass4 | ab_meta_other2 | rules only | bass+perc | phrases tile rather than match |
| ab_cold_bass4 | ab_meta_snare1 | rules only | bass+snare | phrases tile rather than match |
| ab_cold_bass4 | ab_toaddtry1_kick1 | rules only | bass+kick | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass4 | ab_toaddtry1_kick2 | rules only | bass+kick | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass4 | ab_toaddtry1_kick3 | rules only | bass+kick | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass4 | ab_toaddtry1_other1 | rules only | bass+perc | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass4 | ab_toaddtry1_other2 | rules only | bass+perc | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass4 | ab_toaddtry1_other3 | rules only | bass+perc | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass4 | ab_toaddtry1_snare1 | rules only | bass+snare | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass4 | bs_dd_part2 | rules only | bass+drums, bass+pad | only rules (no shared source folder) support it, phrases tile rather than match, tonal estimate weak or nearby key |
| ab_cold_bass4 | bs_lv2_alien_spaceship | rules only | bass+drums, bass+synth | only rules (no shared source folder) support it, tonal estimate weak or nearby key |
| ab_cold_bass4 | bs_lv3_hell | rules only | bass+drums | only rules (no shared source folder) support it, phrases tile rather than match |
| ab_cold_bass4 | bs_lv4_hospital | rules only | bass+drums, bass+synth | only rules (no shared source folder) support it, phrases tile rather than match, tonal estimate weak or nearby key |
| ab_cold_bass4 | bs_metaverse_ready_fusion | rules only | bass+drums, bass+synth | phrases tile rather than match, tonal estimate weak or nearby key |
| ... | 184 more in the JSON | | | |

## Same notes under another name

- `ToAddTry3/Cold/Kick2.mid` has the same notes as `ToAddTry3/Meta/Kick1.mid`
- `ToAddTry3/Cold/Snare2.mid` has the same notes as `ToAddTry3/Meta/Snare1.mid`
- `ToAddTry3/Meta/Kick1.mid` has the same notes as `ToAddTry3/Cold/Kick2.mid`
- `ToAddTry3/Meta/Snare1.mid` has the same notes as `ToAddTry3/Cold/Snare2.mid`

