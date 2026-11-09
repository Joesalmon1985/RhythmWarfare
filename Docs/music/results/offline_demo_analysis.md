## demo_perfect_build_drop_mix
72.9s peak -0.2 dBFS, rms -8.6 dB, clipped samples 0, longest silence 0.17s at 3.51s, silences>250ms 0, max sample step 1.23
builds passed 1/2, recoveries 0, misses 0, hits 46
```
[0.000] BUILD gatekeeper:firstDrop scheduled: start 3.000, drop 36.103 (3 phases: drums / bass / buildup)
[13.835] gatekeeper:firstDrop drums: 18/18 = 100.0% (warm-up loop, not gated)
[24.875] EVAL gatekeeper:firstDrop bass: 12/12 = 100.0% (threshold 80%) -> PASS
[24.875] buildup: gatekeeper enters at 25.069 (clip 58.621s), eases in over 8 beats; drop 36.103
[34.528] EVAL gatekeeper:firstDrop buildup: 16/16 = 100.0% (threshold 80%) -> PASS
[34.528] DROP gatekeeper:firstDrop at 36.103
[36.107] BUILD gatekeeper:secondDrop scheduled: start 135.413, drop 168.517 (3 phases: drums / bass / buildup)
[36.107] L2: handover to 'dropdis' unavailable -> fallback build gatekeeper:secondDrop
```

## demo_partial_stem_mutes
62.9s peak -0.2 dBFS, rms -9.0 dB, clipped samples 0, longest silence 0.17s at 3.51s, silences>250ms 0, max sample step 1.23
builds passed 1/2, recoveries 0, misses 4, hits 42
```
[0.000] BUILD gatekeeper:firstDrop scheduled: start 3.000, drop 36.103 (3 phases: drums / bass / buildup)
[11.371] MISS kick pad 1: stem muted (timeline keeps running)
[12.320] RECOVERED kick: stem restored at its current musical position
[13.835] gatekeeper:firstDrop drums: 17/18 = 94.4% (warm-up loop, not gated)
[14.133] MISS bass pad 1: stem muted (timeline keeps running)
[16.107] RECOVERED bass: stem restored at its current musical position
[24.875] EVAL gatekeeper:firstDrop bass: 11/12 = 91.7% (threshold 80%) -> PASS
[24.875] buildup: gatekeeper enters at 25.069 (clip 58.621s), eases in over 8 beats; drop 36.103
[29.995] MISS snare pad 4: stem muted (timeline keeps running)
[32.405] MISS kick pad 1: stem muted (timeline keeps running)
[32.661] RECOVERED snare: stem restored at its current musical position
[33.696] RECOVERED kick: stem restored at its current musical position
[34.528] EVAL gatekeeper:firstDrop buildup: 14/16 = 87.5% (threshold 80%) -> PASS
[34.528] DROP gatekeeper:firstDrop at 36.103
[36.107] BUILD gatekeeper:secondDrop scheduled: start 135.413, drop 168.517 (3 phases: drums / bass / buildup)
[36.107] L2: handover to 'dropdis' unavailable -> fallback build gatekeeper:secondDrop
```

