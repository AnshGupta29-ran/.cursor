using UnityEngine;

namespace TD.Core
{
    /// <summary>Top-down RTS camera: WASD/arrow pan, edge pan, scroll zoom, drag pan.</summary>
    public class CameraController : MonoBehaviour
    {
        public float panSpeed = 8f;
        public float edgePanSpeed = 6f;
        public float zoomSpeed = 6f;
        public float minZoom = 4f;
        public float maxZoom = 16f;
        public bool edgePan = true;

        Vector3 _min, _max;
        Camera _cam;
        Vector3 _dragOrigin;
        bool _dragging;

        public void SetBounds(Bounds b)
        {
            _min = b.min; _max = b.max;
        }

        void Awake() { _cam = GetComponent<Camera>(); }

        void Update()
        {
            if (GameManager.Instance != null && GameManager.Instance.State != GameState.Playing)
                return;

            float dt = Time.unscaledDeltaTime;
            var move = Vector3.zero;
            if (Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow)) move.y += 1;
            if (Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow)) move.y -= 1;
            if (Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow)) move.x -= 1;
            if (Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow)) move.x += 1;
            transform.position += move * (panSpeed * dt * Zoom01() * 2f);

            if (edgePan && !GameManager.Instance.SpeedWasHeld)
            {
                var pos = Input.mousePosition;
                var edge = Vector3.zero;
                const float m = 12f;
                if (pos.x < m) edge.x -= 1; else if (pos.x > Screen.width - m) edge.x += 1;
                if (pos.y < m) edge.y -= 1; else if (pos.y > Screen.height - m) edge.y += 1;
                if (move == Vector3.zero) transform.position += edge * (edgePanSpeed * dt * Zoom01() * 2f);
            }

            float scroll = Input.mouseScrollDelta.y;
            if (Mathf.Abs(scroll) > 0.01f)
                _cam.orthographicSize = Mathf.Clamp(_cam.orthographicSize - scroll * zoomSpeed * dt * 10f, minZoom, maxZoom);

            if (Input.GetMouseButtonDown(2) || Input.GetMouseButtonDown(1) && !OverUI())
            {
                _dragging = true;
                _dragOrigin = _cam.ScreenToWorldPoint(Input.mousePosition);
            }
            if ((Input.GetMouseButton(2)) && _dragging)
            {
                var current = _cam.ScreenToWorldPoint(Input.mousePosition);
                transform.position += _dragOrigin - current;
            }
            if (Input.GetMouseButtonUp(2)) _dragging = false;

            var p = transform.position;
            p.x = Mathf.Clamp(p.x, _min.x, _max.x);
            p.y = Mathf.Clamp(p.y, _min.y, _max.y);
            transform.position = p;
        }

        float Zoom01() => Mathf.InverseLerp(minZoom, maxZoom, _cam.orthographicSize) * 0.9f + 0.1f;

        static bool OverUI()
        {
            return UnityEngine.EventSystems.EventSystem.current != null &&
                   UnityEngine.EventSystems.EventSystem.current.IsPointerOverGameObject();
        }
    }
}
