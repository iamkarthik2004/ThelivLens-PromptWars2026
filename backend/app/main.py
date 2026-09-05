from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routes.analysis import router as analysis_router
from app.routes.health import router as health_router
from app.routes.legacy import router as legacy_router
from app.core.config import get_settings
from app.database import InMemoryRepository, MongoRepository

settings = get_settings()

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    use_mongo = bool(settings.mongodb_uri) and settings.environment.lower() == "production"
    app.state.repository = MongoRepository(settings.mongodb_uri, settings.mongodb_database) if use_mongo else InMemoryRepository()
    if use_mongo:
        try:
            await app.state.repository.connect()
        except Exception:
            app.state.repository = InMemoryRepository()
    yield
    app.state.repository.close()


app = FastAPI(
    title="ThelivLens API", version="2.0.0", lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=False, allow_methods=["*"], allow_headers=["*"],
)
app.include_router(health_router, prefix="/api")
app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(analysis_router, prefix="/api")
app.include_router(analysis_router, prefix=settings.api_v1_prefix)
app.include_router(legacy_router, prefix="/api")
app.include_router(legacy_router, prefix=settings.api_v1_prefix)

# Serve frontend static files in production
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        # API routes are already handled, this catches everything else
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(STATIC_DIR / "index.html"))
