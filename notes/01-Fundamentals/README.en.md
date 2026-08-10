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

This is the **product contract**, not a claim that the product already exists. The repository is still laying foundations: the communication and TF2 examples are runnable today; URDF, RViz, rosbag2/MCAP, the web bridge, dashboard, and Docker workflow will join this same path.

## Directory contract

```text
embodied-ai-journey/
├── ros_ws/                         # runnable, buildable ROS2 experiment code only
│   └── src/fundamentals/
│       ├── ros2_fundamentals/      # Topic, Service, Action, Parameter
│       └── tf2_coordinate_systems/ # static/dynamic TF and lookup
└── notes/                          # learning narrative, concepts, labs, and retrospectives only
    └── 01-Fundamentals/
        ├── README.md               # month entry and product goal
        ├── 01-ROS2-Communication/
        ├── 02-TF2-And-Coordinate-Systems/
        └── 03-URDF-And-RViz/
```

New experiment code belongs in `ros_ws`; its purpose, instructions, observations, and failures belong in `notes`. Readers can follow the story through the notes or build the workspace directly.

## Learning map

### In progress: make nodes talk

[01 · ROS2 Communication](01-ROS2-Communication) starts with Topics and adds Services, Actions, and Parameters in one small package. It answers when to broadcast an event, wait for a response, or expose progress and cancellation. Those choices will become the Web Gateway API boundaries.

### In progress: make data know where it is

[02 · TF2 & Coordinate Systems](02-TF2-And-Coordinate-Systems) uses static and dynamic frames to make “where the camera is on the robot” queryable. The circular motion is deliberately minimal and visible; a real camera, arm, and visual detection will all depend on the same TF tree later.

### In progress: make the robot visible

[03 · URDF & RViz](03-URDF-And-RViz) makes R2D2's structure, joint state, and TF visible together. It is the key step from understanding frames to verifying that data drives a model.

### Next: make it demonstrable

The remaining Fundamentals work stays intentionally narrow: rosbag2 + MCAP to preserve a run, FastAPI + WebSocket + a web console to connect ROS2 to the web, then Docker Compose and one-command startup so a stranger can reproduce the demo.

## Run the current experiments

The environment is fixed to **Ubuntu 24.04 + ROS2 Jazzy**. For a first build:

```bash
cd ros_ws
colcon build --packages-select ros2_fundamentals tf2_coordinate_systems urdf_r2d2
source install/setup.bash
```

Then follow either experiment chapter above exactly, including its terminal layout. After changing into `ros_ws`, every new terminal needs:

```bash
source install/setup.bash
```

## How these notes are written

This is not a line-by-line copy of official documentation. Each note keeps four things: the question I wanted to test, steps you can reproduce with expected output, the boundary of the concept, and the failures or next steps that remain. By month end, the chapters should form a replayable chain of evidence rather than a collection of disconnected API notes.
