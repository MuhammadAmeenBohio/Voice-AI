# Reviewer Instructions — Voice AI Patient Intake System

**System:** Muhammad Autonomous Patient Intake Coordinator  
**Stack:** FastAPI, SQLModel, SQLite, Vapi Voice AI (Deepgram + GPT-4o-mini + ElevenLabs)  
**Package Manager:** `uv`

---

## 1. Quick Local Launch

```powershell
# 1. Activate environment
.venv\Scripts\activate

# 2. Run automated test suite
uv run pytest -v

# 3. Start server
uv run uvicorn main:app --reload --port 8000
```

Once started:
- **Interactive Dashboard:** [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- **API Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Service Liveness:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 2. Testing the Voice Agent

### Option A: In-Browser Web Voice Calling (Direct & Zero Telephony Fees)
1. Open [http://localhost:8000/dashboard](http://localhost:8000/dashboard).
2. Click **"Start Voice Call"**.
3. Allow browser microphone access and speak naturally with Muhammad.

### Option B: Local Webhook Simulator (Instant Validation)
To simulate the complete conversational intake flow, data validation, and database write without using any Vapi credits:
```powershell
uv run python voice_agent/simulate_call.py
```

### Option C: PSTN Phone Dial-in
If testing via telephone:
- Dial the provisioned number: **`+1 (724) 304-6263`**
- *(Note: If calling from outside the US, use a VoIP dialer like Skype, Google Voice, or TextNow, or use Option A above).*

---

## 3. Recommended Test Scenarios

### Scenario 1: New Patient Intake
- **Spoken Name:** Alex Taylor
- **Date of Birth:** April 12, 1992
- **Sex:** Male
- **Phone Number:** 555-888-9999
- **Address:** 100 Main Street, Austin, TX 78701
- **Optional Info:** Opt-in to provide Blue Cross insurance with ID `BC-9922`
- **Confirmation:** Listen to Muhammad read back all fields, say *"Yes, that's correct"*, and verify the record appears in `GET /patients` and on the dashboard.

### Scenario 2: Returning Patient Duplicate Detection (Bonus)
- Provide existing phone number: `5551234567` (matching seeded patient Jane Doe).
- Muhammad will detect the record and ask: *"It looks like we already have a record for Jane Doe. Would you like to update your information instead?"*

### Scenario 3: In-Flight Error Correction & Validation
- **Invalid Phone:** Say *"My phone number is 123"* -> Muhammad re-prompts specifically for a 10-digit number.
- **Future DOB:** Say *"I was born in 2099"* -> Muhammad notes the date is in the future and asks for the correct birth year.
- **Spelling Correction:** Say *"Actually, my name is spelled T-A-Y-L-O-R"* -> Muhammad updates the spelling and re-confirms.

---

## 4. REST API Verification

```bash
# List all active patients
curl http://localhost:8000/patients

# Filter by last name
curl "http://localhost:8000/patients?last_name=Doe"

# View call transcripts and summaries
curl http://localhost:8000/calls
```
