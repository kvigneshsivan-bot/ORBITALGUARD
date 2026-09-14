import json
import unittest
from pathlib import Path

from app.anomaly_detection import detect_anomalies
from app.diagnosis.engine import diagnose, health_score
from app.health import status_for_score
from app.telemetry.schema import TelemetryRecord


BASE = {
    "satellite_id": "SAT-TEST", "temperature": 28, "battery_soc": 82,
    "battery_voltage": 12.4, "battery_current": 2.8, "solar_power": 74,
    "signal_strength": 88, "cpu_temperature": 48, "cpu_load": 36,
    "attitude_error": 0.1, "attitude_status": "NOMINAL", "communication_status": "NOMINAL",
}


def telemetry(**changes):
    values = {**BASE, **changes}
    return TelemetryRecord(**values).as_dict()


class PipelineTests(unittest.TestCase):
    def test_dataset_records_validate_and_include_required_fields(self):
        dataset_path = Path(__file__).parents[1] / "data" / "telemetry_dataset.json"
        records = json.loads(dataset_path.read_text(encoding="utf-8"))
        required = set(BASE) | {"timestamp"}
        self.assertGreaterEqual(len(records), 3)
        for record in records:
            self.assertTrue(required <= record.keys())
            self.assertEqual(TelemetryRecord(**record).satellite_id, record["satellite_id"])

    def test_normal_telemetry_has_no_anomalies(self):
        self.assertEqual(detect_anomalies(telemetry()), [])
        self.assertEqual(diagnose(telemetry()), [])
        self.assertEqual(health_score([]), 100)

    def test_high_temperature_is_thermal_critical(self):
        result = diagnose(telemetry(temperature=72))
        self.assertEqual(result[0]["fault"], "Thermal Control Anomaly")
        self.assertEqual(result[0]["subsystem"], "Thermal Control System")
        self.assertEqual(result[0]["severity"], "CRITICAL")
        self.assertIn("temperature", result[0]["diagnostic_explanation"])
        self.assertEqual(status_for_score(health_score(result)), "WARNING")

    def test_power_combination_has_explainable_root_cause(self):
        result = diagnose(telemetry(battery_soc=18, battery_voltage=8.6, solar_power=6))
        faults = {item["fault"] for item in result}
        self.assertIn("Possible Power Generation Deficiency", faults)
        self.assertIn("Low Battery SOC", faults)
        self.assertIn("Electrical Power System (EPS)", {item["subsystem"] for item in result})
        self.assertTrue(all(item["root_cause"] and item["recovery"] for item in result))
        self.assertIn("power-saving", result[0]["recovery"])

    def test_each_subsystem_rule_is_classified(self):
        cases = [
            ({"solar_power": 15}, "Low Solar Power", "Electrical Power System (EPS)"),
            ({"communication_status": "FAILED"}, "Communication Link Degradation", "Communication System"),
            ({"attitude_error": 3.0}, "Attitude Control Anomaly", "Attitude Determination and Control System (ADCS)"),
            ({"cpu_temperature": 84}, "High CPU Temperature", "Onboard Computing System"),
            ({"cpu_load": 90}, "High CPU Load", "Onboard Computing System"),
        ]
        for changes, fault, subsystem in cases:
            with self.subTest(fault=fault):
                result = diagnose(telemetry(**changes))
                self.assertIn(fault, {item["fault"] for item in result})
                self.assertIn(subsystem, {item["subsystem"] for item in result})

    def test_multiple_critical_penalties_are_cumulative(self):
        result = diagnose(telemetry(temperature=72, battery_soc=18, battery_voltage=8.6, solar_power=6))
        self.assertEqual(health_score(result), 0)


if __name__ == "__main__":
    unittest.main()