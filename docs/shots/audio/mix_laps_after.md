# Mix measurement, two laps per path scene

Written by `python tools/run/measure_mix.py` (offline render from the packs, perfect play, block b = mix stage b, the bass revealed at beat 16; see the script's docstring).
Voice seconds are per 64-beat phase; `in` = the block (1-4) the voice is first audible; peak is before the run's limiter.

## Before and after

Means over each run's scenes (bass seconds include a carried bass in block 0); worst peak = the loudest scene, before any limiter (the run has none).

| run | bass band 30-250 | sub 30-80 | bass-drums dB | phone bass dB | bass audible s / phase | bass leads s / phase | scenes with a carry | LUFS | worst peak dBFS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gospel | 88.8% -> 89.3% | 51.9% -> 52.4% | +12.0 -> +13.9 | -0.2 -> -0.2 | 23.2 of 31.0 -> 50.6 of 58.3 | 23.2 -> 50.6 | 0 -> 0 of 17 | -14.1 -> -13.6 | -0.8 -> -0.8 |
| squadron | 87.4% -> 87.4% | 38.4% -> 37.9% | +14.4 -> +16.0 | -0.6 -> -0.6 | 20.6 of 27.4 -> 48.0 of 54.9 | 20.6 -> 48.0 | 0 -> 0 of 14 | -12.9 -> -12.6 | -0.9 -> -0.9 |
| ember | 89.7% -> 90.1% | 44.3% -> 44.6% | +13.3 -> +15.4 | -0.1 -> -0.1 | 19.9 of 26.5 -> 44.6 of 51.2 | 19.9 -> 44.6 | 0 -> 0 of 15 | -13.1 -> -12.6 | -1.3 -> -1.3 |

## gospel (124 BPM)

Dwell: phase 31.0 s (4 blocks of 7.74 s), laps per scene [1, 2]: a scene lasts 31.0-61.9 s (mean 56.8 s) and the default route 681 s; 17 scenes; default route 12 phases; phases per music family along it [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], per world [3, 2, 2, 5]; 1-1 arrangement sections per phase (shortest 31.0 s); up to 3 mix/arrangement changes per phase; stage bass gains [0.0, 1.0, 0.85, 1.0]; recipe bass floor 0.9; bass in 23.2 s then out 7.7 s at every scene change (carried at 0.5 within a family); 0 hotspots dip the music to 0.55 (-5.2 dB) for 6 beats (2.9 s); phase fade 0.6 s; run level -3 dB.

| scene | family | drums s (in) | bass s (in) | synth s (in) | bass leads s | LUFS | peak dBFS | bass band 30-250 | sub 30-80 | bass-drums dB | bass-synth dB | phone bass dB | carry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| jordan | gospel_bethlehem | 31.0 (1) | 23.2 (2) | 0.0 (-) | 23.2 | -14.4 | -0.9 | 90% | 54% | +11.8 | +23.1 | -0.2 |  |
| jordan.baptism | gospel_baptism | 61.9 (1) | 54.2 (2) | 0.0 (-) | 54.2 | -13.6 | -1.9 | 90% | 52% | +14.2 | +23.2 | -0.1 |  |
| jordan.wilderness | gospel_wilderness | 61.9 (1) | 54.2 (2) | 0.0 (-) | 54.2 | -13.2 | -1.7 | 88% | 50% | +14.4 | +23.3 | -0.2 |  |
| jordan.nazareth | gospel_nazareth | 61.9 (1) | 54.2 (2) | 0.0 (-) | 54.2 | -13.9 | -1.6 | 90% | 55% | +14.1 | +23.0 | -0.2 |  |
| galilee | gospel_lakeshore | 61.9 (1) | 54.2 (2) | 0.0 (-) | 54.2 | -13.6 | -1.5 | 90% | 52% | +14.2 | +23.2 | -0.1 |  |
| galilee.capernaum | gospel_capernaum | 61.9 (1) | 54.2 (2) | 0.0 (-) | 54.2 | -13.2 | -0.8 | 88% | 50% | +14.4 | +23.3 | -0.2 |  |
| galilee.mount | gospel_mount | 61.9 (1) | 54.2 (2) | 0.0 (-) | 54.2 | -13.9 | -1.7 | 90% | 55% | +14.1 | +23.0 | -0.2 |  |
| galilee.storm | gospel_storm | 61.9 (1) | 54.2 (2) | 0.0 (-) | 54.2 | -13.6 | -1.0 | 90% | 52% | +14.2 | +23.2 | -0.1 |  |
| road | gospel_bethany | 61.9 (1) | 54.2 (2) | 0.0 (-) | 54.2 | -13.2 | -1.2 | 88% | 50% | +14.4 | +23.3 | -0.2 |  |
| road.loaves | gospel_loaves | 61.9 (1) | 54.2 (2) | 0.0 (-) | 54.2 | -13.9 | -1.5 | 90% | 55% | +14.1 | +23.0 | -0.2 |  |
| road.entry | gospel_entry | 61.9 (1) | 54.2 (2) | 0.0 (-) | 54.2 | -13.6 | -1.6 | 90% | 52% | +14.2 | +23.2 | -0.1 |  |
| jerusalem | gospel_temple | 61.9 (1) | 54.2 (2) | 0.0 (-) | 54.2 | -13.2 | -1.6 | 88% | 50% | +14.4 | +23.3 | -0.2 |  |
| jerusalem.gethsemane | gospel_gethsemane | 61.9 (1) | 54.2 (2) | 0.0 (-) | 54.2 | -13.9 | -1.2 | 90% | 55% | +14.1 | +23.0 | -0.2 |  |
| jerusalem.trial | gospel_trial | 61.9 (1) | 54.2 (2) | 0.0 (-) | 54.2 | -13.6 | -1.5 | 90% | 52% | +14.2 | +23.2 | -0.1 |  |
| jerusalem.golgotha | gospel_golgotha | 31.0 (1) | 23.2 (2) | 0.0 (-) | 23.2 | -13.7 | -1.6 | 87% | 49% | +12.1 | +23.5 | -0.2 |  |
| jerusalem.tomb | gospel_tomb | 61.9 (1) | 54.2 (2) | 0.0 (-) | 54.2 | -13.9 | -1.6 | 90% | 55% | +14.1 | +23.0 | -0.2 |  |
| jerusalem.road | gospel_road_beyond | 61.9 (1) | 54.2 (2) | 0.0 (-) | 54.2 | -13.6 | -1.4 | 90% | 52% | +14.2 | +23.2 | -0.1 |  |

Mean over the 17 scenes: bass band 89.3%, sub 52.4%, bass-drums +13.9 dB, phone bass -0.2 dB, bass audible 50.6 s and leading 50.6 s of 58.3 s in a scene, LUFS -13.6, worst peak -0.8 dBFS.

## squadron (140 BPM)

Dwell: phase 27.4 s (4 blocks of 6.86 s), laps per scene [2]: a scene lasts 54.9-54.9 s (mean 54.9 s) and the default route 658 s; 14 scenes; default route 12 phases; phases per music family along it [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], per world [2, 1, 3, 3, 1, 1, 1]; 1-1 arrangement sections per phase (shortest 27.4 s); up to 3 mix/arrangement changes per phase; stage bass gains [0.0, 1.0, 0.9, 1.0]; recipe bass floor 0.9; bass in 20.6 s then out 6.9 s at every scene change (carried at 0.5 within a family); 0 hotspots dip the music to 0.55 (-5.2 dB) for 6 beats (2.6 s); phase fade 0.6 s; run level -1.5 dB.

| scene | family | drums s (in) | bass s (in) | synth s (in) | bass leads s | LUFS | peak dBFS | bass band 30-250 | sub 30-80 | bass-drums dB | bass-synth dB | phone bass dB | carry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| base | squadron_c01 | 54.9 (1) | 48.0 (2) | 0.0 (-) | 48.0 | -11.4 | -3.5 | 83% | 32% | +14.9 | +20.8 | -0.6 |  |
| base.c02 | squadron_c02 | 54.9 (1) | 48.0 (2) | 0.0 (-) | 48.0 | -13.1 | -3.4 | 70% | 35% | +15.8 | +20.9 | -0.7 |  |
| base.c03 | squadron_c03 | 54.9 (1) | 48.0 (2) | 41.1 (3) | 48.0 | -15.8 | -2.7 | 87% | 18% | +15.6 | +15.6 | -0.7 |  |
| air | squadron_c04 | 54.9 (1) | 48.0 (2) | 0.0 (-) | 48.0 | -12.0 | -1.5 | 86% | 33% | +15.3 | +21.1 | -0.7 |  |
| air.c05 | squadron_c05 | 54.9 (1) | 48.0 (2) | 0.0 (-) | 48.0 | -15.3 | -3.1 | 85% | 41% | +10.6 | +20.7 | -1.1 |  |
| air.c06 | squadron_c06 | 54.9 (1) | 48.0 (2) | 34.3 (4) | 48.0 | -15.3 | -0.9 | 84% | 31% | +11.9 | +19.0 | -1.2 |  |
| city | squadron_c07 | 13.7 (1) | 48.0 (2) | 0.0 (-) | 48.0 | -11.9 | -2.6 | 91% | 69% | +21.5 | +22.0 | -0.5 |  |
| city.c08 | squadron_c08 | 54.9 (1) | 48.0 (2) | 0.0 (-) | 48.0 | -10.3 | -2.9 | 93% | 51% | +18.2 | +27.0 | -0.2 |  |
| city.c09 | squadron_c09 | 54.9 (1) | 48.0 (2) | 34.3 (4) | 48.0 | -13.7 | -3.5 | 89% | 30% | +10.8 | +19.8 | -0.5 |  |
| city.c10 | squadron_c10 | 13.7 (1) | 48.0 (2) | 0.0 (-) | 48.0 | -10.8 | -2.9 | 89% | 51% | +21.4 | +22.7 | -0.4 |  |
| escape | squadron_c11 | 54.9 (1) | 48.0 (2) | 34.3 (4) | 48.0 | -11.5 | -3.7 | 92% | 17% | +17.4 | +20.8 | -0.3 |  |
| escape.c12 | squadron_c12 | 54.9 (1) | 48.0 (2) | 0.0 (-) | 48.0 | -11.9 | -2.0 | 87% | 47% | +13.3 | +21.5 | -0.3 |  |
| escape.c13 | squadron_c13 | 13.7 (1) | 48.0 (2) | 0.0 (-) | 48.0 | -10.5 | -2.6 | 93% | 36% | +22.1 | +23.6 | -0.2 |  |
| escape.c14 | squadron_c14 | 54.9 (1) | 48.0 (2) | 0.0 (-) | 48.0 | -12.5 | -2.8 | 94% | 42% | +14.9 | +21.2 | -0.7 |  |

Mean over the 14 scenes: bass band 87.4%, sub 37.9%, bass-drums +16.0 dB, phone bass -0.6 dB, bass audible 48.0 s and leading 48.0 s of 54.9 s in a scene, LUFS -12.6, worst peak -0.9 dBFS.

## ember (145 BPM)

Dwell: phase 26.5 s (4 blocks of 6.62 s), laps per scene [1, 2]: a scene lasts 26.5-53.0 s (mean 50.9 s) and the default route 662 s; 15 scenes; default route 13 phases; phases per music family along it [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], per world [3, 2, 2, 4, 2]; 1-1 arrangement sections per phase (shortest 26.5 s); up to 3 mix/arrangement changes per phase; stage bass gains [0.0, 1.0, 0.85, 1.0]; recipe bass floor 0.9; bass in 19.9 s then out 6.6 s at every scene change (carried at 0.5 within a family); 0 hotspots dip the music to 0.55 (-5.2 dB) for 6 beats (2.5 s); phase fade 0.6 s; run level -2 dB.

| scene | family | drums s (in) | bass s (in) | synth s (in) | bass leads s | LUFS | peak dBFS | bass band 30-250 | sub 30-80 | bass-drums dB | bass-synth dB | phone bass dB | carry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hollow | ember_e00_orchard | 26.5 (1) | 19.9 (2) | 0.0 (-) | 19.9 | -13.5 | -1.6 | 90% | 48% | +13.0 | +23.3 | -0.1 |  |
| hollow.ford | ember_e01_ford | 53.0 (1) | 46.3 (2) | 0.0 (-) | 46.3 | -12.5 | -1.5 | 90% | 44% | +15.6 | +23.5 | -0.1 |  |
| hollow.inn | ember_e02_inn | 53.0 (1) | 46.3 (2) | 0.0 (-) | 46.3 | -12.1 | -1.9 | 90% | 42% | +15.8 | +23.7 | -0.2 |  |
| north | ember_e03_birch_hall | 53.0 (1) | 46.3 (2) | 0.0 (-) | 46.3 | -13.0 | -1.7 | 91% | 48% | +15.2 | +23.2 | -0.1 |  |
| north.pass | ember_e04_high_pass | 53.0 (1) | 46.3 (2) | 0.0 (-) | 46.3 | -12.5 | -1.8 | 90% | 44% | +15.6 | +23.5 | -0.1 |  |
| deeps | ember_e05_deep_halls | 53.0 (1) | 46.3 (2) | 0.0 (-) | 46.3 | -12.1 | -1.6 | 90% | 42% | +15.8 | +23.7 | -0.2 |  |
| deeps.falls | ember_e06_falls | 53.0 (1) | 46.3 (2) | 0.0 (-) | 46.3 | -13.0 | -2.0 | 91% | 48% | +15.2 | +23.2 | -0.1 |  |
| marsh | ember_e07_reed_marsh | 53.0 (1) | 46.3 (2) | 0.0 (-) | 46.3 | -12.5 | -1.7 | 90% | 44% | +15.6 | +23.5 | -0.1 |  |
| marsh.wall | ember_e08_black_wall | 53.0 (1) | 46.3 (2) | 0.0 (-) | 46.3 | -12.1 | -2.0 | 90% | 42% | +15.8 | +23.7 | -0.2 |  |
| marsh.stair | ember_e09_stair_of_bells | 53.0 (1) | 46.3 (2) | 0.0 (-) | 46.3 | -13.0 | -1.5 | 91% | 48% | +15.2 | +23.2 | -0.1 |  |
| marsh.plain | ember_e10_ash_plain | 53.0 (1) | 46.3 (2) | 0.0 (-) | 46.3 | -12.5 | -1.8 | 90% | 44% | +15.6 | +23.5 | -0.1 |  |
| mountain | ember_e11_throat | 53.0 (1) | 46.3 (2) | 0.0 (-) | 46.3 | -12.1 | -1.8 | 90% | 42% | +15.8 | +23.7 | -0.2 |  |
| mountain.spring | ember_e12_drowned_spring | 53.0 (1) | 46.3 (2) | 0.0 (-) | 46.3 | -13.0 | -2.4 | 91% | 48% | +15.2 | +23.2 | -0.1 |  |
| mountain.keeper | ember_e13_keeper | 53.0 (1) | 46.3 (2) | 0.0 (-) | 46.3 | -12.5 | -1.3 | 90% | 44% | +15.6 | +23.5 | -0.1 |  |
| mountain.taken | ember_e14_taken | 53.0 (1) | 46.3 (2) | 0.0 (-) | 46.3 | -12.1 | -2.0 | 90% | 42% | +15.8 | +23.7 | -0.2 |  |

Mean over the 15 scenes: bass band 90.1%, sub 44.6%, bass-drums +15.4 dB, phone bass -0.1 dB, bass audible 44.6 s and leading 44.6 s of 51.2 s in a scene, LUFS -12.6, worst peak -1.3 dBFS.

