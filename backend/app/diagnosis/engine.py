from ..anomaly_detection import detect_anomalies
from ..health import calculate_health, status_for_score
from ..recovery import recommendation_for
from ..root_cause import explain_root_cause

FAULTS = {
    "HIGH_TEMPERATURE": ("Thermal Control Anomaly", "Thermal Control System"),
    "LOW_BATTERY_SOC": ("Low Battery SOC", "Electrical Power System (EPS)"),
    "LOW_BATTERY_VOLTAGE": ("Low Battery Voltage", "Electrical Power System (EPS)"),
    "LOW_SOLAR_POWER": ("Low Solar Power", "Electrical Power System (EPS)"),
    "WEAK_SIGNAL": ("Weak Communication Signal", "Communication System"),
    "COMMUNICATION_DEGRADED": ("Communication Link Degradation", "Communication System"),
    "COMMUNICATION_FAILURE": ("Communication Link Degradation", "Communication System"),
    "HIGH_CPU_TEMPERATURE": ("High CPU Temperature", "Onboard Computing System"),
    "HIGH_CPU_LOAD": ("High CPU Load", "Onboard Computing System"),
    "ATTITUDE_ERROR": ("Attitude Control Anomaly", "Attitude Determination and Control System (ADCS)"),
}


def diagnose(telemetry: dict) -> list[dict]:
    anomalies = detect_anomalies(telemetry)
    codes = {item["code"] for item in anomalies}
    if {"LOW_SOLAR_POWER", "LOW_BATTERY_SOC"} <= codes:
        anomalies.insert(0, {"code": "POWER_GENERATION_DEFICIENCY", "parameter": "battery_soc / solar_power", "observed_value": "combined", "severity": "CRITICAL", "threshold": "combined rule", "comparison": "combined"})
    result = []
    for anomaly in anomalies:
        fault, subsystem = FAULTS.get(anomaly["code"], ("Possible Power Generation Deficiency", "Electrical Power System (EPS)"))
        related = [item for item in anomalies if item["code"] != "POWER_GENERATION_DEFICIENCY"]
        result.append({
            "fault": fault,
            "fault_id": anomaly["code"],
            "severity": anomaly["severity"],
            "subsystem": subsystem,
            "parameter": anomaly["parameter"],
            "observed_value": anomaly["observed_value"],
            "threshold": anomaly["threshold"],
            "root_cause": explain_root_cause(related),
            "diagnostic_explanation": f"{anomaly['parameter']} observed at {anomaly['observed_value']}; configured threshold is {anomaly['comparison']} {anomaly['threshold']}.",
            "recovery": recommendation_for({item["code"] for item in related}),
        })
    return result


def health_score(faults: list[dict]) -> int:
    return calculate_health(faults)
