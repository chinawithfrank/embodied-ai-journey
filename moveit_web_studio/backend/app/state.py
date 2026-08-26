from datetime import datetime, timezone
from threading import Lock
from time import monotonic
from uuid import uuid4

from .models import JointSnapshot, PickPlaceRequest, StatusSnapshot, TaskSnapshot


def utc_now():
    return datetime.now(timezone.utc)


class StudioState:
    def __init__(self):
        self._lock = Lock()
        self._ros_available = False
        self._ros_reason = 'ROS bridge has not started.'
        self._joint_state = JointSnapshot()
        self._last_joint_state_at = None
        self._tasks: dict[str, TaskSnapshot] = {}

    def set_ros_status(self, available, reason=None):
        with self._lock:
            self._ros_available = available
            self._ros_reason = reason

    def set_joint_state(self, names, positions):
        with self._lock:
            self._joint_state = JointSnapshot(
                names=names, positions=positions, received_at=utc_now())
            self._last_joint_state_at = monotonic()

    def create_task(self, request: PickPlaceRequest):
        now = utc_now()
        task = TaskSnapshot(
            id=uuid4().hex[:12],
            pick=request.pick,
            place=request.place,
            status='queued',
            message='Waiting for the MoveIt executor.',
            progress=0.0,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._tasks[task.id] = task
        return task

    def update_task(self, task_id, **changes):
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            updated = task.model_copy(
                update={**changes, 'updated_at': utc_now()})
            self._tasks[task_id] = updated
            return updated

    def list_tasks(self):
        with self._lock:
            return sorted(
                self._tasks.values(), key=lambda task: task.created_at,
                reverse=True)

    def snapshot(self):
        with self._lock:
            robot_online = (
                self._ros_available
                and self._last_joint_state_at is not None
                and monotonic() - self._last_joint_state_at < 3.0
            )
            return StatusSnapshot(
                ros_available=self._ros_available,
                robot_online=robot_online,
                ros_reason=self._ros_reason,
                joint_state=self._joint_state,
            )
