"""FastAPI application for the `api` container."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings
from app.db import build_engine, ensure_schema
from app.routes import dashboard, exports


def create_app(settings: Settings | None = None) -> FastAPI:
    """Example: uvicorn app.main:app  (settings come from the environment)."""
    resolved = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = build_engine(resolved)
        ensure_schema(engine, resolved.schema_name)
        app.state.settings = resolved
        app.state.engine = engine
        yield
        engine.dispose()

    app = FastAPI(title="Dashboard Tiflux", lifespan=lifespan)
    app.include_router(dashboard.router)
    app.include_router(exports.router)
    return app


app = create_app()
