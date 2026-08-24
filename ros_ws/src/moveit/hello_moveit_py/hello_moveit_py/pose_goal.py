import time

from geometry_msgs.msg import PoseStamped
import rclpy
from rclpy.logging import get_logger

from moveit.planning import MoveItPy


def main(args=None):
    rclpy.init(args=args)
    logger = get_logger('hello_moveit_py')
    moveit_py = MoveItPy(node_name='hello_moveit_py')
    panda_arm = moveit_py.get_planning_component('panda_arm')

    pose_goal = PoseStamped()
    pose_goal.header.frame_id = 'panda_link0'
    pose_goal.pose.orientation.w = 1.0
    pose_goal.pose.position.x = 0.28
    pose_goal.pose.position.y = -0.2
    pose_goal.pose.position.z = 0.5

    panda_arm.set_start_state_to_current_state()
    panda_arm.set_goal_state(
        pose_stamped_msg=pose_goal,
        pose_link='panda_link8',
    )
    logger.info('Planning a pose goal for panda_link8.')
    plan_result = panda_arm.plan()

    if plan_result:
        logger.info('Plan found. Executing trajectory.')
        moveit_py.execute(plan_result.trajectory, controllers=[])
        time.sleep(2.0)
    else:
        logger.error('Planning failed.')

    rclpy.shutdown()
