# Voice AI Patient Registration System

A voice-based AI agent that answers a real phone call, conversationally
registers a new patient, persists the record to a database, and exposes it
through a REST API and a simple web dashboard.

## Live Demo

- **Phone number:** +1 (863) 758 9028
- **API base URL:** https://web-production-6c593.up.railway.app
- **Interactive API docs (Swagger):** https://web-production-6c593.up.railway.app/docs
- **Dashboard:** https://web-production-6c593.up.railway.app/dashboard
- **Repository:** https://github.com/AhmedMemon-007/patient-registration-api

No credentials are required to test the API or dashboard — both are public,
read-friendly endpoints with server-side input validation on writes.

## Architecture

```
Caller (phone)
    │
    ▼
Vapi (telephony + STT + TTS + LLM)
    │  tool calls: find_patient_by_phone, create_patient, end_call_tool
    ▼
FastAPI REST API  (Railway, persistent volume)
    │
    ▼
SQLite database (patients.db)
```

The voice agent (built on Vapi) handles the phone call, speech-to-text,
text-to-speech, and conversation logic via an LLM. It calls two custom
tools that hit this project's own REST API to check for existing patients
and persist new registrations, plus a built-in tool to hang up the call
once registration is complete.

## Tech Stack & Why

- **Vapi** — handles telephony, STT/TTS, and phone number provisioning, so
  effort went into prompt engineering and backend integration rather than
  building voice infrastructure from scratch.
- **FastAPI** — fast to write, built-in request validation via Pydantic,
  matches the required JSON envelope (`{"data": ..., "error": ...}`) and
  proper HTTP status codes with minimal boilerplate.
- **SQLite** — zero-setup, file-based, persists via a mounted Railway
  volume. Sufficient for this scope; would migrate to Postgres for
  concurrent multi-caller production use.
- **Railway** — simple GitHub-connected deploys with persistent volumes,
  used to host the API and back it with a durable SQLite file.

## Data Model

All fields from the standard US patient demographic dataset are supported,
with server-side validation independent of whatever the voice agent
already checked (name format, DOB not in the future, valid US state, 10-digit
phone numbers, 5-digit/ZIP+4 zip codes, `sex` restricted to a fixed enum,
etc.). Optional fields left blank by the caller are correctly normalized
from empty strings to `null` server-side.

## REST API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/patients` | List all patients. Supports `?last_name=`, `?date_of_birth=`, `?phone_number=` |
| GET | `/patients/:id` | Retrieve a single patient by UUID |
| POST | `/patients` | Create a new patient |
| PUT | `/patients/:id` | Partial update of an existing patient |
| DELETE | `/patients/:id` | Soft-delete (sets `deleted_at`, does not hard-delete) |

All responses use the envelope `{ "data": ..., "error": ... }` with proper
HTTP status codes (200, 201, 404, 422, 500).

## Voice Agent Design

The system prompt (full text in `docs/system_prompt.txt` in this repo)
directs the agent to:

- Collect required fields conversationally, in natural groupings — never
  reading a form list.
- Check `find_patient_by_phone` early in the call and offer to update an
  existing record if the caller is a returning patient.
- Offer optional fields (insurance, emergency contact, preferred language)
  once, letting the caller opt in rather than asking about each one.
- Read back a full summary and get explicit confirmation before saving.
- Re-prompt for just the affected field on corrections or invalid input
  (e.g. an invalid date of birth), rather than restarting the whole call.
- Call `create_patient` only after confirmation, then use `end_call_tool`
  to hang up gracefully with a closing line.
- On a failed save, tell the caller plainly and offer a callback number or
  a retry, rather than leaving dead air.

## Setup (local development)

```bash
cd app
pip install -r ../requirements.txt
uvicorn main:app --reload --port 8000
```

Visit `http://127.0.0.1:8000/docs` to test the API locally. Note: locally,
`patients.db` is written next to the `app/` folder; on Railway it's written
to `/data/patients.db` on a mounted persistent volume (see `app/db.py`).

## Environment Variables

None are required to run the API itself. The Vapi assistant configuration
(system prompt, tools, phone number) is managed entirely in the Vapi
dashboard and is not part of this repository's runtime config.

## Known Limitations

- No HIPAA compliance (explicitly out of scope per the assessment brief;
  no real patient data is stored).
- SQLite is not safe for concurrent writes at scale — fine for a single
  phone line, would need Postgres for a real multi-line deployment.
- No retry/queue if the `create_patient` tool call fails mid-call; the
  agent surfaces the failure to the caller instead of silently dropping it.
- The dashboard is a minimal read-only table (no auth, no pagination) —
  intentionally simple given the assessment's time constraints.
- Insurance and emergency contact fields are stored as free text without
  additional format validation.

## Next Steps

- Migrate to Postgres for concurrent-safe production use.
- Store per-call transcripts linked to the patient record.
- Add multi-language support (the system prompt currently handles English
  conversations only).
- Add automated tests for the API layer (unit tests for validators, CRUD,
  and endpoint status codes).
- Add basic auth or an API key to the dashboard and write endpoints before
  any real deployment beyond this assessment.
