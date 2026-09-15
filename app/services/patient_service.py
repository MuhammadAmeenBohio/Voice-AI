"""Service layer for Patient business logic, uniqueness checks, and CRUD."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Optional
from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.models import (
    Appointment,
    AppointmentCreate,
    Patient,
    PatientCreate,
    PatientUpdate,
    normalize_phone,
    parse_dob,
    utc_now,
)
from app.responses import patient_dict

logger = logging.getLogger("patients.service")


def get_active_patient(session: Session, patient_id: uuid.UUID) -> Patient:
    """Retrieve an active (non-soft-deleted) patient by ID, or raise 404."""
    patient = session.get(Patient, patient_id)
    if not patient or patient.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def find_active_by_phone(session: Session, phone: str) -> Optional[Patient]:
    """Find the active patient matching a phone number."""
    return session.exec(
        select(Patient).where(
            Patient.deleted_at.is_(None),
            Patient.phone_number == phone,
        )
    ).first()


def ensure_unique_phone(
    session: Session, phone: str, *, exclude_patient_id: Optional[uuid.UUID] = None
) -> None:
    """Verify that no other active patient possesses this phone number."""
    existing = find_active_by_phone(session, phone)
    if existing and existing.patient_id != exclude_patient_id:
        raise HTTPException(
            status_code=400,
            detail=(
                f"A patient with this phone number already exists "
                f"({existing.first_name} {existing.last_name}, id={existing.patient_id}). "
                "Use PUT /patients/{id} to update instead of creating a duplicate."
            ),
        )


def list_patients(
    session: Session,
    last_name: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    phone_number: Optional[str] = None,
) -> list[Patient]:
    """Query active patients with optional filtering on last_name, DOB, or phone."""
    stmt = select(Patient).where(Patient.deleted_at.is_(None))
    if last_name:
        stmt = stmt.where(func.lower(col(Patient.last_name)) == last_name.strip().lower())
    if date_of_birth:
        try:
            dob = parse_dob(date_of_birth)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        stmt = stmt.where(Patient.date_of_birth == dob)
    if phone_number:
        try:
            phone = normalize_phone(phone_number)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        stmt = stmt.where(Patient.phone_number == phone)
    return list(session.exec(stmt.order_by(col(Patient.created_at).desc())).all())


def create_patient(session: Session, payload: PatientCreate) -> Patient:
    """Validate uniqueness and persist a new patient record."""
    ensure_unique_phone(session, payload.phone_number)
    patient = Patient.model_validate(payload.model_dump())
    session.add(patient)
    session.commit()
    session.refresh(patient)
    logger.info("Created patient: %s", json.dumps(patient_dict(patient), default=str))
    return patient


def update_patient(session: Session, patient: Patient, payload: PatientUpdate) -> Patient:
    """Apply partial update to an existing active patient."""
    data = payload.model_dump(exclude_unset=True)
    if "phone_number" in data and data["phone_number"] is not None:
        ensure_unique_phone(session, data["phone_number"], exclude_patient_id=patient.patient_id)
    for key, value in data.items():
        setattr(patient, key, value)
    patient.updated_at = utc_now()
    session.add(patient)
    session.commit()
    session.refresh(patient)
    logger.info("Updated patient_id=%s modified_fields=%s", patient.patient_id, list(data.keys()))
    return patient


def soft_delete_patient(session: Session, patient: Patient) -> None:
    """Soft-delete an active patient (sets deleted_at timestamp)."""
    patient.deleted_at = utc_now()
    patient.updated_at = utc_now()
    session.add(patient)
    session.commit()
    logger.info("Soft-deleted patient_id=%s", patient.patient_id)


def schedule_appointment(session: Session, payload: AppointmentCreate) -> Appointment:
    """Schedule a consultation appointment for a registered patient."""
    # Ensure patient exists
    get_active_patient(session, payload.patient_id)
    appt = Appointment(
        patient_id=payload.patient_id,
        appointment_date=payload.appointment_date,
        appointment_time=payload.appointment_time or "09:00 AM",
        reason=payload.reason or "General Consultation",
    )
    session.add(appt)
    session.commit()
    session.refresh(appt)
    logger.info("Scheduled appointment %s for patient %s", appt.appointment_id, appt.patient_id)
    return appt
