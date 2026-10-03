import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.core.config import settings
from backend.database.base import Base
from backend.database.session import engine
from backend.api.endpoints import findings, validation, reports, settings as api_settings
from backend.services.validation_service import validation_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("autovalidate")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully.")
    yield
    await engine.dispose()
    logger.info("Database connections closed.")


app = FastAPI(
    title="AutoValidate Pro API",
    description="AI-Powered Penetration Testing Scanner Findings Validation Engine",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local dev flexibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(findings.router, prefix="/api")
app.include_router(validation.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(api_settings.router, prefix="/api")


# WebSocket Manager for real-time progress broadcast
active_websockets: list[WebSocket] = []

async def on_validation_event(event_data: dict):
    disconnected = []
    for ws in active_websockets:
        try:
            await ws.send_json(event_data)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        if ws in active_websockets:
            active_websockets.remove(ws)

validation_service.register_subscriber(on_validation_event)


@app.websocket("/ws/validation")
async def websocket_validation(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        while True:
            # Keep-alive heartbeat receiver
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        if websocket in active_websockets:
            active_websockets.remove(websocket)


@app.get("/")
async def root():
    return {
        "app": "AutoValidate Pro",
        "version": "1.0.0",
        "status": "operational",
        "docs_url": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
