"""REST API endpoints for Patient operations."""

from __future__ import annotations

import uuid
from typing import Optional
from fastapi import APIRouter, Query

from app.models import PatientCreate, PatientUpdate
from app.responses import ok, patient_dict
from app.routers.deps import SessionDep, WriteAuth
from app.services import patient_service

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("")
def get_patients(
    session: SessionDep,
    last_name: Optional[str] = Query(default=None, description="Filter by patient last name"),
    date_of_birth: Optional[str] = Query(default=None, description="Filter by DOB (YYYY-MM-DD or MM/DD/YYYY)"),
    phone_number: Optional[str] = Query(default=None, description="Filter by 10-digit phone number"),
):
    """List active patients matching optional search parameters."""
    rows = patient_service.list_patients(session, last_name, date_of_birth, phone_number)
    return ok([patient_dict(p) for p in rows])


@router.get("/{patient_id}")
def get_patient(patient_id: uuid.UUID, session: SessionDep):
    """Retrieve a single active patient by UUID."""
    patient = patient_service.get_active_patient(session, patient_id)
    return ok(patient_dict(patient))


@router.post("", status_code=201)
def create_patient(payload: PatientCreate, session: SessionDep, _: WriteAuth):
    """Create a new patient record with server-side validation."""
    patient = patient_service.create_patient(session, payload)
    return ok(patient_dict(patient), status_code=201)


@router.put("/{patient_id}")
def update_patient(
    patient_id: uuid.UUID, payload: PatientUpdate, session: SessionDep, _: WriteAuth
):
    """Update demographic fields of an existing patient record."""
    target = patient_service.get_active_patient(session, patient_id)
    patient = patient_service.update_patient(session, target, payload)
    return ok(patient_dict(patient))


@router.delete("/{patient_id}")
def delete_patient(patient_id: uuid.UUID, session: SessionDep, _: WriteAuth):
    """Soft-delete a patient record (sets deleted_at timestamp)."""
    target = patient_service.get_active_patient(session, patient_id)
    patient_service.soft_delete_patient(session, target)
    return ok({"patient_id": str(patient_id), "deleted": True})
