def explain_root_cause(anomalies: list[dict]) -> str:
    codes = {item["code"] for item in anomalies}
    if {"LOW_SOLAR_POWER", "LOW_BATTERY_SOC", "LOW_BATTERY_VOLTAGE"} <= codes:
        return "Insufficient solar power generation is reducing battery charging and declining battery voltage."
    if {"HIGH_CPU_TEMPERATURE", "HIGH_CPU_LOAD"} <= codes:
        return "Excessive onboard processing load may be causing thermal stress in the onboard computing subsystem."
    causes = {
        "HIGH_TEMPERATURE": "Spacecraft temperature is above the thermal operating limit.",
        "HIGH_CPU_TEMPERATURE": "Onboard processor temperature is above the expected operating range.",
        "LOW_BATTERY_SOC": "Battery charge is below the required operating margin.",
        "LOW_BATTERY_VOLTAGE": "Battery voltage is below the expected power-system range.",
        "LOW_SOLAR_POWER": "Solar generation is below the expected charging range.",
        "COMMUNICATION_FAILURE": "The communication link has failed or signal strength is critically low.",
        "ATTITUDE_ERROR": "Satellite attitude error is outside the acceptable pointing range.",
        "HIGH_CPU_LOAD": "Processor utilization may delay non-essential onboard tasks.",
    }
    return causes.get(next(iter(codes), ""), "Telemetry parameter is outside its configured operating range.")