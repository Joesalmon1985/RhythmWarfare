using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using Bedsit.Game;
using Bedsit.Sims2;
using UnityEditor;
using UnityEngine;

namespace Bedsit.EditorTools
{
    /// <summary>
    /// Converts the LIVE content (room + four Sims built at run time from the user's Sims 2 install through OpenTS2) into
    /// ordinary Unity assets under Assets/LocalBaked (git-ignored: derived from EA assets):
    ///   * every mesh, material and texture becomes a normal asset (textures re-imported with ASTC on Android),
    ///   * each character becomes a prefab of plain skinned meshes + a skeleton, with full-body animation clips sampled
    ///     frame by frame from the ORIGINAL Sims 2 animations (IK already resolved, so no rigging package is needed at run time),
    ///   * the room becomes one prefab (door keeps its original animation clip).
    /// The game then runs without a Sims 2 install and without OpenTS2 data: on a phone, or on any PC.
    /// Run: open Bedsit.unity, press Play (with the Sims 2 config present), wait for the game to be ready, then menu Bedsit/Bake.
    /// </summary>
    public static class ContentBaker
    {
        const string Root = "Assets/LocalBaked";
        const string ResDir = Root + "/Resources/Baked";
        const string TexDir = Root + "/Textures";
        const string MatDir = Root + "/Materials";
        const string MeshDir = Root + "/Meshes";
        const string ClipDir = Root + "/Clips";

        static readonly Dictionary<int, Texture2D> TexCache = new Dictionary<int, Texture2D>();
        static readonly Dictionary<int, Material> MatCache = new Dictionary<int, Material>();
        static readonly Dictionary<int, Mesh> MeshCache = new Dictionary<int, Mesh>();
        static int _counter;
        static readonly StringBuilder Report = new StringBuilder();

        static readonly (string key, float fps)[] BakedKeys =
        {
            (AnimationKeys.Idle, 30f), (AnimationKeys.Wave, 30f), (AnimationKeys.Clap, 30f),
            (AnimationKeys.Cheer, 30f), (AnimationKeys.Greet, 30f), (AnimationKeys.Surprise, 30f),
        };

        public static string LastStatus { get; private set; } = "idle";
        public static bool Running { get; private set; }

        // ------------------------------------------------------------------------------------------------ entry points

        [MenuItem("Bedsit/Bake/Bake live content to local assets (Play mode)")]
        public static void Run()
        {
            var g = BedsitGame.Instance;
            if (!Application.isPlaying || g == null || !g.Ready) { Debug.LogError("[Bake] Enter Play mode in Bedsit.unity and wait until the game is ready."); return; }
            if (BedsitContent.UsingBaked) { Debug.LogError("[Bake] The game is running from baked content already; set BEDSIT_CONTENT=live."); return; }
            if (Running) return;
            Runner.Start(BakeRoutine(g));
        }

        // ------------------------------------------------------------------------------------------------ routine

