using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using OpenTS2.Components;
using OpenTS2.Content;
using UnityEngine;

namespace Bedsit.Sims2
{
    /// <summary>
    /// A Sims 2 character in the Unity scene: genuine game skeleton ("auskel"), genuine body/head/hair/clothing meshes
    /// and genuine game animations, assembled by OpenTS2's SimCharacterComponent. Implements ICharacterActor so
    /// gameplay code never touches Sims 2 types.
    /// </summary>
    public class SimCharacterActor : MonoBehaviour, ICharacterActor
    {
        public string ActorId { get; private set; }
        public Transform Root => transform;
        public string CurrentKey { get; private set; }
        public bool IsPlayingOneShot { get; private set; }
        public event Action<string> OneShotFinished;

        /// <summary>Where this appearance came from (for provenance): "naked-base" or "N001_User00005.package".</summary>
        public string AppearanceSource { get; private set; }

        public SimCharacterComponent Sim { get; private set; }
        Animation _animation;
        readonly Dictionary<string, string> _clipNames = new Dictionary<string, string>();   // key -> clip name on this actor
        Coroutine _oneShot;
        string _resolvedIdleName;

        // ------------------------------------------------------------------------------------------------ creation

        /// <summary>The unclothed base Sim (the exact proof used by OpenTS2's own SimAnimationTest).</summary>
        public static SimCharacterActor CreateNakedBase(string actorId)
        {
            if (!Sims2Runtime.Initialise()) return null;
            var sim = SimCharacterComponent.CreateNakedBaseSim();
            return Wrap(actorId, sim, "naked-base (amBodyNaked_cres / amHairBald_cres / amFace_cres, auskel skeleton)");
        }

        /// <summary>
        /// A premade neighbourhood Sim with its genuine CAS appearance and clothing, rigged with the original skeleton so
        /// the original animations can drive it. Reads Neighborhoods/{prefix}/Characters/{prefix}_User{id:D5}.package
        /// from the configured user directory (a local copy of the game's own N001 Pleasantview characters).
        /// </summary>
        public static SimCharacterActor CreateFromNeighborhood(string actorId, string neighborhoodPrefix, uint userInstanceId)
        {
            if (!Sims2Runtime.Initialise()) return null;
            var outfit = SimCharacterComponent.CreatePersonOutfit(neighborhoodPrefix, userInstanceId, default, skinnedParts: true);
            if (outfit == null)
            {
                Debug.LogWarning($"[SimCharacterActor] no outfit for {neighborhoodPrefix}_User{userInstanceId:D5}");
                return null;
            }
            var sim = SimCharacterComponent.CreateAnimatedFromOutfit(outfit);
            if (sim == null)
            {
                Debug.LogWarning($"[SimCharacterActor] outfit for {neighborhoodPrefix}_User{userInstanceId:D5} has no rigged skeleton");
                UnityEngine.Object.Destroy(outfit);
                return null;
            }
            return Wrap(actorId, sim, $"{neighborhoodPrefix}_User{userInstanceId:D5}.package (CAS outfit, Casual1)");
        }

        static SimCharacterActor Wrap(string actorId, SimCharacterComponent sim, string source)
        {
            var go = new GameObject("Actor_" + actorId);
            var actor = go.AddComponent<SimCharacterActor>();
            actor.ActorId = actorId;
            actor.AppearanceSource = source;
            actor.Sim = sim;
            sim.transform.SetParent(go.transform, false);
            actor._animation = sim.GetComponentInChildren<Animation>();
            if (actor._animation == null) Debug.LogWarning("[SimCharacterActor] no Animation component on " + actorId);
            else actor._animation.cullingType = AnimationCullingType.AlwaysAnimate;

            // Register every IK chain the library's animations use up front: SimCharacterComponent rebuilds its
            // animation graph whenever a new chain appears, and rebuilding mid-playback can crash the editor.
            foreach (var key in SimAnimationLibrary.Definitions.Keys)
            {
                var res = SimAnimationLibrary.Resolve(key);
                if (res != null) sim.AdjustInverseKinematicWeightsForAnimation(res.Asset.AnimResource);
            }
            return actor;
        }

        // ------------------------------------------------------------------------------------------------ animation

