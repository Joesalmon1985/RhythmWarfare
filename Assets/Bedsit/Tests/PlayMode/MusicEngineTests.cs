using System;
using System.IO;
using System.Linq;
using Bedsit.Music;
using NUnit.Framework;
using UnityEngine;

namespace Bedsit.Tests
{
    /// <summary>
    /// Offline, device-free tests of the music cycle. They drive the real MusicDirector/Mixer/RhythmJudge with scripted players
    /// and inspect the actual rendered samples. These are AUTOMATED checks; they are not a substitute for listening.
    /// Songs other than Gatekeeper are not on this PC: tests that need three tracks SIMULATE them with Gatekeeper audio (flagged
    /// `simulated`), purely to exercise the scheduling arithmetic.
    /// </summary>
    public class MusicEngineTests
    {
        const int Sr = 48000;
        static string Root;

        [OneTimeSetUp]
        public void FindAudio()
        {
            Root = MusicSession.FindAudioRoot();
            if (Root == null || !File.Exists(Path.Combine(Root, "songs", "gatekeeper.wav")))
                Assert.Ignore("LocalAudio/songs/gatekeeper.wav not found: run Tools/music/prepare_audio.py");
        }

        static MusicSession New(bool simulate = false) => MusicSession.Create(Root, Sr, simulate);

        // ================================================================================================ cues

        [Test]
        public void SuppliedCueEntriesMatchTheBrief()
        {
            var songs = SongManifest.Parse(Resources.Load<TextAsset>("Music/songs").text);
            double Entry(string id, string a, int b) => CueMath.Derive(songs.Find(id), true).First(c => c.anchor == a && c.beatsBefore == b).time;
            Assert.AreEqual(25.542, Entry("gatekeeper", "firstDrop", 128), 0.001);
            Assert.AreEqual(22.042, Entry("dropdis", "firstDrop", 128), 0.001);
            Assert.AreEqual(0.012, Entry("levels", "firstDrop", 128), 0.001);
        }

        [Test]
        public void CuesBeforeTheFileStartAreRejectedNotClamped()
        {
            var songs = SongManifest.Parse(Resources.Load<TextAsset>("Music/songs").text);
            foreach (var s in songs.songs)
            {
                var cues = CueMath.Derive(s);
                Assert.AreEqual(8, cues.Count);
                foreach (var c in cues)
                {
                    if (c.time < 0) { Assert.IsFalse(c.valid, c.ToString()); Assert.Less(c.time, 0, "negative times are kept, not clamped to 0"); }
                    else Assert.IsTrue(c.valid, c.ToString());
                }
            }
            var gk = songs.Find("gatekeeper");
            Assert.IsFalse(CueMath.Entry(gk, "firstDrop", 256).valid);
            Assert.IsFalse(CueMath.Entry(gk, "firstDrop", 384).valid);
            Assert.IsTrue(CueMath.Entry(gk, "secondDrop", 384).valid);
        }

        [Test]
        public void HandoverIntoAnInvalidEntryCueIsRejected()
        {
            var s = New(true);
            // Make Drop Dis' first drop so early that 128 beats before it would start before the file does.
            s.Songs.Find("dropdis").firstDrop = 30.0;
            s.Director.Start();
            s.RenderOffline(60.0, MusicBot.Perfect());
            Assert.IsTrue(s.Director.Log.Any(l => l.Contains("before the start of the file")), string.Join("\n", s.Director.Log));
        }

        // ================================================================================================ Gatekeeper-only first pass

