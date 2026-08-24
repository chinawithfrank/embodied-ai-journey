[← Month Two: MoveIt](../README.en.md) · [Back to Home](../../../README.en.md) · [中文](README.md) | **English**

# 01 · First MoveItPy Project: Give an Arm a Pose Target

The official “Your First C++ MoveIt Project” teaches `MoveGroupInterface`. This lab keeps its essential task—set a pose target, plan, and execute—but uses MoveIt's Python API, `moveit_py`, so the early focus stays on motion-planning concepts rather than C++ syntax.

```text
PoseStamped target
       |
hello_moveit_py -> MoveItPy / PlanningComponent(panda_arm)
       |                     |
       |             model + joint_states + OMPL -> execute()
       |                                             |
       +---------------------------------------- RViz <- mock controller
```

## Code

[`hello_moveit_py`](../../../ros_ws/src/moveit/hello_moveit_py) contains:

- [`pose_goal.py`](../../../ros_ws/src/moveit/hello_moveit_py/hello_moveit_py/pose_goal.py), which creates `MoveItPy`, sets a Panda pose goal, plans, and executes;
- [`moveit_py.yaml`](../../../ros_ws/src/moveit/hello_moveit_py/config/moveit_py.yaml), which configures the Planning Scene Monitor and OMPL for the Python process;
- [`demo.launch.py`](../../../ros_ws/src/moveit/hello_moveit_py/launch/demo.launch.py), which starts the model, mock controllers, RViz, static TF, and Python node.

Unlike the C++ tutorial, this lab does **not** start `move_group`. `MoveItPy` is Python access to MoveItCpp, so planning runs inside the Python node and needs the complete MoveIt configuration passed by its launch file.

## Prepare and build

Use **Ubuntu 24.04 + ROS2 Jazzy**:

```bash
sudo apt update
sudo apt install ros-jazzy-moveit ros-jazzy-moveit-resources-panda-moveit-config
source /opt/ros/jazzy/setup.bash
ros2 pkg prefix moveit_py
ros2 pkg prefix moveit_resources_panda_moveit_config
```

Then build the project:

```bash
cd ros_ws
colcon build --packages-select hello_moveit_py
source install/setup.bash
```

## Run

One launch command starts the complete experiment:

```bash
source /opt/ros/jazzy/setup.bash
cd ros_ws
source install/setup.bash
ros2 launch hello_moveit_py demo.launch.py
```

Expect `Planning a pose goal for panda_link8.` followed by `Plan found. Executing trajectory.` RViz shows Panda moving its seven arm joints towards this target:

```text
frame: panda_link0
position: (0.28, -0.20, 0.50)
orientation: (0, 0, 0, 1)
link: panda_link8
```

The unit quaternion is intentional; a zero quaternion is not a valid pose orientation. The mock controller updates simulation state only and never drives physical hardware.

## Verify

The Python node exits after its one trajectory, while RViz and controllers remain active. In another terminal:

```bash
ros2 control list_controllers
ros2 topic echo /joint_states --once
```

Expect active `joint_state_broadcaster` and `panda_arm_controller` entries plus Panda joint state. The client does not command individual joints; MoveIt plans a trajectory and the controller publishes the result.

## Concepts to keep

- `MoveItPy` loads the model, Planning Scene Monitor, and planning pipelines in the Python process.
- `panda_arm` names Panda's seven-arm-joint planning group.
- The start state comes from current `/joint_states`; the goal is a pose tied to `panda_link0` and applied to `panda_link8`.
- `plan()` and `execute()` are deliberately separate. A plan is not permission to move real hardware.

## Common failures

- `ros2 run` alone has no MoveIt parameters; start with the provided launch file.
- A missing frame or zero quaternion makes a pose ambiguous or invalid.
- If planning starts before controllers publish joint state, wait a few seconds and retry; inspect `ros2 control list_controllers`.

## Next

The next Python lab adds collision objects to the Planning Scene and separates “the goal is reachable” from “the entire path is safe.”

## References

- [MoveIt: Your First C++ MoveIt Project](https://moveit.picknik.ai/main/doc/tutorials/your_first_project/your_first_project.html)
- [MoveIt: Motion Planning Python API](https://moveit.picknik.ai/main/doc/examples/motion_planning_python_api/motion_planning_python_api_tutorial.html)
