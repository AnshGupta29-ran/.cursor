using System.Collections.Generic;
using TD.Content;
using TD.Core;
using UnityEngine;

namespace TD.Enemies
{
    /// <summary>
    /// A single enemy walking the path. Handles movement (with slow effects),
    /// damage/armor, death rewards and reaching the base.
    /// </summary>
    [RequireComponent(typeof(SpriteRenderer))]
    public class Enemy : MonoBehaviour
    {
        public static readonly List<Enemy> All = new List<Enemy>();

        public EnemyDefinition Def { get; private set; }
        public float Health { get; private set; }
        public float MaxHealth { get; private set; }
        public float DistanceTravelled { get; private set; }
        public int Segment { get; private set; }
        public float SegmentProgress { get; private set; }
        public float SlowRemaining { get; private set; }
        public float CurrentSlowAmount { get; private set; }
        public bool IsDead { get; private set; }

        EnemyPath _path;
        SpriteRenderer _sr;
        Transform _healthBarFill;
        float _bobPhase;
        float _flyHeight;
        Vector3 _heading = Vector3.right;
        float _hitFlash;

        public void Initialize(EnemyDefinition def, EnemyPath path, float healthMult)
        {
            Def = def;
            _path = path;
            MaxHealth = def.health * healthMult;
            Health = MaxHealth;
            DistanceTravelled = 0f;
            Segment = 0; SegmentProgress = 0f;
            SlowRemaining = 0f; CurrentSlowAmount = 0f;
            _bobPhase = Random.value * Mathf.PI * 2f;
            _flyHeight = def.flying ? 0.45f : 0f;

            BuildVisual();
            transform.position = path.Spawn;
            UpdateHealthBar();
        }

        void BuildVisual()
        {
            _sr = GetComponent<SpriteRenderer>();
            _sr.sprite = Def.enemyClass == EnemyClass.Flyer ? SpriteFactory.Diamond()
                : Def.enemyClass == EnemyClass.Boss ? SpriteFactory.Star()
                : Def.enemyClass == EnemyClass.Swift ? SpriteFactory.Triangle()
                : SpriteFactory.Circle();
            _sr.color = Def.color;
            _sr.sortingOrder = 10;
            transform.localScale = Vector3.one * Def.scale * 0.7f;

            // dark outline
            var outline = new GameObject("outline");
            outline.transform.SetParent(transform, false);
            outline.transform.localScale = Vector3.one * 1.15f;
            var osr = outline.AddComponent<SpriteRenderer>();
            osr.sprite = _sr.sprite;
            osr.color = new Color(0f, 0f, 0f, 0.55f);
            osr.sortingOrder = 9;

            // eyes give cheap "alive" feel
            var eye = new GameObject("eye");
            eye.transform.SetParent(transform, false);
            eye.transform.localPosition = new Vector3(0.18f, 0.12f, -0.1f);
            eye.transform.localScale = Vector3.one * 0.18f;
            var esr = eye.AddComponent<SpriteRenderer>();
            esr.sprite = SpriteFactory.Circle();
            esr.color = Color.white;
            esr.sortingOrder = 11;

            // health bar (world space, above head)
            var barBg = new GameObject("hpBg");
            barBg.transform.SetParent(transform, false);
            barBg.transform.localPosition = new Vector3(0f, 0.75f, -0.1f);
            var bg = barBg.AddComponent<SpriteRenderer>();
            bg.sprite = SpriteFactory.Square();
            bg.color = new Color(0f, 0f, 0f, 0.6f);
            bg.sortingOrder = 20;
            barBg.transform.localScale = new Vector3(0.9f, 0.12f, 1f);

            var barFill = new GameObject("hpFill");
            barFill.transform.SetParent(barBg.transform, false);
            barFill.transform.localPosition = new Vector3(-0.5f, 0f, -0.1f);
            var fill = barFill.AddComponent<SpriteRenderer>();
            fill.sprite = SpriteFactory.Square();
            fill.color = new Color(0.3f, 0.9f, 0.35f);
            fill.sortingOrder = 21;
            // pivot at left: child scale x in [0,1] of parent width
            barFill.transform.localScale = new Vector3(1f, 0.8f, 1f);
            _healthBarFill = barFill.transform;
        }

        void OnEnable() { All.Add(this); }
        void OnDisable() { All.Remove(this); }