        static IEnumerator BakeRoutine(BedsitGame g)
        {
            Running = true;
            LastStatus = "baking";
            Report.Clear();
            TexCache.Clear(); MatCache.Clear(); MeshCache.Clear(); _counter = 0;
            foreach (var d in new[] { ResDir, TexDir, MatDir, MeshDir, ClipDir }) Directory.CreateDirectory(d);

            g.StopAllCoroutines();
            g.Input.Locked = true;
            g.Hud.SetFade(0f);

            // ---- 1. sample the original animations into plain clips (from the player's Sim; same skeleton for every Sim)
            var actor = g.Player;
            var animGo = actor.GetComponentInChildren<Animation>().gameObject;
            var skeletonRoot = actor.Bone("auskel");
            var bones = skeletonRoot.GetComponentsInChildren<Transform>(true).ToList();
            var paths = bones.Select(b => AnimationUtility.CalculateTransformPath(b, animGo.transform)).ToList();
            var positionBones = new HashSet<string> { "root_trans", "pelvis" };
            var clips = new List<BakedActorData.Entry>();
            Report.AppendLine($"skeleton bones sampled: {bones.Count}");

            foreach (var (key, fps) in BakedKeys)
            {
                var res = SimAnimationLibrary.Resolve(key);
                if (res == null) { Report.AppendLine("SKIP (unresolved) " + key); continue; }
                float length = Mathf.Max(res.DurationSeconds, 0.5f);
                int n = Mathf.Max(2, Mathf.RoundToInt(length * fps));
                var rot = new Quaternion[bones.Count][];
                var pos = new Vector3[bones.Count][];
                for (int i = 0; i < bones.Count; i++) { rot[i] = new Quaternion[n]; pos[i] = new Vector3[n]; }

                for (int f = 0; f < n; f++)
                {
                    LastStatus = $"sampling {key} {f + 1}/{n}";
                    actor.ScrubTo(key, f / (float)n);
                    yield return null; yield return null; yield return null;
                    for (int i = 0; i < bones.Count; i++) { rot[i][f] = bones[i].localRotation; pos[i][f] = bones[i].localPosition; }
                }

                bool loop = key == AnimationKeys.Idle;
                var clip = new AnimationClip { name = $"{key}_{res.ResourceName}", frameRate = fps, legacy = true };
                int keyCount = loop ? n + 1 : n;
                for (int i = 0; i < bones.Count; i++)
                {
                    var kx = new Keyframe[keyCount]; var ky = new Keyframe[keyCount]; var kz = new Keyframe[keyCount]; var kw = new Keyframe[keyCount];
                    for (int f = 0; f < keyCount; f++)
                    {
                        var q = rot[i][f % n];
                        float t = f / fps;
                        kx[f] = new Keyframe(t, q.x); ky[f] = new Keyframe(t, q.y); kz[f] = new Keyframe(t, q.z); kw[f] = new Keyframe(t, q.w);
                    }
                    clip.SetCurve(paths[i], typeof(Transform), "localRotation.x", Smooth(kx));
                    clip.SetCurve(paths[i], typeof(Transform), "localRotation.y", Smooth(ky));
                    clip.SetCurve(paths[i], typeof(Transform), "localRotation.z", Smooth(kz));
                    clip.SetCurve(paths[i], typeof(Transform), "localRotation.w", Smooth(kw));
                    if (positionBones.Contains(bones[i].name))
                    {
                        var px = new Keyframe[keyCount]; var py = new Keyframe[keyCount]; var pz = new Keyframe[keyCount];
                        for (int f = 0; f < keyCount; f++)
                        {
                            var p = pos[i][f % n]; float t = f / fps;
                            px[f] = new Keyframe(t, p.x); py[f] = new Keyframe(t, p.y); pz[f] = new Keyframe(t, p.z);
                        }
                        clip.SetCurve(paths[i], typeof(Transform), "localPosition.x", Smooth(px));
                        clip.SetCurve(paths[i], typeof(Transform), "localPosition.y", Smooth(py));
                        clip.SetCurve(paths[i], typeof(Transform), "localPosition.z", Smooth(pz));
                    }
                }
                clip.EnsureQuaternionContinuity();
                clip.wrapMode = loop ? WrapMode.Loop : WrapMode.Once;
                var clipPath = $"{ClipDir}/{key}.anim";
                AssetDatabase.CreateAsset(clip, clipPath);
                clips.Add(new BakedActorData.Entry { Key = key, Clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(clipPath), SourceResource = res.ResourceName });
                Report.AppendLine($"clip {key}: {res.ResourceName} ({res.Package}), {n} frames @ {fps} fps, {bones.Count} bones");
            }
            actor.ResetToIdle();

            // ---- 2. characters
            var cast = new[] { (g.Player, g.PlayerSim), (g.NpcCorridor, g.CorridorSim), (g.NpcEast, g.EastSim), (g.NpcWest, g.WestSim) };
            foreach (var (a, simId) in cast)
            {
                LastStatus = "baking character " + simId;
                a.ResetToIdle();
                yield return null; yield return null; yield return null;
                var clone = UnityEngine.Object.Instantiate(a.gameObject);
                clone.name = "Actor_" + simId;
                clone.transform.position = Vector3.zero; clone.transform.rotation = Quaternion.identity;
                Strip(clone, removeAnimation: true);
                var cloneAnimGo = FindAnimationHost(clone, animGo.name, a);
                var anim = cloneAnimGo.AddComponent<Animation>();
                anim.playAutomatically = false;
                BakeRenderers(clone);
                var data = clone.AddComponent<BakedActorData>();
                data.Clips = clips.ToArray();
                data.SourceNote = $"N001_User{simId:D5}.package";
                var path = $"{ResDir}/Actor_{simId}.prefab";
                PrefabUtility.SaveAsPrefabAsset(clone, path);
                UnityEngine.Object.DestroyImmediate(clone);
                Report.AppendLine($"character prefab {path}");
                yield return null;
            }

            // ---- 3. room
            LastStatus = "baking world";
            var live = g.World;
            var worldClone = UnityEngine.Object.Instantiate(live.gameObject);
            worldClone.name = "BedsitWorld";
            foreach (var m in worldClone.GetComponentsInChildren<MirrorReflectionController>(true))
            {
                for (int i = m.transform.childCount - 1; i >= 0; i--)
                {
                    var c = m.transform.GetChild(i);
                    if (c.name == "MirrorGlass" || c.name == "MirrorCamera") UnityEngine.Object.DestroyImmediate(c.gameObject);
                }
                UnityEngine.Object.DestroyImmediate(m);
            }
            Strip(worldClone, removeAnimation: false);
            var cloneWorld = worldClone.GetComponent<BedsitWorld>();
            if (live.Door != null && cloneWorld.Door != null && live.Door.AnimationComponent != null)
            {
                var liveClip = live.Door.AnimationComponent.GetClip(live.Door.ClipName);
                // Save a serialized COPY: the live clip is still held by the running Animation component.
                var clip = new AnimationClip { legacy = true, wrapMode = WrapMode.ClampForever };
                EditorUtility.CopySerialized(liveClip, clip);
                clip.legacy = true;
                clip.name = live.Door.ClipName;
                var clipPath = $"{ClipDir}/{clip.name}.anim";            // file name == clip name (Unity renames assets to their file name)
                AssetDatabase.CreateAsset(clip, clipPath);
                AssetDatabase.SaveAssets();
                clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(clipPath);
                Report.AppendLine($"door clip length {clip.length:0.00}s, curves {AnimationUtility.GetCurveBindings(clip).Length}");
                AnimationUtility.SetAnimationClips(cloneWorld.Door.AnimationComponent, new[] { clip });
                cloneWorld.Door.AnimationComponent.clip = clip;
                Report.AppendLine("door clip " + clip.name);
            }
            BakeRenderers(worldClone);
            var worldPath = $"{ResDir}/World.prefab";
            PrefabUtility.SaveAsPrefabAsset(worldClone, worldPath);
            UnityEngine.Object.DestroyImmediate(worldClone);
            Report.AppendLine($"world prefab {worldPath}");

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Report.AppendLine($"unique meshes {MeshCache.Count}, materials {MatCache.Count}, textures {TexCache.Count}");
            File.WriteAllText(Root + "/bake_report.txt", Report.ToString());
            File.WriteAllText("Evidence/bake_report.txt", Report.ToString());
            Debug.Log("[Bake] finished\n" + Report);
            g.Input.Locked = false;
            LastStatus = "done";
            Running = false;
        }