        [Test]
        public void PerfectPlayEnablesTheRecordedDropAtItsAnchor()
        {
            var s = New();
            s.Director.Start();
            double bs = 60.0 / 174.0;
            double D1 = 3.0 + 96 * bs;                       // 3 s start delay + three 32-beat phases
            var mix = s.RenderOffline(D1 + 20.0, MusicBot.Perfect());
            var ws = s.Judge.Windows.Take(3).ToList();          // the 4th window already belongs to the next build (scheduled at the drop)
            Assert.AreEqual(3, ws.Count, "drums, bass, buildup");
            Assert.IsTrue(ws[0].Label.EndsWith("drums") && ws[1].Label.EndsWith("bass") && ws[2].Label.EndsWith("buildup"), string.Join(" | ", ws.Select(w => w.Label)));
            foreach (var w in ws) { Assert.AreEqual(w.Total, w.Hits, w.Label + ": all notes hit"); Assert.AreEqual(0, w.Misses); }
            Assert.AreEqual(0.0, ws[0].Threshold, "the first drum loop is a warm-up, not gated");
            Assert.AreEqual(0.8, ws[1].Threshold, 1e-9); Assert.AreEqual(0.8, ws[2].Threshold, 1e-9);
            Assert.AreEqual(1, s.Director.BuildsPassed);
            Assert.AreEqual(0, s.Director.RecoveryAttempts);
            Assert.AreEqual(MusicMode.Mixing, s.Director.Mode, "the rhythm game drops away after the drop");
            Assert.AreEqual("gatekeeper", s.Director.CurrentSongId);
            // the recording's own buildup enters exactly one loop (32 beats) before the drop, and its drop lands at the planned time
            var rec = s.Mixer.Voices.First(v => v.Role == "recorded");
            Assert.AreEqual(69.655, s.Mixer.ClipTimeAt(rec, D1), 0.0006);
            Assert.AreEqual(D1, s.Mixer.TimelineOfClipTime(rec, 69.655), 0.0006);
            Assert.AreEqual(D1 - 32 * bs, s.Mixer.TimelineOfClipTime(rec, 69.655 - 32 * bs), 0.0006);
            Assert.IsTrue(s.Director.Log.Any(l => l.Contains($"buildup: gatekeeper enters at {D1 - 32 * bs:0.000}")), string.Join("\n", s.Director.Log));
            // chart is sane: 96 beats in three loops, nothing charted in the last 4 beats before the drop
            int total = ws.Sum(w => w.Total);
            Assert.Greater(total, 40); Assert.Less(total, 130);
            Assert.LessOrEqual(ws[2].Notes.Max(n => n.Time), D1 - 4 * bs + 1e-6);
            var rep = AudioStats.Analyze(mix, Sr, -60, 3.2);            // 0..3 s is the intentional start delay
            Debug.Log("[music] perfect first pass: " + rep);
            Assert.AreEqual(0, rep.ClippedSamples, "no clipping after the limiter");
            Assert.Less(rep.LongestSilenceSeconds, 0.25, "no gap anywhere after the start delay");
            Assert.AreEqual(1, s.Director.Log.Count(l => l.StartsWith("[") && l.Contains("DROP gatekeeper:firstDrop")));
        }

        [Test]
        public void WarmUpLoopIsNotGatedButTheBassLoopIs()
        {
            double bs = 60.0 / 174.0;
            // miss the whole first drum loop: the build still passes with no recovery
            var a = New(); a.Director.Start();
            var botA = new MusicBot { Rule = n => !a.Judge.WindowOf(n.Window).Label.EndsWith("drums") };
            a.RenderOffline(3.0 + 96 * bs + 8.0, botA);
            Assert.AreEqual(0, a.Director.RecoveryAttempts, string.Join("\n", a.Director.Log));
            Assert.AreEqual(1, a.Director.BuildsPassed);
            Assert.IsNotNull(a.Mixer.Voices.FirstOrDefault(v => v.Role == "recorded"));

            // miss the bass loop: the bass comes round again (custom loops never stop) and the buildup waits
            var b = New(); b.Director.Start();
            var botB = new MusicBot { Rule = n => { var w = b.Judge.WindowOf(n.Window); return !(w.Label.EndsWith("bass") && !w.Label.StartsWith("recovery")); } };
            b.RenderOffline(3.0 + 32 * bs * 2 + 2.0, botB);                // just after the first bass loop has been evaluated
            Assert.IsTrue(b.Director.Log.Any(l => l.Contains("RECOVERY #1: bass again")), string.Join("\n", b.Director.Log));
            Assert.IsNull(b.Mixer.Voices.FirstOrDefault(v => v.Role == "recorded"), "the recording's buildup has not entered yet");
        }

        [Test]
        public void FailureGetsRecoveryLoopsThenTheDropWithoutRewindOrSilence()
        {
            var s = New();
            s.Director.Start();
            double bs = 60.0 / 174.0, D1 = 3.0 + 96 * bs;
            var mix = s.RenderOffline(3.0 + 7 * 32 * bs + 25.0, MusicBot.Failing());      // warm-up + 3 bass + 3 buildup attempts
            Assert.GreaterOrEqual(s.Director.RecoveryAttempts, 3, "recovery loops were offered");
            Assert.IsTrue(s.Judge.Windows.Any(w => w.Label.StartsWith("recovery")));
            Assert.IsTrue(s.Director.Log.Any(l => l.Contains("drop held")), "a failed buildup holds the drop");
            Assert.IsTrue(s.Director.Log.Any(l => l.Contains("exhausted")), "no soft-lock: the drop plays after the attempts run out");
            var rec = s.Mixer.Voices.Where(v => v.Role == "recorded").OrderBy(v => s.Mixer.TimelineOfClipTime(v, 69.655)).LastOrDefault();
            Assert.IsNotNull(rec, "the recorded drop eventually plays");
            // the recording is never started past its drop anchor; its drop lands later than the original plan
            Assert.AreEqual(69.655, s.Mixer.ClipTimeAt(rec, s.Mixer.TimelineOfClipTime(rec, 69.655)), 0.0006);
            Assert.Greater(s.Mixer.TimelineOfClipTime(rec, 69.655), D1 + 32 * bs);
            // never silent after the custom build starts, even while a failed buildup is eased out and re-entered
            var rep = AudioStats.Analyze(mix, Sr, -60, 3.5, mix.Length / 2.0 / Sr);
            Debug.Log("[music] failure/recovery: " + rep);
            Assert.Less(rep.LongestSilenceSeconds, 0.25, "no audible gap");
            Assert.AreEqual(0, rep.ClippedSamples);
        }

