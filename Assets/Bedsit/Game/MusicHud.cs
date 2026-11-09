using System.Collections.Generic;
using Bedsit.Music;
using UnityEngine;
using UnityEngine.UI;

namespace Bedsit.Game
{
    /// <summary>
    /// Presentation of the rhythm layer: four pads along the bottom, notes scrolling down towards them. Visible only in RHYTHM
    /// mode (faded out in MIXING mode); contains no diagnostic text.
    /// </summary>
    public class MusicHud : MonoBehaviour
    {
        public MusicPoc Poc;

        const float PadTop = 0.18f, LaneTop = 0.60f, Scroll = 2.2f;
        static readonly Color[] PadColors =
        {
            new Color(1.00f, 0.45f, 0.20f), new Color(0.25f, 0.85f, 1.00f), new Color(0.80f, 0.45f, 1.00f), new Color(0.45f, 1.00f, 0.45f),
        };

        Canvas _canvas;
        CanvasGroup _group;
        readonly Image[] _pads = new Image[4];
        readonly float[] _flash = new float[4];
        readonly List<Image> _notePool = new List<Image>();
        Image _bar;
        float _alpha;

        void Awake()
        {
            var go = new GameObject("MusicHudCanvas");
            go.transform.SetParent(transform, false);
            _canvas = go.AddComponent<Canvas>();
            _canvas.renderMode = RenderMode.ScreenSpaceOverlay; _canvas.sortingOrder = 90;
            go.AddComponent<CanvasScaler>().uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            _group = go.AddComponent<CanvasGroup>(); _group.alpha = 0f; _group.blocksRaycasts = false; _group.interactable = false;
            for (int i = 0; i < 4; i++)
            {
                float x0 = InputRegions.SideWidth + i * (1f - 2f * InputRegions.SideWidth) / 4f, x1 = x0 + (1f - 2f * InputRegions.SideWidth) / 4f;
                _pads[i] = Rect(go.transform, "Pad" + (i + 1), new Vector2(x0 + 0.004f, 0.01f), new Vector2(x1 - 0.004f, PadTop - 0.01f), new Color(PadColors[i].r, PadColors[i].g, PadColors[i].b, 0.30f));
            }
            _bar = Rect(go.transform, "BuildBar", new Vector2(InputRegions.SideWidth, PadTop), new Vector2(InputRegions.SideWidth, PadTop + 0.006f), new Color(1f, 1f, 1f, 0.6f));
        }

        static Image Rect(Transform parent, string name, Vector2 amin, Vector2 amax, Color c)
        {
            var img = new GameObject(name).AddComponent<Image>();
            img.transform.SetParent(parent, false);
            img.color = c; img.raycastTarget = false;
            var rt = img.rectTransform; rt.anchorMin = amin; rt.anchorMax = amax; rt.offsetMin = rt.offsetMax = Vector2.zero;
            return img;
        }

        void Update()
        {
            if (Poc == null || Poc.Session == null) return;
            var s = Poc.Session; double now = s.Mixer.Time;
            bool rhythm = s.Director.Mode == MusicMode.Rhythm;
            _alpha = Mathf.MoveTowards(_alpha, rhythm ? 1f : 0f, Time.unscaledDeltaTime * 2.5f);
            _group.alpha = _alpha;
            if (_alpha <= 0.001f) return;

            for (int i = 0; i < 4; i++)
            {
                if (UnityEngine.Input.GetKey(i == 0 ? KeyCode.D : i == 1 ? KeyCode.F : i == 2 ? KeyCode.J : KeyCode.K)) _flash[i] = 1f;
                _flash[i] = Mathf.MoveTowards(_flash[i], 0f, Time.unscaledDeltaTime * 4f);
                var c = PadColors[i]; _pads[i].color = new Color(c.r, c.g, c.b, 0.28f + 0.5f * _flash[i]);
            }

            // notes: pending notes scroll towards the pad line; hit/missed notes are not drawn
            int used = 0;
            foreach (var n in s.Judge.PendingNotes(now, Scroll))
            {
                float k = Mathf.Clamp01((float)((n.Time - now) / Scroll));
                float y = Mathf.Lerp(PadTop, LaneTop, k);
                int lane = Mathf.Clamp(n.Pad - 1, 0, 3);
                float w = (1f - 2f * InputRegions.SideWidth) / 4f, x0 = InputRegions.SideWidth + lane * w;
                var img = NoteImage(used++);
                var rt = img.rectTransform;
                rt.anchorMin = new Vector2(x0 + w * 0.18f, y); rt.anchorMax = new Vector2(x0 + w * 0.82f, y + 0.028f);
                rt.offsetMin = rt.offsetMax = Vector2.zero;
                var c = PadColors[lane]; img.color = new Color(c.r, c.g, c.b, Mathf.Lerp(1f, 0.55f, k));
                img.gameObject.SetActive(true);
            }
            for (int i = used; i < _notePool.Count; i++) _notePool[i].gameObject.SetActive(false);

            // build progress bar along the pad line
            var w0 = Poc.Session.Director.CurrentWindow;
            float prog = w0 == null ? 0f : Mathf.Clamp01((float)((now - w0.Start) / Mathf.Max(0.001f, (float)(w0.End - w0.Start))));
            var rt2 = _bar.rectTransform; rt2.anchorMax = new Vector2(InputRegions.SideWidth + prog * (1f - 2f * InputRegions.SideWidth), PadTop + 0.006f);
        }

        Image NoteImage(int i)
        {
            while (_notePool.Count <= i)
            {
                var img = Rect(_canvas.transform, "Note", Vector2.zero, Vector2.one, Color.white);
                _notePool.Add(img);
            }
            return _notePool[i];
        }
    }
}
