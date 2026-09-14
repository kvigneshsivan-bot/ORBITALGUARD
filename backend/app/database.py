from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def init_db():
    from . import models
    Base.metadata.create_all(bind=engine)
    migrations = {"telemetry": {"attitude_error": "FLOAT DEFAULT 0.0"}, "faults": {"fault_id": "VARCHAR", "detected_parameters": "TEXT", "observed_values": "TEXT", "thresholds": "TEXT", "diagnostic_explanation": "TEXT"}, "alerts": {"fault_id": "VARCHAR"}}
    with engine.begin() as connection:
        for table, additions in migrations.items():
            columns = {column["name"] for column in inspect(engine).get_columns(table)}
            for name, definition in additions.items():
                if name not in columns:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))
