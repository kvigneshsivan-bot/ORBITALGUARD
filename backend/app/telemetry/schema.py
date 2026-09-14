from datetime import datetime, UTC
from pydantic import BaseModel, Field


class TelemetryRecord(BaseModel):
    timestamp: datetime | None = None
    satellite_id: str = Field(min_length=1, max_length=32)
    temperature: float
    battery_soc: float = Field(ge=0, le=100)
    battery_voltage: float = Field(ge=0)
    battery_current: float
    solar_power: float = Field(ge=0)
    signal_strength: float = Field(ge=0, le=100)
    cpu_temperature: float
    cpu_load: float = Field(ge=0, le=100)
    attitude_error: float = Field(default=0, ge=0)
    attitude_status: str = "NOMINAL"
    communication_status: str = "NOMINAL"

    def as_dict(self) -> dict:
        values = self.model_dump()
        values["timestamp"] = self.timestamp or datetime.now(UTC).replace(tzinfo=None)
        return values