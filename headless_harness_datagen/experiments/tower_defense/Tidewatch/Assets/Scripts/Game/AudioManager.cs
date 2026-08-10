using System.Collections.Generic;
using UnityEngine;
using Tidewatch.Core;

namespace Tidewatch.Game
{
    /// <summary>
    /// All audio is procedurally generated at startup (no licensed assets). Three logical
    /// buses — Master, Music, SFX — are applied per-source (Music source, ambient source,
    /// one-shot SFX source) because an AudioMixer asset can only be authored in the editor;
    /// the volume sliders and mute map onto these buses. Ocean ambience + a music bed loop;
    /// every core action has a distinct synthesized SFX.
    /// </summary>
    public sealed class AudioManager : MonoBehaviour
    {
        private AudioSource _musicSrc;
        private AudioSource _ambienceSrc;
        private AudioSource _sfxSrc;
        private readonly Dictionary<string, AudioClip> _sfx = new Dictionary<string, AudioClip>();
        private GameSettings _settings;

        private const int SR = 44100;

        public void Init(GameSettings settings)
        {
            _settings = settings;

            _musicSrc = MakeSource("Music", true);
            _ambienceSrc = MakeSource("Ambience", true);
            _sfxSrc = MakeSource("SFX", false);

            BuildClips();
            _musicSrc.clip = MakeMusicBed();
            _musicSrc.loop = true;
            _musicSrc.volume = 0.5f;
            _musicSrc.Play();
            _ambienceSrc.clip = MakeOcean();
            _ambienceSrc.loop = true;
            _ambienceSrc.volume = 0.4f;
            _ambienceSrc.Play();

            ApplySettings();
        }

        private AudioSource MakeSource(string name, bool loop)
        {
            var go = new GameObject(name);
            go.transform.SetParent(transform, false);
            var src = go.AddComponent<AudioSource>();
            src.loop = loop;
            src.playOnAwake = false;
            return src;
        }

        private void BuildClips()
        {
            _sfx[TowerIds.BeaconSpire] = Tone(880f, 0.10f, 0.4f, Wave.Sine, 0.4f);
            _sfx[TowerIds.FlareMortar] = Tone(220f, 0.25f, 0.5f, Wave.Square, 0.6f);
            _sfx[TowerIds.PrismArray] = Tone(1320f, 0.08f, 0.3f, Wave.Triangle, 0.4f);
            _sfx[TowerIds.HarpoonBallista] = NoiseBurst(0.08f, 0.5f);
            _sfx[TowerIds.FogBell] = Tone(392f, 0.6f, 0.5f, Wave.Sine, 0.7f);
            _sfx["death"] = Tone(160f, 0.2f, 0.4f, Wave.Sawtooth, 0.5f);
            _sfx["disabled"] = Tone(196f, 0.4f, 0.4f, Wave.Square, 0.4f);
            _sfx["horn"] = Tone(294f, 0.7f, 0.6f, Wave.Sawtooth, 0.6f);
            _sfx["tide"] = MakeWhoosh(0.9f, 0.5f);
            _sfx["lantern"] = Tone(120f, 0.5f, 0.5f, Wave.Sine, 0.6f);
            _sfx["build"] = Tone(520f, 0.12f, 0.4f, Wave.Triangle, 0.5f);
            _sfx["sell"] = Tone(340f, 0.12f, 0.4f, Wave.Triangle, 0.5f);
            _sfx["upgrade"] = Tone(660f, 0.15f, 0.4f, Wave.Sine, 0.5f);
            _sfx["ui"] = Tone(700f, 0.05f, 0.3f, Wave.Sine, 0.4f);
        }

        private enum Wave { Sine, Square, Triangle, Sawtooth }

        private static AudioClip Tone(float freq, float dur, float decay, Wave wave, float vol)
        {
            int n = (int)(SR * dur);
            var data = new float[n];
            for (int i = 0; i < n; i++)
            {
                float t = (float)i / SR;
                float env = Mathf.Exp(-t * (1f / Mathf.Max(0.01f, decay)));
                float ph = 2f * Mathf.PI * freq * t;
                float s;
                switch (wave)
                {
                    case Wave.Square: s = Mathf.Sign(Mathf.Sin(ph)); break;
                    case Wave.Triangle: s = 2f * Mathf.Abs(2f * (t * freq % 1f) - 1f) - 1f; break;
                    case Wave.Sawtooth: s = 2f * (t * freq % 1f) - 1f; break;
                    default: s = Mathf.Sin(ph); break;
                }
                data[i] = s * env * vol;
            }
            var clip = AudioClip.Create($"tone{freq}", n, 1, SR, false);
            clip.SetData(data, 0);
            return clip;
        }

