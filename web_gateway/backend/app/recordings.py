import os
import signal
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .models import RecordingSnapshot
from .state import GatewayState


class RecordingManager:
    topics = ('/joint_states', '/visualization_marker')

    def __init__(self, state: GatewayState, recordings_dir: Path, notify):
        self._state = state
        self._recordings_dir = recordings_dir
        self._notify = notify
        self._process: subprocess.Popen | None = None

    def start(self) -> RecordingSnapshot:
        if self._process is not None and self._process.poll() is None:
            raise RuntimeError('A recording is already active.')

        self._recordings_dir.mkdir(parents=True, exist_ok=True)
        started_at = datetime.now(timezone.utc)
        recording_id = started_at.strftime('run-%Y%m%d-%H%M%S')
        output_dir = self._recordings_dir / recording_id
        command = [
            'ros2', 'bag', 'record', '--storage', 'mcap', '-o', str(output_dir),
            *self.topics,
        ]
        self._process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        recording = RecordingSnapshot(
            id=recording_id,
            status='recording',
            started_at=started_at,
        )
        self._state.set_active_recording(recording)
        self._state.add_log('info', f'MCAP recording started: {recording_id}')
        self._notify()
        return recording

    def stop(self) -> RecordingSnapshot:
        recording = self._state.get_active_recording()
        if recording is None:
            raise RuntimeError('No recording is active.')
        if self._process is not None and self._process.poll() is None:
            os.killpg(self._process.pid, signal.SIGINT)
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
        stopped = recording.model_copy(update={
            'status': 'ready',
            'stopped_at': datetime.now(timezone.utc),
            'size_bytes': self._directory_size(self._recordings_dir / recording.id),
        })
        self._process = None
        self._state.set_active_recording(None)
        self._state.add_log('info', f'MCAP recording stopped: {recording.id}')
        self._notify()
        return stopped

    def list_recordings(self) -> list[RecordingSnapshot]:
        active = self._state.get_active_recording()
        if not self._recordings_dir.exists():
            return [active] if active else []
        recordings = []
        for directory in sorted(self._recordings_dir.iterdir(), reverse=True):
            if not directory.is_dir() or not directory.name.startswith('run-'):
                continue
            started_at = datetime.fromtimestamp(
                directory.stat().st_mtime, tz=timezone.utc)
            status = 'recording' if active and active.id == directory.name else 'ready'
            recordings.append(RecordingSnapshot(
                id=directory.name,
                status=status,
                started_at=started_at,
                stopped_at=None if status == 'recording' else started_at,
                size_bytes=self._directory_size(directory),
            ))
        if active is not None and all(item.id != active.id for item in recordings):
            recordings.insert(0, active)
        return recordings

    @staticmethod
    def _directory_size(directory: Path) -> int:
        if not directory.exists():
            return 0
        return sum(path.stat().st_size for path in directory.rglob('*')
                   if path.is_file())
