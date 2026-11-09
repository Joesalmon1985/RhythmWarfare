using System;
using System.Collections.Generic;
using UnityEngine;

namespace Bedsit.Music
{
    /// <summary>One recording: where the file is, its tempo/beat grid and the three anchors (see Resources/Music/songs.json).</summary>
    [Serializable]
    public class SongDef
    {
        public string id, title, artist, file, key, stems, bpmEvidence;
        public bool available, bpmVerifiedFromAudio, preciseAnchors, simulated;
        public double bpm, beatOrigin, durationSeconds;
        public double ownerFirstDrop, ownerSecondDrop, ownerEnding;
        public double firstDrop, secondDrop, ending;

        public double BeatSeconds => 60.0 / bpm;

        public double Anchor(string name)
        {
            switch (name)
            {
                case "firstDrop": return firstDrop;
                case "secondDrop": return secondDrop;
                case "ending": return ending;
                default: throw new ArgumentException("unknown anchor " + name);
            }
        }
    }

    [Serializable]
    public class SongManifest
    {
        public string format, notes;
        public SongDef[] songs;
        public SongDef Find(string id) { foreach (var s in songs) if (s.id == id) return s; return null; }
        public static SongManifest Parse(string json) => JsonUtility.FromJson<SongManifest>(json);
    }

    [Serializable]
    public class PlanSettings
    {
        public double threshold = 0.8, recoveryThreshold = 0.6;
        public int buildBeats = 128, recoveryBeats = 32, maxRecoveryAttempts = 3;
        public double fadeOutBeats = 32, customFadeBeats = 1, customFadeInBeats = 4, recordedFadeBeatsAtBuild = 4;
        public double stemMuteRampSeconds = 0.03, stemRestoreRampSeconds = 0.08;
        public float stemMuteLevel = 0.15f;              // gain a mistaken stem is REDUCED to (0 = full mute)
        public int restoreAfterHits = 2;
        public double prepMarginBeats = 8, evalLeadSeconds = 0.2, startDelaySeconds = 3.0;
        public double judgePerfectSeconds = 0.045, judgeGoodSeconds = 0.09;
        public float customGain = 0.8f, recordedGain = 0.9f;
    }

    [Serializable]
    public class BuildLoopDef { public string[] charted, audible; }

    [Serializable]
    public class LegDef
    {
        public string id, type, song, anchor, from, fromAnchor, to, toAnchor;
        public string[] outgoingCandidates;
        public string fallbackType, fallbackSong, fallbackAnchor;     // flat: JsonUtility cannot deserialize a nested LegDef
    }

    [Serializable]
    public class PlanDef
    {
        public string format, notes;
        public PlanSettings settings;
        public string[] order;
        public BuildLoopDef[] buildLoops;
        public LegDef[] legs;
        public static PlanDef Parse(string json) => JsonUtility.FromJson<PlanDef>(json);
    }

    [Serializable]
    public class LoopCue { public int tick, pad; }

    [Serializable]
    public class LoopStemDef { public string id, clip, part, sound, file, key; public LoopCue[] cues; }

    [Serializable]
    public class LoopManifest
    {
        public string format, source;
        public int ticksPerBeat;
        public int loopBeats;
        public LoopStemDef[] stems;
        public LoopStemDef Find(string id) { foreach (var s in stems) if (s.id == id) return s; return null; }
        public static LoopManifest Parse(string json) => JsonUtility.FromJson<LoopManifest>(json);
    }

    public struct Cue
    {
        public string song, anchor;
        public int beatsBefore;
        public double time;
        public bool valid;
        public string reason;
        public override string ToString() => $"{song} {anchor} -{beatsBefore} beats = {time:0.000}s {(valid ? "VALID" : "INVALID: " + reason)}";
    }

    /// <summary>Entry-point maths. Cues that would start before the file does are INVALID (never clamped to 0).</summary>
    public static class CueMath
    {
        public static readonly (string anchor, int[] beats)[] Candidates =
        {
            ("firstDrop", new[] { 128, 256, 384 }),
            ("secondDrop", new[] { 128, 256, 384 }),
            ("ending", new[] { 128, 256 }),
        };

        /// <param name="useOwnerTimestamps">true = the supplied reference timestamps, false = the precise anchors used for alignment.</param>
        public static List<Cue> Derive(SongDef s, bool useOwnerTimestamps = false)
        {
            var list = new List<Cue>();
            foreach (var (anchor, beats) in Candidates)
            {
                double a = useOwnerTimestamps
                    ? (anchor == "firstDrop" ? s.ownerFirstDrop : anchor == "secondDrop" ? s.ownerSecondDrop : s.ownerEnding)
                    : s.Anchor(anchor);
                foreach (int b in beats)
                {
                    double t = a - b * s.BeatSeconds;
                    var c = new Cue { song = s.id, anchor = anchor, beatsBefore = b, time = t, valid = true };
                    if (t < 0) { c.valid = false; c.reason = "before the start of the file"; }
                    else if (s.durationSeconds > 0 && t >= s.durationSeconds) { c.valid = false; c.reason = "after the end of the file"; }
                    list.Add(c);
                }
            }
            return list;
        }

        public static Cue Entry(SongDef s, string anchor, int beatsBefore)
        {
            double t = s.Anchor(anchor) - beatsBefore * s.BeatSeconds;
            return new Cue { song = s.id, anchor = anchor, beatsBefore = beatsBefore, time = t, valid = t >= 0 && (s.durationSeconds <= 0 || t < s.durationSeconds), reason = t < 0 ? "before the start of the file" : "" };
        }
    }
}
