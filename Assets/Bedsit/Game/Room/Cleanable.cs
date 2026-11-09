using System.Collections;
using System.Collections.Generic;
using Bedsit.Rooms;
using UnityEngine;

namespace Bedsit.Game
{
    /// <summary>
    /// One tidy-up task in a room. It owns a MESSY arrangement (one or more real prop instances) and a TIDY arrangement, and an
    /// action that plays between them:
    ///   bin   - the item is picked up and thrown into a bin (lid flips, "bin" sound) - the only action where the item really goes away;
    ///   make  - bedding lifts, is shaken out and settles flat with a puff;
    ///   fold  - the heap squashes and a neat folded stack drops onto the shelf;
    ///   stack - the tidy parts hop into place one after another;
    ///   slide - the same object lifts and slides to its proper place (cups to the tray, shoes to the rack);
    ///   swap/coil/zip - messy shrinks, tidy pops in (cables coiled, bag zipped...).
    /// It derives from ClutterItem, so Act One's picking, compass pips, tidy meter and visitor choice work unchanged.
    /// The highlight is deliberately subtle: a small slow-pulsing star above the item, and a gentle warm tint when hovered.
    /// </summary>
    public class Cleanable : ClutterItem
    {
        public CleanableDef Def;
        public readonly List<Transform> MessyParts = new List<Transform>();
        public readonly List<Transform> TidyParts = new List<Transform>();
        public Transform BinTarget;
        public Vector3 SlideTargetPos; public Quaternion SlideTargetRot = Quaternion.identity;
        public string Id => Def != null ? Def.id : name;
        public string Action => Def != null ? Def.action : "swap";

        Transform _icon; SpriteRenderer _iconR;
        float _phase, _hoverK;
        bool _hoverOn;
        readonly List<(Renderer r, Material[] original)> _hoverSaved = new List<(Renderer, Material[])>();
        static Camera _camMain;

        protected override void Awake() { base.Awake(); _phase = Random.value * 6.28f; }

        /// <summary>Called by the builder once all parts exist: tidy parts start hidden.</summary>
        public void Init()
        {
            Kind = Def != null ? Def.id : "cleanable";
            foreach (var t in TidyParts) if (t != null) t.gameObject.SetActive(false);
        }

        public override void AttachGlow(int layer)
        {
            var go = new GameObject("TidyIcon");
            go.layer = layer;                                           // never rendered in the mirror
            go.transform.SetParent(transform, false);
            _iconR = go.AddComponent<SpriteRenderer>();
            _iconR.sprite = FxSprites.Star;
            _iconR.sortingOrder = 6;
            _iconR.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            _iconR.receiveShadows = false;
            _icon = go.transform;
        }

        public override void SetHover(bool on)
        {
            if (on == _hoverOn) return;
            _hoverOn = on;
            if (on) ApplyHoverTint(); else RestoreHoverTint();
        }

        void ApplyHoverTint()
        {
            _hoverSaved.Clear();
            foreach (var part in MessyParts)
            {
                if (part == null) continue;
                foreach (var r in part.GetComponentsInChildren<Renderer>())
                {
                    var orig = r.sharedMaterials;
                    var copies = new Material[orig.Length];
                    for (int i = 0; i < orig.Length; i++)
                    {
                        copies[i] = orig[i] != null ? new Material(orig[i]) : null;
                        if (copies[i] == null || !copies[i].HasProperty("_EmissionColor")) continue;
                        var c = copies[i].HasProperty("_Color") ? copies[i].color : Color.gray;
                        copies[i].EnableKeyword("_EMISSION");
                        copies[i].SetColor("_EmissionColor", new Color(0.30f + c.r * 0.12f, 0.24f + c.g * 0.1f, 0.12f) * 0.55f);
                    }
                    _hoverSaved.Add((r, orig));
                    r.sharedMaterials = copies;
                }
            }
        }

        void RestoreHoverTint()
        {
            foreach (var (r, orig) in _hoverSaved)
            {
                if (r == null) continue;
                foreach (var m in r.sharedMaterials) if (m != null && !System.Array.Exists(orig, o => o == m)) Destroy(m);
                r.sharedMaterials = orig;
            }
            _hoverSaved.Clear();
        }

