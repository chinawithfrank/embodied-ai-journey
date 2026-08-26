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
    # Task 是整次抓取放置的总容器；所有子阶段按加入顺序组成任务树。
    task = core.Task()
    task.name = 'tutorial pick and place'
    # 从 launch 传入的 robot_description 中加载 Panda 的 URDF、SRDF 和运动学配置。
    task.loadRobotModel(node)
    # 把后续阶段反复使用的名称存为任务属性，子容器可以继承它们。
    task.properties['group'] = ARM_GROUP
    task.properties['eef'] = HAND_GROUP
    task.properties['ik_frame'] = HAND_FRAME

    # 读取当前 /joint_states 和规划场景，作为整条任务的起始机器人状态。
    task.add(stages.CurrentState('current state'))

    # 三类规划器分别负责：避障自由运动、简单关节动作、
    # 以及末端直线笛卡尔运动。
    sampling_planner = core.PipelinePlanner(node)
    interpolation_planner = core.JointInterpolationPlanner()
    cartesian_planner = core.CartesianPath()
    # 教程要求笛卡尔动作以全速运行，每两个轨迹点最多相距 1 厘米。
    cartesian_planner.max_velocity_scaling_factor = 1.0
    cartesian_planner.max_acceleration_scaling_factor = 1.0
    cartesian_planner.step_size = 0.01

    # 先把手爪张开，确保机械臂靠近圆柱时处于可抓取状态。
    open_hand = stages.MoveTo('open hand', interpolation_planner)
    open_hand.group = HAND_GROUP
    open_hand.setGoal('open')
    task.add(open_hand)

    # 用 OMPL 把“当前手臂姿态”连接到后面生成的任意一个可抓取姿态。
    move_to_pick = stages.Connect(
        'move to pick', [(ARM_GROUP, sampling_planner)])
    # Connect 默认只有 1 秒；教程明确给自由空间连接 5 秒。
    move_to_pick.timeout = 5.0
    # 继承 task 的 group、eef、ik_frame 等公共属性。
    configure_from_parent(move_to_pick)
    task.add(move_to_pick)

    # 抓取不是一个动作，而是一串必须连续成功的子阶段。
    grasp = core.SerialContainer('pick object')
    # 让抓取容器能使用任务顶层定义的手臂、手爪和末端坐标系。
    task.properties.exposeTo(
        grasp.properties, ['eef', 'group', 'ik_frame'])
    configure_from_parent(grasp, ['eef', 'group', 'ik_frame'])

    # 从预抓取位姿沿 panda_hand 的正 Z 方向直线靠近物体。
    approach = stages.MoveRelative('approach object', cartesian_planner)
    # marker_ns 只影响 RViz 中这段轨迹的显示分组。
    approach.marker_ns = 'approach_object'
    # 指定被直线移动的末端链接，并继承手臂规划组。
    approach.properties['link'] = HAND_FRAME
    configure_from_parent(approach, ['group'])
    # 必须至少靠近 10 厘米，最多移动 15 厘米，
    # 避免“几乎没动”也算成功。
    approach.min_distance = 0.1
    approach.max_distance = 0.15
    approach_direction = Vector3Stamped()
    approach_direction.header.frame_id = HAND_FRAME
    approach_direction.vector = Vector3(z=1.0)
    approach.setDirection(approach_direction)
    grasp.add(approach)

    # 围绕圆柱采样多个抓取方向，而不是把抓取姿态写死为一个值。
    grasp_generator = stages.GenerateGraspPose('generate grasp pose')
    configure_from_parent(grasp_generator)
    grasp_generator.marker_ns = 'grasp_pose'
    # 采样抓取姿态时，手爪应保持 open；目标物体是场景中的 object。
    grasp_generator.pregrasp = 'open'
    grasp_generator.object = OBJECT_NAME
    # 每隔 15° 采样一次，角度越小，候选越多、规划也越慢。
    grasp_generator.angle_delta = pi / 12.0
    # 从任务起始场景取得圆柱的形状和初始位姿。
    grasp_generator.setMonitoredStage(task['current state'])

    # 对每个抓取候选求逆运动学，得到真正可由 Panda 关节达到的抓取姿态。
    grasp_ik = stages.ComputeIK('grasp pose IK', grasp_generator)
    # 最多保留 8 个差异足够大的关节解，避免大量近似重复解。
    grasp_ik.max_ik_solutions = 8
    grasp_ik.min_solution_distance = 1.0
    # TCP 位于两指中间，并使用教程给定的末端朝向和 10 厘米偏移。
    grasp_ik.ik_frame = grasp_ik_frame()
    configure_from_parent(grasp_ik, ['eef', 'group'])
    # target_pose 由 GenerateGraspPose 写入接口状态，再传给 IK 求解器。
    configure_from_interface(grasp_ik, ['target_pose'])
    grasp.add(grasp_ik)

    # 接触物体前临时允许手爪与圆柱碰撞，否则闭爪会被碰撞检查拒绝。
    allow_collision = stages.ModifyPlanningScene(
        'allow collision (hand, object)')
    allow_collision.allowCollisions(
        OBJECT_NAME, HAND_COLLISION_LINKS, True)
    grasp.add(allow_collision)

    # 将手爪从 open 命名姿态移动到 close 命名姿态，夹住圆柱。
    close_hand = stages.MoveTo('close hand', interpolation_planner)
    close_hand.group = HAND_GROUP
    close_hand.setGoal('close')
    grasp.add(close_hand)

    # 把 object 从世界障碍物变为 panda_hand 的附着物；之后它会随手运动。
    attach_object = stages.ModifyPlanningScene('attach object')
    attach_object.attachObject(OBJECT_NAME, HAND_FRAME)
    grasp.add(attach_object)

    # 抓住后沿世界坐标系正 Z 方向抬起物体，给后续搬运留出空间。
    lift = stages.MoveRelative('lift object', cartesian_planner)
    configure_from_parent(lift, ['group'])
    # IK 参考仍是手坐标系；这里不额外偏移末端。
    lift.ik_frame = frame_pose(HAND_FRAME)
    lift.marker_ns = 'lift_object'
    lift.min_distance = 0.1
    lift.max_distance = 0.3
    lift_direction = Vector3Stamped()
    lift_direction.header.frame_id = 'world'
    lift_direction.vector = Vector3(z=1.0)
    lift.setDirection(lift_direction)
    grasp.add(lift)
    # 至此 pick object 的全部子阶段完成，将整个串行容器加入总任务。
    task.add(grasp)

    # 把抓取后的状态连接到放置候选：手臂用 OMPL 避障，
    # 手爪用关节插值处理开合状态。
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

    # 放置同样由多个不可拆开的连续步骤组成。
    place = core.SerialContainer('place object')
    task.properties.exposeTo(
        place.properties, ['eef', 'group', 'ik_frame'])
    configure_from_parent(place, ['eef', 'group', 'ik_frame'])

    # 先生成物体放到哪里，再为该位置计算机械臂 IK。
    place_generator = stages.GeneratePlacePose('generate place pose')
    configure_from_parent(place_generator)
    place_generator.marker_ns = 'place_pose'
    place_generator.object = OBJECT_NAME
    # 教程的放置目标：相对 object 坐标系沿 Y 正方向移动 0.5 米。
    place_target = frame_pose(OBJECT_NAME, y=0.5)
    place_generator.pose = place_target
    # 监控 attach 阶段，确保放置计算知道物体相对手的真实附着关系。
    place_generator.setMonitoredStage(task['pick object']['attach object'])

    # 放置姿态也需要 IK；教程只保留 2 个候选，减少后续组合数量。
    place_ik = stages.ComputeIK('place pose IK', place_generator)
    place_ik.max_ik_solutions = 2
    place_ik.min_solution_distance = 1.0
    # 以物体本身作为 IK 参考，表示“把已附着物体送到目标位姿”。
    place_ik.ik_frame = frame_pose(OBJECT_NAME)
    configure_from_parent(place_ik, ['eef', 'group'])
    configure_from_interface(place_ik, ['target_pose'])
    place.add(place_ik)

    # 到达放置位姿后张开手爪，释放圆柱。
    open_hand_after_place = stages.MoveTo('open hand after place', interpolation_planner)
    open_hand_after_place.group = HAND_GROUP
    open_hand_after_place.setGoal('open')
    place.add(open_hand_after_place)

    # 松手后恢复手爪与物体的碰撞检查，之后二者不应再相互穿透。
    forbid_collision = stages.ModifyPlanningScene(
        'forbid collision (hand, object)')
    forbid_collision.allowCollisions(
        OBJECT_NAME, HAND_COLLISION_LINKS, False)
    place.add(forbid_collision)

    # 把 object 从 panda_hand 分离，重新作为世界中的独立物体。
    detach_object = stages.ModifyPlanningScene('detach object')
    detach_object.detachObject(OBJECT_NAME, HAND_FRAME)
    place.add(detach_object)

    # 松手后沿世界坐标系 X 负方向撤离，避免手爪仍贴着物体。
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
    # 将完整放置容器加入总任务。
    task.add(place)

    # 最后回到 Panda SRDF 中定义的 ready 命名姿态，
    # 让任务结束在可预测的位置。
    return_home = stages.MoveTo('return home', interpolation_planner)
    configure_from_parent(return_home, ['group'])
    return_home.setGoal('ready')
    task.add(return_home)
    # 返回构建完成的任务；main() 会负责调用 plan() 和 execute()。
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
