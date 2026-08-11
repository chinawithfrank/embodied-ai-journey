[← Month One Fundamentals](../README.en.md) · [Back to Home](../../../README.en.md) · [中文](README.md) | **English**

# 04 · RViz Marker: Sending Basic Shapes

The R2D2 lab shows what the robot itself looks like. Real development also needs to show things that do not belong in a URDF: detected objects, planned paths, collision regions, grasp candidates, and debugging state. `visualization_msgs/Marker` sends that temporary, dynamic visual information directly to RViz.

This is the first RViz Marker lab. Once per second it updates one Marker into a green cube, sphere, arrow, and cylinder. The goal is to see RViz as a ROS2-message-driven debugging canvas, not just a robot-model viewer.

## Concepts

- **Marker** — one visual object sent to RViz. It is not a physical collision object and does not move a robot.
- **`header.frame_id`** — the coordinate frame holding the Marker. This lab uses `my_frame` and sets RViz Fixed Frame to the same value, so no additional TF is needed.
- **namespace + id** — the Marker identity. The same `ns='basic_shapes'` and `id=0` updates one object instead of adding another shape each second.
- **type** — this lab cycles through `CUBE`, `SPHERE`, `ARROW`, and `CYLINDER`.
- **action** — `ADD` creates or updates an object; later experiments use `DELETE` and `DELETEALL`.
- **pose, scale, color, lifetime** — location/orientation, size, colour, and persistence. `color.a` must be non-zero or the Marker is invisible.

## Code

The official Jazzy tutorial is in C++; this repository ports the same behaviour to rclpy to match the other Fundamentals packages. The [official tutorial](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/RViz/Marker-Sending-Basic-Shapes/Marker-Sending-Basic-Shapes.html) logic is preserved in [`basic_shapes.py`](../../../ros_ws/src/fundamentals/rviz_markers/rviz_markers/basic_shapes.py): it publishes a green Marker with `ns='basic_shapes'` and `id=0` on `/visualization_marker`, then advances through the four shapes every second.

The package is [`ros_ws/src/fundamentals/rviz_markers`](../../../ros_ws/src/fundamentals/rviz_markers).

## Build

Install RViz if it is not already available:

```bash
sudo apt install ros-jazzy-rviz2
```

From `ros_ws`:

```bash
colcon build --packages-select rviz_markers
source install/setup.bash
```

## Lab: view the basic shapes in RViz

Use two terminals. In both, change into `ros_ws` and run `source install/setup.bash`.

Terminal 1 publishes the Marker:

```bash
ros2 run rviz_markers basic_shapes
```

Terminal 2 starts RViz:

```bash
rviz2
```

Configure RViz in the left panel:

1. Expand **Global Options** and set **Fixed Frame** to `my_frame`.
2. Click **Add**.
3. Choose **By topic**.
4. Expand `/visualization_marker` and select **Marker**.

After one second, the centre view shows a green object cycling **cube → sphere → arrow → cylinder**. Zoom the camera if necessary: the shape is at the origin.

## Verify with the CLI

Before relying on RViz, confirm that the message exists:

```bash
ros2 topic echo /visualization_marker --once
```

It includes `frame_id: my_frame`, `ns: basic_shapes`, `id: 0`, and green colour with non-zero alpha. `type` changes over time. Check the frequency with:

```bash
ros2 topic hz /visualization_marker
```

## The boundary to remember

URDF describes relatively stable robot structure; Markers describe temporary information from one run. A detected cup, planned path, current goal, or error region should be a timestamped, frame-aware Marker—not forced into the URDF.

## Common pitfalls

- If RViz reports `Fixed Frame [my_frame] does not exist`, confirm terminal 1 is publishing. The Marker header frame and Fixed Frame must match exactly here.
- If a Marker exists but is invisible, check that `color.a` is greater than `0` and every scale axis is positive.
- Do not change `ns` or `id` randomly in the loop, or RViz treats every message as a new object and the scene becomes cluttered.
- A Marker is visual data, not TF, URDF, or an obstacle in the physical world. It does not replace transforms, collision detection, or motion planning.

## Next step

The next Marker lab will use `POINTS`, `LINE_STRIP`, and `LINE_LIST` for trajectories, point-cloud-style results, or planned paths.
