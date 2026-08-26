#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash
source /workspace/ros_ws/install/setup.bash
cd /workspace/moveit_web_studio/backend

ros2 launch hello_moveit_py web_moveit.launch.py &
ros_launch_pid=$!

cleanup() {
  kill -SIGINT "$ros_launch_pid" 2>/dev/null || true
  wait "$ros_launch_pid" 2>/dev/null || true
}

trap cleanup EXIT INT TERM
uvicorn app.main:app --host 0.0.0.0 --port 8001 &
api_pid=$!

wait -n "$ros_launch_pid" "$api_pid"
