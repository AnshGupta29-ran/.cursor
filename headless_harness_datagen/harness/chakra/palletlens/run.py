"""Dev entry point: python run.py  →  Swagger UI at http://127.0.0.1:8000/docs

The first run downloads the MobileNetV3-Small weights (~10 MB, one time) and
creates the SQLite database automatically.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
