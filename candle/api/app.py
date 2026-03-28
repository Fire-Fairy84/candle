"""FastAPI application factory for the Candle REST API."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from candle.api.routes.alerts import router as alerts_router
from candle.api.routes.pairs import router as pairs_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Candle API starting up")
    yield
    logger.info("Candle API shutting down")


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application.

    Returns:
        A configured FastAPI instance with all routers registered under /api/v1.
    """
    app = FastAPI(
        title="Candle API",
        description="Crypto market screener — pairs, candles, and alert history",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(pairs_router, prefix="/api/v1")
    app.include_router(alerts_router, prefix="/api/v1")
    return app


app = create_app()