        protected override void LateUpdate()
        {
            if (Tidied || _icon == null) return;
            if (_camMain == null) _camMain = Camera.main;
            if (_camMain == null) return;
            float inv = 1f / Mathf.Max(0.0001f, transform.lossyScale.x);
            Vector3 top = PickCentre + Vector3.up * (Height * 0.5f + 0.09f);
            float pulse = 0.5f + 0.5f * Mathf.Sin(Time.time * 2.2f + _phase);
            _hoverK = Mathf.MoveTowards(_hoverK, _hoverOn ? 1f : 0f, Time.deltaTime * 6f);
            float live = Tidying ? 0f : 1f;
            _icon.position = top + Vector3.up * (0.015f * Mathf.Sin(Time.time * 2.6f + _phase)) + (_camMain.transform.position - top).normalized * 0.12f;
            _icon.rotation = _camMain.transform.rotation * Quaternion.Euler(0f, 0f, 8f * Mathf.Sin(Time.time * 1.3f + _phase));
            _icon.localScale = Vector3.one * (0.085f + 0.025f * pulse + 0.05f * _hoverK) * inv;
            _iconR.color = new Color(1f, 0.90f, 0.55f, (0.50f + 0.35f * pulse + 0.15f * _hoverK) * live);
        }

        // ------------------------------------------------------------------------------------------------ doing it

        public override bool Tidy()
        {
            if (Tidied || Tidying) return false;
            Tidying = true;
            RestoreHoverTint(); _hoverOn = false;
            if (_iconR != null) _iconR.enabled = false;
            StartCoroutine(Run());
            return true;
        }

        /// <summary>Instantly show the finished state (loading a save, tests).</summary>
        public void SnapToTidy()
        {
            if (Tidied) return;
            StopAllCoroutines();
            RestoreHoverTint();
            FinalState();
            Tidied = true; Tidying = false;
            if (_iconR != null) _iconR.enabled = false;
            RaiseGone();
        }

        void FinalState()
        {
            string a = Action;
            if (a == "bin") { foreach (var t in MessyParts) if (t != null) t.gameObject.SetActive(false); return; }
            if (TidyParts.Count == 0)
            {
                foreach (var t in MessyParts) if (t != null) { t.position = SlideTargetPos; t.rotation = SlideTargetRot; t.localScale = Vector3.one * (Def != null && Def.tidy != null ? Def.tidy.scale : 1f); }
                return;
            }
            foreach (var t in MessyParts) if (t != null) t.gameObject.SetActive(false);
            foreach (var t in TidyParts) if (t != null) { t.gameObject.SetActive(true); t.localScale = Vector3.one * ScaleOf(t); }
        }

        readonly Dictionary<Transform, float> _scales = new Dictionary<Transform, float>();
        float ScaleOf(Transform t) { return _scales.TryGetValue(t, out var s) ? s : 1f; }
        public void RememberScale(Transform t, float s) { _scales[t] = s; }

        IEnumerator Run()
        {
            string sound = !string.IsNullOrEmpty(Def?.sound) ? Def.sound : DefaultSound(Action);
            Vector3 centre = PickCentre;
            switch (Action)
            {
                case "bin": yield return BinRoutine(sound); break;
                case "make": SfxSynth.Play(sound, centre, 0.55f); yield return MakeRoutine(); break;
                case "fold": SfxSynth.Play(sound, centre, 0.5f); yield return FoldRoutine(); break;
                case "stack": yield return StackRoutine(sound); break;
                case "slide": SfxSynth.Play(sound, centre, 0.55f); yield return SlideRoutine(); break;
                default: SfxSynth.Play(sound, centre, 0.5f); yield return SwapRoutine(); break;
            }
            Vector3 fx = TidyParts.Count > 0 && TidyParts[0] != null ? TidyParts[0].position + Vector3.up * 0.1f : (Action == "bin" && BinTarget != null ? BinTarget.position + Vector3.up * 0.4f : centre);
            SparkBurst.Spawn(fx, 0.18f, 8);
            SfxSynth.Play("chime", fx, 0.16f);
            Tidied = true; Tidying = false;
            RaiseGone();
        }

        static string DefaultSound(string a)
        {
            switch (a) { case "bin": return "bin"; case "make": return "rustle"; case "fold": return "rustle"; case "slide": return "clink"; case "stack": return "thunk"; case "coil": return "rustle"; case "zip": return "zip"; default: return "thunk"; }
        }

