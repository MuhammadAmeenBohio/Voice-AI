# Voice AI System Specification & Calling Guide (Calling from Pakistan & Global)

This document contains the complete technical specification, all requirements preserved from the assessment, and the exact APIs and setups needed to test and call the Voice AI agent from Pakistan or anywhere globally.

---

## 1. Why Calling US Numbers Fails from Pakistan & The Solutions

### The Problem
When you dial a standard US phone number (e.g. `+1 434-290-7724` or `+1 415...`) from a mobile phone in Pakistan (Jazz, Zong, Telenor, Ufone):
1. **Carrier Outbound IDD Restrictions**: In Pakistan, outbound International Direct Dialing (IDD) is disabled by default on many SIM cards unless explicitly activated with carrier deposit/bundle. Without it, the network disconnects immediately with a generic tone or error.
2. **High International Airtime Rates**: Direct calls from Pakistan to the US cost 30–50 PKR/minute on mobile networks.
3. **VoIP Virtual Number Filtering**: Numbers provisioned via free trial platforms (like Vapi's free pool) are often tagged as VoIP/virtual numbers. Some international carrier switches do not complete routes to unverified US VoIP numbers.
4. **Vapi Trial Expiry**: Free trial accounts on Vapi have a $10 credit limit. When exhausted, inbound calls are terminated with `call.start.error-subscription-insufficient-credits`.

---

## 2. The 4 Methods to Call the Agent from Pakistan

### Method 1: In-Browser Web Voice Calling (WebRTC) — **RECOMMENDED (0 PKR, 0 US Carrier Fees)**
Vapi provides a high-fidelity WebRTC Web Calling SDK (`@vapi-ai/web`).
- **How it works**: We embed a "Talk to Muhammad" voice call button directly into our Dashboard.
- **Experience**: You open the web dashboard in Chrome/Edge on your PC or smartphone in Pakistan, click **"Start Voice Call"**, speak into your microphone, and converse with Muhammad in real time.
- **Latency & Quality**: Ultra-low latency (<600ms), crystal-clear HD audio, and zero phone carrier fees.
- **Reviewer Friendly**: In accordance with the challenge FAQ (*"Provide a working local setup with clear instructions for us to test"*), anyone in the world can test the system without needing a US SIM card.

### Method 2: Calling via Skype / Google Voice / Viber Out from Pakistan
If you want to dial a real phone number:
1. Open **Skype**, **Google Voice**, or **Viber Out** on your PC or phone in Pakistan.
2. Dial the provisioned US number: `+1 (724) 304-6263`.
3. Skype and Google Voice route through US domestic PSTN trunks directly, bypassing Pakistani telecom carrier blocks for pennies per minute.

### Method 3: SIP Softphone App (Zoiper / Linphone)
- Vapi supports direct SIP URI calls (e.g., `sip:your-assistant-id@sip.vapi.ai`).
- You install a free SIP app like **Zoiper** or **Linphone** on your mobile phone in Pakistan.
- You configure the SIP endpoint and dial Muhammad over Wi-Fi / 4G data for completely free VoIP calling.

### Method 4: Twilio Number with Global Inbound Routing
- If a dedicated physical phone number is strictly required:
  1. Create a **Twilio** account.
  2. Purchase a US Local or Toll-Free number ($1.15/month).
  3. Under Twilio Voice Settings, ensure **Geo Permissions** allow inbound traffic globally.
  4. In the Vapi Dashboard: Navigate to **Phone Numbers** -> **Import Twilio Number**, and paste your Twilio Account SID and Auth Token.

---

## 3. Complete List of APIs & Credentials Required

| Component | Required? | Service / API | What It's Used For | Where to Get It | Cost |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Voice AI & Telephony** | **YES** | **Vapi API Key** (`VAPI_API_KEY`) | Creates/configures the assistant, tools, and webhook | [vapi.ai](https://vapi.ai) | Free ($10 trial credit, no credit card required) |
| **Web Call Dialer** | **YES** | **Vapi Public Key** (`VAPI_PUBLIC_KEY`) | Authenticates the in-browser WebRTC voice dialer on the dashboard | Vapi Dashboard -> Account -> API Keys -> Public Key | Free (Included in Vapi) |
| **LLM Engine** | *Optional* | **OpenAI API Key** (`OPENAI_API_KEY`) | Powers GPT-4o-mini reasoning & conversation | [platform.openai.com](https://platform.openai.com) | Vapi includes GPT-4o-mini natively from trial credit, so you don't even need your own OpenAI key! |
| **Public Webhook Tunnel** | **YES (for local dev)** | **ngrok** (`NGROK_AUTHTOKEN`) or **Cloudflare Tunnel** | Exposes local FastAPI (`localhost:8000`) so Vapi can call `/vapi/webhook` | [ngrok.com](https://ngrok.com) | Free tier |
| **Cloud Hosting** | *Optional* | **Railway** or **Render** | Production hosting for public HTTPS URL | [railway.app](https://railway.app) or [render.com](https://render.com) | Free trial / free tier |
| **BYO US Phone Number** | *Optional* | **Twilio** (`ACCOUNT_SID`, `AUTH_TOKEN`) | Only needed if Vapi free number pool is empty or for custom global routing | [twilio.com](https://twilio.com) | ~$1.15 for 1 US phone number |

---

## 4. Preserved Core Architecture & Specifications (From Friend's Repo & PDF)

### Data Model (`Patient` SQLModel)
1. `patient_id`: UUIDv4 primary key (auto-generated)
2. `first_name`: 1–50 chars, alphabetic + hyphens/apostrophes (Required)
3. `last_name`: 1–50 chars, alphabetic + hyphens/apostrophes (Required)
4. `date_of_birth`: ISO Date YYYY-MM-DD, valid date not in the future (Required)
5. `sex`: Enum (`Male`, `Female`, `Other`, `Decline to Answer`) (Required)
6. `phone_number`: Valid U.S. 10-digit number (normalized, unique among active patients) (Required)
7. `email`: Valid email format (Optional)
8. `address_line_1`: Street address (Required)
9. `address_line_2`: Apt / Suite / Unit (Optional)
10. `city`: 1–100 characters (Required)
11. `state`: Valid 2-letter U.S. state abbreviation (Required)
12. `zip_code`: 5-digit or ZIP+4 format (Required)
13. `insurance_provider`: Name of provider (Optional)
14. `insurance_member_id`: Alphanumeric member ID (Optional)
15. `preferred_language`: Default 'English' (Optional)
16. `emergency_contact_name`: Full name (Optional)
17. `emergency_contact_phone`: Valid 10-digit phone number (Optional)
18. `created_at`: UTC timestamp (Auto)
19. `updated_at`: UTC timestamp (Auto)
20. `deleted_at`: UTC timestamp for soft delete (Auto)

### API Standards & Envelope
Every API response strictly follows the envelope format:
- Success: `{ "data": <payload>, "error": null }`
- Failure: `{ "data": null, "error": "<error_message>" }`

### REST Endpoints:
- `GET /patients`: Filterable by `?last_name=`, `?date_of_birth=`, `?phone_number=`
- `GET /patients/{id}`: Single patient record
- `POST /patients`: Create record (HTTP 201)
- `PUT /patients/{id}`: Partial update (HTTP 200)
- `DELETE /patients/{id}`: Soft delete (sets `deleted_at`, HTTP 200)
- `GET /calls`: Stored Vapi call transcripts and summaries
- `POST /vapi/webhook`: Webhook handler for Vapi `tool-calls` and `end-of-call-report`

### Conversational Rules (Muhammad System Prompt):
1. Warm, human intake coordinator persona; short conversational turns.
2. Collects required fields first, 1 or 2 at a time.
3. Offers optional fields bundled: *"I can also collect your insurance information, emergency contact, and preferred language. Would you like to provide any of those?"*
4. Immediate re-prompt on invalid data with a concise, helpful reason.
5. As soon as phone number is provided, calls `find_patient_by_phone`. If found: *"It looks like we already have a record for [Name]. Would you like to update your information instead?"*
6. Reads back **all** collected information clearly before calling `create_patient`.
7. Concludes with: *"You're all set, [First Name]. Thanks for registering with us. Have a good day!"*
8. Switches to Spanish if caller says *"Hablo español"*.
