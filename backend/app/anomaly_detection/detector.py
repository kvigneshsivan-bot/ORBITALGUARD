from ..config import THRESHOLDS


def _anomaly(code, parameter, value, severity, threshold, comparison):
    return {"code": code, "parameter": parameter, "observed_value": value, "severity": severity, "threshold": threshold, "comparison": comparison}


def detect_anomalies(telemetry: dict) -> list[dict]:
    anomalies = []
    numeric_rules = (
        ("temperature", "HIGH_TEMPERATURE"), ("battery_soc", "LOW_BATTERY_SOC"),
        ("battery_voltage", "LOW_BATTERY_VOLTAGE"), ("solar_power", "LOW_SOLAR_POWER"),
        ("signal_strength", "WEAK_SIGNAL"), ("cpu_temperature", "HIGH_CPU_TEMPERATURE"),
        ("cpu_load", "HIGH_CPU_LOAD"), ("attitude_error", "ATTITUDE_ERROR"),
    )
    for parameter, code in numeric_rules:
        value = telemetry.get(parameter, 0)
        limits = THRESHOLDS[parameter]
        if parameter in ("battery_soc", "battery_voltage", "solar_power", "signal_strength"):
            if value < limits["critical"]: anomalies.append(_anomaly(code, parameter, value, "CRITICAL", limits["critical"], "below"))
            elif value < limits["warning"]: anomalies.append(_anomaly(code, parameter, value, "WARNING", limits["warning"], "below"))
        elif value > limits["critical"]:
            anomalies.append(_anomaly(code, parameter, value, "CRITICAL", limits["critical"], "above"))
        elif value > limits["warning"]:
            anomalies.append(_anomaly(code, parameter, value, "WARNING", limits["warning"], "above"))
    status = telemetry.get("communication_status", "NOMINAL")
    if status == "FAILED" or telemetry.get("signal_strength", 100) < THRESHOLDS["signal_strength"]["critical"]:
        anomalies.append(_anomaly("COMMUNICATION_FAILURE", "communication_status", status, "CRITICAL", "FAILED", "equals"))
    elif status == "DEGRADED" or telemetry.get("signal_strength", 100) < THRESHOLDS["signal_strength"]["warning"]:
        anomalies.append(_anomaly("COMMUNICATION_DEGRADED", "communication_status", status, "WARNING", "DEGRADED", "equals"))
    if telemetry.get("attitude_status") == "ABNORMAL" and not any(item["code"] == "ATTITUDE_ERROR" for item in anomalies):
        anomalies.append(_anomaly("ATTITUDE_ERROR", "attitude_status", "ABNORMAL", "CRITICAL", "NOMINAL", "not equals"))
    return anomalies