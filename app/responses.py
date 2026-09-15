"""Consistent JSON response envelope helpers and serializers."""

from __future__ import annotations

from typing import Any, Optional
from fastapi.responses import JSONResponse
from app.models import Patient, Sex, isoformat_dt


def ok(data: Any, status_code: int = 200) -> JSONResponse:
    """Return standard success JSON envelope."""
    return JSONResponse(status_code=status_code, content={"data": data, "error": None})


def err(message: str, status_code: int) -> JSONResponse:
    """Return standard error JSON envelope."""
    return JSONResponse(status_code=status_code, content={"data": None, "error": message})


def patient_dict(p: Patient) -> dict[str, Any]:
    """Serialize Patient SQLModel instance into JSON-compatible dictionary."""
    return {
        "patient_id": str(p.patient_id),
        "first_name": p.first_name,
        "last_name": p.last_name,
        "date_of_birth": p.date_of_birth.isoformat(),
        "sex": p.sex.value if isinstance(p.sex, Sex) else p.sex,
        "phone_number": p.phone_number,
        "email": p.email,
        "address_line_1": p.address_line_1,
        "address_line_2": p.address_line_2,
        "city": p.city,
        "state": p.state,
        "zip_code": p.zip_code,
        "insurance_provider": p.insurance_provider,
        "insurance_member_id": p.insurance_member_id,
        "preferred_language": p.preferred_language,
        "emergency_contact_name": p.emergency_contact_name,
        "emergency_contact_phone": p.emergency_contact_phone,
        "created_at": isoformat_dt(p.created_at),
        "updated_at": isoformat_dt(p.updated_at),
        "deleted_at": isoformat_dt(p.deleted_at),
    }
