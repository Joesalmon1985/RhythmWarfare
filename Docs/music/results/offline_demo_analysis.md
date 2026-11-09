## demo_perfect_build_drop_mix
83.9s peak -0.2 dBFS, rms -9.4 dB, clipped samples 0, longest silence 0.17s at 3.51s, silences>250ms 0, max sample step 1.23
builds passed 1/2, recoveries 0, misses 0, hits 60
```
[0.000] BUILD gatekeeper:firstDrop scheduled: start 3.000, drop 47.138 (128 beats)
[46.944] EVAL build gatekeeper:firstDrop: 60/60 = 100.0% (threshold 80%) -> PASS
[46.944] DROP gatekeeper:firstDrop at 47.138
[47.147] BUILD gatekeeper:secondDrop scheduled: start 135.414, drop 179.551 (128 beats)
[47.147] L2: handover to 'dropdis' unavailable -> fallback build gatekeeper:secondDrop
```

## demo_partial_stem_mutes
73.9s peak -0.2 dBFS, rms -10.0 dB, clipped samples 0, longest silence 0.17s at 3.51s, silences>250ms 0, max sample step 1.23
builds passed 1/2, recoveries 0, misses 7, hits 53
```
[0.000] BUILD gatekeeper:firstDrop scheduled: start 3.000, drop 47.138 (128 beats)
[11.371] MISS kick pad 1: stem muted (timeline keeps running)
[12.320] RECOVERED kick: stem restored at its current musical position
[14.133] MISS bass pad 1: stem muted (timeline keeps running)
[16.107] RECOVERED bass: stem restored at its current musical position
[29.995] MISS snare pad 4: stem muted (timeline keeps running)
[32.405] MISS kick pad 1: stem muted (timeline keeps running)
[32.661] RECOVERED snare: stem restored at its current musical position
[33.696] RECOVERED kick: stem restored at its current musical position
[37.579] MISS bass pad 2: stem muted (timeline keeps running)
[40.245] RECOVERED bass: stem restored at its current musical position
[46.197] MISS bass pad 4: stem muted (timeline keeps running)
[46.944] EVAL build gatekeeper:firstDrop: 53/60 = 88.3% (threshold 80%) -> PASS
[46.944] DROP gatekeeper:firstDrop at 47.138
[47.147] BUILD gatekeeper:secondDrop scheduled: start 135.414, drop 179.551 (128 beats)
[47.147] L2: handover to 'dropdis' unavailable -> fallback build gatekeeper:secondDrop
```

## demo_failure_recovery
107.0s peak -0.2 dBFS, rms -11.6 dB, clipped samples 0, longest silence 0.18s at 5.23s, silences>250ms 0, max sample step 1.23
builds passed 0/2, recoveries 3, misses 59, hits 55
```
[0.000] BUILD gatekeeper:firstDrop scheduled: start 3.000, drop 47.138 (128 beats)
[4.821] MISS kick pad 1: stem muted (timeline keeps running)
[5.163] MISS snare pad 4: stem muted (timeline keeps running)
[7.488] RECOVERED kick: stem restored at its current musical position
[15.509] MISS bass pad 2: stem muted (timeline keeps running)
[18.869] RECOVERED bass: stem restored at its current musical position
[22.411] MISS bass pad 2: stem muted (timeline keeps running)
[25.163] MISS kick pad 1: stem muted (timeline keeps running)
[28.523] RECOVERED snare: stem restored at its current musical position
[29.995] MISS snare pad 4: stem muted (timeline keeps running)
[33.696] RECOVERED kick: stem restored at its current musical position
[35.168] MISS kick pad 1: stem muted (timeline keeps running)
[37.493] RECOVERED bass: stem restored at its current musical position
[38.955] MISS bass pad 1: stem muted (timeline keeps running)
[40.939] RECOVERED bass: stem restored at its current musical position
[41.717] MISS bass pad 3: stem muted (timeline keeps running)
[45.419] RECOVERED bass: stem restored at its current musical position
[46.197] MISS bass pad 4: stem muted (timeline keeps running)
[46.944] EVAL build gatekeeper:firstDrop: 28/60 = 46.7% (threshold 80%) -> FAIL
[46.944] RECOVERY #1: custom phrase 47.138 -> 58.172, then drop gatekeeper:firstDrop
[47.829] RECOVERED snare: stem restored at its current musical position
[49.301] MISS snare pad 4: stem muted (timeline keeps running)
[52.661] RECOVERED kick: stem restored at its current musical position
[53.355] RECOVERED snare: stem restored at its current musical position
[54.816] MISS snare pad 4: stem muted (timeline keeps running)
[55.851] MISS kick pad 1: stem muted (timeline keeps running)
[57.141] RECOVERED kick: stem restored at its current musical position
[57.973] EVAL recovery#1 gatekeeper:firstDrop: 10/18 = 55.6% (threshold 60%) -> FAIL
[57.973] RECOVERY #2: custom phrase 58.172 -> 69.207, then drop gatekeeper:firstDrop
[60.245] RECOVERED snare: stem restored at its current musical position
[61.024] MISS kick pad 1: stem muted (timeline keeps running)
[61.717] MISS snare pad 4: stem muted (timeline keeps running)
[65.419] RECOVERED kick: stem restored at its current musical position
[66.539] MISS kick pad 1: stem muted (timeline keeps running)
[68.181] RECOVERED kick: stem restored at its current musical position
[68.523] RECOVERED snare: stem restored at its current musical position
[69.013] EVAL recovery#2 gatekeeper:firstDrop: 9/18 = 50.0% (threshold 60%) -> FAIL
[69.013] RECOVERY #3: custom phrase 69.207 -> 80.241, then drop gatekeeper:firstDrop
[71.029] MISS kick pad 1: stem muted (timeline keeps running)
[71.371] MISS snare pad 4: stem muted (timeline keeps running)
[75.424] RECOVERED snare: stem restored at its current musical position
[76.459] RECOVERED kick: stem restored at its current musical position
[76.885] MISS snare pad 4: stem muted (timeline keeps running)
[77.579] MISS kick pad 1: stem muted (timeline keeps running)
[79.211] RECOVERED kick: stem restored at its current musical position
[80.043] EVAL recovery#3 gatekeeper:firstDrop: 8/18 = 44.4% (threshold 60%) -> FAIL
[80.043] recovery attempts exhausted: continuing to the drop anyway (no soft-lock)
[80.043] DROP gatekeeper:firstDrop at 80.241
[80.245] BUILD gatekeeper:secondDrop scheduled: start 168.517, drop 212.655 (128 beats)
[80.245] L2: handover to 'dropdis' unavailable -> fallback build gatekeeper:secondDrop
```

