## demo_perfect_build_drop_mix
128.1s peak -0.2 dBFS, rms -10.0 dB, clipped samples 0, longest silence 0.17s at 3.51s, silences>250ms 0, max sample step 1.23
builds passed 1/1, recoveries 0, misses 0, hits 60
```
[0.000] BUILD gatekeeper:firstDrop scheduled: start 3.000, drop 91.276 (5 phases: drums / bass / drums2 / bass2 / runin)
[13.835] gatekeeper:firstDrop drums: 18/18 = 100.0% (not gated)
[24.875] gatekeeper:firstDrop bass: 12/12 = 100.0% (not gated)
[35.904] gatekeeper:firstDrop drums2: 18/18 = 100.0% (not gated)
[46.944] EVAL gatekeeper:firstDrop bass2 (all 4 loops): 60/60 = 100.0% (threshold 80%) -> PASS
[46.944] run-in: gatekeeper enters at 47.138 (clip 25.517s), eases in over 8 beats; rhythm game off; drop 91.276
[91.083] DROP gatekeeper:firstDrop at 91.276
[91.285] plan complete after 1 drop(s): no further builds
```

## demo_partial_stem_mutes
118.1s peak -0.2 dBFS, rms -10.5 dB, clipped samples 0, longest silence 0.17s at 3.51s, silences>250ms 0, max sample step 1.23
builds passed 1/1, recoveries 0, misses 7, hits 53
```
[0.000] BUILD gatekeeper:firstDrop scheduled: start 3.000, drop 91.276 (5 phases: drums / bass / drums2 / bass2 / runin)
[11.371] MISS kick pad 1: stem muted (timeline keeps running)
[12.320] RECOVERED kick: stem restored at its current musical position
[13.835] gatekeeper:firstDrop drums: 17/18 = 94.4% (not gated)
[14.133] MISS bass pad 1: stem muted (timeline keeps running)
[16.107] RECOVERED bass: stem restored at its current musical position
[24.875] gatekeeper:firstDrop bass: 11/12 = 91.7% (not gated)
[29.995] MISS snare pad 4: stem muted (timeline keeps running)
[32.405] MISS kick pad 1: stem muted (timeline keeps running)
[32.661] RECOVERED snare: stem restored at its current musical position
[33.696] RECOVERED kick: stem restored at its current musical position
[35.904] gatekeeper:firstDrop drums2: 16/18 = 88.9% (not gated)
[37.579] MISS bass pad 2: stem muted (timeline keeps running)
[40.245] RECOVERED bass: stem restored at its current musical position
[46.197] MISS bass pad 4: stem muted (timeline keeps running)
[46.944] EVAL gatekeeper:firstDrop bass2 (all 4 loops): 53/60 = 88.3% (threshold 80%) -> PASS
[46.944] run-in: gatekeeper enters at 47.138 (clip 25.517s), eases in over 8 beats; rhythm game off; drop 91.276
[91.083] DROP gatekeeper:firstDrop at 91.276
[91.285] plan complete after 1 drop(s): no further builds
```

## demo_failure_recovery
130.1s peak -0.2 dBFS, rms -12.0 dB, clipped samples 0, longest silence 0.18s at 5.23s, silences>250ms 0, max sample step 1.23
builds passed 0/1, recoveries 2, misses 43, hits 41
```
[0.000] BUILD gatekeeper:firstDrop scheduled: start 3.000, drop 91.276 (5 phases: drums / bass / drums2 / bass2 / runin)
[4.821] MISS kick pad 1: stem muted (timeline keeps running)
[5.163] MISS snare pad 4: stem muted (timeline keeps running)
[7.488] RECOVERED kick: stem restored at its current musical position
[13.835] gatekeeper:firstDrop drums: 11/18 = 61.1% (not gated)
[15.509] MISS bass pad 2: stem muted (timeline keeps running)
[18.869] RECOVERED bass: stem restored at its current musical position
[22.411] MISS bass pad 2: stem muted (timeline keeps running)
[24.875] gatekeeper:firstDrop bass: 6/12 = 50.0% (not gated)
[25.163] MISS kick pad 1: stem muted (timeline keeps running)
[25.856] MISS snare pad 4: stem muted (timeline keeps running)
[33.696] RECOVERED kick: stem restored at its current musical position
[34.037] RECOVERED snare: stem restored at its current musical position
[35.168] MISS kick pad 1: stem muted (timeline keeps running)
[35.509] MISS snare pad 4: stem muted (timeline keeps running)
[35.904] gatekeeper:firstDrop drums2: 5/18 = 27.8% (not gated)
[36.203] MISS bass pad 1: stem muted (timeline keeps running)
[38.176] RECOVERED bass: stem restored at its current musical position
[38.955] MISS bass pad 1: stem muted (timeline keeps running)
[40.939] RECOVERED bass: stem restored at its current musical position
[41.717] MISS bass pad 3: stem muted (timeline keeps running)
[45.419] RECOVERED bass: stem restored at its current musical position
[46.197] MISS bass pad 4: stem muted (timeline keeps running)
[46.944] EVAL gatekeeper:firstDrop bass2 (all 4 loops): 28/60 = 46.7% (threshold 80%) -> FAIL
[46.944] RECOVERY #1: bass2 again 47.138 -> 58.172
[47.232] MISS bass pad 1: stem muted (timeline keeps running)
[51.968] RECOVERED bass: stem restored at its current musical position
[54.133] MISS bass pad 3: stem muted (timeline keeps running)
[56.459] RECOVERED bass: stem restored at its current musical position
[57.920] MISS bass pad 3: stem muted (timeline keeps running)
[57.973] EVAL recovery#1 gatekeeper:firstDrop bass2: 6/12 = 50.0% (threshold 60%) -> FAIL
[57.973] RECOVERY #2: bass2 again 58.172 -> 69.207
[59.648] MISS bass pad 2: stem muted (timeline keeps running)
[62.315] RECOVERED bass: stem restored at its current musical position
[65.163] MISS bass pad 3: stem muted (timeline keeps running)
[67.488] RECOVERED bass: stem restored at its current musical position
[68.267] MISS bass pad 4: stem muted (timeline keeps running)
[69.013] EVAL recovery#2 gatekeeper:firstDrop bass2: 7/12 = 58.3% (threshold 60%) -> FAIL
[69.013] recovery attempts exhausted: moving on anyway (no soft-lock)
[69.013] run-in: gatekeeper enters at 69.207 (clip 25.517s), eases in over 8 beats; rhythm game off; drop 113.345
[113.152] DROP gatekeeper:firstDrop at 113.345
[113.355] plan complete after 1 drop(s): no further builds
```

