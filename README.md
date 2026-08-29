# Patient Registration API

A small REST API for registering, looking up, updating, and soft-deleting patient
records, built with **FastAPI**, **Pydantic**, and **SQLite**.

---

## Features

- Create, read, update, and soft-delete patient records
- Field-level validation (name format, DOB, US phone numbers, US state codes,
  ZIP codes, allowed `sex` values, email format)
- Consistent `{ "data": ..., "error": ... }` response envelope on every endpoint
- Duplicate-registration guard (rejects a new patient if the phone number is
  already registered)
- Soft delete — records are flagged with `deleted_at` rather than removed, so
  history is preserved
- SQLite storage with no external database server required

---

## Tech Stack

| Layer | Tool |
|---|---|
| Web framework | [FastAPI](https://fastapi.tiangolo.com/) |
| Server | [Uvicorn](https://www.uvicorn.org/) |
| Validation | [Pydantic v2](https://docs.pydantic.dev/) (+ `email-validator`) |
| Database | SQLite (via the standard library `sqlite3`) |

---

## Project Structure

```
C_cloud/
├── myenv/                 # virtual environment (not committed)
├── patients.db            # SQLite database file (created on first run)
└── app/
    ├── main.py             # FastAPI app + route definitions
    ├── models.py           # Pydantic request/response models & validation
    ├── crud.py              # Database read/write functions
    ├── db.py                 # SQLite connection + schema initialization
    ├── schema.sql            # Table definition
    ├── requirements.txt      # Python dependencies
    └── README.md
```

> `patients.db` is created one directory **above** `app/`, at the project root
> (`C_cloud/patients.db`), the first time the app starts — see `db.py`.

---

## Setup

### 1. Create and activate a virtual environment

Create it at the **project root** (`C_cloud/`), not inside `app/`:

```powershell
cd C:\Users\Admin\Desktop\C_cloud
python -m venv myenv
myenv\Scripts\activate
```

### 2. Install dependencies

```powershell
cd app
pip install -r requirements.txt
```

### 3. Run the server

From inside the `app/` folder:

```powershell
uvicorn main:app --reload
```

The API will be available at:

- **Base URL:** http://127.0.0.1:8000
- **Interactive docs (Swagger UI):** http://127.0.0.1:8000/docs
- **Alternative docs (ReDoc):** http://127.0.0.1:8000/redoc

> The database and its table are created automatically on startup
> (`init_db()` runs `schema.sql` on the `startup` event) — no manual
> migration step is needed.

---

## API Reference

All responses are wrapped in an envelope:

```json
{ "data": ..., "error": ... }
```

Exactly one of `data` / `error` will be non-null.

### `GET /patients`

List patients, optionally filtered.

**Query parameters** (all optional):

| Param | Type |
|---|---|
| `last_name` | string |
| `date_of_birth` | string (`YYYY-MM-DD`) |
| `phone_number` | string |

```bash
curl "http://127.0.0.1:8000/patients?last_name=Smith"
```

### `GET /patients/{patient_id}`

Fetch a single patient by ID. Returns `404` if not found or soft-deleted.

```bash
curl "http://127.0.0.1:8000/patients/<patient_id>"
```

### `POST /patients`

Create a new patient. Returns `201` on success, `422` on validation error,
`409` if the phone number is already registered.

**Required fields:** `first_name`, `last_name`, `date_of_birth`, `sex`,
`phone_number`, `address_line_1`, `city`, `state`, `zip_code`

**Optional fields:** `email`, `address_line_2`, `insurance_provider`,
`insurance_member_id`, `preferred_language` (default `"English"`),
`emergency_contact_name`, `emergency_contact_phone`

```bash
curl -X POST "http://127.0.0.1:8000/patients" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Doe",
    "date_of_birth": "1990-05-14",
    "sex": "Female",
    "phone_number": "555-123-4567",
    "address_line_1": "123 Main St",
    "city": "Springfield",
    "state": "IL",
    "zip_code": "62704"
  }'
```

### `PUT /patients/{patient_id}`

Partially update a patient. Only send the fields you want to change. Same
validation rules as `POST`. Returns `404` if the patient doesn't exist.

```bash
curl -X PUT "http://127.0.0.1:8000/patients/<patient_id>" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "555-999-8888"}'
```

### `DELETE /patients/{patient_id}`

Soft-deletes a patient (sets `deleted_at`; the row is kept, not removed).
Returns `404` if the patient doesn't exist or is already deleted.

```bash
curl -X DELETE "http://127.0.0.1:8000/patients/<patient_id>"
```

---

## Validation Rules

| Field | Rule |
|---|---|
| `first_name`, `last_name` | 1–50 letters, spaces, hyphens, or apostrophes |
| `date_of_birth` | Cannot be in the future |
| `sex` | One of `Male`, `Female`, `Other`, `Decline to Answer` |
| `phone_number`, `emergency_contact_phone` | Must contain exactly 10 digits (formatting characters are stripped automatically) |
| `state` | Valid 2-letter US state/DC abbreviation |
| `zip_code` | 5-digit or ZIP+4 format (`12345` or `12345-6789`) |
| `email` | Valid email format |

---

## Known Limitations

- **No authentication.** Every endpoint is open, including ones that return
  full patient PII. Do not deploy this beyond local development without
  adding an auth layer (API key, OAuth, etc.).
- **SQLite only.** Fine for local dev/small deployments; a concurrent
  multi-user production setup would need a proper server-backed database
  (e.g. PostgreSQL).
- **No `UNIQUE` constraint on `phone_number` at the database level** — the
  duplicate check happens in the application layer only.

---

## License

Internal / educational project — no license specified.
