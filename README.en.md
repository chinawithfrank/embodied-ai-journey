[中文](README.md) | **English**

# 🤖 Build Your Own Embodied AI Robot

> Follow my journey building real-world AI robots from zero.

A software engineer's journey into embodied intelligence.

I spent years building software systems.
Now I'm learning how to build machines that can see,
think and act in the physical world.

This repository documents my journey:
from ROS2 basics → robot simulation → perception →
AI agents → real-world robots.

Everything is open-source.
Everything is built step by step.

⭐ Star this repo if you are also exploring embodied AI.

---

## 🗺️ The Journey

```
software engineer ──► ROS2 basics ──► simulation ──► perception ──► AI agents ──► real-world robot
```

Every chapter follows the same loop: **Learn → Build → Share**.
I hit a real problem, learn the concept behind it, build something small
that proves I understand it, and share exactly what went wrong along the way.

## 📚 Chapters

| # | Chapter | Status | Notes |
|---|---------|--------|-------|
| 00 | [Why Embodied AI](notes/00-Why-Embodied-AI) | ✅ Published | Why a software engineer is betting on physical intelligence |
| 01 | [Month One: Robot Software Fundamentals](notes/01-Fundamentals) | ✅ Complete | Monthly outcome: ROS2 Web Gateway v0.1 |
| 01.1 | [ROS2 Communication](notes/01-Fundamentals/01-ROS2-Communication) | ✅ Published | Topic, Service, Action, and Parameter boundaries with runnable examples |
| 01.2 | [TF2 & Coordinate Systems](notes/01-Fundamentals/02-TF2-And-Coordinate-Systems) | ✅ Published | Static/dynamic transforms, lookup, and the TF tree |
| 01.3 | [URDF & RViz](notes/01-Fundamentals/03-URDF-And-RViz) | ✅ Published | R2D2 model, joint state, and TF working together in a visualisation |
| 01.4 | [RViz Marker: Basic Shapes](notes/01-Fundamentals/04-RViz-Markers) | ✅ Published | Cycled basic shapes in RViz with `visualization_msgs/Marker` |
| 01.5 | [RViz Marker: Points and Lines](notes/01-Fundamentals/04-RViz-Markers/02-Points-And-Lines) | ✅ Published | Time-varying point sets with `POINTS`, `LINE_STRIP`, and `LINE_LIST` |
| 01.6 | [rosbag2 & MCAP](notes/01-Fundamentals/05-Rosbag2-And-MCAP) | ✅ Published | Record joint and Marker messages, then replay a run in RViz |
| 01.7 | [ROS2 Web Gateway v0.1](notes/01-Fundamentals/06-ROS2-Web-Gateway) | ✅ Published | Observe ROS2 state, create/cancel tasks, inspect logs, and trigger MCAP recording from the web |
| 02 | [Month Two: MoveIt & Arm Motion Planning](notes/02-MoveIt) | ✅ Complete | Monthly outcome: MoveIt Web Studio v0.1 |
| 02.1 | [First MoveItPy Project](notes/02-MoveIt/01-Your-First-MoveIt-Project) | ✅ Published | Plan and execute Panda's first end-effector pose motion with Python `MoveItPy` |
| 02.2 | [Understand a Plan in RViz](notes/02-MoveIt/02-Visualizing-In-RViz-With-Python) | ✅ Published | Use Python Markers, `DisplayTrajectory`, and staged services to visualize a goal, plan, and execution |
| 02.3 | [Python Collision-Aware Planning](notes/02-MoveIt/03-Planning-Around-Objects-With-Python) | ✅ Published | Synchronize a `CollisionObject` to MoveItPy and `move_group`, then plan and execute around an obstacle |
| 02.4 | [Python MTC Pick and Place](notes/02-MoveIt/04-Pick-And-Place-With-MTC-Python) | ✅ Published | Use MTC Python task stages to plan, inspect, and execute Panda pick and place |
| 02.5 | [MoveIt Web Studio](notes/02-MoveIt/05-MoveIt-Web-Studio) | ✅ Published | Build a bounded pick-and-place task in the browser, then execute it with MoveItPy |
| 03 | [Month Three: Robot Vision](notes/03-Vision) | 🚧 In progress | Learn to detect objects from camera images, then connect them to robot coordinate frames |
| 03.1 | [YOLO Tennis-Ball Detection and Pixel Coordinates](notes/03-Vision/01-YOLO-Tennis-Ball) | ✅ Published | Train a one-class YOLO model, then show the tennis-ball centre pixel in a webcam stream |
| 04 | [Real Hardware Project: Fan Robot](notes/04-Fan-Robot/README.en.md) | 🚧 In progress | Start with capture, then build toward visual control and reinforcement learning |
| 04.1 | [ESP32-S3 and OV2640: First Eyes](notes/04-Fan-Robot/01-ESP32-Camera/README.en.md) | ✅ Browser video verified | Onboard24MHz,8MB PSRAM, and browser video working; Python snapshots and extended stability still to check |
| 04.2 | [Offline Hand Detection on ESP32](notes/04-Fan-Robot/02-Offline-Hand-Detection/README.en.md) | 🚧 Hardware acceptance pending | S3-local model outputs hand boxes, centers, and offsets; optional AP preview or Wi-Fi-disabled operation |
| 04.3 | [Manual Dual N20 Control, Camera Retained](notes/04-Fan-Robot/03-Manual-Motor-Control/README.en.md) | 🚧 Partially verified | MotorA turns at80% PWM, not60%; dual-motor wiring/test guide added; MotorB and coexistence pending; camera/stop safeguards retained |

