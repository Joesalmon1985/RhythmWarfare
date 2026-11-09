## demo_perfect_build_drop_mix
107.5s peak -0.2 dBFS, rms -8.7 dB, clipped samples 0, longest silence 0.00s at 3.20s, silences>250ms 0, max sample step 1.33
builds passed 1/1, recoveries 0, misses 0, hits 42
```
[0.000] BUILD gatekeeper:firstDrop scheduled (opening): the song starts at 1.000; intro 25.517s (74.0 beats) with a drums minigame, then the 128-beat run-in, drop 70.655
[26.325] EVAL gatekeeper:firstDrop intro: 42/42 = 100.0% (threshold 80%) -> PASS
[26.325] run-in: gatekeeper carries on into its next section at 26.517; rhythm game off; drop 70.655
[70.464] DROP gatekeeper:firstDrop at 70.655
[70.656] plan complete after 1 drop(s): no further builds
```

## demo_partial_stem_mutes
97.5s peak -0.2 dBFS, rms -9.0 dB, clipped samples 0, longest silence 0.00s at 3.20s, silences>250ms 0, max sample step 1.33
builds passed 1/1, recoveries 0, misses 4, hits 38
```
[0.000] BUILD gatekeeper:firstDrop scheduled (opening): the song starts at 1.000; intro 25.517s (74.0 beats) with a drums minigame, then the 128-beat run-in, drop 70.655
[9.024] MISS kick pad 1: stem muted (timeline keeps running)
[11.691] RECOVERED kick: stem restored at its current musical position
[12.821] MISS kick pad 1: stem muted (timeline keeps running)
[13.760] RECOVERED kick: stem restored at its current musical position
[24.203] MISS kick pad 1: stem muted (timeline keeps running)
[26.325] EVAL gatekeeper:firstDrop intro: 38/42 = 90.5% (threshold 80%) -> PASS
[26.325] run-in: gatekeeper carries on into its next section at 26.517; rhythm game off; drop 70.655
[70.464] DROP gatekeeper:firstDrop at 70.655
[70.656] plan complete after 1 drop(s): no further builds
```

## demo_failure_recovery
133.5s peak -0.2 dBFS, rms -10.3 dB, clipped samples 0, longest silence 0.00s at 3.20s, silences>250ms 0, max sample step 1.33
builds passed 0/1, recoveries 2, misses 68, hits 58
```
[0.000] BUILD gatekeeper:firstDrop scheduled (opening): the song starts at 1.000; intro 25.517s (74.0 beats) with a drums minigame, then the 128-beat run-in, drop 70.655
[2.475] MISS snare pad 4: stem muted (timeline keeps running)
[2.816] MISS kick pad 1: stem muted (timeline keeps running)
[4.459] RECOVERED kick: stem restored at its current musical position
[9.280] RECOVERED snare: stem restored at its current musical position
[10.059] MISS kick pad 1: stem muted (timeline keeps running)
[12.128] MISS snare pad 4: stem muted (timeline keeps running)
[12.725] RECOVERED kick: stem restored at its current musical position
[13.163] MISS kick pad 1: stem muted (timeline keeps running)
[14.795] RECOVERED snare: stem restored at its current musical position
[17.643] MISS snare pad 4: stem muted (timeline keeps running)
[23.072] RECOVERED snare: stem restored at its current musical position
[23.765] RECOVERED kick: stem restored at its current musical position
[24.203] MISS kick pad 1: stem muted (timeline keeps running)
[24.544] MISS snare pad 4: stem muted (timeline keeps running)
[26.325] EVAL gatekeeper:firstDrop intro: 19/42 = 45.2% (threshold 80%) -> FAIL
[26.325] RECOVERY #1: intro loops again 26.517 -> 52.034
[27.307] MISS kick pad 1: stem muted (timeline keeps running)
[28.245] RECOVERED kick: stem restored at its current musical position
[29.024] MISS kick pad 1: stem muted (timeline keeps running)
[29.376] MISS snare pad 4: stem muted (timeline keeps running)
[32.725] RECOVERED kick: stem restored at its current musical position
[33.419] RECOVERED snare: stem restored at its current musical position
[34.539] MISS kick pad 1: stem muted (timeline keeps running)
[34.891] MISS snare pad 4: stem muted (timeline keeps running)
[38.592] RECOVERED kick: stem restored at its current musical position
[39.371] MISS kick pad 1: stem muted (timeline keeps running)
[40.320] RECOVERED snare: stem restored at its current musical position
[41.781] MISS snare pad 4: stem muted (timeline keeps running)
[42.731] RECOVERED kick: stem restored at its current musical position
[46.613] MISS kick pad 1: stem muted (timeline keeps running)
[47.211] RECOVERED snare: stem restored at its current musical position
[49.280] RECOVERED kick: stem restored at its current musical position
[49.717] MISS kick pad 1: stem muted (timeline keeps running)
[51.435] MISS snare pad 4: stem muted (timeline keeps running)
[51.840] EVAL recovery#1 gatekeeper:firstDrop intro: 22/42 = 52.4% (threshold 60%) -> FAIL
[51.840] RECOVERY #2: intro loops again 52.034 -> 77.551
[53.163] MISS kick pad 1: stem muted (timeline keeps running)
[53.504] MISS snare pad 4: stem muted (timeline keeps running)
[57.557] RECOVERED snare: stem restored at its current musical position
[58.251] RECOVERED kick: stem restored at its current musical position
[61.099] MISS kick pad 1: stem muted (timeline keeps running)
[61.781] MISS snare pad 4: stem muted (timeline keeps running)
[64.800] RECOVERED kick: stem restored at its current musical position
[66.613] MISS kick pad 1: stem muted (timeline keeps running)
[67.211] RECOVERED snare: stem restored at its current musical position
[68.683] MISS snare pad 4: stem muted (timeline keeps running)
[72.725] RECOVERED snare: stem restored at its current musical position
[75.573] MISS snare pad 4: stem muted (timeline keeps running)
[77.355] EVAL recovery#2 gatekeeper:firstDrop intro: 17/42 = 40.5% (threshold 60%) -> FAIL
[77.355] recovery attempts exhausted: moving on to the run-in anyway (no soft-lock)
[77.355] run-in: gatekeeper carries on into its next section at 77.551; rhythm game off; drop 121.689
[121.493] DROP gatekeeper:firstDrop at 121.689
[121.696] plan complete after 1 drop(s): no further builds
```

