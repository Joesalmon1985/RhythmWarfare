# Mix measurement, one lap per scene

Written by `python tools/run/measure_mix.py` (offline render from the packs, perfect play, block b = mix stage b, the bass revealed at beat 16; see the script's docstring).
Voice seconds are per 64-beat phase; `in` = the block (1-4) the voice is first audible; peak is before the run's limiter.

## gospel (124 BPM)

Dwell: phase 31.0 s (4 blocks of 7.74 s), laps per scene [1]: a scene lasts 31.0-31.0 s (mean 31.0 s) and the default route 372 s; 17 scenes; default route 12 phases; phases per music family along it [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], per world [3, 2, 2, 5]; 1-1 arrangement sections per phase (shortest 31.0 s); up to 3 mix/arrangement changes per phase; stage bass gains [0.0, 1.0, 0.85, 1.0]; recipe bass floor 0.9; bass in 23.2 s then out 7.7 s at every scene change (carried at 0.5 within a family); 0 hotspots dip the music to 0.55 (-5.2 dB) for 6 beats (2.9 s); phase fade 0.6 s; run level -3 dB.

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

Mean over the 17 scenes: bass band 88.8%, sub 51.9%, bass-drums +12.0 dB, phone bass -0.2 dB, bass audible 23.2 s and leading 23.2 s of 31.0 s in a scene, LUFS -14.1, worst peak -0.8 dBFS.

## squadron (140 BPM)

Dwell: phase 27.4 s (4 blocks of 6.86 s), laps per scene [1]: a scene lasts 27.4-27.4 s (mean 27.4 s) and the default route 329 s; 14 scenes; default route 12 phases; phases per music family along it [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], per world [2, 1, 3, 3, 1, 1, 1]; 1-1 arrangement sections per phase (shortest 27.4 s); up to 3 mix/arrangement changes per phase; stage bass gains [0.0, 1.0, 0.9, 1.0]; recipe bass floor 0.9; bass in 20.6 s then out 6.9 s at every scene change (carried at 0.5 within a family); 0 hotspots dip the music to 0.55 (-5.2 dB) for 6 beats (2.6 s); phase fade 0.6 s; run level -1.5 dB.

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

Mean over the 14 scenes: bass band 87.4%, sub 38.4%, bass-drums +14.4 dB, phone bass -0.6 dB, bass audible 20.6 s and leading 20.6 s of 27.4 s in a scene, LUFS -12.9, worst peak -0.9 dBFS.

## ember (145 BPM)

Dwell: phase 26.5 s (4 blocks of 6.62 s), laps per scene [1]: a scene lasts 26.5-26.5 s (mean 26.5 s) and the default route 344 s; 15 scenes; default route 13 phases; phases per music family along it [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], per world [3, 2, 2, 4, 2]; 1-1 arrangement sections per phase (shortest 26.5 s); up to 3 mix/arrangement changes per phase; stage bass gains [0.0, 1.0, 0.85, 1.0]; recipe bass floor 0.9; bass in 19.9 s then out 6.6 s at every scene change (carried at 0.5 within a family); 0 hotspots dip the music to 0.55 (-5.2 dB) for 6 beats (2.5 s); phase fade 0.6 s; run level -2 dB.

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

Mean over the 15 scenes: bass band 89.7%, sub 44.3%, bass-drums +13.3 dB, phone bass -0.1 dB, bass audible 19.9 s and leading 19.9 s of 26.5 s in a scene, LUFS -13.1, worst peak -1.3 dBFS.

