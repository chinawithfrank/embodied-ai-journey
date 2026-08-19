[← Back to Home](../../README.en.md) · [中文](README.md) | **English**

# Month One: Robot Software Fundamentals

> **Monthly goal: ROS2 Web Gateway v0.1** — bring robot data and tasks into the web systems I already know how to build.

I am not starting with motors, mechanisms, or control theory. My first question is closer to my full-stack background: how does data from a robot node reach a backend and a web page reliably? How does a button in that page become a traceable, cancellable robot task?

This month does not need hardware, SLAM, Isaac Sim, or VLA models. It needs a small but complete software spine: ROS2 owns robot-side communication and task execution; the web system exposes state, logs, and controls to people. The later arm, vision, and data products all grow from this path.

## What this month builds

The month-end demo is **ROS2 Web Gateway v0.1**. It is not an empty dashboard; it is a working task path:

```text
ROS2 node publishes state -> backend receives it -> WebSocket -> live web UI
web UI creates a task    -> backend calls it     -> ROS2 Service / Action -> node runs it
                                                   |
                                           progress, cancellation, logs, MCAP recording
```

The final demo must answer six questions: is the robot online, what data is it publishing, can a user create a task, can a long task show progress and be cancelled, where are its logs, and can the run be recorded and replayed?

This product contract is now implemented: communication, TF2, URDF, RViz, and rosbag2/MCAP examples converge in a runnable Web Gateway. It remains a local experiment product, not a safety system for physical hardware.

## Directory contract

```text
embodied-ai-journey/
├── ros_ws/                         # runnable, buildable ROS2 experiment code only
│   └── src/fundamentals/
│       ├── ros2_fundamentals/      # Topic, Service, Action, Parameter
│       ├── tf2_coordinate_systems/ # static/dynamic TF and lookup
│       ├── urdf_r2d2/              # URDF, JointState, TF, and RViz
│       ├── rviz_markers/           # basic shapes and later visualisation labs
│       ├── rosbag2_fundamentals/   # MCAP recording and visual replay
│       └── web_gateway_demo/        # month-one demo graph combining prior nodes
└── notes/                          # learning narrative, concepts, labs, and retrospectives only
    └── 01-Fundamentals/
        ├── README.md               # month entry and product goal
        ├── 01-ROS2-Communication/
        ├── 02-TF2-And-Coordinate-Systems/
        ├── 03-URDF-And-RViz/
        ├── 04-RViz-Markers/
        ├── 05-Rosbag2-And-MCAP/
        └── 06-ROS2-Web-Gateway/
```

New experiment code belongs in `ros_ws`; its purpose, instructions, observations, and failures belong in `notes`. Readers can follow the story through the notes or build the workspace directly.

## Learning map

### In progress: make nodes talk

[01 · ROS2 Communication](01-ROS2-Communication) starts with Topics and adds Services, Actions, and Parameters in one small package. It answers when to broadcast an event, wait for a response, or expose progress and cancellation. Those choices will become the Web Gateway API boundaries.

### In progress: make data know where it is

[02 · TF2 & Coordinate Systems](02-TF2-And-Coordinate-Systems) uses static and dynamic frames to make “where the camera is on the robot” queryable. The circular motion is deliberately minimal and visible; a real camera, arm, and visual detection will all depend on the same TF tree later.

### In progress: make the robot visible

[03 · URDF & RViz](03-URDF-And-RViz) makes R2D2's structure, joint state, and TF visible together. It is the key step from understanding frames to verifying that data drives a model.

### In progress: put runtime information into the scene

[04 · RViz Marker](04-RViz-Markers) now includes basic shapes plus points and lines, turning ROS2 runtime messages into RViz objects. Later detections, trajectories, and debugging regions use the same visual channel.

### In progress: make one run replayable

[05 · rosbag2 & MCAP](05-Rosbag2-And-MCAP) writes R2D2 joint messages and Marker animation to MCAP, then returns them to RViz after the live publishers stop. It turns “what happened in that run?” into inspectable, shareable evidence.

### Complete: make it demonstrable

[06 · ROS2 Web Gateway v0.1](06-ROS2-Web-Gateway) uses FastAPI, WebSocket, Next.js, and Docker Compose to bring prior capabilities into a local experiment console. It shows robot state, creates/cancels restricted tasks, retains gateway logs, and starts/stops MCAP recording from the web.

## Run the current experiments

The environment is fixed to **Ubuntu 24.04 + ROS2 Jazzy**. For a first build:

```bash
cd ros_ws
colcon build --packages-select ros2_fundamentals tf2_coordinate_systems urdf_r2d2 rviz_markers rosbag2_fundamentals web_gateway_demo
source install/setup.bash
```

Then follow either experiment chapter above exactly, including its terminal layout. After changing into `ros_ws`, every new terminal needs:

```bash
source install/setup.bash
```

## How these notes are written

This is not a line-by-line copy of official documentation. Each note keeps four things: the question I wanted to test, steps you can reproduce with expected output, the boundary of the concept, and the failures or next steps that remain. By month end, the chapters should form a replayable chain of evidence rather than a collection of disconnected API notes.