This table is maintained in sync with `notes/`: every new learning subchapter gets a direct link and an updated status here.

## 🧭 How Each Chapter Is Written

Every chapter in [`notes/`](notes) follows the same template
(see [`notes/TEMPLATE.md`](notes/TEMPLATE.md)), so you always know what to expect:

```
# Title

## Why I learned this
The real-world problem — why a robot needs this capability.

## Concept
The plain-language explanation.

## Build
The actual code.

## Experiment
Screenshots / recordings of it running.

## What went wrong
The pitfalls I hit.

## Next step
Where this leads next.
```

## 🗂️ Repo Structure

```
embodied-ai-journey/
├── README.md          this file (Chinese)
├── README.en.md        English version
├── notes/              the journey, written chapter by chapter
│   ├── TEMPLATE.md
│   ├── 00-Why-Embodied-AI/
│   ├── 01-Fundamentals/             month one: ROS2 Web Gateway v0.1
│       ├── 01-ROS2-Communication/
│       ├── 02-TF2-And-Coordinate-Systems/
│       ├── 03-URDF-And-RViz/
│       ├── 04-RViz-Markers/
│       ├── 05-Rosbag2-And-MCAP/
│       └── 06-ROS2-Web-Gateway/
│   ├── 02-MoveIt/                  month two: MoveIt and arm motion planning
│       ├── 01-Your-First-MoveIt-Project/
│       ├── 02-Visualizing-In-RViz-With-Python/
│       ├── 03-Planning-Around-Objects-With-Python/
│       ├── 04-Pick-And-Place-With-MTC-Python/
│       └── 05-MoveIt-Web-Studio/
│   ├── 03-Vision/                   month three: robot vision
│   │   └── 01-YOLO-Tennis-Ball/
│   └── 04-Fan-Robot/                real hardware project: fan robot
│       ├── 01-ESP32-Camera/
│       ├── 02-Offline-Hand-Detection/
│       └── 03-Manual-Motor-Control/
├── ros_ws/             the ROS2 workspace — everything I build gets run here
│   └── src/
│       ├── fundamentals/
│       │   ├── ros2_fundamentals/
│       │   ├── tf2_coordinate_systems/
│       │   ├── urdf_r2d2/
│       │   ├── rviz_markers/
│       │   ├── rosbag2_fundamentals/
│       │   └── web_gateway_demo/
│       ├── moveit/
│           └── hello_moveit_py/
│       ├── vision/
│       │   └── yolo_tennis_ball/
│       └── fan_robot/               camera firmware and computer-side tools
│           ├── firmware/
│           └── tools/
├── web_gateway/        month-one outcome: ROS2 Web Gateway v0.1
├── moveit_web_studio/  month-two outcome: browser-based MoveIt pick-and-place studio
└── recordings/         local rosbag2/MCAP runtime output (not in Git)
```

## ⭐ Follow Along

If you're a software engineer curious about robots, this repo is for you.
Star it, watch it, and follow along as the journey unfolds.
