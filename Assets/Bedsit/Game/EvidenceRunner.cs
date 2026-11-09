using System;
using System.Collections;
using System.IO;
using System.Text;
using Bedsit.Sims2;
using UnityEngine;

namespace Bedsit.Game
{
    /// <summary>
    /// Records evidence screenshots of the real flow (driven through the same InputRouter the player uses), including the
    /// HUD overlay. Enabled with the BEDSIT_EVIDENCE=1 environment variable or the "-evidence" command-line argument, so
    /// it works in the Editor and in the Windows build. Output: Evidence/screenshots/*.png and Evidence/evidence_log.txt.
    /// Screenshots contain EA assets and are therefore git-ignored; the log is committed.
    /// </summary>
    public class EvidenceRunner : MonoBehaviour
    {
        public static bool Requested =>
            Environment.GetEnvironmentVariable("BEDSIT_EVIDENCE") == "1" || Array.IndexOf(Environment.GetCommandLineArgs(), "-evidence") >= 0;

        BedsitGame _g;
        readonly StringBuilder _log = new StringBuilder();

        void Log(string s) { _log.AppendLine(s); Debug.Log("[Evidence] " + s); }

        IEnumerator Start()
        {
            _g = GetComponent<BedsitGame>();
            while (_g == null || !_g.Ready) yield return null;
            Log("evidence run started " + DateTime.Now.ToString("s") + $" resolution {Screen.width}x{Screen.height}");

            // ---- wake-up (real sequence)
            if (!_g.WakeUpFinished)
            {
                yield return Snap("01_wakeup_dark");
                while (_g.Hud.FadeAlpha > 0.55f) yield return null;
                yield return Snap("02_wakeup_fading_in");
                while (_g.Rig.position.y < 1.0f && !_g.WakeUpFinished) yield return null;
                yield return Snap("03_wakeup_rising");
                while (!_g.WakeUpFinished) yield return null;
                Log($"wake-up finished: eye {_g.Rig.position}, facing {_g.View.Facing}");
            }
            yield return new WaitForSeconds(0.6f);

            // ---- four compass views with turn controls
            yield return Snap("10_view_north");
            for (int i = 0; i < 3; i++)
            {
                _g.Input.Raise(PlayerAction.TurnRight);
                yield return WaitTurn();
                yield return new WaitForSeconds(0.3f);
                yield return Snap("1" + (i + 1) + "_view_" + _g.View.Facing.ToString().ToLower());
            }
            _g.Input.Raise(PlayerAction.TurnRight); yield return WaitTurn();
            Log("four right turns -> facing " + _g.View.Facing + " (yaw " + _g.View.CurrentYaw + ")");

            // ---- east window: NPC waves
            _g.Input.Raise(PlayerAction.TurnRight); yield return WaitTurn();
            yield return new WaitForSeconds(0.4f);
            _g.Input.Raise(PlayerAction.Interact);
            yield return new WaitForSeconds(0.55f); yield return Snap("20_east_npc_reacts_a");
            yield return new WaitForSeconds(0.7f); yield return Snap("21_east_npc_reacts_b");
            yield return new WaitForSeconds(1.6f);

            // ---- mirror: player's reflection performs a real Sims 2 animation
            _g.Input.Raise(PlayerAction.TurnRight); yield return WaitTurn();
            yield return new WaitForSeconds(0.5f); yield return Snap("30_mirror_idle");
            _g.Input.Raise(PlayerAction.Interact);
            yield return new WaitForSeconds(0.6f); yield return Snap("31_mirror_wave_a");
            yield return new WaitForSeconds(0.7f); yield return Snap("32_mirror_wave_b");
            yield return new WaitForSeconds(1.6f);

            // ---- west window
            _g.Input.Raise(PlayerAction.TurnRight); yield return WaitTurn();
            yield return new WaitForSeconds(0.4f);
            _g.Input.Raise(PlayerAction.Interact);
            yield return new WaitForSeconds(0.5f); yield return Snap("40_west_npc_reacts");
            yield return new WaitForSeconds(1.8f);

            // ---- north: open the door and walk into the corridor in first person
            _g.Input.Raise(PlayerAction.TurnRight); yield return WaitTurn();
            yield return new WaitForSeconds(0.4f); yield return Snap("50_door_before");
            _g.Input.Raise(PlayerAction.Interact);
            for (int i = 0; i < 4; i++) { yield return new WaitForSeconds(0.55f); yield return Snap("51_corridor_walk_" + i); }
            while (_g.Transition.IsMoving || _g.Zones.CurrentZoneId != BedsitGame.ZoneCorridor) yield return null;
            Log($"arrived in corridor: eye {_g.Rig.position} (eye height constant: {_g.Transition.MinEyeHeightDuringMove}..{_g.Transition.MaxEyeHeightDuringMove})");
            yield return new WaitForSeconds(0.8f); yield return Snap("55_corridor_north");
            _g.Input.Raise(PlayerAction.TurnRight); yield return WaitTurn(); yield return new WaitForSeconds(0.3f); yield return Snap("56_corridor_east");
            _g.Input.Raise(PlayerAction.TurnRight); yield return WaitTurn(); yield return new WaitForSeconds(0.3f); yield return Snap("57_corridor_south_back_to_bedsit");
            _g.Input.Raise(PlayerAction.TurnRight); yield return WaitTurn(); yield return new WaitForSeconds(0.3f); yield return Snap("58_corridor_west");

            Log("content: " + (BedsitContent.UsingBaked ? "BAKED assets" : "LIVE Sims 2 install via OpenTS2"));
            if (!BedsitContent.UsingBaked) Log("provenance:\n" + SimAnimationLibrary.DescribeAll());
            foreach (var line in _g.World.Report) Log("world: " + line);
            foreach (var line in _g.Log) Log("game: " + line);
            var path = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "Evidence", "evidence_log.txt"));
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            File.WriteAllText(path, _log.ToString());
            File.WriteAllText(Path.Combine(Path.GetDirectoryName(path), "evidence_done.txt"), DateTime.Now.ToString("s"));
            if (Array.IndexOf(Environment.GetCommandLineArgs(), "-quit") >= 0 || Application.isBatchMode) Application.Quit();
        }

        IEnumerator WaitTurn() { while (_g.View.IsTurning) yield return null; }

        /// <summary>Screenshot of the real game frame (including the HUD overlay).</summary>
        IEnumerator Snap(string name)
        {
            yield return new WaitForEndOfFrame();
            var dir = ScreenshotUtil.EvidenceDir;
            var path = Path.Combine(dir, name + ".png");
            var tex = ScreenCapture.CaptureScreenshotAsTexture();
            if (tex != null)
            {
                File.WriteAllBytes(path, tex.EncodeToPNG());
                Destroy(tex);
            }
            else ScreenshotUtil.Capture(_g.EyeCamera, name + ".png", 1280, 720);
            Log($"screenshot {name}.png | zone={_g.Zones.CurrentZoneId} facing={_g.View.Facing} eye={_g.Rig.position:F2} fade={_g.Hud.FadeAlpha:F2}");
        }
    }
}
