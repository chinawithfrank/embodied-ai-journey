import rclpy
from rcl_interfaces.msg import SetParametersResult
from rclpy.node import Node


class ParameterExample(Node):

    def __init__(self):
        super().__init__('parameter_example')
        self.declare_parameter('robot_name', 'turtlebot')
        self.declare_parameter('publish_period', 1.0)
        self.add_on_set_parameters_callback(self.validate_parameters)
        self.add_post_set_parameters_callback(self.apply_parameters)
        self.timer = None
        self.create_publish_timer(self.get_parameter('publish_period').value)

    def validate_parameters(self, parameters):
        for parameter in parameters:
            if parameter.name == 'robot_name' and not parameter.value:
                return SetParametersResult(
                    successful=False, reason='robot_name cannot be empty.')
            if parameter.name == 'publish_period' and parameter.value <= 0.0:
                return SetParametersResult(
                    successful=False,
                    reason='publish_period must be positive.')
        return SetParametersResult(successful=True)

    def apply_parameters(self, parameters):
        for parameter in parameters:
            if parameter.name == 'publish_period':
                self.create_publish_timer(parameter.value)

    def create_publish_timer(self, period):
        if self.timer is not None:
            self.destroy_timer(self.timer)
        self.timer = self.create_timer(period, self.timer_callback)
        self.get_logger().info(f'publish_period set to {period:.2f} seconds.')

    def timer_callback(self):
        robot_name = self.get_parameter('robot_name').value
        self.get_logger().info(f'Hello from {robot_name}.')


def main(args=None):
    rclpy.init(args=args)
    node = ParameterExample()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
