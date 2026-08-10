using UnityEngine;
using System.Collections.Generic;

public class Board : MonoBehaviour
{
    public int Width = 6;
    public int Height = 6;
    // 2D array of placed cards (null = empty)
    private Card[,] _grid;
    // Current safe area size (shrinks with Frostline)
    private int _currentWidth;
    private int _currentHeight;

    void Awake()
    {
        _grid = new Card[Width, Height];
        _currentWidth = Width;
        _currentHeight = Height;
    }

    public bool IsPositionValid(Vector2Int pos)
    {
        // Within current safe area
        return pos.x >= 0 && pos.x < _currentWidth && pos.y >= 0 && pos.y < _currentHeight;
    }

    public bool IsCellEmpty(Vector2Int pos)
    {
        return IsPositionValid(pos) && _grid[pos.x, pos.y] == null;
    }

    public void PlaceCard(Card card, Vector2Int pos)
    {
        if (!IsCellEmpty(pos)) return;
        _grid[pos.x, pos.y] = card;
        // Visual representation would be instantiated here (omitted for brevity)
    }

    public void ShrinkBoard(int amount)
    {
        // Reduce playable area from the edges uniformly if possible
        _currentWidth = Mathf.Max(1, _currentWidth - amount);
        _currentHeight = Mathf.Max(1, _currentHeight - amount);
        // Optionally clear cards outside new bounds (simple removal)
        for (int x = _currentWidth; x < Width; x++)
            for (int y = 0; y < Height; y++)
                _grid[x, y] = null;
        for (int y = _currentHeight; y < Height; y++)
            for (int x = 0; x < _currentWidth; x++)
                _grid[x, y] = null;
    }
}
