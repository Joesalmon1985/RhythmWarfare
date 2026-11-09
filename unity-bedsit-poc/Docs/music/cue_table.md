# Cue table (derived)

`cue = anchor - beats * 60/BPM`. A cue is **invalid** if it falls before the start of the file or after its end; invalid cues are listed, never clamped. "owner" columns use the supplied reference timestamps; "used" columns use the anchors the game aligns to (measured from the audio where the file exists, otherwise the owner timestamps).


## The Gatekeeper (Original Mix) - Fresh  (`gatekeeper`, 174.0 BPM, audio on this PC)

| anchor | beats before | owner cue (s) | used cue (s) | valid | note |
|---|---:|---:|---:|:---:|---|
| firstDrop | 128 | 25.542 | 25.517 | yes |  |
| firstDrop | 256 | -18.596 | -18.621 | **NO** | before the start of the file |
| firstDrop | 384 | -62.734 | -62.759 | **NO** | before the start of the file |
| secondDrop | 128 | 157.952 | 157.931 | yes |  |
| secondDrop | 256 | 113.814 | 113.793 | yes |  |
| secondDrop | 384 | 69.676 | 69.655 | yes |  |
| ending | 128 | 268.292 | 268.276 | yes |  |
| ending | 256 | 224.154 | 224.138 | yes |  |

## Drop Dis - CLB ft. Madrush MC  (`dropdis`, 174.0 BPM, **audio NOT on this PC** - owner timestamps only)

| anchor | beats before | owner cue (s) | used cue (s) | valid | note |
|---|---:|---:|---:|:---:|---|
| firstDrop | 128 | 22.042 | 22.042 | yes |  |
| firstDrop | 256 | -22.096 | -22.096 | **NO** | before the start of the file |
| firstDrop | 384 | -66.234 | -66.234 | **NO** | before the start of the file |
| secondDrop | 128 | 132.392 | 132.392 | yes |  |
| secondDrop | 256 | 88.254 | 88.254 | yes |  |
| secondDrop | 384 | 44.116 | 44.116 | yes |  |
| ending | 128 | 220.672 | 220.672 | yes |  |
| ending | 256 | 176.534 | 176.534 | yes |  |

## Levels - Contort  (`levels`, 174.0 BPM, **audio NOT on this PC** - owner timestamps only)

| anchor | beats before | owner cue (s) | used cue (s) | valid | note |
|---|---:|---:|---:|:---:|---|
| firstDrop | 128 | 0.012 | 0.012 | yes |  |
| firstDrop | 256 | -44.126 | -44.126 | **NO** | before the start of the file |
| firstDrop | 384 | -88.264 | -88.264 | **NO** | before the start of the file |
| secondDrop | 128 | 88.282 | 88.282 | yes |  |
| secondDrop | 256 | 44.144 | 44.144 | yes |  |
| secondDrop | 384 | 0.006 | 0.006 | yes |  |
| ending | 128 | 176.562 | 176.562 | yes |  |
| ending | 256 | 132.424 | 132.424 | yes |  |
