using System;
using System.Collections.Generic;

namespace Bedsit.Music
{
    /// <summary>
    /// The authoritative music timeline and a sample-accurate software mixer. Everything (recordings, custom stems, fades,
    /// stem mutes) is a Voice scheduled at an absolute TIMELINE time. The timeline advances only when audio is rendered, so
    /// it is the audio clock: pausing the mixer freezes scheduling, and render-offline == what the device would play.
    /// Thread-safe: the audio thread calls Render, the game thread schedules.
    /// </summary>
    public sealed class Mixer
    {
        public readonly int SampleRate;
        readonly object _lock = new object();
        readonly List<Voice> _voices = new List<Voice>();
        long _frame;

        public bool Paused;
        public float MasterGain = 1f;
        public float Ceiling = 0.90f;               // soft limiter knee; output is asymptotic to MaxOutput (< 0.999, so never "clipped")
        public float MaxOutput = 0.98f;
        public double PeakAfter, PeakBefore;        // since last ResetStats
        public long OverCount;                      // samples that exceeded 1.0 BEFORE the limiter

        public Mixer(int sampleRate = 48000) { SampleRate = sampleRate; }

        public double Time { get { lock (_lock) return _frame / (double)SampleRate; } }
        public long Frame { get { lock (_lock) return _frame; } }

        internal struct Ramp { public long S, E; public float G0, G1; }

        public sealed class Voice
        {
            public string Tag, Role;
            public PcmClip Clip;
            public long StartFrame, ClipOffsetFrames, StopFrame = long.MaxValue;
            public bool Loop;
            public float BaseGain = 1f, BaseTrim = 1f;
            internal readonly List<Ramp> Layout = new List<Ramp>();
            internal readonly List<Ramp> Trim = new List<Ramp>();
            public double StartTime(int sr) => StartFrame / (double)sr;
            public bool Stopped;
        }

        // ------------------------------------------------------------------------------------------------ scheduling

        public long ToFrame(double timelineSeconds) => (long)Math.Round(timelineSeconds * SampleRate);

        /// <summary>Start playing clip position <paramref name="clipSeconds"/> at timeline time <paramref name="timelineTime"/>.</summary>
        public Voice Play(string tag, PcmClip clip, double timelineTime, double clipSeconds, float gain, bool loop = false, string role = null)
        {
            var v = new Voice { Tag = tag, Role = role, Clip = clip, StartFrame = ToFrame(timelineTime), ClipOffsetFrames = (long)Math.Round(clipSeconds * SampleRate), Loop = loop, BaseGain = gain };
            lock (_lock) _voices.Add(v);
            return v;
        }

        static float Eval(List<Ramp> ramps, float baseValue, long frame)
        {
            float val = baseValue;
            long bestStart = long.MinValue;
            for (int i = 0; i < ramps.Count; i++)
            {
                var r = ramps[i];
                if (r.S > frame || r.S < bestStart) continue;
                bestStart = r.S;
                if (frame >= r.E) val = r.G1;
                else val = r.G0 + (r.G1 - r.G0) * (float)((frame - r.S) / (double)Math.Max(1, r.E - r.S));
            }
            return val;
        }

        public float GainAt(Voice v, double t)
        {
            long f = ToFrame(t);
            lock (_lock) return Eval(v.Layout, v.BaseGain, f) * Eval(v.Trim, v.BaseTrim, f);
        }

        public float TrimAt(Voice v, double t) { long f = ToFrame(t); lock (_lock) return Eval(v.Trim, v.BaseTrim, f); }

        /// <summary>Ramp the layout (arrangement) gain from its value at t0 to <paramref name="target"/> at t1.</summary>
        public void RampTo(Voice v, double t0, double t1, float target)
        {
            long f0 = ToFrame(t0), f1 = Math.Max(f0 + 1, ToFrame(t1));
            lock (_lock) v.Layout.Add(new Ramp { S = f0, E = f1, G0 = Eval(v.Layout, v.BaseGain, f0), G1 = target });
        }

        /// <summary>Ramp the "mistake" trim (independent of the arrangement ramps) from its value at t0 to target at t1.</summary>
        public void TrimTo(Voice v, double t0, double t1, float target)
        {
            long f0 = ToFrame(t0), f1 = Math.Max(f0 + 1, ToFrame(t1));
            lock (_lock) v.Trim.Add(new Ramp { S = f0, E = f1, G0 = Eval(v.Trim, v.BaseTrim, f0), G1 = target });
        }

