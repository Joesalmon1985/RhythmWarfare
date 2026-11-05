# Mix after the audio polish

Written by `python tools/run/measure_mix.py` (offline render from the packs, perfect play, block b = mix stage b, the bass revealed at beat 16; see the script's docstring).
Voice seconds are per 64-beat phase; `in` = the block (1-4) the voice is first audible; peak is before the run's limiter.

## Before and after

Means over each run's scenes (bass seconds include a carried bass in block 0); worst peak = the loudest scene, before any limiter (the run has none).

| run | bass band 30-250 | sub 30-80 | bass-drums dB | phone bass dB | bass audible s / phase | bass leads s / phase | scenes with a carry | LUFS | worst peak dBFS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main | 82.9% -> 87.9% | 39.6% -> 36.6% | +3.9 -> +9.3 | -2.9 -> -1.3 | 16.6 -> 21.3 of 22.1 | 11.6 -> 20.2 | 0 -> 31 of 36 | -20.7 -> -14.8 | -2.8 -> -1.1 |
| gospel | 86.4% -> 88.8% | 48.1% -> 51.9% | +10.0 -> +12.0 | -0.2 -> -0.2 | 23.2 -> 23.2 of 31.0 | 23.2 -> 23.2 | 0 -> 0 of 17 | -12.6 -> -14.1 | 1.0 -> -0.8 |
| squadron | 84.8% -> 87.4% | 38.1% -> 38.4% | +11.0 -> +14.4 | -1.2 -> -0.6 | 20.6 -> 20.6 of 27.4 | 19.6 -> 20.6 | 0 -> 0 of 14 | -14.3 -> -12.9 | -0.5 -> -0.9 |
| ember | 88.1% -> 89.7% | 51.9% -> 44.3% | +12.0 -> +13.3 | -0.2 -> -0.1 | 19.9 -> 19.9 of 26.5 | 19.9 -> 19.9 | 0 -> 0 of 15 | -12.6 -> -13.1 | 0.2 -> -1.3 |

## main (174 BPM)

Dwell: phase 22.1 s (4 blocks of 5.52 s); 36 scenes; default route 16 phases; phases per music family along it [4, 4, 8], per world [4, 4, 5, 3]; 1-2 arrangement sections per phase (shortest 11.0 s); up to 4 mix/arrangement changes per phase; stage bass gains [0.0, 1.0, 0.85, 1.0]; recipe bass floor 0.9; bass in 16.6 s then out 5.5 s at every scene change (carried at 0.5 within a family); 24 hotspots dip the music to 0.55 (-5.2 dB) for 6 beats (2.1 s); phase fade 0.6 s; run level +2 dB.

| scene | family | drums s (in) | bass s (in) | synth s (in) | bass leads s | LUFS | peak dBFS | bass band 30-250 | sub 30-80 | bass-drums dB | bass-synth dB | phone bass dB | carry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| warehouse | lv1_warehouse | 22.1 (1) | 16.6 (2) | 11.0 (3) | 16.6 | -15.6 | -3.2 | 88% | 45% | +8.4 | +19.1 | -1.7 |  |
| warehouse.bar | lv1_warehouse | 22.1 (1) | 22.1 (1) | 16.6 (2) | 22.1 | -15.2 | -4.2 | 89% | 45% | +12.8 | +17.7 | -1.2 | yes |
| warehouse.balcony | lv1_warehouse | 22.1 (1) | 22.1 (1) | 11.0 (2) | 22.1 | -14.7 | -3.2 | 94% | 46% | +10.7 | +19.3 | -1.9 | yes |
| warehouse.chill | lv1_warehouse | 22.1 (1) | 22.1 (1) | 16.6 (2) | 22.1 | -14.9 | -3.2 | 92% | 41% | +9.8 | +19.1 | -1.5 | yes |
| warehouse.booth | lv1_warehouse | 16.6 (1) | 22.1 (1) | 16.6 (2) | 22.1 | -14.9 | -4.1 | 92% | 41% | +12.8 | +18.3 | -1.1 | yes |
| warehouse.exit | lv1_warehouse | 22.1 (1) | 22.1 (1) | 5.5 (2) | 22.1 | -14.9 | -2.9 | 91% | 41% | +8.9 | +20.4 | -1.6 | yes |
| mothership | lv2_alien_spaceship | 22.1 (1) | 16.6 (2) | 11.0 (3) | 16.6 | -15.4 | -2.2 | 88% | 53% | +12.0 | +19.2 | -2.0 |  |
| mothership.gallery | lv2_alien_spaceship | 22.1 (1) | 22.1 (1) | 11.0 (3) | 22.1 | -14.5 | -3.0 | 89% | 42% | +12.8 | +19.1 | -1.4 | yes |
| mothership.reactor | lv2_alien_spaceship | 22.1 (1) | 22.1 (1) | 0.0 (-) | 22.1 | -12.9 | -2.9 | 85% | 28% | +11.3 | +21.0 | -1.4 | yes |
| mothership.bridge | lv2_alien_spaceship | 22.1 (1) | 22.1 (1) | 5.5 (2) | 22.1 | -13.6 | -2.9 | 86% | 36% | +11.4 | +20.3 | -1.5 | yes |
| mothership.exit | lv2_alien_spaceship | 22.1 (1) | 22.1 (1) | 0.0 (-) | 22.1 | -15.2 | -1.2 | 90% | 52% | +8.0 | +21.4 | -2.9 | yes |
| underworld | cold_fusion_interface | 22.1 (1) | 16.6 (2) | 0.0 (-) | 16.6 | -14.5 | -2.4 | 81% | 31% | +8.7 | +21.2 | -0.9 |  |
| underworld.court | cold_fusion_interface | 22.1 (1) | 22.1 (1) | 0.0 (-) | 22.1 | -14.1 | -3.2 | 82% | 31% | +9.9 | +22.4 | -0.8 | yes |
| underworld.furnace | cold_fusion_interface | 22.1 (1) | 22.1 (1) | 0.0 (-) | 22.1 | -14.1 | -3.2 | 80% | 31% | +8.8 | +20.7 | -0.8 | yes |
| underworld.pit | cold_fusion_interface | 22.1 (1) | 22.1 (1) | 5.5 (2) | 22.1 | -14.7 | -2.2 | 81% | 28% | +6.9 | +20.9 | -1.4 | yes |
| underworld.exit | cold_fusion_interface | 22.1 (1) | 22.1 (1) | 5.5 (2) | 22.1 | -14.7 | -3.0 | 80% | 33% | +7.6 | +22.3 | -0.9 | yes |
| hospital | lv4_hospital | 22.1 (1) | 16.6 (2) | 16.6 (2) | 16.6 | -13.5 | -3.5 | 96% | 19% | +12.2 | +18.9 | -0.8 |  |
| hospital.corridor | lv4_hospital | 22.1 (1) | 22.1 (1) | 16.6 (2) | 22.1 | -13.0 | -2.3 | 94% | 25% | +11.1 | +18.7 | -1.1 | yes |
| hospital.dayroom | lv4_hospital | 22.1 (1) | 22.1 (1) | 11.0 (2) | 22.1 | -12.6 | -2.3 | 93% | 42% | +7.1 | +18.6 | -2.2 | yes |
| hospital.cafeteria | lv4_hospital | 22.1 (1) | 22.1 (1) | 16.6 (2) | 22.1 | -12.9 | -2.2 | 95% | 34% | +9.7 | +18.5 | -1.3 | yes |
| hospital.garden | lv4_hospital | 22.1 (1) | 22.1 (1) | 16.6 (2) | 22.1 | -12.9 | -3.5 | 95% | 25% | +10.5 | +19.0 | -1.1 | yes |
| hospital.exit | lv4_hospital | 22.1 (1) | 22.1 (1) | 16.6 (2) | 22.1 | -12.5 | -2.2 | 95% | 33% | +8.8 | +18.8 | -1.4 | yes |
| ward | lv5_asylum | 22.1 (1) | 16.6 (2) | 5.5 (2) | 16.6 | -16.7 | -3.6 | 81% | 45% | +5.7 | +21.1 | -0.8 |  |
| ward.art | lv5_asylum | 22.1 (1) | 22.1 (1) | 11.0 (2) | 16.6 | -17.1 | -4.2 | 85% | 35% | +4.9 | +18.5 | -1.2 | yes |
| ward.dorm | lv5_asylum | 22.1 (1) | 22.1 (1) | 5.5 (3) | 16.6 | -17.1 | -4.3 | 81% | 38% | +9.4 | +20.7 | -0.8 | yes |
| ward.corridor | lv5_asylum | 22.1 (1) | 22.1 (1) | 5.5 (3) | 16.6 | -17.2 | -4.3 | 81% | 38% | +9.4 | +20.7 | -0.8 | yes |
| ward.courtyard | lv5_asylum | 22.1 (1) | 22.1 (1) | 0.0 (-) | 16.6 | -16.3 | -1.3 | 83% | 48% | +6.0 | +23.1 | -0.8 | yes |
| ward.exit | lv5_asylum | 22.1 (1) | 22.1 (1) | 11.0 (2) | 22.1 | -17.3 | -1.1 | 84% | 27% | +10.0 | +18.5 | -0.9 | yes |
| hospital_late | lv4_hospital | 22.1 (1) | 22.1 (1) | 16.6 (2) | 22.1 | -13.2 | -3.5 | 96% | 19% | +12.2 | +18.9 | -0.8 | yes |
| hospital_late.cafe | lv4_hospital | 22.1 (1) | 22.1 (1) | 11.0 (2) | 22.1 | -13.0 | -1.5 | 94% | 20% | +9.5 | +18.9 | -1.2 | yes |
| hospital_late.quiet | lv4_hospital | 22.1 (1) | 22.1 (1) | 16.6 (2) | 22.1 | -12.9 | -2.3 | 95% | 34% | +11.4 | +18.5 | -1.0 | yes |
| hospital_late.exit | lv4_hospital | 22.1 (1) | 22.1 (1) | 16.6 (2) | 22.1 | -12.7 | -2.2 | 94% | 34% | +9.2 | +18.5 | -1.4 | yes |
| ward_late | lv5_asylum | 22.1 (1) | 22.1 (1) | 5.5 (2) | 22.1 | -16.5 | -3.6 | 81% | 45% | +5.7 | +21.1 | -0.8 | yes |
| ward_late.treat | lv5_asylum | 22.1 (1) | 22.1 (1) | 16.6 (2) | 16.6 | -17.1 | -3.7 | 84% | 44% | +7.2 | +17.8 | -1.4 | yes |
| ward_late.dorm | lv5_asylum | 22.1 (1) | 22.1 (1) | 11.0 (2) | 16.6 | -17.1 | -2.8 | 86% | 47% | +3.4 | +17.7 | -1.8 | yes |
| ward_late.exit | lv5_asylum | 22.1 (1) | 22.1 (1) | 11.0 (2) | 16.6 | -17.5 | -3.3 | 85% | 40% | +8.9 | +18.9 | -1.1 | yes |

Mean over the 36 scenes: bass band 87.9%, sub 36.6%, bass-drums +9.3 dB, phone bass -1.3 dB, bass audible 21.3 s and leading 20.2 s of 22.1 s, LUFS -14.8, worst peak -1.1 dBFS.

## gospel (124 BPM)

Dwell: phase 31.0 s (4 blocks of 7.74 s); 17 scenes; default route 12 phases; phases per music family along it [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], per world [3, 2, 2, 5]; 1-1 arrangement sections per phase (shortest 31.0 s); up to 3 mix/arrangement changes per phase; stage bass gains [0.0, 1.0, 0.85, 1.0]; recipe bass floor 0.9; bass in 23.2 s then out 7.7 s at every scene change (carried at 0.5 within a family); 0 hotspots dip the music to 0.55 (-5.2 dB) for 6 beats (2.9 s); phase fade 0.6 s; run level -3 dB.

| scene | family | drums s (in) | bass s (in) | synth s (in) | bass leads s | LUFS | peak dBFS | bass band 30-250 | sub 30-80 | bass-drums dB | bass-synth dB | phone bass dB | carry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| jordan | gospel_bethlehem | 31.0 (1) | 23.2 (2) | 0.0 (-) | 23.2 | -14.4 | -0.9 | 90% | 54% | +11.8 | +23.1 | -0.2 |  |
| jordan.baptism | gospel_baptism | 31.0 (1) | 23.2 (2) | 0.0 (-) | 23.2 | -14.1 | -1.9 | 89% | 52% | +12.0 | +23.3 | -0.1 |  |
| jordan.wilderness | gospel_wilderness | 31.0 (1) | 23.2 (2) | 0.0 (-) | 23.2 | -13.7 | -1.7 | 87% | 49% | +12.1 | +23.5 | -0.2 |  |
| jordan.nazareth | gospel_nazareth | 31.0 (1) | 23.2 (2) | 0.0 (-) | 23.2 | -14.4 | -1.6 | 90% | 54% | +11.8 | +23.1 | -0.2 |  |
| galilee | gospel_lakeshore | 31.0 (1) | 23.2 (2) | 0.0 (-) | 23.2 | -14.1 | -1.5 | 89% | 52% | +12.0 | +23.3 | -0.2 |  |
| galilee.capernaum | gospel_capernaum | 31.0 (1) | 23.2 (2) | 0.0 (-) | 23.2 | -13.7 | -0.8 | 87% | 49% | +12.1 | +23.5 | -0.2 |  |
| galilee.mount | gospel_mount | 31.0 (1) | 23.2 (2) | 0.0 (-) | 23.2 | -14.4 | -1.7 | 90% | 54% | +11.8 | +23.1 | -0.2 |  |
| galilee.storm | gospel_storm | 31.0 (1) | 23.2 (2) | 0.0 (-) | 23.2 | -14.1 | -1.0 | 89% | 52% | +12.0 | +23.3 | -0.2 |  |
| road | gospel_bethany | 31.0 (1) | 23.2 (2) | 0.0 (-) | 23.2 | -13.7 | -1.2 | 87% | 49% | +12.1 | +23.5 | -0.2 |  |
| road.loaves | gospel_loaves | 31.0 (1) | 23.2 (2) | 0.0 (-) | 23.2 | -14.4 | -1.5 | 90% | 54% | +11.8 | +23.1 | -0.2 |  |
| road.entry | gospel_entry | 31.0 (1) | 23.2 (2) | 0.0 (-) | 23.2 | -14.1 | -1.6 | 89% | 52% | +12.0 | +23.3 | -0.2 |  |
| jerusalem | gospel_temple | 31.0 (1) | 23.2 (2) | 0.0 (-) | 23.2 | -13.7 | -1.6 | 87% | 49% | +12.1 | +23.5 | -0.2 |  |
| jerusalem.gethsemane | gospel_gethsemane | 31.0 (1) | 23.2 (2) | 0.0 (-) | 23.2 | -14.4 | -1.2 | 90% | 54% | +11.8 | +23.1 | -0.2 |  |
| jerusalem.trial | gospel_trial | 31.0 (1) | 23.2 (2) | 0.0 (-) | 23.2 | -14.1 | -1.5 | 89% | 52% | +12.0 | +23.3 | -0.2 |  |
| jerusalem.golgotha | gospel_golgotha | 31.0 (1) | 23.2 (2) | 0.0 (-) | 23.2 | -13.7 | -1.6 | 87% | 49% | +12.1 | +23.5 | -0.2 |  |
| jerusalem.tomb | gospel_tomb | 31.0 (1) | 23.2 (2) | 0.0 (-) | 23.2 | -14.4 | -1.6 | 90% | 54% | +11.8 | +23.1 | -0.2 |  |
| jerusalem.road | gospel_road_beyond | 31.0 (1) | 23.2 (2) | 0.0 (-) | 23.2 | -14.1 | -1.4 | 89% | 52% | +12.0 | +23.3 | -0.2 |  |

Mean over the 17 scenes: bass band 88.8%, sub 51.9%, bass-drums +12.0 dB, phone bass -0.2 dB, bass audible 23.2 s and leading 23.2 s of 31.0 s, LUFS -14.1, worst peak -0.8 dBFS.

## squadron (140 BPM)

Dwell: phase 27.4 s (4 blocks of 6.86 s); 14 scenes; default route 12 phases; phases per music family along it [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], per world [2, 1, 3, 3, 1, 1, 1]; 1-1 arrangement sections per phase (shortest 27.4 s); up to 3 mix/arrangement changes per phase; stage bass gains [0.0, 1.0, 0.9, 1.0]; recipe bass floor 0.9; bass in 20.6 s then out 6.9 s at every scene change (carried at 0.5 within a family); 0 hotspots dip the music to 0.55 (-5.2 dB) for 6 beats (2.6 s); phase fade 0.6 s; run level -1.5 dB.

| scene | family | drums s (in) | bass s (in) | synth s (in) | bass leads s | LUFS | peak dBFS | bass band 30-250 | sub 30-80 | bass-drums dB | bass-synth dB | phone bass dB | carry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base | squadron_c01 | 27.4 (1) | 20.6 (2) | 0.0 (-) | 20.6 | -11.7 | -3.5 | 83% | 33% | +13.4 | +22.7 | -0.6 |  |
| base.c02 | squadron_c02 | 27.4 (1) | 20.6 (2) | 0.0 (-) | 20.6 | -13.6 | -3.4 | 70% | 35% | +14.2 | +22.7 | -0.8 |  |
| base.c03 | squadron_c03 | 27.4 (1) | 20.6 (2) | 13.7 (3) | 20.6 | -16.2 | -2.7 | 87% | 18% | +14.0 | +17.5 | -0.6 |  |
| air | squadron_c04 | 27.4 (1) | 20.6 (2) | 0.0 (-) | 20.6 | -12.7 | -1.5 | 86% | 33% | +13.8 | +22.9 | -0.7 |  |
| air.c05 | squadron_c05 | 27.4 (1) | 20.6 (2) | 0.0 (-) | 20.6 | -15.7 | -3.1 | 85% | 42% | +9.1 | +22.6 | -1.2 |  |
| air.c06 | squadron_c06 | 27.4 (1) | 20.6 (2) | 6.9 (4) | 20.6 | -16.0 | -0.9 | 84% | 32% | +10.4 | +20.9 | -1.3 |  |
| city | squadron_c07 | 13.7 (1) | 20.6 (2) | 0.0 (-) | 20.6 | -12.0 | -2.6 | 91% | 69% | +19.9 | +23.9 | -0.5 |  |
| city.c08 | squadron_c08 | 27.4 (1) | 20.6 (2) | 0.0 (-) | 20.6 | -10.4 | -2.9 | 93% | 51% | +16.7 | +28.8 | -0.2 |  |
| city.c09 | squadron_c09 | 27.4 (1) | 20.6 (2) | 6.9 (4) | 20.6 | -14.3 | -3.5 | 90% | 32% | +9.3 | +21.7 | -0.5 |  |
| city.c10 | squadron_c10 | 13.7 (1) | 20.6 (2) | 0.0 (-) | 20.6 | -10.9 | -2.9 | 89% | 51% | +19.8 | +24.5 | -0.4 |  |
| escape | squadron_c11 | 27.4 (1) | 20.6 (2) | 6.9 (4) | 20.6 | -11.5 | -3.7 | 92% | 17% | +15.9 | +22.6 | -0.3 |  |
| escape.c12 | squadron_c12 | 27.4 (1) | 20.6 (2) | 0.0 (-) | 20.6 | -12.5 | -2.0 | 87% | 47% | +11.8 | +23.3 | -0.3 |  |
| escape.c13 | squadron_c13 | 13.7 (1) | 20.6 (2) | 0.0 (-) | 20.6 | -10.6 | -2.6 | 93% | 36% | +20.5 | +25.5 | -0.2 |  |
| escape.c14 | squadron_c14 | 27.4 (1) | 20.6 (2) | 0.0 (-) | 20.6 | -12.9 | -2.8 | 94% | 42% | +13.4 | +23.0 | -0.6 |  |

Mean over the 14 scenes: bass band 87.4%, sub 38.4%, bass-drums +14.4 dB, phone bass -0.6 dB, bass audible 20.6 s and leading 20.6 s of 27.4 s, LUFS -12.9, worst peak -0.9 dBFS.

## ember (145 BPM)

Dwell: phase 26.5 s (4 blocks of 6.62 s); 15 scenes; default route 13 phases; phases per music family along it [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], per world [3, 2, 2, 4, 2]; 1-1 arrangement sections per phase (shortest 26.5 s); up to 3 mix/arrangement changes per phase; stage bass gains [0.0, 1.0, 0.85, 1.0]; recipe bass floor 0.9; bass in 19.9 s then out 6.6 s at every scene change (carried at 0.5 within a family); 0 hotspots dip the music to 0.55 (-5.2 dB) for 6 beats (2.5 s); phase fade 0.6 s; run level -2 dB.

| scene | family | drums s (in) | bass s (in) | synth s (in) | bass leads s | LUFS | peak dBFS | bass band 30-250 | sub 30-80 | bass-drums dB | bass-synth dB | phone bass dB | carry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hollow | ember_e00_orchard | 26.5 (1) | 19.9 (2) | 0.0 (-) | 19.9 | -13.5 | -1.6 | 90% | 48% | +13.0 | +23.3 | -0.1 |  |
| hollow.ford | ember_e01_ford | 26.5 (1) | 19.9 (2) | 0.0 (-) | 19.9 | -13.1 | -1.5 | 90% | 43% | +13.4 | +23.7 | -0.1 |  |
| hollow.inn | ember_e02_inn | 26.5 (1) | 19.9 (2) | 0.0 (-) | 19.9 | -12.7 | -1.9 | 89% | 41% | +13.6 | +23.9 | -0.2 |  |
| north | ember_e03_birch_hall | 26.5 (1) | 19.9 (2) | 0.0 (-) | 19.9 | -13.5 | -1.7 | 90% | 48% | +13.0 | +23.3 | -0.1 |  |
| north.pass | ember_e04_high_pass | 26.5 (1) | 19.9 (2) | 0.0 (-) | 19.9 | -13.1 | -1.8 | 90% | 43% | +13.4 | +23.7 | -0.1 |  |
| deeps | ember_e05_deep_halls | 26.5 (1) | 19.9 (2) | 0.0 (-) | 19.9 | -12.7 | -1.6 | 89% | 41% | +13.6 | +23.9 | -0.2 |  |
| deeps.falls | ember_e06_falls | 26.5 (1) | 19.9 (2) | 0.0 (-) | 19.9 | -13.5 | -2.0 | 90% | 48% | +13.0 | +23.3 | -0.1 |  |
| marsh | ember_e07_reed_marsh | 26.5 (1) | 19.9 (2) | 0.0 (-) | 19.9 | -13.1 | -1.7 | 90% | 43% | +13.4 | +23.7 | -0.1 |  |
| marsh.wall | ember_e08_black_wall | 26.5 (1) | 19.9 (2) | 0.0 (-) | 19.9 | -12.7 | -2.0 | 89% | 41% | +13.6 | +23.9 | -0.2 |  |
| marsh.stair | ember_e09_stair_of_bells | 26.5 (1) | 19.9 (2) | 0.0 (-) | 19.9 | -13.5 | -1.5 | 90% | 48% | +13.0 | +23.3 | -0.1 |  |
| marsh.plain | ember_e10_ash_plain | 26.5 (1) | 19.9 (2) | 0.0 (-) | 19.9 | -13.1 | -1.8 | 90% | 43% | +13.4 | +23.7 | -0.1 |  |
| mountain | ember_e11_throat | 26.5 (1) | 19.9 (2) | 0.0 (-) | 19.9 | -12.7 | -1.8 | 89% | 41% | +13.6 | +23.9 | -0.2 |  |
| mountain.spring | ember_e12_drowned_spring | 26.5 (1) | 19.9 (2) | 0.0 (-) | 19.9 | -13.5 | -2.4 | 90% | 48% | +13.0 | +23.3 | -0.1 |  |
| mountain.keeper | ember_e13_keeper | 26.5 (1) | 19.9 (2) | 0.0 (-) | 19.9 | -13.1 | -1.3 | 90% | 43% | +13.4 | +23.7 | -0.1 |  |
| mountain.taken | ember_e14_taken | 26.5 (1) | 19.9 (2) | 0.0 (-) | 19.9 | -12.7 | -2.0 | 89% | 41% | +13.6 | +23.9 | -0.2 |  |

Mean over the 15 scenes: bass band 89.7%, sub 44.3%, bass-drums +13.3 dB, phone bass -0.1 dB, bass audible 19.9 s and leading 19.9 s of 26.5 s, LUFS -13.1, worst peak -1.3 dBFS.

