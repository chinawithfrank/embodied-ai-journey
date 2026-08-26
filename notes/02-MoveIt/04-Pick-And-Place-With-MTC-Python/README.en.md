[← Month Two: MoveIt](../README.en.md) · [Back to Home](../../../README.en.md) · [中文](README.md) | **English**

# 04 · Strict Python Port of the MTC Pick-and-Place Tutorial

The earlier experiment followed a different, older Python `Pick` / `Place` demo. Its scene, container hierarchy, and stage parameters did not match the tutorial requested for this lab, which made tutorial-based debugging unreliable.

This revision uses the [requested MTC tutorial](https://ros.ncnynl.com/cn/moveit2/doc/tutorials/pick_and_place_with_moveit_task_constructor/pick_and_place_with_moveit_task_constructor.html) as its only baseline. It preserves its scene values, task properties, stage order, IK counts, Cartesian distances, Connect timeouts, and return-to-`ready` step. The implementation remains Python; only C++ API calls are translated to Jazzy's Python-binding property syntax.

In Jazzy's Python binding, `SerialContainer` belongs to `moveit.task_constructor.core`, while concrete motion stages belong to `moveit.task_constructor.stages`; the code therefore uses `core.SerialContainer(...)`.

The binding also follows C++ ownership transfer: after `task.add(stage)` or `container.add(stage)`, do not pass the original Python variable to another API. Retrieve a container-owned stage from the task tree instead, for example `task['current state']` or `task['pick object']['attach object']`.

```text
current state → open hand → move to pick
    → pick object: approach → grasp IK → allow collision → close → attach → lift
    → move to place
    → place object: place IK → open → forbid collision → detach → retreat
    → return home
```

## Exact configuration

| Item | Tutorial value | This lab |
| --- | --- | --- |
| Object | Cylinder in `world`, height `0.1 m`, radius `0.02 m` | Same |
| Object location | `x=0.5`, `y=-0.25` | Same |
| Groups | `panda_arm` and `hand` | Same |
| Approach | Hand-frame Z+, `0.1–0.15 m` | Same |
| Grasp sampling | `π / 12`, 8 IK solutions, distance `1.0` | Same |
| Lift / retreat | `0.1–0.3 m`; world Z+ / world X- | Same |
| Place target | Object-frame Y+ `0.5 m`, 2 IK solutions | Same |
| Connect | Five seconds; place connection plans arm and hand | Same |
| Finish | Joint-interpolate to `ready` | Same |

The place connection deliberately uses both groups:

```python
[
    ('panda_arm', sampling_planner),
    ('hand', interpolation_planner),
]
```

This handles both the arm's free-space path and gripper joint state before their trajectories are merged.

## Run it

Build MTC's `ros2` branch in the same workspace first:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/develops/embodied-ai-journey/ros_ws/src
git clone --branch ros2 https://github.com/moveit/moveit_task_constructor.git
cd ..
rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy
colcon build --symlink-install --packages-up-to hello_moveit_py
source install/setup.bash
```

Then launch the lab:

```bash
cd ~/develops/embodied-ai-journey/ros_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch hello_moveit_py mtc_pick_place.launch.py
```

Expected output is:

```text
MTC object is active in the MoveIt Planning Scene.
MTC found a solution and is sending it to the mock controller.
MTC pick-and-place execution completed successfully.
```

The node calls `task.plan(5)`, publishes the first solution, then calls `task.execute(...)`. It therefore executes automatically through `ExecuteTaskSolutionCapability`; do not use the regular RViz MotionPlanning display's `Plan & Execute` button. Here `5` is the maximum number of successful task solutions, not a five-second timeout. Each Connect stage has its own `5.0 s` timeout.

## Inspect in RViz

1. Uncheck the regular `MotionPlanning` display.
2. Set `Global Options → Fixed Frame` to `world`.
3. Add `moveit_task_constructor_visualization → Motion Planning Tasks`.
4. Set `Task Solution Topic` to `/solution`.
5. Select stages and their successful or failed solutions to inspect the task tree.

## Python files

- [`mtc_scene_setup.py`](../../../ros_ws/src/moveit/hello_moveit_py/hello_moveit_py/mtc_scene_setup.py) creates the tutorial cylinder with `/apply_planning_scene`.
- [`mtc_pick_place.py`](../../../ros_ws/src/moveit/hello_moveit_py/hello_moveit_py/mtc_pick_place.py) defines, plans, publishes, and executes the complete task.
- [`mtc_pick_place.launch.py`](../../../ros_ws/src/moveit/hello_moveit_py/launch/mtc_pick_place.launch.py) starts the Panda mock environment and MTC nodes.

`ApplyPlanningScene` replaces the unavailable Jazzy Python `PlanningSceneInterface`, while preserving the tutorial collision object's parameters and behavior.

## Troubleshooting

- **No solution**: read the final `Failing stage(s)` entry and inspect that stage in Motion Planning Tasks.
- **Execution failed**: run `ros2 control list_controllers`; `panda_arm_controller`, `panda_hand_controller`, and `joint_state_broadcaster` must be `active`.
- **`MoveGroupInterface::move()`**: this comes from the regular MotionPlanning display's interactive target, not this MTC task. Disable that display.
- **`No default projection is set`**: an OMPL diagnostic. It matters only together with a specific failed MTC stage.
- **KDL root inertia warning**: a known Panda URDF/KDL compatibility warning, not a task failure.

## References

- [Requested Chinese MTC tutorial](https://ros.ncnynl.com/cn/moveit2/doc/tutorials/pick_and_place_with_moveit_task_constructor/pick_and_place_with_moveit_task_constructor.html)
- [Official MoveIt MTC tutorial](https://moveit.picknik.ai/main/doc/tutorials/pick_and_place_with_moveit_task_constructor/pick_and_place_with_moveit_task_constructor.html)
