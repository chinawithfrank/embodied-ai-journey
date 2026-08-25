[← Back to Home](../../README.en.md) · [中文](README.md) | **English**

# Month Two: MoveIt and Arm Motion Planning

> **Monthly direction: move from “the robot is visible” to “the arm can plan, execute, and explain a motion.”**

Month one established the software spine: ROS2 communication, visualisation, recordings, and a web gateway. Month two starts with a different question: when I say “move the end effector here,” how does an arm find a collision-free, joint-limit-aware path that a controller can execute?

MoveIt is the workbench for that problem. It connects robot models, collision checking, kinematics, planners, and controllers. Each lab separates what I asked for, what MoveIt calculated, what a controller executed, and what RViz let me verify.

## Learning map

### In progress: first planning and execution request

[01 · First MoveItPy Project](01-Your-First-MoveIt-Project) uses Python `MoveItPy` to create a `panda_arm` planning component, set an end-effector pose target, and plan/execute the trajectory with MoveIt's mock controller in RViz.

### Completed: inspect a trajectory before execution

[02 · Understand a Plan in RViz](02-Visualizing-In-RViz-With-Python) uses Python-only target markers and `DisplayTrajectory`, then splits “show goal → plan → execute” into three repeatable ROS 2 services. It makes the source of each RViz visual and the boundary between preview and controller execution explicit.

## Directory contract

```text
embodied-ai-journey/
├── ros_ws/src/
│   ├── fundamentals/              # month-one ROS2 labs
│   └── moveit/hello_moveit_py/    # this month's MoveIt Python client
└── notes/02-MoveIt/
    ├── 01-Your-First-MoveIt-Project/
    └── 02-Visualizing-In-RViz-With-Python/
```

Third-party MoveIt resources are not copied into this repository. The lab uses the installed `moveit_resources_panda_moveit_config`, while this repository keeps my code, steps, and observations ready to be reused with a future arm configuration package.

## Start here

The environment is **Ubuntu 24.04 + ROS2 Jazzy**:

```bash
sudo apt update
sudo apt install ros-jazzy-moveit ros-jazzy-moveit-resources-panda-moveit-config
```

Then follow [01 · Your First MoveIt Project](01-Your-First-MoveIt-Project). Each new terminal should source ROS and the workspace overlay first:

```bash
source /opt/ros/jazzy/setup.bash
cd ros_ws
source install/setup.bash
```
