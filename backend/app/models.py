from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Satellite(Base):
    __tablename__ = "satellites"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    mission_type: Mapped[str] = mapped_column(String)
    orbit_type: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="NORMAL")
    health_score: Mapped[int] = mapped_column(Integer, default=100)
    last_update: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Telemetry(Base):
    __tablename__ = "telemetry"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    satellite_id: Mapped[str] = mapped_column(String, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    temperature: Mapped[float] = mapped_column(Float)
    battery_soc: Mapped[float] = mapped_column(Float)
    battery_voltage: Mapped[float] = mapped_column(Float)
    battery_current: Mapped[float] = mapped_column(Float)
    solar_power: Mapped[float] = mapped_column(Float)
    signal_strength: Mapped[float] = mapped_column(Float)
    cpu_temperature: Mapped[float] = mapped_column(Float)
    cpu_load: Mapped[float] = mapped_column(Float)
    attitude_error: Mapped[float] = mapped_column(Float, default=0.0)
    attitude_status: Mapped[str] = mapped_column(String)
    communication_status: Mapped[str] = mapped_column(String)

class Fault(Base):
    __tablename__ = "faults"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    satellite_id: Mapped[str] = mapped_column(String, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    fault: Mapped[str] = mapped_column(String)
    fault_id: Mapped[str | None] = mapped_column(String, nullable=True)
    severity: Mapped[str] = mapped_column(String)
    subsystem: Mapped[str] = mapped_column(String)
    detected_parameters: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_values: Mapped[str | None] = mapped_column(Text, nullable=True)
    thresholds: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str] = mapped_column(Text)
    diagnostic_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    recovery: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="OPEN")

class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    satellite_id: Mapped[str] = mapped_column(String, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    fault: Mapped[str] = mapped_column(String)
    fault_id: Mapped[str | None] = mapped_column(String, nullable=True)
    severity: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    recommended_action: Mapped[str] = mapped_column(Text)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
