[← Month Two: MoveIt](../README.en.md) · [Home](../../../README.en.md) · [中文](README.md) | **English**

# 05 · MoveIt Web Studio: create a pick-and-place task from the browser

`MoveIt Web Studio v0.1` is the month-two capstone: a small, bounded product that turns a browser task into a MoveItPy pick-and-place execution for the Panda mock robot.

## What it demonstrates

- **Next.js + React Three Fiber + Three.js** render an interactive scene.
- **URDF Loader** loads a lightweight Panda model in the browser.
- **ROSLIB.js** subscribes to `/joint_states`, so the browser model follows the mock controller.
- **FastAPI** accepts only bounded pick/place coordinates and exposes task progress.
- **MoveItPy** plans the approach, grasp, transport, place, retreat, and return-to-ready motions.

The browser never invokes `move_group` or arbitrary ROS commands. It expresses intent; the ROS2 side validates, plans, and executes it.

## Start with Docker

From the repository root:

```bash
docker compose -f moveit_web_studio/docker-compose.yml up --build
```

Open `http://localhost:3002`. Wait until the badge changes from **Waiting for robot** to **Robot online**, keep the default coordinates, and press **Plan and execute**.

The services use API port 8001 and ROSLIB WebSocket port 9092. Stop them with:

```bash
docker compose -f moveit_web_studio/docker-compose.yml down
```

## Local development

Install `ros-jazzy-moveit`, `ros-jazzy-moveit-resources-panda-moveit-config`, `ros-jazzy-rosbridge-suite`, and Node.js 20+.

```bash
# terminal 1
source /opt/ros/jazzy/setup.bash
cd ~/develops/embodied-ai-journey/ros_ws
colcon build --packages-select hello_moveit_py
source install/setup.bash
ros2 launch hello_moveit_py web_moveit.launch.py
```

```bash
# terminal 2
source /opt/ros/jazzy/setup.bash
cd ~/develops/embodied-ai-journey
source ros_ws/install/setup.bash
python3 -m pip install -r moveit_web_studio/backend/requirements.txt
PYTHONPATH=moveit_web_studio/backend uvicorn app.main:app --host 0.0.0.0 --port 8001
```

```bash
# terminal 3
cd ~/develops/embodied-ai-journey/moveit_web_studio/frontend
npm install
npm run dev
```

Open `http://localhost:3000` for local development.

## Task flow

```text
browser coordinates → FastAPI validation → /web_moveit/task_request
  → MoveItPy planning and mock-controller execution
  → /web_moveit/task_status → API progress → browser
```

The orange cube represents the object and the blue cylinder the target. The cube transitions to the target during transport as an explanatory UI layer; MoveIt is still the component that computes the real collision-aware trajectory.

## Safety boundary

The demo limits X/Y to `[-0.7, 0.7] m`, Z to `[0.03, 0.65] m`, and queues only one task. This is an educational mock-robot demo, not a real-robot control stack. Do not connect it to hardware without authentication, operator confirmation, speed/force limits, emergency stop, and hardware-validated workspace limits.

See the Chinese version for the detailed learning narrative and troubleshooting steps.
