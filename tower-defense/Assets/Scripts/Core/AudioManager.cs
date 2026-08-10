using System.Collections.Generic;
using UnityEngine;

namespace TD.Core
{
    public enum SfxId
    {
        Shoot, CannonHit, FrostHit, EnemyDie, BaseHit,
        Build, Upgrade, Sell, UIClick, WaveStart, Victory, Defeat
    }

    /// <summary>
    /// Procedural sound effects: clips are synthesized at startup (no audio
    /// assets needed) and played through a small pool of AudioSources.
    /// Volumes come from SaveSystem.Settings.
    /// </summary>
    public class AudioManager : MonoBehaviour
    {
        public static AudioManager Instance { get; private set; }

        const int SampleRate = 44100;
        readonly Dictionary<SfxId, AudioClip> _clips = new Dictionary<SfxId, AudioClip>();
        readonly List<AudioSource> _sources = new List<AudioSource>();
        readonly Dictionary<SfxId, float> _lastPlay = new Dictionary<SfxId, float>();
        int _next;

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            for (int i = 0; i < 6; i++)
            {
                var go = new GameObject($"sfx{i}");
                go.transform.SetParent(transform, false);
                _sources.Add(go.AddComponent<AudioSource>());
            }
            BuildClips();
        }

        public void Play(SfxId id, float volumeScale = 1f)
        {
            if (!_clips.TryGetValue(id, out var clip)) return;
            // throttle identical sfx so 20 arrows landing on one frame don't stack
            if (_lastPlay.TryGetValue(id, out float t) && Time.unscaledTime - t < 0.045f) return;
            _lastPlay[id] = Time.unscaledTime;

            var src = _sources[_next];
            _next = (_next + 1) % _sources.Count;
            var s = SaveSystem.Settings;
            src.PlayOneShot(clip, s.masterVolume * s.sfxVolume * volumeScale);
        }

        // ------------------------------------------------------------------
        // Clip synthesis
        // ------------------------------------------------------------------
        void BuildClips()
        {
            _clips[SfxId.Shoot] = Render(0.09f, t =>
                Mathf.Sin(2f * Mathf.PI * Mathf.Lerp(880f, 320f, t) * t * 1f) * Envelope(t, 40f));
            _clips[SfxId.CannonHit] = Render(0.28f, t => Noise(t) * Envelope(t, 6f) * 0.9f
                + Mathf.Sin(2f * Mathf.PI * Mathf.Lerp(120f, 40f, t) * t) * Envelope(t, 8f));
            _clips[SfxId.FrostHit] = Render(0.18f, t =>
                Mathf.Sin(2f * Mathf.PI * (1400f + 600f * Mathf.Sin(t * 40f)) * t) * Envelope(t, 20f) * 0.6f);
            _clips[SfxId.EnemyDie] = Render(0.16f, t =>
                Mathf.Sin(2f * Mathf.PI * Mathf.Lerp(600f, 90f, t) * t) * Envelope(t, 10f) * 0.8f);
            _clips[SfxId.BaseHit] = Render(0.35f, t => Noise(t) * Envelope(t, 4f)
                + Mathf.Sin(2f * Mathf.PI * 60f * t) * Envelope(t, 5f));
            _clips[SfxId.Build] = Render(0.12f, t =>
                Mathf.Sin(2f * Mathf.PI * 500f * t) * Envelope(t, 30f) * 0.7f
                + Mathf.Sin(2f * Mathf.PI * 750f * t) * Envelope(t, 50f) * 0.4f);
            _clips[SfxId.Upgrade] = Arp(0.30f, new[] { 440f, 554f, 659f, 880f });
            _clips[SfxId.Sell] = Arp(0.22f, new[] { 660f, 440f });
            _clips[SfxId.UIClick] = Render(0.05f, t =>
                Mathf.Sin(2f * Mathf.PI * 900f * t) * Envelope(t, 80f) * 0.5f);
            _clips[SfxId.WaveStart] = Arp(0.4f, new[] { 220f, 220f, 330f });
            _clips[SfxId.Victory] = Arp(0.7f, new[] { 523f, 659f, 784f, 1047f });
            _clips[SfxId.Defeat] = Arp(0.8f, new[] { 392f, 330f, 262f, 196f });
        }

        static float Envelope(float t, float sharpness) =>
            Mathf.Exp(-t * sharpness);

        static float Noise(float t) =>
            Mathf.PerlinNoise(t * 300f, 0.37f) * 2f - 1f;

        static AudioClip Render(float seconds, System.Func<float, float> f)
        {
            int n = Mathf.CeilToInt(seconds * SampleRate);
            var data = new float[n];
            for (int i = 0; i < n; i++)
                data[i] = Mathf.Clamp(f(i / (float)SampleRate), -1f, 1f) * 0.8f;
            var clip = AudioClip.Create("sfx", n, 1, SampleRate, false);
            clip.SetData(data, 0);
            return clip;
        }

        static AudioClip Arp(float seconds, float[] freqs)
        {
            int n = Mathf.CeilToInt(seconds * SampleRate);
            var data = new float[n];
            float noteLen = seconds / freqs.Length;
            for (int i = 0; i < n; i++)
            {
                float t = i / (float)SampleRate;
                int idx = Mathf.Min(freqs.Length - 1, Mathf.FloorToInt(t / noteLen));
                float nt = t - idx * noteLen;
                data[i] = Mathf.Sin(2f * Mathf.PI * freqs[idx] * t) * Mathf.Exp(-nt * 10f) * 0.7f;
            }
            var clip = AudioClip.Create("arp", n, 1, SampleRate, false);
            clip.SetData(data, 0);
            return clip;
        }
    }
}
