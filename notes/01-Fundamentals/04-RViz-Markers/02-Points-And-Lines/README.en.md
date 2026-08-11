[← RViz Marker Labs](../README.en.md) · [← Month One Fundamentals](../../README.en.md) · [Back to Home](../../../../README.en.md) · [中文](README.md) | **English**

# 04.2 · RViz Marker: Points and Lines

Basic shapes answer “draw one thing at one place.” Vision, planning, and debugging often need many points at once: a predicted trajectory, grasp candidates, a scan, or risk regions along a path. This lab encodes 100 points as three Marker types and makes RViz a viewer for time-varying geometric data.

## Official logic and Python implementation

The [ROS2 Jazzy tutorial](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/RViz/Marker-Points-and-Lines/Marker-Points-and-Lines.html) is written in C++. This workspace provides an equivalent rclpy version in [`points_and_lines.py`](../../../../ros_ws/src/fundamentals/rviz_markers/rviz_markers/points_and_lines.py). At `30 Hz` it sends three messages to `/visualization_marker`:

| Marker | Colour | `id` | How the point array is interpreted |
|---|---:|---:|---|
| `POINTS` | green | 0 | Each `Point` is independent; `scale.x/y` are point width and height |
| `LINE_STRIP` | blue | 1 | Neighbouring points are joined into one ordered polyline; `scale.x` is line width |
| `LINE_LIST` | red | 2 | Every pair of points is an independent segment; `scale.x` is line width |

The 100 base points span `x=-50` to `49`; their `y` and `z` use `sin` and `cos`. The continually increasing phase moves the geometry. For each red segment, the second endpoint is `1 m` higher than the first, making a set of vertical lines.

## Build

From `ros_ws`:

```bash
colcon build --packages-select rviz_markers
source install/setup.bash
```

## Lab: show points, a strip, and segments together

Use two terminals. In both, change into `ros_ws` and run `source install/setup.bash`.

Terminal 1 starts the publisher:

```bash
ros2 run rviz_markers points_and_lines
```

Terminal 2 starts RViz:

```bash
rviz2
```

In the RViz left panel: set **Global Options → Fixed Frame** to `my_frame`; click **Add → By topic**; then expand `/visualization_marker` and choose **Marker**. Zoom out and rotate the 3D view. One display now shows green points, a blue continuous curve, and red vertical segments changing smoothly at 30 Hz. They share one topic safely because their `ns='points_and_lines'` IDs are `0`, `1`, and `2`.

## Verify with the CLI

```bash
ros2 topic hz /visualization_marker
```

The frequency is about `90 Hz`, not `30 Hz`, because every timer callback publishes three Marker messages. Run `ros2 topic echo /visualization_marker --once` to inspect a message. `LINE_LIST` contains `200` points because 100 segments each need two endpoints.

## The boundary to remember

Use `POINTS` for discrete samples, `LINE_STRIP` for ordered paths, and `LINE_LIST` for disconnected relationships such as normals, matches, or velocity vectors. They are a **visualisation protocol** only: the underlying points still need correct frame IDs and timestamps, and Markers do not perform coordinate transformation or time synchronisation.

## Common pitfalls

- `LINE_LIST` does not create one automatically connected line; append points strictly in pairs or an unpaired endpoint cannot create a segment.
- Use `scale.x/y` for `POINTS`; `scale.z` has no effect there.
- Line Markers read only `scale.x` for width; changing `scale.y/z` does not thicken them.
- Running this and Basic Shapes together uses the same topic. Their namespaces keep the content separate, but starting one publisher at a time makes debugging clearer.

## Next step

Replace the synthetic `sin`/`cos` generator with an actual planned path, laser points, or visual detections, then send the same data to the Web Gateway.
