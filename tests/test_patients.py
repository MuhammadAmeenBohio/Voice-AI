"""Comprehensive test suite for Voice AI Patient Registration System."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

from app.database import engine
from app.main import app
from tests.conftest import assert_envelope, sample_patient


def test_health_and_root(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = assert_envelope(r)
    assert body["data"]["status"] == "ok"
    assert body["error"] is None

    r = client.get("/")
    assert r.status_code == 200
    assert assert_envelope(r)["data"]["patients"] == "/patients"


def test_seed_on_startup():
    SQLModel.metadata.drop_all(engine)
    with TestClient(app, raise_server_exceptions=False) as c:
        r = c.get("/patients")
        names = {(p["first_name"], p["last_name"]) for p in r.json()["data"]}
        assert ("Jane", "Doe") in names
        assert ("Robert", "Smith") in names


def test_create_list_get_update_soft_delete(client):
    r = client.post("/patients", json=sample_patient())
    assert r.status_code == 201
    body = assert_envelope(r)
    assert body["error"] is None
    pid = body["data"]["patient_id"]
    uuid.UUID(pid)
    assert body["data"]["state"] == "CO"
    assert body["data"]["phone_number"] == "5554443333"
    assert body["data"]["preferred_language"] == "English"
    assert body["data"]["created_at"]
    assert body["data"]["deleted_at"] is None

    # List all
    r = client.get("/patients")
    assert r.status_code == 200
    assert len(assert_envelope(r)["data"]) == 1

    # Filter by phone
    r = client.get("/patients", params={"phone_number": "555-444-3333"})
    assert len(assert_envelope(r)["data"]) == 1

    # Filter by last name
    r = client.get("/patients", params={"last_name": "johnson"})
    assert len(assert_envelope(r)["data"]) == 1

    # Filter by DOB
    r = client.get("/patients", params={"date_of_birth": "05/20/1990"})
    assert len(assert_envelope(r)["data"]) == 1

    # Get single
    r = client.get(f"/patients/{pid}")
    assert assert_envelope(r)["data"]["first_name"] == "Alice"

    # Update patient
    r = client.put(f"/patients/{pid}", json={"last_name": "O'Neil", "city": "Boulder"})
    assert r.status_code == 200
    assert assert_envelope(r)["data"]["last_name"] == "O'Neil"
    assert assert_envelope(r)["data"]["city"] == "Boulder"

    # Soft delete
    r = client.delete(f"/patients/{pid}")
    assert r.status_code == 200
    assert assert_envelope(r)["data"]["deleted"] is True

    # Confirm not found after soft-delete
    assert client.get(f"/patients/{pid}").status_code == 404
    assert client.get("/patients").json()["data"] == []
    assert client.delete(f"/patients/{pid}").status_code == 404
    assert client.put(f"/patients/{pid}", json={"city": "Aspen"}).status_code == 404


def test_not_found(client):
    r = client.get(f"/patients/{uuid.uuid4()}")
    assert r.status_code == 404
    body = assert_envelope(r)
    assert body["data"] is None
    assert "not found" in body["error"].lower()


def test_duplicate_phone_rejected_until_soft_deleted(client):
    r = client.post("/patients", json=sample_patient())
    assert r.status_code == 201
    pid = r.json()["data"]["patient_id"]

    # Reusing active phone number is rejected with 400
    r = client.post("/patients", json=sample_patient(first_name="Alicia"))
    assert r.status_code == 400
    body = assert_envelope(r)
    assert body["data"] is None
    assert "already exists" in body["error"].lower()

    # Reusing via PUT is rejected with 400
    other = client.post("/patients", json=sample_patient(phone_number="5550001111", first_name="Bob")).json()["data"]
    r = client.put(f"/patients/{other['patient_id']}", json={"phone_number": "5554443333"})
    assert r.status_code == 400

    # Once soft-deleted, phone number can be re-registered
    assert client.delete(f"/patients/{pid}").status_code == 200
    r = client.post("/patients", json=sample_patient(first_name="Alicia"))
    assert r.status_code == 201
    assert r.json()["data"]["first_name"] == "Alicia"


def test_validation_phone_and_future_dob(client):
    r = client.post("/patients", json=sample_patient(phone_number="123"))
    assert r.status_code == 422
    assert assert_envelope(r)["data"] is None

    r = client.post("/patients", json=sample_patient(date_of_birth="2099-01-01"))
    assert r.status_code == 422
    assert "future" in assert_envelope(r)["error"].lower()


def test_validation_name_state_zip_sex_email_member_id(client):
    assert client.post("/patients", json=sample_patient(first_name="Alice123")).status_code == 422
    assert client.post("/patients", json=sample_patient(first_name="")).status_code == 422
    assert client.post("/patients", json=sample_patient(state="XX")).status_code == 422
    assert client.post("/patients", json=sample_patient(zip_code="802")).status_code == 422
    assert client.post("/patients", json=sample_patient(sex="Unknown")).status_code == 422
    assert client.post("/patients", json=sample_patient(email="not-an-email")).status_code == 422
    assert client.post("/patients", json=sample_patient(insurance_member_id="id with spaces!")).status_code == 422


def test_accepts_spoken_and_formatted_inputs(client):
    r = client.post(
        "/patients",
        json=sample_patient(
            date_of_birth="03/15/1985",
            phone_number="+1 (555) 111-2222",
            state="Texas",
            sex="female",
            zip_code="78701-1234",
            first_name="Anne-Marie",
            last_name="O'Neil",
            insurance_member_id="BC-99A",
        ),
    )
    assert r.status_code == 201, r.text
    data = assert_envelope(r)["data"]
    assert data["date_of_birth"] == "1985-03-15"
    assert data["phone_number"] == "5551112222"
    assert data["state"] == "TX"
    assert data["sex"] == "Female"
    assert data["zip_code"] == "78701-1234"
    assert data["first_name"] == "Anne-Marie"


def test_sex_decline_alias_and_plus_one_phone(client):
    r = client.post("/patients", json=sample_patient(sex="prefer not to say", phone_number="15553334444"))
    assert r.status_code == 201
    assert assert_envelope(r)["data"]["sex"] == "Decline to Answer"
    assert assert_envelope(r)["data"]["phone_number"] == "5553334444"


def test_missing_required_and_empty_update(client):
    r = client.post("/patients", json={"first_name": "A"})
    assert r.status_code == 422
    created = client.post("/patients", json=sample_patient()).json()["data"]["patient_id"]
    r = client.put(f"/patients/{created}", json={})
    assert r.status_code == 422


def test_bad_filter_query_params_are_400(client):
    assert client.get("/patients", params={"phone_number": "12"}).status_code == 400
    assert client.get("/patients", params={"date_of_birth": "not-a-date"}).status_code == 400


def test_optional_fields_empty_string_become_none(client):
    r = client.post("/patients", json=sample_patient(email="", address_line_2="", insurance_provider=""))
    assert r.status_code == 201
    data = assert_envelope(r)["data"]
    assert data["email"] is None
    assert data["address_line_2"] is None


def test_dashboard_html(client):
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "Muhammad Patient Intake" in r.text or "Active Patients" in r.text


def test_vapi_create_and_find_and_update(client):
    payload = {
        "message": {
            "type": "tool-calls",
            "toolCallList": [
                {
                    "id": "call_create_1",
                    "name": "create_patient",
                    "parameters": sample_patient(phone_number="5550001111"),
                }
            ],
        }
    }
    r = client.post("/vapi/webhook", json=payload)
    assert r.status_code == 200
    result = r.json()["results"][0]
    assert result["toolCallId"] == "call_create_1"
    inner = json.loads(result["result"])
    assert inner["success"] is True
    pid = inner["patient_id"]

    # find_patient_by_phone
    r = client.post(
        "/vapi/webhook",
        json={
            "message": {
                "type": "tool-calls",
                "toolCallList": [
                    {
                        "id": "call_find_1",
                        "name": "find_patient_by_phone",
                        "parameters": {"phone_number": "(555) 000-1111"},
                    }
                ],
            }
        },
    )
    found = json.loads(r.json()["results"][0]["result"])
    assert found["found"] is True
    assert found["patients"][0]["patient_id"] == pid

    # update_patient
    r = client.post(
        "/vapi/webhook",
        json={
            "message": {
                "type": "tool-calls",
                "toolCalls": [
                    {
                        "id": "call_upd_1",
                        "function": {
                            "name": "update_patient",
                            "arguments": {"patient_id": pid, "city": "Fort Collins"},
                        },
                    }
                ],
            }
        },
    )
    updated = json.loads(r.json()["results"][0]["result"])
    assert updated["success"] is True
    assert client.get(f"/patients/{pid}").json()["data"]["city"] == "Fort Collins"


def test_vapi_create_validation_error_is_returned_not_silent(client):
    r = client.post(
        "/vapi/webhook",
        json={
            "message": {
                "type": "tool-calls",
                "toolCallList": [
                    {
                        "id": "bad",
                        "name": "create_patient",
                        "parameters": sample_patient(phone_number="12", date_of_birth="2099-01-01"),
                    }
                ],
            }
        },
    )
    assert r.status_code == 200
    text = r.json()["results"][0]["result"]
    assert "Validation failed" in text or "future" in text.lower() or "phone" in text.lower()


def test_vapi_unknown_tool_and_openai_arguments_string(client):
    r = client.post(
        "/vapi/webhook",
        json={
            "message": {
                "type": "tool-calls",
                "toolCallList": [{"id": "x", "name": "unknown_tool", "parameters": {}}],
            }
        },
    )
    assert "Unknown tool" in r.json()["results"][0]["result"]


def test_vapi_end_of_call_report_stores_transcript(client):
    r = client.post(
        "/vapi/webhook",
        json={
            "message": {
                "type": "end-of-call-report",
                "call": {"id": "call-abc", "customer": {"number": "+15551212"}},
                "artifact": {"transcript": "Muhammad: Hi\nCaller: Hello"},
                "summary": "Registered Alice Johnson",
            }
        },
    )
    assert r.status_code == 200
    calls = client.get("/calls").json()["data"]
    assert len(calls) == 1
    assert calls[0]["call_id"] == "call-abc"
    assert "Hello" in calls[0]["transcript"]


def test_vapi_status_events_are_acked(client):
    r = client.post("/vapi/webhook", json={"message": {"type": "status-update", "status": "in-progress"}})
    assert r.status_code == 200


def test_hyphen_apostrophe_names_and_emergency_contact(client):
    r = client.post(
        "/patients",
        json=sample_patient(
            first_name="Mary Ann",
            last_name="D'Angelo",
            emergency_contact_name="John Doe",
            emergency_contact_phone="5559998888",
        ),
    )
    assert r.status_code == 201
    data = assert_envelope(r)["data"]
    assert data["first_name"] == "Mary Ann"
    assert data["emergency_contact_phone"] == "5559998888"


def test_unhandled_path_404_uses_envelope(client):
    r = client.get("/nonexistent-path")
    assert r.status_code == 404
    assert assert_envelope(r)["data"] is None


def test_name_and_city_length_boundaries(client):
    ok_name = "A" * 50
    r = client.post("/patients", json=sample_patient(first_name=ok_name, last_name="B"))
    assert r.status_code == 201
    r = client.post("/patients", json=sample_patient(first_name="A" * 51, phone_number="5550000001"))
    assert r.status_code == 422
    r = client.post("/patients", json=sample_patient(city="C" * 101, phone_number="5550000002"))
    assert r.status_code == 422


def test_appointment_scheduling(client):
    """Test bonus appointment scheduling tool."""
    patient = client.post("/patients", json=sample_patient(phone_number="5553337777")).json()["data"]
    pid = patient["patient_id"]

    r = client.post(
        "/vapi/webhook",
        json={
            "message": {
                "type": "tool-calls",
                "toolCallList": [
                    {
                        "id": "call_appt_1",
                        "name": "schedule_appointment",
                        "parameters": {
                            "patient_id": pid,
                            "appointment_date": "2026-10-15",
                            "appointment_time": "10:30 AM",
                            "reason": "Annual Wellness Check",
                        },
                    }
                ],
            }
        },
    )
    assert r.status_code == 200
    res = json.loads(r.json()["results"][0]["result"])
    assert res["success"] is True
    assert res["date"] == "2026-10-15"


def test_persists_in_sqlite_file(tmp_path):
    """Data must survive across separate processes / engine restarts."""
    db_file = tmp_path / "persisted_patients.db"
    url = f"sqlite:///{db_file.as_posix()}"
    payload = json.dumps(sample_patient(phone_number="5551212343"))

    create_code = f"""
import os, json
os.environ["DATABASE_URL"] = {url!r}
from fastapi.testclient import TestClient
import main
with TestClient(main.app) as c:
    r = c.post("/patients", json=json.loads({payload!r}))
    assert r.status_code == 201, r.text
    print(r.json()["data"]["patient_id"])
"""
    created = subprocess.run(
        [sys.executable, "-c", create_code],
        cwd=os.getcwd(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert created.returncode == 0, f"Error creating patient in child process: {created.stderr}"
    pid = created.stdout.strip().splitlines()[-1]

    read_code = f"""
import os
os.environ["DATABASE_URL"] = {url!r}
from fastapi.testclient import TestClient
import main
with TestClient(main.app) as c:
    r = c.get("/patients/" + {pid!r})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["phone_number"] == "5551212343"
"""
    read = subprocess.run(
        [sys.executable, "-c", read_code],
        cwd=os.getcwd(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert read.returncode == 0, f"Error reading patient in child process: {read.stderr}"
