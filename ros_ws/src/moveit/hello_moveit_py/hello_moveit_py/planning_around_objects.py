from geometry_msgs.msg import Point, Pose, PoseStamped
from moveit_msgs.msg import CollisionObject, DisplayTrajectory, PlanningScene
from moveit_msgs.srv import ApplyPlanningScene
import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from shape_msgs.msg import SolidPrimitive
from std_srvs.srv import Trigger
from visualization_msgs.msg import Marker, MarkerArray

from moveit.planning import MoveItPy

BASE_FRAME = 'panda_link0'
END_EFFECTOR_LINK = 'panda_link8'
MARKER_TOPIC = '/rviz_visual_tools'
TRAJECTORY_TOPIC = '/display_planned_path'
OBSTACLE_ID = 'box1'
BOX_DIMENSIONS = (0.50, 0.10, 0.50)
BOX_POSITION = (0.20, 0.20, 0.25)


class ObjectPlanningDemo(Node):

    def __init__(self):
        super().__init__('python_object_planner')
        visualization_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.marker_publisher = self.create_publisher(
            MarkerArray, MARKER_TOPIC, visualization_qos)
        self.trajectory_publisher = self.create_publisher(
            DisplayTrajectory, TRAJECTORY_TOPIC, visualization_qos)
        self.scene_client = self.create_client(
            ApplyPlanningScene, '/apply_planning_scene')
        self.moveit_py = MoveItPy(node_name='python_object_planner')
        self.panda_arm = self.moveit_py.get_planning_component('panda_arm')
        self.target_pose = self.create_target_pose()
        self.collision_object = self.create_collision_object()
        self.plan_result = None
        self.object_ready = False
        self.request_sent = False

        self.add_object_to_local_scene()
        self.scene_timer = self.create_timer(
            0.5, self.add_object_to_move_group)
        self.create_service(Trigger, '~/show_scene', self.show_scene)
        self.create_service(Trigger, '~/plan', self.plan)
        self.create_service(Trigger, '~/execute', self.execute)
        self.publish_scene('Waiting for box1 to enter the Planning Scene')

    def create_target_pose(self):
        target_pose = PoseStamped()
        target_pose.header.frame_id = BASE_FRAME
        target_pose.pose.orientation.y = 0.8
        target_pose.pose.orientation.w = 0.6
        target_pose.pose.position.x = 0.10
        target_pose.pose.position.y = 0.40
        target_pose.pose.position.z = 0.40
        return target_pose

    def create_collision_object(self):
        collision_object = CollisionObject()
        collision_object.header.frame_id = BASE_FRAME
        collision_object.id = OBSTACLE_ID

        box = SolidPrimitive()
        box.type = SolidPrimitive.BOX
        box.dimensions = BOX_DIMENSIONS

        box_pose = Pose()
        box_pose.orientation.w = 1.0
        box_pose.position.x, box_pose.position.y, box_pose.position.z = (
            BOX_POSITION)

        collision_object.primitives.append(box)
        collision_object.primitive_poses.append(box_pose)
        collision_object.operation = CollisionObject.ADD
        return collision_object

    def add_object_to_local_scene(self):
        planning_scene_monitor = self.moveit_py.get_planning_scene_monitor()
        with planning_scene_monitor.read_write() as scene:
            scene.apply_collision_object(self.collision_object)
            scene.current_state.update()

    def add_object_to_move_group(self):
        if self.request_sent or self.object_ready:
            return

        if not self.scene_client.service_is_ready():
            self.get_logger().info(
                'Waiting for MoveIt apply_planning_scene service...')
            return

        request = ApplyPlanningScene.Request()
        request.scene = PlanningScene()
        request.scene.is_diff = True
        request.scene.world.collision_objects.append(self.collision_object)
        self.request_sent = True
        future = self.scene_client.call_async(request)
        future.add_done_callback(self.handle_scene_response)

    def handle_scene_response(self, future):
        try:
            response = future.result()
        except Exception as error:
            self.get_logger().error(f'Could not add {OBSTACLE_ID}: {error}')
            self.request_sent = False
            return

        if not response.success:
            self.get_logger().error(
                f'MoveIt rejected collision object: {OBSTACLE_ID}.')
            self.request_sent = False
            return

        self.object_ready = True
        self.scene_timer.cancel()
        self.publish_scene('box1 is active: plan around the orange obstacle')
        self.get_logger().info(
            'box1 is active in MoveItPy and move_group Planning Scenes.')

    def show_scene(self, request, response):
        del request
        self.publish_scene('1. Inspect the goal and collision object')
        response.success = self.object_ready
        response.message = (
            'Goal and box1 markers are visible.' if self.object_ready else
            'Markers are visible; wait for box1 to enter move_group.')
        return response

    def plan(self, request, response):
        del request
        if not self.object_ready:
            response.success = False
            response.message = 'Wait for box1 to enter move_group first.'
            return response

        self.publish_scene('2. Planning a path around box1')
        self.panda_arm.set_start_state_to_current_state()
        self.panda_arm.set_goal_state(
            pose_stamped_msg=self.target_pose,
            pose_link=END_EFFECTOR_LINK,
        )
        self.plan_result = self.panda_arm.plan()

        if not self.plan_result:
            self.publish_scene('Planning failed: no safe path found')
            response.success = False
            response.message = 'MoveIt could not find a collision-free plan.'
            return response

        display_trajectory = DisplayTrajectory()
        display_trajectory.trajectory.append(
            self.plan_result.trajectory.get_robot_trajectory_msg())
        self.trajectory_publisher.publish(display_trajectory)
        self.publish_scene('3. Plan ready: verify that it avoids box1')
        response.success = True
        response.message = 'Published a collision-aware trajectory to RViz.'
        return response

    def execute(self, request, response):
        del request
        if not self.plan_result:
            response.success = False
            response.message = 'Call plan successfully before execute.'
            return response

        self.publish_scene('4. Executing the collision-aware trajectory')
        self.moveit_py.execute(self.plan_result.trajectory, controllers=[])
        self.plan_result = None
        self.publish_scene('Execution complete: box1 remained in the scene')
        response.success = True
        response.message = 'Mock controller executed the safe trajectory.'
        return response

    def publish_scene(self, title):
        timestamp = self.get_clock().now().to_msg()
        markers = [
            self.create_title_marker(title, timestamp),
            self.create_goal_marker(timestamp),
            self.create_axis_marker(
                2, timestamp, (1.0, 0.15, 0.15), (0.12, 0.0, 0.0)),
            self.create_axis_marker(
                3, timestamp, (0.15, 1.0, 0.15), (0.0, 0.12, 0.0)),
            self.create_axis_marker(
                4, timestamp, (0.15, 0.35, 1.0), (0.0, 0.0, 0.12)),
            self.create_box_marker(timestamp),
            self.create_box_label(timestamp),
        ]
        self.marker_publisher.publish(MarkerArray(markers=markers))

    def create_title_marker(self, title, timestamp):
        marker = Marker()
        marker.header.frame_id = BASE_FRAME
        marker.header.stamp = timestamp
        marker.ns = 'object_planning'
        marker.id = 0
        marker.type = Marker.TEXT_VIEW_FACING
        marker.action = Marker.ADD
        marker.pose.position.z = 1.0
        marker.pose.orientation.w = 1.0
        marker.scale.z = 0.08
        marker.color.r = 1.0
        marker.color.g = 1.0
        marker.color.b = 1.0
        marker.color.a = 1.0
        marker.text = title
        return marker

    def create_goal_marker(self, timestamp):
        marker = Marker()
        marker.header = self.target_pose.header
        marker.header.stamp = timestamp
        marker.ns = 'object_planning'
        marker.id = 1
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD
        marker.pose = self.target_pose.pose
        marker.scale.x = 0.05
        marker.scale.y = 0.05
        marker.scale.z = 0.05
        marker.color.r = 1.0
        marker.color.g = 0.75
        marker.color.b = 0.05
        marker.color.a = 1.0
        return marker

    def create_axis_marker(self, marker_id, timestamp, color, vector):
        marker = Marker()
        marker.header = self.target_pose.header
        marker.header.stamp = timestamp
        marker.ns = 'object_planning'
        marker.id = marker_id
        marker.type = Marker.ARROW
        marker.action = Marker.ADD
        marker.scale.x = 0.01
        marker.scale.y = 0.02
        marker.scale.z = 0.02
        marker.color.r, marker.color.g, marker.color.b = color
        marker.color.a = 1.0
        start = Point(
            x=self.target_pose.pose.position.x,
            y=self.target_pose.pose.position.y,
            z=self.target_pose.pose.position.z,
        )
        offset = self.rotate_vector(vector)
        end = Point(
            x=start.x + offset[0],
            y=start.y + offset[1],
            z=start.z + offset[2],
        )
        marker.points = [start, end]
        return marker

    def rotate_vector(self, vector):
        orientation = self.target_pose.pose.orientation
        cross_x = 2.0 * (orientation.y * vector[2] - orientation.z * vector[1])
        cross_y = 2.0 * (orientation.z * vector[0] - orientation.x * vector[2])
        cross_z = 2.0 * (orientation.x * vector[1] - orientation.y * vector[0])
        return (
            vector[0] + orientation.w * cross_x + (
                orientation.y * cross_z - orientation.z * cross_y),
            vector[1] + orientation.w * cross_y + (
                orientation.z * cross_x - orientation.x * cross_z),
            vector[2] + orientation.w * cross_z + (
                orientation.x * cross_y - orientation.y * cross_x),
        )

    def create_box_marker(self, timestamp):
        marker = Marker()
        marker.header.frame_id = BASE_FRAME
        marker.header.stamp = timestamp
        marker.ns = 'object_planning'
        marker.id = 5
        marker.type = Marker.CUBE
        marker.action = Marker.ADD
        marker.pose = self.collision_object.primitive_poses[0]
        marker.scale.x, marker.scale.y, marker.scale.z = BOX_DIMENSIONS
        marker.color.r = 1.0
        marker.color.g = 0.20
        marker.color.b = 0.05
        marker.color.a = 0.85
        return marker

    def create_box_label(self, timestamp):
        marker = Marker()
        marker.header.frame_id = BASE_FRAME
        marker.header.stamp = timestamp
        marker.ns = 'object_planning'
        marker.id = 6
        marker.type = Marker.TEXT_VIEW_FACING
        marker.action = Marker.ADD
        marker.pose.position.x = BOX_POSITION[0]
        marker.pose.position.y = BOX_POSITION[1]
        marker.pose.position.z = (
            BOX_POSITION[2] + BOX_DIMENSIONS[2] / 2.0 + 0.08)
        marker.pose.orientation.w = 1.0
        marker.scale.z = 0.07
        marker.color.r = 1.0
        marker.color.g = 1.0
        marker.color.b = 1.0
        marker.color.a = 1.0
        marker.text = 'COLLISION\nbox1'
        return marker


def main(args=None):
    rclpy.init(args=args)
    node = ObjectPlanningDemo()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
