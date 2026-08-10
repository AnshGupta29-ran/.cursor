using System.Collections.Generic;
using TD.Content;
using TD.Core;
using TD.Enemies;
using UnityEngine;

namespace TD.Towers
{
    /// <summary>
    /// A placed tower. Handles target acquisition (per definition strategy),
    /// firing (per tower id behavior), upgrades, selling, and level visuals.
    /// </summary>
    public class Tower : MonoBehaviour
    {
        public static readonly List<Tower> All = new List<Tower>();

        public TowerDefinition Def { get; private set; }
        public BuildNode Node { get; private set; }
        public int Level { get; private set; } // 0-based index into Def.levels

        TowerLevel Stats => Def.levels[Level];

        SpriteRenderer _bodySr;
        Transform _barrel;
        SpriteRenderer _barrelSr;
        float _cooldown;

        public static Tower Place(TowerDefinition def, BuildNode node)
        {
            var go = new GameObject($"tower_{def.id}");
            go.transform.position = node.transform.position;
            var t = go.AddComponent<Tower>();
            t.Def = def;
            t.Node = node;
            t.Level = 0;
            t.BuildVisual();
            return t;
        }

        void BuildVisual()
        {
            // stone base
            var baseGo = new GameObject("base");
            baseGo.transform.SetParent(transform, false);
            baseGo.transform.localScale = Vector3.one * 0.9f;
            var bsr = baseGo.AddComponent<SpriteRenderer>();
            bsr.sprite = SpriteFactory.RoundedSquare();
            bsr.color = new Color(0.35f, 0.35f, 0.42f);
            bsr.sortingOrder = 15;

            // colored body
            var bodyGo = new GameObject("body");
            bodyGo.transform.SetParent(transform, false);
            _bodySr = bodyGo.AddComponent<SpriteRenderer>();
            _bodySr.sprite = Def.id == "cannon" ? SpriteFactory.Square()
                : Def.id == "sniper" ? SpriteFactory.Diamond()
                : SpriteFactory.Circle();
            _bodySr.sortingOrder = 16;

            // rotating barrel / crystal
            var barrelGo = new GameObject("barrel");
            barrelGo.transform.SetParent(transform, false);
            _barrel = barrelGo.transform;
            _barrelSr = barrelGo.AddComponent<SpriteRenderer>();
            _barrelSr.sprite = Def.id == "frost" ? SpriteFactory.Diamond() : SpriteFactory.Triangle();
            _barrelSr.sortingOrder = 17;
            _barrelSr.color = Color.white;

            ApplyLevelVisual();
        }

        void ApplyLevelVisual()
        {
            var s = Stats;
            _bodySr.color = s.bodyColor;
            _bodySr.transform.localScale = Vector3.one * 0.62f * s.scale;
            _barrel.localScale = Vector3.one * 0.34f * s.scale;
            _barrelSr.color = Color.Lerp(s.bodyColor, Color.white, 0.35f);
        }

        void OnEnable() { All.Add(this); }
        void OnDisable() { All.Remove(this); }

        void Update()
        {
            var gm = GameManager.Instance;
            if (gm == null || gm.State != GameState.Playing) return;

            _cooldown -= Time.deltaTime;
            if (_cooldown > 0f) return;

            var target = AcquireTarget();
            if (target == null) return;

            AimAt(target);
            _cooldown = 1f / Mathf.Max(0.01f, Stats.fireRate);
            FireAt(target);
        }

        void AimAt(Enemy target)
        {
            var to = target.transform.position - transform.position;
            float a = Mathf.Atan2(to.y, to.x) * Mathf.Rad2Deg;
            // triangle sprite points up
            _barrel.rotation = Quaternion.Euler(0, 0, a - 90f);
        }

        Enemy AcquireTarget()
        {
            float range = Stats.range;
            Enemy best = null;
            float bestKey = 0f;
            foreach (var e in Enemy.All)
            {
                if (e == null || e.IsDead) continue;
                float d = Vector3.Distance(transform.position, e.transform.position);
                if (d > range) continue;

                float key;
                switch (Def.targeting)
                {
                    case Targeting.Last: key = -e.DistanceTravelled; break;
                    case Targeting.Strongest: key = e.Health; break;
                    case Targeting.Closest: key = -d; break;
                    default: key = e.DistanceTravelled; break; // First
                }
                if (best == null || key > bestKey) { best = e; bestKey = key; }
            }
            return best;
        }

        void FireAt(Enemy target)
        {
            if (target == null || target.IsDead) return;
            var s = Stats;
            var from = _barrel.position;
            switch (Def.id)
            {
                case "cannon":
                    Projectile.Fire(from, target, s.projectileSpeed, s.damage,
                        s.splashRadius, 0f, 0f, s.armorPierce, s.bodyColor, arc: true);
                    AudioManager.Instance?.Play(SfxId.Shoot);
                    break;
                case "frost":
                    Projectile.Fire(from, target, s.projectileSpeed, s.damage,
                        0f, s.slowAmount, s.slowDuration, s.armorPierce, s.bodyColor, arc: false);
                    AudioManager.Instance?.Play(SfxId.Shoot);
                    break;
                case "sniper":
                    // instant rail shot: tracer + immediate damage
                    Effects.FireTracer(from, target.transform.position, new Color(1f, 0.9f, 0.5f));
                    target.TakeDamage(s.damage, s.armorPierce);
                    Effects.Burst(target.transform.position, s.bodyColor, 4, 1.6f, 0.08f);
                    AudioManager.Instance?.Play(SfxId.Shoot);
                    break;
                default: // arrow
                    Projectile.Fire(from, target, s.projectileSpeed, s.damage,
                        0f, 0f, 0f, s.armorPierce, s.bodyColor, arc: false);
                    AudioManager.Instance?.Play(SfxId.Shoot);
                    break;
            }
        }

        public bool CanUpgrade => Level < Def.MaxLevel - 1;
        public int NextUpgradeCost => CanUpgrade ? Def.levels[Level + 1].cost : 0;

        public void Upgrade()
        {
            if (!CanUpgrade) return;
            Level++;
            ApplyLevelVisual();
            Effects.RingFlash(transform.position, Stats.bodyColor, 1f, 0.3f);
            Effects.SpawnText(transform.position + Vector3.up * 0.6f, "UPGRADE!", new Color(0.5f, 1f, 0.6f));
            AudioManager.Instance?.Play(SfxId.Upgrade);
        }

        /// <summary>Refund 70% of everything invested so far.</summary>
        public int SellValue => Mathf.RoundToInt(Def.TotalInvested(Level) * 0.7f);

        public void Sell()
        {
            int value = SellValue;
            GameManager.Instance.AddGold(value);
            Effects.SpawnText(transform.position, $"+{value}g", new Color(1f, 0.85f, 0.3f));
            Effects.Burst(transform.position, Color.gray, 8, 2f, 0.1f);
            AudioManager.Instance?.Play(SfxId.Sell);
            Node.Clear();
            Destroy(gameObject);
        }
    }
}
