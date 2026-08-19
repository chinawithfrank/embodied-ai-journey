#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash
source /workspace/ros_ws/install/setup.bash

ros2 launch web_gateway_demo demo.launch.py &
ros_launch_pid=$!

cleanup() {
  kill -SIGINT "$ros_launch_pid" 2>/dev/null || true
  wait "$ros_launch_pid" 2>/dev/null || true
}

trap cleanup EXIT INT TERM
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
uvicorn_pid=$!

wait -n "$ros_launch_pid" "$uvicorn_pid"
