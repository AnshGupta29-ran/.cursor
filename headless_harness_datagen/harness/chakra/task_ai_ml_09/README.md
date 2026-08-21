# Toxicity Filter Microservice Demo

## Overview
A simple HTTP service that checks input text for toxic terms defined in `data/lexicon.json`. It provides:
- **POST /v1/screen** – returns any matching terms.
- **GET /** – a minimal HTML demo page to test the endpoint in the browser.

## Run the demo
```bash
# From this directory
python server.py
```
The server listens on **http://127.0.0.1:3000**.

## Test via `curl`
```bash
curl -X POST -H "Content-Type: application/json" \
    -d '{"text": "This is a gronk and blork test"}' \
    http://127.0.0.1:3000/v1/screen
```
You should see a JSON response with the matched terms.

Open a browser at `http://127.0.0.1:3000/` for an interactive UI.
