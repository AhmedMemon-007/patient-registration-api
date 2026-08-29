import uuid
from datetime import datetime, timezone
from db import get_db

# Columns in schema.sql that do NOT have a NOT NULL constraint.
# On update, an explicit `null` from the client is only honored for
# these -- otherwise it's silently dropped (matches original behavior
# and avoids an uncaught sqlite3.IntegrityError on required columns).
NULLABLE_FIELDS = {
    "email",
    "address_line_2",
    "insurance_provider",
    "insurance_member_id",
    "preferred_language",
    "emergency_contact_name",
    "emergency_contact_phone",
}


def now():
    return datetime.now(timezone.utc).isoformat()


def create_patient(data: dict):
    conn = get_db()
    try:
        pid = str(uuid.uuid4())
        ts = now()
        fields = {**data, "patient_id": pid, "created_at": ts, "updated_at": ts}
        fields["date_of_birth"] = str(fields["date_of_birth"])
        cols = ", ".join(fields.keys())
        placeholders = ", ".join("?" * len(fields))
        conn.execute(f"INSERT INTO patients ({cols}) VALUES ({placeholders})", list(fields.values()))
        conn.commit()
        row = conn.execute("SELECT * FROM patients WHERE patient_id=?", (pid,)).fetchone()
        return dict(row)
    finally:
        conn.close()


def get_patient(patient_id: str):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM patients WHERE patient_id=? AND deleted_at IS NULL", (patient_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def find_by_phone(phone_number: str):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM patients WHERE phone_number=? AND deleted_at IS NULL", (phone_number,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_patients(filters: dict):
    conn = get_db()
    try:
        query = "SELECT * FROM patients WHERE deleted_at IS NULL"
        params = []
        for key in ("last_name", "date_of_birth", "phone_number"):
            if filters.get(key):
                query += f" AND {key} = ?"
                params.append(filters[key])
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_patient(patient_id: str, data: dict):
    conn = get_db()
    try:
        existing = get_patient(patient_id)
        if not existing:
            return None

        # Keep every non-null value, PLUS explicit nulls for columns
        # that are actually allowed to be null in the schema (so a
        # client can clear e.g. email or insurance_provider). Explicit
        # nulls for required columns (first_name, state, etc.) are
        # dropped rather than sent to the DB, which would otherwise
        # raise an uncaught IntegrityError.
        data = {
            k: v for k, v in data.items()
            if v is not None or k in NULLABLE_FIELDS
        }

        if not data:
            return existing

        if "date_of_birth" in data and data["date_of_birth"] is not None:
            data["date_of_birth"] = str(data["date_of_birth"])
        data["updated_at"] = now()

        set_clause = ", ".join(f"{k}=?" for k in data.keys())
        conn.execute(
            f"UPDATE patients SET {set_clause} WHERE patient_id=?",
            list(data.values()) + [patient_id],
        )
        conn.commit()
        row = conn.execute("SELECT * FROM patients WHERE patient_id=?", (patient_id,)).fetchone()
        return dict(row)
    finally:
        conn.close()


def soft_delete_patient(patient_id: str):
    conn = get_db()
    try:
        existing = get_patient(patient_id)
        if not existing:
            return False
        conn.execute(
            "UPDATE patients SET deleted_at=? WHERE patient_id=?", (now(), patient_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()