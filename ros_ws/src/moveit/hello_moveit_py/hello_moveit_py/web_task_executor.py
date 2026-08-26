import json
from queue import Empty, Queue
from threading import Thread

from geometry_msgs.msg import PoseStamped
from moveit_msgs.msg import CollisionObject, PlanningScene
from moveit_msgs.srv import ApplyPlanningScene
import rclpy
from rclpy.node import Node
from shape_msgs.msg import SolidPrimitive
from std_msgs.msg import String

from moveit.planning import MoveItPy

ARM_GROUP = 'panda_arm'
HAND_GROUP = 'hand'
END_EFFECTOR_LINK = 'panda_link8'
BASE_FRAME = 'world'
COMMAND_TOPIC = '/web_moveit/task_request'
STATUS_TOPIC = '/web_moveit/task_status'
OBJECT_ID = 'web_pick_object'
MIN_COORDINATE = -0.7
MAX_COORDINATE = 0.7
MIN_HEIGHT = 0.03
MAX_HEIGHT = 0.65


class WebTaskExecutor(Node):
    """Execute a small, allowlisted pick-and-place workflow for the web demo."""

    def __init__(self):
        super().__init__('web_moveit_task_executor')
        self.status_publisher = self.create_publisher(String, STATUS_TOPIC, 10)
        self.create_subscription(String, COMMAND_TOPIC, self.enqueue_task, 10)
        self.scene_client = self.create_client(
            ApplyPlanningScene, '/apply_planning_scene')
        self.moveit_py = MoveItPy(node_name='web_moveit_moveit_py')
        self.arm = self.moveit_py.get_planning_component(ARM_GROUP)
        self.hand = self.moveit_py.get_planning_component(HAND_GROUP)
        self.task_queue = Queue(maxsize=1)
        self.worker = Thread(target=self.process_tasks, daemon=True)
        self.worker.start()
        self.publish_status('', 'ready', 'Web MoveIt executor is ready.', 0)

    def enqueue_task(self, message):
        try:
            task = json.loads(message.data)
            self.validate_task(task)
            self.task_queue.put_nowait(task)
            self.publish_status(
                task['id'], 'queued', 'Task accepted by the MoveIt executor.', 5)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            task_id = self.extract_task_id(message.data)
            self.publish_status(task_id, 'rejected', str(error), 100)
        except Exception:
            task_id = self.extract_task_id(message.data)
            self.publish_status(
                task_id, 'rejected', 'Another task is already running.', 100)

    def process_tasks(self):
        while rclpy.ok():
            try:
                task = self.task_queue.get(timeout=0.2)
            except Empty:
                continue
            try:
                self.execute_task(task)
            except Exception as error:
                self.get_logger().error(f'Web task failed: {error}')
                self.publish_status(task['id'], 'failed', str(error), 100)
            finally:
                self.task_queue.task_done()

    def execute_task(self, task):
        pick = task['pick']
        place = task['place']
        self.publish_status(task['id'], 'planning', 'Adding the web object.', 10)
        self.apply_object(pick)

        self.publish_status(task['id'], 'planning', 'Planning approach motion.', 20)
        self.plan_and_execute_pose(self.pose_above(pick))

        self.publish_status(
            task['id'], 'grasping',
            'Entering grasp zone and closing the gripper.', 40)
        self.remove_object()
        self.plan_and_execute_pose(self.pose_at(pick, 0.06))
        self.plan_and_execute_named_state(self.hand, 'close')

        self.publish_status(task['id'], 'transporting', 'Moving the object to its target.', 55)
        self.plan_and_execute_pose(self.pose_above(pick))
        self.plan_and_execute_pose(self.pose_above(place))
        self.plan_and_execute_pose(self.pose_at(place, 0.06))

        self.publish_status(task['id'], 'placing', 'Opening the gripper.', 80)
        self.plan_and_execute_named_state(self.hand, 'open')
        self.plan_and_execute_pose(self.pose_above(place))

        self.publish_status(task['id'], 'returning', 'Returning the arm to ready.', 92)
        self.plan_and_execute_named_state(self.arm, 'ready')
        self.publish_status(task['id'], 'succeeded', 'Pick-and-place completed.', 100)

    def plan_and_execute_pose(self, pose):
        self.arm.set_start_state_to_current_state()
        self.arm.set_goal_state(
            pose_stamped_msg=pose,
            pose_link=END_EFFECTOR_LINK,
        )
        result = self.arm.plan()
        if not result:
            raise RuntimeError('MoveIt could not plan a collision-free arm path.')
        self.moveit_py.execute(result.trajectory, controllers=[])

    def plan_and_execute_named_state(self, component, state_name):
        component.set_start_state_to_current_state()
        component.set_goal_state(configuration_name=state_name)
        result = component.plan()
        if not result:
            raise RuntimeError(f'MoveIt could not plan the {state_name} state.')
        self.moveit_py.execute(result.trajectory, controllers=[])

    def apply_object(self, position):
        if not self.scene_client.wait_for_service(timeout_sec=2.0):
            raise RuntimeError('MoveIt planning-scene service is unavailable.')
        collision_object = CollisionObject()
        collision_object.id = OBJECT_ID
        collision_object.header.frame_id = BASE_FRAME
        primitive = SolidPrimitive()
        primitive.type = SolidPrimitive.BOX
        primitive.dimensions = [0.05, 0.05, 0.05]
        pose = self.pose_at(position, 0.025).pose
        collision_object.primitives.append(primitive)
        collision_object.primitive_poses.append(pose)
        collision_object.operation = CollisionObject.ADD
        request = ApplyPlanningScene.Request()
        request.scene = PlanningScene(is_diff=True)
        request.scene.world.collision_objects.append(collision_object)
        response = self.scene_client.call(request)
        if not response.success:
            raise RuntimeError('MoveIt rejected the web collision object.')

    def remove_object(self):
        collision_object = CollisionObject()
        collision_object.id = OBJECT_ID
        collision_object.header.frame_id = BASE_FRAME
        collision_object.operation = CollisionObject.REMOVE
        request = ApplyPlanningScene.Request()
        request.scene = PlanningScene(is_diff=True)
        request.scene.world.collision_objects.append(collision_object)
        self.scene_client.call(request)

    def pose_above(self, position):
        return self.pose_at(position, 0.22)

    def pose_at(self, position, height):
        pose = PoseStamped()
        pose.header.frame_id = BASE_FRAME
        pose.pose.orientation.w = 1.0
        pose.pose.position.x = position['x']
        pose.pose.position.y = position['y']
        pose.pose.position.z = position['z'] + height
        return pose

    def validate_task(self, task):
        if not isinstance(task['id'], str) or not task['id']:
            raise ValueError('Task id is required.')
        for key in ('pick', 'place'):
            position = task[key]
            for coordinate in ('x', 'y', 'z'):
                value = position[coordinate]
                if not isinstance(value, (int, float)):
                    raise ValueError(f'{key}.{coordinate} must be a number.')
            if not MIN_COORDINATE <= position['x'] <= MAX_COORDINATE:
                raise ValueError(f'{key}.x is outside the demo workspace.')
            if not MIN_COORDINATE <= position['y'] <= MAX_COORDINATE:
                raise ValueError(f'{key}.y is outside the demo workspace.')
            if not MIN_HEIGHT <= position['z'] <= MAX_HEIGHT:
                raise ValueError(f'{key}.z is outside the demo workspace.')

    def extract_task_id(self, value):
        try:
            return json.loads(value).get('id', '')
        except (json.JSONDecodeError, AttributeError):
            return ''

    def publish_status(self, task_id, status, message, progress):
        payload = {
            'id': task_id,
            'status': status,
            'message': message,
            'progress': progress,
        }
        self.status_publisher.publish(String(data=json.dumps(payload)))


def main(args=None):
    rclpy.init(args=args)
    node = WebTaskExecutor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