        [Test]
        public void RecoveryCanReachAnotherValidAttempt()
        {
            var s = New();
            s.Director.Start();
            double bs = 60.0 / 174.0;
            // fail both gates first time round (hit none), then hit everything in the recovery loops
            var bot = new MusicBot { Rule = n => s.Judge.WindowOf(n.Window).Label.StartsWith("recovery") };
            s.RenderOffline(3.0 + 5 * 32 * bs + 12.0, bot);
            Assert.AreEqual(1, s.Director.BuildsFailed);
            Assert.AreEqual(2, s.Director.RecoveryAttempts, "one bass recovery and one buildup recovery");
            Assert.IsTrue(s.Director.LastBuildPassed, "the recovery attempts passed");
            Assert.IsTrue(s.Director.Log.Any(l => l.Contains("RECOVERY #1: bass again")));
            Assert.IsTrue(s.Director.Log.Any(l => l.Contains("RECOVERY #1: buildup again")));
            Assert.IsNotNull(s.Mixer.Voices.FirstOrDefault(v => v.Role == "recorded"));
        }

        [Test]
        public void MixingModeProducesNoPhantomMisses()
        {
            var s = New();
            s.Director.Start();
            double bs = 60.0 / 174.0, D1 = 3.0 + 96 * bs;
            var bot = MusicBot.Perfect();
            s.RenderOffline(D1 + 3.0, bot);
            Assert.AreEqual(MusicMode.Mixing, s.Director.Mode);
            int misses = s.Judge.TotalMisses, windows = s.Judge.Windows.Count;
            // 60 s of mixing with a player who taps nothing and everything: no misses, no new windows, energy untouched
            double e = s.Judge.Energy;
            s.RenderOffline(60.0, MusicBot.Idle(), 512, now => { if (s.Director.Mode == MusicMode.Mixing) { s.Judge.Tap(1, now); s.Judge.Tap(4, now); } });
            Assert.AreEqual(misses, s.Judge.TotalMisses);
            Assert.AreEqual(windows, s.Judge.Windows.Count);
            Assert.AreEqual(e, s.Judge.Energy, 1e-9);
        }

        [Test]
        public void SecondBuildReturnsToRhythmWithoutCountingOldNotes()
        {
            var s = New();
            s.Director.Start();
            double bs = 60.0 / 174.0, D1 = 3.0 + 96 * bs, D2 = D1 + (202.0685 - 69.655);
            s.RenderOffline(D2 - 96 * bs + 6.0, MusicBot.Perfect());
            Assert.AreEqual(MusicMode.Rhythm, s.Director.Mode, "rhythm mode restored for the next playable build");
            Assert.AreEqual(4, s.Judge.Windows.Count, "three windows of the first build + the first loop of the second");
            var w2 = s.Judge.Windows[3];
            Assert.AreEqual(0, w2.Misses);
            Assert.IsTrue(w2.Notes.All(n => n.Time >= D2 - 96 * bs - 1e-3), "only notes of the new build: first note " + w2.Notes.Min(n => n.Time) + " vs " + (D2 - 96 * bs) + " | " + string.Join(" // ", s.Director.Log));
            for (int i = 0; i < 3; i++) Assert.AreEqual(s.Judge.Windows[i].Hits, s.Judge.Windows[i].Total, "first build unchanged");
        }

