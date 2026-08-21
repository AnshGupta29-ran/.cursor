// src/main.rs
// Simple toxicity filter microservice using Axum.
// POST /v1/screen with JSON { "text": "..." }
// Returns list of matched terms from lexicon.json.

use axum::{
    extract::{State, Json},
    response::Html,
    routing::{post, get},
    Router,
};
use serde::{Deserialize, Serialize};
use std::{net::SocketAddr, sync::Arc};
use tokio::fs;

#[derive(Debug, Deserialize)]
struct Input {
    text: String,
}

#[derive(Debug, Serialize, Clone)]
struct Term {
    term: String,
    category: String,
    severity_tier: String,
    locale: String,
}

#[derive(Debug, Serialize)]
struct ScreenResponse {
    matches: Vec<Term>,
}

#[derive(Clone)]
struct AppState {
    lexicon: Arc<Vec<Term>>,
}

async fn screen(
    Json(payload): Json<Input>,
    State(state): State<AppState>,
) -> Json<ScreenResponse> {
    let text_lower = payload.text.to_lowercase();
    let matches: Vec<Term> = state
        .lexicon
        .iter()
        .filter(|term| text_lower.contains(&term.term.to_lowercase()))
        .cloned()
        .collect();
    Json(ScreenResponse { matches })
}

fn root() -> Html<&'static str> {
    Html(r#"<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\" />
    <title>Toxicity Filter Demo</title>
</head>
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
</html>"#)
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Load lexicon.json at startup
    let data = fs::read_to_string("data/lexicon.json").await?;
    let lexicon: Vec<Term> = serde_json::from_str(&data)?;
    let state = AppState {
        lexicon: Arc::new(lexicon),
    };

    let app = Router::new()
        .route("/", get(root))
        .route("/v1/screen", post(screen))
        .with_state(state);

    // Bind server
    let addr = SocketAddr::from(([0, 0, 0, 0], 3000));
    println!("Listening on http://{}", addr);
    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await
        .map_err(|e| anyhow::anyhow!(e))
}
