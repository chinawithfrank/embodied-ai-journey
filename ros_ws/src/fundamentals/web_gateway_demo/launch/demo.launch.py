import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    robot_share = get_package_share_directory('urdf_r2d2')
    urdf_path = os.path.join(robot_share, 'urdf', 'r2d2.urdf.xml')

    with open(urdf_path, encoding='utf-8') as urdf_file:
        robot_description = urdf_file.read()

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
        ),
        Node(package='urdf_r2d2', executable='state_publisher'),
        Node(package='rviz_markers', executable='points_and_lines'),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=[
                '--x', '0', '--y', '0', '--z', '0',
                '--roll', '0', '--pitch', '0', '--yaw', '0',
                '--frame-id', 'odom', '--child-frame-id', 'my_frame',
            ],
        ),
        Node(package='ros2_fundamentals', executable='service_server'),
        Node(package='web_gateway_demo', executable='rotation_server'),
    ])