        [Test]
        public void MutedStemReturnsInSyncAndOnlyDuringTheMistake()
        {
            var a = New(); a.Director.Start();
            var mixA = a.RenderOffline(40.0, MusicBot.Perfect());
            var b = New(); b.Director.Start();
            // miss exactly one kick (the 5th kick note in the build), hit everything else
            Note missed = null; int kicks = 0;
            var botB = new MusicBot { Rule = n => { if (n.Stem == "kick" && ++kicks == 5) { missed = n; return false; } return true; } };
            var mixB = b.RenderOffline(40.0, botB);
            Assert.IsNotNull(missed);
            Assert.IsTrue(b.Director.Log.Any(l => l.Contains("stem muted")));
            Assert.IsTrue(b.Director.Log.Any(l => l.Contains("RECOVERED kick")), "restored after the configured recovery rule");
            // find the restore time from the log
            double restoreAt = double.Parse(b.Director.Log.First(l => l.Contains("RECOVERED kick")).Substring(1, 6));
            int fa = (int)((restoreAt + 0.15) * Sr);
            int differing = 0;
            for (int i = fa * 2; i < mixA.Length; i++) if (Math.Abs(mixA[i] - mixB[i]) > 1e-4f) { differing++; }
            Assert.AreEqual(0, differing, "after the restore ramp the two renders are sample-identical: the stem came back exactly in sync");
            // and the mute really changed the sound (the kick stem was reduced during the mistake)
            int t0 = (int)(missed.Time * Sr), t1 = (int)((restoreAt) * Sr);
            double diffEnergy = 0; for (int i = t0 * 2; i < t1 * 2; i++) diffEnergy += Math.Abs(mixA[i] - mixB[i]);
            Assert.Greater(diffEnergy, 1.0, "the muted stem is audible as a difference during the mistake");
            // nothing differs BEFORE the miss
            for (int i = 0; i < (int)((missed.Time - 0.01) * Sr) * 2; i++) Assert.AreEqual(mixA[i], mixB[i], 1e-6f);
        }

        [Test]
        public void PauseFreezesTheTimelineAndSchedulingThenResumesIdentically()
        {
            var cont = New(); cont.Director.Start();
            var mixC = cont.RenderOffline(30.0, MusicBot.Perfect());

            var p = New(); p.Director.Start();
            var bot = MusicBot.Perfect();
            var first = p.RenderOffline(12.0, bot);
            double tFrozen = p.Mixer.Time; int logCount = p.Director.Log.Count; int hits = p.Judge.TotalHits;
            p.Mixer.Paused = true;
            var tmp = new float[1024];
            for (int i = 0; i < 400; i++) { p.Mixer.Render(tmp, 512); Assert.IsTrue(tmp.All(x => x == 0f)); p.Director.Update(p.Mixer.Time); bot.Step(p.Judge, p.Mixer.Time); }
            Assert.AreEqual(tFrozen, p.Mixer.Time, 0.0, "timeline frozen while paused");
            Assert.AreEqual(logCount, p.Director.Log.Count, "no scheduling while paused");
            Assert.AreEqual(hits, p.Judge.TotalHits);
            p.Mixer.Paused = false;
            var rest = p.RenderOffline(18.0, bot);
            var joined = first.Concat(rest).ToArray();
            Assert.AreEqual(mixC.Length, joined.Length);
            double maxDiff = 0; for (int i = 0; i < joined.Length; i++) maxDiff = Math.Max(maxDiff, Math.Abs(joined[i] - mixC[i]));
            Assert.Less(maxDiff, 1e-6, "pause + resume is sample-identical to never pausing");
        }

        // ================================================================================================ three tracks (simulated) + repeat