        /// <summary>Ensure the library animation for this key exists as a clip on this actor. Returns the clip name.</summary>
        string EnsureClip(string key)
        {
            if (_clipNames.TryGetValue(key, out var existing)) return existing;
            var res = SimAnimationLibrary.Resolve(key);
            if (res == null || _animation == null || Sim == null) return null;
            var clip = res.Asset.CreateClipFromResource(Sim.Scenegraph.BoneNamesToRelativePaths, Sim.Scenegraph.BlendNamesToRelativePaths);
            clip.wrapMode = res.Def.Loop ? WrapMode.Loop : WrapMode.Once;
            string clipName = res.ResourceName;
            _animation.AddClip(clip, clipName);
            _clipNames[key] = clipName;
            return clipName;
        }

        void StartClip(string key, float fade)
        {
            var clipName = EnsureClip(key);
            if (clipName == null) return;
            var res = SimAnimationLibrary.Resolve(key);
            Sim.AdjustInverseKinematicWeightsForAnimation(res.Asset.AnimResource);
            _animation.CrossFade(clipName, fade, PlayMode.StopAll);
            CurrentKey = key;
        }

        public void PlayIdle()
        {
            if (_oneShot != null) { StopCoroutine(_oneShot); _oneShot = null; }
            IsPlayingOneShot = false;
            StartClip(AnimationKeys.Idle, 0.25f);
        }

        public bool PlayOneShot(string key)
        {
            if (_animation == null || !SimAnimationLibrary.Has(key)) return false;
            if (EnsureClip(key) == null) return false;
            if (_oneShot != null) StopCoroutine(_oneShot);
            _oneShot = StartCoroutine(OneShotRoutine(key));
            return true;
        }

        IEnumerator OneShotRoutine(string key)
        {
            IsPlayingOneShot = true;
            StartClip(key, 0.15f);
            var clipName = _clipNames[key];
            yield return null;                                   // let the cross-fade register
            while (_animation != null && _animation.IsPlaying(clipName)) yield return null;
            IsPlayingOneShot = false;
            _oneShot = null;
            OneShotFinished?.Invoke(key);
            StartClip(AnimationKeys.Idle, 0.25f);
        }

        // ------------------------------------------------------------------------------------------------ pose + placement

        /// <summary>Local rotation of every skeleton bone: used to prove an original animation visibly changes the pose.</summary>
        public Quaternion[] CapturePose()
        {
            if (Sim == null) return new Quaternion[0];
            return Sim.Scenegraph.BoneNamesToTransform.OrderBy(kv => kv.Key, StringComparer.Ordinal)
                .Select(kv => kv.Value != null ? kv.Value.localRotation : Quaternion.identity).ToArray();
        }

        /// <summary>Largest per-bone angular difference (degrees) between two poses.</summary>
        public static float MaxPoseDelta(Quaternion[] a, Quaternion[] b)
        {
            float max = 0f;
            int n = Math.Min(a.Length, b.Length);
            for (int i = 0; i < n; i++) max = Mathf.Max(max, Quaternion.Angle(a[i], b[i]));
            return max;
        }

        public Transform Bone(string name) =>
            Sim != null && Sim.Scenegraph.BoneNamesToTransform.TryGetValue(name, out var t) ? t : null;

        public void FaceTowards(Vector3 worldPoint)
        {
            var d = worldPoint - transform.position;
            d.y = 0f;
            if (d.sqrMagnitude > 1e-4f) transform.rotation = Quaternion.LookRotation(d.normalized, Vector3.up);
        }

        /// <summary>Put every renderer of this actor on a layer (used to make the player body mirror-only).</summary>
        public void SetLayerRecursive(int layer)
        {
            foreach (var t in GetComponentsInChildren<Transform>(true)) t.gameObject.layer = layer;
        }

        public void SetVisible(bool visible)
        {
            foreach (var r in GetComponentsInChildren<Renderer>(true)) r.enabled = visible;
        }

        /// <summary>World-space bounds of all renderers (for scaling/placement checks).</summary>
        public Bounds RendererBounds()
        {
            var rs = GetComponentsInChildren<Renderer>(true);
            if (rs.Length == 0) return new Bounds(transform.position, Vector3.zero);
            var b = rs[0].bounds;
            for (int i = 1; i < rs.Length; i++) b.Encapsulate(rs[i].bounds);
            return b;
        }
    }
}
