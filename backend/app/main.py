import json
from datetime import datetime, timedelta
from typing import Any
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import Field
from sqlalchemy.orm import Session
from .config import ALLOWED_ORIGINS, INGEST_API_KEY, TELEMETRY_MODE
from .database import SessionLocal, init_db
from .diagnosis.engine import diagnose, health_score, status_for_score
from .telemetry.generator import make_telemetry as generate_telemetry
from .telemetry.schema import TelemetryRecord
from .models import Alert, Fault, Satellite, Telemetry

app = FastAPI(title="Satellite Fault Diagnosis API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

SIMULATION_OVERRIDES: dict[str, dict[str, Any]] = {}
ingest_key = APIKeyHeader(name="X-Ingest-Key", auto_error=False)

class TelemetryIngest(TelemetryRecord):
    pass

def db_session():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def to_dict(row):
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}

def make_telemetry(satellite_id: str):
    return generate_telemetry(satellite_id, SIMULATION_OVERRIDES.get(satellite_id))

def close_active_events(satellite_id: str, db: Session):
    db.query(Fault).filter(Fault.satellite_id == satellite_id, Fault.status == "OPEN").update({Fault.status: "RESOLVED"}, synchronize_session=False)
    db.query(Alert).filter(Alert.satellite_id == satellite_id, Alert.acknowledged.is_(False)).update({Alert.acknowledged: True}, synchronize_session=False)

def sync_active_events(satellite_id: str, telemetry: dict, faults: list[dict], db: Session):
    active_names = {fault["fault_id"] for fault in faults}
    open_faults = {}
    for existing in db.query(Fault).filter(Fault.satellite_id == satellite_id, Fault.status == "OPEN").order_by(Fault.timestamp.desc()).all():
        key = existing.fault_id or existing.fault
        if key in open_faults:
            existing.status = "RESOLVED"
        else:
            open_faults[key] = existing
    open_alerts = {}
    latest_alerts = {}
    for alert in db.query(Alert).filter(Alert.satellite_id == satellite_id).order_by(Alert.timestamp.desc()).all():
        key = alert.fault_id or alert.fault
        if key not in latest_alerts:
            latest_alerts[key] = alert
        if not alert.acknowledged:
            if key in open_alerts:
                alert.acknowledged = True
            else:
                open_alerts[key] = alert
    for existing in open_faults.values():
        if (existing.fault_id or existing.fault) not in active_names:
            existing.status = "RESOLVED"
    for alert in open_alerts.values():
        if (alert.fault_id or alert.fault) not in active_names:
            alert.acknowledged = True
    for fault in faults:
        existing_fault = open_faults.get(fault["fault_id"])
        if existing_fault:
            existing_fault.timestamp = telemetry["timestamp"]
            existing_fault.fault_id = fault["fault_id"]
            existing_fault.severity = fault["severity"]
            existing_fault.detected_parameters = fault["parameter"]
            existing_fault.observed_values = json.dumps(fault["observed_value"])
            existing_fault.thresholds = json.dumps(fault["threshold"])
            existing_fault.root_cause = fault["root_cause"]
            existing_fault.diagnostic_explanation = fault["diagnostic_explanation"]
            existing_fault.recovery = fault["recovery"]
        else:
            db.add(Fault(satellite_id=satellite_id, fault=fault["fault"], fault_id=fault["fault_id"], severity=fault["severity"], subsystem=fault["subsystem"], detected_parameters=fault["parameter"], observed_values=json.dumps(fault["observed_value"]), thresholds=json.dumps(fault["threshold"]), root_cause=fault["root_cause"], diagnostic_explanation=fault["diagnostic_explanation"], recovery=fault["recovery"], status="OPEN", timestamp=telemetry["timestamp"]))
        existing_alert = open_alerts.get(fault["fault_id"]) or (latest_alerts.get(fault["fault_id"]) if existing_fault else None)
        if existing_alert:
            existing_alert.timestamp = telemetry["timestamp"]
            existing_alert.fault_id = fault["fault_id"]
            existing_alert.severity = fault["severity"]
            existing_alert.description = fault["root_cause"]
            existing_alert.recommended_action = fault["recovery"]
        else:
            db.add(Alert(satellite_id=satellite_id, fault=fault["fault"], fault_id=fault["fault_id"], severity=fault["severity"], description=fault["root_cause"], recommended_action=fault["recovery"], acknowledged=False, timestamp=telemetry["timestamp"]))

def apply_current_state(satellite_id: str, telemetry: dict, faults: list[dict], db: Session):
    score = health_score(faults)
    satellite = db.get(Satellite, satellite_id)
    satellite.health_score, satellite.status, satellite.last_update = score, status_for_score(score), telemetry["timestamp"]
    sync_active_events(satellite_id, telemetry, faults, db)

