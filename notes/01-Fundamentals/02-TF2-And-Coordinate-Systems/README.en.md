[← Month One Fundamentals](../README.en.md) · [Back to Home](../../../README.en.md) · [中文](README.md) | **English**

# 02 · TF2 & Coordinate Systems: Make Data Know Where It Is

This chapter teaches the robot to understand where things are.

## Why I learned this

“A cup was detected” sounds complete until the next question: in whose coordinates? A camera can see an object, but an arm still does not know where to reach, because cameras, bases, and joints all use different origins and directions. TF2 connects those local views into a tree, so a program can query position and orientation between any connected frames.

This deliberately does not pretend to be a real robot. The dynamic broadcaster simply moves `camera_link` in a circle around `base_link`, making a transform that changes over time visible. When the Web Gateway later receives real state and logs, the TF tree gives each value the context of where it was, when it was, and what it is relative to.

### How this feeds the month-end product

- Robot and sensor frame relationships give backend status a spatial context instead of leaving it as ungrounded numbers.
- `tf2_echo` and a TF-tree screenshot are debugging evidence when a web view looks wrong: first verify that the coordinate chain exists.
- URDF, RViz, and MCAP work later in the month will reuse the `base_link → sensor_link` model instead of introducing another vocabulary.

## Concept

- **Coordinate frame** — a reference for position and orientation, such as `base_link` (robot base), `camera_link`, or `laser_link`. ROS2 commonly uses a right-handed convention: `x` forward, `y` left, `z` up.
- **Transform** — the translation and rotation of a frame relative to its parent. Translation uses metres and rotation uses a quaternion. This example only rotates around `z`, so it creates a quaternion from yaw in radians.
- **TF tree** — the parent/child graph of all frames. A child has one parent and the graph cannot contain a cycle, allowing TF2 to compose transforms along the tree.
- **Static transform** — an unchanged mounting extrinsic, such as the position of a fixed lidar; published on `/tf_static`.
- **Dynamic transform** — a pose that changes over time, such as a gimbal, joint, or moving camera; continuously published on `/tf`.
- **Query direction** — `lookup_transform(target, source, ...)` returns the transform needed to express coordinates from `source` in `target`. The listener here queries the pose of `camera_link` in `base_link`.

## Build

The code is in [`ros_ws/src/fundamentals/tf2_coordinate_systems`](../../../ros_ws/src/fundamentals/tf2_coordinate_systems) and has three nodes:

1. **Static broadcaster** ([`static_frame_broadcaster.py`](../../../ros_ws/src/fundamentals/tf2_coordinate_systems/tf2_coordinate_systems/static_frame_broadcaster.py)) — publishes the fixed `base_link → laser_link` transform, representing a lidar mounted in front of a robot.
2. **Dynamic broadcaster** ([`dynamic_frame_broadcaster.py`](../../../ros_ws/src/fundamentals/tf2_coordinate_systems/tf2_coordinate_systems/dynamic_frame_broadcaster.py)) — continuously publishes `base_link → camera_link`, moving the camera in a circle and changing its yaw to make the time-varying TF visible.
3. **Listener** ([`frame_listener.py`](../../../ros_ws/src/fundamentals/tf2_coordinate_systems/tf2_coordinate_systems/frame_listener.py)) — caches TF with `tf2_ros.Buffer`, then queries and logs translation and yaw once per second.

### Dependencies

ROS2 Jazzy Desktop normally includes the runtime dependencies. Install the TF inspection tools if needed:

```bash
sudo apt install ros-jazzy-tf2-tools
```

### Build

From `ros_ws`:

```bash
colcon build --packages-select tf2_coordinate_systems
source install/setup.bash
```

### Run — Experiment 1: dynamic transform and lookup

Use two terminals, and run `source install/setup.bash` in each.

Terminal 1 starts the dynamic broadcaster:

```bash
ros2 run tf2_coordinate_systems dynamic_frame_broadcaster
```

Terminal 2 starts the listener:

```bash
ros2 run tf2_coordinate_systems frame_listener
```

The listener logs output similar to:

```text
[INFO] [frame_listener]: camera_link in base_link: x=0.44, y=0.24, z=0.20, yaw=0.50 rad
```

You can also query the TF2 buffer directly:

```bash
ros2 run tf2_ros tf2_echo base_link camera_link
```

Adjust the path radius and angular speed with parameters:

```bash
ros2 run tf2_coordinate_systems dynamic_frame_broadcaster --ros-args \
  -p radius:=1.0 -p angular_speed:=1.2
```

### Run — Experiment 2: static mounting extrinsic

Start the static broadcaster. It publishes a lidar `0.2 m` in front of, and `0.1 m` above, the base by default:

```bash
ros2 run tf2_coordinate_systems static_frame_broadcaster
```

Use parameters to simulate another mounting position and orientation:

```bash
ros2 run tf2_coordinate_systems static_frame_broadcaster --ros-args \
  -p x:=0.35 -p z:=0.15 -p yaw:=0.2
```

Verify it from another terminal:

```bash
ros2 run tf2_ros tf2_echo base_link laser_link
```

### Inspect the TF tree

After starting at least one broadcaster, run this in a terminal in the same ROS Domain:

```bash
ros2 run tf2_tools view_frames
```

It writes `frames.pdf` to the current directory; it should contain `base_link` and its child frames. Alternatively, open `rviz2` and add a **TF** display to inspect the axes visually.

## What to observe after running

Treat these three visible behaviours as completion criteria:

1. `frame_listener` changes `x`, `y`, and yaw continuously while `z` remains `0.20`; it is querying one dynamic frame, not printing random values.
2. `tf2_echo base_link camera_link` agrees with the listener's direction: it expresses the camera pose in the base frame.
3. With the static broadcaster running too, the `view_frames` graph shows both `camera_link` and `laser_link` below `base_link`.

At first startup, `Waiting for …` from the listener is expected: it is waiting for the TF buffer to receive its first transform. Keep that brief failure in the learning record rather than hiding it—real systems expose the same startup-order issue.

## What went wrong

- Do not mix frame names with and without a leading `/`; this chapter consistently uses names such as `base_link` without it.
- It is easy to reverse `lookup_transform` arguments. State the intent first: “convert points in the source frame into the target frame.”
- A newly started listener can have an empty TF buffer. Catch `TransformException` and wait for the next lookup.
- Use `StaticTransformBroadcaster` for a static frame instead of an infrequent dynamic broadcaster. `/tf_static` makes the transform available to nodes that join later.
- A quaternion is not Euler angles. The examples only handle yaw; use full quaternions or a proven conversion library for real 3D poses.

## Next step

The next chapter will transform sensor data into a shared frame such as `base_link` or `map`, then use it for perception, localization, and planning.
