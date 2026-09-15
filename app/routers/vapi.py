"""Vapi webhook router for tool calls and conversation events."""

from __future__ import annotations

import json
import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.routers.deps import SessionDep, WriteAuth
from app.services import vapi_service

logger = logging.getLogger("patients.vapi_router")

router = APIRouter(prefix="/vapi", tags=["Vapi Webhook"])


@router.post("/webhook")
async def handle_vapi_webhook(request: Request, session: SessionDep, _: WriteAuth):
    """
    Main webhook entrypoint for Vapi.
    Receives tool-calls (find_patient, create_patient, update_patient)
    and end-of-call reports for transcript storage.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"results": [], "error": "Invalid JSON"})

    message = body.get("message") if isinstance(body.get("message"), dict) else body
    event_type = str(message.get("type") or "")
    logger.info("Received Vapi event: type=%s", event_type or "unspecified")

    # Handle end-of-call transcript report
    if event_type in {"end-of-call-report", "end-of-call-report-truncated"}:
        try:
            vapi_service.save_end_of_call(session, message)
        except Exception:
            logger.exception("Failed to store end-of-call report")
        return JSONResponse(status_code=200, content={"ok": True})

    # Acknowledge non-tool status events
    if event_type and event_type not in {"tool-calls", "function-call", "tool.calls"}:
        return JSONResponse(status_code=200, content={"ok": True})

    # Process tool calls
    tool_calls = vapi_service.extract_tool_calls(body)
    results = []
    for call in tool_calls:
        name = vapi_service.get_tool_name(call)
        tool_id = vapi_service.get_tool_id(call)
        args = vapi_service.get_tool_args(call)
        logger.info("Executing Vapi tool '%s' with args: %s", name, json.dumps(args, default=str))

        try:
            payload, error = vapi_service.handle_tool_call(session, name, args)
        except Exception:
            logger.exception("Unexpected error executing tool '%s'", name)
            payload, error = None, "A database error occurred. Apologize and ask the caller to try again shortly."

        results.append(vapi_service.format_vapi_result(tool_id, name, payload, error))

    return JSONResponse(status_code=200, content={"results": results})
