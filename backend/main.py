"""
FastAPI application entry point for AgentForge.
Serves both the API and the frontend static files.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import get_config
from backend.logging_config import setup_logging
from backend.database import init_db, close_db

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)
config = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    logger.info("🚀 Starting %s v%s", config.app_name, config.get("app.version", "1.0.0"))
    await init_db()
    yield
    await close_db()
    logger.info("👋 %s shutdown complete", config.app_name)


# Create FastAPI app
app = FastAPI(
    title=config.app_name,
    description=config.get("app.description", "Multi AI Agent Builder Platform"),
    version=config.get("app.version", "1.0.0"),
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=config.get("cors.allow_credentials", True),
    allow_methods=config.get("cors.allow_methods", ["*"]),
    allow_headers=config.get("cors.allow_headers", ["*"]),
)

# Register API routers
from backend.api.auth import router as auth_router
from backend.api.agents import router as agents_router
from backend.api.executions import router as executions_router
from backend.api.providers import router as providers_router

app.include_router(auth_router)
app.include_router(agents_router)
app.include_router(executions_router)
app.include_router(providers_router)


# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "app": config.app_name, "version": config.get("app.version")}


# Serve frontend static files
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/css", StaticFiles(directory=str(frontend_dir / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(frontend_dir / "js")), name="js")
    if (frontend_dir / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve the SPA frontend for all non-API routes."""
        file_path = frontend_dir / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dir / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=config.server_host,
        port=config.server_port,
        reload=config.get("server.reload", True),
        workers=1,  # Use 1 worker for reload mode
    )
