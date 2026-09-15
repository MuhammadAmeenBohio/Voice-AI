"""Dependency injection helpers for authentication and database sessions."""

from __future__ import annotations

from typing import Annotated, Optional
from fastapi import Depends, Header, HTTPException
from sqlmodel import Session

from app.config import API_KEY
from app.database import get_session

SessionDep = Annotated[Session, Depends(get_session)]


def require_write_auth(authorization: Optional[str] = Header(default=None)) -> None:
    """Optional bearer token validation if API_KEY environment variable is set."""
    if not API_KEY:
        return
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if token != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


WriteAuth = Annotated[None, Depends(require_write_auth)]
