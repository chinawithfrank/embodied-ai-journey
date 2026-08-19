[← Month One: Fundamentals](../README.en.md) · [Back to Home](../../../README.en.md) · [中文](README.md) | **English**

# 05 · rosbag2 & MCAP: Keep a Run

Seeing a robot run is not the same as finishing an experiment. The difficult failure often happens while I am not watching the terminal: when did a joint state change, and why did a Marker jump? Re-running from memory is not debugging.

This lab records the existing R2D2 joint state and RViz points-and-lines data into an **MCAP** bag, then replays it with no live publishers. The motion returns in RViz, proving that the result is a reusable stream of ROS2 messages, not a screenshot.

## What this validates

```text
live publishers -> /joint_states ------------┐
                   /visualization_marker ----+-> ros2 bag record --storage mcap
                                               |
                                     recordings/fundamentals_run/
                                               |
ros2 bag play ---------------------------------┘
                   | 
                   +-> robot_state_publisher -> R2D2 joint TF
                   +-> RViz Marker display ----> points and lines
```

`rosbag2` records **messages received on topics and their order in time**. It does not capture a running-node snapshot: source code, launch files, and the rest of the parameter state still come from the replay launch file. That boundary is the key idea in this experiment.

## Why MCAP

MCAP is one storage backend available to rosbag2. This lab explicitly selects it with `--storage mcap`, so `ros2 bag info` identifies the format instead of relying on a system default.

The bag intentionally contains only two topics:

- `/joint_states` preserves R2D2's three joint positions; `robot_state_publisher` rebuilds link TF during playback.
- `/visualization_marker` preserves the animated points, line strip, and line list for RViz.

A production robot investigation commonly records `/tf` and `/tf_static` too. This smaller lab deliberately rebuilds the internal TF from joint states and supplies fixed `odom -> axis` and `odom -> my_frame` transforms in the playback launch. It separates saved data from derived state.

## New code

The [`rosbag2_fundamentals`](../../../ros_ws/src/fundamentals/rosbag2_fundamentals) package combines prior labs into two repeatable states:

- [`recording_demo.launch.py`](../../../ros_ws/src/fundamentals/rosbag2_fundamentals/launch/recording_demo.launch.py) starts the R2D2 state publisher, points-and-lines publisher, `odom -> my_frame` static TF, and RViz.
- [`playback_visualization.launch.py`](../../../ros_ws/src/fundamentals/rosbag2_fundamentals/launch/playback_visualization.launch.py) starts only the model, fixed TF, and RViz; it waits for bag messages instead of publishing fresh data.
- [`replay.rviz`](../../../ros_ws/src/fundamentals/rosbag2_fundamentals/rviz/replay.rviz) displays RobotModel, TF, and `/visualization_marker` with `odom` as its Fixed Frame.

## Prepare

The environment is **Ubuntu 24.04 + ROS2 Jazzy**. Install rosbag2's MCAP backend:

```bash
sudo apt update
sudo apt install ros-jazzy-rosbag2 ros-jazzy-rosbag2-storage-mcap
```

Build the three packages from `ros_ws`:

```bash
colcon build --packages-select urdf_r2d2 rviz_markers rosbag2_fundamentals
source install/setup.bash
```

Run `source install/setup.bash` again in every new terminal opened in `ros_ws`.

## Lab 1: Record a run

Use two terminals.

Terminal 1 starts a scene that continuously produces data:

```bash
ros2 launch rosbag2_fundamentals recording_demo.launch.py
```

RViz should show R2D2 and three moving point/line objects. Keep it running.

Terminal 2 records the two topics. `ros_ws/recordings/` is ignored by Git, so generated bag data does not become source control history.

```bash
mkdir -p recordings
ros2 bag record --storage mcap -o recordings/fundamentals_run \
  /joint_states /visualization_marker
```

Wait about ten seconds, then press `Ctrl-C` in Terminal 2. rosbag2 writes metadata and MCAP data under `recordings/fundamentals_run/`.

## Lab 2: Inspect, then replay

Inspect the result before opening a visualiser:

```bash
ros2 bag info recordings/fundamentals_run
```

Confirm that the storage id is `mcap`, both topics appear, and the duration is roughly what you recorded.

Stop Terminal 1 so its live publishers do not mix with replayed data. Then use two fresh terminals.

Terminal 1 opens the playback-only visualisation environment:

```bash
ros2 launch rosbag2_fundamentals playback_visualization.launch.py
```

Terminal 2 plays the bag:

```bash
ros2 bag play recordings/fundamentals_run
```

R2D2's joints and the points-and-lines animation should repeat. Slow the timeline down when observing it:

```bash
ros2 bag play recordings/fundamentals_run --rate 0.5
```

## Verify the player

While playback is active, open another terminal:

```bash
ros2 topic echo /joint_states --once
ros2 topic echo /visualization_marker --once
```

Timestamped messages confirm that the bag player, rather than the stopped live source, is publishing. `ros2 topic hz /joint_states` shows the active playback rate.

## Boundaries to remember

- **rosbag2 is an event record, not a system snapshot.** It replays messages but does not launch RViz, models, or application nodes for you.
- **Record according to the question.** This lab saves joint and Marker messages; a real navigation or perception issue often also needs TF, cameras, lidar, maps, and parameter evidence.
- **Stop live publishers before replay.** Mixing a bag player with a live source on the same topic makes the timeline untrustworthy.
- **A bag is runtime output, not source.** It can be large and can contain sensitive environment data, so `ros_ws/recordings/` stays outside Git.

## Common pitfalls

- If rosbag2 cannot find `mcap`, install `ros-jazzy-rosbag2-storage-mcap` and source the ROS environment again.
- If `ros2 bag info` has no target topics, start Terminal 1 before recording; rosbag2 only captures messages received after it subscribes.
- If replay has no visible result, stop the live scene, inspect the bag, and make sure RViz's Fixed Frame remains `odom`.
- This lab does not preserve the R2D2 circular base trajectory because `odom -> axis` is generated as live TF and is not recorded. Playback supplies a fixed transform so the joints and Markers remain observable. Add `/tf` and `/tf_static` to the record command when you need the full moving TF tree.

## Next

One ROS2 run can now be preserved, inspected, and replayed. Next, FastAPI and WebSocket can carry live topics, Action progress, and bag metadata to the web on the way to the ROS2 Web Gateway.

## References

- [rosbag2 MCAP storage plugin (official ROS 2 repository)](https://github.com/ros2/rosbag2/tree/rolling/rosbag2_storage_mcap)
- [ROS 2 Jazzy rosbag2 tutorial](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools/Recording-And-Playing-Back-Data.html)
