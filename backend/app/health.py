def calculate_health(anomalies: list[dict]) -> int:
    score = 100 - sum(25 if item["severity"] == "CRITICAL" else 10 for item in anomalies)
    return max(0, min(100, score))


def status_for_score(score: int) -> str:
    if score < 40: return "CRITICAL"
    if score < 70: return "DEGRADED"
    if score < 90: return "WARNING"
    return "NORMAL"