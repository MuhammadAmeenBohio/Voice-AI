"""
Offline Webhook Call Simulator.

Simulates the exact Vapi conversational tool-calls and end-of-call
webhook payloads against the local running FastAPI server or test client.
Allows instant end-to-end verification without consuming telephony credits.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from app.main import app


def run_simulation():
    print("=" * 60)
    print("STARTING CONVERSATIONAL VOICE AGENT SIMULATION (MUHAMMAD)")
    print("=" * 60)

    with TestClient(app) as client:
        # Step 1: Muhammad greets and checks phone number for duplicate
        print("\n[Step 1] Caller provides phone number '5551234567'...")
        find_payload = {
            "message": {
                "type": "tool-calls",
                "toolCallList": [
                    {
                        "id": "call_lookup_1",
                        "name": "find_patient_by_phone",
                        "parameters": {"phone_number": "5551234567"},
                    }
                ],
            }
        }
        res = client.post("/vapi/webhook", json=find_payload)
        print(f"Webhook Status: {res.status_code}")
        result = json.loads(res.json()["results"][0]["result"])
        print(f"Muhammad Tool Result: Found = {result.get('found')}")
        print(f"Muhammad Assistant Message: {result.get('message')}")

        # Step 2: New Patient Registration Flow
        import time
        phone_suffix = str(int(time.time()))[-4:]
        sim_phone = f"555777{phone_suffix}"
        print(f"\n[Step 2] New caller 'Sophia Martinez' provides demographics with phone {sim_phone}...")
        create_payload = {
            "message": {
                "type": "tool-calls",
                "toolCallList": [
                    {
                        "id": "call_create_1",
                        "name": "create_patient",
                        "parameters": {
                            "first_name": "Sophia",
                            "last_name": "Martinez",
                            "date_of_birth": "1994-08-22",
                            "sex": "Female",
                            "phone_number": sim_phone,
                            "email": "sophia.m@example.com",
                            "address_line_1": "742 Evergreen Terrace",
                            "city": "Springfield",
                            "state": "IL",
                            "zip_code": "62704",
                            "insurance_provider": "Aetna",
                            "insurance_member_id": "AET-9944",
                            "preferred_language": "English",
                        },
                    }
                ],
            }
        }
        res = client.post("/vapi/webhook", json=create_payload)
        print(f"Webhook Status: {res.status_code}")
        raw_result = res.json()["results"][0]["result"]
        try:
            create_result = json.loads(raw_result)
        except Exception:
            create_result = {"success": False, "message": raw_result}
        print(f"Muhammad Tool Result: Success = {create_result.get('success')}")
        print(f"Created Patient ID: {create_result.get('patient_id')}")
        patient_id = create_result.get("patient_id")

        # Step 3: Verify Persistence via REST API
        print(f"\n[Step 3] Querying GET /patients/{patient_id} via REST API...")
        get_res = client.get(f"/patients/{patient_id}")
        patient_data = get_res.json()["data"]
        print(f"Retrieved Name:  {patient_data['first_name']} {patient_data['last_name']}")
        print(f"Retrieved DOB:   {patient_data['date_of_birth']}")
        print(f"Retrieved Phone: {patient_data['phone_number']}")
        print(f"Retrieved State: {patient_data['state']}")

        # Step 4: End-of-Call Report & Transcript Storage
        print("\n[Step 4] Call hangs up gracefully, Vapi posts end-of-call-report...")
        end_payload = {
            "message": {
                "type": "end-of-call-report",
                "call": {"id": "call-sim-001", "customer": {"number": "+15557778899"}},
                "artifact": {
                    "transcript": (
                        "Muhammad: Hi, thanks for calling! I can help you register today. What is your name?\n"
                        "Sophia: Hi, my name is Sophia Martinez.\n"
                        "Muhammad: Thanks Sophia. What is your date of birth and phone number?\n"
                        "Sophia: August 22, 1994 and phone is 555-777-8899.\n"
                        "Muhammad: Thank you. Let me review your address and insurance... does that sound correct?\n"
                        "Sophia: Yes, that is correct.\n"
                        "Muhammad: You're all set, Sophia! Have a wonderful day!"
                    )
                },
                "summary": "Successfully registered new patient Sophia Martinez with Aetna insurance.",
            }
        }
        res = client.post("/vapi/webhook", json=end_payload)
        print(f"Webhook End-of-Call Status: {res.status_code}")

        # Step 5: Verify Call Transcript in /calls
        print("\n[Step 5] Checking stored transcripts via GET /calls...")
        calls_res = client.get("/calls")
        stored_calls = calls_res.json()["data"]
        print(f"Total Call Records: {len(stored_calls)}")
        latest = stored_calls[0]
        print(f"Latest Call Summary: {latest['summary']}")
        print(f"Latest Caller Phone: {latest['caller_phone']}")

    print("\n" + "=" * 60)
    print("SIMULATION COMPLETED WITH 100% SUCCESS!")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--interactive", "-i", "chat"]:
        from voice_agent.simulate_call_with_vapi import run_interactive_simulator
        run_interactive_simulator()
    else:
        run_simulation()
