using System;

namespace Bedsit.Music
{
    /// <summary>A synthesized wooden door knock (no sample needed): a low body thump with a faster upper resonance and a short noisy
    /// "tick" at the start. Played three times, on beats 0, 1 and 2 of the drop.</summary>
    public static class KnockSynth
    {
        public static PcmClip Make(int sampleRate, double seconds = 0.42)
        {
            int frames = (int)(seconds * sampleRate);
            var d = new float[frames * 2];
            var rng = new Random(11);
            double phaseA = 0, phaseB = 0, noiseLp = 0;
            for (int i = 0; i < frames; i++)
            {
                double t = i / (double)sampleRate;
                double fA = 105 + 85 * Math.Exp(-t * 55);                 // body: pitch falls from ~190 Hz to ~105 Hz
                double fB = 330 + 120 * Math.Exp(-t * 70);                // upper wood resonance
                phaseA += 2 * Math.PI * fA / sampleRate; phaseB += 2 * Math.PI * fB / sampleRate;
                double body = Math.Sin(phaseA) * Math.Exp(-t * 17);
                double wood = Math.Sin(phaseB) * Math.Exp(-t * 40) * 0.45;
                double noise = (rng.NextDouble() * 2 - 1);
                noiseLp += (noise - noiseLp) * 0.45;                      // gently low-passed noise
                double tick = noiseLp * Math.Exp(-t * 420) * 0.9;
                double attack = Math.Min(1.0, t / 0.0015);                // 1.5 ms ramp: no click at sample 0
                float v = (float)((body + wood + tick) * attack);
                d[i * 2] = v; d[i * 2 + 1] = v;
            }
            double peak = 0; foreach (var x in d) peak = Math.Max(peak, Math.Abs(x));
            float g = peak > 0 ? (float)(0.85 / peak) : 1f;
            for (int i = 0; i < d.Length; i++) d[i] *= g;
            return new PcmClip { Data = d, Frames = frames, SampleRate = sampleRate, Name = "knock(synth)" };
        }
    }
}
