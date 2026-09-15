"""Data models, database tables, and Pydantic schemas."""

from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import EmailStr, field_validator, model_validator
from sqlmodel import Field, SQLModel

from app.config import (
    MEMBER_ID_RE,
    NAME_RE,
    PHONE_DIGITS_RE,
    SEX_ALIASES,
    STATE_NAMES,
    US_STATES,
    ZIP_RE,
)


class Sex(str, Enum):
    male = "Male"
    female = "Female"
    other = "Other"
    decline = "Decline to Answer"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat_dt(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def empty_to_none(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def normalize_phone(value: str) -> str:
    digits = PHONE_DIGITS_RE.sub("", value or "")
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError("phone_number must be a valid U.S. 10-digit number")
    return digits


def validate_name(value: str, field_name: str) -> str:
    cleaned = re.sub(r"\s+", " ", (value or "").strip())
    if not (1 <= len(cleaned) <= 50) or not NAME_RE.match(cleaned):
        raise ValueError(
            f"{field_name} must be 1–50 characters and contain only letters, spaces, hyphens, or apostrophes"
        )
    return cleaned


def parse_dob(value: date | str) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        dob = value
    else:
        text = str(value).strip()
        dob = None
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y"):
            try:
                dob = datetime.strptime(text, fmt).date()
                break
            except ValueError:
                continue
        if dob is None:
            raise ValueError("date_of_birth must be a valid date (YYYY-MM-DD or MM/DD/YYYY)")
    if dob > date.today():
        raise ValueError("date_of_birth cannot be in the future")
    if dob.year < 1900:
        raise ValueError("date_of_birth year must be 1900 or later")
    return dob


def normalize_state(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        raise ValueError("state must be a valid 2-letter U.S. state abbreviation")
    upper = raw.upper()
    if upper in US_STATES:
        return upper
    mapped = STATE_NAMES.get(raw.lower())
    if mapped:
        return mapped
    raise ValueError("state must be a valid 2-letter U.S. state abbreviation")


def normalize_sex(value: Any) -> str:
    if isinstance(value, Sex):
        return value.value
    text = str(value or "").strip()
    mapped = SEX_ALIASES.get(text.lower())
    if mapped:
        return mapped
    for member in Sex:
        if member.value.lower() == text.lower():
            return member.value
    raise ValueError("sex must be Male, Female, Other, or Decline to Answer")


def normalize_zip(value: str) -> str:
    z = (value or "").strip()
    if not ZIP_RE.match(z):
        raise ValueError("zip_code must be 5-digit (#####) or ZIP+4 (#####-####)")
    return z


# --- Database Tables --------------------------------------------------------

class PatientBase(SQLModel):
    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)
    date_of_birth: date
    sex: Sex
    phone_number: str = Field(max_length=10, index=True)
    email: Optional[EmailStr] = None
    address_line_1: str = Field(max_length=200)
    address_line_2: Optional[str] = Field(default=None, max_length=200)
    city: str = Field(max_length=100)
    state: str = Field(min_length=2, max_length=2)
    zip_code: str = Field(max_length=10)
    insurance_provider: Optional[str] = Field(default=None, max_length=100)
    insurance_member_id: Optional[str] = Field(default=None, max_length=50)
    preferred_language: Optional[str] = Field(default="English", max_length=50)
    emergency_contact_name: Optional[str] = Field(default=None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(default=None, max_length=10)


class Patient(PatientBase, table=True):
    __tablename__ = "patients"

    patient_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    deleted_at: Optional[datetime] = Field(default=None, index=True)


class CallRecord(SQLModel, table=True):
    __tablename__ = "call_records"

    call_id: str = Field(primary_key=True, max_length=80)
    transcript: Optional[str] = None
    summary: Optional[str] = None
    caller_phone: Optional[str] = Field(default=None, max_length=20)
    patient_id: Optional[uuid.UUID] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utc_now)


class Appointment(SQLModel, table=True):
    __tablename__ = "appointments"

    appointment_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    patient_id: uuid.UUID = Field(index=True)
    appointment_date: str = Field(max_length=20)
    appointment_time: Optional[str] = Field(default="09:00 AM", max_length=20)
    reason: Optional[str] = Field(default="General Consultation", max_length=200)
    status: str = Field(default="Scheduled", max_length=20)
    created_at: datetime = Field(default_factory=utc_now)


# --- Pydantic Request Schemas -----------------------------------------------

class PatientCreate(PatientBase):
    @field_validator("first_name")
    @classmethod
    def _first(cls, v: str) -> str:
        return validate_name(v, "first_name")

    @field_validator("last_name")
    @classmethod
    def _last(cls, v: str) -> str:
        return validate_name(v, "last_name")

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def _dob(cls, v: Any) -> date:
        return parse_dob(v)

    @field_validator("sex", mode="before")
    @classmethod
    def _sex(cls, v: Any) -> str:
        return normalize_sex(v)

    @field_validator("phone_number", mode="before")
    @classmethod
    def _phone(cls, v: str) -> str:
        return normalize_phone(v)

    @field_validator("state", mode="before")
    @classmethod
    def _state(cls, v: str) -> str:
        return normalize_state(v)

    @field_validator("zip_code", mode="before")
    @classmethod
    def _zip(cls, v: str) -> str:
        return normalize_zip(v)

    @field_validator("city")
    @classmethod
    def _city(cls, v: str) -> str:
        c = (v or "").strip()
        if not (1 <= len(c) <= 100):
            raise ValueError("city must be 1–100 characters")
        return c

    @field_validator("address_line_1")
    @classmethod
    def _addr1(cls, v: str) -> str:
        a = (v or "").strip()
        if not a:
            raise ValueError("address_line_1 is required")
        return a

    @field_validator(
        "email",
        "address_line_2",
        "insurance_provider",
        "insurance_member_id",
        "emergency_contact_name",
        "emergency_contact_phone",
        mode="before",
    )
    @classmethod
    def _empty_optional(cls, v: Any) -> Any:
        return empty_to_none(v)

    @field_validator("insurance_member_id")
    @classmethod
    def _member_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        text = v.strip()
        if not MEMBER_ID_RE.match(text):
            raise ValueError("insurance_member_id must be alphanumeric")
        return text

    @field_validator("emergency_contact_phone", mode="before")
    @classmethod
    def _ec_phone(cls, v: Optional[str]) -> Optional[str]:
        v = empty_to_none(v)
        if v is None:
            return None
        return normalize_phone(str(v))

    @field_validator("emergency_contact_name")
    @classmethod
    def _ec_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_name(v, "emergency_contact_name")

    @field_validator("preferred_language")
    @classmethod
    def _lang(cls, v: Optional[str]) -> Optional[str]:
        if v is None or str(v).strip() == "":
            return "English"
        return str(v).strip()


class PatientUpdate(SQLModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    sex: Optional[Sex] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name")
    @classmethod
    def _first(cls, v: Optional[str]) -> Optional[str]:
        return validate_name(v, "first_name") if v is not None else None

    @field_validator("last_name")
    @classmethod
    def _last(cls, v: Optional[str]) -> Optional[str]:
        return validate_name(v, "last_name") if v is not None else None

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def _dob(cls, v: Any) -> Optional[date]:
        if empty_to_none(v) is None:
            return None
        return parse_dob(v)

    @field_validator("sex", mode="before")
    @classmethod
    def _sex(cls, v: Any) -> Optional[str]:
        if empty_to_none(v) is None:
            return None
        return normalize_sex(v)

    @field_validator("phone_number", mode="before")
    @classmethod
    def _phone(cls, v: Optional[str]) -> Optional[str]:
        if empty_to_none(v) is None:
            return None
        return normalize_phone(v)

    @field_validator("state", mode="before")
    @classmethod
    def _state(cls, v: Optional[str]) -> Optional[str]:
        if empty_to_none(v) is None:
            return None
        return normalize_state(v)

    @field_validator("zip_code", mode="before")
    @classmethod
    def _zip(cls, v: Optional[str]) -> Optional[str]:
        if empty_to_none(v) is None:
            return None
        return normalize_zip(v)

    @field_validator(
        "email",
        "address_line_2",
        "insurance_provider",
        "insurance_member_id",
        "emergency_contact_name",
        "emergency_contact_phone",
        mode="before",
    )
    @classmethod
    def _empty_optional(cls, v: Any) -> Any:
        return empty_to_none(v)

    @field_validator("insurance_member_id")
    @classmethod
    def _member_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        text = v.strip()
        if not MEMBER_ID_RE.match(text):
            raise ValueError("insurance_member_id must be alphanumeric")
        return text

    @field_validator("emergency_contact_phone", mode="before")
    @classmethod
    def _ec_phone(cls, v: Optional[str]) -> Optional[str]:
        v = empty_to_none(v)
        if v is None:
            return None
        return normalize_phone(str(v))

    @field_validator("emergency_contact_name")
    @classmethod
    def _ec_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_name(v, "emergency_contact_name")

    @field_validator("city")
    @classmethod
    def _city(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        c = v.strip()
        if not (1 <= len(c) <= 100):
            raise ValueError("city must be 1–100 characters")
        return c

    @field_validator("address_line_1")
    @classmethod
    def _addr1(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        a = v.strip()
        if not a:
            raise ValueError("address_line_1 is required")
        return a

    @model_validator(mode="after")
    def _at_least_one(self) -> PatientUpdate:
        if not self.model_dump(exclude_unset=True):
            raise ValueError("at least one field is required for update")
        return self


class AppointmentCreate(SQLModel):
    patient_id: uuid.UUID
    appointment_date: str
    appointment_time: Optional[str] = "09:00 AM"
    reason: Optional[str] = "General Consultation"