        // ------------------------------------------------------------------------------------------------ helpers

        static AnimationCurve Smooth(Keyframe[] keys)
        {
            var c = new AnimationCurve(keys);
            for (int i = 0; i < c.length; i++) c.SmoothTangents(i, 0f);
            return c;
        }

        /// <summary>The Animation component in a Sim lives on the scenegraph object that contains the skeleton; find its clone.</summary>
        static GameObject FindAnimationHost(GameObject clone, string liveName, SimCharacterActor live)
        {
            foreach (var t in clone.GetComponentsInChildren<Transform>(true))
                if (t.name == liveName && t.Find("auskel") != null) return t.gameObject;
            foreach (var t in clone.GetComponentsInChildren<Transform>(true))
                if (t.Find("auskel") != null) return t.gameObject;
            return clone;
        }

        static readonly string[] RemovalOrder =
        {
            "TwoBoneIKConstraint", "OverrideTransform", "RigTransform", "Rig", "RigBuilder", "BoneRenderer", "Animator",
            "SimCharacterComponent", "ScenegraphComponent", "AssetReferenceComponent",
        };

        /// <summary>Remove OpenTS2 / Animation Rigging components (and optionally Animation) from a cloned hierarchy.</summary>
        static void Strip(GameObject root, bool removeAnimation)
        {
            for (int pass = 0; pass < 3; pass++)
            {
                var comps = root.GetComponentsInChildren<Component>(true).Where(c => c != null).ToList();
                var doomed = comps.Where(c =>
                {
                    var t = c.GetType();
                    if (removeAnimation && t == typeof(Animation)) return true;
                    var ns = t.Namespace ?? "";
                    return ns.StartsWith("OpenTS2") || ns.StartsWith("UnityEngine.Animations.Rigging") || t == typeof(Animator);
                }).OrderBy(c => { int i = Array.IndexOf(RemovalOrder, c.GetType().Name); return i < 0 ? 99 : i; }).ToList();
                foreach (var c in doomed) if (c != null) UnityEngine.Object.DestroyImmediate(c);
            }
        }

