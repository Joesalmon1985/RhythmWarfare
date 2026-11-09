using System;
using System.Collections.Generic;

namespace Bedsit.Music
{
    public enum NoteState { Pending, Hit, Missed }

    public sealed class Note
    {
        public double Time;           // timeline seconds
        public int Pad;               // 1..4
        public string Stem;           // kick | snare | bass
        public int Window;            // judge window id
        public NoteState State;
        public double HitDelta;       // seconds (hit time - note time)
        public bool Perfect;
    }

    /// <summary>A judged stretch of the timeline (a playable build or a recovery phrase). Only notes inside a window are ever judged.</summary>
    public sealed class JudgeWindow
    {
        public int Id;
        public string Label;
        public double Start, End;     // timeline seconds covered by the window
        public double Threshold;
        public readonly List<Note> Notes = new List<Note>();
        public int Hits, Misses;
        public bool Closed;
        public int Total => Notes.Count;
        public double Accuracy => Notes.Count == 0 ? 1.0 : Hits / (double)Notes.Count;
        public int Pending => Notes.Count - Hits - Misses;
    }

    /// <summary>
    /// Judges pad taps against the notes of the active windows. In MIXING mode there are no windows, so there is nothing to
    /// miss: no phantom misses, no energy loss. Stray taps outside a window are ignored.
    /// </summary>
    public sealed class RhythmJudge
    {
        public double PerfectWindow = 0.045, GoodWindow = 0.09;
        public readonly List<JudgeWindow> Windows = new List<JudgeWindow>();
        public bool Enabled = true;

        public int TotalHits, TotalMisses, StrayTaps;
        public double Energy = 1.0;                       // 0..1, only moves while judging
        public event Action<Note> NoteHit, NoteMissed;

        int _nextId = 1;

        public JudgeWindow AddWindow(string label, double start, double end, double threshold, IEnumerable<Note> notes)
        {
            var w = new JudgeWindow { Id = _nextId++, Label = label, Start = start, End = end, Threshold = threshold };
            foreach (var n in notes) { n.Window = w.Id; w.Notes.Add(n); }
            w.Notes.Sort((a, b) => a.Time.CompareTo(b.Time));
            Windows.Add(w);
            return w;
        }

        public JudgeWindow ActiveWindow(double now)
        {
            foreach (var w in Windows) if (!w.Closed && now >= w.Start - 0.001 && now <= w.End + GoodWindow) return w;
            return null;
        }

        public IEnumerable<Note> PendingNotes(double now, double horizon)
        {
            foreach (var w in Windows)
            {
                if (w.Closed) continue;
                foreach (var n in w.Notes) if (n.State == NoteState.Pending && n.Time >= now - GoodWindow && n.Time <= now + horizon) yield return n;
            }
        }

        /// <summary>A pad was tapped at timeline time <paramref name="now"/>. Returns the note it matched (or null).</summary>
        public Note Tap(int pad, double now)
        {
            if (!Enabled) { StrayTaps++; return null; }
            Note best = null; double bestD = double.MaxValue;
            foreach (var w in Windows)
            {
                if (w.Closed) continue;
                foreach (var n in w.Notes)
                {
                    if (n.State != NoteState.Pending || n.Pad != pad) continue;
                    double d = Math.Abs(n.Time - now);
                    if (d <= GoodWindow && d < bestD) { best = n; bestD = d; }
                }
            }
            if (best == null) { StrayTaps++; return null; }
            best.State = NoteState.Hit; best.HitDelta = now - best.Time; best.Perfect = bestD <= PerfectWindow;
            var win = WindowOf(best.Window); win.Hits++; TotalHits++;
            Energy = Math.Min(1.0, Energy + 0.02);
            NoteHit?.Invoke(best);
            return best;
        }

        public void Update(double now)
        {
            if (!Enabled) return;
            foreach (var w in Windows)
            {
                if (w.Closed) continue;
                foreach (var n in w.Notes)
                {
                    if (n.State == NoteState.Pending && now > n.Time + GoodWindow)
                    {
                        n.State = NoteState.Missed; w.Misses++; TotalMisses++;
                        Energy = Math.Max(0.0, Energy - 0.08);
                        NoteMissed?.Invoke(n);
                    }
                }
            }
        }

        public JudgeWindow WindowOf(int id) { foreach (var w in Windows) if (w.Id == id) return w; return null; }
        public void Close(JudgeWindow w) { w.Closed = true; }
    }
}
