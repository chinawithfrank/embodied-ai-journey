from geometry_msgs.msg import Pose
from moveit_msgs.msg import CollisionObject, PlanningScene
from moveit_msgs.srv import ApplyPlanningScene
import rclpy
from rclpy.node import Node
from shape_msgs.msg import SolidPrimitive

OBJECT_NAME = 'object'


class MtcSceneSetup(Node):

    def __init__(self):
        super().__init__('mtc_scene_setup')
        self.client = self.create_client(
            ApplyPlanningScene, '/apply_planning_scene')
        self.request_sent = False
        self.timer = self.create_timer(0.5, self.add_object)

    def create_object(self):
        collision_object = CollisionObject()
        collision_object.id = OBJECT_NAME
        collision_object.header.frame_id = 'world'

        cylinder = SolidPrimitive()
        cylinder.type = SolidPrimitive.CYLINDER
        cylinder.dimensions = [0.10, 0.02]

        pose = Pose()
        pose.orientation.w = 1.0
        pose.position.x = 0.5
        pose.position.y = -0.25
        pose.position.z = 0.0

        collision_object.primitives.append(cylinder)
        collision_object.primitive_poses.append(pose)
        collision_object.operation = CollisionObject.ADD
        return collision_object

    def add_object(self):
        if self.request_sent:
            return

        if not self.client.service_is_ready():
            self.get_logger().info(
                'Waiting for MoveIt apply_planning_scene service...')
            return

        request = ApplyPlanningScene.Request()
        request.scene = PlanningScene()
        request.scene.is_diff = True
        request.scene.world.collision_objects.append(self.create_object())
        self.request_sent = True
        future = self.client.call_async(request)
        future.add_done_callback(self.handle_response)

    def handle_response(self, future):
        try:
            response = future.result()
        except Exception as error:
            self.get_logger().error(
                f'Could not add {OBJECT_NAME}: {error}')
            self.request_sent = False
            return

        if response.success:
            self.timer.cancel()
            self.get_logger().info(
                'MTC object is active in the MoveIt Planning Scene.')
        else:
            self.get_logger().error(
                'MoveIt rejected the MTC collision object.')
            self.request_sent = False


def main(args=None):
    rclpy.init(args=args)
    node = MtcSceneSetup()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
