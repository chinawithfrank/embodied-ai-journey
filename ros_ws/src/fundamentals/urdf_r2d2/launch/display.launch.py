import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory('urdf_r2d2')
    urdf_path = os.path.join(package_share, 'urdf', 'r2d2.urdf.xml')
    rviz_path = os.path.join(package_share, 'rviz', 'r2d2.rviz')
    with open(urdf_path, encoding='utf-8') as urdf_file:
        robot_description = urdf_file.read()

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
        ),
        Node(
            package='urdf_r2d2',
            executable='state_publisher',
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_path],
        ),
    ])
