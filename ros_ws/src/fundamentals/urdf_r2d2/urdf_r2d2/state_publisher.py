from math import cos, pi, sin

import rclpy
from geometry_msgs.msg import Quaternion, TransformStamped
from rclpy.node import Node
from rclpy.qos import QoSProfile
from sensor_msgs.msg import JointState
from tf2_ros import TransformBroadcaster


class StatePublisher(Node):

    def __init__(self):
        super().__init__('state_publisher')
        qos_profile = QoSProfile(depth=10)
        self.joint_pub = self.create_publisher(
            JointState, 'joint_states', qos_profile)
        self.broadcaster = TransformBroadcaster(self, qos=qos_profile)
        self.degree = pi / 180.0
        self.tilt = 0.0
        self.tilt_increment = self.degree
        self.swivel = 0.0
        self.angle = 0.0
        self.height = 0.0
        self.height_increment = 0.005
        self.odom_transform = TransformStamped()
        self.odom_transform.header.frame_id = 'odom'
        self.odom_transform.child_frame_id = 'axis'
        self.joint_state = JointState()
        self.joint_state.name = ['swivel', 'tilt', 'periscope']
        self.timer = self.create_timer(1.0 / 30.0, self.publish_state)
        self.get_logger().info(f'{self.get_name()} started')

    def publish_state(self):
        now = self.get_clock().now().to_msg()
        self.joint_state.header.stamp = now
        self.joint_state.position = [self.swivel, self.tilt, self.height]
        self.odom_transform.header.stamp = now
        self.odom_transform.transform.translation.x = cos(self.angle) * 2.0
        self.odom_transform.transform.translation.y = sin(self.angle) * 2.0
        self.odom_transform.transform.translation.z = 0.7
        self.odom_transform.transform.rotation = euler_to_quaternion(
            0.0, 0.0, self.angle + pi / 2.0)
        self.joint_pub.publish(self.joint_state)
        self.broadcaster.sendTransform(self.odom_transform)
        self.tilt += self.tilt_increment
        if self.tilt < -0.5 or self.tilt > 0.0:
            self.tilt_increment *= -1.0
        self.height += self.height_increment
        if self.height > 0.2 or self.height < 0.0:
            self.height_increment *= -1.0
        self.swivel += self.degree
        self.angle += self.degree / 4.0


def euler_to_quaternion(roll, pitch, yaw):
    qx = (
        sin(roll / 2.0) * cos(pitch / 2.0) * cos(yaw / 2.0)
        - cos(roll / 2.0) * sin(pitch / 2.0) * sin(yaw / 2.0))
    qy = (
        cos(roll / 2.0) * sin(pitch / 2.0) * cos(yaw / 2.0)
        + sin(roll / 2.0) * cos(pitch / 2.0) * sin(yaw / 2.0))
    qz = (
        cos(roll / 2.0) * cos(pitch / 2.0) * sin(yaw / 2.0)
        - sin(roll / 2.0) * sin(pitch / 2.0) * cos(yaw / 2.0))
    qw = (
        cos(roll / 2.0) * cos(pitch / 2.0) * cos(yaw / 2.0)
        + sin(roll / 2.0) * sin(pitch / 2.0) * sin(yaw / 2.0))
    return Quaternion(x=qx, y=qy, z=qz, w=qw)


def main(args=None):
    rclpy.init(args=args)
    node = StatePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