        static float Ease(float k) { return k * k * (3f - 2f * k); }

        IEnumerator BinRoutine(string sound)
        {
            var bin = BinTarget;
            Vector3 mouth = bin != null ? bin.position + Vector3.up * 0.50f : transform.position + Vector3.up * 0.3f;
            var lid = bin != null ? FindDeep(bin, "lid") : null;
            var parts = new List<(Transform t, Vector3 p0, Quaternion r0, Vector3 s0, float delay)>();
            float d = 0f;
            foreach (var t in MessyParts) { if (t == null) continue; parts.Add((t, t.position, t.rotation, t.localScale, d)); d += 0.12f; }
            float total = 0.55f + d;
            bool played = false;
            Quaternion lid0 = lid != null ? lid.localRotation : Quaternion.identity;
            for (float t = 0f; t < total; t += Time.deltaTime)
            {
                foreach (var p in parts)
                {
                    float k = Mathf.Clamp01((t - p.delay) / 0.55f);
                    if (k <= 0f) continue;
                    float e = Ease(k);
                    Vector3 pos = Vector3.Lerp(p.p0, mouth, e) + Vector3.up * (Mathf.Sin(k * Mathf.PI) * 0.35f);
                    p.t.position = pos;
                    p.t.rotation = Quaternion.Euler(k * 280f, k * 200f, 0f) * p.r0;
                    p.t.localScale = p.s0 * (k < 0.8f ? 1f : Mathf.Lerp(1f, 0.0f, (k - 0.8f) / 0.2f));
                    if (k >= 1f) p.t.gameObject.SetActive(false);
                }
                if (!played && t > 0.4f) { played = true; SfxSynth.Play(sound, mouth, 0.6f); }
                if (lid != null)
                {
                    // flip the lid up as the first item arrives, then close it
                    float lt = Mathf.Clamp01((t - 0.25f) / 0.55f);
                    lid.localRotation = lid0 * Quaternion.Euler(-70f * Mathf.Sin(lt * Mathf.PI), 0f, 0f);
                }
                yield return null;
            }
            foreach (var p in parts) if (p.t != null) p.t.gameObject.SetActive(false);
            if (lid != null) lid.localRotation = lid0;
        }

        static Transform FindDeep(Transform root, string name)
        {
            foreach (var t in root.GetComponentsInChildren<Transform>(true)) if (t.name.ToLowerInvariant().Contains(name)) return t;
            return null;
        }

        IEnumerator MakeRoutine()
        {
            var starts = new List<(Transform t, Vector3 p, Vector3 s)>();
            foreach (var t in MessyParts) if (t != null) starts.Add((t, t.position, t.localScale));
            // shake the covers up
            for (float t = 0f; t < 0.3f; t += Time.deltaTime)
            {
                float k = t / 0.3f;
                foreach (var s in starts) { s.t.position = s.p + Vector3.up * (0.14f * Mathf.Sin(k * Mathf.PI)); s.t.localScale = new Vector3(s.s.x, s.s.y * (1f + 0.15f * Mathf.Sin(k * Mathf.PI)), s.s.z); }
                yield return null;
            }
            foreach (var s in starts) { s.t.position = s.p; s.t.localScale = s.s; s.t.gameObject.SetActive(false); }
            yield return Settle(TidyParts, 0.45f, 0.18f, 0.08f);
        }

        IEnumerator FoldRoutine()
        {
            var starts = new List<(Transform t, Vector3 s)>();
            foreach (var t in MessyParts) if (t != null) starts.Add((t, t.localScale));
            for (float t = 0f; t < 0.32f; t += Time.deltaTime)
            {
                float k = Ease(t / 0.32f);
                foreach (var s in starts) s.t.localScale = new Vector3(s.s.x * (1f + 0.12f * k), s.s.y * (1f - 0.75f * k), s.s.z * (1f + 0.12f * k));
                yield return null;
            }
            foreach (var s in starts) { s.t.localScale = s.s; s.t.gameObject.SetActive(false); }
            yield return Drop(TidyParts, 0.35f, 0.25f, 0.0f);
        }

