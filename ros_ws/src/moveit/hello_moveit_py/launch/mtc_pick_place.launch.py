import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution
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
        .planning_pipelines(
            pipelines=['ompl', 'chomp', 'pilz_industrial_motion_planner'])
        .robot_description(file_path='config/panda.urdf.xacro')
        .trajectory_execution(
            file_path='config/gripper_moveit_controllers.yaml')
        .to_moveit_configs()
    )
    move_group_capabilities = {
        'capabilities': 'move_group/ExecuteTaskSolutionCapability',
    }
    planning_scene_monitor_parameters = {
        'publish_planning_scene': True,
        'publish_geometry_updates': True,
        'publish_state_updates': True,
        'publish_transforms_updates': True,
        'publish_robot_description': True,
        'publish_robot_description_semantic': True,
    }
    controller_config = os.path.join(
        panda_share, 'config', 'ros2_controllers.yaml')
    rviz_config = PathJoinSubstitution([
        FindPackageShare('moveit_resources_panda_moveit_config'),
        'launch',
        'moveit.rviz',
    ])
    controller_spawners = [
        ExecuteProcess(
            cmd=['ros2', 'run', 'controller_manager', 'spawner', controller],
            output='log',
        )
        for controller in [
            'joint_state_broadcaster',
            'panda_arm_controller',
            'panda_hand_controller',
        ]
    ]

    return LaunchDescription([
        TimerAction(
            period=8.0,
            actions=[
                Node(
                    package='hello_moveit_py',
                    executable='mtc_pick_place',
                    name='python_mtc_pick_place',
                    output='screen',
                    parameters=[moveit_config.to_dict()],
                ),
            ],
        ),
        Node(
            package='hello_moveit_py',
            executable='mtc_scene_setup',
            name='mtc_scene_setup',
            output='screen',
        ),
        Node(
            package='moveit_ros_move_group',
            executable='move_group',
            name='move_group',
            output='screen',
            parameters=[
                moveit_config.to_dict(),
                move_group_capabilities,
                planning_scene_monitor_parameters,
            ],
        ),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[moveit_config.robot_description],
            output='log',
        ),
        Node(
            package='controller_manager',
            executable='ros2_control_node',
            parameters=[controller_config],
            remappings=[
                ('/controller_manager/robot_description',
                 '/robot_description'),
            ],
            output='log',
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config],
            parameters=[
                moveit_config.robot_description,
                moveit_config.robot_description_semantic,
                moveit_config.robot_description_kinematics,
                moveit_config.planning_pipelines,
            ],
            output='log',
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=[
                '--frame-id', 'world', '--child-frame-id', 'panda_link0'],
            output='log',
        ),
        *controller_spawners,
    ])
