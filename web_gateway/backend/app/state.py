from datetime import datetime, timezone
from threading import Lock
from time import monotonic
from uuid import uuid4

from .models import GatewaySnapshot, JointSnapshot, LogEntry, RecordingSnapshot
from .models import TaskSnapshot


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class GatewayState:
    """Thread-safe state shared by ROS callbacks and FastAPI handlers."""

    def __init__(self):
        self._lock = Lock()
        self._ros_available = False
        self._ros_reason: str | None = 'ROS bridge has not started.'
        self._motors_enabled = False
        self._joint_state = JointSnapshot()
        self._last_joint_state_at: float | None = None
        self._tasks: dict[str, TaskSnapshot] = {}
        self._logs: list[LogEntry] = []
        self._active_recording: RecordingSnapshot | None = None

    def set_ros_status(self, available: bool, reason: str | None = None) -> None:
        with self._lock:
            self._ros_available = available
            self._ros_reason = reason

    def set_joint_state(self, names: list[str], positions: list[float]) -> None:
        with self._lock:
            self._joint_state = JointSnapshot(
                names=names, positions=positions, received_at=utc_now())
            self._last_joint_state_at = monotonic()

    def set_motors_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._motors_enabled = enabled

    def add_log(self, level: str, message: str) -> None:
        with self._lock:
            self._logs.append(LogEntry(at=utc_now(), level=level, message=message))
            self._logs = self._logs[-200:]

    def create_rotation_task(self, target_degrees: float) -> TaskSnapshot:
        now = utc_now()
        task = TaskSnapshot(
            id=uuid4().hex[:12],
            target_degrees=target_degrees,
            status='queued',
            progress=0.0,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._tasks[task.id] = task
        return task

    def update_task(self, task_id: str, **changes: object) -> TaskSnapshot | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            updated = task.model_copy(
                update={**changes, 'updated_at': utc_now()})
            self._tasks[task_id] = updated
            return updated

    def get_task(self, task_id: str) -> TaskSnapshot | None:
        with self._lock:
            return self._tasks.get(task_id)

    def list_tasks(self) -> list[TaskSnapshot]:
        with self._lock:
            return sorted(
                self._tasks.values(), key=lambda task: task.created_at,
                reverse=True)

    def set_active_recording(self, recording: RecordingSnapshot | None) -> None:
        with self._lock:
            self._active_recording = recording

    def get_active_recording(self) -> RecordingSnapshot | None:
        with self._lock:
            return self._active_recording

    def list_logs(self) -> list[LogEntry]:
        with self._lock:
            return list(reversed(self._logs))

    def snapshot(self) -> GatewaySnapshot:
        with self._lock:
            is_fresh = (
                self._last_joint_state_at is not None
                and monotonic() - self._last_joint_state_at < 3.0
            )
            return GatewaySnapshot(
                robot_online=self._ros_available and is_fresh,
                ros_available=self._ros_available,
                ros_reason=self._ros_reason,
                motors_enabled=self._motors_enabled,
                joint_state=self._joint_state,
                active_recording=self._active_recording,
            )
