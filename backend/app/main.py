from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


@app.get("/")
async def root():
    return {
        "product": "FinSight",
        "description": "Voice-first Personal Financial Intelligence Platform",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "database": "connected"}
