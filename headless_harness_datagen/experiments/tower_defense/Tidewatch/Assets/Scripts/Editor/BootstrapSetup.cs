using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Tidewatch.EditorTools
{
    /// <summary>
    /// One-time project setup so the game is runnable the moment it is opened in the editor:
    /// ensures a scene containing a GameBootstrap exists and is registered in Build Settings.
    /// Runs on load; harmless on subsequent loads (it exits early once a scene is valid).
    /// </summary>
    [InitializeOnLoad]
    public static class BootstrapSetup
    {
        static BootstrapSetup()
        {
            EditorApplication.delayCall += EnsureScene;
        }

        private static void EnsureScene()
        {
            // Already a valid scene in build settings with a bootstrap? Do nothing.
            foreach (var s in EditorBuildSettings.scenes)
            {
                if (s.enabled && System.IO.File.Exists(s.path))
                {
                    var guid = AssetDatabase.AssetPathToGUID(s.path);
                    if (!string.IsNullOrEmpty(guid)) return;
                }
            }

            const string scenePath = "Assets/Scenes/Game.unity";
            System.IO.Directory.CreateDirectory("Assets/Scenes");

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var go = new GameObject("Bootstrap");
            go.AddComponent<Game.GameBootstrap>();
            EditorSceneManager.SaveScene(scene, scenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(scenePath, true) };
            AssetDatabase.SaveAssets();
            Debug.Log("[Tidewatch] Bootstrap scene created and added to Build Settings.");
        }
    }
}
