using Tidewatch.Core;
using UnityEngine;

namespace Tidewatch.Game
{
    /// <summary>View for a live enemy: a colored primitive + status icons, pooled implicitly
    /// by the RunController. No per-frame allocation: position synced from sim state.</summary>
    public sealed class EnemyView : MonoBehaviour
    {
        private Enemy _e;
        private Renderer _body;
        private GameObject _shroudIcon;
        private GameObject _beachedIcon;
        private GameObject _healthBar;
        private float _baseY;

        public static EnemyView Create(Enemy e, ContentDb db)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            go.name = $"Enemy_{e.Def.Id}";
            var col = go.GetComponent<Collider>();
            if (col != null) Destroy(col);
            var view = go.AddComponent<EnemyView>();
            view._e = e;
            view._body = go.GetComponent<Renderer>();
            float scale = e.Def.IsBoss ? 1.4f : e.Def.Id == EnemyIds.Broodmother ? 0.8f : 0.45f;
            go.transform.localScale = Vector3.one * scale;
            view._baseY = 0f;
            view._body.material = new Material(Shader.Find("Standard")) { color = ColorFor(e.Def) };

            // Health bar.
            view._healthBar = GameObject.CreatePrimitive(PrimitiveType.Quad);
            Destroy(view._healthBar.GetComponent<Collider>());
            view._healthBar.transform.SetParent(go.transform, false);
            view._healthBar.transform.localPosition = new Vector3(0f, 1.2f, 0f);
            view._healthBar.transform.localScale = new Vector3(1f / scale, 0.15f / scale, 1f);
            view._healthBar.GetComponent<Renderer>().material =
                new Material(Shader.Find("Standard")) { color = Color.green };

            // Status icons (simple colored quads above the enemy).
            view._shroudIcon = MakeIcon(go.transform, new Color(0.4f, 0.1f, 0.6f), 0.9f, scale);
            view._beachedIcon = MakeIcon(go.transform, new Color(0.9f, 0.6f, 0.1f), 0.7f, scale);
            return view;
        }

        private static GameObject MakeIcon(Transform parent, Color color, float yOff, float scale)
        {
            var icon = GameObject.CreatePrimitive(PrimitiveType.Quad);
            Destroy(icon.GetComponent<Collider>());
            icon.transform.SetParent(parent, false);
            icon.transform.localPosition = new Vector3(0f, yOff, 0f);
            icon.transform.localScale = new Vector3(0.3f / scale, 0.3f / scale, 1f);
            icon.GetComponent<Renderer>().material = new Material(Shader.Find("Standard")) { color = color };
            icon.SetActive(false);
            return icon;
        }

        private static Color ColorFor(EnemyDef d)
        {
            switch (d.Id)
            {
                case EnemyIds.Skitterling: return new Color(0.6f, 0.85f, 0.4f);
                case EnemyIds.BrineHulk: return new Color(0.5f, 0.45f, 0.6f);
                case EnemyIds.AbyssalLurker: return new Color(0.2f, 0.3f, 0.6f);
                case EnemyIds.Spitter: return new Color(0.85f, 0.55f, 0.2f);
                case EnemyIds.Broodmother: return new Color(0.8f, 0.3f, 0.5f);
                case EnemyIds.DrownedBell: return new Color(0.3f, 0.2f, 0.4f);
                default: return Color.magenta;
            }
        }

        public void Sync(float dt)
        {
            if (_e == null) return;
            transform.position = new Vector3(_e.X, _e.Y, -0.2f);
            // Health bar.
            float f = _e.MaxHp > 0 ? _e.Hp / _e.MaxHp : 0f;
            _healthBar.transform.localScale = new Vector3(
                Mathf.Max(0.001f, f) / transform.localScale.x,
                _healthBar.transform.localScale.y, 1f);
            _healthBar.GetComponent<Renderer>().material.color =
                f > 0.5f ? Color.green : f > 0.25f ? Color.yellow : Color.red;
            _shroudIcon.SetActive(_e.ShroudedActive);
            _beachedIcon.SetActive(_e.Beached);
            // Shrouded enemies are dimmer until revealed.
            var c = ColorFor(_e.Def);
            _body.material.color = _e.ShroudedActive ? c * 0.4f : c;
        }

