"""Database engine, session dependency, and initialization."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Generator
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import DATABASE_URL

logger = logging.getLogger("patients.database")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine_kwargs: dict[str, Any] = {"echo": False, "connect_args": connect_args}
if DATABASE_URL in {"sqlite://", "sqlite:///:memory:"}:
    engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, **engine_kwargs)


def get_session() -> Generator[Session, None, None]:
    """Dependency that yields a database session."""
    with Session(engine) as session:
        yield session


def seed_demo_patients() -> None:
    """Seed 2 demo patients if the database has no active patients."""
    from app.models import Patient, Sex

    with Session(engine) as session:
        existing = session.exec(select(Patient).where(Patient.deleted_at.is_(None))).first()
        if existing:
            return

        demo_records = [
            Patient(
                first_name="Jane",
                last_name="Doe",
                date_of_birth=date(1985, 3, 15),
                sex=Sex.female,
                phone_number="5551234567",
                email="jane.doe@example.com",
                address_line_1="123 Main St",
                address_line_2="Apt 4B",
                city="Austin",
                state="TX",
                zip_code="78701",
                insurance_provider="Blue Cross",
                insurance_member_id="BC123456",
                preferred_language="English",
                emergency_contact_name="John Doe",
                emergency_contact_phone="5559876543",
            ),
            Patient(
                first_name="Robert",
                last_name="Smith",
                date_of_birth=date(1972, 11, 2),
                sex=Sex.male,
                phone_number="5552223333",
                email=None,
                address_line_1="456 Oak Ave",
                city="Seattle",
                state="WA",
                zip_code="98101",
                preferred_language="English",
            ),
        ]
        for p in demo_records:
            session.add(p)
        session.commit()
        logger.info("Seeded %d demo patients into SQLite", len(demo_records))


def init_db() -> None:
    """Create all database tables and seed if necessary."""
    SQLModel.metadata.create_all(engine)
    seed_demo_patients()
