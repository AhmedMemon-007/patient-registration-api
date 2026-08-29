from fastapi import FastAPI, HTTPException
import logging

from db import init_db
from models import PatientCreate, PatientUpdate
import crud

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("patient-api")

app = FastAPI(title="Patient Registration API")

@app.on_event("startup")
def startup():
    init_db()

def envelope(data=None, error=None):
    return {"data": data, "error": error}

@app.get("/patients")
def list_patients_endpoint(last_name: str = None, date_of_birth: str = None, phone_number: str = None):
    filters = {"last_name": last_name, "date_of_birth": date_of_birth, "phone_number": phone_number}
    results = crud.list_patients(filters)
    return envelope(data=results)

@app.get("/patients/{patient_id}")
def get_patient_endpoint(patient_id: str):
    patient = crud.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=envelope(error="Patient not found"))
    return envelope(data=patient)

@app.post("/patients", status_code=201)
def create_patient_endpoint(payload: PatientCreate):
    try:
        created = crud.create_patient(payload.model_dump())
        logger.info(f"Patient created: {created['patient_id']} - {created['first_name']} {created['last_name']}")
        return envelope(data=created)
    except Exception as e:
        logger.error(f"DB write failed: {e}")
        raise HTTPException(status_code=500, detail=envelope(error="Failed to save patient record"))

@app.put("/patients/{patient_id}")
def update_patient_endpoint(patient_id: str, payload: PatientUpdate):
    updated = crud.update_patient(patient_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail=envelope(error="Patient not found"))
    return envelope(data=updated)

@app.delete("/patients/{patient_id}")
def delete_patient_endpoint(patient_id: str):
    success = crud.soft_delete_patient(patient_id)
    if not success:
        raise HTTPException(status_code=404, detail=envelope(error="Patient not found"))
    return envelope(data={"patient_id": patient_id, "deleted": True})