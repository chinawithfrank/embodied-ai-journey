import select
import sys
import termios
import tty

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

HELP = """
Control turtlesim with the keyboard.
---------------------------
   w : forward
   x : backward
   a : turn left
   d : turn right
   s : stop
   q : quit
---------------------------
CTRL-C also quits.
"""

MOVE_BINDINGS = {
    'w': (1.0, 0.0),
    'x': (-1.0, 0.0),
    'a': (0.0, 1.0),
    'd': (0.0, -1.0),
    's': (0.0, 0.0),
}

LINEAR_SPEED = 2.0
ANGULAR_SPEED = 2.0


def get_key(settings):
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    key = sys.stdin.read(1) if rlist else ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def main(args=None):
    settings = termios.tcgetattr(sys.stdin)

    rclpy.init(args=args)
    node = Node('keyboard_teleop')
    publisher = node.create_publisher(Twist, '/turtle1/cmd_vel', 10)

    print(HELP)

    try:
        while rclpy.ok():
            key = get_key(settings)
            if key == 'q' or key == '\x03':  # q or CTRL-C
                break
            if key in MOVE_BINDINGS:
                linear, angular = MOVE_BINDINGS[key]
                twist = Twist()
                twist.linear.x = linear * LINEAR_SPEED
                twist.angular.z = angular * ANGULAR_SPEED
                publisher.publish(twist)
    finally:
        publisher.publish(Twist())  # stop the turtle before exiting
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
