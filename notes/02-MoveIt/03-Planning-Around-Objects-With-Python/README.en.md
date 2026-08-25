[← Month Two: MoveIt](../README.en.md) · [Back to Home](../../../README.en.md) · [中文](README.md) | **English**

# 03 · More Than Reaching a Goal: Python Collision-Aware Planning

Seeing a trajectory is not proof that it is safe. This lab puts an orange wall between Panda and its goal, then asks the meaningful question: when the target is reachable, will MoveIt deliberately go around the obstacle?

The official tutorial uses C++ `PlanningSceneInterface` to add `box1` to `move_group`. This Python lab writes the same `CollisionObject` twice: once to MoveItPy's local Planning Scene, which constrains Python planning, and once through `/apply_planning_scene`, which keeps `move_group` and RViz in the same world.

```text
CollisionObject(box1)
    +-> MoveItPy Planning Scene -> Python collision checking
    +-> /apply_planning_scene -> move_group -> RViz Planning Scene
```

An orange marker only makes a wall visible. `CollisionObject.ADD` makes it an object the planner must not cross.

## Code

- [`planning_around_objects.py`](../../../ros_ws/src/moveit/hello_moveit_py/hello_moveit_py/planning_around_objects.py) creates the goal and `box1`, synchronizes both scenes, publishes markers, and exposes planning services.
- [`planning_around_objects.launch.py`](../../../ros_ws/src/moveit/hello_moveit_py/launch/planning_around_objects.launch.py) starts the Python node, `move_group`, Panda mock controller, TF, robot-state publisher, and RViz.

The values match the official tutorial:

```text
goal position: (0.10, 0.40, 0.40) m
goal orientation: (x=0.0, y=0.8, z=0.0, w=0.6)
box1 centre: (0.20, 0.20, 0.25) m
box1 size: (0.50, 0.10, 0.50) m
```

The box pose is its centre, making it a vertical wall from `z = 0.0` to `z = 0.5`. Goal axes rotate with the target quaternion, so this lab also makes orientation visible.

## Build and run

```bash
source /opt/ros/jazzy/setup.bash
cd ros_ws
colcon build --packages-select hello_moveit_py
source install/setup.bash
ros2 launch hello_moveit_py planning_around_objects.launch.py
```

Wait for:

```text
[INFO] [python_object_planner]: box1 is active in MoveItPy and move_group Planning Scenes.
```

In RViz, add a `MarkerArray` display on `/rviz_visual_tools`. Keep `MotionPlanning` enabled, with `Planned Path → Show Robot Visual` checked and trajectory topic `/display_planned_path`.

Then, from a second sourced terminal:

```bash
ros2 service call /python_object_planner/show_scene std_srvs/srv/Trigger "{}"
ros2 service call /python_object_planner/plan std_srvs/srv/Trigger "{}"
ros2 service call /python_object_planner/execute std_srvs/srv/Trigger "{}"
```

First inspect the gold goal, rotated axes, and orange-red `box1`. After `plan`, inspect the trajectory while the scene robot is still motionless. Only `execute` sends that reviewed, collision-aware trajectory to the mock controller.

## What makes the plan avoid the wall

```python
collision_object.operation = CollisionObject.ADD
scene.apply_collision_object(self.collision_object)
request.scene.world.collision_objects.append(self.collision_object)
```

The first two lines add the object to MoveItPy's local scene before `plan()`. The third line sends the same object to `move_group`. In contrast, `Marker.CUBE` is visual-only: remove the marker and the planner still avoids the wall; remove the collision object and the displayed wall no longer constrains motion.

## Experiments to try

Edit `BOX_POSITION` or `BOX_DIMENSIONS` in [`planning_around_objects.py`](../../../ros_ws/src/moveit/hello_moveit_py/hello_moveit_py/planning_around_objects.py), rebuild, and restart. Change one variable at a time:

1. Increase the box Y position to `0.35` and inspect the preferred side of the detour.
2. Widen the box until planning fails; that is a valid “no collision-free path” result.
3. Move the box away and compare the obstacle-free path with the detour.

## Troubleshooting

- **The service says to wait for `box1`**: `move_group` is still starting; wait for the success log.
- **Path crosses a visible wall**: launch this lab, not the previous visualization lab, and verify the `box1 is active...` log.
- **No wall or goal**: add `MarkerArray` with exact topic `/rviz_visual_tools`.
- **No trajectory preview**: check MotionPlanning's planned-path settings and `/display_planned_path`.
- **Planning fails**: restore the official dimensions, then retry after controllers publish initial state.

## References

- [MoveIt: Planning Around Objects](https://moveit.picknik.ai/main/doc/tutorials/planning_around_objects/planning_around_objects.html)
- [MoveIt: Visualizing in RViz](https://moveit.picknik.ai/main/doc/tutorials/visualizing_in_rviz/visualizing_in_rviz.html)
