from datetime import datetime
from random import Random
from typing import Any

from .schema import TelemetryRecord

NORMAL_TELEMETRY = {
    "temperature": 28.0, "battery_soc": 82.0, "battery_voltage": 12.4,
    "battery_current": 2.8, "solar_power": 74.0, "signal_strength": 88.0,
    "cpu_temperature": 48.0, "cpu_load": 36.0, "attitude_error": 0.1,
    "attitude_status": "NOMINAL", "communication_status": "NOMINAL",
}

_NUMERIC_FIELDS = ("temperature", "battery_soc", "battery_voltage", "solar_power", "signal_strength", "cpu_temperature", "cpu_load", "attitude_error")


def make_telemetry(satellite_id: str, overrides: dict[str, Any] | None = None, seed: int | None = None) -> dict:
    values = NORMAL_TELEMETRY.copy()
    overrides = overrides or {}
    values.update(overrides)
    random = Random(seed)
    for field in _NUMERIC_FIELDS:
        if field not in overrides:
            spread = 0.08 if field == "attitude_error" else 1.5
            values[field] = round(values[field] + random.uniform(-spread, spread), 2)
    values.update({"satellite_id": satellite_id, "timestamp": datetime.utcnow()})
    return TelemetryRecord(**values).as_dict()