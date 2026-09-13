"""ShelfSpace API — application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.logging import get_logger, setup_logging
from app.utils.handlers import register_exception_handlers

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_media_dirs()
    from app.services import email_service

    email_service.start_worker()
    logger.info("%s API started (environment=%s)", settings.APP_NAME, settings.ENVIRONMENT)
    yield
    email_service.stop_worker()
    logger.info("ShelfSpace API stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="ShelfSpace API",
        version="1.0.0",
        description="REST API for the ShelfSpace bookstore commerce platform.",
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    @app.get("/health", tags=["system"])
    def health():
        db_ok = True
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception:
            db_ok = False
        return {"status": "ok" if db_ok else "degraded", "database": db_ok}

    settings.ensure_media_dirs()
    app.mount("/media", StaticFiles(directory=settings.MEDIA_DIR), name="media")

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    return app


app = create_app()
