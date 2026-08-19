import tempfile
import unittest
from pathlib import Path

from app.recordings import RecordingManager
from app.state import GatewayState


class GatewayStateTests(unittest.TestCase):

    def test_joint_state_marks_robot_online(self):
        state = GatewayState()
        state.set_ros_status(True)
        state.set_joint_state(['swivel', 'tilt'], [0.3, -0.1])

        snapshot = state.snapshot()

        self.assertTrue(snapshot.robot_online)
        self.assertEqual(snapshot.joint_state.names, ['swivel', 'tilt'])
        self.assertEqual(snapshot.joint_state.positions, [0.3, -0.1])

    def test_task_update_preserves_task_identity(self):
        state = GatewayState()
        task = state.create_rotation_task(90.0)

        updated = state.update_task(task.id, status='running', progress=40.0)

        self.assertEqual(updated.id, task.id)
        self.assertEqual(updated.status, 'running')
        self.assertEqual(updated.progress, 40.0)


class RecordingManagerTests(unittest.TestCase):

    def test_lists_recording_directory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            recordings_dir = Path(temporary_directory)
            run_dir = recordings_dir / 'run-20260819-120000'
            run_dir.mkdir()
            (run_dir / 'data.mcap').write_bytes(b'mcap')
            manager = RecordingManager(
                GatewayState(), recordings_dir, lambda: None)

            recordings = manager.list_recordings()

        self.assertEqual(recordings[0].id, 'run-20260819-120000')
        self.assertEqual(recordings[0].size_bytes, 4)


if __name__ == '__main__':
    unittest.main()
