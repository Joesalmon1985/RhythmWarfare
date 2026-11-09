using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Text;
using Bedsit.Sims2;
using UnityEngine;

namespace Bedsit.Game
{
    /// <summary>
    /// Milestone B proof: assembles genuine Sims 2 characters through OpenTS2, plays ORIGINAL Sims 2 animations on their
    /// original skeleton, measures the resulting bone-pose change and writes provenance + screenshots.
    /// Run from the AnimationProof scene (or the Bedsit/Run Animation Proof menu).
    /// </summary>
    public class AnimationProofRunner : MonoBehaviour
    {
        public bool Finished { get; private set; }
        public string Report { get; private set; }
        public float NakedMaxDelta, DressedMaxDelta;

        IEnumerator Start()
        {
            var sb = new StringBuilder();
            if (!Sims2Runtime.Initialise())
            {
                Report = "FAILED: " + Sims2Runtime.LastError;
                Debug.LogError(Report);
                Finished = true;
                yield break;
            }
            sb.AppendLine("config: " + Sims2Runtime.ConfigPath);

            // stage
            var cam = new GameObject("ProofCamera").AddComponent<Camera>();
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.55f, 0.62f, 0.7f);
            cam.fieldOfView = 40f;
            var light = new GameObject("Sun").AddComponent<Light>();
            light.type = LightType.Directional;
            light.transform.rotation = Quaternion.Euler(40f, -30f, 0f);
            light.intensity = 1.1f;
            var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
            floor.transform.localScale = new Vector3(2f, 1f, 2f);
            floor.GetComponent<Renderer>().material.color = new Color(0.4f, 0.4f, 0.4f);

            var naked = SimCharacterActor.CreateNakedBase("naked");
            var dressed = SimCharacterActor.CreateFromNeighborhood("dressed", "N001", 12);
            var dressed2 = SimCharacterActor.CreateFromNeighborhood("dressed2", "N001", 11);
            var actors = new List<SimCharacterActor>();
            if (naked != null) { naked.transform.position = new Vector3(-0.7f, 0f, 0f); actors.Add(naked); }
            if (dressed != null) { dressed.transform.position = new Vector3(0.7f, 0f, 0f); actors.Add(dressed); }
            if (dressed2 != null) { dressed2.transform.position = new Vector3(1.9f, 0f, 0f); actors.Add(dressed2); }
            foreach (var a in actors) a.FaceTowards(new Vector3(0f, 0f, -5f));
            sb.AppendLine($"naked sim: {(naked != null ? naked.AppearanceSource : "FAILED")}");
            sb.AppendLine($"dressed sim: {(dressed != null ? dressed.AppearanceSource : "FAILED")}");

            cam.transform.position = new Vector3(0.6f, 1.3f, -4.6f);
            cam.transform.LookAt(new Vector3(0.6f, 0.95f, 0f));

            foreach (var a in actors) a.PlayIdle();
            yield return new WaitForSeconds(0.6f);
            ScreenshotUtil.Capture(cam, "proof_01_idle.png");

            // rest pose -> wave
            var rest = new Dictionary<SimCharacterActor, Quaternion[]>();
            var maxDelta = new Dictionary<SimCharacterActor, float>();
            foreach (var a in actors) { rest[a] = a.CapturePose(); maxDelta[a] = 0f; a.PlayOneShot(AnimationKeys.Wave); }

            float t = 0f; bool shot = false;
            while (t < 5f)
            {
                yield return new WaitForSeconds(0.1f);
                t += 0.1f;
                foreach (var a in actors)
                    maxDelta[a] = Mathf.Max(maxDelta[a], SimCharacterActor.MaxPoseDelta(rest[a], a.CapturePose()));
                if (!shot && t >= 1.2f) { ScreenshotUtil.Capture(cam, "proof_02_wave_a.png"); shot = true; }
                if (t >= 2.0f && t < 2.11f) ScreenshotUtil.Capture(cam, "proof_03_wave_b.png");
                bool anyPlaying = false;
                foreach (var a in actors) anyPlaying |= a.IsPlayingOneShot;
                if (!anyPlaying && t > 0.5f) break;
            }
            if (naked != null) NakedMaxDelta = maxDelta[naked];
            if (dressed != null) DressedMaxDelta = maxDelta[dressed];

            sb.AppendLine($"max bone rotation change during wave: naked={NakedMaxDelta:0.0} deg, dressed={DressedMaxDelta:0.0} deg");
            sb.AppendLine("--- animation provenance ---");
            sb.Append(SimAnimationLibrary.DescribeAll());
            Report = sb.ToString();
            var path = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "Evidence", "animation_proof.txt"));
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            File.WriteAllText(path, Report);
            Debug.Log("[AnimationProof]\n" + Report);
            Finished = true;
        }
    }
}
