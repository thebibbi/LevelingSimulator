"""
Database models and connection management
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from config import settings

Base = declarative_base()


# Database Models
class PlatformConfiguration(Base):
    """Stores platform configuration history"""

    __tablename__ = "platform_configurations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    base_radius = Column(Float, nullable=False)
    platform_radius = Column(Float, nullable=False)
    nominal_leg_length = Column(Float, nullable=False)
    min_leg_length = Column(Float, nullable=False)
    max_leg_length = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class CalculationLog(Base):
    """Logs all IK calculations for analysis"""

    __tablename__ = "calculation_logs"

    id = Column(Integer, primary_key=True, index=True)
    configuration = Column(String(50), nullable=False, index=True)
    pose_x = Column(Float)
    pose_y = Column(Float)
    pose_z = Column(Float)
    pose_roll = Column(Float)
    pose_pitch = Column(Float)
    pose_yaw = Column(Float)
    result_valid = Column(Boolean)
    leg_lengths = Column(Text)  # JSON string
    calculation_time_ms = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_agent = Column(String(200))
    ip_address = Column(String(50))


class APIKey(Base):
    """Stores API keys for authentication"""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)


# Database connection
engine = None
SessionLocal = None


def init_db():
    """Initialize database connection and create tables"""
    global engine, SessionLocal

    if not settings.database_enabled:
        return

    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get database session"""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def log_calculation(
    db: Session,
    configuration: str,
    pose: dict,
    result: dict,
    calculation_time: float,
    request_info: Optional[dict] = None,
):
    """Log a calculation to the database"""
    import json

    log_entry = CalculationLog(
        configuration=configuration,
        pose_x=pose.get("x", 0),
        pose_y=pose.get("y", 0),
        pose_z=pose.get("z", 0),
        pose_roll=pose.get("roll", 0),
        pose_pitch=pose.get("pitch", 0),
        pose_yaw=pose.get("yaw", 0),
        result_valid=result.get("valid", False),
        leg_lengths=json.dumps(result.get("leg_lengths", [])),
        calculation_time_ms=calculation_time,
        user_agent=request_info.get("user_agent", "") if request_info else "",
        ip_address=request_info.get("ip", "") if request_info else "",
    )

    db.add(log_entry)
    db.commit()
    return log_entry
