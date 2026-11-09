using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace Bedsit.Game
{
    /// <summary>
    /// Presentation for Act One (text-free):
    ///  * headphones - an earcup on each side of the view and a band across the top, sliding in when the player puts them on and pulsing with the beat;
    ///  * a small compass rose in the top-left: one wedge per view, gold pips for the mess still left in it, the wedge you are facing lit,
    ///    and the north wedge flashing once somebody is knocking;
    ///  * a tidy meter under it that fills with gold as the room is cleaned, with a star at the "clean enough" mark;
    ///  * a ring that pops where you tap an item.
    /// All sprites are drawn procedurally.
    /// </summary>
    public class ActOneHud : MonoBehaviour
    {
        public ActOne Act;

        static readonly Color Gold = new Color(1f, 0.82f, 0.30f);
        Canvas _canvas; RectTransform _canvasRect;
        RectTransform _cupL, _cupR, _band;
        readonly Image[] _wedges = new Image[4];
        readonly List<Image>[] _pips = new List<Image>[4];
        RectTransform _rose;
        Image _barFill, _barStar, _barGlow;
        RectTransform _barFillRt;
        readonly List<Image> _rings = new List<Image>();
        readonly List<float> _ringAge = new List<float>();
        float _beatPulse;

        const float BarW = 150f, BarH = 12f;

        void Awake()
        {
            var go = new GameObject("ActOneCanvas");
            go.transform.SetParent(transform, false);
            _canvas = go.AddComponent<Canvas>();
            _canvas.renderMode = RenderMode.ScreenSpaceOverlay; _canvas.sortingOrder = 95;
            var scaler = go.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize; scaler.referenceResolution = new Vector2(1280, 720); scaler.matchWidthOrHeight = 0.5f;
            _canvasRect = go.GetComponent<RectTransform>();
            BuildHeadphones(go.transform);
            BuildCompass(go.transform);
            BuildBar(go.transform);
        }

        // ------------------------------------------------------------------------------------------------ build

        static Image Img(Transform parent, string name, Sprite sprite, Color c, bool sliced = false)
        {
            var im = new GameObject(name).AddComponent<Image>();
            im.transform.SetParent(parent, false);
            im.sprite = sprite; im.color = c; im.raycastTarget = false;
            if (sliced && sprite != null) im.type = Image.Type.Sliced;
            return im;
        }

        static void Place(RectTransform rt, Vector2 anchor, Vector2 pivot, Vector2 pos, Vector2 size)
        {
            rt.anchorMin = rt.anchorMax = anchor; rt.pivot = pivot; rt.anchoredPosition = pos; rt.sizeDelta = size;
        }

        void BuildHeadphones(Transform root)
        {
            var rr = Sprites.RoundedRect;
            // band across the top
            var band = Img(root, "HeadBand", rr, new Color(0.10f, 0.10f, 0.13f, 0.96f), true);
            _band = band.rectTransform; Place(_band, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(0, 60), new Vector2(780, 40));
            var bandHi = Img(_band, "Hi", rr, new Color(0.28f, 0.28f, 0.34f, 0.9f), true);
            Place(bandHi.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(0, -3), new Vector2(740, 8));
            _cupL = MakeCup(root, "CupL", true); _cupR = MakeCup(root, "CupR", false);
        }

        RectTransform MakeCup(Transform root, string name, bool left)
        {
            var rr = Sprites.RoundedRect;
            var outer = Img(root, name, rr, new Color(0.10f, 0.10f, 0.13f, 0.97f), true);
            var rt = outer.rectTransform;
            Place(rt, new Vector2(left ? 0f : 1f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(left ? -180 : 180, 0), new Vector2(150, 300));
            var rim = Img(rt, "Rim", rr, new Color(0.30f, 0.30f, 0.37f, 0.95f), true);
            Place(rim.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(left ? 6 : -6, 0), new Vector2(128, 270));
            var pad = Img(rt, "Pad", rr, new Color(0.17f, 0.17f, 0.21f, 1f), true);
            Place(pad.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(left ? 8 : -8, 0), new Vector2(108, 240));
            var shine = Img(rt, "Shine", rr, new Color(1f, 1f, 1f, 0.10f), true);
            Place(shine.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(left ? 22 : -22, 40), new Vector2(26, 120));
            return rt;
        }

        void BuildCompass(Transform root)
        {
            var holder = new GameObject("CompassRose").AddComponent<RectTransform>();
            holder.SetParent(root, false);
            Place(holder, new Vector2(0f, 1f), new Vector2(0.5f, 0.5f), new Vector2(96, -96), new Vector2(10, 10));
            _rose = holder;
            var disc = Img(holder, "Disc", Sprites.Disc, new Color(0f, 0f, 0f, 0.28f));
            Place(disc.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(150, 150));
            Vector2[] dirs = { Vector2.up, Vector2.right, Vector2.down, Vector2.left };
            float[] rot = { 0f, -90f, 180f, 90f };
            for (int i = 0; i < 4; i++)
            {
                var w = Img(holder, "Wedge" + i, Sprites.Triangle, new Color(1f, 1f, 1f, 0.35f));
                Place(w.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), dirs[i] * 22f, new Vector2(30, 26));
                w.rectTransform.localRotation = Quaternion.Euler(0, 0, rot[i]);
                _wedges[i] = w;
                _pips[i] = new List<Image>();
            }
            var hub = Img(holder, "Hub", Sprites.Disc, new Color(1f, 1f, 1f, 0.5f));
            Place(hub.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(8, 8));
        }

        void BuildBar(Transform root)
        {
            var bg = Img(root, "TidyBarBg", Sprites.RoundedRect, new Color(0f, 0f, 0f, 0.42f), true);
            Place(bg.rectTransform, new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(24, -186), new Vector2(BarW + 8, BarH + 8));
            _barFill = Img(bg.rectTransform, "Fill", Sprites.RoundedRect, Gold, true);
            _barFillRt = _barFill.rectTransform;
            Place(_barFillRt, new Vector2(0f, 0.5f), new Vector2(0f, 0.5f), new Vector2(4, 0), new Vector2(0, BarH));
            var mark = Img(bg.rectTransform, "Mark", null, new Color(1f, 1f, 1f, 0.8f));
            Place(mark.rectTransform, new Vector2(0f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(4 + BarW * 0.8f, 0), new Vector2(2, BarH + 6));
            _barGlow = Img(bg.rectTransform, "Glow", Sprites.Disc, new Color(1f, 0.85f, 0.3f, 0f));
            Place(_barGlow.rectTransform, new Vector2(1f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(18, 0), new Vector2(50, 50));
            _barStar = Img(bg.rectTransform, "Star", FxSprites.Star, new Color(1f, 1f, 1f, 0.35f));
            Place(_barStar.rectTransform, new Vector2(1f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(18, 0), new Vector2(34, 34));
        }

        // ------------------------------------------------------------------------------------------------ per-frame

        public void PulseAt(Vector2 screenPos)
        {
            RectTransformUtility.ScreenPointToLocalPointInRectangle(_canvasRect, screenPos, null, out var local);
            var ring = Img(_canvas.transform, "Ring", FxSprites.Ring, new Color(1f, 0.9f, 0.5f, 0.9f));
            Place(ring.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), local, new Vector2(40, 40));
            _rings.Add(ring); _ringAge.Add(0f);
        }

        void Update()
        {
            if (Act == null) return;
            // headphones slide in, then bob with the beat
            float p = Act.HeadphonesProgress;
            var poc = MusicPoc.Instance;
            if (poc != null && poc.Session != null && Act.HeadphonesOn)
            {
                double beat = poc.Session.Mixer.Time / poc.Session.Director.BeatSeconds;
                float frac = (float)(beat - System.Math.Floor(beat));
                _beatPulse = Mathf.Lerp(_beatPulse, Mathf.Exp(-5f * frac), Time.unscaledDeltaTime * 30f);
            }
            float s = 1f + 0.035f * _beatPulse;
            _cupL.anchoredPosition = new Vector2(Mathf.Lerp(-180f, 6f, p), 0f); _cupL.localScale = new Vector3(s, s, 1f);
            _cupR.anchoredPosition = new Vector2(Mathf.Lerp(180f, -6f, p), 0f); _cupR.localScale = new Vector3(s, s, 1f);
            _band.anchoredPosition = new Vector2(0f, Mathf.Lerp(60f, 17f, p));

            // compass: pips + facing + knock
            var g = BedsitGame.Instance;
            var facing = g != null && g.View != null ? g.View.Facing : CompassDirection.North;
            float blink = 0.5f + 0.5f * Mathf.Sin(Time.unscaledTime * 9f);
            Vector2[] dirs = { Vector2.up, Vector2.right, Vector2.down, Vector2.left };
            for (int i = 0; i < 4; i++)
            {
                var d = (CompassDirection)i;
                int n = Act.Remaining(d);
                bool isFacing = d == facing;
                Color c = isFacing ? new Color(1f, 0.95f, 0.8f, 0.95f) : new Color(1f, 1f, 1f, 0.32f);
                if (i == 0 && Act.KnockPending) c = Color.Lerp(new Color(1f, 1f, 1f, 0.5f), Gold, blink);
                _wedges[i].color = c;
                while (_pips[i].Count < n) _pips[i].Add(MakePip());
                for (int k = 0; k < _pips[i].Count; k++)
                {
                    bool on = k < n;
                    _pips[i][k].enabled = on;
                    if (!on) continue;
                    Vector2 perp = new Vector2(-dirs[i].y, dirs[i].x);
                    _pips[i][k].rectTransform.anchoredPosition = dirs[i] * 58f + perp * ((k - (n - 1) * 0.5f) * 11f);
                    var pc = Gold; pc.a = isFacing ? 1f : 0.75f; _pips[i][k].color = pc;
                }
            }

            // tidy meter
            float f = Act.TidyFraction;
            _barFillRt.sizeDelta = new Vector2(BarW * f, BarH);
            bool clean = Act.IsClean;
            _barStar.color = clean ? new Color(1f, 0.92f, 0.5f, 1f) : new Color(1f, 1f, 1f, 0.30f);
            _barGlow.color = new Color(1f, 0.85f, 0.3f, clean ? 0.25f + 0.2f * blink : 0f);
            _barFill.color = clean ? Color.Lerp(Gold, new Color(1f, 0.95f, 0.6f), blink * 0.5f) : Gold;

            // tap rings
            for (int i = _rings.Count - 1; i >= 0; i--)
            {
                _ringAge[i] += Time.unscaledDeltaTime;
                float k = _ringAge[i] / 0.45f;
                if (k >= 1f) { Destroy(_rings[i].gameObject); _rings.RemoveAt(i); _ringAge.RemoveAt(i); continue; }
                _rings[i].rectTransform.sizeDelta = Vector2.one * Mathf.Lerp(30f, 150f, 1f - (1f - k) * (1f - k));
                var c = _rings[i].color; c.a = 0.9f * (1f - k); _rings[i].color = c;
            }
        }

        Image MakePip()
        {
            var p = Img(_rose, "Pip", Sprites.Disc, Gold);
            Place(p.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(9, 9));
            return p;
        }

        // ------------------------------------------------------------------------------------------------ sprites

        static class Sprites
        {
            static Sprite _disc, _tri, _rr;
            public static Sprite Disc => _disc != null ? _disc : (_disc = Make(64, 0, (x, y) => Mathf.Clamp01((1f - Mathf.Sqrt(x * x + y * y)) * 24f)));
            public static Sprite Triangle => _tri != null ? _tri : (_tri = Make(64, 0, (x, y) =>
            {
                // upward triangle, apex at the top
                float yy = (y + 1f) * 0.5f;                       // 0 bottom .. 1 top
                float half = (1f - yy) * 0.95f;                   // half-width shrinks towards the apex
                float edge = (half - Mathf.Abs(x)) * 14f;
                return Mathf.Clamp01(edge) * Mathf.Clamp01((yy - 0.04f) * 20f) * Mathf.Clamp01((0.98f - yy) * 20f);
            }));
            public static Sprite RoundedRect => _rr != null ? _rr : (_rr = MakeRounded(48, 16));

            static Sprite Make(int n, int border, System.Func<float, float, float> alpha)
            {
                var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear };
                var px = new Color32[n * n];
                for (int y = 0; y < n; y++)
                    for (int x = 0; x < n; x++)
                    {
                        float fx = (x + 0.5f) / n * 2f - 1f, fy = (y + 0.5f) / n * 2f - 1f;
                        px[y * n + x] = new Color32(255, 255, 255, (byte)(Mathf.Clamp01(alpha(fx, fy)) * 255f));
                    }
                tex.SetPixels32(px); tex.Apply();
                return Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), 100f);
            }

            static Sprite MakeRounded(int n, int r)
            {
                var tex = new Texture2D(n, n, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear };
                var px = new Color32[n * n];
                for (int y = 0; y < n; y++)
                    for (int x = 0; x < n; x++)
                    {
                        float cx = Mathf.Clamp(x + 0.5f, r, n - r), cy = Mathf.Clamp(y + 0.5f, r, n - r);
                        float d = Vector2.Distance(new Vector2(x + 0.5f, y + 0.5f), new Vector2(cx, cy));
                        px[y * n + x] = new Color32(255, 255, 255, (byte)(Mathf.Clamp01(r - d + 0.5f) * 255f));
                    }
                tex.SetPixels32(px); tex.Apply();
                return Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), 100f, 0, SpriteMeshType.FullRect, new Vector4(r, r, r, r));
            }
        }
    }
}
