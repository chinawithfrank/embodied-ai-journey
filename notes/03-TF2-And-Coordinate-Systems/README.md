# TF2 & Coordinate Systems

How I taught my robot to understand where things are.

## Why I learned this

The robot's camera sees an object. But the robot's arm doesn't know where it is.
Every sensor and every joint on a robot has its own idea of "where" — TF2 is
how those ideas get reconciled into one shared picture of the world.

## Concept

- **Coordinate frame** — a point of reference (e.g. the camera, the base of the robot).
- **Transform** — the position and orientation that relates one frame to another.
- **tf tree** — the tree of all frames on the robot, chained together by transforms.

## Build

Create two frames and the transform between them:

```
camera_frame → base_link
```

TBD — add the actual `tf2` broadcaster/listener code once implemented.

## Experiment

TBD — screenshot of the tf tree (`ros2 run tf2_tools view_frames` or `rviz2`).

## What went wrong

TBD

## Next step

TBD
