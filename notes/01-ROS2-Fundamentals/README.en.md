[← Back to Home](../../README.en.md) · [中文](README.md) | **English**

# ROS2 Fundamentals

This chapter targets **ROS2 Jazzy Jalisco** (Ubuntu 24.04) throughout.

## Why I learned this

A robot isn't one monolithic program — it's a pile of independent modules: a camera node, a chassis node, an arm node, each running as its own process, sometimes on different machines, that still need to cooperate in real time. The first problem ROS2 solves is giving those modules a common way to talk to each other. Without understanding that communication layer first, there's no way to wire up perception, decision-making, and control later on.

## Concept

- **Node** — an independently running program that usually does one thing.
- **Topic** — an async broadcast channel between nodes: one node publishes, any number of nodes can subscribe.
- **Service** — synchronous request/response communication, suited to one-off work such as enabling motors or reading a configuration value.
- **Action** — goal-oriented communication for longer tasks; the server streams feedback and the client can cancel a goal.
- **Parameter** — a node-local configuration value that can be supplied at startup or changed while the node is running.
- **Message** — the data structure sent over a topic, e.g. `geometry_msgs/Twist` (a velocity command) or `std_msgs/String`.
- **turtlesim** — ROS2's built-in "sandbox" simulator: a turtle stands in for a real robot, purely for practicing topic communication without touching hardware.

## Build

Code lives in [`ros_ws/src/ros2_fundamentals`](../../ros_ws/src/ros2_fundamentals), with these experiments:

1. **Keyboard-controlled turtlesim** ([`keyboard_teleop.py`](../../ros_ws/src/ros2_fundamentals/ros2_fundamentals/keyboard_teleop.py)) — reads raw keypresses from the terminal via `termios`/`tty`, maps them to a `Twist`, and publishes it on `/turtle1/cmd_vel` to drive the turtle.
2. **Pub / Sub example** ([`pub_example.py`](../../ros_ws/src/ros2_fundamentals/ros2_fundamentals/pub_example.py) / [`sub_example.py`](../../ros_ws/src/ros2_fundamentals/ros2_fundamentals/sub_example.py)) — one node publishes a `String` on `chatter` once a second, the other subscribes and logs it.
3. **Service example** ([`service_server.py`](../../ros_ws/src/ros2_fundamentals/ros2_fundamentals/service_server.py) / [`service_client.py`](../../ros_ws/src/ros2_fundamentals/ros2_fundamentals/service_client.py)) — a server exposes `/set_motors_enabled` using `std_srvs/SetBool`; the client sends an enable/disable request and waits for the response.
4. **Action example** ([`action_client.py`](../../ros_ws/src/ros2_fundamentals/ros2_fundamentals/action_client.py)) — connects to turtlesim's built-in `/turtle1/rotate_absolute` action, sends a target heading, and prints feedback during the rotation.
5. **Parameter example** ([`parameter_example.py`](../../ros_ws/src/ros2_fundamentals/ros2_fundamentals/parameter_example.py)) — declares and validates `robot_name` and `publish_period`; changing the period rebuilds the timer so the configuration takes effect immediately.

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

### Run — Experiment 3: Service example

This needs two terminals. Start the server in terminal 1:

```bash
ros2 run ros2_fundamentals service_server
```

Send a request from terminal 2 (enables motors by default):

```bash
ros2 run ros2_fundamentals service_client
```

Pass a parameter to disable them instead:

```bash
ros2 run ros2_fundamentals service_client --ros-args -p enabled:=false
```

Inspect the interface or call the service directly with the ROS2 CLI:

```bash
ros2 service list
ros2 interface show std_srvs/srv/SetBool
ros2 service call /set_motors_enabled std_srvs/srv/SetBool "{data: true}"
```

### Run — Experiment 4: Action example

Start turtlesim in terminal 1. It provides the `RotateAbsolute` action server:

```bash
ros2 run turtlesim turtlesim_node
```

Send a target heading in radians from terminal 2:

```bash
ros2 run ros2_fundamentals action_client --ros-args -p theta:=1.57
```

The client logs the remaining angle as feedback and the final rotation when complete. Inspect the available actions and the interface with:

```bash
ros2 action list -t
ros2 interface show turtlesim/action/RotateAbsolute
```

### Run — Experiment 5: Parameter example

Pass parameters at startup:

```bash
ros2 run ros2_fundamentals parameter_example --ros-args \
  -p robot_name:=journey_bot -p publish_period:=2.0
```

From another terminal, inspect, read, or update parameters on the running node:

```bash
ros2 param list /parameter_example
ros2 param get /parameter_example robot_name
ros2 param set /parameter_example robot_name scout
ros2 param set /parameter_example publish_period 0.5
```

`robot_name` is reflected in the next log message, while `publish_period` recreates the timer. Empty names and non-positive periods are rejected by the node.

## Experiment

TODO: add screenshots/recordings once this actually runs on Ubuntu + ROS2 Jazzy.

## What went wrong

- Keyboard reading uses raw tty mode, so it has to run in a foreground terminal via `ros2 run` — `ros2 launch` can't reliably forward stdin to multiple child processes, which is why neither experiment has a launch file.
- Every new terminal needs `source install/setup.bash` again; forgetting it makes `ros2 run` unable to find the package.
- `turtlesim` isn't part of the ROS2 core install — it needs a separate `apt install`.
- A service caller waits for one response, so services fit short operations. Use actions for longer navigation or manipulation tasks instead.
- ROS2 parameters are typed. CLI values must match their declared types: `publish_period` is a float and `enabled` is a boolean.

## Next step

Next chapter: [TF2 & Coordinate Systems](../02-TF2-And-Coordinate-Systems) — teaching the robot to understand where things are.
