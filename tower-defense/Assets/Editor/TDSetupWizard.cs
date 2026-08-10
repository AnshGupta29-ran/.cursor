using System.Collections.Generic;
using System.IO;
using TD.Content;
using TD.Core;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace TD.EditorTools
{
    /// <summary>
    /// One-click project setup. Creates Assets/Scenes/Main.unity containing a
    /// fully wired GameBootstrap, syncs the scene's guid into
    /// EditorBuildSettings, and optionally writes the default content out as
    /// ScriptableObject assets for designers to tweak.
    /// </summary>
    public static class TDSetupWizard
    {
        [MenuItem("TD/1. Create Main Scene", priority = 0)]
        public static void CreateMainScene()
        {
            Directory.CreateDirectory("Assets/Scenes");

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var boot = new GameObject("Bootstrap");
            boot.AddComponent<GameBootstrap>();

            const string scenePath = "Assets/Scenes/Main.unity";
            EditorSceneManager.SaveScene(scene, scenePath);

            // sync guid into build settings
            var guid = AssetDatabase.AssetPathToGUID(scenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(scenePath, true) };
            Debug.Log($"[TD] Main scene created at {scenePath} (guid {guid}). Press Play!");

            Selection.activeGameObject = boot;
        }

        [MenuItem("TD/2. Write Content Assets (optional)", priority = 1)]
        public static void WriteContentAssets()
        {
            const string dir = "Assets/Content";
            Directory.CreateDirectory(dir);

            var enemies = DefaultContent.CreateEnemies();
            var byId = new Dictionary<string, EnemyDefinition>();
            foreach (var e in enemies)
            {
                byId[e.id] = e;
                AssetDatabase.CreateAsset(e, $"{dir}/enemy_{e.id}.asset");
            }
            foreach (var t in DefaultContent.CreateTowers())
                AssetDatabase.CreateAsset(t, $"{dir}/tower_{t.id}.asset");
            foreach (var l in DefaultContent.CreateLevels(byId))
            {
                AssetDatabase.CreateAsset(l.waves, $"{dir}/waves_{l.id}.asset");
                AssetDatabase.CreateAsset(l, $"{dir}/level_{l.id}.asset");
            }
            AssetDatabase.SaveAssets();
            Debug.Log($"[TD] Content assets written to {dir}/. The game uses DefaultContent at runtime; " +
                      "these assets are for designers to reference/tweak.");
        }

        [MenuItem("TD/3. Reset Save Data", priority = 2)]
        public static void ResetSave()
        {
            SaveSystem.ResetAll();
            Debug.Log("[TD] Save data reset.");
        }
    }
}
