using System.Collections.Generic;
using UnityEngine;

namespace Bedsit.Game
{
    /// <summary>Tiny synthesised effects for tidying (no sound assets): rustle, thunk, clink, paper, bin, zip, chime.
    /// Deterministic (seeded) so tests/recordings are repeatable.</summary>
    public static class SfxSynth
    {
        const int Rate = 44100;
        static readonly Dictionary<string, AudioClip> Cache = new Dictionary<string, AudioClip>();

        public static AudioClip Get(string name)
        {
            if (string.IsNullOrEmpty(name)) name = "thunk";
            if (Cache.TryGetValue(name, out var c) && c != null) return c;
            float[] d;
            switch (name)
            {
                case "rustle": d = Noise(0.42f, 0.55f, 900f, 0.07f, 11); break;
                case "paper": d = Crinkle(0.5f, 12); break;
                case "clink": d = Clink(13); break;
                case "bin": d = Bin(14); break;
                case "zip": d = Zip(0.38f, 15); break;
                case "chime": d = Chime(); break;
                default: d = Thunk(0.28f, 95f, 16); break;
            }
            c = AudioClip.Create("sfx_" + name, d.Length, 1, Rate, false);
            c.SetData(d, 0);
            Cache[name] = c;
            return c;
        }

        public static void Play(string name, Vector3 at, float volume = 0.6f)
        {
            var go = new GameObject("sfx_" + name);
            go.transform.position = at;
            var a = go.AddComponent<AudioSource>();
            a.clip = Get(name);
            a.volume = volume;
            a.spatialBlend = 0.35f;
            a.Play();
            Object.Destroy(go, a.clip.length + 0.2f);
        }

        static float[] Noise(float dur, float peak, float lp, float attack, int seed)
        {
            var r = new System.Random(seed);
            int n = (int)(dur * Rate); var d = new float[n]; float lpState = 0f;
            float k = Mathf.Clamp01(lp / Rate * 6.2831f);
            for (int i = 0; i < n; i++)
            {
                float t = i / (float)Rate;
                float env = Mathf.Min(1f, t / attack) * Mathf.Exp(-t * 7f);
                float w = (float)(r.NextDouble() * 2.0 - 1.0);
                lpState += k * (w - lpState);
                // soft amplitude flutter = fabric movement
                float flutter = 0.65f + 0.35f * Mathf.Sin(t * 42f + Mathf.Sin(t * 17f) * 2f);
                d[i] = lpState * env * flutter * peak * 2.4f;
            }
            return d;
        }

        static float[] Crinkle(float dur, int seed)
        {
            var r = new System.Random(seed);
            int n = (int)(dur * Rate); var d = new float[n];
            for (int burst = 0; burst < 9; burst++)
            {
                int start = (int)(r.NextDouble() * (n - 2000));
                int len = 300 + r.Next(900);
                float amp = 0.25f + (float)r.NextDouble() * 0.4f;
                float hp = 0f;
                for (int i = 0; i < len && start + i < n; i++)
                {
                    float w = (float)(r.NextDouble() * 2.0 - 1.0);
                    float y = w - hp; hp += 0.35f * y;               // crude high-pass
                    d[start + i] += y * amp * Mathf.Exp(-i / (len * 0.35f));
                }
            }
            return d;
        }

        static float[] Thunk(float dur, float freq, int seed)
        {
            int n = (int)(dur * Rate); var d = new float[n];
            for (int i = 0; i < n; i++)
            {
                float t = i / (float)Rate;
                float f = freq * (1f + 0.6f * Mathf.Exp(-t * 28f));
                d[i] = Mathf.Sin(2f * Mathf.PI * f * t) * Mathf.Exp(-t * 16f) * 0.9f;
            }
            return d;
        }

        static float[] Clink(int seed)
        {
            int n = (int)(0.45f * Rate); var d = new float[n];
            float[] fr = { 2840f, 4210f, 5630f };
            for (int i = 0; i < n; i++)
            {
                float t = i / (float)Rate; float s = 0f;
                for (int k = 0; k < fr.Length; k++) s += Mathf.Sin(2f * Mathf.PI * fr[k] * t) * Mathf.Exp(-t * (14f + k * 9f)) / (k + 1.2f);
                d[i] = s * 0.55f;
            }
            return d;
        }

        static float[] Bin(int seed)
        {
            var thunk = Thunk(0.34f, 70f, seed);
            var rustle = Noise(0.3f, 0.35f, 2500f, 0.01f, seed + 1);
            int n = Mathf.Max(thunk.Length, rustle.Length + 4000); var d = new float[n];
            for (int i = 0; i < thunk.Length; i++) d[i] += thunk[i];
            for (int i = 0; i < rustle.Length; i++) d[i + 3000] += rustle[i];
            // lid clack
            var cl = Clink(seed + 2);
            for (int i = 0; i < cl.Length && i + 9000 < n; i++) d[i + 9000] += cl[i] * 0.35f;
            return d;
        }

        static float[] Zip(float dur, int seed)
        {
            int n = (int)(dur * Rate); var d = new float[n];
            var r = new System.Random(seed);
            for (int i = 0; i < n; i++)
            {
                float t = i / (float)Rate; float k = t / dur;
                float tick = Mathf.Sin(2f * Mathf.PI * (900f + 1800f * k) * t) * ((i / 90) % 2 == 0 ? 1f : 0.2f);
                d[i] = (tick * 0.25f + (float)(r.NextDouble() * 2 - 1) * 0.05f) * Mathf.Min(1f, t * 40f) * Mathf.Min(1f, (dur - t) * 25f);
            }
            return d;
        }

        static float[] Chime()
        {
            int n = (int)(0.9f * Rate); var d = new float[n];
            float[] f = { 880f, 1318.5f, 1760f };
            for (int i = 0; i < n; i++)
            {
                float t = i / (float)Rate; float s = 0f;
                for (int k = 0; k < f.Length; k++) { float st = k * 0.07f; if (t > st) s += Mathf.Sin(2f * Mathf.PI * f[k] * (t - st)) * Mathf.Exp(-(t - st) * 5f) / (k + 1.5f); }
                d[i] = s * 0.5f;
            }
            return d;
        }
    }
}
