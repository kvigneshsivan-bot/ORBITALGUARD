from pathlib import Path
import os

DATABASE_URL = f"sqlite:///{Path(__file__).resolve().parent.parent / 'satellite.db'}"
ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
TELEMETRY_MODE = os.getenv("TELEMETRY_MODE", "simulation").lower()
INGEST_API_KEY = os.getenv("INGEST_API_KEY", "")

THRESHOLDS = {
    "temperature": {"warning": 40, "critical": 60},
    "battery_soc": {"warning": 40, "critical": 20},
    "battery_voltage": {"warning": 11, "critical": 9},
    "solar_power": {"warning": 20, "critical": 10},
    "signal_strength": {"warning": 60, "critical": 30},
    "cpu_temperature": {"warning": 65, "critical": 80},
    "cpu_load": {"warning": 80, "critical": 95},
    "attitude_error": {"warning": 0.5, "critical": 2.0},
    "communication_status": {"warning": "DEGRADED", "critical": "FAILED"},
}
