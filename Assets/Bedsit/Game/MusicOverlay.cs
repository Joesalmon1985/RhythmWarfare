using Bedsit.Music;
using UnityEngine;

namespace Bedsit.Game
{
    /// <summary>
    /// Development diagnostics (F1 / -overlay): bedroom facing, RHYTHM/MIXING, song + position, beat, next anchor, incoming song,
    /// build accuracy vs threshold, stem state, pending plan, pad legend. Deliberately separate from the presentation layer.
    /// </summary>
    public class MusicOverlay : MonoBehaviour
    {
        public MusicPoc Poc;
        public bool Visible;
        GUIStyle _style;

        static readonly string[] Destinations = { "North: Space", "East: Dinosaurs", "South: Magic/Unicorns", "West: Transport" };

        void OnGUI()
        {
            if (!Visible || Poc == null || Poc.Session == null) return;
            if (_style == null) _style = new GUIStyle(GUI.skin.box) { alignment = TextAnchor.UpperLeft, fontSize = 12, richText = false };
            var g = BedsitGame.Instance; var s = Poc.Session; double now = s.Mixer.Time;
            bool ready = g != null && g.View != null && g.Zones != null;    // the world is built asynchronously after launch
            string facing = ready ? g.View.Facing + (g.View.IsTurning ? " (turning)" : "") : "-";
            string dest = ready ? "forward destination (NOT BUILT in this POC): " + Destinations[(int)g.View.Facing] : "";
            var sb = new System.Text.StringBuilder();
            sb.AppendLine($"facing {facing}   zone {(ready ? g.Zones.CurrentZoneId : "-")}   {dest}");
            sb.Append(s.Director.StatusText(now));
            sb.AppendLine($"device audio: {(Poc.DeviceActive ? "yes" : "NO (pumped)")}   paused {Poc.Paused}   taps {Poc.Taps}   bot {(Poc.Bot != null ? "on" : "off")}");
            sb.AppendLine("pads: drums phase 1=kick 4=snare | bass phase 1-4 by pitch    keys D F J K   [F1 overlay] [P pause]");
            int from = Mathf.Max(0, s.Director.Log.Count - 7);
            for (int i = from; i < s.Director.Log.Count; i++) sb.AppendLine(s.Director.Log[i]);
            GUI.Box(new Rect(8, 8, Mathf.Min(Screen.width - 16, 760), 330), sb.ToString(), _style);
        }
    }
}
