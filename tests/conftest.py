"""Pytest fixtures and test configuration."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Force in-memory database and clear API_KEY for standard test runs
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.pop("API_KEY", None)

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, select

from app.database import engine
from app.main import app
from app.models import Appointment, CallRecord, Patient


@pytest.fixture(autouse=True)
def setup_test_database():
    """Ensure a clean database schema before each test."""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def client():
    """FastAPI TestClient with cleared tables."""
    with TestClient(app, raise_server_exceptions=False) as c:
        with Session(engine) as session:
            for row in session.exec(select(Patient)).all():
                session.delete(row)
            for row in session.exec(select(CallRecord)).all():
                session.delete(row)
            for row in session.exec(select(Appointment)).all():
                session.delete(row)
            session.commit()
        yield c


def sample_patient(**overrides) -> Dict[str, Any]:
    """Generate sample valid patient registration payload."""
    data = {
        "first_name": "Alice",
        "last_name": "Johnson",
        "date_of_birth": "1990-05-20",
        "sex": "Female",
        "phone_number": "5554443333",
        "email": "alice@example.com",
        "address_line_1": "100 Pine St",
        "city": "Denver",
        "state": "co",
        "zip_code": "80202",
    }
    data.update(overrides)
    return data


def assert_envelope(response) -> Dict[str, Any]:
    """Verify that response matches standard { data, error } envelope format."""
    body = response.json()
    assert "data" in body, f"Missing 'data' in response envelope: {body}"
    assert "error" in body, f"Missing 'error' in response envelope: {body}"
    return body
