import math

import rclpy
from geometry_msgs.msg import TransformStamped
from rclpy.node import Node
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster


class StaticFrameBroadcaster(Node):

    def __init__(self):
        super().__init__('static_frame_broadcaster')
        self.declare_parameter('parent_frame', 'base_link')
        self.declare_parameter('child_frame', 'laser_link')
        self.declare_parameter('x', 0.2)
        self.declare_parameter('y', 0.0)
        self.declare_parameter('z', 0.1)
        self.declare_parameter('yaw', 0.0)
        self.broadcaster = StaticTransformBroadcaster(self)
        self.broadcast_transform()

    def broadcast_transform(self):
        yaw = self.get_parameter('yaw').value
        transform = TransformStamped()
        transform.header.stamp = self.get_clock().now().to_msg()
        transform.header.frame_id = self.get_parameter('parent_frame').value
        transform.child_frame_id = self.get_parameter('child_frame').value
        transform.transform.translation.x = self.get_parameter('x').value
        transform.transform.translation.y = self.get_parameter('y').value
        transform.transform.translation.z = self.get_parameter('z').value
        transform.transform.rotation.z = math.sin(yaw / 2.0)
        transform.transform.rotation.w = math.cos(yaw / 2.0)
        self.broadcaster.sendTransform(transform)
        self.get_logger().info(
            f'Published static transform: {transform.header.frame_id} -> '
            f'{transform.child_frame_id}')


def main(args=None):
    rclpy.init(args=args)
    node = StaticFrameBroadcaster()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