def store_analysis(satellite_id: str, telemetry: dict, db: Session):
    db.add(Telemetry(**telemetry))
    faults = diagnose(telemetry)
    score = health_score(faults)
    apply_current_state(satellite_id, telemetry, faults, db)
    db.commit()
    return faults, score

def refresh(satellite_id: str, db: Session):
    telemetry = make_telemetry(satellite_id)
    faults, score = store_analysis(satellite_id, telemetry, db)
    return telemetry, faults, score

def process_ingested_telemetry(payload: TelemetryIngest, db: Session):
    satellite = db.get(Satellite, payload.satellite_id)
    if not satellite:
        raise HTTPException(404, "Satellite not found")
    telemetry = payload.model_dump()
    telemetry["timestamp"] = payload.timestamp or datetime.utcnow()
    faults, score = store_analysis(payload.satellite_id, telemetry, db)
    return {**telemetry, "faults": faults, "health_score": score, "source": "ingested"}

def seed():
    init_db()
    db = SessionLocal()
    if db.query(Satellite).count() == 0:
        satellites = [("SAT-01", "Asteria-01", "Earth observation", "Sun-synchronous"), ("SAT-02", "Asteria-02", "Climate research", "Low Earth orbit"), ("SAT-03", "Asteria-03", "Technology demonstrator", "Low Earth orbit")]
        for sid, name, mission, orbit in satellites: db.add(Satellite(id=sid, name=name, mission_type=mission, orbit_type=orbit))
        db.commit()
    if TELEMETRY_MODE != "live" and db.query(Telemetry).count() == 0:
        for sid in ("SAT-01", "SAT-02", "SAT-03"):
            for offset in range(12, 0, -1):
                values = make_telemetry(sid); values["timestamp"] = datetime.utcnow() - timedelta(minutes=offset * 5); db.add(Telemetry(**values))
        db.commit()
    for satellite in db.query(Satellite).all():
        latest = db.query(Telemetry).filter(Telemetry.satellite_id == satellite.id).order_by(Telemetry.timestamp.desc()).first()
        if latest:
            telemetry = to_dict(latest)
            apply_current_state(satellite.id, telemetry, diagnose(telemetry), db)
    db.commit()
    db.close()

@app.on_event("startup")
def startup(): seed()

@app.get("/api/satellites")
def satellites(db: Session = Depends(db_session)): return [to_dict(x) for x in db.query(Satellite).all()]

@app.get("/api/satellites/{satellite_id}")
def satellite(satellite_id: str, db: Session = Depends(db_session)):
    item = db.get(Satellite, satellite_id)
    if not item: raise HTTPException(404, "Satellite not found")
    return to_dict(item)

@app.get("/api/telemetry/{satellite_id}")
def current_telemetry(satellite_id: str, db: Session = Depends(db_session)):
    if not db.get(Satellite, satellite_id): raise HTTPException(404, "Satellite not found")
    if TELEMETRY_MODE == "live":
        row = db.query(Telemetry).filter(Telemetry.satellite_id == satellite_id).order_by(Telemetry.timestamp.desc()).first()
        if not row:
            raise HTTPException(503, "No telemetry has been ingested for this satellite")
        telemetry = to_dict(row)
        faults = diagnose(telemetry)
        return {**telemetry, "faults": faults, "health_score": health_score(faults), "source": "ingested"}
    row = db.query(Telemetry).filter(Telemetry.satellite_id == satellite_id).order_by(Telemetry.timestamp.desc()).first()
    if not row:
        telemetry, faults, score = refresh(satellite_id, db)
        return {**telemetry, "faults": faults, "health_score": score}
    telemetry = to_dict(row)
    faults = diagnose(telemetry)
    return {**telemetry, "faults": faults, "health_score": health_score(faults), "source": "simulation"}

@app.get("/api/telemetry/{satellite_id}/history")
def telemetry_history(satellite_id: str, db: Session = Depends(db_session)):
    rows = db.query(Telemetry).filter(Telemetry.satellite_id == satellite_id).order_by(Telemetry.timestamp.desc()).limit(30).all()
    return [to_dict(x) for x in reversed(rows)]

@app.post("/api/telemetry/ingest", status_code=201)
def ingest_telemetry(payload: TelemetryIngest, db: Session = Depends(db_session), api_key: str | None = Depends(ingest_key)):
    if INGEST_API_KEY and api_key != INGEST_API_KEY:
        raise HTTPException(401, "Invalid telemetry ingestion key")
    return process_ingested_telemetry(payload, db)

@app.get("/api/faults")
def faults(db: Session = Depends(db_session)): return [to_dict(x) for x in db.query(Fault).order_by(Fault.timestamp.desc()).limit(100).all()]

