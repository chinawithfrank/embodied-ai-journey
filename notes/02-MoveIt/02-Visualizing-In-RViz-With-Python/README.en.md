[← Month Two: MoveIt](../README.en.md) · [Back to Home](../../../README.en.md) · [中文](README.md) | **English**

# 02 · Understand a Plan in RViz: a Python-Only Visualization Lab

An arm moving is not proof that I understand its motion. Where is the goal? Which path did the planner choose? Did I inspect that path before execution?

MoveIt's C++ tutorial answers with `MoveItVisualTools`: render a title, goal, and trajectory in RViz, then advance with a `Next` button. This lab preserves that workflow without any C++: Python publishes `MarkerArray` and `DisplayTrajectory`, while three ROS 2 `Trigger` services replace the GUI button.

```text
show_goal -> MarkerArray -> RViz: title, goal sphere, XYZ axes
plan      -> MoveItPy -> DisplayTrajectory -> RViz: planned arm trajectory
execute   -> mock controller -> RViz: updated current robot state
```

## Code

The code stays in [`hello_moveit_py`](../../../ros_ws/src/moveit/hello_moveit_py):

- [`rviz_visualizer.py`](../../../ros_ws/src/moveit/hello_moveit_py/hello_moveit_py/rviz_visualizer.py) implements three Python services and publishes title, goal, axes, and trajectory messages.
- [`visualizing.launch.py`](../../../ros_ws/src/moveit/hello_moveit_py/launch/visualizing.launch.py) starts the Python node, `move_group`, Panda mock controller, TF, robot-state publisher, and RViz.
- [`moveit_py.yaml`](../../../ros_ws/src/moveit/hello_moveit_py/config/moveit_py.yaml) configures MoveItPy's Planning Scene Monitor and OMPL pipeline.

The fixed target puts `panda_link8` at `(0.28, -0.20, 0.50)` in `panda_link0`. The gold sphere marks position; red, green, and blue arrows mark X, Y, and Z. The unit quaternion intentionally keeps these axes aligned with the base frame for a readable first experiment.

## Build

Use **Ubuntu 24.04 + ROS 2 Jazzy**:

```bash
sudo apt update
sudo apt install ros-jazzy-moveit ros-jazzy-moveit-resources-panda-moveit-config

source /opt/ros/jazzy/setup.bash
cd ros_ws
colcon build --packages-select hello_moveit_py
source install/setup.bash
```

## Run it step by step

Start the complete lab:

```bash
source /opt/ros/jazzy/setup.bash
cd ros_ws
source install/setup.bash
ros2 launch hello_moveit_py visualizing.launch.py
```

When RViz opens, add a `MarkerArray` display and set its topic to `/rviz_visual_tools`. Keep `MotionPlanning` enabled; in `Planned Path`, check `Show Robot Visual` and use `/display_planned_path` as its trajectory topic.

In a second sourced terminal, advance through the lab:

```bash
ros2 service call /python_rviz_visualizer/show_goal std_srvs/srv/Trigger "{}"
ros2 service call /python_rviz_visualizer/plan std_srvs/srv/Trigger "{}"
ros2 service call /python_rviz_visualizer/execute std_srvs/srv/Trigger "{}"
```

First inspect the goal sphere and axes. After `plan`, inspect the displayed trajectory while the current robot remains still. Only `execute` sends that inspected trajectory to the mock controller. The saved plan is then cleared, preventing an accidental repeat execution.

## Mapping the C++ tutorial to Python

| C++ tutorial feature | Python implementation | What it reveals |
| --- | --- | --- |
| `publishText()` | `Marker.TEXT_VIEW_FACING` | Current program phase |
| `publishAxisLabeled()` | Gold sphere plus `Marker.ARROW` axes | Goal position and orientation |
| `publishTrajectoryLine()` | `DisplayTrajectory` on `/display_planned_path` | The trajectory MoveItPy actually planned |
| `RvizVisualToolsGui` `Next` | `/show_goal`, `/plan`, `/execute` Trigger services | A pause between every safety-relevant step |
| `trigger()` batching | A direct publish per service | Clear Python message boundaries |

`DisplayTrajectory` carries the `RobotTrajectory` returned by MoveItPy. RViz therefore previews joint motion from the same plan that is later passed to the controller; it is not an illustrative path invented by the visualization code.

## Change the experiment

Modify XYZ in `create_target_pose()` in [`rviz_visualizer.py`](../../../ros_ws/src/moveit/hello_moveit_py/hello_moveit_py/rviz_visualizer.py), rebuild, and restart. Change one coordinate at a time. Always call `show_goal` before `plan`: it makes an invalid or unreachable target visible before the planner reports a failure.

## Troubleshooting

- **No text or sphere**: add `MarkerArray`, not `Marker`, and set Topic exactly to `/rviz_visual_tools`.
- **No planned arm**: keep `MotionPlanning` enabled; check its trajectory topic and `Show Robot Visual`.
- **Plan fails**: wait for controller state, choose a goal nearer Panda's initial pose, and retry.
- **Execute fails**: call `plan` successfully first; this is an intentional guard.
- **Service is missing**: source `install/setup.bash` in the new terminal and wait for the launch to finish.

## References

- [MoveIt: Visualizing in RViz](https://moveit.picknik.ai/main/doc/tutorials/visualizing_in_rviz/visualizing_in_rviz.html)
- [MoveIt: Motion Planning Python API](https://moveit.picknik.ai/main/doc/examples/motion_planning_python_api/motion_planning_python_api_tutorial.html)