        private static AudioClip NoiseBurst(float dur, float vol)
        {
            int n = (int)(SR * dur);
            var data = new float[n];
            var rng = new System.Random(12345);
            for (int i = 0; i < n; i++)
            {
                float t = (float)i / SR;
                float env = Mathf.Exp(-t * 30f);
                data[i] = (float)(rng.NextDouble() * 2 - 1) * env * vol;
            }
            var clip = AudioClip.Create("noise", n, 1, SR, false);
            clip.SetData(data, 0);
            return clip;
        }

        private static AudioClip MakeWhoosh(float dur, float vol)
        {
            int n = (int)(SR * dur);
            var data = new float[n];
            var rng = new System.Random(54321);
            float last = 0f;
            for (int i = 0; i < n; i++)
            {
                float t = (float)i / SR;
                float env = Mathf.Sin(Mathf.PI * t / dur); // swell in and out
                float white = (float)(rng.NextDouble() * 2 - 1);
                last = Mathf.Lerp(last, white, 0.05f); // low-pass
                data[i] = last * env * vol;
            }
            var clip = AudioClip.Create("whoosh", n, 1, SR, false);
            clip.SetData(data, 0);
            return clip;
        }

        private static AudioClip MakeOcean()
        {
            float dur = 6f;
            int n = (int)(SR * dur);
            var data = new float[n];
            var rng = new System.Random(999);
            float last = 0f;
            for (int i = 0; i < n; i++)
            {
                float t = (float)i / SR;
                float swell = 0.5f + 0.5f * Mathf.Sin(2f * Mathf.PI * 0.15f * t);
                float white = (float)(rng.NextDouble() * 2 - 1);
                last = Mathf.Lerp(last, white, 0.03f);
                data[i] = last * swell * 0.5f;
            }
            var clip = AudioClip.Create("ocean", n, 1, SR, false);
            clip.SetData(data, 0);
            return clip;
        }

        private static AudioClip MakeMusicBed()
        {
            // Slow, moody two-note pad loop.
            float dur = 8f;
            int n = (int)(SR * dur);
            var data = new float[n];
            float[] roots = { 110f, 130.81f, 98f, 146.83f }; // A2 C3 G2 D3
            for (int i = 0; i < n; i++)
            {
                float t = (float)i / SR;
                int seg = (int)(t / (dur / roots.Length)) % roots.Length;
                float f = roots[seg];
                float s = Mathf.Sin(2f * Mathf.PI * f * t) * 0.5f
                        + Mathf.Sin(2f * Mathf.PI * f * 1.5f * t) * 0.25f
                        + Mathf.Sin(2f * Mathf.PI * f * 2f * t) * 0.15f;
                float env = Mathf.Min(1f, Mathf.Min(t, dur - t) * 0.5f);
                data[i] = s * env * 0.3f;
            }
            var clip = AudioClip.Create("music", n, 1, SR, false);
            clip.SetData(data, 0);
            return clip;
        }

        // ---- playback ----

        private void Play(string key)
        {
            if (_sfx.TryGetValue(key, out var clip))
                _sfxSrc.PlayOneShot(clip);
        }

        public void PlayTowerFire(string towerId) => Play(towerId);
        public void PlayEnemyDeath() => Play("death");
        public void PlayTowerDisabled() => Play("disabled");
        public void PlayWaveHorn() => Play("horn");
        public void PlayTideTurn() => Play("tide");
        public void PlayLanternDamage() => Play("lantern");
        public void PlayBuild() => Play("build");
        public void PlaySell() => Play("sell");
        public void PlayUpgrade() => Play("upgrade");
        public void PlayUi() => Play("ui");

        // ---- settings ----

        public void ApplySettings()
        {
            float m = _settings.muted ? 0f : 1f;
            AudioListener.volume = m;
            if (_musicSrc != null) _musicSrc.volume = 0.5f * _settings.musicVolume * _settings.masterVolume;
            if (_ambienceSrc != null) _ambienceSrc.volume = 0.4f * _settings.sfxVolume * _settings.masterVolume;
            if (_sfxSrc != null) _sfxSrc.volume = _settings.sfxVolume * _settings.masterVolume;
        }
    }
}