@app.get("/api/alerts")
def alerts(db: Session = Depends(db_session)): return [to_dict(x) for x in db.query(Alert).order_by(Alert.timestamp.desc()).limit(50).all()]

@app.patch("/api/alerts/{alert_id}/acknowledge")
def acknowledge(alert_id: int, db: Session = Depends(db_session)):
    alert = db.get(Alert, alert_id)
    if not alert: raise HTTPException(404, "Alert not found")
    alert.acknowledged = True; db.commit(); return to_dict(alert)

@app.get("/api/health/{satellite_id}")
def health(satellite_id: str, db: Session = Depends(db_session)):
    satellite = db.get(Satellite, satellite_id)
    if not satellite: raise HTTPException(404, "Satellite not found")
    return {"satellite_id": satellite_id, "health_score": satellite.health_score, "status": satellite.status}

@app.get("/api/analytics")
def analytics(db: Session = Depends(db_session)):
    rows = db.query(Fault).all(); active_rows = [row for row in rows if row.status == "OPEN"]; critical = sum(x.severity == "CRITICAL" for x in active_rows); warning = sum(x.severity == "WARNING" for x in active_rows); resolved = sum(x.status == "RESOLVED" for x in rows)
    subsystems = {}; [subsystems.__setitem__(x.subsystem, subsystems.get(x.subsystem, 0) + 1) for x in rows]
    average = db.query(Satellite).all(); avg_health = round(sum(x.health_score for x in average) / len(average), 1) if average else 100
    return {"fault_count": len(rows), "active_count": len(active_rows), "critical_count": critical, "warning_count": warning, "resolved_count": resolved, "average_health": avg_health, "most_affected_subsystem": max(subsystems, key=subsystems.get) if subsystems else "None", "frequency": [{"name": k, "count": v} for k, v in subsystems.items()]}

@app.get("/api/state")
def state(satellite_id: str = "SAT-03", db: Session = Depends(db_session)):
    satellite_rows = db.query(Satellite).all()
    selected_id = satellite_id if any(row.id == satellite_id for row in satellite_rows) else (satellite_rows[0].id if satellite_rows else "SAT-03")
    telemetry = db.query(Telemetry).filter(Telemetry.satellite_id == selected_id).order_by(Telemetry.timestamp.desc()).first()
    history_rows = db.query(Telemetry).filter(Telemetry.satellite_id == selected_id).order_by(Telemetry.timestamp.desc()).limit(30).all()
    analytics_data = analytics(db)
    return {"satellites": [to_dict(row) for row in satellite_rows], "telemetry": to_dict(telemetry) if telemetry else None, "history": [to_dict(row) for row in reversed(history_rows)], "faults": [to_dict(row) for row in db.query(Fault).order_by(Fault.timestamp.desc()).limit(100).all()], "alerts": [to_dict(row) for row in db.query(Alert).order_by(Alert.timestamp.desc()).limit(50).all()], "analytics": analytics_data, "source": source_status()}

@app.post("/api/simulation/{scenario}")
def simulation(scenario: str, satellite_id: str = "SAT-03", db: Session = Depends(db_session)):
    overrides = {"overheating": {"temperature": 68, "cpu_temperature": 84}, "low-battery": {"battery_soc": 18, "battery_voltage": 8.6}, "solar-failure": {"solar_power": 6, "battery_soc": 24}, "communication-failure": {"signal_strength": 18, "communication_status": "FAILED"}, "attitude-error": {"attitude_status": "ABNORMAL"}, "multiple-fault": {"temperature": 68, "cpu_temperature": 84, "battery_soc": 18, "battery_voltage": 8.6, "solar_power": 6, "signal_strength": 18, "communication_status": "FAILED", "attitude_status": "ABNORMAL"}}
    if not db.get(Satellite, satellite_id): raise HTTPException(404, "Satellite not found")
    if scenario == "reset": SIMULATION_OVERRIDES.pop(satellite_id, None)
    elif scenario in overrides: SIMULATION_OVERRIDES[satellite_id] = overrides[scenario]
    else: raise HTTPException(400, "Unknown simulation scenario")
    telemetry, faults, score = refresh(satellite_id, db)
    return {"message": "Simulation applied", "telemetry": telemetry, "faults": faults, "health_score": score}

@app.get("/api/source")
def source_status():
    return {"mode": TELEMETRY_MODE, "simulated": TELEMETRY_MODE != "live", "ingestion_endpoint": "/api/telemetry/ingest"}

@app.get("/api/health")
def api_health(): return {"status": "ok", "simulation": TELEMETRY_MODE != "live", "telemetry_mode": TELEMETRY_MODE}
