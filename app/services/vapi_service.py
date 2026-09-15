"""Dispatcher and processor for Vapi tool-calls and end-of-call webhooks."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Optional
from fastapi import HTTPException
from sqlmodel import Session

from app.models import (
    AppointmentCreate,
    CallRecord,
    PatientCreate,
    PatientUpdate,
)
from app.responses import patient_dict
from app.services import patient_service

logger = logging.getLogger("patients.vapi")


def extract_tool_calls(body: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract tool call objects from various Vapi message structures."""
    msg = body.get("message") if isinstance(body.get("message"), dict) else body
    calls = msg.get("toolCallList") or msg.get("toolCalls") or []
    if not calls:
        wrapped = msg.get("toolWithToolCallList") or []
        for item in wrapped:
            tc = item.get("toolCall") if isinstance(item, dict) else None
            if isinstance(tc, dict):
                calls.append(tc)
    return [c for c in calls if isinstance(c, dict)]


def get_tool_name(call: dict[str, Any]) -> str:
    fn = call.get("function") or {}
    return str(call.get("name") or fn.get("name") or "")


def get_tool_id(call: dict[str, Any]) -> str:
    return str(call.get("id") or call.get("toolCallId") or "")


def get_tool_args(call: dict[str, Any]) -> dict[str, Any]:
    args = call.get("parameters") or call.get("arguments") or {}
    fn = call.get("function") or {}
    if not args:
        args = fn.get("arguments") or fn.get("parameters") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            args = {}
    return args if isinstance(args, dict) else {}


def format_vapi_result(
    tool_call_id: str, name: str, payload: Any, error: Optional[str] = None
) -> dict[str, Any]:
    text = error if error else json.dumps(payload, default=str)
    return {"name": name, "toolCallId": tool_call_id, "result": text}


def handle_tool_call(
    session: Session, name: str, args: dict[str, Any]
) -> tuple[Any, Optional[str]]:
    """Execute domain action for a Vapi tool call and return (result, error)."""
    if name == "find_patient_by_phone":
        phone = args.get("phone_number") or args.get("phone")
        if not phone:
            return None, "phone_number is required"
        try:
            rows = patient_service.list_patients(session, phone_number=str(phone))
        except HTTPException as e:
            return None, str(e.detail)
        if not rows:
            return {"found": False, "patients": []}, None
        return {
            "found": True,
            "patients": [patient_dict(p) for p in rows],
            "message": (
                f"Existing record found for {rows[0].first_name} {rows[0].last_name}. "
                "Ask if they want to update their record instead of creating a new patient."
            ),
        }, None

    if name == "create_patient":
        try:
            payload = PatientCreate.model_validate(args)
            patient = patient_service.create_patient(session, payload)
        except HTTPException as e:
            return None, str(e.detail)
        except Exception as e:
            return None, f"Validation failed: {e}"
        return {
            "success": True,
            "patient_id": str(patient.patient_id),
            "first_name": patient.first_name,
            "message": f"Saved. Confirm with the caller that they are all set, {patient.first_name}.",
        }, None

    if name == "update_patient":
        pid = args.get("patient_id")
        if not pid:
            return None, "patient_id is required"
        try:
            patient_id = uuid.UUID(str(pid))
        except ValueError:
            return None, "patient_id must be a valid UUID"
        fields = {k: v for k, v in args.items() if k != "patient_id"}
        try:
            payload = PatientUpdate.model_validate(fields)
            target = patient_service.get_active_patient(session, patient_id)
            patient = patient_service.update_patient(session, target, payload)
        except HTTPException as e:
            return None, str(e.detail)
        except Exception as e:
            return None, f"Validation failed: {e}"
        return {
            "success": True,
            "patient_id": str(patient.patient_id),
            "first_name": patient.first_name,
            "message": f"Updated record for {patient.first_name}.",
        }, None

    if name == "schedule_appointment":
        pid = args.get("patient_id")
        if not pid:
            return None, "patient_id is required"
        try:
            patient_id = uuid.UUID(str(pid))
        except ValueError:
            return None, "patient_id must be a valid UUID"
        try:
            payload = AppointmentCreate(
                patient_id=patient_id,
                appointment_date=args.get("appointment_date", ""),
                appointment_time=args.get("appointment_time", "09:00 AM"),
                reason=args.get("reason", "Intake Consultation"),
            )
            appt = patient_service.schedule_appointment(session, payload)
        except Exception as e:
            return None, f"Failed to schedule appointment: {e}"
        return {
            "success": True,
            "appointment_id": str(appt.appointment_id),
            "date": appt.appointment_date,
            "time": appt.appointment_time,
            "message": f"Appointment scheduled on {appt.appointment_date} at {appt.appointment_time}.",
        }, None

    return None, f"Unknown tool: {name}"


def save_end_of_call(session: Session, msg: dict[str, Any]) -> None:
    """Store complete call transcript, summary, and duration upon call end."""
    call = msg.get("call") or {}
    call_id = str(call.get("id") or msg.get("callId") or uuid.uuid4())
    artifact = msg.get("artifact") or {}
    transcript = artifact.get("transcript") or msg.get("transcript")
    if isinstance(transcript, list):
        transcript = "\n".join(
            f"{t.get('role', '')}: {t.get('message') or t.get('content') or ''}"
            for t in transcript
            if isinstance(t, dict)
        )
    customer = call.get("customer") or {}
    caller = customer.get("number") or (
        msg.get("customer", {}).get("number") if isinstance(msg.get("customer"), dict) else None
    )

    record = session.get(CallRecord, call_id) or CallRecord(call_id=call_id)
    record.transcript = str(transcript) if transcript else record.transcript
    record.summary = msg.get("summary") or artifact.get("summary") or record.summary
    record.caller_phone = caller or record.caller_phone
    session.add(record)
    session.commit()
    logger.info("Saved call report call_id=%s summary=%s", call_id, (record.summary or "")[:150])
