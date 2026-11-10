import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from backend.app.core.config import settings
from backend.app.db.session import init_db
from backend.app.api.v1.router import api_router
from backend.app.automation.mock_portals import mock_portals_router
from backend.app.api.v1.voice import websocket_voice_endpoint, websocket_gnani_stt_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB models
    await init_db()
    # Seed Aarav Mehta demo data if database is empty
    from backend.data.synthetic.seed_aarav import seed_demo_persona
    await seed_demo_persona()
    yield
    # Shutdown logic


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="FinSight Modular Financial Intelligence Engine Backend",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API
app.include_router(api_router)
app.include_router(mock_portals_router)

# Mount WebSocket directly at /ws/voice as required by architecture.md
app.add_api_websocket_route("/ws/voice", websocket_voice_endpoint)
app.add_api_websocket_route("/ws/voice/stt", websocket_gnani_stt_endpoint)


@app.get("/health")
async def health():
    return {"status": "healthy", "database": "connected"}


# Locate unified frontend production assets if present
FRONTEND_DIST_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
)

if os.path.exists(FRONTEND_DIST_DIR):
    assets_dir = os.path.join(FRONTEND_DIST_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="static_assets")


@app.get("/")
async def root(request: Request):
    accept_header = request.headers.get("accept", "")
    index_file = os.path.join(FRONTEND_DIST_DIR, "index.html")
    # If a browser is requesting the landing page HTML
    if "text/html" in accept_header and os.path.exists(index_file):
        return FileResponse(index_file)
    # Default JSON metadata for API consumers and test suites
    return {
        "product": "FinSight",
        "description": "Voice-first Personal Financial Intelligence Platform",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/{full_path:path}")
async def spa_catch_all(full_path: str):
    file_path = os.path.join(FRONTEND_DIST_DIR, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    index_file = os.path.join(FRONTEND_DIST_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"error": "Not found", "path": full_path}
