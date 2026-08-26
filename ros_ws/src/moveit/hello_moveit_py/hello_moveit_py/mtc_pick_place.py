from math import pi, sqrt
import time

from geometry_msgs.msg import PoseStamped, Vector3, Vector3Stamped
from moveit.task_constructor import core, stages
from moveit_msgs.msg import MoveItErrorCodes
import rclcpp

ARM_GROUP = 'panda_arm'
HAND_GROUP = 'hand'
HAND_FRAME = 'panda_hand'
OBJECT_NAME = 'object'
HAND_COLLISION_LINKS = [
    'panda_hand',
    'panda_leftfinger',
    'panda_rightfinger',
]


def frame_pose(frame_id, x=0.0, y=0.0, z=0.0):
    pose = PoseStamped()
    pose.header.frame_id = frame_id
    pose.pose.orientation.w = 1.0
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.position.z = z
    return pose


def grasp_ik_frame():
    pose = frame_pose(HAND_FRAME, z=0.1)
    pose.pose.orientation.x = sqrt(0.5)
    pose.pose.orientation.z = sqrt(0.5)
    pose.pose.orientation.w = 0.0
    return pose


def configure_from_parent(stage, names=None):
    property_source = core.Stage.PropertyInitializerSource.PARENT
    stage.properties.configureInitFrom(property_source, names or [])


def configure_from_interface(stage, names):
    property_source = core.Stage.PropertyInitializerSource.INTERFACE
    stage.properties.configureInitFrom(property_source, names)


