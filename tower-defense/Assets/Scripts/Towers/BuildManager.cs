using System;
using System.Collections.Generic;
using TD.Content;
using TD.Core;
using UnityEngine;
using UnityEngine.EventSystems;

namespace TD.Towers
{
    /// <summary>
    /// Handles tower placement (with ghost + range preview), tower selection,
    /// upgrade/sell requests, and wave-start input. Owns the build nodes.
    /// </summary>
    public class BuildManager : MonoBehaviour
    {
        public static BuildManager Instance { get; private set; }

        readonly List<BuildNode> _nodes = new List<BuildNode>();

        TowerDefinition _pending;      // tower type being placed
        SpriteRenderer _ghost;
        SpriteRenderer _rangeRing;
        BuildNode _hovered;

        public Tower Selected { get; private set; }
        public bool IsPlacing => _pending != null;

        /// <summary>UI hooks: selection changed, or a node wants the shop to grey out.</summary>
        public event Action SelectionChanged;
        public event Action PlacementModeChanged;

        void Awake() { Instance = this; }

        // ------------------------------------------------------------------
        // Setup (called by GameBootstrap after grid layout is known)
        // ------------------------------------------------------------------
        public void BuildNodes(LevelDefinition level, float originX, float originY)
        {
            ClearNodes();
            for (int i = 0; i < level.buildNodes.Length; i++)
            {
                var cell = level.buildNodes[i];
                var go = new GameObject($"node_{i}");
                go.transform.SetParent(transform, false);
                go.transform.position = Enemies.EnemyPath.CellToWorld(cell, level, originX, originY);
                var node = go.AddComponent<BuildNode>();
                node.Initialize(i, level.cellSize);
                _nodes.Add(node);
            }
        }

        void ClearNodes()
        {
            foreach (var n in _nodes)
                if (n != null) Destroy(n.gameObject);
            _nodes.Clear();
            Select(null);
        }

        public BuildNode GetNode(int index) =>
            index >= 0 && index < _nodes.Count ? _nodes[index] : null;

        // ------------------------------------------------------------------
        // Placement mode (driven by the shop UI)
        // ------------------------------------------------------------------
        public void BeginPlacement(TowerDefinition def)
        {
            if (_pending == def) { CancelPlacement(); return; } // toggle off
            _pending = def;
            Select(null);
            EnsureGhost();
            _ghost.gameObject.SetActive(true);
            _rangeRing.gameObject.SetActive(true);
            PlacementModeChanged?.Invoke();
        }

        public void CancelPlacement()
        {
            if (_pending == null) return;
            _pending = null;
            if (_ghost != null) _ghost.gameObject.SetActive(false);
            if (_rangeRing != null) _rangeRing.gameObject.SetActive(false);
            if (_hovered != null) { _hovered.SetHighlight(false); _hovered = null; }
            PlacementModeChanged?.Invoke();
        }

        void EnsureGhost()
        {
            if (_ghost == null)
            {
                var go = new GameObject("ghost");
                go.transform.SetParent(transform, false);
                _ghost = go.AddComponent<SpriteRenderer>();
                _ghost.sprite = SpriteFactory.Circle();
                _ghost.sortingOrder = 25;
            }
            if (_rangeRing == null)
            {
                var go = new GameObject("rangeRing");
                go.transform.SetParent(transform, false);
                _rangeRing = go.AddComponent<SpriteRenderer>();
                _rangeRing.sprite = SpriteFactory.Ring();
                _rangeRing.sortingOrder = 24;
            }
        }

        // ------------------------------------------------------------------
        // Selection (drives the upgrade/sell panel)
        // ------------------------------------------------------------------
        public void Select(Tower t)
        {
            if (Selected == t) return;
            Selected = t;
            SelectionChanged?.Invoke();
        }

        public bool TryUpgradeSelected()
        {
            var gm = GameManager.Instance;
            if (Selected == null || !Selected.CanUpgrade) return false;
            if (!gm.SpendGold(Selected.NextUpgradeCost)) return false;
            Selected.Upgrade();
            SelectionChanged?.Invoke();
            return true;
        }

