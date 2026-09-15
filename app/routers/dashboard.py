"""Dashboard router serving the web UI and Vapi web calling configuration."""

from __future__ import annotations

import os
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

from app.config import BASE_DIR, VAPI_PUBLIC_KEY

router = APIRouter(tags=["Dashboard"])

HTML_FILE = BASE_DIR / "templates" / "dashboard.html"


@router.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    """Serve the interactive patient intake dashboard."""
    if HTML_FILE.exists():
        content = HTML_FILE.read_text(encoding="utf-8")
        return HTMLResponse(content=content)
    return HTMLResponse(content="<h1>Dashboard file not found</h1>", status_code=500)


@router.get("/call", response_class=HTMLResponse)
@router.get("/test-call", response_class=HTMLResponse)
def get_test_call():
    """Serve the standalone direct WebRTC voice call interface."""
    call_file = BASE_DIR / "test_call.html"
    if call_file.exists():
        return HTMLResponse(content=call_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>test_call.html not found</h1>", status_code=404)


@router.get("/api/vapi-config")
def get_vapi_config():
    """Return public configuration for the in-browser Web Voice Call dialer."""
    return JSONResponse(
        {
            "public_key": VAPI_PUBLIC_KEY or "",
            "assistant_id": os.getenv("VAPI_ASSISTANT_ID", ""),
        }
    )
