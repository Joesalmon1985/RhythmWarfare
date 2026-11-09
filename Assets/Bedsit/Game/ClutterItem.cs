using System;
using System.Collections;
using UnityEngine;

namespace Bedsit.Game
{
    /// <summary>
    /// One piece of mess in the bedsit. While untidy it carries a faint pulsing dust-glow (so it can be found by looking around);
    /// tapping it plays a short tidy animation (pop, spin, shrink away) with a burst of sparkles, then it is gone for good.
    /// </summary>
    public class ClutterItem : MonoBehaviour
    {
        public string Kind = "clutter";
        public float PickRadius = 0.25f;           // world radius used for hit testing and the glow size
        public float Height = 0.2f;                // for the pick centre
        public CompassDirection PrimaryView;       // the view that sees it best (for the compass pips)
        public bool Tidied { get; private set; }
        public bool Tidying { get; private set; }
        public event Action<ClutterItem> Gone;

        public Vector3 PickCentre => transform.position + Vector3.up * (Height * 0.5f);

        Renderer[] _renderers;
        MaterialPropertyBlock _mpb;
        Transform _glow, _glint;
        SpriteRenderer _glowRenderer, _glintRenderer;
        float _phase, _hover;
        Vector3 _baseScale;
        static Camera _cam;

        void Awake()
        {
            _renderers = GetComponentsInChildren<Renderer>(true);
            _mpb = new MaterialPropertyBlock();
            _baseScale = transform.localScale;
            _phase = UnityEngine.Random.value * 6.28f;
        }

        public void AttachGlow(int layer)
        {
            var go = new GameObject("Glow");
            go.layer = layer;                                   // never rendered in the mirror
            go.transform.SetParent(transform, false);
            go.transform.localPosition = new Vector3(0f, Height * 0.5f, 0f);
            _glowRenderer = go.AddComponent<SpriteRenderer>();
            _glowRenderer.sprite = FxSprites.SoftCircle;
            _glowRenderer.sortingOrder = 5;
            _glowRenderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            _glowRenderer.receiveShadows = false;
            _glow = go.transform;

            // a twinkling gold glint above the mess: the "this can be tidied" signal that reads from across the room
            var gl = new GameObject("Glint");
            gl.layer = layer;
            gl.transform.SetParent(transform, false);
            _glintRenderer = gl.AddComponent<SpriteRenderer>();
            _glintRenderer.sprite = FxSprites.Star;
            _glintRenderer.sortingOrder = 6;
            _glintRenderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            _glintRenderer.receiveShadows = false;
            _glint = gl.transform;
        }

        public void SetHover(bool on) { _hover = on ? 1f : 0f; }

        void LateUpdate()
        {
            if (Tidied) return;
            if (_cam == null) _cam = Camera.main;
            if (_glow != null && _cam != null)
            {
                float inv = 1f / Mathf.Max(0.0001f, transform.lossyScale.x);
                Vector3 centre = PickCentre;
                Vector3 toCam = (_cam.transform.position - centre).normalized;
                float pulse = 0.5f + 0.5f * Mathf.Sin(Time.time * 2.0f + _phase);
                float live = Tidying ? 0f : 1f;
                _glow.position = centre + toCam * 0.12f;
                _glow.rotation = _cam.transform.rotation;
                _glowRenderer.color = new Color(1f, 0.86f, 0.45f, (0.20f + 0.16f * pulse) * live + 0.18f * _hover);
                _glow.localScale = Vector3.one * (Mathf.Max(PickRadius * 3.4f, 0.5f) * (0.92f + 0.10f * pulse)) * inv;

                // glint: twinkles on a slow beat, hovering just above the item
                float tw = Mathf.Max(0f, Mathf.Sin(Time.time * 3.1f + _phase * 1.7f));
                _glint.position = centre + Vector3.up * (Height * 0.5f + 0.10f) + toCam * 0.14f;
                _glint.rotation = _cam.transform.rotation * Quaternion.Euler(0f, 0f, Time.time * 25f);
                _glint.localScale = Vector3.one * (0.10f + 0.22f * tw + 0.10f * _hover) * inv;
                _glintRenderer.color = new Color(1f, 0.93f, 0.60f, (0.35f + 0.65f * tw) * live);
            }
            float flash = 0.22f * _hover;
            if (_renderers != null && !Tidying)
                foreach (var r in _renderers)
                {
                    if (r == null || r == _glowRenderer || r == _glintRenderer) continue;
                    r.GetPropertyBlock(_mpb); _mpb.SetFloat("_Flash", flash); r.SetPropertyBlock(_mpb);
                }
        }

        /// <summary>Start the tidy-away animation. Safe to call once.</summary>
        public bool Tidy()
        {
            if (Tidied || Tidying) return false;
            Tidying = true;
            StartCoroutine(TidyRoutine());
            return true;
        }