def create_task(node):
    task = core.Task()
    task.name = 'tutorial pick and place'
    task.loadRobotModel(node)
    task.properties['group'] = ARM_GROUP
    task.properties['eef'] = HAND_GROUP
    task.properties['ik_frame'] = HAND_FRAME

    task.add(stages.CurrentState('current state'))

    sampling_planner = core.PipelinePlanner(node)
    interpolation_planner = core.JointInterpolationPlanner()
    cartesian_planner = core.CartesianPath()
    cartesian_planner.max_velocity_scaling_factor = 1.0
    cartesian_planner.max_acceleration_scaling_factor = 1.0
    cartesian_planner.step_size = 0.01

    open_hand = stages.MoveTo('open hand', interpolation_planner)
    open_hand.group = HAND_GROUP
    open_hand.setGoal('open')
    task.add(open_hand)

    move_to_pick = stages.Connect(
        'move to pick', [(ARM_GROUP, sampling_planner)])
    move_to_pick.timeout = 5.0
    configure_from_parent(move_to_pick)
    task.add(move_to_pick)

    grasp = core.SerialContainer('pick object')
    task.properties.exposeTo(
        grasp.properties, ['eef', 'group', 'ik_frame'])
    configure_from_parent(grasp, ['eef', 'group', 'ik_frame'])

    approach = stages.MoveRelative('approach object', cartesian_planner)
    approach.marker_ns = 'approach_object'
    approach.properties['link'] = HAND_FRAME
    configure_from_parent(approach, ['group'])
    approach.min_distance = 0.1
    approach.max_distance = 0.15
    approach_direction = Vector3Stamped()
    approach_direction.header.frame_id = HAND_FRAME
    approach_direction.vector = Vector3(z=1.0)
    approach.setDirection(approach_direction)
    grasp.add(approach)

    grasp_generator = stages.GenerateGraspPose('generate grasp pose')
    configure_from_parent(grasp_generator)
    grasp_generator.marker_ns = 'grasp_pose'
    grasp_generator.pregrasp = 'open'
    grasp_generator.object = OBJECT_NAME
    grasp_generator.angle_delta = pi / 12.0
    grasp_generator.setMonitoredStage(task['current state'])

    grasp_ik = stages.ComputeIK('grasp pose IK', grasp_generator)
    grasp_ik.max_ik_solutions = 8
    grasp_ik.min_solution_distance = 1.0
    grasp_ik.ik_frame = grasp_ik_frame()
    configure_from_parent(grasp_ik, ['eef', 'group'])
    configure_from_interface(grasp_ik, ['target_pose'])
    grasp.add(grasp_ik)

    allow_collision = stages.ModifyPlanningScene(
        'allow collision (hand, object)')
    allow_collision.allowCollisions(
        OBJECT_NAME, HAND_COLLISION_LINKS, True)
    grasp.add(allow_collision)

    close_hand = stages.MoveTo('close hand', interpolation_planner)
    close_hand.group = HAND_GROUP
    close_hand.setGoal('close')
    grasp.add(close_hand)

    attach_object = stages.ModifyPlanningScene('attach object')
    attach_object.attachObject(OBJECT_NAME, HAND_FRAME)
    grasp.add(attach_object)

    lift = stages.MoveRelative('lift object', cartesian_planner)
    configure_from_parent(lift, ['group'])
    lift.ik_frame = frame_pose(HAND_FRAME)
    lift.marker_ns = 'lift_object'
    lift.min_distance = 0.1
    lift.max_distance = 0.3
    lift_direction = Vector3Stamped()
    lift_direction.header.frame_id = 'world'
    lift_direction.vector = Vector3(z=1.0)
    lift.setDirection(lift_direction)
    grasp.add(lift)
    task.add(grasp)

    move_to_place = stages.Connect(
        'move to place',
        [
            (ARM_GROUP, sampling_planner),
            (HAND_GROUP, interpolation_planner),
        ],
    )
    move_to_place.timeout = 5.0
    configure_from_parent(move_to_place)
    task.add(move_to_place)

    place = core.SerialContainer('place object')
    task.properties.exposeTo(
        place.properties, ['eef', 'group', 'ik_frame'])
    configure_from_parent(place, ['eef', 'group', 'ik_frame'])

    place_generator = stages.GeneratePlacePose('generate place pose')
    configure_from_parent(place_generator)
    place_generator.marker_ns = 'place_pose'
    place_generator.object = OBJECT_NAME
    place_target = frame_pose(OBJECT_NAME, y=0.5)
    place_generator.pose = place_target
    place_generator.setMonitoredStage(task['pick object']['attach object'])

    place_ik = stages.ComputeIK('place pose IK', place_generator)
    place_ik.max_ik_solutions = 2
    place_ik.min_solution_distance = 1.0
    place_ik.ik_frame = frame_pose(OBJECT_NAME)
    configure_from_parent(place_ik, ['eef', 'group'])
    configure_from_interface(place_ik, ['target_pose'])
    place.add(place_ik)

    open_hand_after_place = stages.MoveTo('open hand after place', interpolation_planner)
    open_hand_after_place.group = HAND_GROUP
    open_hand_after_place.setGoal('open')
    place.add(open_hand_after_place)

    forbid_collision = stages.ModifyPlanningScene(
        'forbid collision (hand, object)')
    forbid_collision.allowCollisions(
        OBJECT_NAME, HAND_COLLISION_LINKS, False)
    place.add(forbid_collision)

    detach_object = stages.ModifyPlanningScene('detach object')
    detach_object.detachObject(OBJECT_NAME, HAND_FRAME)
    place.add(detach_object)

    retreat = stages.MoveRelative('retreat', cartesian_planner)
    configure_from_parent(retreat, ['group'])
    retreat.ik_frame = frame_pose(HAND_FRAME)
    retreat.marker_ns = 'retreat'
    retreat.min_distance = 0.1
    retreat.max_distance = 0.3
    retreat_direction = Vector3Stamped()
    retreat_direction.header.frame_id = 'world'
    retreat_direction.vector = Vector3(x=-0.5)
    retreat.setDirection(retreat_direction)
    place.add(retreat)
    task.add(place)

    return_home = stages.MoveTo('return home', interpolation_planner)
    configure_from_parent(return_home, ['group'])
    return_home.setGoal('ready')
    task.add(return_home)
    return task


def main(args=None):
    rclcpp.init(args=args)
    node_options = rclcpp.NodeOptions()
    node_options.automatically_declare_parameters_from_overrides = True
    node = rclcpp.Node('python_mtc_pick_place', node_options)

    task = create_task(node)
    if task.plan(5):
        task.publish(task.solutions[0])
        print('MTC found a solution and is sending it to the mock controller.')
        result = task.execute(task.solutions[0])
        if result.val == MoveItErrorCodes.SUCCESS:
            print('MTC pick-and-place execution completed successfully.')
        else:
            print(f'MTC task execution failed with code: {result.val}')
    else:
        print('MTC could not find a pick-and-place solution.')

    try:
        time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        rclcpp.shutdown()


if __name__ == '__main__':
    main()