        public void SellSelected()
        {
            if (Selected == null) return;
            var t = Selected;
            Select(null);
            t.Sell();
        }

        /// <summary>Restore a tower from a save snapshot without charging gold.</summary>
        public Tower RestoreTower(TowerDefinition def, int nodeIndex, int level)
        {
            var node = GetNode(nodeIndex);
            if (node == null || node.IsOccupied) return null;
            var t = Tower.Place(def, node);
            node.SetOccupied(t);
            for (int i = 0; i < level && t.CanUpgrade; i++) t.Upgrade();
            return t;
        }

        // ------------------------------------------------------------------
        // Per-frame input
        // ------------------------------------------------------------------
        void Update()
        {
            var gm = GameManager.Instance;
            if (gm == null || gm.State != GameState.Playing) { CancelPlacement(); return; }
            if (EventSystem.current != null && EventSystem.current.IsPointerOverGameObject())
            {
                if (_hovered != null) { _hovered.SetHighlight(false); _hovered = null; }
                return;
            }

            var world = Camera.main.ScreenToWorldPoint(Input.mousePosition);
            world.z = 0f;
            var node = NodeAt(world);

            if (_pending != null) UpdatePlacement(world, node);
            else UpdateSelection(node);

            if (Input.GetKeyDown(KeyCode.Return) && !gm.WaveInProgress)
                Enemies.WaveSpawner.Instance?.StartNextWave();
        }

        void UpdatePlacement(Vector3 world, BuildNode node)
        {
            var gm = GameManager.Instance;
            bool overNode = node != null;
            bool valid = overNode && !node.IsOccupied && gm.CanAfford(_pending.BuildCost);

            _ghost.transform.position = overNode ? node.transform.position : world;
            _ghost.sprite = _pending.id == "cannon" ? SpriteFactory.Square()
                : _pending.id == "sniper" ? SpriteFactory.Diamond()
                : SpriteFactory.Circle();
            _ghost.transform.localScale = Vector3.one * 0.62f * _pending.levels[0].scale;
            var c = _pending.levels[0].bodyColor;
            _ghost.color = new Color(c.r, c.g, c.b, valid ? 0.55f : 0.25f);

            float range = _pending.levels[0].range;
            _rangeRing.transform.position = _ghost.transform.position;
            _rangeRing.transform.localScale = Vector3.one * range * 2f;
            _rangeRing.color = new Color(1f, 1f, 1f, 0.25f);

            if (node != _hovered)
            {
                if (_hovered != null) _hovered.SetHighlight(false);
                _hovered = node;
                if (_hovered != null) _hovered.SetHighlight(true, valid);
            }
            else if (_hovered != null)
            {
                _hovered.SetHighlight(true, valid);
            }

            if (Input.GetMouseButtonDown(0) && valid)
            {
                gm.SpendGold(_pending.BuildCost);
                var t = Tower.Place(_pending, node);
                node.SetOccupied(t);
                Core.Effects.RingFlash(node.transform.position, c, 0.8f, 0.25f);
                AudioManager.Instance?.Play(SfxId.Build);
                // stay in placement mode so the player can drop several
            }
            if (Input.GetMouseButtonDown(1)) CancelPlacement();
        }

        void UpdateSelection(BuildNode node)
        {
            if (node != _hovered)
            {
                if (_hovered != null) _hovered.SetHighlight(false);
                _hovered = node;
                if (_hovered != null && _hovered.IsOccupied) _hovered.SetHighlight(true, true);
            }
            if (Input.GetMouseButtonDown(0))
                Select(node != null && node.IsOccupied ? node.Occupant : null);
        }

        BuildNode NodeAt(Vector3 world)
        {
            BuildNode best = null;
            float bestD = 0.6f; // generous click radius (cells are 1 unit)
            foreach (var n in _nodes)
            {
                float d = Vector3.Distance(world, n.transform.position);
                if (d < bestD) { best = n; bestD = d; }
            }
            return best;
        }

        /// <summary>Escape handling: cancel placement first, then selection.</summary>
        public bool CancelModes()
        {
            if (IsPlacing) { CancelPlacement(); return true; }
            if (Selected != null) { Select(null); return true; }
            return false;
        }
    }
}