        IEnumerator TidyRoutine()
        {
            SparkBurst.Spawn(PickCentre, Mathf.Max(0.15f, PickRadius), 14);
            if (_glowRenderer != null) _glowRenderer.enabled = false;
            if (_glintRenderer != null) _glintRenderer.enabled = false;
            Vector3 p0 = transform.position;
            Quaternion r0 = transform.rotation;
            const float dur = 0.5f;
            for (float t = 0f; t < dur; t += Time.deltaTime)
            {
                float k = t / dur;
                float pop = k < 0.25f ? Mathf.SmoothStep(1f, 1.22f, k / 0.25f) : Mathf.Lerp(1.22f, 0f, Mathf.SmoothStep(0f, 1f, (k - 0.25f) / 0.75f));
                transform.localScale = _baseScale * Mathf.Max(0f, pop);
                transform.position = p0 + Vector3.up * (0.28f * Mathf.SmoothStep(0f, 1f, k));
                transform.rotation = Quaternion.Euler(0f, 360f * k * k, 0f) * r0;
                foreach (var r in _renderers)
                {
                    if (r == null || r == _glowRenderer || r == _glintRenderer) continue;
                    r.GetPropertyBlock(_mpb); _mpb.SetFloat("_Flash", 0.5f * (1f - k)); r.SetPropertyBlock(_mpb);
                }
                yield return null;
            }
            Tidied = true; Tidying = false;
            Gone?.Invoke(this);
            gameObject.SetActive(false);
        }
    }

    /// <summary>Procedurally drawn soft sprites shared by the glows, sparkles and the HUD (no asset files).</summary>
    public static class FxSprites
    {
        static Sprite _soft, _star, _ring;

        public static Sprite SoftCircle => _soft != null ? _soft : (_soft = Make(64, (x, y) => { float r = Mathf.Clamp01(1f - Mathf.Sqrt(x * x + y * y)); return r * r; }));
        public static Sprite Star => _star != null ? _star : (_star = Make(64, (x, y) =>
        {
            float ax = Mathf.Abs(x), ay = Mathf.Abs(y);
            float d = Mathf.Pow(Mathf.Pow(ax, 0.5f) + Mathf.Pow(ay, 0.5f), 2f);               // astroid-like four-point star
            float s = Mathf.Clamp01(1f - d * 1.0f);
            float core = Mathf.Clamp01(1f - Mathf.Sqrt(x * x + y * y) * 2.2f);
            return Mathf.Clamp01(s * s * 1.2f + core * core);
        }));
        public static Sprite Ring => _ring != null ? _ring : (_ring = Make(128, (x, y) =>
        {
            float r = Mathf.Sqrt(x * x + y * y);
            return Mathf.Clamp01(1f - Mathf.Abs(r - 0.82f) / 0.12f);
        }));

        static Sprite Make(int n, Func<float, float, float> alpha)
        {
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear };
            var px = new Color32[n * n];
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float fx = (x + 0.5f) / n * 2f - 1f, fy = (y + 0.5f) / n * 2f - 1f;
                    byte a = (byte)(Mathf.Clamp01(alpha(fx, fy)) * 255f);
                    px[y * n + x] = new Color32(255, 255, 255, a);
                }
            tex.SetPixels32(px); tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), n);      // 1 unit across
        }
    }

    /// <summary>A short burst of billboarded sparkles (gold/white) that fly out, fall and fade.</summary>
    public class SparkBurst : MonoBehaviour
    {
        struct P { public Transform T; public SpriteRenderer R; public Vector3 V; public float Spin, Life, Size; }
        P[] _p;
        float _t;
        const float Life = 0.75f;

        public static void Spawn(Vector3 pos, float radius, int count)
        {
            var go = new GameObject("SparkBurst");
            go.transform.position = pos;
            var b = go.AddComponent<SparkBurst>();
            b._p = new P[count];
            for (int i = 0; i < count; i++)
            {
                var g = new GameObject("s"); g.transform.SetParent(go.transform, false);
                g.layer = BedsitLayers.MirrorGlass;
                var r = g.AddComponent<SpriteRenderer>();
                r.sprite = i % 3 == 0 ? FxSprites.SoftCircle : FxSprites.Star;
                r.sortingOrder = 8;
                r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                r.color = i % 2 == 0 ? new Color(1f, 0.9f, 0.5f, 1f) : new Color(1f, 1f, 1f, 1f);
                var dir = UnityEngine.Random.onUnitSphere; dir.y = Mathf.Abs(dir.y) * 0.8f + 0.2f;
                b._p[i] = new P { T = g.transform, R = r, V = dir * UnityEngine.Random.Range(0.5f, 1.3f) * (0.6f + radius), Spin = UnityEngine.Random.Range(-240f, 240f), Size = UnityEngine.Random.Range(0.06f, 0.14f) };
                g.transform.localPosition = dir * radius * 0.3f;
            }
        }

        void LateUpdate()
        {
            _t += Time.deltaTime;
            var cam = Camera.main;
            float k = _t / Life;
            for (int i = 0; i < _p.Length; i++)
            {
                var p = _p[i];
                p.V += Vector3.down * 1.6f * Time.deltaTime;
                p.T.localPosition += p.V * Time.deltaTime;
                if (cam != null) p.T.rotation = cam.transform.rotation * Quaternion.Euler(0f, 0f, p.Spin * _t);
                p.T.localScale = Vector3.one * p.Size * (1f + 0.5f * Mathf.Sin(k * 3.14f));
                var c = p.R.color; c.a = Mathf.Clamp01(1f - k * k); p.R.color = c;
                _p[i] = p;
            }
            if (_t >= Life) Destroy(gameObject);
        }
    }
}
