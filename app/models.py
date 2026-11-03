from datetime import datetime, timezone

from sqlalchemy import BigInteger, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# BigInteger tren PostgreSQL, Integer tren SQLite (de autoincrement hoat dong)
BigId = BigInteger().with_variant(Integer, "sqlite")


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default="operator")  # admin | operator
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Camera(Base):
    __tablename__ = "cameras"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    stream_url: Mapped[str] = mapped_column(String(255), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)  # North|South|East|West
    roi_config: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="online")  # online|offline|error


class TrafficCount(Base):
    __tablename__ = "traffic_counts"
    id: Mapped[int] = mapped_column(BigId, primary_key=True, autoincrement=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)
    vehicle_count: Mapped[int] = mapped_column(Integer, nullable=False)
    breakdown: Mapped[dict | None] = mapped_column(JSON)  # {"car":..,"motorbike":..,"bus":..,"truck":..}
    density_score: Mapped[float | None] = mapped_column(Float)


class TrafficLightState(Base):
    __tablename__ = "traffic_light_states"
    id: Mapped[int] = mapped_column(BigId, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)
    direction_pair: Mapped[str | None] = mapped_column(String(50))  # North-South | East-West
    current_phase: Mapped[str] = mapped_column(String(10), nullable=False)  # RED|YELLOW|GREEN
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False)  # AUTO|MANUAL|FAILSAFE


class SystemLog(Base):
    __tablename__ = "system_logs"
    id: Mapped[int] = mapped_column(BigId, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
