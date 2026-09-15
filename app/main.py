"""FastAPI Application Factory, Lifespan, and Exception Handlers."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import BASE_DIR
from app.database import engine, init_db
from app.models import CallRecord, Patient
from app.responses import err, ok
from app.routers.calls import router as calls_router
from app.routers.dashboard import router as dashboard_router
from app.routers.patients import router as patients_router
from app.routers.vapi import router as vapi_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger("patients.app")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize SQLite database, tables, and seed demo patients on startup."""
    logger.info("Initializing persistent database...")
    init_db()
    yield
    logger.info("Shutting down Voice AI intake server.")


app = FastAPI(
    title="Voice AI Patient Registration API",
    description="Production-grade REST API and Vapi Voice AI webhook for healthcare patient intake.",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount static assets for modern dashboard
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include Routers
app.include_router(patients_router)
app.include_router(calls_router)
app.include_router(vapi_router)
app.include_router(dashboard_router)


# --- Standard Envelope Exception Handlers -----------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    msgs = []
    for error in exc.errors():
        loc = ".".join(str(x) for x in error.get("loc", []) if x != "body")
        msgs.append(f"{loc}: {error.get('msg')}" if loc else str(error.get("msg")))
    detail = "; ".join(msgs) or "Validation error"
    return err(detail, 422)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return err(detail, exc.status_code)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    logger.exception("Unhandled server exception: %s", exc)
    return err("Internal server error", 500)


# --- Root & Health Endpoints ------------------------------------------------

@app.get("/")
def get_root():
    """Service links index."""
    return ok(
        {
            "service": "Voice AI Patient Registration System",
            "docs": "/docs",
            "health": "/health",
            "patients": "/patients",
            "dashboard": "/dashboard",
            "vapi_webhook": "/vapi/webhook",
            "calls": "/calls",
        }
    )


@app.get("/health")
def get_health():
    """Service liveness probe."""
    return ok({"status": "ok"})
