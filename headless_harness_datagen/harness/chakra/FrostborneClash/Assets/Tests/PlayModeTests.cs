using System.Collections;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using UnityEngine.SceneManagement;

public class PlayModeTests
{
    const string ScenePath = "Assets/Scenes/MainScene.unity";

    // Helper to load the test scene asynchronously
    IEnumerator LoadScene()
    {
        var async = SceneManager.LoadSceneAsync(ScenePath, LoadSceneMode.Single);
        while (!async.isDone) yield return null;
    }

    [UnityTest]
    public IEnumerator BoardShrinksWhenFrostlineAdvances()
    {
        // Load scene with all components
        yield return LoadScene();
        var board = GameObject.FindObjectOfType<Board>();
        var frostline = GameObject.FindObjectOfType<Frostline>();
        Assert.NotNull(board);
        Assert.NotNull(frostline);
        int initialWidth = board.Width;
        int initialHeight = board.Height;
        // Advance frostline enough times to trigger a shrink (TurnsPerAdvance = 2)
        for (int i = 0; i < 2; i++) frostline.Advance();
        // After advance, board should have shrunk by 1 on each axis
        Assert.AreEqual(initialWidth - 1, board.Width - (board.Width - board.GetType().GetField("_currentWidth", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance).GetValue(board) as int? ?? 0), "Board width should shrink");
        // Directly verify that internal current width decreased
        var field = board.GetType().GetField("_currentWidth", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        int currentWidth = (int)field.GetValue(board);
        Assert.AreEqual(initialWidth - 1, currentWidth);
        yield return null;
    }

    [UnityTest]
    public IEnumerator ManaCrystallizationCreatesBuff()
    {
        yield return LoadScene();
        var manaPool = GameObject.FindObjectOfType<ManaPool>();
        Assert.NotNull(manaPool);
        // Set current mana above max to simulate excess (max is 10)
        manaPool.CurrentMana = 12;
        manaPool.Crystallize(2);
        // Buff should be active for 2 turns
        Assert.AreEqual(2, manaPool.GetType().GetField("CrystallizedBuffTurns", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance).GetValue(manaPool));
        // Simulate two frames to expire buff
        for (int i = 0; i < 2; i++) yield return null;
        int remaining = (int)manaPool.GetType().GetField("CrystallizedBuffTurns", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance).GetValue(manaPool);
        Assert.AreEqual(0, remaining);
    }

    [UnityTest]
    public IEnumerator GameManagerTurnsAdvanceAndFrostlineTriggers()
    {
        yield return LoadScene();
        var gm = GameObject.FindObjectOfType<GameManager>();
        var frostline = GameObject.FindObjectOfType<Frostline>();
        var board = GameObject.FindObjectOfType<Board>();
        Assert.NotNull(gm);
        Assert.NotNull(frostline);
        Assert.NotNull(board);
        // Record initial safe width
        var field = board.GetType().GetField("_currentWidth", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        int startWidth = (int)field.GetValue(board);
        // Simulate enough turns to cause frostline advance twice (each advance occurs every 2 turns)
        // GameManager triggers EndTurn automatically via timer; we manually call EndTurn to speed up.
        for (int i = 0; i < 4; i++)
        {
            gm.EndTurn();
            yield return null;
        }
        int endWidth = (int)field.GetValue(board);
        // Board should have shrunk by 2 (one per advancement)
        Assert.AreEqual(startWidth - 2, endWidth);
    }
}
