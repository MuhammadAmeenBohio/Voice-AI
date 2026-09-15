"""
Vapi Assistant Setup and Provisioning Script.

Creates or updates the 'Maya Patient Intake' assistant, links all tools,
and attaches a dialable US phone number.

Usage:
  set VAPI_API_KEY=your_key
  set PUBLIC_API_URL=https://your-domain.ngrok-free.app
  python voice_agent/setup_vapi.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import httpx
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.vapi.ai"
ASSISTANT_NAME = "Muhammad Patient Intake"


def die(msg: str, code: int = 1) -> None:
    print(f"\n[ERROR] {msg}", file=sys.stderr)
    raise SystemExit(code)


def main() -> None:
    key = os.getenv("VAPI_API_KEY", "").strip()
    public_url = os.getenv("PUBLIC_API_URL", "").strip().rstrip("/")

    if not key:
        print("[WARNING] VAPI_API_KEY is not set.")
        print("You can get a free key by signing up at https://vapi.ai ($10 free trial credits).")
        print("Once set in your .env file, re-run this script.\n")
        return

    if not public_url.startswith("https://") and not public_url.startswith("http://"):
        die("PUBLIC_API_URL must be an accessible URL, e.g. https://xyz.ngrok-free.app or https://your-app.up.railway.app")

    tools_doc = json.loads((ROOT / "voice_agent" / "tools.json").read_text(encoding="utf-8"))
    prompt = (ROOT / "voice_agent" / "system_prompt.md").read_text(encoding="utf-8")
    webhook_url = f"{public_url}/vapi/webhook"

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    tools_payload = []
    for item in tools_doc["tools"]:
        fn = item["function"]
        tools_payload.append(
            {
                "type": "function",
                "function": {
                    "name": fn["name"],
                    "description": fn.get("description", ""),
                    "parameters": fn["parameters"],
                },
                "server": {"url": webhook_url},
            }
        )

    llm_provider = os.getenv("LLM_PROVIDER", "groq" if os.getenv("GROQ_API_KEY") else "openai").strip().lower()
    if llm_provider == "groq":
        model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
        model_cfg = {
            "provider": "groq",
            "model": model_name,
            "temperature": 0.1,
            "messages": [{"role": "system", "content": prompt}],
            "tools": tools_payload,
        }
        print(f"[INFO] Using LLM Provider: GROQ with lightweight model '{model_name}'")
    else:
        model_cfg = {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.2,
            "messages": [{"role": "system", "content": prompt}],
            "tools": tools_payload,
        }
        print("[INFO] Using LLM Provider: OpenAI with model 'gpt-4o-mini'")

    assistant_body = {
        "name": ASSISTANT_NAME,
        "firstMessage": tools_doc.get("firstMessage"),
        "model": model_cfg,
        "voice": {
            "provider": "11labs",
            "voiceId": "21m00Tcm4TlvDq8ikWAM",  # Warm, professional natural voice (Rachel)
        },
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "en",
        },
        "server": {"url": webhook_url},
        "silenceTimeoutSeconds": 30,
        "maxDurationSeconds": 600,
        "endCallPhrases": ["goodbye", "have a wonderful day", "you're all set", "have a good day"],
    }

    print(f"Connecting to Vapi API with webhook: {webhook_url} ...")

    with httpx.Client(timeout=35.0) as client:
        # Check existing assistants
        list_resp = client.get(f"{API}/assistant", headers=headers)
        if list_resp.status_code >= 400:
            die(f"Vapi list assistants failed: {list_resp.status_code} {list_resp.text}")

        existing = next((a for a in list_resp.json() if a.get("name") == ASSISTANT_NAME), None)
        if existing:
            assistant_id = existing["id"]
            resp = client.patch(f"{API}/assistant/{assistant_id}", headers=headers, json=assistant_body)
            action = "Updated"
        else:
            resp = client.post(f"{API}/assistant", headers=headers, json=assistant_body)
            action = "Created"

        if resp.status_code >= 400:
            die(f"Vapi assistant {action.lower()} failed: {resp.status_code} {resp.text}")

        assistant = resp.json()
        assistant_id = assistant["id"]
        print(f"[SUCCESS] {action} assistant '{ASSISTANT_NAME}' with ID: {assistant_id}")

        # Check attached phone numbers
        num_resp = client.get(f"{API}/phone-number", headers=headers)
        if num_resp.status_code < 400:
            attached = next(
                (n for n in num_resp.json() if n.get("assistantId") == assistant_id),
                None,
            )
            if attached:
                print(f"[INFO] Existing dialable US phone number attached: {attached.get('number')}")
            else:
                print("[INFO] Requesting a free US phone number from Vapi...")
                create_num = client.post(
                    f"{API}/phone-number",
                    headers=headers,
                    json={
                        "provider": "vapi",
                        "numberDesiredAreaCode": os.getenv("VAPI_AREA_CODE", "415"),
                        "assistantId": assistant_id,
                        "name": "Patient Intake Line",
                    },
                )
                if create_num.status_code < 400:
                    phone = create_num.json().get("number")
                    print(f"[SUCCESS] Provisioned new free US phone number: {phone}")
                else:
                    print(
                        f"[NOTE] Automated phone provisioning returned {create_num.status_code}.\n"
                        "To assign a phone number manually: log in to https://vapi.ai -> Phone Numbers -> Get a Free Number, and select 'Maya Patient Intake'."
                    )

    print("\n--- Setup Complete ---")
    print(f"Assistant ID: {assistant_id}")
    print(f"Webhook URL:  {webhook_url}")
    print("You can now call the phone number or use the in-browser Web Voice Dialer on the Dashboard!")


if __name__ == "__main__":
    main()