        public void StopAt(Voice v, double t) { lock (_lock) v.StopFrame = ToFrame(t); }

        /// <summary>Position inside the clip (seconds) that plays at timeline time t.</summary>
        public double ClipTimeAt(Voice v, double t)
        {
            double rel = (ToFrame(t) - v.StartFrame + v.ClipOffsetFrames) / (double)SampleRate;
            if (v.Loop && v.Clip.Frames > 0) rel %= v.Clip.Seconds;
            return rel;
        }

        /// <summary>Timeline time at which the given clip position plays (non-looping voices).</summary>
        public double TimelineOfClipTime(Voice v, double clipSeconds) =>
            (v.StartFrame + (long)Math.Round(clipSeconds * SampleRate) - v.ClipOffsetFrames) / (double)SampleRate;

        public IReadOnlyList<Voice> Voices { get { lock (_lock) return _voices.ToArray(); } }

        public void ResetStats() { lock (_lock) { PeakAfter = PeakBefore = 0; OverCount = 0; } }

        // ------------------------------------------------------------------------------------------------ render

        /// <summary>Fill an interleaved stereo buffer and advance the timeline. While paused, outputs silence and does NOT advance.</summary>
        public void Render(float[] buf, int frames)
        {
            lock (_lock)
            {
                if (Paused) { Array.Clear(buf, 0, frames * 2); return; }
                Array.Clear(buf, 0, frames * 2);
                long f0 = _frame;
                for (int vi = _voices.Count - 1; vi >= 0; vi--)
                {
                    var v = _voices[vi];
                    long vEnd = v.StopFrame;
                    if (!v.Loop) vEnd = Math.Min(vEnd, v.StartFrame - v.ClipOffsetFrames + v.Clip.Frames);
                    if (vEnd <= f0 && vEnd != long.MaxValue) { _voices.RemoveAt(vi); continue; }
                    long a = Math.Max(f0, v.StartFrame), b = Math.Min(f0 + frames, vEnd);
                    if (a >= b) continue;
                    var data = v.Clip.Data; int cf = v.Clip.Frames;
                    bool simple = v.Layout.Count == 0 && v.Trim.Count == 0;
                    float constGain = v.BaseGain * v.BaseTrim;
                    for (long f = a; f < b; f++)
                    {
                        long pos = f - v.StartFrame + v.ClipOffsetFrames;
                        if (v.Loop) { pos %= cf; if (pos < 0) pos += cf; }
                        else if (pos < 0 || pos >= cf) continue;
                        float g = simple ? constGain : Eval(v.Layout, v.BaseGain, f) * Eval(v.Trim, v.BaseTrim, f);
                        int o = (int)(f - f0) * 2;
                        buf[o] += data[pos * 2] * g;
                        buf[o + 1] += data[pos * 2 + 1] * g;
                    }
                }
                // master: gain, peak stats, soft limiter (no hard clipping)
                for (int i = 0; i < frames * 2; i++)
                {
                    float x = buf[i] * MasterGain;
                    float ax = Math.Abs(x);
                    if (ax > PeakBefore) PeakBefore = ax;
                    if (ax > 1f) OverCount++;
                    if (ax > Ceiling)
                    {
                        float over = ax - Ceiling, room = MaxOutput - Ceiling;
                        ax = Ceiling + room * (float)Math.Tanh(over / room);
                        x = x < 0 ? -ax : ax;
                    }
                    if (ax > PeakAfter) PeakAfter = ax;
                    buf[i] = x;
                }
                _frame += frames;
            }
        }

        /// <summary>Convenience for offline rendering: advance by <paramref name="seconds"/> in blocks, calling <paramref name="perBlock"/> after each.</summary>
        public float[] RenderOffline(double seconds, int block, Action<double> perBlock)
        {
            int total = (int)Math.Round(seconds * SampleRate);
            var all = new float[total * 2];
            var tmp = new float[block * 2];
            int done = 0;
            while (done < total)
            {
                int n = Math.Min(block, total - done);
                Render(tmp, n);
                Array.Copy(tmp, 0, all, done * 2, n * 2);
                done += n;
                perBlock?.Invoke(Time);
            }
            return all;
        }
    }
}
