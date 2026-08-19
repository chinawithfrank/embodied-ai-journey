[← Month One: Fundamentals](../README.en.md) · [Back to Home](../../../README.en.md) · [中文](README.md) | **English**

# 06 · ROS2 Web Gateway v0.1: Operate and Revisit a Robot Run

Topics, Services, Actions, TF, RViz, and rosbag2 now work independently, but they are scattered across terminals. **ROS2 Web Gateway v0.1** is the month-one integration product: a deliberately restricted local experiment console that makes a ROS2 run observable, controllable, and reviewable.

It is not a dangerous “expose every ROS2 interface to the browser” proxy. It reads only `/joint_states`, calls only `/set_motors_enabled`, creates or cancels only `/turtle1/rotate_absolute`, and records only `/joint_states` plus `/visualization_marker` in MCAP.

## What the demo proves

At `http://localhost:3001`, the dashboard shows ROS2 connectivity and live R2D2 joints; calls the motor demo Service; creates, observes, and cancels a headless simulated-rotation Action; displays gateway logs; and starts/stops an MCAP recording. This is the concrete answer to the month-one outcome: online state, state data, task creation, progress, cancellation, logs, and MCAP recording in one usable loop.

## Architecture

```text
Next.js Dashboard (3001)
        │ HTTP + WebSocket
        ▼
FastAPI Gateway (8000) ── restricted ROS API ── ROS2 Demo Graph
        │                                      ├─ /joint_states
        │                                      ├─ /set_motors_enabled
        │                                      └─ /turtle1/rotate_absolute
        └─ ros2 bag record --storage mcap ─────> Docker volume
```

The FastAPI process owns the browser API, while a separate ROS2 executor thread owns rclpy callbacks. The relevant implementation lives in [`ros_bridge.py`](../../../web_gateway/backend/app/ros_bridge.py), [`recordings.py`](../../../web_gateway/backend/app/recordings.py), and [`demo.launch.py`](../../../ros_ws/src/fundamentals/web_gateway_demo/launch/demo.launch.py).

## Start it

The Gateway container starts both the ROS2 demo graph and FastAPI, so rclpy and ROS nodes communicate inside one container without cross-container DDS discovery. The demo Action has no GUI and does not need `DISPLAY`.

From the repository root:

```bash
docker compose --env-file web_gateway/.env.example \
  -f web_gateway/docker-compose.yml up --build
```

Open `http://localhost:3001`. Keep the Compose terminal open. Stop the stack with:

```bash
docker compose -f web_gateway/docker-compose.yml down
```

Do not add `-v` when you want to keep recordings: MCAP data lives in the `gateway-recordings` Docker volume.

## Three-minute acceptance run

1. Confirm the dashboard says the robot is online and joint values keep changing.
2. Enable motors, then create a `90` degree turtle rotation. Create another task and cancel it while it runs.
3. Record for ten seconds, stop it, and confirm a `run-...` entry appears.
4. Inspect that entry from the gateway container:

```bash
docker compose -f web_gateway/docker-compose.yml exec gateway \
  bash -lc 'source /opt/ros/jazzy/setup.bash && ros2 bag info /recordings/run-*'
```

The bag must identify MCAP and list `/joint_states` and `/visualization_marker`.

## API boundary

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/status` | Online, joint, motor, and recording snapshot |
| `POST` | `/api/motors` | Request the allowlisted motor demo Service |
| `POST` | `/api/tasks` | Create the simulated rotation Action |
| `POST` | `/api/tasks/{id}/cancel` | Cancel an accepted task |
| `GET` | `/api/logs` | Recent gateway events |
| `GET/POST` | `/api/recordings` | List / start an MCAP recording |
| `POST` | `/api/recordings/stop` | Stop the active recording |
| `WS` | `/ws/telemetry` | Live snapshots |

No client can choose an arbitrary topic, ROS type, Service, Action, or shell command. That deliberate allowlist is what makes v0.1 a useful development tool rather than an accidental remote-control vulnerability. The motor button is educational only; do not use this demo as a safety layer for physical hardware.

## Next

Month one now ends with a usable loop. The next iteration should replace demo sources with Gazebo or real sensors, then add authentication, audit history, data retention, safety boundaries, and hardware-independent emergency controls.
