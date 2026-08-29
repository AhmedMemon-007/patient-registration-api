from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
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

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD_HTML

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Patient Registration Dashboard</title>
<style>
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; background: #0f1117; color: #e6e6e6; margin: 0; padding: 40px; }
  h1 { font-size: 22px; margin-bottom: 4px; }
  p.sub { color: #9aa0a6; margin-top: 0; margin-bottom: 24px; }
  table { width: 100%; border-collapse: collapse; background: #171a21; border-radius: 8px; overflow: hidden; }
  th, td { text-align: left; padding: 10px 14px; font-size: 14px; border-bottom: 1px solid #2a2e38; }
  th { background: #1f232c; color: #9aa0a6; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px; }
  tr:hover { background: #1c2029; }
  .empty { padding: 40px; text-align: center; color: #9aa0a6; }
  .refresh { background: #2563eb; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; }
  .refresh:hover { background: #1d4ed8; }
  .top { display: flex; justify-content: space-between; align-items: center; }
</style>
</head>
<body>
  <div class="top">
    <div>
      <h1>Patient Registration Dashboard</h1>
      <p class="sub">Live records from the Patient Registration API</p>
    </div>
    <button class="refresh" onclick="loadPatients()">Refresh</button>
  </div>
  <div id="content">Loading...</div>

<script>
async function loadPatients() {
  const content = document.getElementById('content');
  content.innerHTML = 'Loading...';
  try {
    const res = await fetch('/patients');
    const json = await res.json();
    const patients = json.data || [];
    if (patients.length === 0) {
      content.innerHTML = '<div class="empty">No patients registered yet.</div>';
      return;
    }
    let rows = patients.map(p => `
      <tr>
        <td>${p.first_name} ${p.last_name}</td>
        <td>${p.date_of_birth}</td>
        <td>${p.sex}</td>
        <td>${p.phone_number}</td>
        <td>${p.city}, ${p.state} ${p.zip_code}</td>
        <td>${new Date(p.created_at).toLocaleString()}</td>
      </tr>
    `).join('');
    content.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Name</th><th>DOB</th><th>Sex</th><th>Phone</th><th>Location</th><th>Registered</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  } catch (e) {
    content.innerHTML = '<div class="empty">Failed to load patients.</div>';
  }
}
loadPatients();
</script>
</body>
</html>
"""