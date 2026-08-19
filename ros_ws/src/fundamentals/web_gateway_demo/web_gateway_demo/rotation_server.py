from time import sleep

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from turtlesim.action import RotateAbsolute


class HeadlessRotationServer(Node):
    """A GUI-free Action server compatible with turtlesim RotateAbsolute."""

    def __init__(self):
        super().__init__('headless_rotation_server')
        self.current_theta = 0.0
        self.action_server = ActionServer(
            self,
            RotateAbsolute,
            '/turtle1/rotate_absolute',
            self.execute_callback,
        )
        self.get_logger().info(
            'Headless rotation Action ready: /turtle1/rotate_absolute')

    def execute_callback(self, goal_handle):
        target_theta = goal_handle.request.theta
        starting_theta = self.current_theta
        delta = target_theta - starting_theta
        steps = 30

        for step in range(steps + 1):
            if goal_handle.is_cancel_requested:
                result = RotateAbsolute.Result()
                result.delta = delta * step / steps
                goal_handle.canceled()
                self.get_logger().info('Rotation goal cancelled.')
                return result

            feedback = RotateAbsolute.Feedback()
            feedback.remaining = delta * (1.0 - step / steps)
            goal_handle.publish_feedback(feedback)
            sleep(0.1)

        self.current_theta = target_theta
        result = RotateAbsolute.Result()
        result.delta = delta
        goal_handle.succeed()
        self.get_logger().info(f'Rotation goal completed: {target_theta:.2f} rad.')
        return result


def main(args=None):
    rclpy.init(args=args)
    node = HeadlessRotationServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
