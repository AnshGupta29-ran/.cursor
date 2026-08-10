import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.api import router as api_router

app = FastAPI(title="LevelLens API")

# Mount API routes under /api
app.include_router(api_router, prefix="/api")

# Serve static frontend files
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
