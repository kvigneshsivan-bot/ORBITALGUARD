def recommendation_for(anomaly_codes: set[str]) -> str:
    if {"LOW_SOLAR_POWER", "LOW_BATTERY_SOC", "LOW_BATTERY_VOLTAGE"} & anomaly_codes:
        return "Enter simulated power-saving mode and monitor solar generation and battery recovery."
    if "HIGH_TEMPERATURE" in anomaly_codes or "HIGH_CPU_TEMPERATURE" in anomaly_codes:
        return "Reduce non-essential processing load and monitor temperature trend."
    if "COMMUNICATION_FAILURE" in anomaly_codes:
        return "Attempt a simulated communication retry and monitor link quality."
    if "ATTITUDE_ERROR" in anomaly_codes:
        return "Verify attitude telemetry and initiate a simulated safe-mode recommendation."
    if "HIGH_CPU_LOAD" in anomaly_codes:
        return "Reduce non-essential processing and monitor CPU load."
    return "Inspect the affected telemetry parameter and continue monitoring."