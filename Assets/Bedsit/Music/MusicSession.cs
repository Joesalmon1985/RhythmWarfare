using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace Bedsit.Music
{
    /// <summary>Scripted player for tests and demos: decides per note whether to hit it (deterministic, seeded).</summary>
    public sealed class MusicBot
    {
        public double HitRate = 1.0;
        public double JitterSeconds = 0.0;
        public Func<Note, bool> Rule;                 // optional override: return true to hit
        readonly System.Random _rng;
        readonly HashSet<Note> _done = new HashSet<Note>();
        public int Hit, Skipped;

        public MusicBot(int seed = 7) { _rng = new System.Random(seed); }

        public static MusicBot Perfect() => new MusicBot { HitRate = 1.0 };
        /// <summary>Hits about 85 % (misses are spread out), so it passes the 80 % threshold but mutes stems along the way.</summary>
        public static MusicBot Partial() => new MusicBot(3) { HitRate = 0.88, JitterSeconds = 0.02 };
        public static MusicBot Failing() => new MusicBot(5) { HitRate = 0.35, JitterSeconds = 0.03 };
        public static MusicBot Idle() => new MusicBot { HitRate = 0.0 };

        public void Step(RhythmJudge judge, double now)
        {
            foreach (var w in judge.Windows)
            {
                if (w.Closed) continue;
                foreach (var n in w.Notes)
                {
                    if (n.State != NoteState.Pending || n.Time > now || _done.Contains(n)) continue;
                    _done.Add(n);
                    bool hit = Rule != null ? Rule(n) : _rng.NextDouble() < HitRate;
                    if (!hit) { Skipped++; continue; }
                    double jitter = (_rng.NextDouble() * 2 - 1) * JitterSeconds;
                    judge.Tap(n.Pad, n.Time + jitter);
                    Hit++;
                }
            }
        }
    }

    public struct AudioReport
    {
        public double Seconds, PeakLinear, RmsDb, LongestSilenceSeconds, LongestSilenceStart, MaxStepJump;
        public long ClippedSamples, ClickCandidates;
        public int SilenceRunsOver250ms;
        public override string ToString() => $"{Seconds:0.0}s peak {20 * Math.Log10(Math.Max(PeakLinear, 1e-9)):0.0} dBFS, rms {RmsDb:0.0} dB, clipped samples {ClippedSamples}, longest silence {LongestSilenceSeconds:0.00}s at {LongestSilenceStart:0.00}s, silences>250ms {SilenceRunsOver250ms}, max sample step {MaxStepJump:0.00}";
    }

    public static class AudioStats
    {
        public static AudioReport Analyze(float[] buf, int sr, double silenceDb = -60.0, double fromSeconds = 0, double toSeconds = -1)
        {
            int frames = buf.Length / 2;
            int f0 = (int)(fromSeconds * sr), f1 = toSeconds < 0 ? frames : Math.Min(frames, (int)(toSeconds * sr));
            var r = new AudioReport { Seconds = (f1 - f0) / (double)sr };
            double sum = 0; int win = sr / 100;        // 10 ms silence windows
            double thr = Math.Pow(10, silenceDb / 20.0);
            int run = 0; int longest = 0; int runs250 = 0; int longestStart = 0;
            double prevL = 0, prevR = 0;
            for (int f = f0; f < f1; f++)
            {
                double l = buf[f * 2], rr = buf[f * 2 + 1];
                double a = Math.Max(Math.Abs(l), Math.Abs(rr));
                if (a > r.PeakLinear) r.PeakLinear = a;
                if (a >= 0.999) r.ClippedSamples++;
                sum += l * l + rr * rr;
                double jump = Math.Max(Math.Abs(l - prevL), Math.Abs(rr - prevR));
                if (f > f0 && jump > r.MaxStepJump) r.MaxStepJump = jump;
                if (f > f0 && jump > 0.6) r.ClickCandidates++;
                prevL = l; prevR = rr;
            }
            for (int w = f0; w + win <= f1; w += win)
            {
                double s = 0; for (int i = 0; i < win; i++) { double l = buf[(w + i) * 2], rr = buf[(w + i) * 2 + 1]; s += l * l + rr * rr; }
                double rms = Math.Sqrt(s / (2.0 * win));
                if (rms < thr) { run++; if (run > longest) { longest = run; longestStart = (w - f0) / win - run + 1; } }
                else { if (run * 0.01 >= 0.25) runs250++; run = 0; }
            }
            if (run * 0.01 >= 0.25) runs250++;
            r.RmsDb = 10 * Math.Log10(Math.Max(sum / Math.Max(1, (f1 - f0) * 2.0), 1e-12));
            r.LongestSilenceSeconds = longest * 0.01;
            r.LongestSilenceStart = fromSeconds + longestStart * 0.01;
            r.SilenceRunsOver250ms = runs250;
            return r;
        }

        /// <summary>RMS (linear) of a time window of a rendered buffer.</summary>
        public static double Rms(float[] buf, int sr, double t0, double t1)
        {
            int a = (int)(t0 * sr), b = Math.Min(buf.Length / 2, (int)(t1 * sr));
            double s = 0; int n = 0;
            for (int f = Math.Max(0, a); f < b; f++) { s += buf[f * 2] * (double)buf[f * 2] + buf[f * 2 + 1] * (double)buf[f * 2 + 1]; n += 2; }
            return n == 0 ? 0 : Math.Sqrt(s / n);
        }
    }

    /// <summary>Everything needed to run the music cycle: manifests, decoded audio, mixer, judge, director.</summary>
    public sealed class MusicSession
    {
        public Mixer Mixer;
        public RhythmJudge Judge;
        public MusicDirector Director;
        public SongManifest Songs;
        public PlanDef Plan;
        public LoopManifest Loops;
        public readonly Dictionary<string, PcmClip> SongPcm = new Dictionary<string, PcmClip>();
        public readonly Dictionary<string, PcmClip> StemPcm = new Dictionary<string, PcmClip>();
        public readonly List<string> Problems = new List<string>();
        public string AudioRoot;

        static readonly Dictionary<string, PcmClip> Cache = new Dictionary<string, PcmClip>();
        static PcmClip Cached(string path, int sr)
        {
            var key = path + "@" + sr;
            lock (Cache) { if (Cache.TryGetValue(key, out var c)) return c; c = PcmClip.LoadWav(path).Resampled(sr); Cache[key] = c; return c; }
        }

        /// <summary>Folder holding songs/*.wav and loops/*.wav (see Tools/music/prepare_audio.py). Null if not found.</summary>
        public static string FindAudioRoot()
        {
            var env = Environment.GetEnvironmentVariable("BEDSIT_AUDIO_DIR");
            var cands = new List<string>();
            if (!string.IsNullOrEmpty(env)) cands.Add(env);
            cands.Add(Path.GetFullPath(Path.Combine(Application.dataPath, "..", "LocalAudio")));
            cands.Add(Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "LocalAudio")));
            cands.Add(Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "..", "LocalAudio")));   // exe in Builds/Windows -> project root
            cands.Add(Path.Combine(Environment.CurrentDirectory, "LocalAudio"));
            foreach (var c in cands) if (Directory.Exists(c)) return c;
            return null;
        }

        /// <param name="simulateMissingSongs">TEST ONLY: unavailable songs are backed by the Gatekeeper audio so the three-track scheduling can be exercised. Never used for the real game.</param>
        public static MusicSession Create(string audioRoot, int sampleRate = 48000, bool simulateMissingSongs = false, Action<SongManifest> tweak = null)
        {
            var s = new MusicSession { AudioRoot = audioRoot };
            s.Songs = SongManifest.Parse(Resources.Load<TextAsset>("Music/songs").text);
            s.Plan = PlanDef.Parse(Resources.Load<TextAsset>("Music/plan").text);
            s.Loops = LoopManifest.Parse(Resources.Load<TextAsset>("Music/loops").text);
            foreach (var song in s.Songs.songs)
            {
                if (string.IsNullOrEmpty(song.file)) continue;
                var path = Path.Combine(audioRoot, song.file.Replace('/', Path.DirectorySeparatorChar));
                if (!File.Exists(path)) { song.available = false; s.Problems.Add($"missing audio for {song.id}: {path}"); continue; }
                s.SongPcm[song.id] = Cached(path, sampleRate);
            }
            if (simulateMissingSongs && s.SongPcm.TryGetValue("gatekeeper", out var gk))
            {
                foreach (var song in s.Songs.songs)
                    if (!s.SongPcm.ContainsKey(song.id)) { s.SongPcm[song.id] = gk; song.available = true; song.simulated = true; song.durationSeconds = gk.Seconds; }
            }
            foreach (var st in s.Loops.stems)
            {
                var path = Path.Combine(audioRoot, st.file.Replace('/', Path.DirectorySeparatorChar));
                if (!File.Exists(path)) { s.Problems.Add("missing stem " + path); continue; }
                s.StemPcm[st.id] = Cached(path, sampleRate);
            }
            tweak?.Invoke(s.Songs);
            s.Mixer = new Mixer(sampleRate);
            s.Judge = new RhythmJudge();
            s.Director = new MusicDirector(s.Mixer, s.Judge, s.Songs, s.Plan, s.Loops, s.SongPcm, s.StemPcm);
            s.Director.KnockClip = KnockSynth.Make(sampleRate);
            return s;
        }

        /// <summary>Render offline (no audio device): the bot plays, the director schedules, exactly as in the game.</summary>
        public float[] RenderOffline(double seconds, MusicBot bot, int block = 512, Action<double> perBlock = null)
        {
            return Mixer.RenderOffline(seconds, block, now =>
            {
                bot?.Step(Judge, now);
                Director.Update(now);
                perBlock?.Invoke(now);
            });
        }
    }
}