        void Update()
        {
            if (IsDead) return;
            var gm = GameManager.Instance;
            if (gm == null || gm.State != GameState.Playing) return;

            float speed = Def.moveSpeed * gm.EnemySpeedMult;
            if (SlowRemaining > 0f)
            {
                SlowRemaining -= Time.deltaTime;
                speed *= 1f - CurrentSlowAmount;
                if (SlowRemaining <= 0f) CurrentSlowAmount = 0f;
            }

            DistanceTravelled += speed * Time.deltaTime;
            var pos = _path.PositionAt(DistanceTravelled, out int seg, out float segT);
            var ahead = _path.PositionAt(DistanceTravelled + 0.05f, out _, out _);
            var dir = ahead - pos;
            if (dir.sqrMagnitude > 0.0001f) _heading = dir.normalized;
            Segment = seg; SegmentProgress = segT;

            // gentle bob + flying hover
            _bobPhase += Time.deltaTime * 6f;
            float bob = Mathf.Sin(_bobPhase) * 0.04f + _flyHeight + (Def.flying ? Mathf.Sin(_bobPhase * 0.7f) * 0.08f : 0f);
            transform.position = pos + new Vector3(0f, bob, 0f);

            // face travel direction
            float angle = Mathf.Atan2(_heading.y, _heading.x) * Mathf.Rad2Deg;
            if (Def.enemyClass == EnemyClass.Swift) // triangle sprite points up by default
                transform.rotation = Quaternion.Euler(0, 0, angle - 90f);
            else
                transform.rotation = Quaternion.Euler(0, 0, angle * 0.15f);

            // hit flash recovery
            if (_hitFlash > 0f)
            {
                _hitFlash -= Time.deltaTime * 6f;
                _sr.color = Color.Lerp(Def.color, Color.white, Mathf.Clamp01(_hitFlash));
            }

            if (DistanceTravelled >= _path.TotalLength)
                ReachBase();
        }

        void UpdateHealthBar()
        {
            if (_healthBarFill == null) return;
            float k = Mathf.Clamp01(Health / MaxHealth);
            // left-aligned fill: shrink + shift so the left edge stays put
            _healthBarFill.localScale = new Vector3(Mathf.Max(k, 0.001f), 0.8f, 1f);
            _healthBarFill.localPosition = new Vector3(-0.5f * (1f - k), 0f, -0.1f);
            var fill = _healthBarFill.GetComponent<SpriteRenderer>();
            fill.color = Color.Lerp(new Color(0.9f, 0.25f, 0.2f), new Color(0.3f, 0.9f, 0.35f), k);
        }

        public void TakeDamage(float amount, float armorPierce = 0f)
        {
            if (IsDead) return;
            float effectiveArmor = Def.armor * (1f - Mathf.Clamp01(armorPierce));
            float final = amount * (1f - effectiveArmor);
            Health -= final;
            _hitFlash = 1f;
            UpdateHealthBar();
            if (Health <= 0f) Die(killed: true);
        }

        public void ApplySlow(float amount, float duration)
        {
            if (IsDead || amount <= 0f) return;
            if (amount >= CurrentSlowAmount || SlowRemaining <= 0f)
            {
                CurrentSlowAmount = Mathf.Clamp01(amount);
                SlowRemaining = duration;
            }
            else
            {
                SlowRemaining = Mathf.Max(SlowRemaining, duration);
            }
        }

        void Die(bool killed)
        {
            if (IsDead) return;
            IsDead = true;
            if (killed)
            {
                GameManager.Instance.OnEnemyKilled(this);
                Effects.Burst(transform.position, Def.color, 10, 3f, 0.14f * Def.scale + 0.08f);
                Effects.SpawnText(transform.position, $"+{Mathf.RoundToInt(Def.reward * GameManager.Instance.RewardMult)}g",
                    new Color(1f, 0.85f, 0.3f));
                AudioManager.Instance?.Play(SfxId.EnemyDie);
            }
            WaveSpawner.Instance?.NotifyEnemyRemoved(this);
            Destroy(gameObject);
        }

        void ReachBase()
        {
            if (IsDead) return;
            IsDead = true;
            GameManager.Instance.OnEnemyReachedBase(this);
            Effects.Burst(transform.position, new Color(1f, 0.3f, 0.2f), 14, 3.5f, 0.18f);
            AudioManager.Instance?.Play(SfxId.BaseHit);
            WaveSpawner.Instance?.NotifyEnemyRemoved(this);
            Destroy(gameObject);
        }
    }
}
