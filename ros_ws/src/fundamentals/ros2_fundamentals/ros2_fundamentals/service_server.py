import rclpy
from rclpy.node import Node
from std_srvs.srv import SetBool


class MotorService(Node):

    def __init__(self):
        super().__init__('motor_service')
        self.enabled = False
        self.service = self.create_service(
            SetBool, 'set_motors_enabled', self.set_motors_callback)
        self.get_logger().info('Service ready: /set_motors_enabled')

    def set_motors_callback(self, request, response):
        self.enabled = request.data
        state = 'enabled' if self.enabled else 'disabled'
        response.success = True
        response.message = f'Motors are {state}.'
        self.get_logger().info(response.message)
        return response


def main(args=None):
    rclpy.init(args=args)
    node = MotorService()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
