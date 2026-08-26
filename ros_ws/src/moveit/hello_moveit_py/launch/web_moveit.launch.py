import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    package_share = get_package_share_directory('hello_moveit_py')
    panda_share = get_package_share_directory(
        'moveit_resources_panda_moveit_config')
    moveit_config = (
        MoveItConfigsBuilder(
            robot_name='panda',
            package_name='moveit_resources_panda_moveit_config',
        )
        .planning_pipelines(pipelines=['ompl'])
        .robot_description(file_path='config/panda.urdf.xacro')
        .trajectory_execution(
            file_path='config/gripper_moveit_controllers.yaml')
        .moveit_cpp(file_path=os.path.join(
            package_share, 'config', 'moveit_py.yaml'))
        .to_moveit_configs()
    )
    controller_config = os.path.join(
        panda_share, 'config', 'ros2_controllers.yaml')
    controller_spawners = [
        ExecuteProcess(
            cmd=['ros2', 'run', 'controller_manager', 'spawner', controller],
            output='screen',
        )
        for controller in [
            'joint_state_broadcaster',
            'panda_arm_controller',
            'panda_hand_controller',
        ]
    ]

    return LaunchDescription([
        Node(
            package='moveit_ros_move_group',
            executable='move_group',
            output='screen',
            parameters=[moveit_config.to_dict()],
        ),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            output='screen',
            parameters=[moveit_config.robot_description],
        ),
        Node(
            package='controller_manager',
            executable='ros2_control_node',
            parameters=[controller_config],
            remappings=[
                ('/controller_manager/robot_description',
                 '/robot_description'),
            ],
            output='screen',
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=[
                '--frame-id', 'world', '--child-frame-id', 'panda_link0'],
            output='screen',
        ),
        Node(
            package='rosbridge_server',
            executable='rosbridge_websocket',
            parameters=[{'port': 9092}],
            output='screen',
        ),
        TimerAction(
            period=5.0,
            actions=[
                Node(
                    package='hello_moveit_py',
                    executable='web_task_executor',
                    output='screen',
                    parameters=[moveit_config.to_dict()],
                ),
            ],
        ),
        *controller_spawners,
    ])
