import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from turtlesim.action import RotateAbsolute


class RotateTurtleClient(Node):

    def __init__(self):
        super().__init__('rotate_turtle_client')
        self.declare_parameter('theta', 1.57)
        self.action_client = ActionClient(
            self, RotateAbsolute, '/turtle1/rotate_absolute')

    def send_goal(self):
        theta = self.get_parameter('theta').value
        if not self.action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('Action server is unavailable.')
            return None

        goal = RotateAbsolute.Goal()
        goal.theta = theta
        self.get_logger().info(f'Rotating turtle to {theta:.2f} radians.')
        future = self.action_client.send_goal_async(
            goal, feedback_callback=self.feedback_callback)
        future.add_done_callback(self.goal_response_callback)
        return future

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected.')
            rclpy.shutdown()
            return

        self.get_logger().info('Goal accepted.')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def feedback_callback(self, feedback_message):
        remaining = feedback_message.feedback.remaining
        self.get_logger().info(f'Remaining rotation: {remaining:.2f}')

    def result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'Final angle: {result.delta:.2f} radians.')
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = RotateTurtleClient()
    try:
        goal_future = node.send_goal()
        if goal_future is not None:
            rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
