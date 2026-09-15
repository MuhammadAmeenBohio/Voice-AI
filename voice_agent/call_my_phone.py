"""
Trigger an outbound call from Vapi to your phone number.

Usage:
  uv run python voice_agent/call_my_phone.py +923001234567
  (or with US numbers: +14155552671)
"""

from __future__ import annotations

import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

API = "https://api.vapi.ai"


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run python voice_agent/call_my_phone.py <YOUR_PHONE_NUMBER_WITH_COUNTRY_CODE>")
        print("Example: uv run python voice_agent/call_my_phone.py +923001234567")
        sys.exit(1)

    target_phone = sys.argv[1].strip()
    api_key = os.getenv("VAPI_API_KEY", "").strip()
    assistant_id = os.getenv("VAPI_ASSISTANT_ID", "").strip()

    if not api_key:
        print("[ERROR] VAPI_API_KEY is not set in your .env file.")
        sys.exit(1)

    if not assistant_id:
        print("[ERROR] VAPI_ASSISTANT_ID is not set in your .env file.")
        print("Please set VAPI_ASSISTANT_ID=<your_assistant_id> in .env")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    print(f"Fetching phone numbers configured on your Vapi account...")
    with httpx.Client(timeout=30.0) as client:
        num_res = client.get(f"{API}/phone-number", headers=headers)
        if num_res.status_code >= 400:
            print(f"[ERROR] Failed to fetch phone numbers: {num_res.status_code} {num_res.text}")
            sys.exit(1)

        numbers = num_res.json()
        if not numbers:
            print("[ERROR] No phone number found in your Vapi account.")
            print("Please create a Free Vapi Number in your Vapi dashboard (Phone Numbers -> Create Phone Number).")
            sys.exit(1)

        # Select the phone number attached to this assistant or the first active number
        selected_number = next((n for n in numbers if n.get("assistantId") == assistant_id), numbers[0])
        phone_number_id = selected_number["id"]
        from_number = selected_number.get("number", "Unknown")

        print(f"[INFO] Using Vapi Outbound Line: {from_number} (ID: {phone_number_id})")
        print(f"[INFO] Dialing destination: {target_phone} ...")

        call_payload = {
            "assistantId": assistant_id,
            "phoneNumberId": phone_number_id,
            "customer": {
                "number": target_phone,
            },
        }

        resp = client.post(f"{API}/call/phone", headers=headers, json=call_payload)
        if resp.status_code >= 400:
            # Fallback to /call
            resp = client.post(f"{API}/call", headers=headers, json=call_payload)

        if resp.status_code >= 400:
            print(f"[ERROR] Call failed ({resp.status_code}): {resp.text}")
            sys.exit(1)

        call_data = resp.json()
        call_id = call_data.get("id")
        print("\n" + "=" * 50)
        print(f"CALL INITIATED SUCCESSFULLY!")
        print(f"Call ID: {call_id}")
        print(f"Your phone ({target_phone}) should ring in a few seconds!")
        print(f"Pick up and speak with Muhammad.")
        print("=" * 50)


if __name__ == "__main__":
    main()
