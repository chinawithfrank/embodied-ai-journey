from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class JointSnapshot(BaseModel):
    names: list[str] = Field(default_factory=list)
    positions: list[float] = Field(default_factory=list)
    received_at: datetime | None = None


class TaskRequest(BaseModel):
    target_degrees: float = Field(ge=-180.0, le=180.0)


class TaskSnapshot(BaseModel):
    id: str
    type: Literal['rotate_turtle'] = 'rotate_turtle'
    target_degrees: float
    status: str
    progress: float = Field(ge=0.0, le=100.0)
    remaining_delta: float | None = None
    created_at: datetime
    updated_at: datetime


class MotorRequest(BaseModel):
    enabled: bool


class RecordingSnapshot(BaseModel):
    id: str
    status: Literal['recording', 'ready']
    started_at: datetime
    stopped_at: datetime | None = None
    size_bytes: int = 0


class LogEntry(BaseModel):
    at: datetime
    level: Literal['info', 'warning', 'error']
    message: str


class GatewaySnapshot(BaseModel):
    robot_online: bool
    ros_available: bool
    ros_reason: str | None = None
    motors_enabled: bool = False
    joint_state: JointSnapshot = Field(default_factory=JointSnapshot)
    active_recording: RecordingSnapshot | None = None
