[← Month One Fundamentals](../README.en.md) · [Back to Home](../../../README.en.md) · [中文](README.md) | **English**

# 03 · URDF & RViz: See the Robot for the First Time

The earlier experiments can publish messages and query transforms, but a stream of terminal numbers does not yet feel like a robot. URDF turns abstract links, joints, and frames into a model with geometry; RViz puts that model, TF, and joint state in one view. This R2D2 lab makes “I published a joint angle” visible as “I can see the robot move.”

## How this feeds the month-end product

The first Web Gateway will not be only a static status card. URDF gives a readable structure to a robot model, joints, and frames; `joint_states` is the first live visual state for a web UI; RViz remains the more direct source of truth during development. If RViz and the web disagree, verify the ROS2 model and TF first.

## Concepts

- **URDF** — XML that describes robot structure: physical parts, visual geometry, and the joints that connect them.
- **Link** — a rigid part, such as R2D2's body, head, or wheel; every link has a frame.
- **Joint** — how two links connect. A joint can be fixed, continuously rotating, or translated along an axis.
- **`JointState`** — a message with joint names and positions. `robot_state_publisher` combines it with URDF to calculate TF for each link.
- **`robot_state_publisher`** — combines a URDF model and real-time joint state, then publishes the robot's TF tree.
- **RViz** — ROS2's 3D visualiser. This lab displays both the robot model and TF, proving that data actually drives the model.

## Code and assets

The package is [`ros_ws/src/fundamentals/urdf_r2d2`](../../../ros_ws/src/fundamentals/urdf_r2d2). Its assets come from the official ROS2 Jazzy URDF tutorial and are stored unchanged:

- [`r2d2.urdf.xml`](../../../ros_ws/src/fundamentals/urdf_r2d2/urdf/r2d2.urdf.xml) — [official URDF source](https://docs.ros.org/en/jazzy/_downloads/872802005223ffdb75b1ab7b25ad445b/r2d2.urdf.xml)
- [`r2d2.rviz`](../../../ros_ws/src/fundamentals/urdf_r2d2/rviz/r2d2.rviz) — [official RViz configuration](https://docs.ros.org/en/jazzy/_downloads/96d68aef72c4f27f32af5961ef48c475/r2d2.rviz)
- [`state_publisher.py`](../../../ros_ws/src/fundamentals/urdf_r2d2/urdf_r2d2/state_publisher.py) — publishes `swivel`, `tilt`, and `periscope` at `30 Hz`, plus a circular `odom → axis` transform.
- [`display.launch.py`](../../../ros_ws/src/fundamentals/urdf_r2d2/launch/display.launch.py) — starts `robot_state_publisher`, the state publisher, and RViz with the official configuration.

## Build

If ROS2 Jazzy Desktop is not installed, install RViz and the state publisher:

```bash
sudo apt install ros-jazzy-robot-state-publisher ros-jazzy-rviz2
```

Build and source the workspace from `ros_ws`:

```bash
colcon build --packages-select urdf_r2d2
source install/setup.bash
```

## Lab: make R2D2 move

Start the full lab from `ros_ws` in terminal 1:

```bash
ros2 launch urdf_r2d2 display.launch.py
```

RViz opens with the R2D2 model. Wait a few seconds and move the camera around. Verify three things: the head/joints change with `JointState`, R2D2's root moves in a circle of radius `2 m`, and the TF display includes both URDF-derived links and the publisher's `odom → axis` transform.

In terminal 2, change into the same `ros_ws`, source `install/setup.bash`, then inspect the joint message:

```bash
ros2 topic echo /joint_states
```

It includes the names `swivel`, `tilt`, and `periscope` with changing positions. Query the root transform too:

```bash
ros2 run tf2_ros tf2_echo odom axis
```

`translation.x` and `translation.y` change while `translation.z` remains near `0.7`, which proves the circle in the publisher is active. Optionally export the full tree with:

```bash
ros2 run tf2_tools view_frames
```

## What the state publisher does

The code keeps the official tutorial's motion but uses a ROS2 timer rather than a blocking loop in the node constructor, matching the lifecycle of the other workspace nodes. Every `1/30` second it publishes `JointState`, creates an `odom → axis` quaternion from yaw, then updates tilt, periscope height, swivel, and the circular-motion angle for the next frame.

The important model is not the quaternion formula: **URDF defines structure, `JointState` defines current pose, TF2 defines frame relationships, and RViz validates all three together.**

## Common pitfalls

- If RViz has no model, check the launch terminal for `robot_state_publisher` errors and confirm that it loaded `robot_description`.
- If the model exists but does not move, inspect `/joint_states`; its names must exactly match joint names in the URDF.
- When TF fails, do not randomly change RViz's Fixed Frame. First use `tf2_echo odom axis` to verify the publisher is sending the root transform.
- URDF lengths use metres and angles normally use radians. Entering millimetres or degrees directly produces a model with implausible scale or pose.

## Next step

Record this visualised run with rosbag2/MCAP so the month-end product can replay a failure instead of only showing the present.
