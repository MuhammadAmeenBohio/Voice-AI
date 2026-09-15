"""Call records and transcript REST endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from sqlmodel import col, select

from app.models import CallRecord, isoformat_dt
from app.responses import ok
from app.routers.deps import SessionDep

router = APIRouter(prefix="/calls", tags=["Calls"])


@router.get("")
def list_calls(session: SessionDep):
    """Retrieve all recorded calls, summaries, and transcripts."""
    records = session.exec(select(CallRecord).order_by(col(CallRecord.created_at).desc())).all()
    return ok(
        [
            {
                "call_id": r.call_id,
                "transcript": r.transcript,
                "summary": r.summary,
                "caller_phone": r.caller_phone,
                "patient_id": str(r.patient_id) if r.patient_id else None,
                "created_at": isoformat_dt(r.created_at),
            }
            for r in records
        ]
    )
