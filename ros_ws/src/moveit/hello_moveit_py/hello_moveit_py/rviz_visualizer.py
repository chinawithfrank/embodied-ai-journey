from geometry_msgs.msg import Point, PoseStamped
from moveit_msgs.msg import DisplayTrajectory
import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from std_srvs.srv import Trigger
from visualization_msgs.msg import Marker, MarkerArray

from moveit.planning import MoveItPy

BASE_FRAME = 'panda_link0'
END_EFFECTOR_LINK = 'panda_link8'
MARKER_TOPIC = '/rviz_visual_tools'
TRAJECTORY_TOPIC = '/display_planned_path'


class RvizVisualizer(Node):

    def __init__(self):
        super().__init__('python_rviz_visualizer')
        marker_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.marker_publisher = self.create_publisher(
            MarkerArray, MARKER_TOPIC, marker_qos)
        self.trajectory_publisher = self.create_publisher(
            DisplayTrajectory, TRAJECTORY_TOPIC, marker_qos)
        self.moveit_py = MoveItPy(node_name='python_rviz_visualizer')
        self.panda_arm = self.moveit_py.get_planning_component('panda_arm')
        self.plan_result = None
        self.target_pose = self.create_target_pose()

        self.create_service(Trigger, '~/show_goal', self.show_goal)
        self.create_service(Trigger, '~/plan', self.plan)
        self.create_service(Trigger, '~/execute', self.execute)

        self.publish_visuals('Python RViz visualization demo is ready')
        self.get_logger().info(
            'Call show_goal, plan, then execute through ROS 2 services.')

    def create_target_pose(self):
        target_pose = PoseStamped()
        target_pose.header.frame_id = BASE_FRAME
        target_pose.pose.orientation.w = 1.0
        target_pose.pose.position.x = 0.28
        target_pose.pose.position.y = -0.20
        target_pose.pose.position.z = 0.50
        return target_pose

    def show_goal(self, request, response):
        del request
        self.publish_visuals('1. Goal pose: inspect the sphere and axes')
        response.success = True
        response.message = 'Goal pose markers are visible in RViz.'
        return response

    def plan(self, request, response):
        del request
        self.publish_visuals('2. Planning trajectory')
        self.panda_arm.set_start_state_to_current_state()
        self.panda_arm.set_goal_state(
            pose_stamped_msg=self.target_pose,
            pose_link=END_EFFECTOR_LINK,
        )
        self.plan_result = self.panda_arm.plan()

        if not self.plan_result:
            self.publish_visuals('Planning failed: choose a different goal')
            response.success = False
            response.message = 'MoveIt could not find a trajectory.'
            return response

        display_trajectory = DisplayTrajectory()
        display_trajectory.trajectory.append(
            self.plan_result.trajectory.get_robot_trajectory_msg())
        self.trajectory_publisher.publish(display_trajectory)
        self.publish_visuals('3. Plan ready: inspect it, then call execute')
        response.success = True
        response.message = 'Published the planned trajectory to RViz.'
        return response

    def execute(self, request, response):
        del request
        if not self.plan_result:
            response.success = False
            response.message = 'Call the plan service before execute.'
            return response

        self.publish_visuals('4. Executing the inspected trajectory')
        self.moveit_py.execute(self.plan_result.trajectory, controllers=[])
        self.plan_result = None
        self.publish_visuals('Execution complete')
        response.success = True
        response.message = 'Mock controller executed the planned trajectory.'
        return response

    def publish_visuals(self, title):
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
        ]
        self.marker_publisher.publish(MarkerArray(markers=markers))

    def create_title_marker(self, title, timestamp):
        marker = Marker()
        marker.header.frame_id = BASE_FRAME
        marker.header.stamp = timestamp
        marker.ns = 'python_visualization'
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
        marker.ns = 'python_visualization'
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

    def create_axis_marker(self, marker_id, timestamp, color, offset):
        marker = Marker()
        marker.header = self.target_pose.header
        marker.header.stamp = timestamp
        marker.ns = 'python_visualization'
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
        end = Point(
            x=start.x + offset[0],
            y=start.y + offset[1],
            z=start.z + offset[2],
        )
        marker.points = [start, end]
        return marker


def main(args=None):
    rclpy.init(args=args)
    node = RvizVisualizer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
