# server.py
# Simple toxicity filter demo using Python's built-in http.server
# POST /v1/screen with JSON {"text": "..."}
# Returns JSON list of matched terms from data/lexicon.json

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "lexicon.json")

# Load lexicon once at startup
with open(DATA_PATH, "r", encoding="utf-8") as f:
    LEXICON = json.load(f)

class Handler(BaseHTTPRequestHandler):
    def _set_json(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            # Serve a minimal HTML demo page
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            html = """<!DOCTYPE html>
<html lang=\"en\">
<head><meta charset=\"UTF-8\"><title>Toxicity Filter Demo</title></head>
<body>
<h1>Toxicity Filter</h1>
<textarea id=\"input\" rows=\"4\" cols=\"50\" placeholder=\"Enter text...\"></textarea><br/>
<button onclick=\"submit()\">Check</button>
<pre id=\"output\"></pre>
<script>
async function submit() {
  const text = document.getElementById('input').value;
  const resp = await fetch('/v1/screen', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text})
  });
  const data = await resp.json();
  document.getElementById('output').textContent = JSON.stringify(data, null, 2);
}
</script>
</body>
</html>"""
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/v1/screen":
            self.send_error(404, "Not found")
            return
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body)
            text = payload.get("text", "").lower()
        except Exception:
            self.send_error(400, "Invalid JSON")
            return
        matches = [term for term in LEXICON if term["term"].lower() in text]
        response = {"matches": matches}
        self._set_json()
        self.wfile.write(json.dumps(response).encode("utf-8"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", "3000"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Listening on http://0.0.0.0:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
