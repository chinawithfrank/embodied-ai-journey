import math

import rclpy
from geometry_msgs.msg import TransformStamped
from rclpy.node import Node
from tf2_ros import TransformBroadcaster


class DynamicFrameBroadcaster(Node):

    def __init__(self):
        super().__init__('dynamic_frame_broadcaster')
        self.declare_parameter('parent_frame', 'base_link')
        self.declare_parameter('child_frame', 'camera_link')
        self.declare_parameter('radius', 0.5)
        self.declare_parameter('height', 0.2)
        self.declare_parameter('angular_speed', 0.5)
        self.broadcaster = TransformBroadcaster(self)
        self.start_time = self.get_clock().now()
        self.timer = self.create_timer(0.1, self.broadcast_transform)

    def broadcast_transform(self):
        elapsed = (self.get_clock().now() - self.start_time).nanoseconds / 1e9
        angle = self.get_parameter('angular_speed').value * elapsed
        transform = TransformStamped()
        transform.header.stamp = self.get_clock().now().to_msg()
        transform.header.frame_id = self.get_parameter('parent_frame').value
        transform.child_frame_id = self.get_parameter('child_frame').value
        transform.transform.translation.x = (
            self.get_parameter('radius').value * math.cos(angle))
        transform.transform.translation.y = (
            self.get_parameter('radius').value * math.sin(angle))
        transform.transform.translation.z = self.get_parameter('height').value
        transform.transform.rotation.z = math.sin(angle / 2.0)
        transform.transform.rotation.w = math.cos(angle / 2.0)
        self.broadcaster.sendTransform(transform)


def main(args=None):
    rclpy.init(args=args)
    node = DynamicFrameBroadcaster()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
