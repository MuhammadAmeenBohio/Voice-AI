# Voice AI Patient Registration System (Muhammad)

An autonomous, conversational voice AI intake system accessible via real PSTN telephony and WebRTC browser voice calling. The system guides patients through U.S. outpatient demographic registration, performs real-time validation and duplicate detection, reads back collected data for explicit confirmation, persists records to a SQLite database across restarts, and exposes a RESTful API and interactive monitoring dashboard.

---

## System Architecture

```
                    +--------------------------------------------+
                    |               CALLER / USER                |
                    +--------------------------------------------+
                                  /                \
                    PSTN Phone   /                  \  WebRTC Browser Call
                    (US Number) /                    \ (Zero Carrier Fees)
                               v                      v
                   +--------------------------------------+
                   |         Vapi Voice AI Engine         |
                   |  - Deepgram Nova-2 (STT)             |
                   |  - OpenAI GPT-4o-mini (LLM)          |
                   |  - ElevenLabs / Vapi Voice (TTS)     |
                   +--------------------------------------+
                                      |
                         POST /vapi/webhook
                         (tool-calls & end-of-call)
                                      v
                   +--------------------------------------+
                   |        FastAPI Intake Backend        |
                   |  - Pydantic v2 Strict Validators     |
                   |  - Domain Service Layer              |
                   |  - Standard Envelope Formatting      |
                   +--------------------------------------+
                                      |
                     +----------------+----------------+
                     |                                 |
                     v                                 v
          +----------------------+          +----------------------+
          |   SQLite Database    |          | Glassmorphic UI      |
          | - patients table     |          | - Live Directory     |
          | - call_records table |          | - Call Transcripts   |
          | - appointments table |          | - WebRTC Voice Call  |
          +----------------------+          +----------------------+
```

---

## Tech Stack Justification

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Voice / Telephony** | **Vapi** | Turnkey integration of telephony, Deepgram STT, ElevenLabs TTS, and low-latency interruption handling (<600ms). Provides free dialable US numbers and native WebRTC browser voice calling. |
| **LLM Orchestration** | **GPT-4o-mini inside Vapi** | Cost-effective, low-latency conversational reasoning capable of natural out-of-order intake, error correction, and structured tool calling. |
| **Backend Framework** | **FastAPI** | High-performance async Python framework with automatic Swagger documentation, dependency injection, and clean exception handling. |
| **Data Layer** | **SQLModel + SQLite** | Combines SQLAlchemy ORM and Pydantic validation into a single paradigm. Zero-configuration persistent storage that survives server restarts. |
| **Package Manager** | **`uv`** | High-performance Python package and virtual environment manager providing sub-second installations and reproducible builds. |
| **Dashboard UI** | **Vanilla CSS + HTML5** | Modern glassmorphic dark-theme interface with zero external CSS framework bloat, instant rendering, and embedded Vapi Web Call SDK. |

---

## Project Structure

```
Voice AI/
├── app/
│   ├── config.py              # App settings, regexes, US state abbreviations
│   ├── database.py            # SQLite engine, sessions, startup seed records
│   ├── models.py              # Patient, CallRecord, Appointment tables & schemas
│   ├── responses.py           # Standard { data, error } envelope helpers
│   ├── services/
│   │   ├── patient_service.py # CRUD, duplicate phone check, soft-delete, filters
│   │   └── vapi_service.py    # Vapi tool-call & end-of-call report dispatcher
│   ├── routers/
│   │   ├── patients.py        # REST API (/patients endpoints)
│   │   ├── calls.py           # Call transcripts endpoint (/calls)
│   │   ├── vapi.py            # Vapi webhook handler (/vapi/webhook)
│   │   └── dashboard.py       # Interactive web dashboard route (/dashboard)
│   ├── static/                # Dashboard CSS & JavaScript (search, modals, WebRTC)
│   └── templates/             # Dashboard HTML markup
├── voice_agent/
│   ├── system_prompt.md       # Muhammad conversational prompt with stage-by-stage intake
│   ├── tools.json             # Function schemas for create, find, update, appointment
│   ├── setup_vapi.py          # Automated provisioning script for Vapi assistant & number
│   └── simulate_call.py       # Offline conversational webhook simulator
├── tests/
│   ├── conftest.py            # Pytest test fixtures & in-memory test DB
│   └── test_patients.py       # 23 automated tests covering all requirements
├── pyproject.toml             # uv configuration
├── requirements.txt           # Pip dependency manifest
└── README.md
```

