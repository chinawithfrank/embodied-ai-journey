import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import QoSProfile
from visualization_msgs.msg import Marker


class BasicShapesPublisher(Node):

    def __init__(self):
        super().__init__('basic_shapes')
        self.publisher = self.create_publisher(
            Marker, 'visualization_marker', QoSProfile(depth=1))
        self.shapes = [
            Marker.CUBE,
            Marker.SPHERE,
            Marker.ARROW,
            Marker.CYLINDER,
        ]
        self.shape_index = 0
        self.timer = self.create_timer(1.0, self.publish_marker)
        self.get_logger().info(
            'Publishing basic shapes on /visualization_marker')

    def publish_marker(self):
        marker = Marker()
        marker.header.frame_id = 'my_frame'
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = 'basic_shapes'
        marker.id = 0
        marker.type = self.shapes[self.shape_index]
        marker.action = Marker.ADD
        marker.pose.orientation.w = 1.0
        marker.scale.x = 1.0
        marker.scale.y = 1.0
        marker.scale.z = 1.0
        marker.color.g = 1.0
        marker.color.a = 1.0
        marker.lifetime = Duration(seconds=0.0).to_msg()
        self.publisher.publish(marker)
        self.shape_index = (self.shape_index + 1) % len(self.shapes)


def main(args=None):
    rclpy.init(args=args)
    node = BasicShapesPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
