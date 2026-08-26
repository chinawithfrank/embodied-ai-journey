import json
from threading import Thread

from .state import StudioState

try:
    import rclpy
    from rclpy.executors import MultiThreadedExecutor
    from rclpy.node import Node
    from sensor_msgs.msg import JointState
    from std_msgs.msg import String

    ROS_IMPORT_ERROR = None
except ImportError as error:
    ROS_IMPORT_ERROR = error


class RosBridge:
    def __init__(self, state: StudioState, notify):
        self._state = state
        self._notify = notify
        self._node = None
        self._executor = None
        self._thread = None
        self._task_publisher = None

    def start(self):
        if ROS_IMPORT_ERROR is not None:
            self._state.set_ros_status(False, str(ROS_IMPORT_ERROR))
            return
        try:
            rclpy.init(args=None)
            self._node = Node('moveit_web_gateway')
            self._task_publisher = self._node.create_publisher(
                String, '/web_moveit/task_request', 10)
            self._node.create_subscription(
                String, '/web_moveit/task_status', self._on_task_status, 10)
            self._node.create_subscription(
                JointState, '/joint_states', self._on_joint_state, 10)
            self._executor = MultiThreadedExecutor()
            self._executor.add_node(self._node)
            self._thread = Thread(target=self._executor.spin, daemon=True)
            self._thread.start()
            self._state.set_ros_status(True)
            self._notify()
        except Exception as error:
            self._state.set_ros_status(False, str(error))

    def shutdown(self):
        if self._executor is not None:
            self._executor.shutdown()
        if self._node is not None:
            self._node.destroy_node()
        if ROS_IMPORT_ERROR is None and rclpy.ok():
            rclpy.shutdown()

    def submit_task(self, task):
        if self._task_publisher is None:
            raise RuntimeError('ROS bridge is unavailable.')
        payload = {
            'id': task.id,
            'pick': task.pick.model_dump(),
            'place': task.place.model_dump(),
        }
        self._task_publisher.publish(String(data=json.dumps(payload)))

    def _on_joint_state(self, message):
        self._state.set_joint_state(list(message.name), list(message.position))
        self._notify()

    def _on_task_status(self, message):
        try:
            payload = json.loads(message.data)
            if payload.get('id'):
                self._state.update_task(
                    payload['id'],
                    status=payload['status'],
                    message=payload['message'],
                    progress=float(payload['progress']),
                )
                self._notify()
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return
