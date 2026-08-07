[← Back to Home](../../README.en.md) · [中文](README.md) | **English**

# ROS2 Fundamentals

This chapter targets **ROS2 Jazzy Jalisco** (Ubuntu 24.04) throughout.

## Why I learned this

A robot isn't one monolithic program — it's a pile of independent modules: a camera node, a chassis node, an arm node, each running as its own process, sometimes on different machines, that still need to cooperate in real time. The first problem ROS2 solves is giving those modules a common way to talk to each other. Without understanding that communication layer first, there's no way to wire up perception, decision-making, and control later on.

## Concept

- **Node** — an independently running program that usually does one thing.
- **Topic** — an async broadcast channel between nodes: one node publishes, any number of nodes can subscribe.
- **Message** — the data structure sent over a topic, e.g. `geometry_msgs/Twist` (a velocity command) or `std_msgs/String`.
- **turtlesim** — ROS2's built-in "sandbox" simulator: a turtle stands in for a real robot, purely for practicing topic communication without touching hardware.

## Build

Code lives in [`ros_ws/src/ros2_fundamentals`](../../ros_ws/src/ros2_fundamentals), two experiments:

1. **Keyboard-controlled turtlesim** ([`keyboard_teleop.py`](../../ros_ws/src/ros2_fundamentals/ros2_fundamentals/keyboard_teleop.py)) — reads raw keypresses from the terminal via `termios`/`tty`, maps them to a `Twist`, and publishes it on `/turtle1/cmd_vel` to drive the turtle.
2. **Pub / Sub example** ([`pub_example.py`](../../ros_ws/src/ros2_fundamentals/ros2_fundamentals/pub_example.py) / [`sub_example.py`](../../ros_ws/src/ros2_fundamentals/ros2_fundamentals/sub_example.py)) — one node publishes a `String` on `chatter` once a second, the other subscribes and logs it.

### Dependencies

```bash
sudo apt install ros-jazzy-turtlesim
```

### Build

From the `ros_ws` directory:

```bash
colcon build --packages-select ros2_fundamentals
source install/setup.bash
```

### Run — Experiment 1: keyboard-controlled turtlesim

Needs two terminals (both need `source install/setup.bash` first).

Terminal 1:

```bash
ros2 run turtlesim turtlesim_node
```

Terminal 2:

```bash
ros2 run ros2_fundamentals keyboard_teleop
```

| Key | Action |
|-----|--------|
| w | forward |
| x | backward |
| a | turn left |
| d | turn right |
| s | stop |
| q | quit |

### Run — Experiment 2: Pub / Sub example

Also needs two terminals.

```bash
ros2 run ros2_fundamentals pub_example
```

```bash
ros2 run ros2_fundamentals sub_example
```

You can also just run `ros2 topic echo /chatter` to watch the topic directly.

## Experiment

TODO: add screenshots/recordings once this actually runs on Ubuntu + ROS2 Jazzy.

## What went wrong

- Keyboard reading uses raw tty mode, so it has to run in a foreground terminal via `ros2 run` — `ros2 launch` can't reliably forward stdin to multiple child processes, which is why neither experiment has a launch file.
- Every new terminal needs `source install/setup.bash` again; forgetting it makes `ros2 run` unable to find the package.
- `turtlesim` isn't part of the ROS2 core install — it needs a separate `apt install`.

## Next step

Next chapter: [TF2 & Coordinate Systems](../02-TF2-And-Coordinate-Systems) — teaching the robot to understand where things are.
