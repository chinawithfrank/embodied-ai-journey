from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Position(BaseModel):
    x: float = Field(ge=-0.7, le=0.7)
    y: float = Field(ge=-0.7, le=0.7)
    z: float = Field(ge=0.03, le=0.65)


class PickPlaceRequest(BaseModel):
    pick: Position
    place: Position


class TaskSnapshot(BaseModel):
    id: str
    pick: Position
    place: Position
    status: str
    message: str
    progress: float = Field(ge=0.0, le=100.0)
    created_at: datetime
    updated_at: datetime


class JointSnapshot(BaseModel):
    names: list[str] = Field(default_factory=list)
    positions: list[float] = Field(default_factory=list)
    received_at: datetime | None = None


class StatusSnapshot(BaseModel):
    ros_available: bool
    robot_online: bool
    ros_reason: str | None = None
    joint_state: JointSnapshot = Field(default_factory=JointSnapshot)
