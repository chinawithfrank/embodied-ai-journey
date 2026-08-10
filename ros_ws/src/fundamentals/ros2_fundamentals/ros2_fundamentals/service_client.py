import rclpy
from rclpy.node import Node
from std_srvs.srv import SetBool


class MotorClient(Node):

    def __init__(self):
        super().__init__('motor_client')
        self.declare_parameter('enabled', True)
        self.client = self.create_client(SetBool, 'set_motors_enabled')

    def send_request(self):
        enabled = self.get_parameter('enabled').value
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Service unavailable, waiting again...')

        request = SetBool.Request()
        request.data = enabled
        self.future = self.client.call_async(request)


def main(args=None):
    rclpy.init(args=args)
    node = MotorClient()
    node.send_request()
    rclpy.spin_until_future_complete(node, node.future)

    try:
        response = node.future.result()
        node.get_logger().info(
            f'Success: {response.success}, message: {response.message}')
    except Exception as error:
        node.get_logger().error(f'Service call failed: {error}')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
