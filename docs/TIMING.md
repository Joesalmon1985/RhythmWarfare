# Timing: clocks, offsets and their signs

## The song clock

`SongClock.audio_time()` is the position of the sound reaching the listener:

```
audio_time = transport.playback_position()           # frames mixed so far, from the audio thread
           + AudioServer.get_time_since_last_mix()   # wall time since that mix block
           - output_latency                          # AudioServer.get_output_latency(), cached when the song starts
```

It is never built from accumulated frame deltas, it is clamped so audio-thread jitter cannot move it backwards,
and it freezes while paused. During the pre-song countdown it is negative. All four stems are one
`AudioStreamSynchronized` inside one `AudioStreamPlayer`, so there is exactly one playhead; muting a stem changes its
gain (30 ms ramp) and never stops or restarts it.

## Two offsets, kept apart

| Offset | Lives in | Sign |
| --- | --- | --- |
| `song_offset_ms` (authored, per song pack) | `Level.tick_to_seconds`: `song_offset_ms / 1000 + tick * 60 / (bpm * ticks_per_beat)` | Positive moves every chart event later in the audio. Use it when the stems carry leading silence before bar 1. |
| `calibration_ms` (per device and player, `user://settings.cfg`) | `SongClock.judge_time() = audio_time() - calibration_ms / 1000` | Positive means the player's taps are measured late on this device (touch latency, personal habit); subtracting it judges the taps earlier. The calibration screen measures it as the mean lateness of taps against a generated metronome. |

Judgement and the note display both use `judge_time()`, so what the player sees on the timing line is what is judged.

## Judgement windows

Perfect within ±45 ms, Good within ±100 ms, both the full reward. A bass hold needs its press inside the start
window and the finger down until the tail, with 60 ms of early-release tolerance; the reward resolves at the
scheduled tail, never earlier.

## Pause and resume

Pause freezes the audio (`stream_paused`), the clock, judgement and (from M1) the battle together. An active hold
is voided: no reward, no penalty, excluded from accuracy. Resume shows a 3-second countdown and re-anchors the
clock at the frozen value, so time can never jump backwards across a pause. App focus loss pauses.
