# Mix before the audio polish (origin/main 710a96a5)

Written by `python tools/run/measure_mix.py` (offline render from the packs, perfect play, block b = mix stage b, the bass revealed at beat 16; see the script's docstring).
Voice seconds are per 64-beat phase; `in` = the block (1-4) the voice is first audible; peak is before the run's limiter.

## main (174 BPM)

Dwell: phase 22.1 s (4 blocks of 5.52 s); 36 scenes; default route 16 phases; phases per music family along it [4, 4, 8], per world [4, 4, 5, 3]; 1-2 arrangement sections per phase (shortest 11.0 s); up to 4 mix/arrangement changes per phase; stage bass gains [0.0, 1.0, 0.5, 1.0]; recipe bass floor 0; bass in 16.6 s then out 5.5 s at every scene change (carried at 0 within a family); 24 hotspots dip the music to 0.35 (-9.1 dB) for 8 beats (2.8 s); phase fade 0.6 s; run level +0 dB.

| scene | family | drums s (in) | bass s (in) | synth s (in) | bass leads s | LUFS | peak dBFS | bass band 30-250 | sub 30-80 | bass-drums dB | bass-synth dB | phone bass dB | carry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| warehouse | lv1_warehouse | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -21.5 | -6.6 | 78% | 42% | +1.7 | +11.7 | -4.5 |  |
| warehouse.bar | lv1_warehouse | 22.1 (1) | 16.6 (2) | 16.6 (2) | 16.6 | -21.4 | -7.6 | 82% | 46% | +7.7 | +12.1 | -2.7 |  |
| warehouse.balcony | lv1_warehouse | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -20.8 | -7.9 | 90% | 53% | +5.6 | +13.5 | -4.6 |  |
| warehouse.chill | lv1_warehouse | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -20.9 | -7.1 | 86% | 42% | +4.1 | +12.7 | -3.5 |  |
| warehouse.booth | lv1_warehouse | 22.1 (1) | 16.6 (2) | 16.6 (2) | 16.6 | -21.2 | -7.6 | 87% | 43% | +7.4 | +12.3 | -2.5 |  |
| warehouse.exit | lv1_warehouse | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -21.0 | -6.9 | 85% | 42% | +2.8 | +14.0 | -3.6 |  |
| mothership | lv2_alien_spaceship | 22.1 (1) | 16.6 (2) | 16.6 (2) | 16.6 | -20.9 | -6.5 | 76% | 49% | +6.2 | +12.6 | -4.9 |  |
| mothership.gallery | lv2_alien_spaceship | 22.1 (1) | 16.6 (2) | 16.6 (2) | 16.6 | -20.2 | -8.4 | 83% | 38% | +8.3 | +14.1 | -2.7 |  |
| mothership.reactor | lv2_alien_spaceship | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -18.8 | -7.5 | 82% | 29% | +6.7 | +15.7 | -2.2 |  |
| mothership.bridge | lv2_alien_spaceship | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -19.6 | -7.5 | 83% | 39% | +6.6 | +14.8 | -2.6 |  |
| mothership.exit | lv2_alien_spaceship | 22.1 (1) | 16.6 (2) | 11.0 (2) | 11.0 | -21.0 | -5.4 | 79% | 46% | +2.6 | +15.6 | -6.5 |  |
| underworld | cold_fusion_interface | 22.1 (1) | 16.6 (2) | 11.0 (3) | 11.0 | -20.6 | -6.8 | 72% | 31% | +3.9 | +15.7 | -1.8 |  |
| underworld.court | cold_fusion_interface | 22.1 (1) | 16.6 (2) | 11.0 (3) | 11.0 | -20.3 | -7.1 | 77% | 32% | +4.8 | +16.5 | -1.7 |  |
| underworld.furnace | cold_fusion_interface | 22.1 (1) | 16.6 (2) | 11.0 (3) | 11.0 | -19.9 | -7.2 | 70% | 30% | +3.9 | +15.1 | -1.9 |  |
| underworld.pit | cold_fusion_interface | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -20.2 | -2.8 | 70% | 28% | +2.0 | +15.3 | -2.9 |  |
| underworld.exit | cold_fusion_interface | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -20.8 | -2.8 | 76% | 35% | +0.9 | +15.0 | -2.4 |  |
| hospital | lv4_hospital | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -20.9 | -8.2 | 89% | 26% | +5.3 | +11.5 | -3.1 |  |
| hospital.corridor | lv4_hospital | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -19.3 | -7.4 | 88% | 34% | +5.4 | +12.4 | -3.3 |  |
| hospital.dayroom | lv4_hospital | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -17.8 | -6.0 | 89% | 42% | +2.5 | +13.4 | -4.5 |  |
| hospital.cafeteria | lv4_hospital | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -19.3 | -6.3 | 90% | 36% | +4.3 | +12.4 | -3.4 |  |
| hospital.garden | lv4_hospital | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -18.9 | -7.2 | 89% | 33% | +4.8 | +12.7 | -3.3 |  |
| hospital.exit | lv4_hospital | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -17.9 | -6.3 | 91% | 36% | +4.2 | +13.4 | -3.3 |  |
| ward | lv5_asylum | 22.1 (1) | 16.6 (2) | 5.5 (2) | 11.0 | -22.6 | -6.2 | 80% | 49% | +0.6 | +15.6 | -1.5 |  |
| ward.art | lv5_asylum | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -22.0 | -6.7 | 83% | 43% | +0.2 | +13.2 | -2.4 |  |
| ward.dorm | lv5_asylum | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -22.6 | -6.3 | 79% | 42% | +4.7 | +15.3 | -1.5 |  |
| ward.corridor | lv5_asylum | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -22.6 | -6.3 | 79% | 42% | +4.7 | +15.3 | -1.5 |  |
| ward.courtyard | lv5_asylum | 22.1 (1) | 16.6 (2) | 11.0 (2) | 11.0 | -21.9 | -5.4 | 85% | 60% | +0.7 | +17.0 | -1.8 |  |
| ward.exit | lv5_asylum | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -23.3 | -6.9 | 80% | 30% | +5.3 | +13.2 | -1.6 |  |
| hospital_late | lv4_hospital | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -20.9 | -8.2 | 89% | 26% | +5.3 | +11.5 | -3.1 |  |
| hospital_late.cafe | lv4_hospital | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -19.4 | -5.2 | 88% | 25% | +3.9 | +12.7 | -3.3 |  |
| hospital_late.quiet | lv4_hospital | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -19.2 | -7.4 | 91% | 38% | +5.7 | +12.1 | -3.1 |  |
| hospital_late.exit | lv4_hospital | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -18.2 | -6.3 | 90% | 37% | +4.6 | +13.2 | -3.3 |  |
| ward_late | lv5_asylum | 22.1 (1) | 16.6 (2) | 5.5 (2) | 11.0 | -22.6 | -6.2 | 80% | 49% | +0.6 | +15.6 | -1.5 |  |
| ward_late.treat | lv5_asylum | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -22.3 | -6.8 | 79% | 50% | +2.1 | +11.9 | -3.0 |  |
| ward_late.dorm | lv5_asylum | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -22.3 | -6.6 | 86% | 61% | -3.4 | +10.2 | -4.6 |  |
| ward_late.exit | lv5_asylum | 22.1 (1) | 16.6 (2) | 16.6 (2) | 11.0 | -22.7 | -6.9 | 82% | 42% | +4.1 | +13.6 | -1.9 |  |

Mean over the 36 scenes: bass band 82.9%, sub 39.6%, bass-drums +3.9 dB, phone bass -2.9 dB, bass audible 16.6 s and leading 11.6 s of 22.1 s, LUFS -20.7, worst peak -2.8 dBFS.

## gospel (124 BPM)

Dwell: phase 31.0 s (4 blocks of 7.74 s); 17 scenes; default route 12 phases; phases per music family along it [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], per world [3, 2, 2, 5]; 1-1 arrangement sections per phase (shortest 31.0 s); up to 3 mix/arrangement changes per phase; stage bass gains [0.0, 1.0, 0.5, 1.0]; recipe bass floor 0; bass in 23.2 s then out 7.7 s at every scene change (carried at 0 within a family); 0 hotspots dip the music to 0.35 (-9.1 dB) for 8 beats (3.9 s); phase fade 0.6 s; run level +0 dB.

| scene | family | drums s (in) | bass s (in) | synth s (in) | bass leads s | LUFS | peak dBFS | bass band 30-250 | sub 30-80 | bass-drums dB | bass-synth dB | phone bass dB | carry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| jordan | gospel_bethlehem | 31.0 (1) | 23.2 (2) | 7.7 (3) | 23.2 | -12.9 | 0.5 | 88% | 51% | +10.0 | +20.7 | -0.3 |  |
| jordan.baptism | gospel_baptism | 31.0 (1) | 23.2 (2) | 7.7 (3) | 23.2 | -12.7 | 0.6 | 87% | 49% | +10.0 | +20.7 | -0.2 |  |
| jordan.wilderness | gospel_wilderness | 31.0 (1) | 23.2 (2) | 7.7 (3) | 23.2 | -12.4 | 0.7 | 85% | 45% | +10.0 | +20.7 | -0.3 |  |
| jordan.nazareth | gospel_nazareth | 31.0 (1) | 23.2 (2) | 7.7 (3) | 23.2 | -12.9 | 0.3 | 88% | 51% | +10.0 | +20.7 | -0.3 |  |
| galilee | gospel_lakeshore | 31.0 (1) | 23.2 (2) | 7.7 (3) | 23.2 | -12.6 | 0.4 | 87% | 48% | +10.0 | +20.7 | -0.2 |  |
| galilee.capernaum | gospel_capernaum | 31.0 (1) | 23.2 (2) | 7.7 (3) | 23.2 | -12.4 | 1.0 | 85% | 45% | +10.0 | +20.7 | -0.3 |  |
| galilee.mount | gospel_mount | 31.0 (1) | 23.2 (2) | 7.7 (3) | 23.2 | -12.9 | 0.1 | 88% | 51% | +10.0 | +20.7 | -0.3 |  |
| galilee.storm | gospel_storm | 31.0 (1) | 23.2 (2) | 7.7 (3) | 23.2 | -12.6 | 0.7 | 87% | 48% | +10.0 | +20.7 | -0.2 |  |
| road | gospel_bethany | 31.0 (1) | 23.2 (2) | 7.7 (3) | 23.2 | -12.4 | 0.6 | 84% | 45% | +10.0 | +20.7 | -0.3 |  |
| road.loaves | gospel_loaves | 31.0 (1) | 23.2 (2) | 7.7 (3) | 23.2 | -12.9 | 0.2 | 88% | 51% | +10.0 | +20.7 | -0.3 |  |
| road.entry | gospel_entry | 31.0 (1) | 23.2 (2) | 7.7 (3) | 23.2 | -12.6 | 0.5 | 87% | 48% | +10.0 | +20.7 | -0.2 |  |
| jerusalem | gospel_temple | 31.0 (1) | 23.2 (2) | 7.7 (3) | 23.2 | -12.4 | 0.5 | 85% | 45% | +10.0 | +20.7 | -0.3 |  |
| jerusalem.gethsemane | gospel_gethsemane | 31.0 (1) | 23.2 (2) | 7.7 (3) | 23.2 | -12.9 | 0.3 | 88% | 51% | +10.0 | +20.7 | -0.3 |  |
| jerusalem.trial | gospel_trial | 31.0 (1) | 23.2 (2) | 7.7 (3) | 23.2 | -12.6 | 0.9 | 87% | 48% | +10.0 | +20.7 | -0.2 |  |
| jerusalem.golgotha | gospel_golgotha | 31.0 (1) | 23.2 (2) | 7.7 (3) | 23.2 | -12.4 | 0.8 | 84% | 45% | +10.0 | +20.7 | -0.3 |  |
| jerusalem.tomb | gospel_tomb | 31.0 (1) | 23.2 (2) | 7.7 (3) | 23.2 | -12.9 | 0.4 | 88% | 51% | +10.0 | +20.7 | -0.3 |  |
| jerusalem.road | gospel_road_beyond | 31.0 (1) | 23.2 (2) | 7.7 (3) | 23.2 | -12.6 | 1.0 | 87% | 48% | +10.0 | +20.7 | -0.2 |  |

Mean over the 17 scenes: bass band 86.4%, sub 48.1%, bass-drums +10.0 dB, phone bass -0.2 dB, bass audible 23.2 s and leading 23.2 s of 31.0 s, LUFS -12.6, worst peak 1.0 dBFS.

## squadron (140 BPM)

Dwell: phase 27.4 s (4 blocks of 6.86 s); 14 scenes; default route 12 phases; phases per music family along it [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], per world [2, 1, 3, 3, 1, 1, 1]; 1-1 arrangement sections per phase (shortest 27.4 s); up to 3 mix/arrangement changes per phase; stage bass gains [0.0, 1.0, 0.9, 1.0]; recipe bass floor 0; bass in 20.6 s then out 6.9 s at every scene change (carried at 0 within a family); 0 hotspots dip the music to 0.35 (-9.1 dB) for 8 beats (3.4 s); phase fade 0.6 s; run level +0 dB.

| scene | family | drums s (in) | bass s (in) | synth s (in) | bass leads s | LUFS | peak dBFS | bass band 30-250 | sub 30-80 | bass-drums dB | bass-synth dB | phone bass dB | carry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base | squadron_c01 | 27.4 (1) | 20.6 (2) | 6.9 (4) | 20.6 | -13.2 | -0.5 | 81% | 33% | +11.0 | +20.4 | -0.7 |  |
| base.c02 | squadron_c02 | 27.4 (1) | 20.6 (2) | 6.9 (4) | 20.6 | -14.3 | -0.5 | 68% | 35% | +11.9 | +20.3 | -1.0 |  |
| base.c03 | squadron_c03 | 27.4 (1) | 20.6 (2) | 13.7 (3) | 20.6 | -18.1 | -0.6 | 82% | 17% | +10.5 | +13.9 | -0.8 |  |
| air | squadron_c04 | 27.4 (1) | 20.6 (2) | 6.9 (4) | 20.6 | -13.6 | -0.5 | 84% | 33% | +11.2 | +20.4 | -0.9 |  |
| air.c05 | squadron_c05 | 27.4 (1) | 20.6 (2) | 13.7 (3) | 13.7 | -19.6 | -0.6 | 74% | 45% | -1.3 | +12.2 | -5.0 |  |
| air.c06 | squadron_c06 | 27.4 (1) | 20.6 (2) | 13.7 (3) | 13.7 | -20.1 | -0.5 | 75% | 33% | +1.8 | +12.3 | -4.0 |  |
| city | squadron_c07 | 20.6 (1) | 20.6 (2) | 6.9 (4) | 20.6 | -13.2 | -0.6 | 90% | 68% | +17.7 | +21.7 | -0.7 |  |
| city.c08 | squadron_c08 | 27.4 (1) | 20.6 (2) | 0.0 (-) | 20.6 | -10.5 | -0.5 | 92% | 51% | +15.3 | +27.4 | -0.2 |  |
| city.c09 | squadron_c09 | 27.4 (1) | 20.6 (2) | 13.7 (3) | 20.6 | -16.0 | -0.5 | 89% | 31% | +5.2 | +17.6 | -0.6 |  |
| city.c10 | squadron_c10 | 20.6 (1) | 20.6 (2) | 6.9 (4) | 20.6 | -11.4 | -0.6 | 86% | 47% | +17.6 | +22.3 | -0.4 |  |
| escape | squadron_c11 | 27.4 (1) | 20.6 (2) | 13.7 (3) | 20.6 | -13.1 | -0.5 | 94% | 10% | +13.3 | +20.0 | -0.3 |  |
| escape.c12 | squadron_c12 | 27.4 (1) | 20.6 (2) | 6.9 (4) | 20.6 | -13.4 | -1.0 | 86% | 48% | +9.2 | +20.7 | -0.5 |  |
| escape.c13 | squadron_c13 | 13.7 (1) | 20.6 (2) | 0.0 (-) | 20.6 | -10.8 | -0.5 | 92% | 38% | +19.0 | +23.9 | -0.2 |  |
| escape.c14 | squadron_c14 | 27.4 (1) | 20.6 (2) | 6.9 (4) | 20.6 | -13.5 | -0.5 | 96% | 43% | +11.2 | +20.8 | -0.8 |  |

Mean over the 14 scenes: bass band 84.8%, sub 38.1%, bass-drums +11.0 dB, phone bass -1.2 dB, bass audible 20.6 s and leading 19.6 s of 27.4 s, LUFS -14.3, worst peak -0.5 dBFS.

## ember (145 BPM)

Dwell: phase 26.5 s (4 blocks of 6.62 s); 15 scenes; default route 13 phases; phases per music family along it [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], per world [3, 2, 2, 4, 2]; 1-1 arrangement sections per phase (shortest 26.5 s); up to 3 mix/arrangement changes per phase; stage bass gains [0.0, 1.0, 0.5, 1.0]; recipe bass floor 0; bass in 19.9 s then out 6.6 s at every scene change (carried at 0 within a family); 0 hotspots dip the music to 0.35 (-9.1 dB) for 8 beats (3.3 s); phase fade 0.6 s; run level +0 dB.

| scene | family | drums s (in) | bass s (in) | synth s (in) | bass leads s | LUFS | peak dBFS | bass band 30-250 | sub 30-80 | bass-drums dB | bass-synth dB | phone bass dB | carry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hollow | ember_e00_orchard | 26.5 (1) | 19.9 (2) | 6.6 (3) | 19.9 | -12.9 | -0.5 | 89% | 60% | +12.0 | +21.7 | -0.1 |  |
| hollow.ford | ember_e01_ford | 26.5 (1) | 19.9 (2) | 6.6 (3) | 19.9 | -12.6 | -0.5 | 89% | 51% | +12.0 | +21.7 | -0.1 |  |
| hollow.inn | ember_e02_inn | 26.5 (1) | 19.9 (2) | 6.6 (3) | 19.9 | -12.3 | -0.2 | 86% | 45% | +12.0 | +21.7 | -0.2 |  |
| north | ember_e03_birch_hall | 26.5 (1) | 19.9 (2) | 6.6 (3) | 19.9 | -12.9 | -0.1 | 89% | 59% | +12.0 | +21.7 | -0.1 |  |
| north.pass | ember_e04_high_pass | 26.5 (1) | 19.9 (2) | 6.6 (3) | 19.9 | -12.6 | -0.1 | 88% | 51% | +12.0 | +21.7 | -0.1 |  |
| deeps | ember_e05_deep_halls | 26.5 (1) | 19.9 (2) | 6.6 (3) | 19.9 | -12.3 | -0.5 | 86% | 45% | +12.0 | +21.7 | -0.2 |  |
| deeps.falls | ember_e06_falls | 26.5 (1) | 19.9 (2) | 6.6 (3) | 19.9 | -12.9 | -0.1 | 89% | 60% | +12.0 | +21.7 | -0.1 |  |
| marsh | ember_e07_reed_marsh | 26.5 (1) | 19.9 (2) | 6.6 (3) | 19.9 | -12.6 | -0.5 | 88% | 51% | +12.0 | +21.7 | -0.1 |  |
| marsh.wall | ember_e08_black_wall | 26.5 (1) | 19.9 (2) | 6.6 (3) | 19.9 | -12.3 | -0.3 | 86% | 45% | +12.0 | +21.7 | -0.2 |  |
| marsh.stair | ember_e09_stair_of_bells | 26.5 (1) | 19.9 (2) | 6.6 (3) | 19.9 | -12.9 | 0.0 | 89% | 59% | +12.0 | +21.7 | -0.1 |  |
| marsh.plain | ember_e10_ash_plain | 26.5 (1) | 19.9 (2) | 6.6 (3) | 19.9 | -12.6 | -0.2 | 88% | 51% | +12.0 | +21.7 | -0.1 |  |
| mountain | ember_e11_throat | 26.5 (1) | 19.9 (2) | 6.6 (3) | 19.9 | -12.3 | 0.2 | 86% | 45% | +12.0 | +21.7 | -0.2 |  |
| mountain.spring | ember_e12_drowned_spring | 26.5 (1) | 19.9 (2) | 6.6 (3) | 19.9 | -12.9 | -0.5 | 89% | 60% | +12.0 | +21.7 | -0.1 |  |
| mountain.keeper | ember_e13_keeper | 26.5 (1) | 19.9 (2) | 6.6 (3) | 19.9 | -12.6 | -0.3 | 89% | 51% | +12.0 | +21.7 | -0.1 |  |
| mountain.taken | ember_e14_taken | 26.5 (1) | 19.9 (2) | 6.6 (3) | 19.9 | -12.3 | 0.1 | 86% | 45% | +12.0 | +21.7 | -0.2 |  |

Mean over the 15 scenes: bass band 88.1%, sub 51.9%, bass-drums +12.0 dB, phone bass -0.2 dB, bass audible 19.9 s and leading 19.9 s of 26.5 s, LUFS -12.6, worst peak 0.2 dBFS.

