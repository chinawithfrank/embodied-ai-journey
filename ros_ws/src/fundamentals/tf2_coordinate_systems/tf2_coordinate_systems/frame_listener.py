import math

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformException, TransformListener


class FrameListener(Node):

    def __init__(self):
        super().__init__('frame_listener')
        self.declare_parameter('target_frame', 'base_link')
        self.declare_parameter('source_frame', 'camera_link')
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)
        self.timer = self.create_timer(1.0, self.lookup_transform)

    def lookup_transform(self):
        target_frame = self.get_parameter('target_frame').value
        source_frame = self.get_parameter('source_frame').value
        try:
            transform = self.buffer.lookup_transform(
                target_frame, source_frame, Time())
        except TransformException as error:
            self.get_logger().info(
                f'Waiting for {source_frame} -> {target_frame}: {error}')
            return

        translation = transform.transform.translation
        rotation = transform.transform.rotation
        yaw = math.atan2(
            2.0 * (rotation.w * rotation.z + rotation.x * rotation.y),
            1.0 - 2.0 * (rotation.y ** 2 + rotation.z ** 2))
        self.get_logger().info(
            f'{source_frame} in {target_frame}: '
            f'x={translation.x:.2f}, y={translation.y:.2f}, '
            f'z={translation.z:.2f}, yaw={yaw:.2f} rad')


def main(args=None):
    rclpy.init(args=args)
    node = FrameListener()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
