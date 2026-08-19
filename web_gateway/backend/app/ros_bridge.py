from math import pi
from threading import Thread
from time import monotonic

from .state import GatewayState

try:
    import rclpy
    from action_msgs.msg import GoalStatus
    from rclpy.action import ActionClient
    from rclpy.executors import MultiThreadedExecutor
    from rclpy.node import Node
    from sensor_msgs.msg import JointState
    from std_srvs.srv import SetBool
    from turtlesim.action import RotateAbsolute

    ROS_IMPORT_ERROR = None
except ImportError as error:
    ROS_IMPORT_ERROR = error


class RosBridge:
    """A deliberately small ROS allowlist exposed to the HTTP API."""

    def __init__(self, state: GatewayState, notify):
        self._state = state
        self._notify = notify
        self._node = None
        self._executor = None
        self._thread = None
        self._motor_client = None
        self._rotate_client = None
        self._goal_handles = {}
        self._initial_remaining = {}
        self._last_notification_at = 0.0

    def start(self) -> None:
        if ROS_IMPORT_ERROR is not None:
            self._state.set_ros_status(False, f'rclpy unavailable: {ROS_IMPORT_ERROR}')
            self._state.add_log('error', 'ROS bridge did not start: rclpy unavailable.')
            return
        try:
            rclpy.init(args=None)
            self._node = Node('web_gateway_bridge')
            self._motor_client = self._node.create_client(
                SetBool, '/set_motors_enabled')
            self._rotate_client = ActionClient(
                self._node, RotateAbsolute, '/turtle1/rotate_absolute')
            self._node.create_subscription(
                JointState, '/joint_states', self._on_joint_state, 10)
            self._executor = MultiThreadedExecutor()
            self._executor.add_node(self._node)
            self._thread = Thread(target=self._executor.spin, daemon=True)
            self._thread.start()
            self._state.set_ros_status(True)
            self._state.add_log('info', 'ROS bridge started with a restricted API.')
            self._notify()
        except Exception as error:
            self._state.set_ros_status(False, str(error))
            self._state.add_log('error', f'ROS bridge failed to start: {error}')

    def shutdown(self) -> None:
        if self._executor is not None:
            self._executor.shutdown()
        if self._node is not None:
            self._node.destroy_node()
        if ROS_IMPORT_ERROR is None and rclpy.ok():
            rclpy.shutdown()

    def set_motors(self, enabled: bool) -> None:
        self._require_bridge()
        if not self._motor_client.wait_for_service(timeout_sec=2.0):
            raise RuntimeError('/set_motors_enabled is unavailable.')
        request = SetBool.Request(data=enabled)
        future = self._motor_client.call_async(request)
        future.add_done_callback(lambda completed: self._on_motor_response(
            completed, enabled))

    def create_rotation_task(self, target_degrees: float):
        self._require_bridge()
        task = self._state.create_rotation_task(target_degrees)
        if not self._rotate_client.wait_for_server(timeout_sec=2.0):
            self._state.update_task(task.id, status='rejected')
            raise RuntimeError('/turtle1/rotate_absolute is unavailable.')
        goal = RotateAbsolute.Goal()
        goal.theta = target_degrees * pi / 180.0
        future = self._rotate_client.send_goal_async(
            goal,
            feedback_callback=lambda feedback: self._on_rotation_feedback(
                task.id, feedback),
        )
        future.add_done_callback(
            lambda completed: self._on_goal_response(task.id, completed))
        self._state.add_log('info', f'Rotation task created: {task.id}')
        self._notify()
        return task

    def cancel_task(self, task_id: str) -> None:
        task = self._state.get_task(task_id)
        if task is None:
            raise KeyError(task_id)
        goal_handle = self._goal_handles.get(task_id)
        if goal_handle is None:
            raise RuntimeError('The task cannot be cancelled yet.')
        self._state.update_task(task_id, status='cancel_requested')
        future = goal_handle.cancel_goal_async()
        future.add_done_callback(lambda completed: self._on_cancel_response(
            task_id, completed))
        self._state.add_log('warning', f'Cancellation requested: {task_id}')
        self._notify()

    def _on_joint_state(self, message) -> None:
        self._state.set_joint_state(list(message.name), list(message.position))
        if monotonic() - self._last_notification_at >= 0.2:
            self._last_notification_at = monotonic()
            self._notify()

    def _on_motor_response(self, future, enabled: bool) -> None:
        try:
            response = future.result()
            if not response.success:
                raise RuntimeError(response.message)
            self._state.set_motors_enabled(enabled)
            self._state.add_log('info', response.message)
        except Exception as error:
            self._state.add_log('error', f'Motor service failed: {error}')
        self._notify()

    def _on_goal_response(self, task_id: str, future) -> None:
        try:
            goal_handle = future.result()
            if not goal_handle.accepted:
                self._state.update_task(task_id, status='rejected')
                self._state.add_log('warning', f'Rotation task rejected: {task_id}')
                return
            self._goal_handles[task_id] = goal_handle
            self._state.update_task(task_id, status='running')
            result_future = goal_handle.get_result_async()
            result_future.add_done_callback(
                lambda completed: self._on_rotation_result(task_id, completed))
        except Exception as error:
            self._state.update_task(task_id, status='failed')
            self._state.add_log('error', f'Rotation task failed: {error}')
        self._notify()

    def _on_rotation_feedback(self, task_id: str, feedback_message) -> None:
        remaining = abs(feedback_message.feedback.remaining)
        initial = self._initial_remaining.setdefault(task_id, max(remaining, 0.001))
        progress = max(0.0, min(99.0, (1.0 - remaining / initial) * 100.0))
        self._state.update_task(
            task_id, progress=progress, remaining_delta=remaining)
        self._notify()

    def _on_rotation_result(self, task_id: str, future) -> None:
        try:
            result = future.result()
            status = (
                'succeeded' if result.status == GoalStatus.STATUS_SUCCEEDED
                else 'cancelled' if result.status == GoalStatus.STATUS_CANCELED
                else 'failed'
            )
            self._state.update_task(task_id, status=status, progress=100.0)
            self._state.add_log('info', f'Rotation task {status}: {task_id}')
        except Exception as error:
            self._state.update_task(task_id, status='failed')
            self._state.add_log('error', f'Rotation result failed: {error}')
        finally:
            self._goal_handles.pop(task_id, None)
            self._initial_remaining.pop(task_id, None)
        self._notify()

    def _on_cancel_response(self, task_id: str, future) -> None:
        try:
            response = future.result()
            if not response.goals_canceling:
                self._state.add_log('warning', f'Cancellation rejected: {task_id}')
        except Exception as error:
            self._state.add_log('error', f'Cancellation failed: {error}')
        self._notify()

    def _require_bridge(self) -> None:
        if self._node is None:
            raise RuntimeError('ROS bridge is unavailable.')
