from math import cos, pi, sin

import rclpy
from geometry_msgs.msg import Point
from rclpy.node import Node
from rclpy.qos import QoSProfile
from visualization_msgs.msg import Marker


class PointsAndLinesPublisher(Node):

    def __init__(self):
        super().__init__('points_and_lines')
        self.publisher = self.create_publisher(
            Marker, 'visualization_marker', QoSProfile(depth=10))
        self.phase = 0.0
        self.timer = self.create_timer(1.0 / 30.0, self.publish_markers)
        self.get_logger().info(
            'Publishing points and lines on /visualization_marker')

    def publish_markers(self):
        now = self.get_clock().now().to_msg()
        points = self.create_marker(Marker.POINTS, 0, now)
        line_strip = self.create_marker(Marker.LINE_STRIP, 1, now)
        line_list = self.create_marker(Marker.LINE_LIST, 2, now)
        points.scale.x = 0.2
        points.scale.y = 0.2
        points.color.g = 1.0
        points.color.a = 1.0
        line_strip.scale.x = 0.1
        line_strip.color.b = 1.0
        line_strip.color.a = 1.0
        line_list.scale.x = 0.1
        line_list.color.r = 1.0
        line_list.color.a = 1.0

        for point_index in range(100):
            angle = self.phase + point_index / 100.0 * 2.0 * pi
            point = Point(
                x=float(point_index - 50),
                y=5.0 * sin(angle),
                z=5.0 * cos(angle),
            )
            points.points.append(point)
            line_strip.points.append(point)
            line_list.points.append(point)
            line_list.points.append(
                Point(x=point.x, y=point.y, z=point.z + 1.0))

        self.publisher.publish(points)
        self.publisher.publish(line_strip)
        self.publisher.publish(line_list)
        self.phase += 0.04

    def create_marker(self, marker_type, marker_id, stamp):
        marker = Marker()
        marker.header.frame_id = 'my_frame'
        marker.header.stamp = stamp
        marker.ns = 'points_and_lines'
        marker.id = marker_id
        marker.type = marker_type
        marker.action = Marker.ADD
        marker.pose.orientation.w = 1.0
        return marker


def main(args=None):
    rclpy.init(args=args)
    node = PointsAndLinesPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