        public void Despawn()
        {
            Destroy(gameObject);
        }
    }

    /// <summary>View for a placed tower: colored base + a muzzle flash on fire + disabled state.</summary>
    public sealed class TowerView : MonoBehaviour
    {
        private TowerInstance _t;
        private Renderer _body;
        private GameObject _disabledIcon;
        private float _flashTimer;

        public static TowerView Create(TowerInstance t, ContentDb db)
        {
            var go = new GameObject($"Tower_{t.DefId}");
            var view = go.AddComponent<TowerView>();
            view._t = t;
            go.transform.position = new Vector3(t.Plot.X + 0.5f, t.Plot.Y + 0.5f, -0.15f);

            var baseGo = GameObject.CreatePrimitive(PrimitiveType.Cube);
            Destroy(baseGo.GetComponent<Collider>());
            baseGo.transform.SetParent(go.transform, false);
            baseGo.transform.localPosition = Vector3.zero;
            baseGo.transform.localScale = new Vector3(0.7f, 0.7f, 0.7f);
            view._body = baseGo.GetComponent<Renderer>();
            view._body.material = new Material(Shader.Find("Standard")) { color = ColorFor(t.DefId) };

            var def = db.GetTower(t.DefId);
            if (def.EmitsLight)
            {
                var glow = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                Destroy(glow.GetComponent<Collider>());
                glow.transform.SetParent(go.transform, false);
                glow.transform.localPosition = new Vector3(0f, 0.4f, 0f);
                glow.transform.localScale = Vector3.one * 0.3f;
                glow.GetComponent<Renderer>().material =
                    new Material(Shader.Find("Standard")) { color = new Color(1f, 0.9f, 0.5f) };
            }

            view._disabledIcon = GameObject.CreatePrimitive(PrimitiveType.Quad);
            Destroy(view._disabledIcon.GetComponent<Collider>());
            view._disabledIcon.transform.SetParent(go.transform, false);
            view._disabledIcon.transform.localPosition = new Vector3(0f, 0.8f, 0f);
            view._disabledIcon.transform.localScale = new Vector3(0.4f, 0.4f, 1f);
            view._disabledIcon.GetComponent<Renderer>().material =
                new Material(Shader.Find("Standard")) { color = new Color(0.2f, 0.2f, 0.25f) };
            view._disabledIcon.SetActive(false);
            view.RefreshTier();
            return view;
        }

        private static Color ColorFor(string id)
        {
            switch (id)
            {
                case TowerIds.BeaconSpire: return new Color(0.95f, 0.85f, 0.4f);
                case TowerIds.FlareMortar: return new Color(0.9f, 0.45f, 0.2f);
                case TowerIds.PrismArray: return new Color(0.5f, 0.7f, 0.95f);
                case TowerIds.HarpoonBallista: return new Color(0.6f, 0.6f, 0.65f);
                case TowerIds.FogBell: return new Color(0.75f, 0.65f, 0.4f);
                default: return Color.white;
            }
        }

        public void RefreshTier()
        {
            // Grow slightly per tier so tier is readable at a glance.
            float s = 0.7f + _t.Tier * 0.1f + (_t.BranchId != null ? 0.05f : 0f);
            transform.GetChild(0).localScale = new Vector3(s, s, s);
        }

        public void SetDisabled(bool disabled)
        {
            _disabledIcon.SetActive(disabled);
            _body.material.color = disabled ? ColorFor(_t.DefId) * 0.4f : ColorFor(_t.DefId);
        }

        public void Fire(Vector3? target)
        {
            _flashTimer = 0.08f;
            _body.material.color = Color.white;
        }

        public void Sync(float dt)
        {
            if (_flashTimer > 0f)
            {
                _flashTimer -= dt;
                if (_flashTimer <= 0f && !_t.IsDisabled)
                    _body.material.color = ColorFor(_t.DefId);
            }
        }
    }
}
