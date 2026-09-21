from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    username: str
    role: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class EnrollmentRequest(BaseModel):
    device_id: str = Field(min_length=8, max_length=120)
    name: str = Field(min_length=1, max_length=200)
    os_name: str = "Unknown"
    os_version: str = "Unknown"
    architecture: str = "Unknown"
    agent_version: str = "0.1.0"
    enrollment_code: str = Field(min_length=4, max_length=32)


class EnrollmentResponse(BaseModel):
    device_id: str
    approved: bool
    agent_token: str | None = None
    message: str


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    device_id: str
    name: str
    os_name: str
    os_version: str
    architecture: str
    agent_version: str
    ip_address: str | None
    approved: bool
    status: str
    last_seen_at: datetime | None
    last_heartbeat_at: datetime | None
    metrics: dict[str, Any] = Field(default_factory=dict)


class ProcessTarget(BaseModel):
    pid: int = Field(gt=0)
    create_time: float = Field(gt=0)


class TerminateRequest(ProcessTarget):
    mode: Literal["graceful", "force"] = "force"
    tree: bool = False


class ProcessTuningRequest(ProcessTarget):
    priority: str | int | None = None
    affinity: list[int] | None = None


class DispatchRequest(BaseModel):
    workload_id: str
    device_id: str
    arguments: list[str] = Field(default_factory=list)


class AgentMessage(BaseModel):
    type: str
    request_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    device_id: str | None
    kind: str
    severity: str
    message: str
    metric: str | None
    threshold: float | None
    first_observed_at: datetime
    last_observed_at: datetime
    acknowledged: bool
    resolved: bool