        static void BakeRenderers(GameObject root)
        {
            foreach (var r in root.GetComponentsInChildren<Renderer>(true))
            {
                if (r is SkinnedMeshRenderer smr) smr.sharedMesh = BakeMesh(smr.sharedMesh);
                else if (r is MeshRenderer && r.TryGetComponent<MeshFilter>(out var mf)) mf.sharedMesh = BakeMesh(mf.sharedMesh);
                var mats = r.sharedMaterials;
                for (int i = 0; i < mats.Length; i++) mats[i] = BakeMaterial(mats[i]);
                r.sharedMaterials = mats;
            }
        }

        static string Safe(string s)
        {
            if (string.IsNullOrEmpty(s)) return "unnamed";
            var sb = new StringBuilder();
            foreach (var ch in s) sb.Append(char.IsLetterOrDigit(ch) || ch == '_' || ch == '-' ? ch : '_');
            return sb.Length > 48 ? sb.ToString(0, 48) : sb.ToString();
        }

        static Mesh BakeMesh(Mesh m)
        {
            if (m == null || AssetDatabase.Contains(m)) return m;
            if (MeshCache.TryGetValue(m.GetInstanceID(), out var cached)) return cached;
            m.name = $"{Safe(m.name)}_{_counter++}";
            AssetDatabase.CreateAsset(m, $"{MeshDir}/{m.name}.asset");
            MeshCache[m.GetInstanceID()] = m;
            return m;
        }

        static Material BakeMaterial(Material m)
        {
            if (m == null || AssetDatabase.Contains(m)) return m;
            if (MatCache.TryGetValue(m.GetInstanceID(), out var cached)) return cached;
            var copy = new Material(m) { name = $"{Safe(m.name)}_{_counter++}" };
            foreach (var prop in copy.GetTexturePropertyNames())
            {
                if (copy.GetTexture(prop) is Texture2D t2) copy.SetTexture(prop, BakeTexture(t2));
            }
            AssetDatabase.CreateAsset(copy, $"{MatDir}/{copy.name}.mat");
            MatCache[m.GetInstanceID()] = copy;
            return copy;
        }

        static Texture2D BakeTexture(Texture2D src)
        {
            if (src == null) return null;
            if (AssetDatabase.Contains(src)) return src;
            if (TexCache.TryGetValue(src.GetInstanceID(), out var cached)) return cached;

            var rt = RenderTexture.GetTemporary(src.width, src.height, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Default);
            var prev = RenderTexture.active;
            Graphics.Blit(src, rt);
            RenderTexture.active = rt;
            var tmp = new Texture2D(src.width, src.height, TextureFormat.RGBA32, false);
            tmp.ReadPixels(new Rect(0, 0, src.width, src.height), 0, 0);
            tmp.Apply();
            RenderTexture.active = prev;
            RenderTexture.ReleaseTemporary(rt);

            var path = $"{TexDir}/{Safe(src.name)}_{_counter++}.png";
            File.WriteAllBytes(path, tmp.EncodeToPNG());
            UnityEngine.Object.DestroyImmediate(tmp);
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
            var ti = (TextureImporter)AssetImporter.GetAtPath(path);
            ti.textureType = TextureImporterType.Default;
            ti.wrapMode = src.wrapMode;
            ti.filterMode = FilterMode.Bilinear;
            ti.mipmapEnabled = src.mipmapCount > 1;
            ti.alphaSource = TextureImporterAlphaSource.FromInput;
            ti.alphaIsTransparency = true;
            ti.isReadable = false;
            ti.maxTextureSize = 1024;
            ti.textureCompression = TextureImporterCompression.Compressed;
            ti.SetPlatformTextureSettings(new TextureImporterPlatformSettings
            {
                name = "Android", overridden = true, maxTextureSize = 512, format = TextureImporterFormat.ASTC_6x6, compressionQuality = 50,
            });
            ti.SaveAndReimport();
            var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
            TexCache[src.GetInstanceID()] = tex;
            return tex;
        }

        // ------------------------------------------------------------------------------------------------ editor coroutine

        sealed class Runner
        {
            readonly IEnumerator _it;
            Runner(IEnumerator it) { _it = it; }
            public static void Start(IEnumerator it) { var r = new Runner(it); EditorApplication.update += r.Tick; }
            void Tick()
            {
                try { if (!_it.MoveNext()) EditorApplication.update -= Tick; }
                catch (Exception e) { Debug.LogException(e); EditorApplication.update -= Tick; Running = false; LastStatus = "FAILED: " + e.Message; }
            }
        }
    }
}
