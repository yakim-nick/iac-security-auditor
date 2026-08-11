from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.config import settings
from src.models.database import init_db, close_db
from src.routes.webhooks import router as webhook_router
from src.routes.audits import router as audit_router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open the DB pool on startup and close it on shutdown."""
    logger.info("Starting IaC Security Auditor")
    await init_db()
    yield
    await close_db()


app = FastAPI(title="IaC Security Auditor", version="1.0.0", lifespan=lifespan)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Turn any unhandled exception into a generic 500 so internals never leak."""
    logger.error(f"Unhandled: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": "internal_server_error"})


app.include_router(webhook_router, prefix="/webhooks")
app.include_router(audit_router, prefix="/audits")


@app.get("/health")
async def health():
    """Liveness probe for orchestrators and load balancers."""
    return {"status": "healthy", "version": "1.0.0"}
