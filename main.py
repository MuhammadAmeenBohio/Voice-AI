"""Root application entrypoint for Voice AI Patient Registration System."""

from __future__ import annotations

import os
import uvicorn

from app.database import engine
from app.main import app
from app.models import CallRecord, Patient

__all__ = ["app", "engine", "Patient", "CallRecord"]

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
