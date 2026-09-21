from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DeviceStatus(str, Enum):
    pending = "pending"
    connected = "connected"
    stale = "stale"
    disconnected = "disconnected"
    overloaded = "overloaded"
    warning = "warning"


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    os_name: Mapped[str] = mapped_column(String(200), default="Unknown")
    os_version: Mapped[str] = mapped_column(String(200), default="Unknown")
    architecture: Mapped[str] = mapped_column(String(80), default="Unknown")
    agent_version: Mapped[str] = mapped_column(String(40), default="0.1.0")
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    credential_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enrollment_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    latest_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics = relationship("MetricSample", back_populates="device", cascade="all, delete-orphan")


class MetricSample(Base):
    __tablename__ = "metric_samples"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.device_id"), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    cpu_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    disk_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    upload_bps: Mapped[float | None] = mapped_column(Float, nullable=True)
    download_bps: Mapped[float | None] = mapped_column(Float, nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    device = relationship("Device", back_populates="metrics")


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str | None] = mapped_column(ForeignKey("devices.device_id"), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(60), index=True)
    severity: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(Text)
    metric: Mapped[str | None] = mapped_column(String(60), nullable=True)
    threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    first_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor: Mapped[str] = mapped_column(String(120), default="system")
    action: Mapped[str] = mapped_column(String(100), index=True)
    device_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    command_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    outcome: Mapped[str] = mapped_column(String(80), default="accepted")
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class AdminUser(Base):
    __tablename__ = "admin_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(120), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(40), default="admin")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Workload(Base):
    __tablename__ = "workloads"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workload_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    executable_path: Mapped[str] = mapped_column(Text)
    allowed_arguments: Mapped[list] = mapped_column(JSON, default=list)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)


class CommandRecord(Base):
    __tablename__ = "command_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    command_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    device_id: Mapped[str] = mapped_column(String(120), index=True)
    command_type: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(40), default="queued")
    request: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (UniqueConstraint("command_id", name="uq_command_id"),)