## demo_failure_recovery
107.0s peak -0.2 dBFS, rms -10.8 dB, clipped samples 0, longest silence 0.18s at 5.23s, silences>250ms 0, max sample step 1.23
builds passed 0/2, recoveries 4, misses 51, hits 51
```
[0.000] BUILD gatekeeper:firstDrop scheduled: start 3.000, drop 36.103 (3 phases: drums / bass / buildup)
[4.821] MISS kick pad 1: stem muted (timeline keeps running)
[5.163] MISS snare pad 4: stem muted (timeline keeps running)
[7.488] RECOVERED kick: stem restored at its current musical position
[13.835] gatekeeper:firstDrop drums: 11/18 = 61.1% (warm-up loop, not gated)
[15.509] MISS bass pad 2: stem muted (timeline keeps running)
[18.869] RECOVERED bass: stem restored at its current musical position
[22.411] MISS bass pad 2: stem muted (timeline keeps running)
[24.875] EVAL gatekeeper:firstDrop bass: 6/12 = 50.0% (threshold 80%) -> FAIL
[24.875] RECOVERY #1: bass again 25.069 -> 36.103
[25.163] MISS bass pad 1: stem muted (timeline keeps running)
[30.592] RECOVERED bass: stem restored at its current musical position
[32.064] MISS bass pad 3: stem muted (timeline keeps running)
[35.904] EVAL recovery#1 gatekeeper:firstDrop bass: 2/12 = 16.7% (threshold 60%) -> FAIL
[35.904] RECOVERY #2: bass again 36.103 -> 47.138
[36.203] MISS bass pad 1: stem muted (timeline keeps running)
[38.176] RECOVERED bass: stem restored at its current musical position
[40.341] MISS bass pad 2: stem muted (timeline keeps running)
[44.384] RECOVERED bass: stem restored at its current musical position
[45.504] MISS bass pad 2: stem muted (timeline keeps running)
[46.795] RECOVERED bass: stem restored at its current musical position
[46.944] EVAL recovery#2 gatekeeper:firstDrop bass: 7/12 = 58.3% (threshold 60%) -> FAIL
[46.944] recovery attempts exhausted: moving on anyway (no soft-lock)
[46.944] buildup: gatekeeper enters at 47.138 (clip 58.621s), eases in over 8 beats; drop 58.172
[47.232] MISS kick pad 1: stem muted (timeline keeps running)
[47.925] MISS snare pad 4: stem muted (timeline keeps running)
[51.968] RECOVERED snare: stem restored at its current musical position
[53.440] MISS snare pad 4: stem muted (timeline keeps running)
[55.424] RECOVERED kick: stem restored at its current musical position
[55.851] MISS kick pad 1: stem muted (timeline keeps running)
[56.107] RECOVERED snare: stem restored at its current musical position
[56.597] EVAL gatekeeper:firstDrop buildup: 7/16 = 43.8% (threshold 80%) -> FAIL
[56.597] RECOVERY #1: buildup again 58.172 -> 69.207 (buildup re-enters, drop held)
[56.597] buildup: gatekeeper enters at 58.172 (clip 58.621s), eases in over 8 beats; drop 69.207
[58.176] RECOVERED kick: stem restored at its current musical position
[58.955] MISS snare pad 4: stem muted (timeline keeps running)
[61.024] MISS kick pad 1: stem muted (timeline keeps running)
[63.008] RECOVERED snare: stem restored at its current musical position
[63.691] RECOVERED kick: stem restored at its current musical position
[64.469] MISS snare pad 4: stem muted (timeline keeps running)
[66.539] MISS kick pad 1: stem muted (timeline keeps running)
[67.147] RECOVERED snare: stem restored at its current musical position
[67.637] EVAL recovery#1 gatekeeper:firstDrop buildup: 9/16 = 56.3% (threshold 60%) -> FAIL
[67.637] RECOVERY #2: buildup again 69.207 -> 80.241 (buildup re-enters, drop held)
[67.637] buildup: gatekeeper enters at 69.207 (clip 58.621s), eases in over 8 beats; drop 80.241
[69.301] MISS kick pad 1: stem muted (timeline keeps running)
[69.995] MISS snare pad 4: stem muted (timeline keeps running)
[74.037] RECOVERED snare: stem restored at its current musical position
[74.731] RECOVERED kick: stem restored at its current musical position
[77.579] MISS kick pad 1: stem muted (timeline keeps running)
[78.667] EVAL recovery#2 gatekeeper:firstDrop buildup: 9/16 = 56.3% (threshold 60%) -> FAIL
[78.667] recovery attempts exhausted: moving on anyway (no soft-lock)
[78.667] DROP gatekeeper:firstDrop at 80.241
[80.245] BUILD gatekeeper:secondDrop scheduled: start 179.551, drop 212.655 (3 phases: drums / bass / buildup)
[80.245] L2: handover to 'dropdis' unavailable -> fallback build gatekeeper:secondDrop
```