---

## Quick Start & Local Setup (with `uv`)

### 1. Prerequisites
- Python 3.10+
- [`uv`](https://github.com/astral-sh/uv) package manager installed (`pip install uv` or `winget install --id=astral-sh.uv`)

### 2. Installation
```powershell
# Create virtual environment
uv venv

# Activate on Windows
.venv\Scripts\activate

# Install all dependencies
uv pip install -r requirements.txt

# Create environment configuration
copy .env.example .env
```

### 3. Run Automated Tests
```powershell
uv run pytest -v
```
*All 23 tests covering CRUD, server-side validation, soft delete, duplicate detection, Vapi tool-calls, and process persistence pass.*

### 4. Start the Application Server
```powershell
uv run uvicorn main:app --reload --port 8000
```

- **Dashboard:** [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## Testing the Voice Agent

### Option 1: In-Browser Web Voice Calling (Direct WebRTC — Zero Telecom Fees)
> [!IMPORTANT]
> **Why Web Calling Was Added**: Calling US PSTN numbers (`+1 ...`) from outside North America (e.g., Pakistan) frequently fails due to carrier-level International Direct Dialing (IDD) blocks, and free VoIP apps like TextNow or Dingtone often restrict calls to virtual VoIP trunks. 
> To provide an accessible, reliable, and free testing experience for reviewers and evaluators, i have integrated **Direct WebRTC In-Browser Voice Calling** directly into the application:
> 1. Open the dashboard at `http://localhost:8000/dashboard` (or `https://your-app.up.railway.app/dashboard`).
> 2. Click **"Start Voice Call"** (or use the standalone dialer at `/call`).
> 3. Grant browser microphone permission when prompted.
> 4. Speak naturally with **Muhammad**—the assistant listens in real-time via Deepgram STT, reasons with GPT-4o-mini, and responds with natural voice synthesis.
> 5. Your patient demographic data will be checked for duplicates, confirmed, saved into SQLite, and displayed live on the dashboard table!

### Option 2: Interactive Terminal Simulator
Experience Muhammad's intake conversation directly in your terminal:
```powershell
uv run python voice_agent/simulate_call.py --interactive
```
*(Or run `uv run python voice_agent/simulate_call.py` for automated end-to-end regression testing).*

### Option 3: Real Inbound Phone Telephony (US Line)
If calling from a US phone line or an enabled international service:
- **Intake Line:** `+1 (724) 304-6263`
- Connected to Muhammad on Vapi with real-time tool execution.

---

## Deployment to Railway (One-Click Cloud Hosting)

The repository includes a ready-to-use [Procfile](file:///c:/Users/Syscom/Desktop/Hello/Voice%20AI/Procfile) and [Dockerfile](file:///c:/Users/Syscom/Desktop/Hello/Voice%20AI/Dockerfile):

1. **Push to GitHub**:
   ```powershell
   git add .
   git commit -m "feat: complete voice AI patient registration system"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```
2. **Deploy on Railway**:
   - Go to [railway.com](https://railway.com) and click **"New Project"** -> **"Deploy from GitHub repo"**.
   - Select your repository. Railway will detect the `Procfile`/`Dockerfile` and build automatically.
   - Go to **Settings** -> **Networking** -> **Generate Domain** to get your public HTTPS URL (e.g., `https://my-app.up.railway.app`).
3. **Set Environment Variables in Railway**:
   - `DATABASE_URL=sqlite:///./patients.db`
   - `VAPI_API_KEY=your_vapi_private_key`
   - `VAPI_PUBLIC_KEY=your_vapi_public_key`
   - `VAPI_ASSISTANT_ID=f87a7c69-c6a9-4bfe-91c6-a9e90c0b39ea`
   - `PUBLIC_API_URL=https://your-generated-domain.up.railway.app`
4. **Link Vapi Webhook**:
   - Set `PUBLIC_API_URL` to your Railway domain in your local `.env` and run:
     ```powershell
     uv run python voice_agent/setup_vapi.py
     ```
   - Now, Vapi cloud webhooks will execute against your live Railway backend!

---

## REST API Specification

All mutating and querying endpoints adhere to the required JSON response envelope:
```json
{
  "data": <payload>,
  "error": null
}
```

| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Service liveness probe | 200 |
| `GET` | `/patients` | List active patients (`?last_name=`, `?date_of_birth=`, `?phone_number=`) | 200, 400 |
| `GET` | `/patients/{id}` | Retrieve single active patient by UUID | 200, 404 |
| `POST` | `/patients` | Register new patient (server-side validation) | 201, 400, 422 |
| `PUT` | `/patients/{id}` | Update existing patient record (partial update) | 200, 400, 404, 422 |
| `DELETE` | `/patients/{id}` | Soft-delete patient (sets `deleted_at`) | 200, 404 |
| `GET` | `/calls` | List recorded voice intake summaries & transcripts | 200 |
| `POST` | `/vapi/webhook` | Webhook for Vapi tool-calling and end-of-call events | 200, 400 |

---

## Patient Demographic Data Model

Enforces all 18 demographic fields required by U.S. healthcare providers:
- `first_name`, `last_name`: 1–50 characters, alphabetic with hyphens and apostrophes.
- `date_of_birth`: Valid date, not in the future, normalized to `YYYY-MM-DD`.
- `sex`: Enum (`Male`, `Female`, `Other`, `Decline to Answer`).
- `phone_number`: Valid U.S. 10-digit number (normalized, unique across active patients).
- `email`: Valid RFC email format (optional).
- `address_line_1`, `address_line_2` (apt/suite), `city`, `state` (2-letter abbreviation), `zip_code` (5-digit or ZIP+4).
- `insurance_provider`, `insurance_member_id` (alphanumeric).
- `preferred_language`: Defaults to `English`.
- `emergency_contact_name`, `emergency_contact_phone`.
- `patient_id` (UUIDv4), `created_at` (UTC), `updated_at` (UTC), `deleted_at` (UTC soft delete).

---

## Conversational Features & Bonus Challenges

1. **Natural Conversational Flow**: Muhammad introduces himself warmly and collects information conversationally (1 or 2 fields at a time) rather than interrogating.
2. **Optional Bundle Opt-In**: Collects required fields first, then asks: *"I can also collect your insurance information, emergency contact, and preferred language. Would you like to provide any of those?"*
3. **Duplicate Recognition**: Checks phone number immediately. If found, asks: *"It looks like we already have a record for [Name]. Would you like to update your information instead?"*
4. **Mandatory Confirmation**: Always reads back all fields in plain English before calling `create_patient`.
5. **Spanish Language Switch (Bonus)**: If the caller says *"Hablo español"*, Muhammad immediately switches to fluent Spanish intake.
6. **Appointment Scheduling (Bonus)**: Includes `schedule_appointment` tool and database table for booking initial consultations.
7. **Transcript Logging (Bonus)**: Full conversation transcripts and summaries stored upon call completion.

---

## Known Limitations & Trade-Offs

- **Demonstration Only**: Not HIPAA compliant; do not enter real Protected Health Information (PHI).
- **SQLite Storage**: Uses SQLite for zero-ops local persistence. For multi-instance cloud deployments, swap `DATABASE_URL` for PostgreSQL.
- **International Telecom Routing**: Dialing US numbers directly from cellular SIM cards outside the US requires international direct dialing (IDD). The embedded in-browser WebRTC dialer provides a seamless, zero-cost alternative.