        IEnumerator StackRoutine(string sound)
        {
            var starts = new List<(Transform t, Vector3 s)>();
            foreach (var t in MessyParts) if (t != null) starts.Add((t, t.localScale));
            for (float t = 0f; t < 0.22f; t += Time.deltaTime)
            {
                float k = Ease(t / 0.22f);
                foreach (var s in starts) s.t.localScale = s.s * (1f - k);
                yield return null;
            }
            foreach (var s in starts) { s.t.localScale = s.s; s.t.gameObject.SetActive(false); }
            // each tidy part drops in with its own thump, one after another
            for (int i = 0; i < TidyParts.Count; i++)
            {
                var one = new List<Transform> { TidyParts[i] };
                StartCoroutine(Drop(one, 0.22f, 0.2f, 0f));
                if (i % 2 == 0) SfxSynth.Play(sound, TidyParts[i].position, 0.35f);
                yield return new WaitForSeconds(0.1f);
            }
            yield return new WaitForSeconds(0.25f);
        }

        IEnumerator SlideRoutine()
        {
            var starts = new List<(Transform t, Vector3 p, Quaternion r)>();
            foreach (var t in MessyParts) if (t != null) starts.Add((t, t.position, t.rotation));
            const float dur = 0.55f;
            for (float t = 0f; t < dur; t += Time.deltaTime)
            {
                float k = Ease(t / dur);
                foreach (var s in starts)
                {
                    s.t.position = Vector3.Lerp(s.p, SlideTargetPos, k) + Vector3.up * (Mathf.Sin(k * Mathf.PI) * 0.09f);
                    s.t.rotation = Quaternion.Slerp(s.r, SlideTargetRot, k);
                }
                yield return null;
            }
            foreach (var s in starts) { s.t.position = SlideTargetPos; s.t.rotation = SlideTargetRot; }
            yield return new WaitForSeconds(0.05f);
        }

        IEnumerator SwapRoutine()
        {
            var starts = new List<(Transform t, Vector3 s)>();
            foreach (var t in MessyParts) if (t != null) starts.Add((t, t.localScale));
            for (float t = 0f; t < 0.2f; t += Time.deltaTime)
            {
                float k = Ease(t / 0.2f);
                foreach (var s in starts) s.t.localScale = s.s * (1f - 0.85f * k);
                yield return null;
            }
            foreach (var s in starts) { s.t.localScale = s.s; s.t.gameObject.SetActive(false); }
            yield return Settle(TidyParts, 0.35f, 0.0f, 0.0f, 0.7f);
        }

        /// <summary>Tidy parts appear and settle: scale (from → 1.06 → 1) with an optional rise.</summary>
        IEnumerator Settle(List<Transform> parts, float dur, float rise, float stretch, float from = 0.9f)
        {
            var list = new List<(Transform t, Vector3 p, float s)>();
            foreach (var t in parts) if (t != null) { t.gameObject.SetActive(true); list.Add((t, t.position, ScaleOf(t))); }
            for (float t = 0f; t < dur; t += Time.deltaTime)
            {
                float k = t / dur;
                float over = k < 0.6f ? Mathf.Lerp(from, 1.07f, Ease(k / 0.6f)) : Mathf.Lerp(1.07f, 1f, Ease((k - 0.6f) / 0.4f));
                foreach (var l in list)
                {
                    l.t.localScale = new Vector3(l.s * over, l.s * (over + stretch * (1f - k)), l.s * over);
                    l.t.position = l.p + Vector3.up * (rise * (1f - Ease(k)));
                }
                yield return null;
            }
            foreach (var l in list) { l.t.localScale = Vector3.one * l.s; l.t.position = l.p; }
        }

        IEnumerator Drop(List<Transform> parts, float dur, float height, float unused)
        {
            var list = new List<(Transform t, Vector3 p, float s)>();
            foreach (var t in parts) if (t != null) { t.gameObject.SetActive(true); list.Add((t, t.position, ScaleOf(t))); }
            for (float t = 0f; t < dur; t += Time.deltaTime)
            {
                float k = t / dur;
                float fall = 1f - k * k;
                float bounce = k > 0.75f ? Mathf.Sin((k - 0.75f) / 0.25f * Mathf.PI) * 0.025f : 0f;
                foreach (var l in list) { l.t.position = l.p + Vector3.up * (height * fall + bounce); l.t.localScale = Vector3.one * l.s * Mathf.Min(1f, 0.6f + k * 1.2f); }
                yield return null;
            }
            foreach (var l in list) { l.t.position = l.p; l.t.localScale = Vector3.one * l.s; }
        }
    }
}
