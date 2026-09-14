# Satellite Fault Diagnosis & Recovery Recommendation System

An academic aerospace software prototype that monitors simulated satellite telemetry, detects threshold violations, explains probable faults, scores satellite health, and presents recovery recommendations in a ground-station-style console.

> This application uses simulated data only. It is not connected to a real satellite and its recovery recommendations must not be used to control a spacecraft.

## Problem statement
Operators need a clear way to turn raw telemetry into explainable fault information. This project separates telemetry generation, validation, diagnosis, health scoring, alerting, and presentation so a real telemetry adapter can be added later.

## Objectives
- Monitor realistic simulated telemetry for SAT-01, SAT-02, and SAT-03.
- Detect abnormal conditions using configurable thresholds.
- Identify the affected subsystem and probable root cause.
- Recommend software-level recovery actions for academic demonstration.
- Preserve telemetry, faults, and alerts in SQLite for history and analytics.

## Architecture
`Telemetry dataset/generator -> schema validation -> anomaly detection -> fault classification -> root cause -> health -> alert/recovery -> SQLite -> React operator console`

The diagnosis engine is deterministic and explainable. It does not claim to use AI predictions.

## Features
- Fleet dashboard with health scores and status counts.
- Live polling every five seconds.
- Temperature trend chart with Recharts.
- Telemetry detail view, fault history, alert acknowledgement, and analytics.
- Controlled overheating, battery, solar, communication, attitude, and multiple-fault simulations.
- SQLite database initialized automatically on backend startup.
- Structured telemetry dataset at `backend/data/telemetry_dataset.json` with normal and abnormal records.
- Explainable anomaly records containing parameter, observed value, threshold, and severity.

## Technology stack
- Frontend: React, Vite, JavaScript, CSS, Recharts.
- Backend: Python, FastAPI, Uvicorn.
- Database: SQLite and SQLAlchemy.

## Folder structure
```text
frontend/
  src/
    components/ pages/ data/ services/ hooks/ utils/
    App.jsx main.jsx index.css
  package.json vite.config.js
backend/
  app/
    main.py database.py models.py config.py
    diagnosis/engine.py
  requirements.txt
README.md
```

## Installation and run
### Backend
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` to use the complete console. During development, Vite proxies `/api` requests to the FastAPI server on port `8000`, so the browser uses one URL. Set `VITE_API_URL` only when using another API origin.

## API overview
- `GET /api/satellites`
- `GET /api/satellites/{satellite_id}`
- `GET /api/telemetry/{satellite_id}`
- `GET /api/telemetry/{satellite_id}/history`
- `GET /api/faults`
- `GET /api/alerts`
- `PATCH /api/alerts/{alert_id}/acknowledge`
- `GET /api/analytics`
- `GET /api/health/{satellite_id}`
- `POST /api/telemetry/ingest`
- `GET /api/source`
- `POST /api/simulation/{scenario}` where scenario is `overheating`, `low-battery`, `solar-failure`, `communication-failure`, `attitude-error`, `multiple-fault`, or `reset`.

## Real telemetry integration
The default `TELEMETRY_MODE=simulation` keeps the academic demo self-contained. Set `TELEMETRY_MODE=live` when a ground-station adapter is ready. In live mode, the backend never generates random telemetry and waits for records at `POST /api/telemetry/ingest`. Set `INGEST_API_KEY` and send it as the `X-Ingest-Key` header in deployed environments.

Example PowerShell request:
```powershell
$body = @{ satellite_id = "SAT-01"; temperature = 31.2; battery_soc = 78; battery_voltage = 12.3; battery_current = 2.7; solar_power = 70; signal_strength = 86; cpu_temperature = 49; cpu_load = 41; attitude_status = "NOMINAL"; communication_status = "NOMINAL" } | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/api/telemetry/ingest -Method Post -ContentType "application/json" -Headers @{ "X-Ingest-Key" = "your-configured-key" } -Body $body
```

## Telemetry processing pipeline
Thresholds are centralized in `backend/app/config.py`. The modular pipeline is split into:

- `backend/app/telemetry/`: validated telemetry schema and realistic deterministic generator.
- `backend/app/anomaly_detection/`: threshold comparisons that emit structured anomaly records.
- `backend/app/diagnosis/`: anomaly-to-subsystem fault classification.
- `backend/app/root_cause.py`: explainable rule-based root-cause analysis.
- `backend/app/recovery.py`: academic/software recovery recommendations.
- `backend/app/health.py`: centralized health score and status bands.

The diagnosis engine checks temperature, battery SOC, voltage, solar power, signal strength, CPU temperature/load, attitude error/status, and communication status. Combined conditions produce higher-level diagnoses such as Possible Power Generation Deficiency. The system does not claim to use AI or machine learning.

Health starts at 100. Warning faults subtract 10 points and critical faults subtract 25 points. The score is cumulative and clamped to 0-100. Status bands are NORMAL (90-100), WARNING (70-89), DEGRADED (40-69), and CRITICAL (0-39).

## Recovery recommendation concept
Recommendations are explanatory software outputs such as entering a simulated power-saving mode, reducing non-essential processing, retrying communication, or checking attitude telemetry. They are not real spacecraft commands.

## Limitations and future enhancements
This project does not include a real spacecraft connection or command link. A mission-specific ground-station adapter, authentication, operator roles, WebSocket streaming, migrations, audit logs, and hardware-in-the-loop validation are still required before operational deployment.