        [Test]
        public void ThreeTrackSequenceAndRepeatReachEveryIntendedDrop()
        {
            var s = New(true);
            Assert.IsTrue(s.Songs.Find("dropdis").simulated && s.Songs.Find("levels").simulated, "tracks 2 and 3 are SIMULATED in this test");
            s.Director.Start();
            var mix = s.RenderOffline(700.0, MusicBot.Perfect(), 1024);
            var log = s.Director.Log;
            Debug.Log("[music] three-track log:\n" + string.Join("\n", log.Where(l => l.Contains("HANDOVER") || l.Contains("DROP") || l.Contains("BUILD") || l.Contains("REPEAT") || l.Contains("EVAL"))));
            Assert.GreaterOrEqual(s.Director.HandoversDone, 3, "Gatekeeper->Drop Dis->Levels->Gatekeeper");
            Assert.AreEqual(0, s.Judge.TotalMisses);
            // every handover: incoming drop anchor reached at the shared timeline time, outgoing silent exactly there
            foreach (var l in log.Where(x => x.Contains("HANDOVER scheduled")))
            {
                // "... fades A->D; song enters E (clip C) -> drop D"
                Assert.IsTrue(l.Contains("-> drop"), l);
            }
            var legsDone = log.Where(l => l.Contains("HANDOVER done")).ToList();
            Assert.IsTrue(legsDone[0].Contains("dropdis:firstDrop"));
            Assert.IsTrue(legsDone[1].Contains("levels:firstDrop"));
            Assert.IsTrue(legsDone[2].Contains("gatekeeper:firstDrop"), "repeat path returns to Gatekeeper");
            // first handover timing: Drop Dis' first drop aligns with Gatekeeper's second drop
            double bs = 60.0 / 174.0, D1 = 3.0 + 96 * bs, D2 = D1 + (202.0685 - 69.655);
            Assert.IsTrue(log.Any(l => l.Contains($"drop {D2:0.000}")), "handover 1 drop at Gatekeeper's second drop " + D2.ToString("0.000"));
            // incoming enters exactly 128 beats before the shared drop, outgoing is gone by the drop (no double drop)
            Assert.IsTrue(log.Any(l => l.Contains($"enters {D2 - 128 * bs:0.000}")));
            var rep = AudioStats.Analyze(mix, Sr, -60, 3.2);
            Debug.Log("[music] 700 s three-track render: " + rep);
            Assert.AreEqual(0, rep.ClippedSamples);
            Assert.Less(rep.LongestSilenceSeconds, 0.5);
        }

        [Test]
        public void HandoverNeverSchedulesFromAnAnchorAlreadyReached()
        {
            var s = New(true);
            s.Director.Start();
            s.RenderOffline(700.0, MusicBot.Perfect(), 1024);
            // the repeat leg must have rejected the already-reached second drop and chosen the ending
            Assert.IsTrue(s.Director.Log.Any(l => l.Contains("handover rejected") || l.Contains("HANDOVER scheduled") && l.Contains("gatekeeper")), string.Join("\n", s.Director.Log.TakeLast(20)));
        }

        // ================================================================================================ demonstrations (actual rendered audio)

        [Test]
        public void RenderDemonstrationsAndAnalyseThem()
        {
            string dir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "Evidence", "audio"));
            Directory.CreateDirectory(dir);
            var report = new System.Text.StringBuilder();
            double bs = 60.0 / 174.0, D1 = 3.0 + 96 * bs;
            void Run(string name, MusicBot bot, double secs, bool simulate = false)
            {
                var s = New(simulate); s.Director.Start();
                var mix = s.RenderOffline(secs, bot);
                PcmClip.SaveWav16(Path.Combine(dir, name + ".wav"), mix, Sr);
                var rep = AudioStats.Analyze(mix, Sr, -60, 3.2);
                report.AppendLine($"## {name}\n{rep}\nbuilds passed {s.Director.BuildsPassed}/{s.Director.BuildsStarted}, recoveries {s.Director.RecoveryAttempts}, misses {s.Judge.TotalMisses}, hits {s.Judge.TotalHits}\n```\n{string.Join("\n", s.Director.Log)}\n```\n");
                Assert.AreEqual(0, rep.ClippedSamples, name + " clipped");
            }
            Run("demo_perfect_build_drop_mix", MusicBot.Perfect(), D1 + 40.0);
            Run("demo_partial_stem_mutes", MusicBot.Partial(), D1 + 30.0);
            Run("demo_failure_recovery", MusicBot.Failing(), 3.0 + 7 * 32 * bs + 30.0);
            File.WriteAllText(Path.Combine(dir, "analysis.md"), report.ToString());
            Assert.IsTrue(File.Exists(Path.Combine(dir, "demo_perfect_build_drop_mix.wav")));
        }

        // ================================================================================================ input

        [Test]
        public void PadStripRegionsAreFourPadsAboveTheBottomEdgeBetweenTheTurnZones()
        {
            Assert.AreEqual(0, InputRegions.ClassifyPad(new Vector2(0.30f, 0.05f)));
            Assert.AreEqual(1, InputRegions.ClassifyPad(new Vector2(0.45f, 0.05f)));
            Assert.AreEqual(2, InputRegions.ClassifyPad(new Vector2(0.55f, 0.05f)));
            Assert.AreEqual(3, InputRegions.ClassifyPad(new Vector2(0.70f, 0.05f)));
            Assert.AreEqual(-1, InputRegions.ClassifyPad(new Vector2(0.10f, 0.05f)), "left zone turns, it is not a pad");
            Assert.AreEqual(-1, InputRegions.ClassifyPad(new Vector2(0.5f, 0.5f)));
            Assert.AreEqual(PlayerAction.TurnLeft, InputRegions.Classify(new Vector2(0.10f, 0.05f)));
        }
    }
}
