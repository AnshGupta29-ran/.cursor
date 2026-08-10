using System;
using UnityEngine;
using UnityEngine.UI;

namespace Tidewatch.Game
{
    /// <summary>
    /// Small code-driven uGUI helpers so every screen is styled consistently (no default
    /// gray panels). All screens are built in code from these primitives.
    /// </summary>
    public static class Ui
    {
        public static readonly Color PanelBg = new Color(0.08f, 0.11f, 0.16f, 0.92f);
        public static readonly Color PanelBgLight = new Color(0.12f, 0.16f, 0.22f, 0.92f);
        public static readonly Color Accent = new Color(0.95f, 0.78f, 0.30f);
        public static readonly Color TextCol = new Color(0.92f, 0.93f, 0.95f);
        public static readonly Color SubText = new Color(0.65f, 0.70f, 0.75f);
        public static readonly Color Valid = new Color(0.25f, 0.85f, 0.40f);
        public static readonly Color Invalid = new Color(0.95f, 0.30f, 0.30f);

        public static Font DefaultFont => Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");

        public static RectTransform Root(Transform parent, string name)
        {
            var go = new GameObject(name, typeof(RectTransform));
            var rt = (RectTransform)go.transform;
            rt.SetParent(parent, false);
            Stretch(rt);
            return rt;
        }

        public static void Stretch(RectTransform rt)
        {
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
        }

        public static RectTransform Panel(Transform parent, string name, Color? bg = null)
        {
            var rt = Root(parent, name);
            var img = rt.gameObject.AddComponent<Image>();
            img.color = bg ?? PanelBg;
            return rt;
        }

        public static Text Label(Transform parent, string name, string text, int size, TextAnchor anchor = TextAnchor.MiddleCenter)
        {
            var rt = Root(parent, name);
            var t = rt.gameObject.AddComponent<Text>();
            t.font = DefaultFont;
            t.text = text;
            t.fontSize = size;
            t.alignment = anchor;
            t.color = TextCol;
            return t;
        }

        public static Button Button(Transform parent, string name, string label, Action onClick, Color? bg = null)
        {
            var rt = Root(parent, name);
            var img = rt.gameObject.AddComponent<Image>();
            img.color = bg ?? PanelBgLight;
            var btn = rt.gameObject.AddComponent<Button>();
            var txt = Label(rt, "Label", label, 22);
            Stretch(txt.rectTransform);
            btn.targetGraphic = img;
            var colors = btn.colors;
            colors.highlightedColor = Accent;
            colors.pressedColor = Accent * 0.8f;
            btn.colors = colors;
            if (onClick != null) btn.onClick.AddListener(() => onClick());
            return btn;
        }

        public static Slider Slider(Transform parent, string name, float value, Action<float> onChange)
        {
            var rt = Root(parent, name);
            var slider = rt.gameObject.AddComponent<Slider>();
            var bgImg = rt.gameObject.AddComponent<Image>();
            bgImg.color = PanelBgLight;
            // Fill area.
            var fillArea = Root(rt, "FillArea");
            var fill = Panel(fillArea, "Fill", Accent);
            slider.fillRect = fill;
            // Handle.
            var handle = Root(rt, "Handle");
            var hImg = handle.gameObject.AddComponent<Image>();
            hImg.color = TextCol;
            handle.sizeDelta = new Vector2(20, 20);
            slider.handleRect = handle;
            slider.targetGraphic = hImg;
            slider.minValue = 0f;
            slider.maxValue = 1f;
            slider.value = value;
            if (onChange != null) slider.onValueChanged.AddListener(v => onChange(v));
            return slider;
        }

        public static Toggle Toggle(Transform parent, string name, bool value, string label, Action<bool> onChange)
        {
            var rt = Root(parent, name);
            var toggle = rt.gameObject.AddComponent<Toggle>();
            var bg = Panel(rt, "Bg", PanelBgLight);
            bg.sizeDelta = new Vector2(28, 28);
            bg.anchorMin = new Vector2(0, 0.5f);
            bg.anchorMax = new Vector2(0, 0.5f);
            bg.pivot = new Vector2(0, 0.5f);
            bg.anchoredPosition = Vector2.zero;
            var check = Panel(bg, "Check", Accent);
            check.anchorMin = Vector2.zero;
            check.anchorMax = Vector2.one;
            check.offsetMin = new Vector2(5, 5);
            check.offsetMax = new Vector2(-5, -5);
            toggle.graphic = check.GetComponent<Image>();
            toggle.targetGraphic = bg.GetComponent<Image>();
            var txt = Label(rt, "Label", label, 20, TextAnchor.MiddleLeft);
            txt.rectTransform.anchorMin = new Vector2(0, 0);
            txt.rectTransform.anchorMax = new Vector2(1, 1);
            txt.rectTransform.offsetMin = new Vector2(40, 0);
            txt.rectTransform.offsetMax = Vector2.zero;
            toggle.isOn = value;
            if (onChange != null) toggle.onValueChanged.AddListener(v => onChange(v));
            return toggle;
        }

        /// <summary>Position a RectTransform within its parent using anchors + offsets.</summary>
        public static void Place(RectTransform rt, Vector2 anchorMin, Vector2 anchorMax, Vector2 offsetMin, Vector2 offsetMax)
        {
            rt.anchorMin = anchorMin;
            rt.anchorMax = anchorMax;
            rt.offsetMin = offsetMin;
            rt.offsetMax = offsetMax;
        }

        /// <summary>Convenience: place at a fractional rect of the parent.</summary>
        public static void Frac(RectTransform rt, float x0, float y0, float x1, float y1, float pad = 0f)
        {
            Place(rt, new Vector2(x0, y0), new Vector2(x1, y1), new Vector2(pad, pad), new Vector2(-pad, -pad));
        }

        /// <summary>Anchor an element to a center point (0..1 fraction) with a fixed size.</summary>
        public static void Anchored(this RectTransform rt, Vector2 center, Vector2 size)
        {
            rt.anchorMin = center;
            rt.anchorMax = center;
            rt.pivot = new Vector2(0.5f, 0.5f);
            rt.sizeDelta = size;
            rt.anchoredPosition = Vector2.zero;
        }
    }
}
